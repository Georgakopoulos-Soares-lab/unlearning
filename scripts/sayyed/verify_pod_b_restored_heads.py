"""Verify packaged binary/multiclass historical heads in a fresh restored payload."""
import hashlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from scipy.special import expit
from threadpoolctl import threadpool_limits

root=Path(sys.argv[1])/'restored-head-smoke'
provenance=json.loads((root/'PROVENANCE.json').read_text())
checks=[]
with threadpool_limits(limits=1):
    for record in provenance['examples']:
        task=record['task']
        path=root/(task+'.joblib')
        assert hashlib.sha256(path.read_bytes()).hexdigest()==record['head_sha256']
        model=joblib.load(path)
        with np.load(root/(task+'.npz'),allow_pickle=False) as a:
            assert model[-1].classes_.tolist()==a['classes'].tolist()
            x=a['features'];expected=a['expected_probabilities']
            predicted=model.predict_proba(x)
            scaled=x.copy();scaled-=model[0].mean_;scaled/=model[0].scale_
            score=scaled@model[-1].coef_.T+model[-1].intercept_
            if len(a['classes'])==2:
                p=expit(score[:,0]);independent=np.column_stack([1-p,p])
            else:
                score-=score.max(axis=1,keepdims=True);p=np.exp(score);independent=p/p.sum(axis=1,keepdims=True)
            delta=max(float(np.max(np.abs(predicted-expected))),float(np.max(np.abs(independent-expected))))
            assert delta<=1e-12
            checks.append(dict(task=task,rows=len(x),max_abs_probability_delta=delta))
print(json.dumps(dict(status='PASS',checks=checks,scope='Restored historical heads; no new feature extraction or model fitting'),indent=2))
