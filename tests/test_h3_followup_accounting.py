"""Small independent-accounting fixtures, including probability ties and pairing."""
import numpy as np
import pytest
from scripts.sayyed.verify_h3_followup import rank_metrics


def test_tied_rank_auc_and_average_precision():
    m=rank_metrics(np.array([0,1,0,1]),np.array([.1,.4,.4,.9]))
    assert m['auroc']==.875
    assert m['average_precision']==pytest.approx((1+2/3)/2)
    assert m['confusion_matrix']==[[2,0],[1,1]]


def test_weighted_sequence_resampling_matches_explicit_duplicates():
    y=np.array([0,1,0,1]);p=np.array([.1,.4,.4,.9]);weights=np.array([0,3,2,1])
    a=rank_metrics(y,p,weights);b=rank_metrics(np.repeat(y,weights),np.repeat(p,weights))
    for key in ['auroc','average_precision','accuracy','balanced_accuracy']:
        assert a[key]==pytest.approx(b[key])


def test_zero_weight_top_scores_have_finite_average_precision():
    m=rank_metrics(np.array([0,1,0,1]),np.array([.1,.4,.4,.9]),np.array([2,1,1,0]))
    assert np.isfinite(m['average_precision'])


def test_pairing_keeps_identical_predictions_zero_difference():
    y=np.array([0,1,0,1]);p=np.array([.1,.4,.4,.9]);rng=np.random.default_rng(123)
    for _ in range(20):
        ix=rng.integers(4,size=12)
        if len(np.unique(y[ix]))<2:continue
        weights=np.bincount(ix,minlength=4)
        assert rank_metrics(y,p,weights)['auroc']-rank_metrics(y,p.copy(),weights)['auroc']==0


def test_missing_class_is_rejected():
    with pytest.raises(ValueError,match='Missing class'):
        rank_metrics(np.array([0,1]),np.array([.1,.9]),np.array([1,0]))
