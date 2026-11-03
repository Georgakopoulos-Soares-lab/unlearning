"""Paired frozen-backbone logistic evaluation; test reuse is exploratory."""
import argparse,csv,hashlib,json,time
from pathlib import Path
import joblib,numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from threadpoolctl import threadpool_limits
from scripts.sayyed.h3_followup import train_model,metric,write,sha

def arrays(path,manifest):
    path=Path(path);identity=json.loads((path/'identity.json').read_text());done=json.loads((path/'complete.json').read_text())
    pieces=[]
    for f in sorted(path.glob('chunk_*.npz')):
        with np.load(f,allow_pickle=False) as a:
            if str(a['cache_key'])!=identity['cache_key']:raise ValueError('Wrong cache key')
            pieces.append({k:a[k] for k in a.files if k!='cache_key'})
    out={k:np.concatenate([x[k] for x in pieces]) for k in pieces[0]}
    if done['examples']!=len(manifest) or out['ids'].tolist()!=[r['id'] for r in manifest]:raise ValueError('Row association mismatch')
    if out['labels'].tolist()!=[r['label'] for r in manifest] or out['split'].tolist()!=[r['split'] for r in manifest]:raise ValueError('Label/split mismatch')
    if out['sequence_sha256'].tolist()!=[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in manifest]:raise ValueError('Sequence mismatch')
    return out,identity

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--post',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    started=time.monotonic();cpu_started=time.process_time();run=Path(args.output);run.mkdir(parents=True,exist_ok=True);(run/'models').mkdir(exist_ok=True)
    rows=list(map(json.loads,Path(args.manifest).read_text().splitlines()));base,bi=arrays(args.base,rows);post,pi=arrays(args.post,rows)
    if bi['cache_key']==pi['cache_key'] or bi['checkpoint']==pi['checkpoint']:raise ValueError('Model cache collision')
    y=base['labels'];splits=base['split'];tr=np.flatnonzero(splits=='train');groups=np.array([r['exact_rc_group'] for r in rows]);folds=list(StratifiedGroupKFold(n_splits=3,shuffle=True,random_state=42).split(tr,y[tr],groups[tr]))
    if [int(sum(splits==s)) for s in ['train','dev','test']]!=[11971,1497,1497]:raise ValueError('Unexpected H3 split counts')
    for a,b in [('train','dev'),('train','test'),('dev','test')]:
        if set(groups[splits==a])&set(groups[splits==b]):raise ValueError('Cross-split exact/RC group')
    protocol=dict(task='EMP/H3',status='exploratory reused test',base=bi,post=pi,manifest_sha256=sha(args.manifest),selection='3 identical training-only grouped stratified CV folds; balanced L2; fold-local StandardScaler; C=.1,1,10; smaller-C ties; seed42; all-train refit',threshold=.5,bootstrap_seed=20261103,bootstrap_repetitions=2000,source_sha256=sha(__file__),lineage='reference comparison; parent checksum lineage unverified')
    pp=run/'protocol.json'
    if pp.exists() and json.loads(pp.read_text())!=protocol:raise ValueError('Protocol changed')
    write(pp,protocol);write(run/'folds.json',[dict(train_ids=base['ids'][tr[a]].tolist(),validation_ids=base['ids'][tr[b]].tolist()) for a,b in folds])
    metrics=[];predictions=[];comparisons=[]
    for name,arr in [('base',base),('maxent',post)]:
        for split in ['dev','test']:
            ix=np.flatnonzero(splits==split);nll=float(np.sum(arr['nll_sum'][ix],dtype=np.float64)/np.sum(arr['n_tokens'][ix]))
            for key,value in [('causal_nll',nll),('perplexity',float(np.exp(nll)))]:metrics.append(dict(model=name,task='EMP/H3',split=split,layer='backbone',probe='none',metric=key,value=value))
    for layer in ['final_norm','decoder_layer_16']:
        if np.array_equal(base[layer],post[layer]):raise ValueError('Identical base/post features; investigate source')
        models={}
        for name,arr in [('base',base),('maxent',post)]:
            fit_started=time.monotonic();fit_cpu_started=time.process_time();x=arr[layer];candidates=[]
            with threadpool_limits(limits=4):
                for c in [.1,1.,10.]:
                    scores=[]
                    for a,b in folds:
                        model,attempts=train_model(x[tr[a]],y[tr[a]],c)
                        if attempts[-1]['warnings']:raise ValueError('CV warning')
                        scores.append(float(roc_auc_score(y[tr[b]],model.predict_proba(x[tr[b]])[:,1])))
                    candidates.append(dict(C=c,scores=scores,mean_auroc=float(np.mean(scores))))
                    write(run/(name+'_'+layer+'_cv.json'),candidates)
                chosen=max(candidates,key=lambda v:(v['mean_auroc'],-v['C']))['C'];model,attempts=train_model(x[tr],y[tr],chosen)
                if attempts[-1]['warnings']:raise ValueError('Refit warning')
            joblib.dump(model,run/'models'/f'{name}_{layer}.joblib');models[name]=model
            write(run/f'{name}_{layer}_fit_timing.json',dict(wall_seconds=time.monotonic()-fit_started,cpu_seconds=time.process_time()-fit_cpu_started))
            print(name,layer,'selected C',chosen,flush=True)
        for split in ['dev','test']:
            ix=np.flatnonzero(splits==split)
            probs={'base_refit':models['base'].predict_proba(base[layer][ix])[:,1], 'maxent_refit':models['maxent'].predict_proba(post[layer][ix])[:,1], 'maxent_fixed_base':models['base'].predict_proba(post[layer][ix])[:,1]}
            for condition,p in probs.items():
                m=metric(y[ix],p)
                for key in ['auroc','accuracy','balanced_accuracy','average_precision','classification_cross_entropy']:
                    metrics.append(dict(model=condition,task='EMP/H3',split=split,layer=layer,probe='logistic',metric=key,value=m[key]))
            for j,i in enumerate(ix):predictions.append(dict(id=str(base['ids'][i]),label=int(y[i]),split=split,layer=layer,group=str(groups[i]),probabilities={n:float(p[j]) for n,p in probs.items()}))
            # The fixed H3 exact/RC groups are singleton here; do not imply homology independence.
            if len(set(groups[ix]))!=len(ix):raise ValueError('Non-singleton groups require grouped bootstrap amendment')
            rng=np.random.default_rng(20261103);draws=rng.integers(len(ix),size=(2000,len(ix)),dtype=np.int32);samples={n:[] for n in ['maxent_refit','maxent_fixed_base']};rejected=0
            for draw in draws:
                yy=y[ix][draw]
                if len(np.unique(yy))<2:rejected+=1;continue
                base_auc=roc_auc_score(yy,probs['base_refit'][draw])
                for n in samples:samples[n].append(float(roc_auc_score(yy,probs[n][draw])-base_auc))
            np.savez_compressed(run/f'{layer}_{split}_bootstrap.npz',ids=base['ids'][ix],indices=draws,**{k:np.array(v) for k,v in samples.items()})
            for n,values in samples.items():
                lo,hi=np.quantile(values,[.025,.975]);comparisons.append(dict(task='EMP/H3',split=split,layer=layer,probe=n,metric='auroc',difference=float(roc_auc_score(y[ix],probs[n])-roc_auc_score(y[ix],probs['base_refit'])),ci_low=float(lo),ci_high=float(hi),status='paired conditional exploratory; singleton sequence resampling; no homology groups',rejected=rejected))
        with (run/'predictions.jsonl').open('w') as f:
            for r in predictions:f.write(json.dumps(r)+'\n')
        for filename,records in [('metrics.csv',metrics),('paired_comparisons.csv',comparisons)]:
            with (run/filename).open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
        write(run/(layer+'_complete.json'),dict(wall_seconds=time.monotonic()-started))
    with (run/'predictions.jsonl').open('w') as f:
        for r in predictions:f.write(json.dumps(r)+'\n')
    for name,records in [('metrics.csv',metrics),('paired_comparisons.csv',comparisons)]:
        with (run/name).open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
    write(run/'fit_complete.json',dict(cpu_seconds=time.process_time()-cpu_started,wall_seconds=time.monotonic()-started,prediction_rows=len(predictions),source_sha256=sha(__file__)))
if __name__=='__main__':main()
