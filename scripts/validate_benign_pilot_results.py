"""Reconstruct saved probes and aggregate metrics without a GPU or Evo2 import."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benign_pilot.metrics import aggregate


def validate(run):
    manifest = [json.loads(line) for line in (run/'subset_manifest.jsonl').read_text().splitlines()]
    checks = []
    for task in json.loads((run/'config.json').read_text())['tasks']:
        directory = run/task
        result = json.loads((directory/'complete.json').read_text())
        selected = [r for r in manifest if r['task']==task]
        metrics = [json.loads(line) for line in (directory/'per_example_metrics.jsonl').read_text().splitlines()]
        assert [r['id'] for r in metrics] == [r['id'] for r in selected], task
        assert all(r['n_tokens']==m['scored_length']-1 for r,m in zip(metrics,selected)), task
        for split in ['train','validation']:
            assert aggregate([r for r in metrics if r['split']==split]) == result['nll'][split], task
        features = np.load(directory/'features.npz',allow_pickle=False)
        assert features['cache_key'].item() == result['cache_key'], task
        validation = np.array([r['split']=='validation' for r in selected])
        labels = np.array([r['label'] for r in selected])
        for row in result['probes']:
            if not row['selected']:
                continue
            saved = np.load(directory/(row['layer']+'.probe.npz'),allow_pickle=False)
            scaler = StandardScaler()
            scaler.mean_,scaler.scale_ = saved['mean'],saved['scale']
            scaler.n_features_in_ = len(saved['mean'])
            classifier = LogisticRegression(C=row['C'],class_weight='balanced',solver='lbfgs')
            classifier.coef_,classifier.intercept_,classifier.classes_ = saved['coef'],saved['intercept'],saved['classes']
            classifier.n_features_in_ = len(saved['mean'])
            probabilities = classifier.predict_proba(scaler.transform(features[row['layer']][validation]))
            if len(classifier.classes_)==2:
                score=roc_auc_score(labels[validation],probabilities[:,int(np.flatnonzero(classifier.classes_==1).item())])
            else:
                score=roc_auc_score(labels[validation],probabilities,labels=classifier.classes_,multi_class='ovr',average='macro')
            assert score==row['validation_auroc'], (task,row['layer'],score,row['validation_auroc'])
            checks.append(dict(task=task,layer=row['layer'],reconstructed_auroc=score,exact_match=True))
    result = dict(samples_verified=len(manifest),checks=checks,all_passed=True)
    (run/'artifact_validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    validate(parser.parse_args().run_dir)
