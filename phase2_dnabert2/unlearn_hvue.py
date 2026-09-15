"""LoRA unlearning baselines for DNABERT-2 HVUE host-tropism classifier."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, matthews_corrcoef, roc_auc_score
from torch.utils.data import DataLoader, Dataset


DEFAULT_MODEL = "zhihan1996/DNABERT-2-117M"
DEFAULT_SPLIT_DIR = "data/dnabert2/unlearn_splits"
DEFAULT_OUT_DIR = "data/dnabert2/unlearn_runs/hvue_host_tropism"


class JsonlDataset(Dataset):
    def __init__(self, path: Path) -> None:
        self.rows = []
        with path.open() as handle:
            for line in handle:
                if line.strip():
                    self.rows.append(json.loads(line))
        if not self.rows:
            raise RuntimeError(f"No rows found in {path}")

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.rows[index]
        return {"id": row["id"], "sequence": row["sequence"], "label": int(row["label"])}


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


def move_batch(batch: dict[str, Any], device: torch.device) -> dict[str, Any]:
    return {key: value.to(device) if torch.is_tensor(value) else value for key, value in batch.items()}


def cycle(loader: DataLoader) -> Iterator[dict[str, Any]]:
    while True:
        for batch in loader:
            yield batch


def probability_from_logits(logits: torch.Tensor) -> torch.Tensor:
    if logits.shape[-1] == 1:
        return torch.sigmoid(logits.squeeze(-1))
    return torch.softmax(logits, dim=-1)[:, 1]


def apply_lora(model: torch.nn.Module, args: argparse.Namespace) -> torch.nn.Module:
    try:
        from peft import LoraConfig, TaskType, get_peft_model
    except ImportError as exc:
        raise RuntimeError("LoRA unlearning requires PEFT. Install with: python -m pip install peft") from exc
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
        print("[dnabert2-unlearn] LoRA target modules not found; falling back to DNABERT-2 fused attention target: Wqkv")
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
        raise RuntimeError("DNABERT-2 unlearning requires transformers.") from exc

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


def classification_metrics(labels: list[int], scores: list[float]) -> dict[str, float]:
    predictions = [1 if score >= 0.5 else 0 for score in scores]
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "mcc": float(matthews_corrcoef(labels, predictions)),
        "auroc": float(roc_auc_score(labels, scores)) if len(set(labels)) > 1 else math.nan,
        "auprc": float(average_precision_score(labels, scores)) if len(set(labels)) > 1 else math.nan,
    }


@torch.no_grad()
def evaluate(model: torch.nn.Module, loader: DataLoader, device: torch.device) -> dict[str, float]:
    model.eval()
    labels: list[int] = []
    scores: list[float] = []
    losses: list[float] = []
    for batch in loader:
        batch.pop("ids")
        batch = move_batch(batch, device)
        outputs = model(**batch)
        labels.extend(batch["labels"].detach().cpu().tolist())
        scores.extend(probability_from_logits(outputs.logits).detach().cpu().tolist())
        if outputs.loss is not None:
            losses.append(float(outputs.loss.detach().cpu()))
    return {"loss": float(np.mean(losses)) if losses else math.nan, **classification_metrics(labels, scores)}


def symmetric_kl(logits_a: torch.Tensor, logits_b: torch.Tensor) -> torch.Tensor:
    logp_a = F.log_softmax(logits_a, dim=-1)
    logp_b = F.log_softmax(logits_b, dim=-1)
    p_a = logp_a.exp()
    p_b = logp_b.exp()
    return 0.5 * (
        F.kl_div(logp_a, p_b, reduction="batchmean") + F.kl_div(logp_b, p_a, reduction="batchmean")
    )


def forget_uniform_kl(logits: torch.Tensor) -> torch.Tensor:
    logp = F.log_softmax(logits, dim=-1)
    target = torch.full_like(logp, 1.0 / logp.shape[-1])
    return F.kl_div(logp, target, reduction="batchmean")


def compute_unlearn_loss(
    model: torch.nn.Module,
    reference: torch.nn.Module | None,
    forget_batch: dict[str, Any],
    retain_batch: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[torch.Tensor, dict[str, float]]:
    forget_outputs = model(**forget_batch)
    retain_outputs = model(**retain_batch)
    forget_ce = forget_outputs.loss
    retain_ce = retain_outputs.loss

    if args.objective == "gradient_ascent":
        weighted_forget = -args.alpha_forget * forget_ce
        weighted_retain = args.alpha_retain * retain_ce
        loss = weighted_forget + weighted_retain
        retain_kl = torch.zeros_like(loss)
        forget_uniform = torch.zeros_like(loss)
    elif args.objective == "ga_retain_kl":
        if reference is None:
            raise RuntimeError("ga_retain_kl requires a frozen reference model")
        with torch.no_grad():
            retain_ref = reference(
                input_ids=retain_batch["input_ids"],
                attention_mask=retain_batch.get("attention_mask"),
                token_type_ids=retain_batch.get("token_type_ids"),
            )
        retain_kl = symmetric_kl(retain_outputs.logits, retain_ref.logits)
        weighted_forget = -args.alpha_forget * forget_ce
        weighted_retain = args.alpha_retain * retain_kl
        loss = weighted_forget + weighted_retain
        forget_uniform = torch.zeros_like(loss)
    elif args.objective == "uniform_forget_retain_kl":
        if reference is None:
            raise RuntimeError("uniform_forget_retain_kl requires a frozen reference model")
        with torch.no_grad():
            retain_ref = reference(
                input_ids=retain_batch["input_ids"],
                attention_mask=retain_batch.get("attention_mask"),
                token_type_ids=retain_batch.get("token_type_ids"),
            )
        forget_uniform = forget_uniform_kl(forget_outputs.logits)
        retain_kl = symmetric_kl(retain_outputs.logits, retain_ref.logits)
        weighted_forget = args.alpha_forget * forget_uniform
        weighted_retain = args.alpha_retain * retain_kl
        loss = weighted_forget + weighted_retain
    else:
        raise ValueError(f"Unknown objective: {args.objective}")

    metrics = {
        "loss": float(loss.detach().cpu()),
        "forget_ce": float(forget_ce.detach().cpu()),
        "retain_ce": float(retain_ce.detach().cpu()),
        "retain_kl": float(retain_kl.detach().cpu()),
        "forget_uniform_kl": float(forget_uniform.detach().cpu()),
        "weighted_forget": float(weighted_forget.detach().cpu()),
        "weighted_retain": float(weighted_retain.detach().cpu()),
    }
    return loss, metrics


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def write_metrics(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "step",
        "split",
        "loss",
        "forget_ce",
        "retain_ce",
        "retain_kl",
        "forget_uniform_kl",
        "weighted_forget",
        "weighted_retain",
        "accuracy",
        "f1",
        "mcc",
        "auroc",
        "auprc",
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default=DEFAULT_MODEL)
    parser.add_argument("--split-dir", default=DEFAULT_SPLIT_DIR)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--objective",
        choices=["gradient_ascent", "ga_retain_kl", "uniform_forget_retain_kl"],
        default="ga_retain_kl",
    )
    parser.add_argument("--steps", type=int, default=500)
    parser.add_argument("--eval-every", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--alpha-forget", type=float, default=1.0)
    parser.add_argument("--alpha-retain", type=float, default=1.0)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--lora-target-modules", default="Wqkv")
    parser.add_argument("--save-model", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer, model = load_tokenizer_and_classifier(args.model_name, num_labels=2)
    collate_fn = make_collate_fn(tokenizer, args.max_length)
    split_dir = Path(args.split_dir)
    forget_train = JsonlDataset(split_dir / "forget_train.jsonl")
    retain_train = JsonlDataset(split_dir / "retain_train.jsonl")
    forget_val = JsonlDataset(split_dir / "forget_val.jsonl")
    retain_val = JsonlDataset(split_dir / "retain_val.jsonl")
    forget_test = JsonlDataset(split_dir / "forget_test.jsonl")
    retain_test = JsonlDataset(split_dir / "retain_test.jsonl")

    model = apply_lora(model, args)
    model.to(device)

    reference = None
    if args.objective in {"ga_retain_kl", "uniform_forget_retain_kl"}:
        _reference_tokenizer, reference = load_tokenizer_and_classifier(args.model_name, num_labels=2)
        reference.to(device)
        reference.eval()
        for parameter in reference.parameters():
            parameter.requires_grad = False

    forget_loader = DataLoader(forget_train, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    retain_loader = DataLoader(retain_train, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)
    eval_loaders = {
        "forget_val": DataLoader(forget_val, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn),
        "retain_val": DataLoader(retain_val, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn),
        "forget_test": DataLoader(forget_test, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn),
        "retain_test": DataLoader(retain_test, batch_size=args.batch_size, shuffle=False, collate_fn=collate_fn),
    }
    forget_iter = cycle(forget_loader)
    retain_iter = cycle(retain_loader)
    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=args.lr)

    run_dir = Path(args.out_dir) / args.objective
    train_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []
    for step in range(1, args.steps + 1):
        model.train()
        forget_batch = move_batch(next(forget_iter), device)
        retain_batch = move_batch(next(retain_iter), device)
        forget_batch.pop("ids")
        retain_batch.pop("ids")
        optimizer.zero_grad(set_to_none=True)
        loss, metrics = compute_unlearn_loss(model, reference, forget_batch, retain_batch, args)
        loss.backward()
        optimizer.step()
        train_rows.append({"step": step, "split": "train", **metrics})
        if step == 1 or step % args.eval_every == 0 or step == args.steps:
            print(
                f"[dnabert2-unlearn] step={step} loss={metrics['loss']:.5f} "
                f"forget_ce={metrics['forget_ce']:.5f} retain_term={metrics['weighted_retain']:.5f}"
            )
            for split, loader in eval_loaders.items():
                row = {"step": step, "split": split, **evaluate(model, loader, device)}
                eval_rows.append(row)

    write_metrics(run_dir / "train_metrics.csv", train_rows)
    write_metrics(run_dir / "eval_metrics.csv", eval_rows)
    metadata = {
        "model_name": args.model_name,
        "objective": args.objective,
        "steps": args.steps,
        "eval_every": args.eval_every,
        "batch_size": args.batch_size,
        "lr": args.lr,
        "max_length": args.max_length,
        "seed": args.seed,
        "alpha_forget": args.alpha_forget,
        "alpha_retain": args.alpha_retain,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lora_dropout": args.lora_dropout,
        "lora_target_modules": args.lora_target_modules,
        "trainable_parameters": int(sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)),
        "total_parameters": int(sum(parameter.numel() for parameter in model.parameters())),
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    if args.save_model:
        model.save_pretrained(run_dir / "model")
        tokenizer.save_pretrained(run_dir / "model")
    print(f"[dnabert2-unlearn] wrote {run_dir / 'eval_metrics.csv'}")


if __name__ == "__main__":
    main()
