import json
from pathlib import Path

import pytest

from scripts.sayyed.multiretain_report import (
    DIFFERENCE_FIELDS,
    METRIC_FIELDS,
    aggregate_rows,
    layer_key,
    plot_difference_heatmaps,
    plot_profiles,
    read_rows,
)


FIXTURES = Path(__file__).parent / "fixtures" / "multiretain"


def test_synthetic_profile_and_heatmap_exports(tmp_path):
    metrics = read_rows(FIXTURES / "SYNTHETIC_METRICS.csv", METRIC_FIELDS, "value")
    paths, completed, aggregates = plot_profiles(
        metrics,
        tmp_path / "profiles",
        metric="auroc",
        split="dev",
        probe_policy="independent_refit",
        synthetic=True,
    )
    assert len(completed) == 72
    assert len(aggregates) == 36
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths)
    differences = read_rows(FIXTURES / "SYNTHETIC_DIFFERENCES.csv", DIFFERENCE_FIELDS, "difference")
    heatmaps, completed_differences = plot_difference_heatmaps(
        differences,
        tmp_path / "differences",
        metric="auroc",
        split="dev",
        probe_policy="independent_refit",
        synthetic=True,
    )
    assert len(completed_differences) == 36
    assert len(heatmaps) == 6


def test_missing_value_must_be_null_with_reason(tmp_path):
    path = tmp_path / "rows.csv"
    path.write_text(
        ",".join(METRIC_FIELDS)
        + "\nemp_H3,dev,base,reference,decoder.layers.0,42,independent_refit,auroc,0,blocked,missing\n"
    )
    with pytest.raises(ValueError, match="null and a reason"):
        read_rows(path, METRIC_FIELDS, "value")


def test_aggregate_preserves_seed_range():
    rows = read_rows(FIXTURES / "SYNTHETIC_METRICS.csv", METRIC_FIELDS, "value")
    aggregate = aggregate_rows(rows, "value")[0]
    assert aggregate["seed_n"] == 2
    assert aggregate["seeds"] == "17;42"
    assert aggregate["min"] <= aggregate["mean"] <= aggregate["max"]


def test_layer_numbering_is_explicit():
    assert layer_key("decoder.layers.16") == (0, 16)
    assert layer_key("decoder.layers[16]") == (0, 16)
    assert layer_key("decoder.final_norm") == (1, 0)
    with pytest.raises(ValueError, match="Unrecognized"):
        layer_key("blocks.15")
