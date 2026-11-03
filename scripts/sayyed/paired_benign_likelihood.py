"""Paired sequence-level causal NLL accounting on the saved H3 bootstrap draws."""
import argparse,csv,json
from pathlib import Path
import numpy as np
from scripts.sayyed.fit_maxent_benign import arrays

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--post',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--probes',required=True);a=ap.parse_args();run=Path(a.probes);rows=list(map(json.loads,Path(a.manifest).read_text().splitlines()));base,_=arrays(a.base,rows);post,_=arrays(a.post,rows)
    if not np.array_equal(base['n_tokens'],post['n_tokens']):raise ValueError('Model target counts differ')
    for arr in [base,post]:
        if not np.array_equal(arr['n_tokens'],[len(r['sequence'])-1 for r in rows]):raise ValueError('Causal target mask/count mismatch')
    out=[]
    for split in ['dev','test']:
        ix=np.flatnonzero(base['split']==split)
        with np.load(run/f'final_norm_{split}_bootstrap.npz',allow_pickle=False) as b:draws=b['indices'];ids=b['ids']
        if not np.array_equal(ids,base['ids'][ix]):raise ValueError('Bootstrap row identity mismatch')
        losses=[arr['nll_sum'][ix].astype(np.float64) for arr in [base,post]];counts=base['n_tokens'][ix];point=[float(x.sum()/counts.sum()) for x in losses];samples=[]
        for draw in draws:samples.append([float(x[draw].sum()/counts[draw].sum()) for x in losses])
        samples=np.array(samples)
        for metric,values,delta in [('causal_nll',samples[:,1]-samples[:,0],point[1]-point[0]),('perplexity',np.exp(samples[:,1])-np.exp(samples[:,0]),float(np.exp(point[1])-np.exp(point[0])))]:
            lo,hi=np.quantile(values,[.025,.975]);out.append(dict(task='EMP/H3',split=split,layer='backbone',probe='none',metric=metric,difference=delta,ci_low=float(lo),ci_high=float(hi),status='paired whole-sequence losses/counts; same prespecified2000 draws; conditional exploratory',rejected=0))
    with (run/'likelihood_paired.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(out[0]),lineterminator='\n');w.writeheader();w.writerows(out)
    print('Causal masks/counts verified; paired likelihood intervals saved',flush=True)
if __name__=='__main__':main()
