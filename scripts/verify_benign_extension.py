"""Read-only saved-result verification for the new extension; no GPU or refitting."""
import hashlib,json,math
from pathlib import Path
import joblib
import numpy as np
from benign_pilot.extension import controls,auc,groups,write
from benign_pilot.data import eligibility_for_run

run=Path('/workspace/meeting-artifacts/evo2-extension-20261021T0942');config=json.loads((run/'config.json').read_text());rows=[json.loads(l) for l in (run/'subset_manifest.jsonl').read_text().splitlines()];identity=json.loads((run/'extraction_identity.json').read_text())
checks={}
for task in config['tasks']:
    selected=[r for r in rows if r['task']==task];ids=[r['id'] for r in selected];tr=np.array([r['split']=='train' for r in selected]);dv=~tr;y=np.array([r['label'] for r in selected]);g=groups(selected)
    if not eligibility_for_run(config,run,rows)[task]['eligible'] or set(g[tr])&set(g[dv]):raise ValueError('Task ineligible')
    source=np.load(run/task/'features.npz',allow_pickle=False)
    assert source['ids'].tolist()==ids and source['labels'].tolist()==y.tolist()
    assert source['split'].tolist()==[r['split'] for r in selected]
    assert source['sequence_sha256'].tolist()==[r['scored_prefix_sha256'] for r in selected]
    assert json.loads(source['extraction_identity'].item())==identity
    expectedkey=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();assert source['cache_key'].item()==expectedkey
    x=controls([r['sequence'] for r in selected]);x.update({k:source[k] for k in config['layers']})
    out=run/'expanded_matched'/task;metrics=json.loads((out/'metrics.json').read_text());preds=[json.loads(l) for l in (out/'predictions.jsonl').read_text().splitlines()]
    assert [r['id'] for r in preds]==[r['id'] for r in selected if r['split']=='validation']
    assert [r['label'] for r in preds]==y[dv].tolist()
    folds=json.loads((out/'folds.json').read_text());trainids={r['id'] for r in selected if r['split']=='train'};seen=[]
    idgroup={r['id']:v for r,v in zip(selected,g)}
    for a,b in folds:
        assert set(a)|set(b)==trainids and not set(a)&set(b)
        assert not {idgroup[i] for i in a}&{idgroup[i] for i in b};seen+=b
    assert len(seen)==len(set(seen))==int(tr.sum()) and set(seen)==trainids
    methods={}
    for name,features in x.items():
        assert features.shape[0]==len(selected) and np.isfinite(features).all()
        if name in config['layers']:assert features.shape==(len(selected),1920)
        m=metrics[name];best=max(m['candidates'],key=lambda c:c['mean_fold_auroc']);assert best['C']==m['C']
        for c in m['candidates']:assert len(c['fold_auroc'])==5 and abs(np.mean(c['fold_auroc'])-c['mean_fold_auroc'])<1e-14
        model=joblib.load(out/(name+'.joblib'));p=model.predict_proba(features[dv]);saved=np.array([r['probabilities'][name] for r in preds]);delta=float(np.max(np.abs(p-saved)))
        assert delta<=1e-12 and abs(auc(y[dv],p,model[-1].classes_)-m['auroc'])<=1e-12
        assert np.allclose(model[0].mean_,np.mean(features[tr].astype(float),axis=0),atol=1e-10,rtol=1e-10)
        methods[name]=dict(auroc=m['auroc'],prediction_max_abs_delta=delta,C=m['C'],converged=m['converged'])
    losses=[json.loads(l) for l in (run/task/'per_example_metrics.jsonl').read_text().splitlines()];assert [r['id'] for r in losses]==ids
    complete=json.loads((run/task/'extraction_complete.json').read_text());assert complete['cache_key']==expectedkey
    likelihood={}
    for s in ['train','validation']:
        pairs=[(r,l) for r,l in zip(selected,losses) if r['split']==s];assert all(l['n_tokens']==r['scored_length']-1 and math.isfinite(l['nll_sum']) and l['split']==r['split'] for r,l in pairs)
        total=math.fsum(l['nll_sum'] for r,l in pairs);count=sum(l['n_tokens'] for r,l in pairs);nll=total/count;expected=complete['nll'][s]
        assert expected['n_tokens']==count and abs(expected['corpus_nll']-nll)<1e-12 and abs(expected['perplexity']-math.exp(nll))<1e-12
        likelihood[s]=dict(n_examples=len(pairs),targets=count,nll_sum=total,corpus_nll=nll,perplexity=math.exp(nll))
    checks[task]=dict(methods=methods,likelihood=likelihood,identities_and_folds_verified=True)
write(run/'new_saved_result_verification.json',dict(all_passed=True,tasks=checks,examples=len(rows),scope='new saved IDs, labels, hashes, feature finite shapes, grouped folds, scaler means, selected C, probability reconstruction/AUROC, independent likelihood accounting; no refit or GPU regeneration'))
print(json.dumps(checks,indent=2))
