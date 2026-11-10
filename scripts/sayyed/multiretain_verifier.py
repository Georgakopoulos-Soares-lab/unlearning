"""Contract-driven, independent CPU checks for finalized benign artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import joblib
import numpy as np


METRIC_TOLERANCE = 1e-12
PROBABILITY_TOLERANCE = 1e-12


def sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"Blank JSONL row at {path}:{line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"Non-object JSONL row at {path}:{line_number}")
            rows.append(row)
    if not rows:
        raise ValueError(f"Empty JSONL file: {path}")
    return rows


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Empty CSV file: {path}")
    return rows


def load_complete_unit(path: str | Path) -> tuple[dict[str, Any], dict[str, Path]]:
    receipt_path = Path(path)
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("schema") != "multiretain-unit-v1":
        raise ValueError("Unexpected unit schema")
    if receipt.get("status") != "COMPLETE":
        raise ValueError("Only COMPLETE producer units are eligible")
    files = receipt.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Complete unit must enumerate files")
    roles: dict[str, Path] = {}
    for entry in files:
        role = entry.get("role")
        file_path = Path(entry.get("path", ""))
        if not role or not file_path.is_absolute():
            raise ValueError("Every artifact needs a role and absolute path")
        if role in roles:
            raise ValueError(f"Duplicate artifact role: {role}")
        if not file_path.is_file():
            raise ValueError(f"Missing artifact: {file_path}")
        if file_path.stat().st_size != entry.get("bytes"):
            raise ValueError(f"Artifact size mismatch: {file_path}")
        if sha256(file_path) != entry.get("sha256"):
            raise ValueError(f"Artifact hash mismatch: {file_path}")
        roles[role] = file_path
    for role in ("protocol", "manifest", "predictions", "metrics"):
        if role not in roles:
            raise ValueError(f"Missing required artifact role: {role}")
    return receipt, roles


def _weights(n: int, weights: np.ndarray | None) -> np.ndarray:
    if weights is None:
        return np.ones(n, dtype=np.float64)
    result = np.asarray(weights, dtype=np.float64)
    if result.shape != (n,) or not np.isfinite(result).all() or (result < 0).any():
        raise ValueError("Invalid observation weights")
    if result.sum() <= 0:
        raise ValueError("Weights must have positive mass")
    return result


def binary_metrics(
    labels: np.ndarray,
    scores: np.ndarray,
    weights: np.ndarray | None = None,
) -> dict[str, Any]:
    y = np.asarray(labels)
    p = np.asarray(scores, dtype=np.float64)
    if y.ndim != 1 or p.shape != y.shape:
        raise ValueError("Binary labels and scores must be aligned vectors")
    if not np.isin(y, [0, 1]).all():
        raise ValueError("Binary labels must be 0/1")
    if not np.isfinite(p).all():
        raise ValueError("Nonfinite scores")
    w = _weights(len(y), weights)
    order = np.argsort(p, kind="stable")
    sorted_p = p[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_p)) + 1]
    positive = np.add.reduceat((w * y)[order], starts)
    negative = np.add.reduceat((w * (1 - y))[order], starts)
    n_positive = float(positive.sum())
    n_negative = float(negative.sum())
    if n_positive == 0 or n_negative == 0:
        raise ValueError("AUROC requires both classes")
    auroc = float(
        np.sum(positive * (np.cumsum(negative) - negative + 0.5 * negative))
        / (n_positive * n_negative)
    )
    descending_positive = positive[::-1]
    descending_negative = negative[::-1]
    denominator = np.cumsum(descending_positive) + np.cumsum(descending_negative)
    precision = np.divide(
        np.cumsum(descending_positive),
        denominator,
        out=np.zeros_like(denominator),
        where=denominator > 0,
    )
    average_precision = float(
        np.sum(descending_positive / n_positive * precision)
    )
    predicted = p >= 0.5
    true_positive = float(np.sum(w * y * predicted))
    true_negative = float(np.sum(w * (1 - y) * ~predicted))
    confusion = [
        [true_negative, n_negative - true_negative],
        [n_positive - true_positive, true_positive],
    ]
    if weights is None:
        confusion = [[int(value) for value in row] for row in confusion]
    return {
        "auroc": auroc,
        "average_precision": average_precision,
        "accuracy": (true_positive + true_negative) / (n_positive + n_negative),
        "balanced_accuracy": 0.5
        * (true_positive / n_positive + true_negative / n_negative),
        "sensitivity": true_positive / n_positive,
        "specificity": true_negative / n_negative,
        "confusion_matrix": confusion,
    }


def validate_probabilities(
    probabilities: np.ndarray, classes: list[int]
) -> np.ndarray:
    p = np.asarray(probabilities, dtype=np.float64)
    if p.ndim != 2 or p.shape[1] != len(classes):
        raise ValueError("Probability/class-column shape mismatch")
    if classes != sorted(set(classes)):
        raise ValueError("Class columns must be unique and sorted")
    if not np.isfinite(p).all():
        raise ValueError("Nonfinite probabilities")
    if (p < 0).any() or (p > 1).any():
        raise ValueError("Probabilities outside [0,1]")
    if not np.allclose(p.sum(axis=1), 1, rtol=0, atol=PROBABILITY_TOLERANCE):
        raise ValueError("Probability rows do not sum to one")
    return p


def classification_metrics(
    labels: np.ndarray,
    probabilities: np.ndarray,
    classes: list[int],
    weights: np.ndarray | None = None,
) -> dict[str, Any]:
    y = np.asarray(labels)
    p = validate_probabilities(probabilities, classes)
    if y.ndim != 1 or len(y) != len(p) or not np.isin(y, classes).all():
        raise ValueError("Labels are incompatible with probability columns")
    w = _weights(len(y), weights)
    class_counts = {c: float(w[y == c].sum()) for c in classes}
    if any(count == 0 for count in class_counts.values()):
        raise ValueError("Every declared class must have positive evaluation mass")
    if len(classes) == 2:
        return binary_metrics(y == classes[1], p[:, 1], weights)
    recalls = []
    correct = 0.0
    predicted_labels = np.argmax(p, axis=1)
    for index, label in enumerate(classes):
        selected = y == label
        recall_numerator = float(w[selected & (predicted_labels == index)].sum())
        recalls.append(recall_numerator / class_counts[label])
        correct += recall_numerator
    one_vs_rest = [
        binary_metrics((y == label).astype(int), p[:, index], w)["auroc"]
        for index, label in enumerate(classes)
    ]
    return {
        "auroc": float(np.mean(one_vs_rest)),
        "accuracy": correct / float(w.sum()),
        "balanced_accuracy": float(np.mean(recalls)),
        "confusion_matrix": np.asarray(
            [
                [
                    float(w[(y == actual) & (np.argmax(p, axis=1) == predicted)].sum())
                    for predicted in range(len(classes))
                ]
                for actual in classes
            ]
        ).tolist(),
    }


def _prediction_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return str(row["task"]), str(row["split"]), str(row["id"])


def verify_prediction_metrics(
    manifest: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
    metric_rows: list[dict[str, str]],
    *,
    evaluation_split: str,
    layer: str,
    tolerance: float = METRIC_TOLERANCE,
) -> dict[str, Any]:
    manifest_by_key = {_prediction_key(row): row for row in manifest}
    if len(manifest_by_key) != len(manifest):
        raise ValueError("Duplicate manifest identity")
    prediction_by_key = {_prediction_key(row): row for row in predictions}
    if len(prediction_by_key) != len(predictions):
        raise ValueError("Duplicate prediction identity")
    expected = {
        key for key, row in manifest_by_key.items() if row["split"] == evaluation_split
    }
    if not expected or set(prediction_by_key) != expected:
        raise ValueError("Prediction coverage does not match the evaluation manifest")
    for key, row in prediction_by_key.items():
        reference = manifest_by_key[key]
        if row["label"] != reference["label"]:
            raise ValueError(f"Prediction label mismatch: {key}")
        if row.get("group") != reference.get("exact_rc_group"):
            raise ValueError(f"Prediction group mismatch: {key}")
        if row.get("sequence_sha256") != reference.get("sequence_sha256"):
            raise ValueError(f"Prediction sequence hash mismatch: {key}")
    ordered = [prediction_by_key[key] for key in sorted(prediction_by_key)]
    classes = ordered[0].get("classes")
    if not isinstance(classes, list) or not all(isinstance(c, int) for c in classes):
        raise ValueError("Prediction classes must be a sorted integer list")
    labels = np.asarray([row["label"] for row in ordered], dtype=int)
    probe_names = set(ordered[0].get("probabilities", {}))
    if not probe_names:
        raise ValueError("No probe probabilities saved")
    recorded: dict[tuple[str, str], float] = {}
    for row in metric_rows:
        if row["split"] == evaluation_split and row["layer"] == layer:
            key = (row["model"], row["metric"])
            if key in recorded:
                raise ValueError(f"Duplicate recorded metric: {key}")
            value = float(row["value"])
            if not math.isfinite(value):
                raise ValueError("Nonfinite recorded metric")
            recorded[key] = value
    checked = {}
    for row in ordered:
        if row.get("classes") != classes or set(row["probabilities"]) != probe_names:
            raise ValueError("Inconsistent class/probe schema")
    for probe in sorted(probe_names):
        probabilities = validate_probabilities(
            np.asarray([row["probabilities"][probe] for row in ordered]), classes
        )
        metrics = classification_metrics(labels, probabilities, classes)
        expected_metrics = {"auroc", "accuracy", "balanced_accuracy"}
        if len(classes) == 2:
            expected_metrics.add("average_precision")
        for name in expected_metrics:
            if (probe, name) not in recorded:
                raise ValueError(f"Missing recorded metric: {probe}/{name}")
            if not math.isclose(
                metrics[name], recorded[probe, name], rel_tol=0, abs_tol=tolerance
            ):
                raise ValueError(f"Independent metric mismatch: {probe}/{name}")
        if (probe, "classification_cross_entropy") in recorded:
            epsilon = np.finfo(np.float64).eps
            clipped = np.clip(probabilities, epsilon, 1 - epsilon)
            class_index = {label: index for index, label in enumerate(classes)}
            chosen = np.asarray(
                [clipped[i, class_index[label]] for i, label in enumerate(labels)]
            )
            cross_entropy = float(-np.mean(np.log(chosen)))
            if not math.isclose(
                cross_entropy,
                recorded[probe, "classification_cross_entropy"],
                rel_tol=0,
                abs_tol=tolerance,
            ):
                raise ValueError(f"Classification CE mismatch: {probe}")
            metrics["classification_cross_entropy"] = cross_entropy
        checked[probe] = metrics
    return {
        "evaluation_rows": len(ordered),
        "evaluation_split": evaluation_split,
        "layer": layer,
        "classes": classes,
        "probes": checked,
        "score_direction": "binary sorted class 1; multiclass macro one-vs-rest",
        "binary_threshold": 0.5,
    }


def verify_folds(
    folds: list[dict[str, Any]], manifest: list[dict[str, Any]], evaluation_split: str
) -> dict[str, int]:
    train = {str(row["id"]): row for row in manifest if row["split"] == "train"}
    evaluation = {
        str(row["id"]) for row in manifest if row["split"] == evaluation_split
    }
    if not folds or not train:
        raise ValueError("Training folds and training manifest rows are required")
    validation_occurrences: Counter[str] = Counter()
    for fold in folds:
        training_ids = set(map(str, fold["train_ids"]))
        validation_ids = set(map(str, fold["validation_ids"]))
        if len(training_ids) != len(fold["train_ids"]) or len(validation_ids) != len(
            fold["validation_ids"]
        ):
            raise ValueError("Duplicate ID within fold")
        if training_ids & validation_ids or training_ids | validation_ids != set(train):
            raise ValueError("Fold does not partition training IDs")
        if (training_ids | validation_ids) & evaluation:
            raise ValueError("Evaluation ID in training folds")
        training_groups = {train[row]["exact_rc_group"] for row in training_ids}
        validation_groups = {train[row]["exact_rc_group"] for row in validation_ids}
        if training_groups & validation_groups:
            raise ValueError("Fold group leakage")
        validation_occurrences.update(validation_ids)
    if validation_occurrences != Counter(train.keys()):
        raise ValueError("Each training ID must be validated exactly once")
    return {"folds": len(folds), "training_ids": len(train)}


def verify_selection(selection: dict[str, Any]) -> float:
    candidates = selection.get("candidates")
    if not candidates:
        raise ValueError("Missing train-only selection candidates")
    for candidate in candidates:
        scores = candidate.get("scores")
        if not scores or not np.isfinite(scores).all():
            raise ValueError("Invalid candidate CV scores")
        expected = float(np.mean(scores))
        if not math.isclose(expected, candidate["mean_auroc"], rel_tol=0, abs_tol=1e-15):
            raise ValueError("Candidate mean AUROC mismatch")
        if candidate.get("training_scope") != "train_only":
            raise ValueError("Candidate must declare train_only scope")
    selected = max(candidates, key=lambda row: (row["mean_auroc"], -row["C"]))["C"]
    if selected != selection.get("selected_C"):
        raise ValueError("Selected C violates the frozen tie rule")
    return float(selected)


def reconstruct_linear_predictions(
    features_path: str | Path,
    model_path: str | Path,
    saved_probabilities: np.ndarray,
    expected_ids: list[str],
    *,
    feature_dtype: str,
    coefficient_dtype: str,
    tolerance: float = 1e-10,
) -> dict[str, Any]:
    with np.load(features_path, allow_pickle=False) as features:
        ids = features["ids"].astype(str).tolist()
        matrix = features["features"]
    if ids != expected_ids:
        raise ValueError("Feature/prediction ID order mismatch")
    if str(matrix.dtype) != feature_dtype or not np.isfinite(matrix).all():
        raise ValueError("Feature dtype or finiteness mismatch")
    model = joblib.load(model_path)
    scaler = model[0]
    classifier = model[-1]
    if str(classifier.coef_.dtype) != coefficient_dtype:
        raise ValueError("Coefficient dtype mismatch")
    if not np.isfinite(classifier.coef_).all() or not np.isfinite(classifier.intercept_).all():
        raise ValueError("Nonfinite fitted model")
    standardized = matrix.copy()
    standardized -= scaler.mean_.astype(standardized.dtype)
    standardized /= scaler.scale_.astype(standardized.dtype)
    logits = standardized @ classifier.coef_.astype(np.float64).T + classifier.intercept_.astype(
        np.float64
    )
    if logits.shape[1] == 1:
        positive = 1 / (1 + np.exp(-logits[:, 0]))
        reconstructed = np.column_stack([1 - positive, positive])
    else:
        shifted = logits - logits.max(axis=1, keepdims=True)
        exponential = np.exp(shifted)
        reconstructed = exponential / exponential.sum(axis=1, keepdims=True)
    saved = np.asarray(saved_probabilities, dtype=np.float64)
    if saved.shape != reconstructed.shape:
        raise ValueError("Saved/reconstructed probability shape mismatch")
    maximum = float(np.max(np.abs(saved - reconstructed)))
    if maximum > tolerance:
        raise ValueError("Saved linear probabilities do not reconstruct")
    return {
        "rows": len(ids),
        "feature_dtype": feature_dtype,
        "coefficient_dtype": coefficient_dtype,
        "max_abs_delta": maximum,
        "tolerance": tolerance,
        "standardization_dtype": feature_dtype,
        "affine_and_probability_dtype": "float64",
    }


def verify_lm_aggregates(
    losses: list[dict[str, Any]],
    metric_rows: list[dict[str, str]],
    *,
    model: str,
    split: str,
) -> dict[str, float | int]:
    ids = [str(row["id"]) for row in losses]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate loss IDs")
    loss_sum = math.fsum(float(row["nll_sum"]) for row in losses)
    target_count = sum(int(row["n_tokens"]) for row in losses)
    if target_count <= 0 or any(int(row["n_tokens"]) <= 0 for row in losses):
        raise ValueError("LM target counts must be positive")
    if not math.isfinite(loss_sum) or loss_sum < 0:
        raise ValueError("Invalid LM loss sum")
    nll = loss_sum / target_count
    expected = {
        row["metric"]: float(row["value"])
        for row in metric_rows
        if row["model"] == model and row["split"] == split and row["layer"] == "backbone"
    }
    for metric, value in (("causal_nll", nll), ("perplexity", math.exp(nll))):
        if metric not in expected or not math.isclose(
            value, expected[metric], rel_tol=0, abs_tol=METRIC_TOLERANCE
        ):
            raise ValueError(f"LM aggregate mismatch: {metric}")
    return {"sequences": len(losses), "valid_targets": target_count, "causal_nll": nll}


def verify_paired_bootstrap(
    predictions: list[dict[str, Any]],
    comparisons: list[dict[str, str]],
    bootstrap_path: str | Path,
    *,
    baseline_probe: str,
    seed: int,
    resamples: int,
    tolerance: float = METRIC_TOLERANCE,
) -> dict[str, Any]:
    by_id = {str(row["id"]): row for row in predictions}
    if len(by_id) != len(predictions):
        raise ValueError("Duplicate prediction IDs")
    with np.load(bootstrap_path, allow_pickle=False) as saved:
        ids = saved["ids"].astype(str).tolist()
        group_names = saved["group_names"].astype(str)
        row_groups = saved["row_groups"]
        draws = saved["group_draws"]
        arrays = {name: saved[name] for name in saved.files if name in {r["probe"] for r in comparisons}}
    if set(ids) != set(by_id) or len(ids) != len(by_id):
        raise ValueError("Bootstrap/prediction ID coverage mismatch")
    rows = [by_id[row_id] for row_id in ids]
    labels = np.asarray([row["label"] for row in rows])
    classes = rows[0]["classes"]
    row_group_labels = np.asarray([str(row["group"]) for row in rows])
    if (
        len(set(group_names)) != len(group_names)
        or row_groups.shape != (len(rows),)
        or not np.issubdtype(row_groups.dtype, np.integer)
        or (row_groups < 0).any()
        or (row_groups >= len(group_names)).any()
        or not np.array_equal(group_names[row_groups], row_group_labels)
    ):
        raise ValueError("Bootstrap group identity mismatch")
    expected_draws = np.random.default_rng(seed).integers(
        len(group_names), size=(resamples, len(group_names)), dtype=np.int32
    )
    if not np.array_equal(draws, expected_draws):
        raise ValueError("Bootstrap seed/resample definition mismatch")
    probabilities = {
        name: np.asarray([row["probabilities"][name] for row in rows])
        for name in {baseline_probe, *[row["probe"] for row in comparisons]}
    }
    maximum = 0.0
    results = {}
    for comparison in comparisons:
        probe = comparison["probe"]
        values = []
        rejected = 0
        for draw in draws:
            weights = np.bincount(draw, minlength=len(group_names))[row_groups]
            if any(weights[labels == label].sum() == 0 for label in classes):
                rejected += 1
                continue
            baseline = classification_metrics(
                labels, probabilities[baseline_probe], classes, weights
            )["auroc"]
            compared = classification_metrics(
                labels, probabilities[probe], classes, weights
            )["auroc"]
            values.append(compared - baseline)
        if probe not in arrays or not np.array_equal(
            np.asarray(values), arrays[probe]
        ):
            delta = float(np.max(np.abs(np.asarray(values) - arrays[probe])))
            maximum = max(maximum, delta)
            if delta > tolerance:
                raise ValueError("Paired bootstrap values mismatch")
        low, high = np.quantile(values, [0.025, 0.975])
        if not np.allclose(
            [low, high],
            [float(comparison["ci_low"]), float(comparison["ci_high"])],
            rtol=0,
            atol=tolerance,
        ):
            raise ValueError("Paired interval mismatch")
        if rejected != int(comparison["rejected"]):
            raise ValueError("Rejected-resample count mismatch")
        results[probe] = {"accepted_resamples": len(values), "rejected": rejected}
    return {
        "resample_seed": seed,
        "requested_resamples": resamples,
        "max_abs_delta": maximum,
        "contrasts": results,
        "scope": "conditional on fitted probes and supplied groups; not seed uncertainty",
    }


def verify_unit(receipt_path: str | Path) -> dict[str, Any]:
    receipt, roles = load_complete_unit(receipt_path)
    protocol = json.loads(roles["protocol"].read_text())
    if protocol.get("manifest_sha256") != sha256(roles["manifest"]):
        raise ValueError("Protocol manifest hash mismatch")
    unit = receipt.get("unit")
    if not isinstance(unit, dict):
        raise ValueError("Unit identity must be an object")
    manifest = read_jsonl(roles["manifest"])
    predictions = read_jsonl(roles["predictions"])
    metric_rows = read_csv(roles["metrics"])
    result: dict[str, Any] = {
        "status": "PASS",
        "receipt": str(receipt_path),
        "unit": unit,
        "prediction_verification": verify_prediction_metrics(
            manifest,
            predictions,
            metric_rows,
            evaluation_split=unit["split"],
            layer=unit["layer"],
        ),
        "scope": "saved-output computational verification; not GPU replication or scientific validation",
    }
    if "folds" in roles:
        result["fold_verification"] = verify_folds(
            json.loads(roles["folds"].read_text()), manifest, unit["split"]
        )
    if "selection" in roles:
        result["selected_C"] = verify_selection(
            json.loads(roles["selection"].read_text())
        )
    if "losses" in roles:
        result["lm_verification"] = verify_lm_aggregates(
            read_jsonl(roles["losses"]),
            metric_rows,
            model=unit["checkpoint"],
            split=unit["split"],
        )
    if "linear_model" in receipt:
        config = receipt["linear_model"]
        probe = config["probe"]
        saved = np.asarray(
            [row["probabilities"][probe] for row in predictions]
        )
        if config.get("source_model_sha256") != sha256(roles[config["model_role"]]):
            raise ValueError("Fixed-base model identity mismatch")
        result["linear_reconstruction"] = reconstruct_linear_predictions(
            roles[config["features_role"]],
            roles[config["model_role"]],
            saved,
            [str(row["id"]) for row in predictions],
            feature_dtype=config["feature_dtype"],
            coefficient_dtype=config["coefficient_dtype"],
            tolerance=float(config.get("tolerance", 1e-10)),
        )
    if "bootstrap" in roles:
        result["paired_verification"] = verify_paired_bootstrap(
            predictions,
            read_csv(roles["contrasts"]),
            roles["bootstrap"],
            baseline_probe=receipt["baseline_probe"],
            seed=int(protocol["bootstrap_seed"]),
            resamples=int(protocol["bootstrap_resamples"]),
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = verify_unit(args.unit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"VERIFIED {args.unit}")


if __name__ == "__main__":
    main()
