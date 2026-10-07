import json
from pathlib import Path

from phase2_dnabert2.build_unlearn_splits import main, split_rows


def test_split_rows_uses_forget_label() -> None:
    rows = [{"label": 1, "id": "a"}, {"label": 0, "id": "b"}, {"label": 1, "id": "c"}]
    forget, retain = split_rows(rows, forget_label=1)
    assert [row["id"] for row in forget] == ["a", "c"]
    assert [row["id"] for row in retain] == ["b"]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_main_writes_forget_and_retain_splits(tmp_path: Path, monkeypatch) -> None:
    data_dir = tmp_path / "hvue"
    rows = [
        {"id": "p", "sequence": "ACGT", "label": 1, "split": "train"},
        {"id": "n", "sequence": "TGCA", "label": 0, "split": "train"},
    ]
    for split in ("train", "val", "test"):
        split_rows = [{**row, "id": f"{row['id']}_{split}", "split": split} for row in rows]
        write_jsonl(data_dir / f"host_tropism_{split}.jsonl", split_rows)
    out_dir = tmp_path / "splits"
    monkeypatch.setattr(
        "sys.argv",
        [
            "build_unlearn_splits.py",
            "--data-dir",
            str(data_dir),
            "--out-dir",
            str(out_dir),
            "--forget-label",
            "1",
        ],
    )
    main()
    assert (out_dir / "forget_train.jsonl").read_text().count("\n") == 1
    assert (out_dir / "retain_train.jsonl").read_text().count("\n") == 1
    metadata = json.loads((out_dir / "metadata.json").read_text())
    assert metadata["summary"]["forget_train"]["label_counts"] == {"1": 1}
