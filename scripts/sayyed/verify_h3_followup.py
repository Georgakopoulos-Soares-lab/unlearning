"""Independent weighted-rank/contingency accounting for new H3 artifacts."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import time

import joblib
import numpy as np
from threadpoolctl import threadpool_limits
from scipy.special import expit

from .h3_followup import load, matrices, sha, write


def rank_metrics(y,p,weights=None):
    w=np.ones(len(y)) if weights is None else np.asarray(weights,dtype=float)
    order=np.argsort(p,kind='stable');sorted_p=p[order];starts=np.r_[0,np.flatnonzero(np.diff(sorted_p))+1]
    pos=np.add.reduceat((w*y)[order],starts);neg=np.add.reduceat((w*(1-y))[order],starts)
    npos=pos.sum();nneg=neg.sum()
    if npos==0 or nneg==0:raise ValueError('Missing class')
    auroc=float(np.sum(pos*(np.cumsum(neg)-neg+.5*neg))/(npos*nneg))
    # Integrate descending-score precision at each recall jump, including tied scores together.
    dp=pos[::-1];dn=neg[::-1];den=np.cumsum(dp)+np.cumsum(dn)
    precision=np.divide(np.cumsum(dp),den,out=np.zeros_like(den),where=den>0)
    ap=float(np.sum(dp/npos*precision))
    predicted=p>=.5;tp=float(np.sum(w*y*predicted));tn=float(np.sum(w*(1-y)*(~predicted)))
    return dict(auroc=auroc,average_precision=ap,accuracy=(tp+tn)/(npos+nneg),
                balanced_accuracy=.5*(tp/npos+tn/nneg),sensitivity=tp/npos,specificity=tn/nneg,
                confusion_matrix=[[int(tn),int(nneg-tn)],[int(npos-tp),int(tp)]],class1_prevalence=npos/(npos+nneg))


def verify(run):
    started=time.perf_counter();cpu_started=time.process_time();cfg,original,manifest,a=load(run)
    if sha(run/'protocol.json')!=json.loads((run/'protocol_hash.json').read_text())['sha256']:raise ValueError('Protocol changed')
    predictions=[json.loads(x) for x in (run/'predictions.jsonl').read_text().splitlines()]
    if len({r['id'] for r in predictions})!=len(predictions):raise ValueError('Duplicate prediction IDs')
    by_id={r['id']:r for r in manifest};new_metrics=json.loads((run/'supplemental_metrics.json').read_text())
    original_metrics=json.loads((run/'original_metrics.json').read_text());uncertainty=json.loads((run/'uncertainty.json').read_text())
    for row in predictions:
        reference=by_id[row['id']]
        if reference['label']!=row['label'] or reference['split']!=row['split'] or reference['exact_rc_group']!=row['group']:raise ValueError('Prediction identity mismatch')
    train=np.flatnonzero(a['split']=='train');folds=json.loads((run/'folds.json').read_text());train_ids=set(a['ids'][train]);eval_ids={r['id'] for r in predictions}
    seen=[];lookup={str(v):i for i,v in enumerate(a['ids'])}
    for fold in folds:
        tr=set(fold['train_ids']);va=set(fold['validation_ids'])
        if tr&va or tr|va!=train_ids or (tr|va)&eval_ids:raise ValueError('Fold leakage')
        if {by_id[i]['exact_rc_group'] for i in tr}&{by_id[i]['exact_rc_group'] for i in va}:raise ValueError('Fold group leakage')
        seen.extend(va)
    if Counter(seen)!=Counter(train_ids):raise ValueError('CV validation coverage')
    xs=matrices(manifest,a);reconstruction={};independent={}
    for name in cfg['conditions']:
        model=joblib.load(run/'models'/(name+'.joblib'));x=xs[name]
        expected=np.mean(x[train],axis=0,dtype=np.float64)
        if not np.allclose(model[0].mean_,expected,rtol=1e-10,atol=1e-10):raise ValueError('Refit scaler training scope')
        candidates=new_metrics[name]['candidates'];choice=max(candidates,key=lambda v:(v['mean_auroc'],-v['C']))['C']
        if choice!=new_metrics[name]['selected_C'] or model[-1].C!=choice:raise ValueError('Selection rule')
        if any(any(attempt['warnings'] for attempt in fold['attempts'][-1:]) for c in candidates for fold in c['diagnostics']):raise ValueError('Unresolved CV warning')
        deltas={}
        for split in ['dev','test']:
            selected=[r for r in predictions if r['split']==split];ix=np.array([lookup[r['id']] for r in selected])
            saved=np.array([r['probabilities'][name] for r in selected]);loaded=model.predict_proba(x[ix])[:,1]
            standardized=x[ix].copy();standardized-=model[0].mean_.astype(standardized.dtype);standardized/=model[0].scale_.astype(standardized.dtype)
            logits=(standardized@model[-1].coef_.T+model[-1].intercept_)[:,0];manual=expit(logits)
            delta=float(np.max(np.abs(saved-loaded)));manual_delta=float(np.max(np.abs(saved-manual)))
            if delta>1e-12 or manual_delta>1e-10:raise ValueError('Pipeline reconstruction')
            deltas[split]=dict(saved_vs_loaded_max_abs=delta,saved_vs_affine_sigmoid_max_abs=manual_delta)
        reconstruction[name]=deltas
    for split in ['dev','test']:
        rows=[r for r in predictions if r['split']==split];y=np.array([r['label'] for r in rows]);names=list(rows[0]['probabilities']);probs={n:np.array([r['probabilities'][n] for r in rows]) for n in names}
        point={}
        for name in names:
            independent_metrics=rank_metrics(y,probs[name]);recorded=original_metrics[split] if name=='original_mlp' else new_metrics[name]['splits'][split]
            for key,v in independent_metrics.items():
                if key=='confusion_matrix':
                    if v!=recorded[key]:raise ValueError('Confusion mismatch')
                elif not math.isclose(v,recorded[key],abs_tol=1e-12,rel_tol=1e-12):raise ValueError('Metric mismatch '+key)
            eps=np.finfo(np.float64).eps;p=np.clip(probs[name],eps,1-eps)
            ce=-math.fsum(float(t*math.log(q)+(1-t)*math.log1p(-q)) for t,q in zip(y,p))/len(y)
            ce_tolerance=16*np.finfo(np.float32).eps if name=='evo2_norm' else 1e-12
            if not math.isclose(ce,recorded['classification_cross_entropy'],rel_tol=0,abs_tol=ce_tolerance):raise ValueError('Cross-entropy mismatch')
            independent_metrics['classification_cross_entropy_abs_delta']=abs(ce-recorded['classification_cross_entropy'])
            independent_metrics['classification_cross_entropy_tolerance']=float(ce_tolerance)
            independent_metrics['classification_cross_entropy']=ce;point[name]=independent_metrics
        with np.load(run/(split+'_bootstrap_indices.npz'),allow_pickle=False) as b:
            ids=b['ids'];draws=b['indices']
        if list(ids)!=[r['id'] for r in rows] or draws.shape!=(2000,len(rows)):raise ValueError('Bootstrap ID alignment')
        expected_rng=np.random.default_rng(cfg['bootstrap']['seed'])
        if not np.array_equal(draws,expected_rng.integers(len(rows),size=draws.shape,dtype=np.int32)):raise ValueError('Bootstrap seed/order')
        with np.load(run/(split+'_bootstrap_samples.npz'),allow_pickle=False) as b:samples={k:b[k] for k in b.files}
        maximum=0.;losses=np.array([r['nll_sum'] for r in rows]);counts=np.array([r['n_tokens'] for r in rows])
        for j,indices in enumerate(draws):
            weights=np.bincount(indices,minlength=len(rows))
            for name in names:
                m=rank_metrics(y,probs[name],weights);values=np.array([m[k] for k in ['auroc','accuracy','balanced_accuracy']])
                maximum=max(maximum,float(np.max(np.abs(values-samples[name][j]))))
            nll=float(np.dot(weights,losses)/np.dot(weights,counts));maximum=max(maximum,abs(nll-float(samples['causal_nll'][j])))
        if maximum>1e-12:raise ValueError('Independent paired bootstrap mismatch')
        for left,right in cfg['bootstrap']['contrasts']:
            delta=samples[left][:,0]-samples[right][:,0];lo,hi=np.percentile(delta,[2.5,97.5]);c=uncertainty[split]['paired_auroc_differences'][left+' minus '+right]
            if not np.allclose([lo,hi],[c['low'],c['high']],atol=1e-12,rtol=0):raise ValueError('Paired interval mismatch')
        independent[split]=dict(examples=len(rows),metrics=point,paired_resamples_verified=2000,weighted_rank_bootstrap_max_abs_delta=maximum)
    exposure=json.loads((run/'training_exposure.json').read_text())
    with np.load(run/'original_sampler.npz',allow_pickle=False) as b:
        draws=b['draw_indices_in_train'];ids=b['train_ids']
    if list(ids)!=list(a['ids'][train]):raise ValueError('Sampler ID order')
    for row in exposure['summaries']:
        d=draws[:row['step']].reshape(-1)
        if len(d)!=row['draws'] or len(set(d))!=row['unique_rows']:raise ValueError('Exposure counts')
    seed_checks=verify_seeds(run,a) if (run/'seed_results.json').exists() else {}
    result=dict(passed=True,seed_checks=seed_checks,method='Independent weighted-rank AUROC/AP, contingency metrics, explicit cross entropy, affine-sigmoid pipeline reconstruction, all2000 paired resamples per split; no refitting or GPU inference',
        fold_training_ids_verified=len(train_ids),evaluation_rows_verified=len(predictions),pipeline_reconstruction=reconstruction,splits=independent,
        original_selected_unique_training_rows=exposure['summaries'][4]['unique_rows'])
    write(run/'verification.json',result);write(run/'verification_timing.json',dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu_started))
    print('FOLLOWUP_VERIFIED',len(predictions),flush=True)



def verify_seeds(run,a):
    import torch
    torch.set_num_threads(4)
    values=json.loads((run/'seed_results.json').read_text());lookup={str(v):i for i,v in enumerate(a['ids'])};result={}
    for seed,record in values.items():
        expected=max(record['trajectory'],key=lambda v:(v['dev']['auroc'],-v['step']))['step']
        if expected!=record['selected_step']:raise ValueError('Seed selection rule')
        path=run/'seed_sensitivity'/f'seed-{seed}-selected.pt'
        if sha(path)!=record['selected_head_sha256']:raise ValueError('Seed head hash')
        head=torch.nn.Sequential(torch.nn.LayerNorm(1920),torch.nn.Linear(1920,1920),torch.nn.GELU(),torch.nn.Dropout(.1),torch.nn.Linear(1920,2))
        head.load_state_dict(torch.load(path,weights_only=True,map_location='cpu'));head.eval();deltas={}
        rows=[json.loads(x) for x in (run/'seed_sensitivity'/f'seed-{seed}-predictions.jsonl').read_text().splitlines()]
        for split in ['dev','test']:
            selected=[r for r in rows if r['split']==split];ix=np.array([lookup[r['id']] for r in selected]);y=a['labels'][ix]
            if list(y)!=[r['label'] for r in selected]:raise ValueError('Seed label alignment')
            with torch.inference_mode():p=torch.cat([head(torch.from_numpy(a['features'][ix[i:i+256]]).float()).softmax(-1)[:,1] for i in range(0,len(ix),256)]).numpy()
            saved=np.array([r['probability_class1'] for r in selected]);delta=float(np.max(abs(saved-p)))
            if delta!=0:raise ValueError('Seed saved-head probability reconstruction')
            m=rank_metrics(y,saved)
            for key in ['auroc','accuracy','balanced_accuracy','average_precision']:
                if not math.isclose(m[key],record['metrics'][split][key],abs_tol=1e-12,rel_tol=1e-12):raise ValueError('Seed metrics')
            deltas[split]=delta
        result[seed]=dict(selected_step=expected,reconstructed_probability_max_abs=deltas)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    with threadpool_limits(limits=4):verify(a.run)


if __name__=='__main__':main()
