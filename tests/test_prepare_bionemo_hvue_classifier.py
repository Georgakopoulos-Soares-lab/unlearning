from __future__ import annotations

import csv
import json
from pathlib import Path

from phase2_evo2.prepare_bionemo_hvue_classifier import (
    label_mapping,
    normalize_split,
    read_task_rows,
    write_jsonl,
)


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_read_task_rows_filters_normalizes_and_truncates(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    write_manifest(
        manifest,
        [
            {
                "benchmark": "hvue",
                "task": "hvue_human_host_tropism",
                "split": "dev",
                "sequence": "acgtxyz",
                "label": "1.0",
                "family": "",
                "group": "hvue_forget",
                "id": "keep",
            },
            {
                "benchmark": "hvue",
                "task": "other",
                "split": "dev",
                "sequence": "AAAA",
                "label": "0",
                "family": "",
                "group": "",
                "id": "drop-task",
            },
            {
                "benchmark": "hvue",
                "task": "hvue_human_host_tropism",
                "split": "holdout",
                "sequence": "AAAA",
                "label": "0",
                "family": "",
                "group": "",
                "id": "drop-split",
            },
        ],
    )

    rows = read_task_rows(manifest, "hvue_human_host_tropism", max_length=3)

    assert len(rows) == 1
    assert rows[0]["id"] == "keep"
    assert rows[0]["split"] == "val"
    assert rows[0]["sequence"] == "ACG"
    assert rows[0]["label_raw"] == "1"
    assert rows[0]["length"] == 3


def test_write_jsonl_uses_stable_integer_label_mapping(tmp_path: Path) -> None:
    rows = [
        {
            "id": "b",
            "task": "task",
            "split": "train",
            "sequence": "CCCC",
            "label_raw": "1",
            "family": "",
            "group": "",
        },
        {
            "id": "a",
            "task": "task",
            "split": "train",
            "sequence": "AAAA",
            "label_raw": "0",
            "family": "",
            "group": "",
        },
    ]
    labels = label_mapping(row["label_raw"] for row in rows)
    out = tmp_path / "train.jsonl"

    write_jsonl(out, rows, labels)

    parsed = [json.loads(line) for line in out.read_text().splitlines()]
    assert labels == {"0": 0, "1": 1}
    assert parsed[0]["label"] == 1
    assert parsed[1]["label"] == 0
    assert parsed[0]["sequence"] == "CCCC"


def test_normalize_split_accepts_validation_aliases() -> None:
    assert normalize_split("dev") == "val"
    assert normalize_split("validation") == "val"
    assert normalize_split("test") == "test"
