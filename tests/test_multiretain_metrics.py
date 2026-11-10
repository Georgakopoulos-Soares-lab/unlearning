import numpy as np
import pytest
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             log_loss, roc_auc_score)
from scripts.sayyed.multiretain_metrics import bootstrap_metrics, group_resampling, decisions


@pytest.mark.parametrize('classes', [np.array([0, 1]), np.array([0, 1, 2])])
def test_weighted_ties_match_explicit_resampled_sklearn_metrics(classes):
    y = np.tile(classes, 4)
    rng = np.random.default_rng(271)
    raw = rng.integers(1, 4, size=(len(y), len(classes))).astype(float)
    p = raw / raw.sum(1, keepdims=True)
    # Ensure exact zero/one probabilities and ties are included.
    p[0] = 0
    p[0, 0] = 1
    names, inverse, draws, weights = group_resampling(np.array(['g'+str(i//2) for i in range(len(y))]), repetitions=17)
    got, valid = bootstrap_metrics(y, p, classes, weights)
    for b, counts in enumerate(weights):
        ix = np.repeat(np.arange(len(y)), counts.astype(int))
        yy, pp = y[ix], p[ix]
        if len(np.unique(yy)) != len(classes):
            assert not valid[b]
            assert all(np.isnan(value[b]) for value in got.values())
            continue
        binary = len(classes) == 2
        expected = dict(auroc=roc_auc_score(yy, pp[:, 1]) if binary else
                        roc_auc_score(yy, pp, labels=classes, multi_class='ovr', average='macro'),
                        average_precision=average_precision_score(yy, pp[:, 1]) if binary else
                        np.mean([average_precision_score(yy == c, pp[:, i]) for i, c in enumerate(classes)]),
                        accuracy=accuracy_score(yy, decisions(pp, classes)),
                        balanced_accuracy=balanced_accuracy_score(yy, decisions(pp, classes)),
                        classification_cross_entropy=log_loss(yy, pp, labels=classes))
        for key in expected:
            assert got[key][b] == pytest.approx(expected[key], abs=1e-12)
