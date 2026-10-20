"""Synthetic correctness fixtures; these are not biological benchmark results."""
import math

import pytest
import torch

from benign_pilot.metrics import aggregate, causal_nll, masked_pool


def test_hand_computed_causal_alignment():
    logits = torch.tensor([[[math.log(3), 0.], [0., math.log(4)], [9., -9.]]])
    sums, counts = causal_nll(logits, torch.tensor([[1, 0, 1]]), torch.ones(1, 3))
    assert counts == [2]
    assert sums[0] == pytest.approx(-math.log(.75) - math.log(.8), abs=1e-6)


def test_unequal_lengths_padding_and_special_targets():
    tokens = torch.tensor([[1, 2, 3, 0], [2, 1, 0, 0]])
    mask = torch.tensor([[1, 1, 1, 1], [1, 1, 0, 0]])
    sums, counts = causal_nll(torch.zeros(2, 4, 4), tokens, mask, special_ids=(0,))
    assert counts == [2, 1]
    assert sums == pytest.approx([2 * math.log(4), math.log(4)])


def test_final_partial_batch_and_zero_targets():
    results = []
    for start in range(0, 5, 2):
        size = min(2, 5-start)
        sums, counts = causal_nll(torch.zeros(size, 3, 4), torch.ones(size, 3, dtype=torch.long), torch.ones(size, 3))
        results.extend(dict(nll_sum=s, n_tokens=n) for s, n in zip(sums, counts))
    assert aggregate(results)['n_examples'] == 5
    assert aggregate(results)['n_tokens'] == 10
    with pytest.raises(ValueError, match="Zero valid"):
        causal_nll(torch.zeros(1, 1, 4), torch.ones(1, 1, dtype=torch.long), torch.ones(1, 1))


def test_corpus_aggregation_repartition_invariant():
    a = aggregate([dict(nll_sum=1., n_tokens=1), dict(nll_sum=9., n_tokens=3)])
    b = aggregate([dict(nll_sum=5., n_tokens=2), dict(nll_sum=5., n_tokens=2)])
    assert a['corpus_nll'] == b['corpus_nll'] == 2.5
    assert aggregate([dict(nll_sum=1000., n_tokens=1)])['perplexity_overflow']


def test_pool_masks_padding_and_rejects_empty():
    hidden = torch.tensor([[[1., 3.], [3., 5.], [900., 900.]]])
    assert masked_pool(hidden, torch.tensor([[1, 1, 0]])).tolist() == [[2., 4.]]
    with pytest.raises(ValueError):
        masked_pool(hidden, torch.zeros(1, 3))


def test_nonfinite_and_bad_counts_fail():
    with pytest.raises(ValueError):
        causal_nll(torch.full((1, 2, 4), float('nan')), torch.ones(1, 2, dtype=torch.long), torch.ones(1, 2))
    for row in [dict(nll_sum=float('inf'), n_tokens=2), dict(nll_sum=1., n_tokens=0)]:
        with pytest.raises(ValueError):
            aggregate([row])


def test_probe_scaler_fits_training_only_and_positive_class():
    import numpy as np
    from benign_pilot.probes import fit_probes
    x = np.array([[0.], [1.], [2.], [3.], [100.], [101.]])
    labels = np.array([0, 0, 1, 1, 0, 1])
    splits = np.array(['train']*4 + ['validation']*2)
    candidates, best, scaler, classifier = fit_probes(x, labels, splits)
    assert scaler.mean_.tolist() == [1.5]
    assert all(c['positive_class'] == 1 and c['positive_column'] == 1 for c in candidates)
    assert best == 0  # All three candidate AUROCs tie; smaller C wins.


def test_normalization_stratification_and_reverse_complements():
    from benign_pilot.data import normalize, select_indices, overlap_report
    assert normalize(' acgR\n') == 'ACGN'
    with pytest.raises(ValueError):
        normalize('AC!T')
    labels = [0]*30 + [1]*10
    selected = select_indices(labels, 20, 42)
    assert selected == sorted(selected) == select_indices(labels, 20, 42)
    assert sum(labels[i] for i in selected) == 5
    rows = [dict(id='a', split='train', full_sequence='ACGA', sequence='ACGA'),
            dict(id='b', split='validation', full_sequence='TCGT', sequence='TCGT')]
    overlap = overlap_report(rows)
    assert overlap['sequence_exact']['cross_split_groups'] == 0
    assert overlap['sequence_reverse_complement_canonical']['cross_split_groups'] == 1


def test_prepare_opens_only_official_train_and_dev(tmp_path, monkeypatch):
    import json
    import zipfile
    from benign_pilot.data import prepare
    archive = tmp_path/'synthetic.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        for split in ['train','dev']:
            z.writestr(f'GUE/EMP/H3/{split}.csv', 'sequence,label\nACGTAC,0\nTTGTAC,1\n')
        z.writestr('GUE/EMP/H3/test.csv', 'SHOULD NEVER BE READ')
    real_read = zipfile.ZipFile.read
    def checked_read(self, name, *args, **kwargs):
        assert not str(name).endswith('test.csv')
        return real_read(self,name,*args,**kwargs)
    monkeypatch.setattr(zipfile.ZipFile,'read',checked_read)
    config=dict(tasks={'gue_emp_h3':'EMP/H3'},train_size=256,validation_size=128,
                seed=42,max_length=4,data_source_revision='synthetic fixture')
    prepared=prepare(config,archive,tmp_path)
    assert prepared['samples'] == 4
    rows=[json.loads(line) for line in (tmp_path/'subset_manifest.jsonl').read_text().splitlines()]
    assert rows[0]['truncated'] and rows[0]['original_length'] == 6
    assert rows[0]['group_id'] is None


def test_multiclass_probe_uses_macro_one_vs_rest():
    import numpy as np
    from benign_pilot.probes import fit_probes
    x=np.array([[0.,0.],[1.,0.],[0.,1.],[.1,.1],[.9,.1],[.1,.9]])
    y=np.array([0,1,2,0,1,2])
    candidates, best, scaler, classifier=fit_probes(x,y,np.array(['train']*3+['validation']*3))
    assert candidates[best]['validation_auroc'] == 1.
    assert candidates[best]['auroc_definition'] == 'macro one-vs-rest'
    assert candidates[best]['positive_column'] is None


def test_runner_rejects_other_branches_and_wrong_model(monkeypatch):
    from benign_pilot import run
    monkeypatch.setattr(run, 'git', lambda *args: 'main')
    with pytest.raises(RuntimeError, match='Only experiments-ashay'):
        run.guard({})
    monkeypatch.setattr(run, 'git', lambda *args: 'experiments-ashay' if args[0]=='branch' else 'https://github.com/Georgakopoulos-Soares-lab/unlearning.git')
    with pytest.raises(ValueError, match='Original Evo2-1B'):
        run.guard(dict(model_name='evo2_7b_base'))
