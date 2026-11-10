import numpy as np
import pytest
from threadpoolctl import threadpool_limits
from scripts.sayyed.fit_multiretain_parallel import cv_fold
from scripts.sayyed.h3_followup import train_model
from scripts.sayyed.fit_maxent_extension import auc


@pytest.mark.parametrize('count', [2, 3])
def test_parallel_fold_uses_same_training_only_pipeline_and_class_order(count):
    rng = np.random.default_rng(617)
    x = rng.normal(size=(90, 9)).astype(np.float32)
    y = np.arange(90) % count
    train, validation = np.arange(60), np.arange(60, 90)
    classes = np.arange(count)
    value, attempts, cpu = cv_fold(x, y, train, validation, .1, classes)
    with threadpool_limits(limits=1):
        reference, _ = train_model(x[train], y[train], .1)
        expected = auc(y[validation], reference.predict_proba(x[validation]), classes)
    assert value == pytest.approx(expected, abs=1e-12)
    assert not attempts[-1]['warnings']
    assert cpu >= 0
