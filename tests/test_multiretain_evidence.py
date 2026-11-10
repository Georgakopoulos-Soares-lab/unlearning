import math
import re

from scripts.sayyed.build_multiretain_evidence import (
    build_coverage,
    transform_maxent,
    transform_reconciliation,
)


def test_evidence_is_complete_and_historical():
    rows = transform_reconciliation() + transform_maxent()
    assert len(rows) == 420
    assert len({row["claim_id"] for row in rows}) == len(rows)
    assert all(row["task"] != "HVUE human-host-tropism" for row in rows)
    assert all(re.fullmatch(r"[0-9a-f]{40}", row["source_commit"]) for row in rows)
    assert all(math.isfinite(float(row["metric_value"])) for row in rows)
    assert {row["study"] for row in rows} >= {
        "pilot_256train_128dev",
        "six_task_extension_1024train",
        "supplied_H3",
        "posthoc_followup",
        "bionemo_common_protocol_h3_only",
    }


def test_coverage_has_nulls_and_explicit_blockers():
    rows = build_coverage()
    assert len(rows) == 2808
    assert all(row["value"] == "" and row["missing_reason"] for row in rows)
    assert {row["status"] for row in rows} == {"expected", "blocked", "invalid"}
    multi = [row for row in rows if row["model_arm"] == "multi_retain"]
    assert len(multi) == 936
    assert all(row["status"] == "blocked" for row in multi)
    assert all(row["retain_mixture_identity"] == "" for row in multi)


def test_coverage_uses_26_exact_representations_and_three_seeds():
    rows = build_coverage()
    base_refit = [
        row
        for row in rows
        if row["model_arm"] == "base" and row["probe_policy"] == "independent_refit"
    ]
    assert len({row["layer"] for row in base_refit}) == 26
    assert {row["seed"] for row in base_refit} == {42, 17, 1234}
    assert "decoder.layers.16" in {row["layer"] for row in base_refit}
    assert "blocks.15" not in {row["layer"] for row in base_refit}
