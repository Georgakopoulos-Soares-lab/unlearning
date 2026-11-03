"""Independent rank/count verification of saved paired benign predictions."""
import argparse,csv,json,hashlib
from pathlib import Path
import numpy as np
from scripts.sayyed.verify_h3_followup import rank_metrics

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--manifest',required=True);args=ap.parse_args();run=Path(args.run)
    manifest={r['id']:r for r in map(json.loads,Path(args.manifest).read_text().splitlines())};rows=list(map(json.loads,(run/'predictions.jsonl').read_text().splitlines()))
    if len(rows)!=5988 or len({(r['id'],r['layer']) for r in rows})!=len(rows):raise ValueError('Prediction coverage/duplicate issue')
    recorded={(r['model'],r['split'],r['layer'],r['metric']):float(r['value']) for r in csv.DictReader((run/'metrics.csv').open())}
    checked=[];bootstrap_max_delta=0.;contrasts={(r['split'],r['layer'],r['probe']):r for r in csv.DictReader((run/'paired_comparisons.csv').open())}
    for r in rows:
        ref=manifest[r['id']]
        if r['label']!=ref['label'] or r['split']!=ref['split'] or r['group']!=ref['exact_rc_group']:raise ValueError('Identity mismatch')
    for layer in ['final_norm','decoder_layer_16']:
        for split in ['dev','test']:
            rr=[r for r in rows if r['layer']==layer and r['split']==split];y=np.array([r['label'] for r in rr])
            if len(rr)!=1497:raise ValueError('Split coverage issue')
            for name in ['base_refit','maxent_refit','maxent_fixed_base']:
                p=np.array([r['probabilities'][name] for r in rr]);m=rank_metrics(y,p)
                if not np.isfinite(p).all() or np.any((p<0)|(p>1)):raise ValueError('Invalid probabilities')
                for key in ['auroc','average_precision','accuracy','balanced_accuracy']:
                    if not np.isclose(m[key],recorded[name,split,layer,key],rtol=0,atol=1e-12):raise ValueError('Metric mismatch '+key)
                checked.append(dict(model=name,split=split,layer=layer,metrics=m))
            with np.load(run/f'{layer}_{split}_bootstrap.npz',allow_pickle=False) as b:
                draws=b['indices'];ids=b['ids'];saved={k:b[k] for k in ['maxent_refit','maxent_fixed_base']}
            if ids.tolist()!=[r['id'] for r in rr] or not np.array_equal(draws,np.random.default_rng(20261103).integers(len(rr),size=(2000,len(rr)),dtype=np.int32)):raise ValueError('Bootstrap identity/seed mismatch')
            probs={n:np.array([r['probabilities'][n] for r in rr]) for n in ['base_refit','maxent_refit','maxent_fixed_base']}
            recomputed={n:[] for n in saved}
            for draw in draws:
                weights=np.bincount(draw,minlength=len(rr))
                if len(np.unique(y[draw]))<2:continue
                bauc=rank_metrics(y,probs['base_refit'],weights)['auroc']
                for name in saved:recomputed[name].append(rank_metrics(y,probs[name],weights)['auroc']-bauc)
            for name in saved:
                delta=float(np.max(np.abs(np.array(recomputed[name])-saved[name])));bootstrap_max_delta=max(bootstrap_max_delta,delta)
                if delta>1e-12:raise ValueError('Paired bootstrap mismatch')
                lo,hi=np.quantile(recomputed[name],[.025,.975]);ref=contrasts[split,layer,name]
                if abs(lo-float(ref['ci_low']))>1e-12 or abs(hi-float(ref['ci_high']))>1e-12:raise ValueError('Interval mismatch')
    (run/'independent_verification.json').write_text(json.dumps(dict(prediction_rows=len(rows),bootstrap_max_abs_delta=bootstrap_max_delta,checks=checked,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Predictions and identities; independent tied-rank/contingency metrics; not GPU replication'),indent=2));print('Independent prediction verification passed',len(checked),'conditions',flush=True)
if __name__=='__main__':main()
