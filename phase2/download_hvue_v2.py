#!/usr/bin/env python3
"""Download the HVUE-v2 CSV files while preserving their Hub layout."""

from __future__ import annotations

import argparse
from pathlib import Path

from huggingface_hub import snapshot_download


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download all CSV splits from duttaprat/HVUE-v2."
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/benchmarks/raw/hvue_v2"),
        help="Destination directory (default: data/benchmarks/raw/hvue_v2).",
    )
    parser.add_argument(
        "--revision",
        default="main",
        help="Hub branch, tag, or commit to download (default: main).",
    )
    args = parser.parse_args()

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    downloaded_path = snapshot_download(
        repo_id="duttaprat/HVUE-v2",
        repo_type="dataset",
        revision=args.revision,
        local_dir=out_dir,
        allow_patterns=["*.csv"],
    )

    csv_files = sorted(out_dir.rglob("*.csv"))
    print(f"[download_hvue_v2] downloaded {len(csv_files)} CSV files")
    print(f"[download_hvue_v2] output: {downloaded_path}")


if __name__ == "__main__":
    main()
