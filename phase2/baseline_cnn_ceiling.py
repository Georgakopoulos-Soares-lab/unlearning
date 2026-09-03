"""Supervised CNN ceiling baseline -- the comparator that actually binds.

Companion to ``eval_kmer_baseline.py``, reading the same benchmark manifest and
emitting the same shape of CSV so the two are directly comparable.

Why this exists
---------------
Across a 22-task audit (GENEB regulatory / histone / methylation / species /
coding plus viral benchmarks) the **tuned CNN was the strongest non-foundation
baseline on 21 of 22 tasks**; a k-mer logistic regression bound on exactly one
(``iDHS-EL_DNase_I``, 0.6411 vs CNN 0.5900). Qualifying a target against k-mer
alone therefore over-estimates model headroom by **0.10-0.66 MCC** and will
manufacture targets that do not exist.

The search space is not incidental. Two axes decide the result:

* **Receptive field, not capacity.** On a 600bp splice task a ResNet with 9.44M
  parameters and a 89bp receptive field scores 0.336 MCC; a U-Net with 0.26M
  parameters and global receptive field scores 0.951. That is +0.62 MCC at 36x
  fewer parameters. Kernel size and dilation base move receptive field at
  essentially zero parameter cost (dilated 0.68M: RF 249 at ``dbase=2`` vs 2729
  at ``dbase=4``), so they are swept as first-class axes.
* **Matched tuning budget.** A baseline given one learning rate against a model
  given several is not a baseline. Stage 3 sweeps LR at the same budget.

Selection is on the ``val`` split only; ``test`` is scored once per cell and the
dev-selected number is reported separately from the oracle-best-over-ladder
number so the reader can see the selection cost.

Protocol note
-------------
Report ``--refit-seeds`` >= 3. A single seed is not an estimate: on one task a
1-seed cell read 0.6100 and its 3-seed mean was 0.5550, and on another a
3-seed refit under a too-aggressive early-stopping rule read 0.8185 +- 0.0533
where a converged 5-seed refit read 0.8413 +- 0.0128 -- the same experiment
flipped its own verdict. If seeds disagree by more than a few points, raise
``--min-epochs`` and ``--patience`` before trusting the spread.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from phase2.run_metadata import build_run_metadata, write_metadata

csv.field_size_limit(sys.maxsize)

FIELDNAMES = [
    "benchmark",
    "task",
    "split_type",
    "group",
    "baseline",
    "stage",
    "arch",
    "channels",
    "blocks",
    "kernel",
    "dilation_base",
    "receptive_field_bp",
    "params",
    "lr",
    "n_seeds",
    "seqlen",
    "n_train",
    "n_val",
    "n_test",
    "selection_metric",
    "val_score",
    "test_score",
    "test_score_sd",
    "is_dev_selected",
    "oracle_best_test",
]

# (arch, channels, blocks) spanning ~0.04M -> ~10M parameters.
LADDER: tuple[tuple[str, int, int], ...] = (
    ("dilated", 32, 3), ("dilated", 64, 4), ("dilated", 128, 5),
    ("dilated", 256, 5), ("dilated", 448, 6),
    ("unet", 24, 3), ("unet", 48, 3), ("unet", 112, 3), ("unet", 64, 4),
    ("resnet", 64, 3), ("resnet", 128, 4), ("resnet", 256, 5), ("resnet", 320, 5),
)

BASE_MAP = np.full(256, 4, dtype=np.int64)
for _i, _ch in enumerate("ACGT"):
    BASE_MAP[ord(_ch)] = _i


@dataclass
class Record:
    benchmark: str
    task: str
    split_type: str
    group: str
    split: str
    sequence: str
    label: str


def receptive_field(arch: str, blocks: int, kernel: int, dilation_base: int) -> Optional[int]:
    """Effective receptive field in bp. ``None`` for U-Net, which is global."""
    if arch == "unet":
        return None
    if arch == "dilated":
        return 1 + sum((kernel - 1) * dilation_base ** min(i, 8) for i in range(blocks))
    # resnet: stem conv plus two dilated convs per residual block
    return 1 + (kernel - 1) + sum(2 * (kernel - 1) * dilation_base ** min(i, 8) for i in range(blocks))


def build_model(arch: str, n_classes: int, channels: int, blocks: int,
                kernel: int = 9, dilation_base: Optional[int] = None, dropout: float = 0.2):
    """Construct one architecture. Imported lazily so the module loads without torch."""
    import torch.nn as nn
    import torch.nn.functional as F

    class Dilated(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            db = dilation_base if dilation_base is not None else 2
            self.emb = nn.Embedding(5, channels)
            layers = []
            for i in range(blocks):
                dil = db ** min(i, 8)
                layers += [
                    nn.Conv1d(channels, channels, kernel, padding=dil * (kernel - 1) // 2, dilation=dil),
                    nn.BatchNorm1d(channels), nn.GELU(), nn.Dropout(dropout),
                ]
            self.body = nn.Sequential(*layers)
            self.head = nn.Linear(channels, n_classes)

        def forward(self, x):
            h = self.emb(x).transpose(1, 2)
            h = self.body(h)
            return self.head(h.mean(-1))

    class ResBlk(nn.Module):
        def __init__(self, c: int, dil: int) -> None:
            super().__init__()
            pad = dil * (kernel - 1) // 2
            self.b = nn.Sequential(
                nn.Conv1d(c, c, kernel, padding=pad, dilation=dil), nn.BatchNorm1d(c), nn.GELU(),
                nn.Dropout(dropout),
                nn.Conv1d(c, c, kernel, padding=pad, dilation=dil), nn.BatchNorm1d(c),
            )

        def forward(self, x):
            return F.gelu(x + self.b(x))

    class ResNet(nn.Module):
        def __init__(self) -> None:
            super().__init__()
            db = dilation_base if dilation_base is not None else 1
            self.emb = nn.Embedding(5, channels)
            self.stem = nn.Sequential(
                nn.Conv1d(channels, channels, kernel, padding=(kernel - 1) // 2),
                nn.BatchNorm1d(channels), nn.GELU(),
            )
            self.body = nn.Sequential(*[ResBlk(channels, db ** min(i, 8)) for i in range(blocks)])
            self.head = nn.Linear(channels, n_classes)

        def forward(self, x):
            h = self.stem(self.emb(x).transpose(1, 2))
            return self.head(self.body(h).mean(-1))

    class UNet(nn.Module):
        """Strided down/up path: receptive field spans the whole input."""

        def __init__(self) -> None:
            super().__init__()
            self.emb = nn.Embedding(5, channels)
            pad = (kernel - 1) // 2
            self.down = nn.ModuleList([
                nn.Sequential(
                    nn.Conv1d(channels, channels, kernel, stride=2, padding=pad),
                    nn.BatchNorm1d(channels), nn.GELU(), nn.Dropout(dropout),
                ) for _ in range(blocks)
            ])
            self.up = nn.ModuleList([
                nn.Sequential(
                    nn.Conv1d(channels, channels, kernel, padding=pad),
                    nn.BatchNorm1d(channels), nn.GELU(),
                ) for _ in range(blocks)
            ])
            self.head = nn.Linear(channels, n_classes)

        def forward(self, x):
            h = self.emb(x).transpose(1, 2)
            skips = []
            for layer in self.down:
                skips.append(h)
                h = layer(h)
            for layer, skip in zip(self.up, reversed(skips)):
                h = F.interpolate(h, size=skip.shape[-1], mode="nearest")
                h = layer(h) + skip
            return self.head(h.mean(-1))

    return {"dilated": Dilated, "resnet": ResNet, "unet": UNet}[arch]()


def encode(sequences: Sequence[str], length: int) -> np.ndarray:
    out = np.full((len(sequences), length), 4, dtype=np.int64)
    for i, seq in enumerate(sequences):
        trimmed = seq[:length]
        if trimmed:
            out[i, : len(trimmed)] = BASE_MAP[np.frombuffer(trimmed.encode(), np.uint8)]
    return out


def clean_sequence(value: object, max_length: int) -> str:
    seq = "".join(ch for ch in str(value or "").upper() if ch in {"A", "C", "G", "T", "N"})
    return seq[:max_length] if max_length > 0 else seq


def normalize_split(value: object) -> str:
    split = str(value or "").lower()
    return "val" if split in {"dev", "valid", "validation"} else split


def normalize_split_type(value: object) -> str:
    split_type = str(value or "").strip().lower()
    if not split_type:
        return "random"
    if split_type in {"cluster-disjoint", "cluster_disjoint", "disjoint"}:
        return "cluster_disjoint"
    return split_type


def read_manifest(args) -> list[Record]:
    task_filter = ({p.strip() for p in args.task_filter.split(",") if p.strip()}
                   if args.task_filter else None)
    records: list[Record] = []
    with open(args.benchmark_manifest, newline="") as handle:
        reader = csv.DictReader(handle)
        missing = {"split", "sequence", "label"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Manifest missing required columns: {sorted(missing)}")
        for row in reader:
            task = row.get("task") or args.default_task
            if task_filter is not None and task not in task_filter:
                continue
            split = normalize_split(row.get("split"))
            label = str(row.get("label", "")).strip()
            seq = clean_sequence(row.get("sequence", ""), args.max_length)
            if split not in {"train", "val", "test"} or not label or not seq:
                continue
            records.append(Record(
                row.get("benchmark") or args.default_benchmark,
                task,
                normalize_split_type(row.get("split_type")),
                row.get("group", "") or args.default_group,
                split, seq, label,
            ))
    return records


def score(y_true: np.ndarray, pred: np.ndarray, prob: np.ndarray, metric: str) -> float:
    from sklearn.metrics import f1_score, matthews_corrcoef, roc_auc_score
    if metric == "auroc":
        try:
            if prob.shape[1] == 2:
                return float(roc_auc_score(y_true, prob[:, 1]))
            return float(roc_auc_score(y_true, prob, multi_class="ovr", average="macro"))
        except ValueError:
            return float("nan")
    if metric == "macro_f1":
        return float(f1_score(y_true, pred, average="macro", zero_division=0))
    return float(matthews_corrcoef(y_true, pred))


def train_cell(arch: str, channels: int, blocks: int, kernel: int, dilation_base: Optional[int],
               lr: float, seeds: Sequence[int], tensors: dict, n_classes: int,
               metric: str, args, save_prefix: Optional[str] = None) -> Optional[list[dict]]:
    """Train one (architecture, kernel, dilation, lr) cell over ``seeds``.

    Returns per-seed val/test scores, or ``None`` if every seed hit OOM.

    When ``save_prefix`` is set, per-seed test predictions are written alongside the
    labels. A paired bootstrap needs row-level predictions from **both** arms, and the
    targets in this project are +0.08 to +0.14 against seed SDs of 0.012-0.032 -- close
    enough that a seed-SD gate alone is not an adequate significance test.
    """
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    x_train, y_train = tensors["train"]
    x_val, y_val = tensors["val"]
    x_test, y_test = tensors["test"]
    per_seed: list[dict] = []
    use_amp = args.device.startswith("cuda")

    for seed in seeds:
        torch.manual_seed(seed)
        np.random.seed(seed)
        try:
            model = build_model(arch, n_classes, channels, blocks, kernel, dilation_base).to(args.device)
        except (RuntimeError, torch.cuda.OutOfMemoryError):  # pragma: no cover - hardware dependent
            torch.cuda.empty_cache()
            return None
        opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-2)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)

        def predict(inputs):
            model.eval()
            chunks = []
            with torch.no_grad():
                for i in range(0, len(inputs), args.eval_batch):
                    batch = inputs[i : i + args.eval_batch].to(args.device)
                    if use_amp:
                        with torch.autocast("cuda", dtype=torch.bfloat16):
                            logits = model(batch)
                    else:
                        logits = model(batch)
                    chunks.append(torch.softmax(logits.float(), -1).cpu().numpy())
            model.train()
            prob = np.vstack(chunks)
            return prob.argmax(1), prob

        best = (-math.inf, 0, None, None)
        no_improve = 0
        try:
            for epoch in range(1, args.epochs + 1):
                order = torch.randperm(len(x_train))
                for i in range(0, len(order) - args.batch_size + 1, args.batch_size):
                    idx = order[i : i + args.batch_size]
                    inputs = x_train[idx].to(args.device)
                    targets = y_train[idx].to(args.device)
                    if use_amp:
                        with torch.autocast("cuda", dtype=torch.bfloat16):
                            loss = F.cross_entropy(model(inputs), targets)
                    else:
                        loss = F.cross_entropy(model(inputs), targets)
                    opt.zero_grad()
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    opt.step()
                sched.step()
                val_pred, val_prob = predict(x_val)
                val_score = score(y_val.numpy(), val_pred, val_prob, metric)
                if val_score > best[0] + 5e-4:
                    test_pred, test_prob = predict(x_test)
                    best = (val_score, epoch, test_pred, test_prob)
                    no_improve = 0
                else:
                    no_improve += 1
                    if epoch >= args.min_epochs and no_improve >= args.patience:
                        break
        except torch.cuda.OutOfMemoryError:  # pragma: no cover - hardware dependent
            torch.cuda.empty_cache()
            del model
            return None

        test_score = score(y_test.numpy(), best[2], best[3], metric)
        record = {"seed": int(seed), "val": round(best[0], 4),
                  "test": round(test_score, 4), "best_epoch": int(best[1])}
        if save_prefix:
            os.makedirs(os.path.dirname(os.path.abspath(save_prefix)) or ".", exist_ok=True)
            path = f"{save_prefix}__s{seed}__preds.npz"
            np.savez_compressed(path, y_true=y_test.numpy(), y_pred=best[2], y_prob=best[3])
            record["predictions_path"] = path
        per_seed.append(record)
        del model
        if use_amp:
            torch.cuda.empty_cache()
    return per_seed


def summarize(arch: str, channels: int, blocks: int, kernel: int, dilation_base: Optional[int],
              lr: float, per_seed: list[dict], n_classes: int) -> dict:
    params = sum(p.numel() for p in build_model(arch, n_classes, channels, blocks,
                                                kernel, dilation_base).parameters())
    tests = [row["test"] for row in per_seed]
    return {
        "arch": arch, "channels": channels, "blocks": blocks, "kernel": kernel,
        "dilation_base": dilation_base, "lr": lr, "params": int(params),
        "receptive_field_bp": receptive_field(arch, blocks, kernel, dilation_base),
        "val": round(float(np.mean([row["val"] for row in per_seed])), 4),
        "test": round(float(np.mean(tests)), 4),
        "test_sd": round(float(np.std(tests, ddof=1)), 4) if len(tests) > 1 else None,
        "n_seeds": len(per_seed), "runs": per_seed,
    }


def search_task(task: str, split_type: str, records: list[Record], args) -> Optional[dict]:
    """Three-stage search: capacity -> receptive field -> learning rate."""
    import torch

    labels = sorted({record.label for record in records})
    if len(labels) < 2:
        print(f"[cnn] skip task={task} split_type={split_type}: fewer than two classes")
        return None
    label_to_id = {label: idx for idx, label in enumerate(labels)}
    by_split: dict[str, list[Record]] = {"train": [], "val": [], "test": []}
    for record in records:
        by_split[record.split].append(record)
    if not all(by_split[name] for name in ("train", "val", "test")):
        print(f"[cnn] skip task={task} split_type={split_type}: missing a split")
        return None

    length = args.seqlen or max(len(record.sequence) for record in records)
    tensors = {}
    for name, rows in by_split.items():
        tensors[name] = (
            torch.from_numpy(encode([r.sequence for r in rows], length)),
            torch.tensor([label_to_id[r.label] for r in rows], dtype=torch.long),
        )
    n_classes = len(labels)
    metric = args.metric
    print(f"[cnn] task={task} split_type={split_type} classes={n_classes} "
          f"train={len(by_split['train'])} val={len(by_split['val'])} "
          f"test={len(by_split['test'])} seqlen={length} metric={metric}", flush=True)

    ladder: list[dict] = []
    base_lr = args.lrs[0]

    # Stage 1 -- capacity, default kernel/dilation, base LR, one seed.
    stage1: list[dict] = []
    for arch, channels, blocks in LADDER:
        default_db = 1 if arch == "resnet" else 2
        per_seed = train_cell(arch, channels, blocks, args.default_kernel, default_db,
                              base_lr, args.seeds[:1], tensors, n_classes, metric, args)
        if per_seed is None:
            print(f"  [s1] {arch}-{channels}x{blocks}: OOM, skipped", flush=True)
            continue
        row = summarize(arch, channels, blocks, args.default_kernel, default_db,
                        base_lr, per_seed, n_classes)
        row["stage"] = "capacity"
        stage1.append(row)
        ladder.append(row)
        print(f"  [s1] {arch:<8} ch={channels:<4} nb={blocks} {row['params']/1e6:6.2f}M "
              f"RF={row['receptive_field_bp']} val={row['val']:.4f} test={row['test']:.4f}", flush=True)
    if not stage1:
        print(f"[cnn] task={task}: every capacity cell failed")
        return None
    top1 = sorted(stage1, key=lambda r: -r["val"])[: args.topk_capacity]

    # Stage 2 -- receptive field: kernel x dilation base at ~zero parameter cost.
    stage2 = list(top1)
    for parent in top1:
        if parent["arch"] == "unet":
            combos = [(k, 1) for k in args.kernels]          # U-Net has no dilation axis
        else:
            combos = [(k, db) for k in args.kernels for db in args.dilation_bases]
        default_db = 1 if parent["arch"] == "resnet" else 2
        for kernel, dilation_base in combos:
            if kernel == args.default_kernel and dilation_base == default_db:
                continue                                      # already measured in stage 1
            per_seed = train_cell(parent["arch"], parent["channels"], parent["blocks"],
                                  kernel, dilation_base, base_lr, args.seeds[:1],
                                  tensors, n_classes, metric, args)
            if per_seed is None:
                continue
            row = summarize(parent["arch"], parent["channels"], parent["blocks"],
                            kernel, dilation_base, base_lr, per_seed, n_classes)
            row["stage"] = "receptive_field"
            stage2.append(row)
            ladder.append(row)
            print(f"  [s2] {parent['arch']:<8} k={kernel:<3} d={dilation_base} "
                  f"RF={row['receptive_field_bp']} val={row['val']:.4f} test={row['test']:.4f}", flush=True)
    top2 = sorted(stage2, key=lambda r: -r["val"])[: args.topk_receptive_field]

    # Stage 3 -- learning rate at the same budget the model under test received.
    for parent in top2:
        for lr in args.lrs:
            seeds = args.seeds if lr != base_lr else args.seeds[1:]
            if not seeds:
                continue
            per_seed = train_cell(parent["arch"], parent["channels"], parent["blocks"],
                                  parent["kernel"], parent["dilation_base"], lr, seeds,
                                  tensors, n_classes, metric, args)
            if per_seed is None:
                continue
            if lr == base_lr:
                per_seed = parent["runs"] + per_seed
            row = summarize(parent["arch"], parent["channels"], parent["blocks"],
                            parent["kernel"], parent["dilation_base"], lr, per_seed, n_classes)
            row["stage"] = "learning_rate"
            ladder.append(row)
            print(f"  [s3] {parent['arch']:<8} k={parent['kernel']:<3} "
                  f"d={parent['dilation_base']} lr={lr:<8g} val={row['val']:.4f} "
                  f"test={row['test']:.4f}", flush=True)

    dev_selected = max(ladder, key=lambda r: r["val"])

    # Refit the dev-selected cell at several seeds. A 1-seed number is not an estimate.
    if args.refit_seeds and dev_selected["n_seeds"] < args.refit_seeds:
        seeds = list(range(args.seeds[0], args.seeds[0] + args.refit_seeds))
        print(f"  [refit] dev-selected cell at {args.refit_seeds} seeds", flush=True)
        prefix = (os.path.join(args.predictions_dir, f"{task}__{split_type}__cnn_ceiling")
                  if args.predictions_dir else None)
        per_seed = train_cell(dev_selected["arch"], dev_selected["channels"], dev_selected["blocks"],
                              dev_selected["kernel"], dev_selected["dilation_base"],
                              dev_selected["lr"], seeds, tensors, n_classes, metric, args,
                              save_prefix=prefix)
        if per_seed:
            refit = summarize(dev_selected["arch"], dev_selected["channels"], dev_selected["blocks"],
                              dev_selected["kernel"], dev_selected["dilation_base"],
                              dev_selected["lr"], per_seed, n_classes)
            refit["stage"] = "refit"
            ladder.append(refit)
            dev_selected = refit
            print(f"  [refit] test={refit['test']:.4f} +/-{refit['test_sd']} "
                  f"over {refit['n_seeds']} seeds", flush=True)

    finite = [r["test"] for r in ladder if r["test"] is not None and math.isfinite(r["test"])]
    return {
        "task": task,
        "split_type": split_type,
        "benchmark": records[0].benchmark,
        "group": records[0].group,
        "metric": metric,
        "n_classes": n_classes,
        "seqlen": length,
        "n_train": len(by_split["train"]),
        "n_val": len(by_split["val"]),
        "n_test": len(by_split["test"]),
        "ladder": ladder,
        "dev_selected": dev_selected,
        "oracle_best_test": max(finite) if finite else None,
    }


def rows_for_csv(result: dict) -> Iterable[dict]:
    selected = result["dev_selected"]
    for row in result["ladder"]:
        yield {
            "benchmark": result["benchmark"],
            "task": result["task"],
            "split_type": result["split_type"],
            "group": result["group"],
            "baseline": "cnn_ceiling",
            "stage": row.get("stage", ""),
            "arch": row["arch"],
            "channels": row["channels"],
            "blocks": row["blocks"],
            "kernel": row["kernel"],
            "dilation_base": row["dilation_base"],
            "receptive_field_bp": row["receptive_field_bp"],
            "params": row["params"],
            "lr": row["lr"],
            "n_seeds": row["n_seeds"],
            "seqlen": result["seqlen"],
            "n_train": result["n_train"],
            "n_val": result["n_val"],
            "n_test": result["n_test"],
            "selection_metric": result["metric"],
            "val_score": row["val"],
            "test_score": row["test"],
            "test_score_sd": row["test_sd"],
            "is_dev_selected": int(row is selected),
            "oracle_best_test": result["oracle_best_test"],
        }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--benchmark-manifest", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", default="")
    parser.add_argument("--metadata-path", default="")
    parser.add_argument("--task-filter", default="")
    parser.add_argument("--default-benchmark", default="unspecified")
    parser.add_argument("--default-task", default="unspecified")
    parser.add_argument("--default-group", default="")
    parser.add_argument("--metric", default="mcc", choices=["mcc", "macro_f1", "auroc"])
    parser.add_argument("--max-length", type=int, default=0, help="0 = no truncation")
    parser.add_argument("--seqlen", type=int, default=0, help="0 = longest sequence in the task")
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43])
    parser.add_argument("--refit-seeds", type=int, default=3,
                        help="re-run the dev-selected cell at N seeds; <3 is not an estimate")
    parser.add_argument("--predictions-dir", default="",
                        help="save per-seed test predictions for the dev-selected cell; "
                             "required for a paired bootstrap against the model arm")
    parser.add_argument("--lrs", nargs="+", type=float, default=[1e-3, 3e-4, 3e-3])
    parser.add_argument("--kernels", nargs="+", type=int, default=[5, 9, 15, 21])
    parser.add_argument("--dilation-bases", nargs="+", type=int, default=[1, 2, 4])
    parser.add_argument("--default-kernel", type=int, default=9)
    parser.add_argument("--topk-capacity", type=int, default=3)
    parser.add_argument("--topk-receptive-field", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--min-epochs", type=int, default=8,
                        help="floor before early stopping can fire; too low truncates seeds")
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--eval-batch", type=int, default=256)
    parser.add_argument("--device", default="cuda:0")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    records = read_manifest(args)
    if not records:
        print("[cnn] manifest produced no usable rows")
        return 1

    grouped: dict[tuple[str, str], list[Record]] = {}
    for record in records:
        grouped.setdefault((record.task, record.split_type), []).append(record)

    results = []
    for (task, split_type), rows in sorted(grouped.items()):
        result = search_task(task, split_type, rows, args)
        if result is not None:
            results.append(result)

    if not results:
        print("[cnn] no task produced a result")
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out_csv)) or ".", exist_ok=True)
    with open(args.out_csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        for result in results:
            for row in rows_for_csv(result):
                writer.writerow(row)
    print(f"[cnn] wrote {args.out_csv}")

    if args.out_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.out_json)) or ".", exist_ok=True)
        with open(args.out_json, "w") as handle:
            json.dump(results, handle, indent=2)
        print(f"[cnn] wrote {args.out_json}")

    if args.metadata_path:
        write_metadata(args.metadata_path, build_run_metadata(
            args=args,
            data_paths=[args.benchmark_manifest],
            extra={"baseline": "cnn_ceiling", "n_tasks": len(results)},
        ))
        print(f"[cnn] wrote {args.metadata_path}")

    for result in results:
        selected = result["dev_selected"]
        print(f"[cnn] {result['task']} / {result['split_type']}: "
              f"dev-selected {selected['arch']} {selected['params']/1e6:.2f}M "
              f"k={selected['kernel']} d={selected['dilation_base']} "
              f"RF={selected['receptive_field_bp']} -> test {selected['test']} "
              f"+/-{selected['test_sd']} ({selected['n_seeds']} seeds), "
              f"oracle-best {result['oracle_best_test']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
