"""CPU figures; adapted from Kimi commit8116ca826a54c66b48111f7750a30d819e238343.

Codex changes: bound rounded seed means to observed range and space heatmap labels.
Source metric values and conditional intervals remain unchanged.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


STATUSES = {"expected", "completed", "blocked", "invalid", "not_attempted"}
METRIC_FIELDS = [
    "task",
    "split",
    "checkpoint",
    "checkpoint_role",
    "layer",
    "seed",
    "probe_policy",
    "metric",
    "value",
    "status",
    "missing_reason",
]
DIFFERENCE_FIELDS = [
    "task",
    "split",
    "checkpoint",
    "checkpoint_role",
    "layer",
    "seed",
    "probe_policy",
    "metric",
    "difference",
    "ci_low",
    "ci_high",
    "status",
    "missing_reason",
]
TASK_ORDER = [
    "emp_H3",
    "gue_prom_300_all",
    "gue_splice_reconstructed",
    "gue_prom_core_all",
    "gue_tf_0",
    "gue_mouse_0",
]


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: str | Path, fields: list[str], value_field: str) -> list[dict[str, Any]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != fields:
            raise ValueError(f"Schema mismatch: expected {fields}, got {reader.fieldnames}")
        rows = list(reader)
    if not rows:
        raise ValueError("Reporting input is empty")
    identities = set()
    for line, row in enumerate(rows, 2):
        identity = tuple(
            row[field]
            for field in fields
            if field not in {value_field, "ci_low", "ci_high", "status", "missing_reason"}
        )
        if identity in identities:
            raise ValueError(f"Duplicate reporting identity at line {line}")
        identities.add(identity)
        if row["status"] not in STATUSES:
            raise ValueError(f"Invalid status at line {line}")
        if row["status"] != "completed":
            if row[value_field] != "" or not row["missing_reason"]:
                raise ValueError(f"Missing values need null and a reason at line {line}")
            continue
        if row["missing_reason"]:
            raise ValueError(f"Completed row has a missing reason at line {line}")
        try:
            value = float(row[value_field])
            seed = int(row["seed"])
        except ValueError as error:
            raise ValueError(f"Invalid completed numeric value at line {line}") from error
        if not math.isfinite(value):
            raise ValueError(f"Nonfinite completed value at line {line}")
        row[value_field] = value
        row["seed"] = seed
        if value_field == "difference":
            for bound in ("ci_low", "ci_high"):
                row[bound] = float(row[bound]) if row[bound] else None
            if (row["ci_low"] is None) != (row["ci_high"] is None):
                raise ValueError(f"Interval bounds must be paired at line {line}")
            if row["ci_low"] is not None and not row["ci_low"] <= value <= row["ci_high"]:
                raise ValueError(f"Point difference outside interval at line {line}")
    return rows


def layer_key(layer: str) -> tuple[int, int | str]:
    match = re.fullmatch(r"(?:decoder\.layers(?:\.|\[)|decoder_layer_)(\d+)\]?", layer)
    if match:
        return 0, int(match.group(1))
    if layer in {"decoder.final_norm", "final_norm"}:
        return 1, 0
    if layer == "backbone":
        return 2, 0
    raise ValueError(f"Unrecognized exact layer name: {layer}")


def layer_label(layer: str) -> str:
    key = layer_key(layer)
    return str(key[1]) if key[0] == 0 else ("final norm" if key[0] == 1 else "backbone")


def ordered_tasks(rows: list[dict[str, Any]]) -> list[str]:
    tasks = {row["task"] for row in rows}
    return [task for task in TASK_ORDER if task in tasks] + sorted(tasks - set(TASK_ORDER))


def aggregate_rows(rows: list[dict[str, Any]], value_field: str) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["status"] == "completed":
            identity = tuple(
                row[field]
                for field in ("task", "split", "checkpoint", "checkpoint_role", "layer", "probe_policy", "metric")
            )
            groups[identity].append(row)
    output = []
    for identity, members in sorted(groups.items(), key=lambda item: (item[0][0], layer_key(item[0][4]), item[0][2])):
        values = np.asarray([row[value_field] for row in members], dtype=float)
        output.append(
            {
                **dict(zip(("task", "split", "checkpoint", "checkpoint_role", "layer", "probe_policy", "metric"), identity)),
                "seed_n": len(values),
                "seeds": ";".join(str(row["seed"]) for row in sorted(members, key=lambda row: row["seed"])),
                "mean": float(np.clip(values.mean(), values.min(), values.max())),
                "min": float(values.min()),
                "max": float(values.max()),
            }
        )
    return output


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _watermark(figure: plt.Figure, synthetic: bool) -> None:
    if synthetic:
        figure.text(
            0.5,
            0.5,
            "SYNTHETIC — NOT BIOLOGICAL RESULTS",
            ha="center",
            va="center",
            fontsize=24,
            color="crimson",
            alpha=0.25,
            rotation=25,
            zorder=100,
        )


def save_figure(figure: plt.Figure, output_base: Path) -> list[Path]:
    paths = []
    for suffix in (".png", ".pdf", ".svg"):
        path = output_base.with_suffix(suffix)
        figure.savefig(path, dpi=180, bbox_inches="tight")
        paths.append(path)
    plt.close(figure)
    return paths


def plot_profiles(
    rows: list[dict[str, Any]],
    output_base: Path,
    *,
    metric: str,
    split: str,
    probe_policy: str,
    synthetic: bool,
) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    selected = [
        row
        for row in rows
        if row["metric"] == metric and row["split"] == split and row["probe_policy"] == probe_policy
    ]
    if not selected:
        raise ValueError("No rows match the requested profile")
    completed = [row for row in selected if row["status"] == "completed"]
    if not completed:
        raise ValueError("No completed values match the requested profile")
    tasks = ordered_tasks(selected)
    layers = sorted({row["layer"] for row in selected}, key=layer_key)
    x_lookup = {layer: index for index, layer in enumerate(layers)}
    aggregates = aggregate_rows(completed, "value")
    aggregate_lookup = {
        (row["task"], row["checkpoint"], row["layer"]): row for row in aggregates
    }
    checkpoints = sorted({row["checkpoint"] for row in selected})
    colors = plt.cm.tab10(np.linspace(0, 1, max(10, len(checkpoints))))
    figure, axes = plt.subplots(2, 3, figsize=(17, 9), sharex=True)
    for axis, task in zip(axes.flat, tasks):
        for checkpoint_index, checkpoint in enumerate(checkpoints):
            task_rows = [
                row for row in completed if row["task"] == task and row["checkpoint"] == checkpoint
            ]
            points = []
            for layer in layers:
                aggregate = aggregate_lookup.get((task, checkpoint, layer))
                if aggregate is None:
                    continue
                x = x_lookup[layer]
                seeds = [row for row in task_rows if row["layer"] == layer]
                axis.scatter(
                    [x] * len(seeds),
                    [row["value"] for row in seeds],
                    color=colors[checkpoint_index],
                    alpha=0.3,
                    s=16,
                )
                points.append((x, aggregate))
            if points:
                axis.errorbar(
                    [point[0] for point in points],
                    [point[1]["mean"] for point in points],
                    yerr=[
                        [point[1]["mean"] - point[1]["min"] for point in points],
                        [point[1]["max"] - point[1]["mean"] for point in points],
                    ],
                    label=checkpoint,
                    color=colors[checkpoint_index],
                    marker="o",
                    capsize=3,
                )
            missing = sorted(
                {
                    f"{row['checkpoint']}: {row['status']}"
                    for row in selected
                    if row["task"] == task and row["checkpoint"] == checkpoint and row["status"] != "completed"
                }
            )
            if missing:
                axis.text(
                    0.02,
                    0.02 + 0.06 * checkpoint_index,
                    "missing " + ", ".join(missing),
                    transform=axis.transAxes,
                    fontsize=7,
                    color="crimson",
                )
        axis.set_title(task)
        axis.set_xticks(range(len(layers)), [layer_label(layer) for layer in layers], rotation=45)
        axis.grid(alpha=0.2)
        axis.set_ylim(0, 1 if metric in {"auroc", "accuracy", "balanced_accuracy", "average_precision"} else None)
    for axis in list(axes.flat)[len(tasks):]:
        axis.axis("off")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    if handles:
        figure.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.0), ncol=len(checkpoints))
    roles = ", ".join(sorted({row["checkpoint_role"] for row in selected}))
    seeds = sorted({row["seed"] for row in completed})
    figure.suptitle(f"{metric} by exact layer — {split} — {probe_policy}", y=1.05)
    figure.text(
        0.5,
        -0.02,
        f"Checkpoint roles: {roles}. Seeds: {seeds}; lines=mean, bars=observed min/max, faint points=each seed. "
        "Missing arms are labeled; no bootstrap interval is aggregated across seeds.",
        ha="center",
        fontsize=9,
    )
    _watermark(figure, synthetic)
    return save_figure(figure, output_base), completed, aggregates


def plot_difference_heatmaps(
    rows: list[dict[str, Any]],
    output_prefix: Path,
    *,
    metric: str,
    split: str,
    probe_policy: str,
    synthetic: bool,
) -> tuple[list[Path], list[dict[str, Any]]]:
    selected = [
        row
        for row in rows
        if row["metric"] == metric and row["split"] == split and row["probe_policy"] == probe_policy
    ]
    if not selected:
        raise ValueError("No paired differences match the requested heatmap")
    completed = [row for row in selected if row["status"] == "completed"]
    aggregates = aggregate_rows(completed, "difference")
    paths = []
    for checkpoint in sorted({row["checkpoint"] for row in selected}):
        checkpoint_rows = [row for row in selected if row["checkpoint"] == checkpoint]
        tasks = ordered_tasks(checkpoint_rows)
        layers = sorted({row["layer"] for row in checkpoint_rows}, key=layer_key)
        matrix = np.full((len(tasks), len(layers)), np.nan)
        lookup = {(row["task"], row["layer"]): row for row in aggregates if row["checkpoint"] == checkpoint}
        for i, task in enumerate(tasks):
            for j, layer in enumerate(layers):
                if (task, layer) in lookup:
                    matrix[i, j] = lookup[task, layer]["mean"]
        width = max(8, len(layers) * 0.7)
        figure, axis = plt.subplots(figsize=(width, 1.2 + len(tasks) * 0.65))
        finite = matrix[np.isfinite(matrix)]
        limit = float(np.max(np.abs(finite))) if len(finite) else 1.0
        image = axis.imshow(matrix, cmap="coolwarm", vmin=-limit, vmax=limit, aspect="auto")
        for i, task in enumerate(tasks):
            for j, layer in enumerate(layers):
                value = matrix[i, j]
                axis.text(j, i, "NA" if np.isnan(value) else f"{value:+.3f}", ha="center", va="center", fontsize=7)
        axis.set_xticks(range(len(layers)), [layer_label(layer) for layer in layers], rotation=45)
        axis.set_yticks(range(len(tasks)), tasks)
        figure.colorbar(image, ax=axis, label=f"mean {metric} difference")
        seeds = sorted({row["seed"] for row in completed if row["checkpoint"] == checkpoint})
        role = next(row["checkpoint_role"] for row in checkpoint_rows)
        axis.set_title(f"{checkpoint} ({role}) — {split} — {probe_policy}")
        figure.text(
            0.5,
            -0.03,
            f"Cell=mean over seeds {seeds}; NA=missing/not completed. Source pointwise bootstrap intervals are conditional "
            "on fitted probes and supplied groups; they are not combined across seeds.",
            ha="center",
            fontsize=9,
        )
        _watermark(figure, synthetic)
        safe_checkpoint = re.sub(r"[^A-Za-z0-9_.-]", "_", checkpoint)
        paths.extend(save_figure(figure, Path(f"{output_prefix}_{safe_checkpoint}")))
    return paths, completed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", required=True, type=Path)
    parser.add_argument("--differences", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--metric", default="auroc")
    parser.add_argument("--split", required=True)
    parser.add_argument("--probe-policy", required=True)
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = read_rows(args.metrics, METRIC_FIELDS, "value")
    profile_paths, completed, aggregates = plot_profiles(
        rows,
        args.output / "per_layer_profiles",
        metric=args.metric,
        split=args.split,
        probe_policy=args.probe_policy,
        synthetic=args.synthetic,
    )
    per_seed_fields = METRIC_FIELDS
    per_seed_path = args.output / "per_seed.csv"
    write_csv(per_seed_path, completed, per_seed_fields)
    aggregate_fields = ["task", "split", "checkpoint", "checkpoint_role", "layer", "probe_policy", "metric", "seed_n", "seeds", "mean", "min", "max"]
    aggregate_path = args.output / "seed_aggregate.csv"
    write_csv(aggregate_path, aggregates, aggregate_fields)
    difference_paths = []
    difference_completed = []
    if args.differences:
        difference_rows = read_rows(args.differences, DIFFERENCE_FIELDS, "difference")
        difference_paths, difference_completed = plot_difference_heatmaps(
            difference_rows,
            args.output / "paired_difference_heatmap",
            metric=args.metric,
            split=args.split,
            probe_policy=args.probe_policy,
            synthetic=args.synthetic,
        )
        write_csv(args.output / "paired_differences_per_seed.csv", difference_completed, DIFFERENCE_FIELDS)
    outputs = [*profile_paths, per_seed_path, aggregate_path, *difference_paths]
    if args.differences:
        outputs.append(args.output / "paired_differences_per_seed.csv")
    manifest = {
        "schema": "multiretain-figure-manifest-v1",
        "synthetic": args.synthetic,
        "metric": args.metric,
        "split": args.split,
        "probe_policy": args.probe_policy,
        "interval_scope": "pointwise conditional intervals remain in source tables; figures aggregate point estimates by seed only",
        "inputs": [
            {"path": str(path), "sha256": sha256(path)}
            for path in [args.metrics, *([args.differences] if args.differences else [])]
        ],
        "outputs": [
            {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in outputs
        ],
    }
    manifest_path = args.output / "figure_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"REPORTED {len(completed)} metric rows; {len(difference_completed)} paired rows; synthetic={args.synthetic}")


if __name__ == "__main__":
    main()
