"""Paired benign official-dev probes with binary / macro-OVR metrics."""
import argparse,csv,json,time
from pathlib import Path
import joblib,numpy as np
from sklearn.metrics import roc_auc_score,accuracy_score,balanced_accuracy_score,average_precision_score,log_loss
from sklearn.model_selection import StratifiedGroupKFold
from threadpoolctl import threadpool_limits
from scripts.sayyed.fit_maxent_benign import arrays
from scripts.sayyed.h3_followup import train_model,write,sha

def auc(y,p,classes):
    return float(roc_auc_score(y,p[:,1])) if len(classes)==2 else float(roc_auc_score(y,p,multi_class='ovr',average='macro',labels=classes))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--post',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();run=Path(a.output);run.mkdir(parents=True,exist_ok=True);(run/'models').mkdir(exist_ok=True)
    rows=list(map(json.loads,Path(a.manifest).read_text().splitlines()));base,bi=arrays(a.base,rows);post,pi=arrays(a.post,rows)
    if bi['cache_key']==pi['cache_key']:raise ValueError('Cache collision')
    y=base['labels'];tasks=np.array([r['task'] for r in rows]);groups=np.array([r['exact_rc_group'] for r in rows]);splits=base['split'];metrics=[];comparisons=[];predictions=[]
    protocol=dict(base=bi,post=pi,manifest_sha256=sha(a.manifest),source_sha256=sha(__file__),selection='5 identical task-local grouped stratified training folds; balanced L2 logistic, fold-local scaler; C=.1,1,10; smaller-C ties; all-train refit; seed42',decision='binary p(class1)>=.5; multiclass argmax with sorted numeric classes',auroc='binary class1; multiclass macro one-vs-rest',bootstrap_seed=20261103,bootstrap_repetitions=2000,bootstrap='2000 paired exact/RC-group resamples; conditional on fitted heads, no homology guarantee',comparison='reference models; immutable parent lineage unresolved')
    write(run/'protocol.json',protocol);started=time.monotonic();cpu_started=time.process_time()
    for task in sorted(set(tasks)):
        tr=np.flatnonzero((tasks==task)&(splits=='train'));dv=np.flatnonzero((tasks==task)&(splits=='dev'));classes=np.unique(y[tr]);C=len(classes)
        if len(tr)!=1024 or len(dv)!=512 or set(groups[tr])&set(groups[dv]):raise ValueError('Task split/overlap mismatch')
        folds=list(StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42).split(tr,y[tr],groups[tr]));write(run/f'{task}_folds.json',[dict(train_ids=base['ids'][tr[x]].tolist(),validation_ids=base['ids'][tr[z]].tolist()) for x,z in folds])
        for name,arr in [('base',base),('maxent',post)]:
            nll=float(np.sum(arr['nll_sum'][dv],dtype=np.float64)/np.sum(arr['n_tokens'][dv]))
            for key,val in [('causal_nll',nll),('perplexity',float(np.exp(nll)))]:metrics.append(dict(model=name,task=task,split='dev',layer='backbone',probe='none',metric=key,value=val))
        for layer in ['final_norm','decoder_layer_16']:
            if np.array_equal(base[layer][dv],post[layer][dv]):raise ValueError('Identical features; investigate')
            models={}
            for name,arr in [('base',base),('maxent',post)]:
                candidates=[];start=time.monotonic()
                with threadpool_limits(limits=4):
                    for c in [.1,1.,10.]:
                        scores=[]
                        for x,z in folds:
                            model,attempts=train_model(arr[layer][tr[x]],y[tr[x]],c)
                            if attempts[-1]['warnings']:raise ValueError('CV warning')
                            scores.append(auc(y[tr[z]],model.predict_proba(arr[layer][tr[z]]),classes))
                        candidates.append(dict(C=c,scores=scores,mean_auroc=float(np.mean(scores))))
                        write(run/f'{task}_{name}_{layer}_cv.json',candidates)
                    chosen=max(candidates,key=lambda c:(c['mean_auroc'],-c['C']))['C'];model,attempts=train_model(arr[layer][tr],y[tr],chosen)
                    if attempts[-1]['warnings']:raise ValueError('Refit warning')
                if not np.array_equal(model.classes_,classes):raise ValueError('Class ordering mismatch')
                joblib.dump(model,run/'models'/f'{task}_{name}_{layer}.joblib');models[name]=model;write(run/f'{task}_{name}_{layer}_fit_timing.json',dict(wall_seconds=time.monotonic()-start,selected_C=chosen));print(task,name,layer,'C',chosen,flush=True)
            probs={'base_refit':models['base'].predict_proba(base[layer][dv]),'maxent_refit':models['maxent'].predict_proba(post[layer][dv]),'maxent_fixed_base':models['base'].predict_proba(post[layer][dv])}
            for name,p in probs.items():
                if not np.isfinite(p).all() or not np.allclose(p.sum(1),1):raise ValueError('Invalid probability matrix')
                pred=(p[:,1]>=.5).astype(int) if C==2 else classes[p.argmax(1)]
                m=dict(auroc=auc(y[dv],p,classes),accuracy=float(accuracy_score(y[dv],pred)),balanced_accuracy=float(balanced_accuracy_score(y[dv],pred)),classification_cross_entropy=float(log_loss(y[dv],p,labels=classes)))
                if C==2:m['average_precision']=float(average_precision_score(y[dv],p[:,1]))
                metrics.extend(dict(model=name,task=task,split='dev',layer=layer,probe='logistic',metric=k,value=v) for k,v in m.items())
            for j,i in enumerate(dv):predictions.append(dict(id=str(base['ids'][i]),task=task,split='dev',layer=layer,label=int(y[i]),group=str(groups[i]),classes=classes.tolist(),probabilities={n:p[j].tolist() for n,p in probs.items()}))
            unique,inverse=np.unique(groups[dv],return_inverse=True);rng=np.random.default_rng(20261103);draws=rng.integers(len(unique),size=(2000,len(unique)),dtype=np.int32);members=[np.flatnonzero(inverse==i) for i in range(len(unique))];samples={n:[] for n in ['maxent_refit','maxent_fixed_base']};rejected=0
            for draw in draws:
                ix=np.concatenate([members[g] for g in draw]);yy=y[dv][ix]
                if len(np.unique(yy))!=C:rejected+=1;continue
                ba=auc(yy,probs['base_refit'][ix],classes)
                for n in samples:samples[n].append(auc(yy,probs[n][ix],classes)-ba)
            np.savez_compressed(run/f'{task}_{layer}_bootstrap.npz',ids=base['ids'][dv],group_names=unique,row_groups=inverse,group_draws=draws,**{k:np.array(v) for k,v in samples.items()})
            for name,v in samples.items():
                lo,hi=np.quantile(v,[.025,.975]);comparisons.append(dict(task=task,split='dev',layer=layer,probe=name,metric='auroc',difference=auc(y[dv],probs[name],classes)-auc(y[dv],probs['base_refit'],classes),ci_low=float(lo),ci_high=float(hi),status='paired conditional exploratory exact/RC-group resampling; homology unknown',rejected=rejected))
            with (run/'predictions.jsonl').open('w') as f:
                for r in predictions:f.write(json.dumps(r)+'\n')
            for filename,records in [('metrics.csv',metrics),('paired_comparisons.csv',comparisons)]:
                with (run/filename).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]),lineterminator='\n');w.writeheader();w.writerows(records)
            write(run/f'{task}_{layer}_complete.json',dict(wall_seconds=time.monotonic()-started))
    write(run/'fit_complete.json',dict(wall_seconds=time.monotonic()-started,cpu_seconds=time.process_time()-cpu_started,prediction_rows=len(predictions)))
if __name__=='__main__':main()
