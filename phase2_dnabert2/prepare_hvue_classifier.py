"""Prepare HVUE JSONL splits for DNABERT-2 sequence classification."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


csv.field_size_limit(sys.maxsize)

DEFAULT_TASK = "hvue_human_host_tropism"
DEFAULT_INPUT = "data/evo2/benchmarks/hvue_gue_manifest.csv"
DEFAULT_OUT_DIR = "data/dnabert2/hvue"


def normalize_split(value: object) -> str:
    split = str(value or "").strip().lower()
    if split in {"dev", "valid", "validation"}:
        return "val"
    return split


def clean_sequence(value: object, max_length: int) -> str:
    sequence = str(value or "").upper()
    sequence = "".join(base for base in sequence if base in {"A", "C", "G", "T", "N"})
    if max_length > 0:
        sequence = sequence[:max_length]
    return sequence


def normalize_label(value: object) -> str:
    label = str(value or "").strip()
    if not label or label.lower() in {"nan", "na", "none", "null"}:
        return ""
    try:
        numeric = float(label)
    except ValueError:
        return label
    if not math.isfinite(numeric):
        return ""
    if numeric.is_integer():
        return str(int(numeric))
    return format(numeric, "g")


def label_mapping(labels: Iterable[str]) -> dict[str, int]:
    return {label: idx for idx, label in enumerate(sorted(set(labels)))}


def read_task_rows(path: Path, task: str, max_length: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"task", "split", "sequence", "label"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Manifest missing required columns: {sorted(missing)}")
        for index, row in enumerate(reader):
            if row.get("task") != task:
                continue
            split = normalize_split(row.get("split"))
            if split not in {"train", "val", "test"}:
                continue
            sequence = clean_sequence(row.get("sequence"), max_length)
            label = normalize_label(row.get("label"))
            if not sequence or not label:
                continue
            rows.append(
                {
                    "id": row.get("id") or row.get("record_id") or f"{task}|{split}|{index}",
                    "task": task,
                    "split": split,
                    "sequence": sequence,
                    "label_raw": label,
                    "raw_length": len(str(row.get("sequence") or "")),
                    "length": len(sequence),
                    "family": row.get("family", ""),
                    "group": row.get("group", ""),
                }
            )
    return rows


def write_jsonl(path: Path, rows: list[dict[str, object]], labels: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(
                json.dumps(
                    {
                        "id": row["id"],
                        "sequence": row["sequence"],
                        "label": labels[str(row["label_raw"])],
                        "label_raw": row["label_raw"],
                        "task": row["task"],
                        "split": row["split"],
                        "family": row.get("family", ""),
                        "group": row.get("group", ""),
                    },
                    sort_keys=True,
                )
                + "\n"
            )


def summarize(rows: list[dict[str, object]], labels: dict[str, int], max_length: int) -> dict[str, object]:
    by_split: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_split[str(row["split"])].append(row)
    splits = {}
    for split, split_rows in sorted(by_split.items()):
        lengths = [int(row["length"]) for row in split_rows]
        splits[split] = {
            "rows": len(split_rows),
            "label_counts_raw": dict(sorted(Counter(str(row["label_raw"]) for row in split_rows).items())),
            "label_counts_encoded": dict(sorted(Counter(str(labels[str(row["label_raw"])]) for row in split_rows).items())),
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0,
            "mean_length": (sum(lengths) / len(lengths)) if lengths else 0,
            "truncated_rows": sum(int(row["raw_length"]) > int(row["length"]) for row in split_rows),
        }
    return {
        "task": rows[0]["task"] if rows else "",
        "max_length": max_length,
        "label_to_id": labels,
        "id_to_label": {str(value): key for key, value in labels.items()},
        "splits": splits,
        "total_rows": len(rows),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=DEFAULT_INPUT)
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--prefix", default="host_tropism")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = read_task_rows(Path(args.manifest), args.task, args.max_length)
    if not rows:
        raise RuntimeError(f"No usable rows found for task={args.task!r} in {args.manifest}")
    labels = label_mapping(str(row["label_raw"]) for row in rows)
    by_split: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_split[str(row["split"])].append(row)
    missing = {"train", "val", "test"} - set(by_split)
    if missing:
        raise RuntimeError(f"Missing required splits: {sorted(missing)}")
    out_dir = Path(args.out_dir)
    for split in ("train", "val", "test"):
        write_jsonl(out_dir / f"{args.prefix}_{split}.jsonl", by_split[split], labels)
    summary = summarize(rows, labels, args.max_length)
    summary["files"] = {split: str(out_dir / f"{args.prefix}_{split}.jsonl") for split in ("train", "val", "test")}
    summary_path = out_dir / f"{args.prefix}_metadata.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"[dnabert2-hvue] wrote {summary_path}")


if __name__ == "__main__":
    main()
