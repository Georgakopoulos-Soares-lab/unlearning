"""Extract only split=train sequences from the labeled manifest FASTA into a
plain (unlabeled) FASTA, for causal-LM continued-pretraining fine-tuning via
train_evo2.py --fasta-data. Keeps val/test sequences out entirely, so they
stay unseen for any later classification-style evaluation.

Usage:
    python extract_train_only_fasta.py \
        --input-fasta /projects/MENTISLab/unlearning/data/evo2/benchmarks/hvue_gue_manifest.fasta \
        --output-fasta /projects/MENTISLab/unlearning/data/evo2/benchmarks/hvue_train_only.fasta \
        --split-key split --train-value train
"""

import argparse
import re
from pathlib import Path


_HEADER_KV_RE = re.compile(r"(\w+)=(\S+)")


def extract(input_fasta: Path, output_fasta: Path, split_key: str, train_value: str) -> None:
    n_written = 0
    n_total = 0
    keep = False
    with open(input_fasta) as fin, open(output_fasta, "w") as fout:
        for line in fin:
            if line.startswith(">"):
                n_total += 1
                header_kv = dict(_HEADER_KV_RE.findall(line[1:]))
                keep = header_kv.get(split_key) == train_value
                if keep:
                    n_written += 1
                    seqid = line[1:].split()[0]
                    fout.write(f">{seqid}\n")
            elif keep:
                fout.write(line)
    print(f"Wrote {n_written}/{n_total} sequences (split={train_value!r}) to {output_fasta}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-fasta", type=Path, required=True)
    parser.add_argument("--output-fasta", type=Path, required=True)
    parser.add_argument("--split-key", default="split")
    parser.add_argument("--train-value", default="train")
    args = parser.parse_args()
    extract(args.input_fasta, args.output_fasta, args.split_key, args.train_value)
