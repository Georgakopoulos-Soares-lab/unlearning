"""Convert a labeled FASTA file (headers with label=/split= fields) into
train/val/test JSONL files, each line {"sequence": "...", "label": 0/1},
as required by BioNeMo's official evo2_classifier.py example.

Usage:
    python fasta_to_jsonl.py \
        --fasta-path /projects/MENTISLab/unlearning/data/evo2/benchmarks/hvue_gue_manifest.fasta \
        --output-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/jsonl
"""

import argparse
import json
import re
from pathlib import Path


_HEADER_KV_RE = re.compile(r"(\w+)=(\S+)")


def convert(fasta_path: Path, output_dir: Path, label_key: str, split_key: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    writers = {
        split: open(output_dir / f"{split}.jsonl", "w")
        for split in ("train", "val", "test")
    }
    counts = {split: 0 for split in writers}

    current_header_kv: dict[str, str] | None = None
    current_seq_parts: list[str] = []

    def _flush():
        if current_header_kv is None:
            return
        split = current_header_kv.get(split_key)
        if split not in writers:
            return  # header present but no recognized split= value -- skip
        if label_key not in current_header_kv:
            return  # no label -- skip (shouldn't happen given our data, but be safe)
        sequence = "".join(current_seq_parts).upper()
        label = int(current_header_kv[label_key])
        writers[split].write(json.dumps({"sequence": sequence, "label": label}) + "\n")
        counts[split] += 1

    with open(fasta_path) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            if line.startswith(">"):
                _flush()
                header = line[1:]
                current_header_kv = dict(_HEADER_KV_RE.findall(header))
                current_seq_parts = []
            else:
                current_seq_parts.append(line)
        _flush()  # last record

    for split, w in writers.items():
        w.close()

    print("Wrote:")
    for split, n in counts.items():
        print(f"  {split}.jsonl: {n} sequences -> {output_dir / f'{split}.jsonl'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--fasta-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--label-key", default="label")
    parser.add_argument("--split-key", default="split")
    args = parser.parse_args()
    convert(args.fasta_path, args.output_dir, args.label_key, args.split_key)
