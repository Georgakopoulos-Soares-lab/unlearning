from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from phase2.rescore_filtered import evaluate, main, read_index, rows_to_drop, score


def write_preds(path: Path, y_true, y_pred) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, y_true=np.asarray(y_true), y_pred=np.asarray(y_pred))
    return str(path)


def write_index(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task", "arm", "role", "path", "seed"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return str(path)


def arms_from(entries):
    out = {}
    for arm, role, paths in entries:
        out[arm] = [{"path": p, "role": role, "seed": str(i)} for i, p in enumerate(paths)]
    return out


def test_rows_to_drop_parses_mmseqs_query_ids(tmp_path: Path) -> None:
    m8 = tmp_path / "hits.m8"
    m8.write_text("te3|1\ttr9|1\t0.99\t400\n"
                  "te7|0\ttr2|0\t0.95\t400\n"
                  "te3|1\ttr4|1\t0.91\t400\n")   # duplicate query collapses
    assert list(rows_to_drop(str(m8), 10)) == [3, 7]


def test_rows_to_drop_accepts_a_plain_index_list(tmp_path: Path) -> None:
    idx = tmp_path / "drop.txt"
    idx.write_text("0\n4\n4\n9\n")
    assert list(rows_to_drop(str(idx), 10)) == [0, 4, 9]


def test_rows_to_drop_is_empty_for_a_missing_or_empty_mask(tmp_path: Path) -> None:
    assert len(rows_to_drop(str(tmp_path / "nope.m8"), 10)) == 0
    empty = tmp_path / "empty.m8"
    empty.write_text("")
    assert len(rows_to_drop(str(empty), 10)) == 0


def test_rows_to_drop_rejects_a_mask_from_a_different_test_order(tmp_path: Path) -> None:
    """A silent off-by-one between mask and predictions would filter the wrong rows."""
    m8 = tmp_path / "hits.m8"
    m8.write_text("te50|1\ttr1|1\t0.99\t400\n")
    with pytest.raises(ValueError, match="not in the same test-set order"):
        rows_to_drop(str(m8), 10)


def test_filtering_can_grow_the_excess(tmp_path: Path) -> None:
    """The phage pattern: removing leaked rows leaves the excess intact or larger.

    Rows 0-3 are ones the baseline gets right and the model gets wrong, so dropping
    them should widen the gap.
    """
    y = [0, 0, 0, 0, 1, 1, 1, 1, 0, 1]
    base = write_preds(tmp_path / "b_s0.npz", y, [0, 0, 0, 0, 1, 0, 0, 0, 1, 0])
    base2 = write_preds(tmp_path / "b_s1.npz", y, [0, 0, 0, 0, 1, 0, 0, 0, 1, 0])
    mod = write_preds(tmp_path / "m_s0.npz", y, [1, 1, 1, 1, 1, 1, 1, 1, 0, 1])
    mod2 = write_preds(tmp_path / "m_s1.npz", y, [1, 1, 1, 1, 1, 1, 1, 1, 0, 1])
    arms = arms_from([("cnn", "baseline", [base, base2]), ("nt_v2", "model", [mod, mod2])])
    official = evaluate("t", arms, np.ones(10, bool), "official", "mcc", None)
    keep = np.ones(10, bool)
    keep[[0, 1, 2, 3]] = False
    filtered = evaluate("t", arms, keep, "id>=0.7", "mcc", official["excess"])
    assert filtered["n_removed"] == 4
    assert filtered["excess"] > official["excess"]
    assert filtered["delta_vs_official"] > 0


def test_binding_baseline_is_the_strongest_baseline_arm(tmp_path: Path) -> None:
    y = [0, 1] * 8
    weak = write_preds(tmp_path / "kmer.npz", y, [0] * 16)
    strong = write_preds(tmp_path / "cnn.npz", y, y)
    mod = write_preds(tmp_path / "m.npz", y, y)
    arms = arms_from([("kmer", "baseline", [weak]), ("cnn", "baseline", [strong]),
                      ("nt_v2", "model", [mod])])
    out = evaluate("t", arms, np.ones(16, bool), "official", "mcc", None)
    assert out["binding_baseline"] == "cnn"
    assert out["excess"] == 0.0, "model equals the CNN, so there is no excess"


def test_evaluate_needs_both_a_model_and_a_baseline_arm(tmp_path: Path) -> None:
    y = [0, 1] * 8
    only_model = arms_from([("nt_v2", "model", [write_preds(tmp_path / "m.npz", y, y)])])
    assert evaluate("t", only_model, np.ones(16, bool), "official", "mcc", None) is None


def test_misaligned_seeds_are_rejected(tmp_path: Path) -> None:
    a = write_preds(tmp_path / "a.npz", [0, 1, 0, 1], [0, 1, 0, 1])
    b = write_preds(tmp_path / "b.npz", [1, 0, 1, 0], [1, 0, 1, 0])
    arms = arms_from([("cnn", "baseline", [a, b])])
    with pytest.raises(ValueError, match="y_true differs"):
        evaluate("t", arms, np.ones(4, bool), "official", "mcc", None)


def test_read_index_groups_by_task_and_arm(tmp_path: Path) -> None:
    idx = write_index(tmp_path / "idx.csv", [
        {"task": "t1", "arm": "cnn", "role": "baseline", "path": "a.npz", "seed": "42"},
        {"task": "t1", "arm": "cnn", "role": "baseline", "path": "b.npz", "seed": "43"},
        {"task": "t1", "arm": "nt_v2", "role": "model", "path": "c.npz", "seed": "42"},
        {"task": "t2", "arm": "cnn", "role": "baseline", "path": "d.npz", "seed": "42"},
    ])
    got = read_index(idx)
    assert set(got) == {"t1", "t2"}
    assert len(got["t1"]["cnn"]) == 2
    assert got["t1"]["nt_v2"][0]["role"] == "model"


def test_read_index_rejects_a_missing_column(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task", "arm", "path"])
        writer.writeheader()
        writer.writerow({"task": "t", "arm": "a", "path": "p.npz"})
    with pytest.raises(ValueError, match="missing columns"):
        read_index(str(path))


def test_score_supports_the_three_metrics() -> None:
    y = np.array([0, 0, 1, 1])
    perfect = np.array([0, 0, 1, 1])
    assert score(y, perfect, "mcc") == pytest.approx(1.0)
    assert score(y, perfect, "macro_f1") == pytest.approx(1.0)
    assert score(y, perfect, "auroc") == pytest.approx(1.0)


def test_main_end_to_end_writes_official_and_filtered_rows(tmp_path: Path) -> None:
    y = [0] * 20 + [1] * 20
    base = write_preds(tmp_path / "cnn.npz", y, [0] * 20 + [1] * 14 + [0] * 6)
    mod = write_preds(tmp_path / "nt.npz", y, [0] * 20 + [1] * 18 + [0] * 2)
    idx = write_index(tmp_path / "idx.csv", [
        {"task": "phage", "arm": "cnn", "role": "baseline", "path": base, "seed": "42"},
        {"task": "phage", "arm": "nt_v2", "role": "model", "path": mod, "seed": "42"},
    ])
    m8 = tmp_path / "hits.m8"
    m8.write_text("".join(f"te{i}|0\ttr{i}|0\t0.99\t400\n" for i in range(5)))
    out = tmp_path / "rescored.csv"
    assert main(["--prediction-index", idx, "--out-csv", str(out),
                 "--mask", f"phage:id>=0.7/c0.3:{m8}"]) == 0
    rows = list(csv.DictReader(out.open()))
    assert [r["filter"] for r in rows] == ["official", "id>=0.7/c0.3"]
    assert int(rows[1]["n_removed"]) == 5
    assert int(rows[1]["n_clean"]) == 35
    assert rows[0]["binding_baseline"] == "cnn"


def test_main_skips_a_filter_that_leaves_too_few_rows(tmp_path: Path) -> None:
    y = [0] * 20 + [1] * 20
    base = write_preds(tmp_path / "cnn.npz", y, y)
    mod = write_preds(tmp_path / "nt.npz", y, y)
    idx = write_index(tmp_path / "idx.csv", [
        {"task": "t", "arm": "cnn", "role": "baseline", "path": base, "seed": "42"},
        {"task": "t", "arm": "nt_v2", "role": "model", "path": mod, "seed": "42"},
    ])
    m8 = tmp_path / "hits.m8"
    m8.write_text("".join(f"te{i}|0\ttr{i}|0\t0.99\t400\n" for i in range(39)))
    out = tmp_path / "rescored.csv"
    assert main(["--prediction-index", idx, "--out-csv", str(out), "--mask", f"t:strict:{m8}"]) == 0
    rows = list(csv.DictReader(out.open()))
    assert [r["filter"] for r in rows] == ["official"], "the 1-row filter must be skipped"


def test_main_rejects_a_malformed_mask_spec(tmp_path: Path) -> None:
    y = [0, 1] * 8
    p = write_preds(tmp_path / "a.npz", y, y)
    idx = write_index(tmp_path / "idx.csv", [
        {"task": "t", "arm": "cnn", "role": "baseline", "path": p, "seed": "42"},
        {"task": "t", "arm": "m", "role": "model", "path": p, "seed": "42"},
    ])
    with pytest.raises(SystemExit, match="TASK:LABEL:PATH"):
        main(["--prediction-index", idx, "--out-csv", str(tmp_path / "o.csv"),
              "--mask", "bad_spec"])
