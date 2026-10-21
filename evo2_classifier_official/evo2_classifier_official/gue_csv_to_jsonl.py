import csv
import json
import argparse
from pathlib import Path


def gue_csv_to_jsonl(input_dir: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)

    for csv_file in sorted(input_dir.rglob("*.csv")):
        relative = csv_file.relative_to(input_dir)
        out_file = output_dir / relative.with_suffix(".jsonl")
        out_file.parent.mkdir(parents=True, exist_ok=True)

        with open(csv_file, "r") as f_in, open(out_file, "w") as f_out:
            reader = csv.DictReader(f_in)
            for row in reader:
                seq = row.get("seq") or row.get("sequence")
                if seq is None:
                    raise ValueError(
                        f"No sequence column found in {csv_file}. "
                        f"Columns: {list(row.keys())}"
                    )
                record = {"sequence": seq, "label": int(row["label"])}
                f_out.write(json.dumps(record) + "\n")

        print(f"{csv_file} → {out_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert GUE CSV files to JSONL format."
    )
    parser.add_argument(
        "--input_dir",
        type=Path,
        required=True,
        help="Path to the root GUE directory containing CSV files.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        required=True,
        help="Path to the output directory for JSONL files.",
    )
    args = parser.parse_args()

    if not args.input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {args.input_dir}")

    gue_csv_to_jsonl(args.input_dir, args.output_dir)
    print(f"\nDone. JSONL files written to {args.output_dir}")
