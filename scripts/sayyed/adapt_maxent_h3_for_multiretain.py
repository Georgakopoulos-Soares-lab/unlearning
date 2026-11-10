"""Create a consumer-owned, lossless verification view of historical H3 outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

from scripts.sayyed.multiretain_verifier import read_csv, read_jsonl, sha256


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--layer", choices=["final_norm", "decoder_layer_16"], required=True)
    parser.add_argument("--split", choices=["dev", "test"], required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = read_jsonl(args.manifest)
    by_id = {row["id"]: row for row in manifest}
    source_predictions = read_jsonl(args.source / "predictions.jsonl")
    predictions = []
    for row in source_predictions:
        if row["layer"] != args.layer or row["split"] != args.split:
            continue
        reference = by_id[row["id"]]
        predictions.append(
            {
                "id": row["id"],
                "task": reference["task"],
                "split": row["split"],
                "label": row["label"],
                "group": row["group"],
                "sequence_sha256": reference["sequence_sha256"],
                "classes": [0, 1],
                "probabilities": {
                    name: [1.0 - float(value), float(value)]
                    for name, value in row["probabilities"].items()
                },
            }
        )
    prediction_path = args.output / "predictions.jsonl"
    write_jsonl(prediction_path, predictions)
    metric_rows = [
        row
        for row in read_csv(args.source / "metrics.csv")
        if row["split"] == args.split and row["layer"] == args.layer
    ]
    metric_path = args.output / "metrics.csv"
    with metric_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metric_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(metric_rows)
    protocol_path = args.output / "protocol.json"
    protocol_path.write_text(
        json.dumps(
            {
                "manifest_sha256": sha256(args.manifest),
                "bootstrap_seed": 20261103,
                "bootstrap_resamples": 2000,
                "adaptation": "scalar class-1 to [class0,class1]; sequence hash joined by ID; singleton groups use explicit original row order",
                "historical": True,
                "new_measurement": False,
            },
            indent=2,
        )
        + "\n"
    )
    with np.load(args.source / f"{args.layer}_{args.split}_bootstrap.npz", allow_pickle=False) as saved:
        ids = saved["ids"].astype(str).tolist()
        if ids != [row["id"] for row in predictions]:
            raise ValueError("Historical bootstrap ID order mismatch")
        group_names = np.asarray([row["group"] for row in predictions])
        row_groups = np.arange(len(predictions), dtype=np.int32)
        group_draws = saved["indices"]
        arrays = {name: saved[name] for name in ("maxent_refit", "maxent_fixed_base")}
    bootstrap_path = args.output / "bootstrap.npz"
    np.savez(
        bootstrap_path,
        ids=np.asarray(ids),
        group_names=group_names,
        row_groups=row_groups,
        group_draws=group_draws,
        **arrays,
    )
    comparisons = [
        row
        for row in read_csv(args.source / "paired_comparisons.csv")
        if row["split"] == args.split and row["layer"] == args.layer
    ]
    contrast_path = args.output / "paired_comparisons.csv"
    with contrast_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(comparisons)
    roles = {
        "protocol": protocol_path,
        "manifest": args.manifest,
        "predictions": prediction_path,
        "metrics": metric_path,
        "folds": args.source / "folds.json",
        "contrasts": contrast_path,
        "bootstrap": bootstrap_path,
    }
    receipt = {
        "schema": "multiretain-unit-v1",
        "status": "COMPLETE",
        "unit": {
            "task": "emp_H3",
            "split": args.split,
            "checkpoint": "base_and_h3_only_maxent",
            "layer": args.layer,
            "seed": 42,
            "probe_policy": "independent_refit_and_fixed_base",
        },
        "historical_adaptation": True,
        "source": str(args.source),
        "baseline_probe": "base_refit",
        "files": [
            {
                "role": role,
                "path": str(path.resolve()),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for role, path in roles.items()
        ],
    }
    (args.output / "COMPLETE.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"ADAPTED {len(predictions)} historical rows into {args.output}")


if __name__ == "__main__":
    main()
