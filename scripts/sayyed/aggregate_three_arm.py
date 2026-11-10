"""Audit new-vs-H3 paired contrasts, and serialize three-arm/control results."""
import argparse,csv,json,hashlib,time
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from scripts.sayyed.multiretain_independent import metrics as independent
from scripts.sayyed.multiretain_metrics import bootstrap_metrics,point_metrics
from scripts.sayyed.multiretain_support import atomic_json

def write(path,rows):
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def subtract_shared_base_contrasts(new_delta, old_delta, valid):
 new_delta=np.asarray(new_delta);old_delta=np.asarray(old_delta);valid=np.asarray(valid)
 if new_delta.shape!=old_delta.shape or new_delta.shape!=valid.shape or valid.dtype!=np.bool_ or not valid.any():
  raise ValueError('Paired distribution shape/mask mismatch')
 delta=new_delta-old_delta
 if not np.isfinite(delta[valid]).all():raise ValueError('Nonfinite paired draws')
 return delta,np.quantile(delta[valid],[.025,.975])

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--reference-run',required=True);p.add_argument('--controls',required=True);a=p.parse_args();root,old,ctrl=map(Path,[a.run,a.reference_run,a.controls]);out=root/'reports';out.mkdir(exist_ok=True);start=time.monotonic();cpu=time.process_time();m=[];d=[];reference=[];links=[];control_comparisons=[];new_h3=[];lm_m=[];lm_d=[];cache={};maxdelta=0.;units=0
 def weights(group,task,split):
  key=(group,task,split)
  if key not in cache:
   with np.load(root/'probes'/group/task/(split+'_resampling.npz'),allow_pickle=False) as s,np.load(old/'probes'/group/task/(split+'_resampling.npz'),allow_pickle=False) as o:
    for k in ['ids','group_names','row_groups','group_draws']:assert np.array_equal(s[k],o[k]),('resampling',key,k)
    cache[key]=np.stack([np.bincount(x,minlength=len(s['group_names'])) for x in s['group_draws']])[:,s['row_groups']]
  return cache[key]
 for group in ['H3','other_five']:
  loss_arrays={}
  for arm,folder in [('new',root/'features'/group/'new'),('old',old/'features'/group/'maxent')]:
   pieces=[]
   for chunk in sorted(folder.glob('chunk_*.npz')):
    with np.load(chunk,allow_pickle=False) as c:pieces.append({k:c[k] for k in ['ids','nll_sum','n_tokens']})
   loss_arrays[arm]={k:np.concatenate([v[k] for v in pieces]) for k in ['ids','nll_sum','n_tokens']}
  assert np.array_equal(loss_arrays['new']['ids'],loss_arrays['old']['ids']);loss_lookup={str(v):i for i,v in enumerate(loss_arrays['new']['ids'])}
  audit=json.loads((root/'producer_audit'/group/'VERIFICATION_COMPLETE.json').read_text());assert audit['status']=='PASS';idx=json.loads((root/'probes'/group/'PROBE_INDEX.json').read_text());assert len(idx['units'])==(78 if group=='H3' else 390)
  for entry in idx['units']:
   task,layer,seed=entry['task'],entry['layer'],entry['cv_seed'];unit=root/'probes'/group/task/layer/f'seed{seed}';assert sha(unit/'COMPLETE.json')==entry['receipt_sha256'];prior=old/'probes'/group/task/layer/f'seed{seed}';result=json.loads((unit/'results.json').read_text());prev=json.loads((prior/'results.json').read_text());m.extend(result['metrics']);m.extend(x for x in prev['metrics'] if x['policy']!='base_refit');d.extend(dict(x,contrast='new_minus_base') for x in result['contrasts']);reference.extend(prev['contrasts']);units+=1
   oldbase={(x['split'],x['metric']):x['value'] for x in prev['metrics'] if x['policy']=='base_refit'}
   for x in result['metrics']:
    if x['policy']=='base_refit':assert abs(x['value']-oldbase[x['split'],x['metric']])<1e-12
   for split in (['dev','test'] if group=='H3' else ['dev']):
    w=weights(group,task,split)
    with np.load(unit/(split+'_predictions.npz'),allow_pickle=False) as n,np.load(prior/(split+'_predictions.npz'),allow_pickle=False) as o,np.load(unit/(split+'_bootstrap.npz'),allow_pickle=False) as nb,np.load(prior/(split+'_bootstrap.npz'),allow_pickle=False) as ob:
     for k in ['ids','labels','classes','groups','sequence_sha256']:assert np.array_equal(n[k],o[k]),('join',task,layer,seed,split,k)
     assert np.array_equal(n['prob_base_refit'],o['prob_base_refit']);y,classes=n['labels'],n['classes'];valid=nb['valid'];assert np.array_equal(valid,ob['valid'])
     for policy,oldpolicy in [('new_refit','h3_only_refit'),('new_fixed_base','h3_only_fixed_base')]:
      ni,nv=independent(y,n['prob_'+policy],classes,w);oi,ov=independent(y,o['prob_'+oldpolicy],classes,w);assert np.array_equal(nv,valid) and np.array_equal(ov,valid)
      npnt,_=independent(y,n['prob_'+policy],classes,np.ones((1,len(y))));opnt,_=independent(y,o['prob_'+oldpolicy],classes,np.ones((1,len(y))));samples={}
      for metric in ni:
       distribution,ci=subtract_shared_base_contrasts(nb[policy+'__'+metric],ob[oldpolicy+'__'+metric],valid);separate=ni[metric]-oi[metric];delta=float(np.max(np.abs(distribution[valid]-separate[valid])));maxdelta=max(maxdelta,delta);assert delta<1e-12;ci=np.quantile(distribution[valid],[.025,.975]);ici=np.quantile(separate[valid],[.025,.975]);assert np.max(np.abs(ci-ici))<1e-12
       x=dict(task=task,layer=layer,cv_seed=seed,split=split,policy=policy,metric=metric,contrast='new_minus_h3_only',difference=float(npnt[metric][0]-opnt[metric][0]),ci_low=float(ci[0]),ci_high=float(ci[1]),valid=int(valid.sum()),invalid=int((~valid).sum()),scope='pointwise unadjusted conditional on fitted heads; exact/RC groups only');d.append(x);new_h3.append(x);samples[metric]=distribution
      paired_out=root/'paired_bootstrap'/group/task/layer/f'seed{seed}';paired_out.mkdir(parents=True,exist_ok=True)
      np.savez_compressed(paired_out/(split+'_'+policy+'_vs_h3.npz'),valid=valid,**samples)
      if layer in ['decoder_layer_16','final_norm']:
       for control in ['composition','4mer']:
        cu=ctrl/'tasks'/task/control/f'seed{seed}'
        with np.load(cu/(split+'_predictions.npz'),allow_pickle=False) as cp,np.load(cu/(split+'_bootstrap.npz'),allow_pickle=False) as cb:
         for k in ['ids','labels','classes','groups']:assert np.array_equal(n[k],cp[k])
         assert np.array_equal(valid,cb['valid']);ci_metrics,_=independent(y,cp['probabilities'],classes,w);cpoint,_=independent(y,cp['probabilities'],classes,np.ones((1,len(y))));newpoint,_=point_metrics(y,n['prob_'+policy],classes);newdraw,ndvalid=bootstrap_metrics(y,n['prob_'+policy],classes,w);assert np.array_equal(valid,ndvalid)
         for metric in ni:
          assert np.max(np.abs(ci_metrics[metric][valid]-cb[metric][valid]))<1e-12;dist=newdraw[metric]-cb[metric];separate=ni[metric]-ci_metrics[metric];assert np.max(np.abs(dist[valid]-separate[valid]))<1e-12;ci=np.quantile(dist[valid],[.025,.975]);control_comparisons.append(dict(task=task,split=split,layer=layer,cv_seed=seed,policy=policy,control=control,metric=metric,difference=float(newpoint[metric]-cpoint[metric][0]),ci_low=float(ci[0]),ci_high=float(ci[1]),valid=int(valid.sum()),invalid=int((~valid).sum())))
    links.append(dict(task=task,layer=layer,cv_seed=seed,split=split,new_receipt=str(unit/'COMPLETE.json'),new_receipt_sha256=sha(unit/'COMPLETE.json'),old_receipt=str(prior/'COMPLETE.json'),old_receipt_sha256=sha(prior/'COMPLETE.json'),new_predictions=str(unit/(split+'_predictions.npz')),old_predictions=str(prior/(split+'_predictions.npz')),protocol_sha256=sha(root/'PROTOCOL_V2.json')))
   print('PAIRED',units,task,layer,seed,flush=True)
  for task in sorted({x['task'] for x in idx['units']}):
   newtask=root/'probes'/group/task;oldtask=old/'probes'/group/task;nr=json.loads((newtask/'lm_metrics.json').read_text());orr=json.loads((oldtask/'lm_metrics.json').read_text());lm_m.extend(nr['metrics']);lm_m.extend(x for x in orr['metrics'] if x['arm']=='h3_only_maxent');lm_d.extend(nr['contrasts']);lm_d.extend(orr['contrasts'])
   for split in (['dev','test'] if group=='H3' else ['dev']):
    with np.load(newtask/(split+'_lm_bootstrap.npz'),allow_pickle=False) as ns,np.load(oldtask/(split+'_lm_bootstrap.npz'),allow_pickle=False) as os:
     for metric in ['causal_nll','perplexity']:
      newpoint=next(x[metric] for x in nr['metrics'] if x['split']==split and x['arm']=='new_checkpoint');oldpoint=next(x[metric] for x in orr['metrics'] if x['split']==split and x['arm']=='h3_only_maxent');dist=ns[metric]-os[metric]
      with np.load(newtask/(split+'_resampling.npz'),allow_pickle=False) as rr:loss_ix=[loss_lookup[str(v)] for v in rr['ids']]
      ww=weights(group,task,split);direct={};directpoint={}
      for arm in ['new','old']:
       sums=loss_arrays[arm]['nll_sum'][loss_ix].astype(float);counts=loss_arrays[arm]['n_tokens'][loss_ix].astype(float);nll=np.einsum('ij,j->i',ww,sums)/np.einsum('ij,j->i',ww,counts);point=float(sums.sum()/counts.sum());direct[arm]=nll if metric=='causal_nll' else np.exp(nll);directpoint[arm]=point if metric=='causal_nll' else float(np.exp(point))
      assert abs(directpoint['new']-newpoint)<1e-12 and abs(directpoint['old']-oldpoint)<1e-12
      assert np.max(np.abs(dist-(direct['new']-direct['old'])))<1e-12
      ci=np.quantile(dist,[.025,.975]);lm_d.append(dict(task=task,split=split,metric=metric,contrast='new_checkpoint_minus_h3_only',difference=newpoint-oldpoint,ci_low=float(ci[0]),ci_high=float(ci[1]),valid=len(dist),invalid=0,interpretation='paired conditional sequence/exact-RC-group bootstrap; no homology guarantee'))
 write(out/'native_metrics.csv',m);write(out/'native_contrasts.csv',d);write(out/'h3_only_minus_base_reference.csv',reference);write(out/'control_contrasts.csv',control_comparisons);write(out/'ROW_EVIDENCE.csv',links);write(out/'LM_METRICS.csv',lm_m);write(out/'LM_CONTRASTS.csv',lm_d)
 # Consumer renderer schema; unchanged base appears in both policies as an alias.
 render_m=[];render_d=[]
 for x in m:
  policy=x['policy'];arm='base' if policy=='base_refit' else ('h3_only_maxent' if policy.startswith('h3_only') else 'three_source_config2151');layer='decoder.final_norm' if x['layer']=='final_norm' else 'decoder.layers.'+x['layer'].rsplit('_',1)[-1];row=dict(task=x['task'],split=x['split'],checkpoint=arm,checkpoint_role=arm,layer=layer,seed=x['cv_seed'],probe_policy='fixed_base_scaler_and_head' if policy.endswith('fixed_base') else 'independent_refit',metric=x['metric'],value=x['value'],status='completed',missing_reason='');render_m.append(row)
  if policy=='base_refit':render_m.append(dict(row,probe_policy='fixed_base_scaler_and_head'))
 for x in d:
  layer='decoder.final_norm' if x['layer']=='final_norm' else 'decoder.layers.'+x['layer'].rsplit('_',1)[-1];render_d.append(dict(task=x['task'],split=x['split'],checkpoint=x['contrast'],checkpoint_role='three_source_config2151',layer=layer,seed=x['cv_seed'],probe_policy='fixed_base_scaler_and_head' if x['policy'].endswith('fixed_base') else 'independent_refit',metric=x['metric'],difference=x['difference'],ci_low=x['ci_low'],ci_high=x['ci_high'],status='completed',missing_reason=''))
 write(out/'metrics.csv',render_m);write(out/'differences.csv',render_d)
 atomic_json(out/'PAIRED_VERIFICATION.json',dict(status='PASS',units=units,new_vs_h3_contrasts=len(new_h3),new_vs_base_and_h3_contrasts=len(d),control_contrasts=len(control_comparisons),max_independent_draw_delta=maxdelta,wall_seconds=time.monotonic()-start,cpu_process_seconds=time.process_time()-cpu,scope='Separate pairwise/threshold verification of every new-vs-H3 and anchor-control metric/resample; original base/new LM full audits plus matched saved LM contrast subtraction; no GPU replication'))
if __name__=='__main__':
 with threadpool_limits(limits=4):main()
