from __future__ import annotations

import csv
from pathlib import Path

import pytest

from phase2.baseline_cnn_ceiling import (
    LADDER,
    encode,
    parse_args,
    read_manifest,
    receptive_field,
    rows_for_csv,
)


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def args(argv: list[str] | None = None):
    return parse_args((argv or []) + ["--benchmark-manifest", "m.csv", "--out-csv", "o.csv"])


def test_receptive_field_grows_with_dilation_base_at_fixed_capacity() -> None:
    """The stage-2 axis: same architecture and parameter count, 11x the receptive field.

    This is why kernel and dilation are swept as first-class axes rather than left at
    defaults -- on a 600bp task the difference was +0.62 MCC.
    """
    assert receptive_field("dilated", 5, 9, 2) == 249
    assert receptive_field("dilated", 5, 9, 4) == 2729
    assert receptive_field("dilated", 5, 9, 4) > 10 * receptive_field("dilated", 5, 9, 2)


def test_unet_receptive_field_is_reported_as_global() -> None:
    assert receptive_field("unet", 3, 9, 2) is None


def test_resnet_receptive_field_counts_two_convs_per_block() -> None:
    # stem (k-1) plus 2*(k-1) per block at dilation 1
    assert receptive_field("resnet", 3, 9, 1) == 1 + 8 + 3 * 16


def test_ladder_spans_three_architecture_families() -> None:
    assert {arch for arch, _, _ in LADDER} == {"dilated", "unet", "resnet"}
    assert len(LADDER) == 13


def test_encode_maps_bases_and_pads_with_the_n_index() -> None:
    encoded = encode(["ACGT", "AC"], 6)
    assert encoded.shape == (2, 6)
    assert list(encoded[0]) == [0, 1, 2, 3, 4, 4]
    assert list(encoded[1]) == [0, 1, 4, 4, 4, 4]


def test_encode_truncates_to_requested_length() -> None:
    assert list(encode(["ACGTACGT"], 3)[0]) == [0, 1, 2]


def test_encode_treats_n_as_the_pad_index() -> None:
    assert list(encode(["ANG"], 3)[0]) == [0, 4, 2]


def test_read_manifest_normalizes_dev_to_val_and_drops_unusable_rows(tmp_path: Path) -> None:
    manifest = tmp_path / "m.csv"
    write_manifest(manifest, [
        {"task": "t", "split": "train", "sequence": "ACGT", "label": "0", "split_type": ""},
        {"task": "t", "split": "dev", "sequence": "ACGT", "label": "1", "split_type": ""},
        {"task": "t", "split": "test", "sequence": "ACGT", "label": "0", "split_type": ""},
        {"task": "t", "split": "train", "sequence": "", "label": "1", "split_type": ""},
        {"task": "t", "split": "train", "sequence": "ACGT", "label": "", "split_type": ""},
        {"task": "t", "split": "holdout", "sequence": "ACGT", "label": "1", "split_type": ""},
    ])
    parsed = parse_args(["--benchmark-manifest", str(manifest), "--out-csv", "o.csv"])
    records = read_manifest(parsed)
    assert len(records) == 3
    assert {r.split for r in records} == {"train", "val", "test"}
    assert {r.split_type for r in records} == {"random"}


def test_read_manifest_rejects_a_manifest_missing_required_columns(tmp_path: Path) -> None:
    manifest = tmp_path / "bad.csv"
    write_manifest(manifest, [{"task": "t", "split": "train", "sequence": "ACGT"}])
    parsed = parse_args(["--benchmark-manifest", str(manifest), "--out-csv", "o.csv"])
    with pytest.raises(ValueError, match="missing required columns"):
        read_manifest(parsed)


def test_read_manifest_honours_the_task_filter(tmp_path: Path) -> None:
    manifest = tmp_path / "m.csv"
    write_manifest(manifest, [
        {"task": "keep", "split": "train", "sequence": "ACGT", "label": "0", "split_type": ""},
        {"task": "drop", "split": "train", "sequence": "ACGT", "label": "0", "split_type": ""},
    ])
    parsed = parse_args(["--benchmark-manifest", str(manifest), "--out-csv", "o.csv",
                         "--task-filter", "keep"])
    assert {r.task for r in read_manifest(parsed)} == {"keep"}


def test_defaults_enforce_the_multi_seed_and_search_protocol() -> None:
    parsed = args()
    assert parsed.refit_seeds >= 3, "a 1-seed cell is not an estimate"
    assert parsed.kernels == [5, 9, 15, 21]
    assert parsed.dilation_bases == [1, 2, 4]
    assert len(parsed.lrs) >= 3, "the baseline must get the tuning budget the model got"
    # Early stopping must not be able to fire before min_epochs: an aggressive rule
    # truncated seeds and flipped a verdict on phage_fragments.
    assert parsed.min_epochs >= 8
    assert parsed.patience >= 8


def test_rows_for_csv_marks_exactly_one_dev_selected_row() -> None:
    selected = {"stage": "refit", "arch": "dilated", "channels": 128, "blocks": 5, "kernel": 9,
                "dilation_base": 4, "receptive_field_bp": 2729, "params": 677000, "lr": 1e-3,
                "n_seeds": 5, "val": 0.85, "test": 0.84, "test_sd": 0.01}
    other = dict(selected, stage="capacity", n_seeds=1, val=0.80, test=0.79, test_sd=None)
    result = {"benchmark": "b", "task": "t", "split_type": "random", "group": "g",
              "metric": "mcc", "seqlen": 4000, "n_train": 10, "n_val": 2, "n_test": 2,
              "ladder": [other, selected], "dev_selected": selected,
              "oracle_best_test": 0.84}
    rows = list(rows_for_csv(result))
    assert sum(row["is_dev_selected"] for row in rows) == 1
    assert rows[1]["is_dev_selected"] == 1
    assert rows[1]["stage"] == "refit"
    # The oracle-best column travels with every row so the selection cost stays visible.
    assert all(row["oracle_best_test"] == 0.84 for row in rows)
