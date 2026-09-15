"""Compare BioNeMo Evo2 HVUE classifier outputs against k-mer baselines."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, average_precision_score, f1_score, roc_auc_score


DEFAULT_KMER_512 = "data/evo2/kmer_baselines/hvue_host_tropism_matched_512.csv"
DEFAULT_KMER_FULL = "data/evo2/kmer_baselines/hvue_host_tropism_full_sequence.csv"
DEFAULT_OUT = "data/evo2/bionemo_runs/hvue_host_tropism/comparison.csv"


def read_first_csv(path: str | Path) -> dict[str, str]:
    with Path(path).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[0] if rows else {}


def read_prediction_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open() as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def pick_column(row: dict[str, Any], candidates: list[str]) -> str:
    for name in candidates:
        if name in row and row[name] not in ("", None):
            return name
    return ""


def score_predictions(path: str | Path, name: str) -> dict[str, Any]:
    rows = read_prediction_rows(Path(path))
    if not rows:
        raise RuntimeError(f"No prediction rows found: {path}")
    first = rows[0]
    label_col = pick_column(first, ["label", "true_label", "target", "y_true", "label_id"])
    score_col = pick_column(
        first,
        [
            "probability_positive",
            "positive_probability",
            "prob_1",
            "score",
            "prediction_score",
            "logit_1",
        ],
    )
    pred_col = pick_column(first, ["predicted_label", "prediction", "pred", "label_pred", "predicted_label_id"])
    if not label_col:
        raise RuntimeError(f"Could not identify label column in {path}; columns={list(first)}")
    if not score_col and not pred_col:
        raise RuntimeError(f"Could not identify score or prediction column in {path}; columns={list(first)}")

    y_true = np.array([int(float(row[label_col])) for row in rows], dtype=np.int64)
    y_score = None
    if score_col:
        y_score = np.array([float(row[score_col]) for row in rows], dtype=float)
        y_pred = (y_score >= 0.5).astype(np.int64)
    else:
        y_pred = np.array([int(float(row[pred_col])) for row in rows], dtype=np.int64)

    result: dict[str, Any] = {
        "method": name,
        "source": str(path),
        "n_test": len(rows),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "auroc": "",
        "auprc": "",
    }
    if y_score is not None and len(set(y_true.tolist())) == 2:
        result["auroc"] = float(roc_auc_score(y_true, y_score))
        result["auprc"] = float(average_precision_score(y_true, y_score))
    return result


def kmer_row(path: str, name: str) -> dict[str, Any]:
    row = read_first_csv(path)
    return {
        "method": name,
        "source": path,
        "n_test": row.get("n_test", ""),
        "accuracy": row.get("accuracy", ""),
        "f1": row.get("f1", ""),
        "auroc": row.get("auroc", ""),
        "auprc": row.get("auprc", ""),
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["method", "source", "n_test", "accuracy", "f1", "auroc", "auprc"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kmer-512", default=DEFAULT_KMER_512)
    parser.add_argument("--kmer-full", default=DEFAULT_KMER_FULL)
    parser.add_argument("--head-predictions", default="")
    parser.add_argument("--lora-predictions", default="")
    parser.add_argument("--out-csv", default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = [
        kmer_row(args.kmer_512, "kmer_512"),
        kmer_row(args.kmer_full, "kmer_full_sequence"),
    ]
    if args.head_predictions:
        rows.append(score_predictions(args.head_predictions, "bionemo_evo2_head_only"))
    if args.lora_predictions:
        rows.append(score_predictions(args.lora_predictions, "bionemo_evo2_lora"))
    write_rows(Path(args.out_csv), rows)
    print(f"[bionemo-hvue] wrote {args.out_csv}")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
