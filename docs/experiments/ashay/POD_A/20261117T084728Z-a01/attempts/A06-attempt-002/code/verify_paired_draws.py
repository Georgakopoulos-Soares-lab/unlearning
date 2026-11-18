"""Supplement: independently verify every stored paired-bootstrap draw, not only intervals."""
import argparse,datetime
import joblib
from threadpoolctl import threadpool_limits
from h3_common import *
from independent_math import reconstruct,metrics
from audit_h3 import independent_distribution,residual
def main(alias):
 from scope6 import authorize
 authorize(alias)
 maximum=0.;arrays=0;draw_values=0;units=0
 for key in LAYERS:
  for seed in SEEDS:
   unit=A/'h3'/alias/key/('seed'+str(seed));final=read(unit/'COMPLETE.json');require(final['status']=='VERIFIED','Core H3 audit not passed');producer=read(unit/'PRODUCER_COMPLETE.json');verify_refs(unit,producer);model=joblib.load(unit/'head.joblib');base=joblib.load(checked_old(producer['original_base_head']['path']))
   for split in ['dev','test']:
    with cache(alias,split) as z:meta={k:z[k] for k in z.files}
    x=cache(alias,split,key);weights,dp=draws(split,meta['ids'],meta['groups']);old,_=historical_predictions(key,seed,split,meta)
    with np.load(unit/(split+'_bootstrap.npz'),allow_pickle=False) as saved:
     for policy,head in [('independent_refit',model),('fixed_original_base',base)]:
      p=reconstruct(head,x);target,valid=metrics(meta['labels'],p,np.array([0,1]),weights);refs={'base':old['prob_base_refit'],'R1':old['prob_h3_only_refit' if policy=='independent_refit' else 'prob_h3_only_fixed_base']}
      if key in ['decoder_layer_16','final_norm']:
       for name in ['composition','kmer4']:refs['control_'+name]=control_predictions(name,seed,split,meta)[0]
      for name,pr in refs.items():
       ck=digest({'p':hashlib.sha256(pr.tobytes()).hexdigest(),'draws':sha(dp),'reference':name})+'.npz';rd,rv=independent_distribution(pr,meta['labels'],weights,ck);require(np.array_equal(valid,rv),'Paired class validity mismatch')
       for metric in METRICS:
        delta=target[metric]-rd[metric];maximum=max(maximum,residual(delta,saved[policy+'__minus_'+name+'__'+metric],1e-12,'Every saved paired draw'));arrays+=1;draw_values+=len(delta)
   units+=1
 report={'status':'PASS','candidate':alias,'verified_H3_units':units,'paired_draw_arrays_verified':arrays,'paired_draw_values_verified':draw_values,'max_abs_residual':maximum,'tolerance':1e-12,'source_sha256':sha(__file__),'core_audits_reused':'Core probability, metric, target-bootstrap and interval audits unchanged; this adds every saved paired-difference array','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(C/('H3_AUDIT_SUPPLEMENT_'+alias+'.json'),report);print(json.dumps(report))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',required=True,choices=['R5']);a=p.parse_args()
 with threadpool_limits(limits=4):main(a.candidate)
