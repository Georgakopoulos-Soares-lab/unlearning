import numpy as np
import pytest
from scripts.sayyed.multiretain_independent import metrics, reconstruct
from scripts.sayyed.multiretain_metrics import bootstrap_metrics
from scripts.sayyed.h3_followup import train_model


@pytest.mark.parametrize('count', [2, 3])
def test_pairwise_audit_matches_producer_with_ties_and_missing_classes(count):
    rng = np.random.default_rng(913)
    classes = np.arange(count)
    y = np.tile(classes, 5)
    raw = rng.integers(1, 4, size=(len(y), count)).astype(float)
    p = raw/raw.sum(axis=1, keepdims=True)
    weights = rng.integers(0, 3, size=(13, len(y)))
    weights[0] = (y == 0)
    got, valid = metrics(y, p, classes, weights)
    expected, expected_valid = bootstrap_metrics(y, p, classes, weights)
    assert np.array_equal(valid, expected_valid)
    assert not valid[0]
    for key in expected:
        assert np.allclose(got[key], expected[key], rtol=0, atol=1e-12, equal_nan=True)


@pytest.mark.parametrize('count', [2, 3])
def test_saved_scaler_head_algebra_matches_predictions(count):
    rng = np.random.default_rng(104)
    x = rng.normal(size=(60, 7)).astype(np.float32)
    y = np.arange(60) % count
    model, _ = train_model(x, y, .1)
    assert np.allclose(reconstruct(model, x), model.predict_proba(x), rtol=0, atol=1e-12)
