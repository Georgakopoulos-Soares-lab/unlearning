"""Compare DNABERT-2 HVUE results against existing Evo2/k-mer baselines."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_RUN_ROOT = "data/dnabert2/runs/hvue_host_tropism"
DEFAULT_OUT = "data/dnabert2/runs/hvue_host_tropism/comparison.csv"
KMER_FILES = {
    "kmer_matched_512": "data/evo2/kmer_baselines/hvue_host_tropism_matched_512.csv",
    "kmer_full_sequence": "data/evo2/kmer_baselines/hvue_host_tropism_full_sequence.csv",
}
EVO2_FILE = "data/evo2/base_benchmarks/hvue_host_tropism/eval_benchmarks.csv"


def read_metric_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def pick_metric(row: dict[str, str], *names: str) -> str:
    for name in names:
        if row.get(name) not in {None, ""}:
            return str(row[name])
    return ""


def collect_rows(run_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for name, filename in KMER_FILES.items():
        for row in read_metric_csv(Path(filename)):
            rows.append(
                {
                    "system": name,
                    "mode": "baseline",
                    "split": pick_metric(row, "split") or "test",
                    "auroc": pick_metric(row, "auroc", "test_auroc"),
                    "auprc": pick_metric(row, "auprc", "test_auprc"),
                    "mcc": pick_metric(row, "mcc", "test_mcc"),
                    "accuracy": pick_metric(row, "accuracy", "test_accuracy"),
                    "source": filename,
                }
            )
    for row in read_metric_csv(Path(EVO2_FILE)):
        rows.append(
            {
                "system": "evo2",
                "mode": pick_metric(row, "training_mode") or "frozen_head",
                "split": pick_metric(row, "split") or "test",
                "auroc": pick_metric(row, "auroc", "test_auroc"),
                "auprc": pick_metric(row, "auprc", "test_auprc"),
                "mcc": pick_metric(row, "mcc", "test_mcc"),
                "accuracy": pick_metric(row, "accuracy", "test_accuracy"),
                "source": EVO2_FILE,
            }
        )
    for metrics_path in sorted(run_root.glob("*/eval_metrics.csv")):
        for row in read_metric_csv(metrics_path):
            if row.get("split") != "test":
                continue
            rows.append(
                {
                    "system": "dnabert2",
                    "mode": pick_metric(row, "mode") or metrics_path.parent.name,
                    "split": row.get("split", "test"),
                    "auroc": pick_metric(row, "auroc"),
                    "auprc": pick_metric(row, "auprc"),
                    "mcc": pick_metric(row, "mcc"),
                    "accuracy": pick_metric(row, "accuracy"),
                    "source": str(metrics_path),
                }
            )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", default=DEFAULT_RUN_ROOT)
    parser.add_argument("--out", default=DEFAULT_OUT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = collect_rows(Path(args.run_root))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["system", "mode", "split", "auroc", "auprc", "mcc", "accuracy", "source"]
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"[dnabert2-hvue] wrote {out}")


if __name__ == "__main__":
    main()
