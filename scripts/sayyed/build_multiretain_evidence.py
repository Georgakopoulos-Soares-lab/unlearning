"""Build the historical evidence map and planned all-layer coverage template."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "experiments" / "ashay" / "multiretain-reporting-v1"
EVIDENCE_FIELDS = [
    "claim_id",
    "study",
    "task",
    "model_backend",
    "checkpoint_identity",
    "split_sample_counts",
    "representation",
    "probe_policy",
    "seed",
    "metric_definition",
    "metric_value",
    "source_commit",
    "source_path",
    "evidence_type",
    "verification_status",
    "comparability_limitations",
]
COVERAGE_FIELDS = [
    "study",
    "model_arm",
    "retain_mixture_identity",
    "task",
    "split",
    "layer",
    "seed",
    "probe_policy",
    "status",
    "value",
    "missing_reason",
    "source_unit",
]
TASKS = {
    "emp_H3": ("test", "11971 train/1497 dev/1497 test"),
    "gue_prom_300_all": ("dev", "1024 train/512 official dev"),
    "gue_splice_reconstructed": ("dev", "1024 train/512 official dev"),
    "gue_prom_core_all": ("dev", "1024 train/512 official dev"),
    "gue_tf_0": ("dev", "1024 train/512 official dev"),
    "gue_mouse_0": ("dev", "1024 train/512 official dev"),
}
LAYERS = [f"decoder.layers.{index}" for index in range(25)] + ["decoder.final_norm"]
SEEDS = [42, 17, 1234]
POLICIES = ["independent_refit", "fixed_base_scaler_and_head"]


def metric_definition(task: str, metric: str) -> str:
    if metric == "auroc":
        return "macro one-vs-rest AUROC" if "splice" in task else "numeric class-1 tied-rank AUROC"
    if metric == "balanced_accuracy":
        return "mean class recall; binary threshold .5 or multiclass argmax"
    if metric == "accuracy":
        return "fraction correct; binary threshold .5 or multiclass argmax"
    if metric == "average_precision":
        return "class-1 average precision with tied scores grouped"
    if metric == "causal_nll":
        return "summed next-token loss divided by valid targets"
    if metric in {"perplexity", "lm_perplexity"}:
        return "exp(token-weighted causal NLL), not classifier CE PPL"
    if metric == "classification_cross_entropy":
        return "mean classifier cross-entropy; distinct from causal NLL"
    return metric


def historical_limitations(study: str) -> str:
    if study == "pilot_256train_128dev":
        return "exploratory 256/128 dev-selected heads; not comparable as an effect to train-only-CV or test studies"
    if study == "six_task_extension_1024train":
        return "reused official dev; 1024/512 train-only CV; biological groups and numeric class meanings unresolved"
    if study == "supplied_H3":
        return "reused exploratory test; original backend; MLP selected on dev; not BioNeMo-equivalent"
    if study == "posthoc_followup":
        return "post-hoc reused test; conditional intervals; readout/exposure differences; not an unlearning effect"
    if study == "BioNeMo aggregate log":
        return "aggregate log only; split/checkpoint/load/pairing identity unresolved; no new evaluation"
    return "historical evidence; inspect source protocol before comparison"


def transform_reconciliation() -> list[dict[str, Any]]:
    path = ROOT / "docs" / "experiments" / "ashay" / "metrics-reconciliation-v1" / "VERIFIED_METRICS.csv"
    output = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row["task"] == "HVUE human-host-tropism":
                continue
            study = row["study"]
            source_path = row["source_artifact"]
            if source_path.startswith("bionemo:"):
                source_commit = "b90fc1853d1d3be79922a98a2649c91c89716637"
                source_path = source_path.removeprefix("bionemo:")
            elif "extension/" in source_path or "baseline_probe_results" in source_path:
                source_commit = (
                    "06fb273ae0cf3578f4c79d3c97052b93c4f6300a"
                    if "baseline_probe_results" in source_path
                    else "5bb08f502d6739e6ce84f2fe77799d4f4ba71cc3"
                )
            else:
                source_commit = "89c7e934fb025fe1048d9e06dd0fb039211fe46a"
            if study == "pilot_256train_128dev":
                evidence = "historical_aggregate_table"
                verification = "aggregate only; no prediction-level reconstruction claimed"
            elif study == "BioNeMo aggregate log":
                evidence = "historical_aggregate_log"
                verification = row["verification_status"]
            else:
                evidence = "historical_saved_outputs"
                verification = row["verification_status"] + "; later saved-output verification reported at 89c7e934; not repeated here"
            output.append(
                {
                    "claim_id": f"{study}:{row['task']}:{row['model_checkpoint']}:{row['intervention']}:{row['split']}:{row['representation']}:{row['probe']}:{row['metric']}",
                    "study": study,
                    "task": row["task"],
                    "model_backend": f"{row['model_checkpoint']}; {study}",
                    "checkpoint_identity": f"{row['model_checkpoint']}; intervention={row['intervention']}",
                    "split_sample_counts": f"{row['split']} n={row['sample_count']}",
                    "representation": row["representation"],
                    "probe_policy": row["probe"],
                    "seed": "42" if "42" in row["probe"] or study in {"pilot_256train_128dev", "six_task_extension_1024train", "posthoc_followup"} else "not_recorded",
                    "metric_definition": metric_definition(row["task"], row["metric"]),
                    "metric_value": row["value"],
                    "source_commit": source_commit,
                    "source_path": source_path,
                    "evidence_type": evidence,
                    "verification_status": verification,
                    "comparability_limitations": historical_limitations(study),
                }
            )
    return output


def transform_maxent() -> list[dict[str, Any]]:
    path = ROOT / "docs" / "experiments" / "ashay" / "maxent-benign-v1" / "metrics.csv"
    output = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            task = "emp_H3" if row["task"] == "EMP/H3" else row["task"]
            model = row["model"]
            checkpoint = (
                "evo2_1b_base_mbridge/iter_0000001; local shard receipt in run_manifest.json"
                if model.startswith("base")
                else "H3-only MaxEnt iter_0002000; retain config emp_h3; parent/exposure unresolved"
            )
            representation = {
                "final_norm": "decoder.final_norm",
                "decoder_layer_16": "decoder.layers[16] (zero-indexed 17th block)",
                "backbone": "backbone causal LM output",
            }[row["layer"]]
            policy = {
                "base": "none",
                "maxent": "none",
                "base_refit": "independent_refit",
                "maxent_refit": "independent_refit",
                "maxent_fixed_base": "fixed_base_scaler_and_head",
            }[model]
            output.append(
                {
                    "claim_id": f"bionemo_h3_only:{task}:{model}:{row['split']}:{row['layer']}:{row['metric']}",
                    "study": "bionemo_common_protocol_h3_only",
                    "task": task,
                    "model_backend": "BioNeMo native frozen Evo2-1B; separately fitted CPU logistic probes",
                    "checkpoint_identity": checkpoint,
                    "split_sample_counts": f"{row['split']}; {TASKS[task][1]}",
                    "representation": representation,
                    "probe_policy": policy,
                    "seed": "42" if policy != "none" else "not_applicable",
                    "metric_definition": metric_definition(task, row["metric"]),
                    "metric_value": row["value"],
                    "source_commit": "b5f700ff4f96a305b4c84d12346baccd94a22cdc",
                    "source_path": "docs/experiments/ashay/maxent-benign-v1/metrics.csv",
                    "evidence_type": "historical_saved_predictions" if policy != "none" else "historical_per_sequence_loss_statistics",
                    "verification_status": "all scalar records independently recomputed in historical audit; not GPU replicated or newly recomputed here",
                    "comparability_limitations": "H3 test/other-task dev reused and exploratory; reference-model comparison only; parent lineage and row-level exposure unresolved; fixed/refitted policies not interchangeable",
                }
            )
    return output


def build_coverage() -> list[dict[str, Any]]:
    rows = []
    for arm in ("base", "h3_only_maxent", "multi_retain"):
        for task, (split, _) in TASKS.items():
            for layer in LAYERS:
                for seed in SEEDS:
                    for policy in POLICIES:
                        if arm == "multi_retain":
                            status = "blocked"
                            reason = "multi-retain checkpoint and exact retain mixture not identified"
                            mixture = ""
                        elif arm == "base" and policy == "fixed_base_scaler_and_head":
                            status = "invalid"
                            reason = "fixed-base-on-base is not a distinct comparison arm"
                            mixture = "not_applicable"
                        else:
                            status = "expected"
                            reason = "awaiting fixed8 smoke gate and finalized producer COMPLETE units"
                            mixture = "not_applicable" if arm == "base" else "EMP/H3 only; exact row/token exposure unknown"
                        rows.append(
                            {
                                "study": "planned_multiretain_all_layer",
                                "model_arm": arm,
                                "retain_mixture_identity": mixture,
                                "task": task,
                                "split": split,
                                "layer": layer,
                                "seed": seed,
                                "probe_policy": policy,
                                "status": status,
                                "value": "",
                                "missing_reason": reason,
                                "source_unit": "",
                            }
                        )
    return rows


def write(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    evidence = transform_reconciliation() + transform_maxent()
    write(OUTPUT / "EVIDENCE_INDEX.csv", EVIDENCE_FIELDS, evidence)
    write(OUTPUT / "COVERAGE_TEMPLATE.csv", COVERAGE_FIELDS, build_coverage())
    print(f"EVIDENCE_ROWS {len(evidence)}; COVERAGE_ROWS {len(build_coverage())}")


if __name__ == "__main__":
    main()
