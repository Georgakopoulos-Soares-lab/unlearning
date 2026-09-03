"""Guards on the significance gate itself.

`ratio = excess / (2*sqrt(sd_model^2 + sd_baseline^2))` silently inflates when the
binding baseline is deterministic. On `iDHS-EL_DNase_I` the binding baseline is a k-mer
logistic regression with no seed spread, and the naive gate reported ratio 7.22 where
accounting for baseline variance gave 0.72 -- a tenfold over-statement that would have
promoted a cosmetic target to QUALIFIED.
"""
from __future__ import annotations

from phase2.score_target_qualification import parse_args, qualify


def args(**overrides):
    argv = ["--scores-csv", "x", "--out-csv", "y"]
    for key, value in overrides.items():
        argv += [f"--{key.replace('_', '-')}", str(value)]
    return parse_args(argv)


def payload(model, baselines):
    return {"model": model, "baselines": baselines, "metric": "mcc"}


def arm(name, score, sd=None, seeds=3):
    return {"arm": name, "score": score, "sd": sd, "n_seeds": seeds}


def test_deterministic_binding_baseline_cannot_yield_qualified() -> None:
    """iDHS-EL: k-mer binds at 0.6411 with no SD, model 0.7054 +- 0.0045."""
    result = qualify("iDHS_DNase_I", payload(
        arm("dnabert2", 0.7054, 0.0045),
        [arm("kmer", 0.6411, None, seeds=0), arm("cnn_ceiling", 0.5900, 0.0445)],
    ), args(max_recoverability=0.95))
    assert result["binding_baseline"] == "kmer"
    assert result["ratio"] > 5, "the naive gate is inflated -- that is the point"
    assert "OVER-estimate" in result["notes"]
    assert result["verdict"] == "PROVISIONAL", "an inflated gate must not qualify a target"


def test_baseline_with_seed_sd_is_not_flagged() -> None:
    result = qualify("t", payload(
        arm("model", 0.90, 0.005), [arm("cnn_ceiling", 0.50, 0.005)],
    ), args())
    assert "OVER-estimate" not in result["notes"]
    assert result["verdict"] == "QUALIFIED"


def test_model_without_seed_sd_is_reported_as_under_estimated() -> None:
    result = qualify("t", payload(
        arm("model", 0.90, None), [arm("cnn_ceiling", 0.50, 0.005)],
    ), args())
    assert "under-estimate" in result["notes"]


def test_no_sd_anywhere_does_not_assess_significance() -> None:
    result = qualify("t", payload(
        arm("model", 0.90, None, seeds=0), [arm("cnn_ceiling", 0.50, None, seeds=0)],
    ), args())
    assert result["gate"] is None
    assert result["ratio"] is None
    assert result["significant"] is False
    assert "significance not assessed" in result["notes"]


def test_per_model_breakdown_shows_every_model_against_one_baseline() -> None:
    """The phage pattern: NT-v2 is above the CNN, three other gLMs are below it.

    Reporting only the winning arm hides that the excess belongs to one model rather
    than to "gLMs" as a class.
    """
    payload_ = {
        "model": arm("nt_v2_500m", 0.9196, 0.0049),
        "all_models": [arm("nt_v2_500m", 0.9196, 0.0049), arm("dnabert2", 0.8221, 0.0077),
                       arm("gena_lm", 0.7162, 0.0092), arm("hyenadna", 0.8074, 0.0055)],
        "baselines": [arm("cnn_ceiling", 0.8413, 0.0128, seeds=5), arm("kmer", 0.6290, None, 0)],
        "metric": "mcc",
    }
    result = qualify("GUE_phage_fragments", payload_, args(max_recoverability=0.92))
    per = {e["arm"]: e for e in result["per_model"]}
    assert len(per) == 4
    assert per["nt_v2_500m"]["excess"] > 0 and per["nt_v2_500m"]["ratio"] > 2
    for losing in ("dnabert2", "gena_lm", "hyenadna"):
        assert per[losing]["excess"] < 0, f"{losing} should be below the CNN"
    # Sorted best-first so the winner is unambiguous.
    assert result["per_model"][0]["arm"] == "nt_v2_500m"
    # All arms judged against the SAME binding baseline.
    assert result["binding_baseline"] == "cnn_ceiling"


def test_per_model_falls_back_to_the_single_model_arm() -> None:
    result = qualify("t", payload(arm("m", 0.9, 0.01), [arm("cnn", 0.5, 0.01)]), args())
    assert [e["arm"] for e in result["per_model"]] == ["m"]
