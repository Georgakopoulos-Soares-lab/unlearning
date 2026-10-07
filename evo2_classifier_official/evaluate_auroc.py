"""Evaluate a trained evo2_classifier.py checkpoint: AUROC + accuracy on a JSONL split.

Must be run with the same launcher (torchrun) and environment as training,
since predict() initializes torch.distributed internally.

Usage:
    torchrun --nproc-per-node 1 evaluate_auroc.py \
        --ckpt-dir /projects/MENTISLab/unlearning/results/evo2_official/head_only/checkpoints \
        --jsonl /projects/MENTISLab/unlearning/data/evo2/benchmarks/jsonl/test.jsonl \
        --micro-batch-size 64
"""

import argparse
import json
from pathlib import Path

import torch
import torch.nn.functional as F  # noqa: N812
from sklearn.metrics import roc_auc_score, accuracy_score

from evo2_classifier import predict


def _read_jsonl(path: Path) -> tuple[list[str], list[int]]:
    sequences, labels = [], []
    with open(path) as f:
        for line in f:
            obj = json.loads(line)
            sequences.append(obj["sequence"])
            labels.append(int(obj["label"]))
    return sequences, labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ckpt-dir", type=Path, required=True, help="Path to the trained checkpoint directory (parent of iter_* subdirs).")
    parser.add_argument("--jsonl", type=Path, required=True, help="JSONL file with {sequence, label} to evaluate on.")
    parser.add_argument("--micro-batch-size", type=int, default=64)
    args = parser.parse_args()

    sequences, labels = _read_jsonl(args.jsonl)
    print(f"Loaded {len(sequences)} sequences from {args.jsonl}")

    result = predict(
        trained_ckpt_dir=args.ckpt_dir,
        sequences=sequences,
        micro_batch_size=args.micro_batch_size,
        return_logits=True,
    )

    logits = result["logits"]  # [N, num_classes], CPU tensor
    preds = result["predictions"]  # [N], argmax already computed by predict()
    labels_t = torch.tensor(labels, dtype=torch.long)

    probs = F.softmax(logits.float(), dim=-1)
    positive_class_probs = probs[:, 1]  # P(label=1) -- assumes binary, label 1 is "positive"

    auroc = roc_auc_score(labels_t.numpy(), positive_class_probs.numpy())
    acc = accuracy_score(labels_t.numpy(), preds.numpy())

    print()
    print("=" * 60)
    print(f"N examples:  {len(sequences)}")
    print(f"AUROC:       {auroc:.4f}")
    print(f"Accuracy:    {acc:.4f}")
    print(f"Class balance in this split: {labels_t.float().mean().item():.4f} positive")
    print("=" * 60)


if __name__ == "__main__":
    main()
