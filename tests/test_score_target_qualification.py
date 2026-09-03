from __future__ import annotations

import csv
from pathlib import Path

from phase2.score_target_qualification import main, parse_args, qualify, read_scores


def write_scores(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["task", "arm", "role", "score", "score_sd", "n_seeds", "metric"]
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def args(**overrides):
    argv = ["--scores-csv", "x", "--out-csv", "y"]
    for key, value in overrides.items():
        argv += [f"--{key.replace('_', '-')}", str(value)]
    return parse_args(argv)


def payload(model, baselines, metric="mcc"):
    return {"model": model, "baselines": baselines, "metric": metric}


def arm(name, score, sd=None, seeds=3):
    return {"arm": name, "score": score, "sd": sd, "n_seeds": seeds}


def test_cosmetic_target_is_rejected_despite_a_large_ratio() -> None:
    """promoter_all: excess is 6x the seed noise, and removing it changes nothing.

    This is the case the one-criterion gate lets through.
    """
    result = qualify("promoter_all", payload(
        arm("nt_v2_500m", 0.9557, 0.0021), [arm("cnn", 0.9245, 0.0014), arm("kmer", 0.8227)],
    ), args())
    assert result["significant"] is True
    assert result["ratio"] > 5
    assert result["recoverability"] > 0.96
    assert result["removal_meaningful"] is False
    assert result["verdict"] == "NOT_QUALIFIED_COSMETIC"


def test_no_excess_is_rejected() -> None:
    result = qualify("virobench_family", payload(
        arm("nt_v2_500m", 0.8867, 0.0075), [arm("kmer", 0.9475)],
    ), args())
    assert result["excess"] < 0
    assert result["verdict"] == "NOT_QUALIFIED_NO_EXCESS"


def test_binding_baseline_is_the_strongest_arm_not_the_first() -> None:
    """iDHS-EL is the one task in 22 where k-mer beat the swept CNN."""
    result = qualify("iDHS_DNase_I", payload(
        arm("dnabert2", 0.7054, 0.0045), [arm("cnn", 0.5900, 0.0445), arm("kmer", 0.6411)],
    ), args())
    assert result["binding_baseline"] == "kmer"
    assert result["baseline_score"] == 0.6411


def test_phage_is_significant_but_marginal_on_recoverability() -> None:
    """The project's best candidate: passes criterion 1, fails criterion 2 at 91.5%."""
    result = qualify("GUE_phage_fragments", payload(
        arm("nt_v2_500m", 0.9196, 0.0049), [arm("cnn", 0.8413, 0.0128, seeds=5), arm("kmer", 0.6290)],
    ), args())
    assert result["significant"] is True
    assert round(result["ratio"], 2) == 2.86
    assert 0.91 < result["recoverability"] < 0.92
    assert result["verdict"] == "NOT_QUALIFIED_COSMETIC"
    # Raising the bar to 92% flips it, which is why the threshold is an explicit flag.
    relaxed = qualify("GUE_phage_fragments", payload(
        arm("nt_v2_500m", 0.9196, 0.0049), [arm("cnn", 0.8413, 0.0128, seeds=5), arm("kmer", 0.6290)],
    ), args(max_recoverability=0.92))
    assert relaxed["verdict"] == "QUALIFIED"


def test_low_recoverability_and_real_excess_qualifies() -> None:
    result = qualify("lncrna_g_max", payload(
        arm("nt_v2_500m", 0.5116, 0.0317), [arm("cnn", 0.3750, 0.0353), arm("kmer", 0.1431)],
    ), args(max_recoverability=0.90))
    assert result["recoverability"] < 0.75
    assert result["verdict"] in {"QUALIFIED", "NOT_QUALIFIED_NO_EXCESS"}
    # ratio 1.44 clears the gate, so this is the qualifying branch.
    assert result["significant"] is True
    assert result["verdict"] == "QUALIFIED"


def test_single_seed_arm_is_provisional_not_qualified() -> None:
    result = qualify("some_task", payload(
        arm("model", 0.90, 0.001, seeds=1), [arm("cnn", 0.50, 0.001, seeds=3)],
    ), args())
    assert result["verdict"] == "PROVISIONAL"
    assert "seed(s)" in result["notes"]


def test_missing_baseline_cannot_qualify_a_target() -> None:
    result = qualify("no_base", payload(arm("model", 0.9, 0.01), []), args())
    assert result["verdict"] == "NO_BASELINE"


def test_near_the_line_ratio_recommends_a_paired_bootstrap() -> None:
    result = qualify("borderline", payload(
        arm("model", 0.60, 0.02), [arm("cnn", 0.55, 0.02)],
    ), args(max_recoverability=0.95))
    assert 0.7 < result["ratio"] < 1.5
    assert "paired bootstrap" in result["notes"]


def test_read_scores_keeps_the_best_model_arm_and_all_baselines(tmp_path: Path) -> None:
    path = tmp_path / "arms.csv"
    write_scores(path, [
        {"task": "t", "arm": "nt_v2", "role": "model", "score": 0.80, "score_sd": 0.01, "n_seeds": 3},
        {"task": "t", "arm": "hyenadna", "role": "model", "score": 0.70, "score_sd": 0.01, "n_seeds": 3},
        {"task": "t", "arm": "cnn", "role": "baseline", "score": 0.60, "score_sd": 0.01, "n_seeds": 3},
        {"task": "t", "arm": "kmer", "role": "baseline", "score": 0.50},
    ])
    tasks = read_scores(str(path))
    assert tasks["t"]["model"]["arm"] == "nt_v2"
    assert len(tasks["t"]["baselines"]) == 2


def test_main_writes_csv(tmp_path: Path) -> None:
    scores = tmp_path / "arms.csv"
    write_scores(scores, [
        {"task": "t", "arm": "model", "role": "model", "score": 0.90, "score_sd": 0.005, "n_seeds": 3},
        {"task": "t", "arm": "cnn", "role": "baseline", "score": 0.50, "score_sd": 0.005, "n_seeds": 3},
    ])
    out = tmp_path / "qual.csv"
    assert main(["--scores-csv", str(scores), "--out-csv", str(out)]) == 0
    rows = list(csv.DictReader(out.open()))
    assert rows[0]["verdict"] == "QUALIFIED"
    assert rows[0]["binding_baseline"] == "cnn"
