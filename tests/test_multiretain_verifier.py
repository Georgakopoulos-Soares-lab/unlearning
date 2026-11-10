import csv
import hashlib
import json

import joblib
import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from scripts.sayyed.multiretain_verifier import (
    binary_metrics,
    classification_metrics,
    load_complete_unit,
    reconstruct_linear_predictions,
    sha256,
    verify_folds,
    verify_lm_aggregates,
    verify_paired_bootstrap,
    verify_prediction_metrics,
    verify_selection,
    verify_unit,
)


def synthetic_unit(tmp_path, reverse_predictions=False):
    labels = [0, 0, 1, 1]
    scores = [0.1, 0.4, 0.6, 0.9]
    manifest = []
    predictions = []
    for index, (label, score) in enumerate(zip(labels, scores)):
        row_id = f"synthetic-{index}"
        sequence_hash = hashlib.sha256(row_id.encode()).hexdigest()
        manifest.append(
            {
                "id": row_id,
                "task": "SYNTHETIC",
                "split": "dev",
                "label": label,
                "exact_rc_group": f"group-{index}",
                "sequence_sha256": sequence_hash,
            }
        )
        predictions.append(
            {
                "id": row_id,
                "task": "SYNTHETIC",
                "split": "dev",
                "label": label,
                "group": f"group-{index}",
                "sequence_sha256": sequence_hash,
                "classes": [0, 1],
                "probabilities": {"base_refit": [1 - score, score]},
            }
        )
    if reverse_predictions:
        predictions.reverse()
    paths = {
        "protocol": tmp_path / "protocol.json",
        "manifest": tmp_path / "manifest.jsonl",
        "predictions": tmp_path / "predictions.jsonl",
        "metrics": tmp_path / "metrics.csv",
    }
    for role in ("manifest", "predictions"):
        rows = manifest if role == "manifest" else predictions
        paths[role].write_text("".join(json.dumps(row) + "\n" for row in rows))
    paths["protocol"].write_text(
        json.dumps({"manifest_sha256": sha256(paths["manifest"])}) + "\n"
    )
    with paths["metrics"].open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["model", "task", "split", "layer", "metric", "value"]
        )
        writer.writeheader()
        for metric in ("auroc", "average_precision", "accuracy", "balanced_accuracy"):
            writer.writerow(
                {
                    "model": "base_refit",
                    "task": "SYNTHETIC",
                    "split": "dev",
                    "layer": "decoder.layers.0",
                    "metric": metric,
                    "value": 1,
                }
            )
    receipt = {
        "schema": "multiretain-unit-v1",
        "status": "COMPLETE",
        "unit": {
            "task": "SYNTHETIC",
            "split": "dev",
            "checkpoint": "synthetic-base",
            "layer": "decoder.layers.0",
            "seed": 42,
            "probe_policy": "independent_refit",
        },
        "files": [
            {
                "role": role,
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for role, path in paths.items()
        ],
    }
    receipt_path = tmp_path / "COMPLETE.json"
    receipt_path.write_text(json.dumps(receipt) + "\n")
    return receipt_path, manifest, predictions, paths


def test_tied_rank_auroc_and_average_precision():
    result = binary_metrics(
        np.array([0, 0, 1, 1]), np.array([0.2, 0.2, 0.2, 0.8])
    )
    assert result["auroc"] == pytest.approx(0.75)
    assert result["average_precision"] == pytest.approx(0.75)
    assert result["confusion_matrix"] == [[2, 0], [1, 1]]


def test_reversed_class_columns_rejected():
    with pytest.raises(ValueError, match="sorted"):
        classification_metrics(
            np.array([0, 1]), np.array([[0.8, 0.2], [0.2, 0.8]]), [1, 0]
        )


def test_missing_class_rejected():
    with pytest.raises(ValueError, match="both classes"):
        binary_metrics(np.array([0, 0]), np.array([0.2, 0.8]))


def test_multiclass_macro_ovr_and_confusion():
    labels = np.array([0, 1, 2])
    probabilities = np.eye(3) * 0.7 + 0.1
    result = classification_metrics(labels, probabilities, [0, 1, 2])
    assert result["auroc"] == pytest.approx(1.0)
    assert result["accuracy"] == pytest.approx(1.0)
    assert result["balanced_accuracy"] == pytest.approx(1.0)
    assert result["confusion_matrix"] == np.eye(3).tolist()


def test_shuffled_prediction_ids_pass_end_to_end(tmp_path):
    receipt_path, _, _, _ = synthetic_unit(tmp_path, reverse_predictions=True)
    result = verify_unit(receipt_path)
    assert result["status"] == "PASS"
    assert result["prediction_verification"]["evaluation_rows"] == 4


def test_nonfinite_scores_rejected(tmp_path):
    _, manifest, predictions, _ = synthetic_unit(tmp_path)
    predictions[0]["probabilities"]["base_refit"][1] = float("nan")
    metric_rows = [
        {"model": "base_refit", "split": "dev", "layer": "decoder.layers.0", "metric": "auroc", "value": "1"}
    ]
    with pytest.raises(ValueError, match="Nonfinite"):
        verify_prediction_metrics(
            manifest, predictions, metric_rows, evaluation_split="dev", layer="decoder.layers.0"
        )


def test_mismatched_manifest_hash_rejected(tmp_path):
    receipt_path, _, _, paths = synthetic_unit(tmp_path)
    original = paths["manifest"].read_text()
    paths["manifest"].write_text(original.replace('"dev"', '"tev"', 1))
    with pytest.raises(ValueError, match="hash mismatch"):
        load_complete_unit(receipt_path)


def test_incomplete_unit_rejected(tmp_path):
    receipt_path, _, _, _ = synthetic_unit(tmp_path)
    receipt = json.loads(receipt_path.read_text())
    receipt["status"] = "PARTIAL"
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError, match="COMPLETE"):
        load_complete_unit(receipt_path)


def test_unequal_lm_target_counts_use_token_weighting():
    losses = [
        {"id": "a", "nll_sum": 2.0, "n_tokens": 2},
        {"id": "b", "nll_sum": 4.0, "n_tokens": 1},
    ]
    rows = [
        {"model": "base", "split": "dev", "layer": "backbone", "metric": "causal_nll", "value": "2"},
        {"model": "base", "split": "dev", "layer": "backbone", "metric": "perplexity", "value": str(np.exp(2))},
    ]
    result = verify_lm_aggregates(losses, rows, model="base", split="dev")
    assert result["valid_targets"] == 3
    assert result["causal_nll"] == 2


def test_fold_group_leakage_rejected():
    manifest = [
        {"id": "a", "split": "train", "exact_rc_group": "same"},
        {"id": "b", "split": "train", "exact_rc_group": "same"},
        {"id": "c", "split": "dev", "exact_rc_group": "other"},
    ]
    folds = [{"train_ids": ["a"], "validation_ids": ["b"]}]
    with pytest.raises(ValueError, match="group leakage"):
        verify_folds(folds, manifest, "dev")


def test_selection_uses_smaller_c_on_tie():
    selection = {
        "candidates": [
            {"C": 0.1, "scores": [0.8, 0.6], "mean_auroc": 0.7, "training_scope": "train_only"},
            {"C": 1.0, "scores": [0.7, 0.7], "mean_auroc": 0.7, "training_scope": "train_only"},
        ],
        "selected_C": 0.1,
    }
    assert verify_selection(selection) == 0.1
    selection["selected_C"] = 1.0
    with pytest.raises(ValueError, match="tie rule"):
        verify_selection(selection)


def test_linear_reconstruction_and_id_alignment(tmp_path):
    features = np.array([[0, 0], [0, 1], [1, 0], [2, 2]], dtype=np.float32)
    labels = np.array([0, 0, 1, 1])
    model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0))
    model.fit(features, labels)
    ids = ["a", "b", "c", "d"]
    np.savez(tmp_path / "features.npz", ids=np.array(ids), features=features)
    joblib.dump(model, tmp_path / "model.joblib")
    saved = model.predict_proba(features)
    result = reconstruct_linear_predictions(
        tmp_path / "features.npz",
        tmp_path / "model.joblib",
        saved,
        ids,
        feature_dtype="float32",
        coefficient_dtype="float64",
        tolerance=2e-8,
    )
    assert result["max_abs_delta"] < 2e-8
    with pytest.raises(ValueError, match="ID order"):
        reconstruct_linear_predictions(
            tmp_path / "features.npz",
            tmp_path / "model.joblib",
            saved,
            list(reversed(ids)),
            feature_dtype="float32",
            coefficient_dtype="float64",
            tolerance=2e-8,
        )


def test_paired_bootstrap_reconstructs_ids_groups_and_seed(tmp_path):
    predictions = []
    for index, (label, base, post) in enumerate(
        [(0, 0.1, 0.2), (0, 0.3, 0.4), (1, 0.6, 0.7), (1, 0.9, 0.8)]
    ):
        predictions.append(
            {
                "id": f"id-{index}",
                "label": label,
                "group": f"group-{index}",
                "classes": [0, 1],
                "probabilities": {
                    "base_refit": [1 - base, base],
                    "post_refit": [1 - post, post],
                },
            }
        )
    ids = np.array([row["id"] for row in predictions])
    groups = np.array([row["group"] for row in predictions])
    draws = np.random.default_rng(20261103).integers(4, size=(5, 4), dtype=np.int32)
    values = []
    for draw in draws:
        weights = np.bincount(draw, minlength=4)
        labels = np.array([row["label"] for row in predictions])
        base = classification_metrics(
            labels,
            np.array([row["probabilities"]["base_refit"] for row in predictions]),
            [0, 1],
            weights,
        )["auroc"]
        post = classification_metrics(
            labels,
            np.array([row["probabilities"]["post_refit"] for row in predictions]),
            [0, 1],
            weights,
        )["auroc"]
        values.append(post - base)
    low, high = np.quantile(values, [0.025, 0.975])
    np.savez(
        tmp_path / "bootstrap.npz",
        ids=ids[::-1],
        group_names=groups,
        row_groups=np.arange(4)[::-1],
        group_draws=draws,
        post_refit=np.array(values),
    )
    comparisons = [
        {"probe": "post_refit", "ci_low": str(low), "ci_high": str(high), "rejected": "0"}
    ]
    result = verify_paired_bootstrap(
        predictions,
        comparisons,
        tmp_path / "bootstrap.npz",
        baseline_probe="base_refit",
        seed=20261103,
        resamples=5,
    )
    assert result["max_abs_delta"] == 0
    assert result["contrasts"]["post_refit"]["accepted_resamples"] == 5


def test_valid_training_folds_pass():
    manifest = [
        {"id": "a", "split": "train", "exact_rc_group": "ga"},
        {"id": "b", "split": "train", "exact_rc_group": "gb"},
        {"id": "c", "split": "dev", "exact_rc_group": "gc"},
    ]
    folds = [{"train_ids": ["b"], "validation_ids": ["a"]}, {"train_ids": ["a"], "validation_ids": ["b"]}]
    assert verify_folds(folds, manifest, "dev") == {"folds": 2, "training_ids": 2}
