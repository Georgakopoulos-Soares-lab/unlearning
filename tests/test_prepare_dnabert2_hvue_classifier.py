import csv
import json
from pathlib import Path

from phase2_dnabert2.prepare_hvue_classifier import main, read_task_rows


def write_manifest(path: Path) -> None:
    rows = [
        {"id": "a", "task": "hvue_human_host_tropism", "split": "train", "sequence": "acgtnxyz", "label": "1"},
        {"id": "b", "task": "hvue_human_host_tropism", "split": "validation", "sequence": "tttt", "label": "0.0"},
        {"id": "c", "task": "hvue_human_host_tropism", "split": "test", "sequence": "cccc", "label": "1.0"},
        {"id": "d", "task": "other", "split": "train", "sequence": "aaaa", "label": "1"},
    ]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "task", "split", "sequence", "label"])
        writer.writeheader()
        writer.writerows(rows)


def test_read_task_rows_filters_and_cleans(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest)
    rows = read_task_rows(manifest, "hvue_human_host_tropism", max_length=5)
    assert [row["id"] for row in rows] == ["a", "b", "c"]
    assert rows[0]["sequence"] == "ACGTN"
    assert rows[1]["split"] == "val"
    assert rows[1]["label_raw"] == "0"


def test_main_writes_three_splits_and_metadata(tmp_path: Path, monkeypatch) -> None:
    manifest = tmp_path / "manifest.csv"
    out_dir = tmp_path / "dnabert2"
    write_manifest(manifest)
    monkeypatch.setattr(
        "sys.argv",
        [
            "prepare_hvue_classifier.py",
            "--manifest",
            str(manifest),
            "--out-dir",
            str(out_dir),
            "--max-length",
            "4",
        ],
    )
    main()
    for split in ("train", "val", "test"):
        assert (out_dir / f"host_tropism_{split}.jsonl").exists()
    metadata = json.loads((out_dir / "host_tropism_metadata.json").read_text())
    assert metadata["splits"]["train"]["rows"] == 1
    assert metadata["label_to_id"] == {"0": 0, "1": 1}
