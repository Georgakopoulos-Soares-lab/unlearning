"""Build DNABERT-2 forget/retain JSONL splits from prepared HVUE data."""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


DEFAULT_DATA_DIR = "data/dnabert2/hvue"
DEFAULT_OUT_DIR = "data/dnabert2/unlearn_splits"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def split_rows(rows: list[dict[str, Any]], forget_label: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    forget = []
    retain = []
    for row in rows:
        target = forget if int(row["label"]) == forget_label else retain
        target.append(row)
    return forget, retain


def sample_rows(rows: list[dict[str, Any]], max_rows: int, seed: int) -> list[dict[str, Any]]:
    if max_rows <= 0 or len(rows) <= max_rows:
        return list(rows)
    rng = random.Random(seed)
    sampled = list(rows)
    rng.shuffle(sampled)
    return sampled[:max_rows]


def summarize(rows_by_name: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    summary = {}
    for name, rows in sorted(rows_by_name.items()):
        summary[name] = {
            "rows": len(rows),
            "label_counts": dict(sorted(Counter(str(row["label"]) for row in rows).items())),
            "split_counts": dict(sorted(Counter(str(row.get("split", "")) for row in rows).items())),
        }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--prefix", default="host_tropism")
    parser.add_argument("--forget-label", type=int, default=1)
    parser.add_argument("--forget-max-train", type=int, default=0)
    parser.add_argument("--retain-max-train", type=int, default=0)
    parser.add_argument("--seed", type=int, default=13)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    out_dir = Path(args.out_dir)
    all_outputs: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "val", "test"):
        rows = read_jsonl(data_dir / f"{args.prefix}_{split}.jsonl")
        forget, retain = split_rows(rows, args.forget_label)
        if split == "train":
            forget = sample_rows(forget, args.forget_max_train, args.seed)
            retain = sample_rows(retain, args.retain_max_train, args.seed + 1)
        forget_path = out_dir / f"forget_{split}.jsonl"
        retain_path = out_dir / f"retain_{split}.jsonl"
        write_jsonl(forget_path, forget)
        write_jsonl(retain_path, retain)
        all_outputs[f"forget_{split}"] = forget
        all_outputs[f"retain_{split}"] = retain
    metadata = {
        "source_data_dir": str(data_dir),
        "forget_label": args.forget_label,
        "forget_max_train": args.forget_max_train,
        "retain_max_train": args.retain_max_train,
        "seed": args.seed,
        "summary": summarize(all_outputs),
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    print(f"[dnabert2-unlearn] wrote {out_dir / 'metadata.json'}")


if __name__ == "__main__":
    main()
