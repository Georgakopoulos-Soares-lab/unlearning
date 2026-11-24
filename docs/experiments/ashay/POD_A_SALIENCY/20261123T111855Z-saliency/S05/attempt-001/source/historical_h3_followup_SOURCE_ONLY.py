"""Parameterized, CPU-only benign H3 supplemental study on immutable caches."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import time
import warnings

import joblib
import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, balanced_accuracy_score,
                             confusion_matrix, log_loss, roc_auc_score)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

from benign_pilot.extension import controls


def sha(path):
    return hashlib.file_digest(Path(path).open('rb'), 'sha256').hexdigest()


def write(path, value):
    path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def load(run):
    cfg=json.loads((run/'protocol.json').read_text());original=Path(cfg['original_run'])
    rows=[json.loads(x) for x in (original/'manifest.jsonl').read_text().splitlines()]
    if sha(original/'manifest.jsonl')!=cfg['manifest_sha256']:raise ValueError('Manifest changed')
    pieces=[]
    for name,digest in cfg['chunk_sha256'].items():
        path=original/'chunks'/name
        if sha(path)!=digest:raise ValueError('Input chunk changed')
        with np.load(path,allow_pickle=False) as a:
            if str(a['cache_key'])!=cfg['feature_cache_key']:raise ValueError('Wrong cache')
            pieces.append({k:a[k] for k in ['ids','labels','split','sequence_sha256','features','nll_sum','n_tokens']})
    arrays={k:np.concatenate([v[k] for v in pieces]) for k in pieces[0]}
    if list(arrays['ids'])!=[r['id'] for r in rows] or len(set(arrays['ids']))!=len(rows):raise ValueError('ID mismatch')
    if list(arrays['labels'])!=[r['label'] for r in rows] or list(arrays['split'])!=[r['split'] for r in rows]:raise ValueError('Label/split mismatch')
    for i,row in enumerate(rows):
        if hashlib.sha256(row['sequence'].encode()).hexdigest()!=str(arrays['sequence_sha256'][i]):raise ValueError('Sequence mismatch')
        if int(arrays['n_tokens'][i])!=len(row['sequence'])-1:raise ValueError('Causal count mismatch')
    if not np.isfinite(arrays['features']).all():raise ValueError('Nonfinite features')
    return cfg,original,rows,arrays


def freeze(original,run):
    if (run/'protocol.json').exists():raise ValueError('Protocol already frozen')
    complete=json.loads((original/'extraction_complete.json').read_text())
    identity=json.loads((original/'head_execution_identity.json').read_text())
    rows=[json.loads(x) for x in (original/'manifest.jsonl').read_text().splitlines()]
    groups={s:{r['exact_rc_group'] for r in rows if r['split']==s} for s in ['train','dev','test']}
    if any(groups[a]&groups[b] for a,b in [('train','dev'),('train','test'),('dev','test')]):raise ValueError('Cross-split group overlap')
    cfg=dict(protocol_id='benign-h3-posthoc-cached-readout-v1',frozen_utc=datetime.now(timezone.utc).isoformat(),
        original_run=str(original.resolve()),manifest_sha256=sha(original/'manifest.jsonl'),
        original_protocol_sha256=sha(original/'protocol.json'),original_head_identity=identity,
        original_predictions_sha256=sha(original/'predictions.jsonl'),feature_cache_key=complete['cache_key'],
        chunk_sha256={p.name:sha(p) for p in sorted((original/'chunks').glob('*.npz'))},
        conditions=['evo2_norm','composition','4mer'],
        features=dict(evo2_norm='Unchanged cached mean-pooled post-final RMSNorm, width1920',
            composition='ACGT counts / total canonical bases, four frequencies',
            **{'4mer':'All256 ACGT lexicographic overlapping forward-strand4mers / total canonical4mer windows'}),
        sequence_handling='Reuse exact cached manifest sequence; uppercase, no extra truncation or augmentation. No RC averaging/canonicalizing features; exact/RC identity used only for grouping.',
        selection=dict(folds=3,splitter='StratifiedGroupKFold',shuffle=True,seed=42,
            grouping='Manifest exact_rc_group; no verified biological groups available',
            C_candidates=[.1,1.,10.],criterion='Mean training-CV AUROC; exact ties choose smaller C',
            preprocessing='StandardScaler fitted only within each train fold, then all train for refit',
            refit='All11971 training rows; no dev/test fitting or selection',solver='lbfgs',
            penalty='L2',class_weight='balanced',tol=1e-4,max_iter=2000,random_state=42,
            convergence_policy='If a fit reaches iteration limit, retry identical training-only fit at10000 iterations; no other hyperparameter change; unresolved failure blocks that condition',threshold=.5),
        bootstrap=dict(seed=20261027,resamples=2000,interval='Percentile2.5/97.5',
            unit='Whole examples/exact-RC groups; manifest groups are all singletons',
            pairing='Identical resampled evaluation IDs for every fitted condition and all AUROC contrasts',
            splits=['dev','test'],metrics=['AUROC','accuracy','balanced_accuracy'],
            contrasts=[['evo2_norm','composition'],['evo2_norm','4mer'],['original_mlp','evo2_norm']],
            nll='Whole-sequence resampling, sum(loss)/sum(targets), exp for perplexity',
            qualification='Post-hoc exploratory, pointwise unadjusted intervals conditional on fitted classifiers and split; exclude training/selection uncertainty and unknown homology dependence'),
        resources=dict(threads=4,estimated_dense_input_MiB=len(rows)*(1920+256+4)*8/2**20,
            expected_peak_GiB_upper_bound=4,expected_runtime='Minutes to tens of minutes; first actual CV fit provides training-only cost estimate; no competing heavy jobs'),
        seed_sensitivity='Optional seeds17/1234 require a separately frozen amendment before their test scoring')
    write(run/'protocol.json',cfg);write(run/'protocol_hash.json',dict(sha256=sha(run/'protocol.json')))
    write(run/'execution_start.json',dict(utc=datetime.now(timezone.utc).isoformat(),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=sha(__file__),control_source_sha256=sha('benign_pilot/extension.py'),
        packages={n:importlib.metadata.version(n) for n in ['numpy','torch','scikit-learn','scipy','joblib','threadpoolctl']},
        gpu_usage_at_start=json.loads(Path('/workspace/meeting-artifacts/evo2-pilot.gpu-budget.json').read_text())['used_seconds']))
    print('PROTOCOL_FROZEN',sha(run/'protocol.json'),flush=True)


def exposure(run):
    import torch
    cfg,original,rows,a=load(run);train=np.flatnonzero(a['split']=='train');y=a['labels'][train]
    source=original/'source_snapshot/scripts/sayyed/run_h3.py'
    if sha(source)!=cfg['original_head_identity']['source_sha256']:raise ValueError('Executed sampler source mismatch')
    generator=torch.Generator().manual_seed(42)
    draws=np.stack([torch.randint(len(train),(8,),generator=generator).numpy() for _ in range(300)])
    other=torch.randint(len(train),(300,8),generator=torch.Generator().manual_seed(42)).numpy()
    if not np.array_equal(draws,other):raise ValueError('Sampler reconstruction disagreement')
    summaries=[]
    for step in [50,100,150,200,250,300]:
        d=draws[:step].reshape(-1);unique,counts=np.unique(d,return_counts=True)
        summaries.append(dict(step=step,draws=len(d),unique_rows=len(unique),fraction_seen=len(unique)/len(train),
            draw_class_counts={str(k):v for k,v in Counter(map(int,y[d])).items()},
            unique_class_counts={str(k):v for k,v in Counter(map(int,y[unique])).items()},
            repeated_draws=len(d)-len(unique),rows_drawn_more_than_once=int(np.sum(counts>1))))
    state=torch.load(original/'heads/step-250.pt',map_location='cpu',weights_only=True)
    result=dict(available_train_rows=len(train),feature_extracted_rows=len(rows),
        metric_scored_rows={s:int(np.sum(a['split']==s)) for s in ['train','dev','test']},
        selected_step=250,parameter_count=sum(t.numel() for t in state.values()),
        summaries=summaries,source_sha256=sha(source),torch_version=torch.__version__,
        sampler='Reconstructed from executed torch.Generator().manual_seed(42), 300 consecutive randint batches8; not an originally logged draw trace',
        selected_unique_ids=[str(a['ids'][train[i]]) for i in np.unique(draws[:250])],
        interpretation='Available/extracted/scored training rows differ from gradient-exposed rows; limited exposure is a protocol limitation, not an established cause of performance')
    np.savez_compressed(run/'original_sampler.npz',draw_indices_in_train=draws,train_ids=a['ids'][train])
    write(run/'training_exposure.json',result)
    print('EXPOSURE',[(x['step'],x['unique_rows']) for x in summaries],flush=True)


def metric(y,p):
    tn,fp,fn,tp=map(int,confusion_matrix(y,p>=.5,labels=[0,1]).ravel())
    return dict(examples=len(y),auroc=float(roc_auc_score(y,p)),average_precision=float(average_precision_score(y,p)),
        accuracy=float(accuracy_score(y,p>=.5)),balanced_accuracy=float(balanced_accuracy_score(y,p>=.5)),
        sensitivity=tp/(tp+fn),specificity=tn/(tn+fp),confusion_matrix=[[tn,fp],[fn,tp]],
        class1_prevalence=float(np.mean(y)),classification_cross_entropy=float(log_loss(y,p)))


def matrices(rows,a):
    return {'evo2_norm':a['features'],**controls([r['sequence'] for r in rows])}


def pipeline(c,max_iter):
    return make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',
        tol=1e-4,max_iter=max_iter,random_state=42))


def train_model(x,y,c):
    attempts=[]
    for limit in [2000,10000]:
        model=pipeline(c,limit);started=time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');model.fit(x,y)
        conv=[w for w in caught if issubclass(w.category,ConvergenceWarning)]
        attempts.append(dict(max_iter=limit,n_iter=model[-1].n_iter_.tolist(),seconds=time.perf_counter()-started,
                             warnings=[str(w.message) for w in caught]))
        if not conv:return model,attempts
    raise RuntimeError('Unresolved train-only convergence failure')


def fit(run):
    started=time.perf_counter();cpu_started=time.process_time();cfg,original,rows,a=load(run)
    indices={s:np.flatnonzero(a['split']==s) for s in ['train','dev','test']};train=indices['train'];y=a['labels']
    group=np.array([r['exact_rc_group'] for r in rows]);train_groups=group[train]
    folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42).split(np.zeros(len(train)),y[train],train_groups))
    for tr,va in folds:
        if set(train_groups[tr])&set(train_groups[va]):raise ValueError('Group leakage')
    write(run/'folds.json',[dict(train_ids=a['ids'][train[tr]].tolist(),validation_ids=a['ids'][train[va]].tolist()) for tr,va in folds])
    xs=matrices(rows,a);results={};probabilities={}
    models=run/'models';models.mkdir(exist_ok=True)
    for name in cfg['conditions']:
        x=xs[name];candidates=[];condition_started=time.perf_counter()
        for c in cfg['selection']['C_candidates']:
            scores=[];diagnostics=[]
            for fold,(tr,va) in enumerate(folds):
                model,attempts=train_model(x[train[tr]],y[train[tr]],c)
                if not np.allclose(model[0].mean_,np.mean(x[train[tr]],axis=0,dtype=np.float64),rtol=1e-10,atol=1e-10):raise ValueError('Fold scaler leakage')
                scores.append(float(roc_auc_score(y[train[va]],model.predict_proba(x[train[va]])[:,1])))
                diagnostics.append(dict(fold=fold,attempts=attempts,scaler_training_rows=len(tr),
                    scaler_mean_sha256=hashlib.sha256(model[0].mean_.tobytes()).hexdigest()))
                print('CV',name,c,fold,scores[-1],sum(t['seconds'] for t in attempts),flush=True)
                write(run/'cv_progress.json',dict(condition=name,C=c,fold=fold,seconds=time.perf_counter()-started))
            candidates.append(dict(C=c,fold_auroc=scores,mean_auroc=float(np.mean(scores)),diagnostics=diagnostics))
            write(run/(name+'_cv.partial.json'),candidates)
        selected=max(candidates,key=lambda x:(x['mean_auroc'],-x['C']))
        model,attempts=train_model(x[train],y[train],selected['C'])
        if not np.allclose(model[0].mean_,np.mean(x[train],axis=0,dtype=np.float64),rtol=1e-10,atol=1e-10):raise ValueError('Refit scaler mismatch')
        joblib.dump(model,models/(name+'.joblib'))
        np.savez_compressed(models/(name+'.parameters.npz'),scaler_mean=model[0].mean_,scaler_scale=model[0].scale_,
                            coef=model[-1].coef_,intercept=model[-1].intercept_,classes=model[-1].classes_)
        results[name]=dict(selected_C=selected['C'],candidates=candidates,refit_attempts=attempts,
            training_rows=len(train),feature_dimension=x.shape[1],wall_seconds=time.perf_counter()-condition_started,splits={})
        probabilities[name]={}
        for split in ['dev','test']:
            ix=indices[split];p=model.predict_proba(x[ix])[:,1];probabilities[name][split]=p
            results[name]['splits'][split]=metric(y[ix],p)
        write(run/'supplemental_metrics.partial.json',results)
    original_predictions={r['id']:r for r in map(json.loads,(original/'predictions.jsonl').read_text().splitlines())}
    original_metrics={}
    for split in ['dev','test']:
        ix=indices[split];p=np.array([original_predictions[str(i)]['probability_class1'] for i in a['ids'][ix]])
        original_metrics[split]=metric(y[ix],p)
    write(run/'original_metrics.json',original_metrics)
    with (run/'predictions.jsonl').open('w') as out:
        for split in ['dev','test']:
            for j,i in enumerate(indices[split]):
                row=original_predictions[str(a['ids'][i])]
                out.write(json.dumps(dict(id=str(a['ids'][i]),split=split,label=int(y[i]),
                    group=str(group[i]),sequence_sha256=str(a['sequence_sha256'][i]),
                    probabilities={'original_mlp':row['probability_class1'],**{n:float(probabilities[n][split][j]) for n in cfg['conditions']}},
                    nll_sum=float(a['nll_sum'][i]),n_tokens=int(a['n_tokens'][i])))+'\n')
    write(run/'supplemental_metrics.json',results)
    write(run/'fit_timing.json',dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu_started))
    print('FIT_COMPLETE',flush=True)


def bootstrap(run):
    started=time.perf_counter();cpu_started=time.process_time();cfg=json.loads((run/'protocol.json').read_text())
    predictions=[json.loads(x) for x in (run/'predictions.jsonl').read_text().splitlines()];result={}
    for split in ['dev','test']:
        rows=[r for r in predictions if r['split']==split];y=np.array([r['label'] for r in rows]);names=list(rows[0]['probabilities'])
        probabilities={n:np.array([r['probabilities'][n] for r in rows]) for n in names}
        groups=[r['group'] for r in rows]
        if len(set(groups))!=len(groups):raise ValueError('Protocol assumed singleton groups; amendment required')
        losses=np.array([r['nll_sum'] for r in rows]);counts=np.array([r['n_tokens'] for r in rows])
        rng=np.random.default_rng(cfg['bootstrap']['seed']);samples={n:[] for n in names};nll=[];draws=[];rejected=0
        for rep in range(2000):
            ix=rng.integers(len(rows),size=len(rows),dtype=np.int32);draws.append(ix)
            if len(np.unique(y[ix]))<2:rejected+=1;continue
            for n in names:
                p=probabilities[n][ix];samples[n].append([roc_auc_score(y[ix],p),accuracy_score(y[ix],p>=.5),balanced_accuracy_score(y[ix],p>=.5)])
            nll.append(float(losses[ix].sum()/counts[ix].sum()))
        draw_array=np.asarray(draws);np.savez_compressed(run/(split+'_bootstrap_indices.npz'),ids=np.array([r['id'] for r in rows]),indices=draw_array)
        arrays={n:np.asarray(v) for n,v in samples.items()}
        summary={}
        for n,values in arrays.items():
            observed=metric(y,probabilities[n]);summary[n]={}
            for j,key in enumerate(['auroc','accuracy','balanced_accuracy']):
                lo,hi=np.percentile(values[:,j],[2.5,97.5]);summary[n][key]=dict(estimate=observed[key],low=float(lo),high=float(hi))
        contrasts={}
        for left,right in cfg['bootstrap']['contrasts']:
            values=arrays[left][:,0]-arrays[right][:,0];lo,hi=np.percentile(values,[2.5,97.5])
            contrasts[left+' minus '+right]=dict(estimate=summary[left]['auroc']['estimate']-summary[right]['auroc']['estimate'],low=float(lo),high=float(hi))
        lo,hi=np.percentile(nll,[2.5,97.5]);point=math.fsum(map(float,losses))/sum(map(int,counts))
        result[split]=dict(examples=len(rows),seed=cfg['bootstrap']['seed'],resamples=2000,valid_resamples=len(nll),missing_class_resamples=rejected,
            index_sha256=hashlib.sha256(draw_array.tobytes()).hexdigest(),models=summary,paired_auroc_differences=contrasts,
            causal_nll=dict(estimate=point,low=float(lo),high=float(hi)),lm_perplexity=dict(estimate=math.exp(point),low=math.exp(float(lo)),high=math.exp(float(hi))))
        np.savez_compressed(run/(split+'_bootstrap_samples.npz'),**arrays,causal_nll=np.asarray(nll))
        write(run/'uncertainty.partial.json',result)
        print('BOOTSTRAP_COMPLETE',split,flush=True)
    result['qualification']=cfg['bootstrap']['qualification'];write(run/'uncertainty.json',result)
    write(run/'bootstrap_timing.json',dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu_started))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','exposure','fit','bootstrap']);p.add_argument('--run',required=True,type=Path);p.add_argument('--original',type=Path);args=p.parse_args()
    with threadpool_limits(limits=4):
        if args.stage=='freeze':freeze(args.original,args.run)
        else:{'exposure':exposure,'fit':fit,'bootstrap':bootstrap}[args.stage](args.run)


if __name__=='__main__':main()
