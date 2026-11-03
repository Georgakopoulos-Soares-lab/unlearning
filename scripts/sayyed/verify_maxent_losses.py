"""Independent classifier-CE and causal loss/count accounting for new benign outputs."""
import argparse,csv,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
import joblib

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--metrics',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();root=Path(a.root);records=list(csv.DictReader(Path(a.metrics).open()));lookup={(r['model'],r['task'],r['split'],r['layer'],r['metric']):float(r['value']) for r in records};checks=[];dtypes={}
    for study in ['H3-probes','promoter-splice-probes','remaining-probes']:
        grouped=defaultdict(list)
        for r in map(json.loads,(root/study/'predictions.jsonl').read_text().splitlines()):
            for condition,p in r['probabilities'].items():
                model='base' if condition in ['base_refit','maxent_fixed_base'] else 'maxent'
                filename=(f'{r["task"]}_{model}_{r["layer"]}.joblib' if 'task' in r else f'{model}_{r["layer"]}.joblib')
                path=root/study/'models'/filename
                if path not in dtypes:dtypes[path]=joblib.load(path)[-1].coef_.dtype
                dtype=dtypes[path];eps=float(np.finfo(dtype).eps)
                if isinstance(p,list):q=float(np.array(p,dtype=dtype)[r['classes'].index(r['label'])])
                else:q=float(np.array(p,dtype=dtype)) if r['label']==1 else float(np.array(1,dtype=dtype)-np.array(p,dtype=dtype))
                q=min(1-eps,max(eps,q));grouped[(condition,r.get('task','EMP/H3'),r['split'],r['layer'])].append(-math.log(q))
        for key,losses in grouped.items():
            actual=math.fsum(losses)/len(losses);expected=lookup[(*key,'classification_cross_entropy')];delta=abs(actual-expected)
            if delta>1e-12:raise ValueError(f'Classifier CE mismatch {key}: {delta}')
            checks.append(dict(kind='classification_CE',key=list(key),value=actual,absolute_delta=delta,tolerance=1e-12,precision='Clipping/complement use actual saved fitted-model coefficient dtype; float64 log/summation'))
    specifications=[('base','base-H3','inputs/H3_manifest.jsonl',True),('maxent','maxent-H3','inputs/H3_manifest.jsonl',True),('base','base-promoter-splice','promoter-splice-data/evaluation_manifest.jsonl',False),('maxent','maxent-promoter-splice','promoter-splice-data/evaluation_manifest.jsonl',False),('base','base-remaining','remaining-data/evaluation_manifest.jsonl',False),('maxent','maxent-remaining','remaining-data/evaluation_manifest.jsonl',False)]
    for model,cache,manifest,h3 in specifications:
        rows={r['id']:r for r in map(json.loads,(root/manifest).read_text().splitlines())};groups=defaultdict(list)
        for path in sorted((root/cache).glob('chunk_*.npz')):
            with np.load(path,allow_pickle=False) as z:
                for i,rid in enumerate(z['ids']):
                    r=rows[str(rid)];count=int(z['n_tokens'][i]);loss=float(z['nll_sum'][i])
                    if count!=len(r['sequence'])-1 or not math.isfinite(loss):raise ValueError('Causal masking/count identity')
                    if r['split']!='train':groups[('EMP/H3' if h3 else r['task'],r['split'])].append((loss,count))
        for (task,split),values in groups.items():
            nll=math.fsum(x[0] for x in values)/sum(x[1] for x in values)
            for metric,value in [('causal_nll',nll),('perplexity',math.exp(nll))]:
                expected=lookup[model,task,split,'backbone',metric];delta=abs(value-expected)
                if delta>1e-12:raise ValueError('LM aggregate mismatch')
                checks.append(dict(kind='LM_from_saved_sequence_statistics',key=[model,task,split,metric],value=value,absolute_delta=delta,tolerance=1e-12))
    Path(a.output).write_text(json.dumps(dict(classifier_ce_conditions=sum(x['kind']=='classification_CE' for x in checks),lm_metric_records=sum(x['kind']!='classification_CE' for x in checks),checks=checks,scope='CE from saved probabilities; LM from saved per-sequence loss sums/counts; not independent GPU replication'),indent=2));print('LOSS_ACCOUNTING_VERIFIED',len(checks),max(x['absolute_delta'] for x in checks),flush=True)
if __name__=='__main__':main()
