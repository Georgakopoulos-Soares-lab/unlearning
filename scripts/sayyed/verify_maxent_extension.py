"""Independent saved-prediction binary/macro-OVR and grouped-pair accounting."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from scripts.sayyed.verify_h3_followup import rank_metrics

def auc(y,p,classes,weights=None):
    if len(classes)==2:return rank_metrics(y,p[:,1],weights)['auroc']
    return float(np.mean([rank_metrics((y==c).astype(int),p[:,j],weights)['auroc'] for j,c in enumerate(classes)]))
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--manifest',required=True);a=ap.parse_args();run=Path(a.run)
    manifest=list(map(json.loads,Path(a.manifest).read_text().splitlines()));by_id={r['id']:r for r in manifest};rows=list(map(json.loads,(run/'predictions.jsonl').read_text().splitlines()));metric={(r['task'],r['layer'],r['model'],r['metric']):float(r['value']) for r in csv.DictReader((run/'metrics.csv').open())};ci={(r['task'],r['layer'],r['probe']):r for r in csv.DictReader((run/'paired_comparisons.csv').open())};checked=[];max_delta=0.
    if len({(r['id'],r['layer']) for r in rows})!=len(rows):raise ValueError('Duplicate prediction identity')
    for r in rows:
        ref=by_id[r['id']]
        if any(r[k]!=ref[k] for k in ['task','split','label']) or r['group']!=ref['exact_rc_group']:raise ValueError('Prediction association mismatch')
    for task in sorted({r['task'] for r in manifest}):
        dev=[r for r in manifest if r['task']==task and r['split']=='dev'];classes=np.array(sorted({r['label'] for r in manifest if r['task']==task and r['split']=='train'}))
        for layer in ['final_norm','decoder_layer_16']:
            rr=[r for r in rows if r['task']==task and r['layer']==layer]
            if [r['id'] for r in rr]!=[r['id'] for r in dev] or len(rr)!=512:raise ValueError('Dev row coverage/order mismatch')
            if any(r['classes']!=classes.tolist() for r in rr):raise ValueError('Class ordering mismatch')
            y=np.array([r['label'] for r in rr]);probs={name:np.array([r['probabilities'][name] for r in rr]) for name in ['base_refit','maxent_refit','maxent_fixed_base']}
            for name,p in probs.items():
                if p.shape!=(512,len(classes)) or not np.isfinite(p).all() or not np.allclose(p.sum(1),1):raise ValueError('Probability shape/range')
                pred=(p[:,1]>=.5).astype(int) if len(classes)==2 else classes[p.argmax(1)]
                m=dict(auroc=auc(y,p,classes),accuracy=float(np.mean(pred==y)),balanced_accuracy=float(np.mean([np.mean(pred[y==c]==c) for c in classes])))
                if len(classes)==2:m['average_precision']=rank_metrics(y,p[:,1])['average_precision']
                for key,val in m.items():
                    if abs(val-metric[task,layer,name,key])>1e-12:raise ValueError('Independent metric mismatch')
                checked.append(dict(task=task,layer=layer,model=name,metrics=m))
            with np.load(run/f'{task}_{layer}_bootstrap.npz',allow_pickle=False) as b:
                draws=b['group_draws'];inverse=b['row_groups'];names=b['group_names'];saved={n:b[n] for n in ['maxent_refit','maxent_fixed_base']};ids=b['ids']
            unique,expected_inverse=np.unique([r['group'] for r in rr],return_inverse=True)
            if not np.array_equal(unique,names) or not np.array_equal(expected_inverse,inverse) or ids.tolist()!=[r['id'] for r in rr]:raise ValueError('Bootstrap group identity')
            if not np.array_equal(draws,np.random.default_rng(20261103).integers(len(unique),size=(2000,len(unique)),dtype=np.int32)):raise ValueError('Bootstrap seed')
            recomputed={n:[] for n in saved};rejected=0
            for draw in draws:
                weights=np.bincount(draw,minlength=len(unique))[inverse]
                if any(weights[y==c].sum()==0 for c in classes):rejected+=1;continue
                base=auc(y,probs['base_refit'],classes,weights)
                for n in saved:recomputed[n].append(auc(y,probs[n],classes,weights)-base)
            for n,vals in recomputed.items():
                delta=float(np.max(np.abs(np.array(vals)-saved[n])));max_delta=max(max_delta,delta)
                if delta>1e-12:raise ValueError('Independent grouped paired sample mismatch')
                lo,hi=np.quantile(vals,[.025,.975]);ref=ci[task,layer,n]
                if abs(lo-float(ref['ci_low']))>1e-12 or abs(hi-float(ref['ci_high']))>1e-12 or rejected!=int(ref['rejected']):raise ValueError('Interval/rejection accounting')
    (run/'independent_verification.json').write_text(json.dumps(dict(prediction_rows=len(rows),conditions=len(checked),checks=checked,bootstrap_max_abs_delta=max_delta,scope='Independent tied-rank/class-count predictions and exact/RC-group bootstrap; no GPU replication'),indent=2));print('EXTENSION_VERIFIED',len(checked),len(rows),max_delta,flush=True)
if __name__=='__main__':main()
