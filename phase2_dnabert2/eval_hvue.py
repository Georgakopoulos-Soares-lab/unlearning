"""Train/evaluate DNABERT-2 on prepared HVUE classification JSONL splits."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, matthews_corrcoef, roc_auc_score
from torch.utils.data import DataLoader, Dataset


DEFAULT_MODEL = "zhihan1996/DNABERT-2-117M"
DEFAULT_DATA_DIR = "data/dnabert2/hvue"
DEFAULT_OUT_DIR = "data/dnabert2/runs/hvue_host_tropism"


class JsonlSequenceDataset(Dataset):
    def __init__(self, path: Path) -> None:
        self.rows: list[dict[str, Any]] = []
        with path.open() as handle:
            for line in handle:
                if line.strip():
                    row = json.loads(line)
                    self.rows.append(row)
        if not self.rows:
            raise RuntimeError(f"No rows found in {path}")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        return {
            "id": row["id"],
            "sequence": row["sequence"],
            "label": int(row["label"]),
        }


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def make_collate_fn(tokenizer: Any, max_length: int):
    def collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
        encoded = tokenizer(
            [row["sequence"] for row in batch],
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        )
        encoded["labels"] = torch.tensor([row["label"] for row in batch], dtype=torch.long)
        encoded["ids"] = [row["id"] for row in batch]
        return encoded

    return collate


def freeze_for_head_only(model: torch.nn.Module) -> list[str]:
    for parameter in model.parameters():
        parameter.requires_grad = False
    trainable_names = []
    head_tokens = ("classifier", "score", "pre_classifier", "pooler", "head")
    for name, parameter in model.named_parameters():
        if any(token in name.lower() for token in head_tokens):
            parameter.requires_grad = True
            trainable_names.append(name)
    if not trainable_names:
        raise RuntimeError("Could not find a classification head to train for --mode head_only")
    return trainable_names


def apply_lora(model: torch.nn.Module, args: argparse.Namespace) -> torch.nn.Module:
    try:
        from peft import LoraConfig, TaskType, get_peft_model
    except ImportError as exc:
        raise RuntimeError("LoRA mode requires PEFT. Install with: python -m pip install peft") from exc
    target_modules = resolve_lora_target_modules(model, args.lora_target_modules)
    config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        task_type=TaskType.SEQ_CLS,
        target_modules=target_modules or None,
    )
    return get_peft_model(model, config)


def resolve_lora_target_modules(model: torch.nn.Module, target_spec: str) -> list[str]:
    requested = [item.strip() for item in target_spec.split(",") if item.strip()]
    module_names = [name for name, module in model.named_modules() if isinstance(module, torch.nn.Linear)]
    matched = [
        target
        for target in requested
        if any(name == target or name.endswith(f".{target}") for name in module_names)
    ]
    if matched:
        return matched
    if any(name.endswith(".Wqkv") or name == "Wqkv" for name in module_names):
        print("[dnabert2-hvue] LoRA target modules not found; falling back to DNABERT-2 fused attention target: Wqkv")
        return ["Wqkv"]
    raise RuntimeError(
        "No requested LoRA target modules were found. "
        f"Requested={requested}; available Linear suffixes={sorted({name.split('.')[-1] for name in module_names})}"
    )


def load_tokenizer_and_classifier(model_name: str, num_labels: int = 2) -> tuple[Any, torch.nn.Module]:
    try:
        from transformers import AutoConfig, AutoModelForSequenceClassification, AutoTokenizer
        from transformers.dynamic_module_utils import get_class_from_dynamic_module
    except ImportError as exc:
        raise RuntimeError("DNABERT-2 eval requires transformers. Install with: python -m pip install transformers") from exc

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    config = AutoConfig.from_pretrained(model_name, trust_remote_code=True)
    pad_token_id = getattr(tokenizer, "pad_token_id", None)
    if pad_token_id is None:
        pad_token_id = getattr(tokenizer, "eos_token_id", None)
    if pad_token_id is None:
        pad_token_id = 0
    config.pad_token_id = pad_token_id
    config.num_labels = num_labels
    class_ref = getattr(config, "auto_map", {}).get("AutoModelForSequenceClassification")
    if class_ref:
        model_class = get_class_from_dynamic_module(class_ref, model_name)
        patch_dnabert2_runtime(model_class)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        config=config,
        trust_remote_code=True,
        low_cpu_mem_usage=False,
        device_map=None,
        _fast_init=False,
    )
    return tokenizer, model


def patch_dnabert2_runtime(model_class: type) -> None:
    module = sys.modules.get(model_class.__module__)
    if module is not None:
        module.flash_attn_qkvpacked_func = None
    encoder_class = getattr(module, "BertEncoder", None) if module is not None else None
    if encoder_class is None or getattr(encoder_class, "_phase2_dnabert2_alibi_patch", False):
        return
    original = encoder_class.rebuild_alibi_tensor

    def rebuild_alibi_tensor_cpu_default(self, size: int, device: Any = None):
        if device is None:
            device = torch.device("cpu")
        return original(self, size=size, device=device)

    encoder_class.rebuild_alibi_tensor = rebuild_alibi_tensor_cpu_default
    encoder_class._phase2_dnabert2_alibi_patch = True


def move_batch(batch: dict[str, Any], device: torch.device) -> dict[str, Any]:
    return {key: value.to(device) if torch.is_tensor(value) else value for key, value in batch.items()}


def probability_from_logits(logits: torch.Tensor) -> torch.Tensor:
    if logits.shape[-1] == 1:
        return torch.sigmoid(logits.squeeze(-1))
    return torch.softmax(logits, dim=-1)[:, 1]


@torch.no_grad()
def evaluate(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> tuple[dict[str, float], list[dict[str, Any]]]:
    model.eval()
    ids: list[str] = []
    labels: list[int] = []
    scores: list[float] = []
    losses: list[float] = []
    for batch in loader:
        batch_ids = list(batch.pop("ids"))
        batch = move_batch(batch, device)
        outputs = model(**batch)
        prob = probability_from_logits(outputs.logits)
        ids.extend(batch_ids)
        labels.extend(batch["labels"].detach().cpu().tolist())
        scores.extend(prob.detach().cpu().tolist())
        if outputs.loss is not None:
            losses.append(float(outputs.loss.detach().cpu()))
    predictions = [1 if score >= 0.5 else 0 for score in scores]
    metrics = {
        "loss": float(np.mean(losses)) if losses else math.nan,
        "accuracy": float(accuracy_score(labels, predictions)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "mcc": float(matthews_corrcoef(labels, predictions)),
        "auroc": float(roc_auc_score(labels, scores)) if len(set(labels)) > 1 else math.nan,
        "auprc": float(average_precision_score(labels, scores)) if len(set(labels)) > 1 else math.nan,
    }
    rows = [{"id": sample_id, "label": label, "score": score, "prediction": pred} for sample_id, label, score, pred in zip(ids, labels, scores, predictions)]
    return metrics, rows


def train_one_epoch(model: torch.nn.Module, loader: DataLoader, optimizer: torch.optim.Optimizer, device: torch.device) -> float:
    model.train()
    losses = []
    for batch in loader:
        batch.pop("ids")
        batch = move_batch(batch, device)
        optimizer.zero_grad(set_to_none=True)
        loss = model(**batch).loss
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    return float(np.mean(losses)) if losses else math.nan


def write_metrics(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["epoch", "split", "mode", "model_name", "loss", "accuracy", "f1", "mcc", "auroc", "auprc"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_predictions(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "label", "score", "prediction"])
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--prefix", default="host_tropism")
    parser.add_argument("--mode", choices=["head_only", "lora", "full_ft"], default="lora")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--lora-target-modules", default="Wqkv")
    parser.add_argument("--save-model", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir) / args.mode
    train_dataset = JsonlSequenceDataset(data_dir / f"{args.prefix}_train.jsonl")
    val_dataset = JsonlSequenceDataset(data_dir / f"{args.prefix}_val.jsonl")
    test_dataset = JsonlSequenceDataset(data_dir / f"{args.prefix}_test.jsonl")

    tokenizer, model = load_tokenizer_and_classifier(args.model_name, num_labels=2)
    if args.mode == "head_only":
        trainable = freeze_for_head_only(model)
    elif args.mode == "lora":
        model = apply_lora(model, args)
        trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]
    else:
        trainable = [name for name, parameter in model.named_parameters() if parameter.requires_grad]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    collate_fn = make_collate_fn(tokenizer, args.max_length)
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, collate_fn=collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_fn)

    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr)
    metrics_rows: list[dict[str, Any]] = []
    best_val = -math.inf
    best_state = None
    for epoch in range(1, args.epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, device)
        val_metrics, _ = evaluate(model, val_loader, device)
        row = {"epoch": epoch, "split": "val", "mode": args.mode, "model_name": args.model_name, **val_metrics}
        metrics_rows.append(row)
        print(f"[dnabert2-hvue] epoch={epoch} train_loss={train_loss:.5f} val_auroc={val_metrics['auroc']:.5f}")
        if val_metrics["auroc"] > best_val:
            best_val = val_metrics["auroc"]
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    test_metrics, test_predictions = evaluate(model, test_loader, device)
    metrics_rows.append({"epoch": "best", "split": "test", "mode": args.mode, "model_name": args.model_name, **test_metrics})
    write_metrics(out_dir / "eval_metrics.csv", metrics_rows)
    write_predictions(out_dir / "test_predictions.csv", test_predictions)
    metadata = {
        "model_name": args.model_name,
        "mode": args.mode,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "max_length": args.max_length,
        "seed": args.seed,
        "trainable_parameter_names": trainable,
        "trainable_parameters": int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)),
        "total_parameters": int(sum(parameter.numel() for parameter in model.parameters())),
        "test_metrics": test_metrics,
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    if args.save_model:
        model.save_pretrained(out_dir / "model")
        tokenizer.save_pretrained(out_dir / "model")
    print(f"[dnabert2-hvue] wrote {out_dir / 'eval_metrics.csv'}")


if __name__ == "__main__":
    main()
