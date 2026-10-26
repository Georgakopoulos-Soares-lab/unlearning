"""Independent saved-output accounting and frozen-head prediction reconstruction."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import torch

RUN=Path('/workspace/meeting-artifacts/sayyed-base-20261026-v1')


def auc(labels, probabilities):
    ordered=sorted(zip(probabilities,labels));rank=1;positive_rank=0.
    i=0
    while i<len(ordered):
        j=i+1
        while j<len(ordered) and ordered[j][0]==ordered[i][0]:j+=1
        average=(rank+rank+j-i-1)/2
        positive_rank+=average*sum(y for _,y in ordered[i:j])
        rank+=j-i;i=j
    positive=sum(labels);negative=len(labels)-positive
    return (positive_rank-positive*(positive+1)/2)/(positive*negative)


def main():
    torch.set_num_threads(4)
    rows=[json.loads(l) for l in (RUN/'manifest.jsonl').read_text().splitlines()]
    predictions=[json.loads(l) for l in (RUN/'predictions.jsonl').read_text().splitlines()]
    metrics=json.loads((RUN/'metrics.json').read_text());identity=json.loads((RUN/'head_execution_identity.json').read_text())
    assert len({r['id'] for r in rows})==len(rows)==len(predictions)
    saved={r['id']:r for r in predictions};arrays=[]
    for path in sorted((RUN/'chunks').glob('*.npz')):
        with np.load(path,allow_pickle=False) as a:
            assert str(a['cache_key'])==identity['feature_cache_key']
            arrays.append({k:a[k] for k in ['ids','labels','split','sequence_sha256','features','nll_sum','n_tokens']})
    a={k:np.concatenate([x[k] for x in arrays]) for k in arrays[0]}
    assert list(a['ids'])==[r['id'] for r in rows]
    for i,row in enumerate(rows):
        p=saved[row['id']]
        assert row['label']==p['label']==int(a['labels'][i])
        assert row['split']==p['split']==str(a['split'][i])
        assert hashlib.sha256(row['sequence'].encode()).hexdigest()==str(a['sequence_sha256'][i])
        assert p['n_tokens']==len(row['sequence'])-1==int(a['n_tokens'][i])
        assert p['nll_sum']==float(a['nll_sum'][i])
    selection=json.loads((RUN/'selection.json').read_text())
    chosen=max(selection['candidates'],key=lambda r:(r['dev']['auroc'],-r['step']))['step']
    assert chosen==selection['selected_step']==metrics['selected_step']
    head=torch.nn.Sequential(torch.nn.LayerNorm(1920),torch.nn.Linear(1920,1920),torch.nn.GELU(),torch.nn.Dropout(.1),torch.nn.Linear(1920,2))
    head_path=RUN/'heads'/f'step-{chosen}.pt'
    assert hashlib.sha256(head_path.read_bytes()).hexdigest()==identity['selected_head_sha256']
    head.load_state_dict(torch.load(head_path,weights_only=True));head.eval()
    checks={}
    for split in ['train','dev','test']:
        selected=[r for r in predictions if r['split']==split];labels=[r['label'] for r in selected];p=[r['probability_class1'] for r in selected]
        confusion=Counter((y,int(prob>=.5)) for y,prob in zip(labels,p))
        acc=sum(y==int(prob>=.5) for y,prob in zip(labels,p))/len(labels)
        balanced=sum(confusion[c,c]/sum(y==c for y in labels) for c in [0,1])/2
        loss=math.fsum(r['nll_sum'] for r in selected);tokens=sum(r['n_tokens'] for r in selected)
        m=dict(auroc=auc(labels,p),accuracy=acc,balanced_accuracy=balanced,class1_prevalence=sum(labels)/len(labels),
            majority_baseline=max(sum(labels),len(labels)-sum(labels))/len(labels),causal_nll=loss/tokens,lm_perplexity=math.exp(loss/tokens))
        for k,v in m.items():assert math.isclose(v,metrics['splits'][split][k],rel_tol=1e-12,abs_tol=1e-12),(split,k)
        indices=np.flatnonzero(a['split']==split)
        with torch.inference_mode():reconstructed=torch.cat([head(torch.from_numpy(a['features'][indices[i:i+256]]).float()).softmax(-1)[:,1] for i in range(0,len(indices),256)]).numpy()
        delta=max(abs(float(prob)-saved[str(a['ids'][idx])]['probability_class1']) for idx,prob in zip(indices,reconstructed))
        assert delta<=1e-7
        checks[split]=dict(examples=len(labels),independent_metrics=m,max_probability_reconstruction_delta=delta)
    result=dict(passed=True,rows_verified=len(rows),selected_step=chosen,checks=checks,
        limitations='Reconstruction uses saved frozen features; independent aggregate accounting does not regenerate GPU features')
    (RUN/'independent_verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
