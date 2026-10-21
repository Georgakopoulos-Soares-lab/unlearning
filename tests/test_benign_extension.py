import numpy as np
import pytest
from benign_pilot.extension import controls, groups, fold_indices, pipeline, auc, bootstrap


def test_ambiguity_and_strand():
    x=controls(['AAAANCCCC','TTTTNGGGG'])
    assert np.allclose(x['composition'].sum(axis=1),1)
    assert np.allclose(x['4mer'].sum(axis=1),1)
    assert np.count_nonzero(x['4mer'][0])==2
    assert not np.array_equal(x['4mer'][0],x['4mer'][1])


def test_groups_and_folds():
    rows=[dict(sequence=s,full_sequence_sha256=str(i),group_id=None) for i,s in enumerate(['AAAAC','GTTTT','CCCCC'])]
    g=groups(rows);assert g[0]==g[1] and g[0]!=g[2]
    y=np.array([0,1]*30);g=np.array([str(i) for i in range(60)])
    for a,b in fold_indices(y,g):assert not set(g[a])&set(g[b])


def test_fold_scaler_and_multiclass():
    model=pipeline(1);model.fit(np.array([[0.],[1.],[2.],[3.]]),[0,1,0,1]);assert model[0].mean_[0]==1.5
    assert auc(np.array([0,1,2]),np.eye(3),np.array([0,1,2]))==1


def test_paired_bootstrap():
    y=np.array([0,1]*12);p=np.array([[.8,.2] if v==0 else [.2,.8] for v in y])
    result=bootstrap(y,{'blocks.7':p,'4mer':p},np.arange(len(y)),n=30)['blocks.7 minus 4mer']
    assert result['difference']==result['low']==result['high']==0
