"""Build explicitly synthetic reporting fixtures; never use as scientific results."""

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
TASKS = ["emp_H3", "gue_prom_300_all", "gue_splice_reconstructed", "gue_prom_core_all", "gue_tf_0", "gue_mouse_0"]
LAYERS = ["decoder.layers.0", "decoder.layers.1", "decoder.final_norm"]
SEEDS = [42, 17]
METRIC_FIELDS = ["task", "split", "checkpoint", "checkpoint_role", "layer", "seed", "probe_policy", "metric", "value", "status", "missing_reason"]
DIFFERENCE_FIELDS = ["task", "split", "checkpoint", "checkpoint_role", "layer", "seed", "probe_policy", "metric", "difference", "ci_low", "ci_high", "status", "missing_reason"]


def common(task, checkpoint, role, layer, seed):
    return {
        "task": task,
        "split": "dev",
        "checkpoint": checkpoint,
        "checkpoint_role": role,
        "layer": layer,
        "seed": seed,
        "probe_policy": "independent_refit",
        "metric": "auroc",
    }


def main():
    metrics = []
    differences = []
    for task_index, task in enumerate(TASKS):
        for layer_index, layer in enumerate(LAYERS):
            for seed_index, seed in enumerate(SEEDS):
                base = 0.60 + 0.01 * task_index + 0.02 * layer_index + 0.005 * seed_index
                post = base + 0.02 - 0.005 * task_index
                for checkpoint, role, value in (
                    ("synthetic-base", "reference", base),
                    ("synthetic-post", "intervention", post),
                ):
                    metrics.append({**common(task, checkpoint, role, layer, seed), "value": f"{value:.6f}", "status": "completed", "missing_reason": ""})
                difference = post - base
                differences.append({**common(task, "synthetic-post", "intervention", layer, seed), "difference": f"{difference:.6f}", "ci_low": f"{difference - 0.02:.6f}", "ci_high": f"{difference + 0.02:.6f}", "status": "completed", "missing_reason": ""})
            missing_metric = common(task, "synthetic-multi", "broader-retain-unidentified", layer, "")
            metrics.append({**missing_metric, "value": "", "status": "expected", "missing_reason": "synthetic placeholder"})
            missing_difference = common(task, "synthetic-multi", "broader-retain-unidentified", layer, "")
            differences.append({**missing_difference, "difference": "", "ci_low": "", "ci_high": "", "status": "expected", "missing_reason": "synthetic placeholder"})
    for filename, fields, rows in (
        ("SYNTHETIC_METRICS.csv", METRIC_FIELDS, metrics),
        ("SYNTHETIC_DIFFERENCES.csv", DIFFERENCE_FIELDS, differences),
    ):
        with (ROOT / filename).open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)


if __name__ == "__main__":
    main()
