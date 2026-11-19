"""Consumer-only paired-vector recovery, with active producer-path denial."""
from pathlib import Path
import argparse,json,hashlib,sys,os,math
import numpy as np
from portable_math8 import resolve,probabilities,pair,weights_from_draws,historical_lm
from independent_math import metrics
from analysis_pairs import lm_numbers

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(root,dep,kind,label):
 mapping=dep['immutable_saved_outputs'];maxima={k:0. for k in ['point','draw','CI']};counts={k:0 for k in maxima};worst={};vectors=0;checks=[];raw_routes=set();earlier=read(root/'EARLIER_NEW_OUTPUT_DEPENDENCIES.json')['files']
 def compare(kind,a,b,unit,valid=None):
  a=np.asarray(a,dtype=np.float64);b=np.asarray(b,dtype=np.float64);assert a.shape==b.shape and np.array_equal(np.isnan(a),np.isnan(b));valid=np.isfinite(a) if valid is None else valid;assert np.isfinite(a[valid]).all() and np.isfinite(b[valid]).all();delta=float(np.max(np.abs(a[valid]-b[valid]))) if valid.any() else 0.;assert delta<=1e-12,(kind,unit,delta);counts[kind]+=int(valid.sum())
  if delta>=maxima[kind]:maxima[kind]=delta;worst[kind]=unit
 if kind=='classifier':
  family=label.removeprefix('adjacent_');paths=[p for p in (root/'artifacts/contrasts/classifier'/family).glob('*/*/*/seed*/COMPLETE.json') if p.parent.parent.name in ['decoder_layer_16','final_norm']];assert len(paths)==42
  for path in paths:
   record=read(path.parent/'RESULTS.json');target=record['endpoints']['target'];reference=record['endpoints']['reference'];uid=record['unit_id']
   with np.load(path.parent/'paired_draws.npz',allow_pickle=False) as saved:
    for policy in ['independent_refit','fixed_original_base']:
     pt,meta,cl=probabilities(target,policy,mapping);pr,mr,cr=probabilities(reference,policy,mapping);pair(meta,mr,cl,cr);assert target['draw']==reference['draw'];w,_=weights_from_draws(resolve(target['draw'],mapping),meta);a,valid=metrics(meta['labels'],pt,cl,w);b,vb=metrics(meta['labels'],pr,cl,w);assert np.array_equal(valid,vb) and np.array_equal(valid,saved['valid']);pa,pv=metrics(meta['labels'],pt,cl,np.ones((1,len(pt))));pb,pvb=metrics(meta['labels'],pr,cl,np.ones((1,len(pt))));assert pv.all() and pvb.all()
     rows=[r for r in record['rows'] if r['policy']==policy];assert len(rows)==5
     for r in rows:
      metric=r['metric'];delta=a[metric]-b[metric];name=family+'/'+uid+'/'+policy+'/'+metric;compare('draw',delta,saved[policy+'__'+metric],name,valid);compare('point',[pa[metric][0]-pb[metric][0]],[r['estimate']],name);compare('CI',np.quantile(delta[valid],[.025,.975],method='linear'),[r['ci_low'],r['ci_high']],name);vectors+=1;checks.append({'logical_id':r['logical_id'],'status':'PASS','attempted':2000,'valid':int(valid.sum())})
  assert vectors==420
 elif kind=='LM':
  cache={};paths=list((root/'artifacts/contrasts/LM').glob('*/*/*/COMPLETE.json'));assert len(paths)==35
  def statistics(item):
   alias=item['candidate'];task=item['task'];split=item['split'];key=(alias,task,split)
   if key in cache:return cache[key]
   original=item['statistics']['path'];rel='artifacts/normalized-lm/'+alias+'/'+task+'/'+split+'/sufficient_statistics.npz';p=root/rel
   if not p.exists():
    desc=earlier[original];p=Path(desc['consumer_root'])/desc['member'];assert '/consumer' in str(p) and p.stat().st_size==desc['bytes'] and sha(p)==desc['sha256']
   assert p.stat().st_size==item['statistics']['bytes'] and sha(p)==item['statistics']['sha256']
   with np.load(p,allow_pickle=False) as z:meta={k:z[k] for k in z.files}
   if item['endpoint']['prediction_descriptor']['hash_kind']=='LM_SEALED_FEATURE_BUNDLE_WITH_SUM_COUNT_SELECTOR':
    raw,source=historical_lm(item['endpoint']['prediction_descriptor'],item['endpoint']['raw_cohort'],task,split,mapping)
    for k in raw:assert np.array_equal(raw[k],meta[k]),'Typed historical LM normalization differs: '+k
    raw_routes.add(alias+'/'+task+'/'+split)
   cache[key]=meta;return meta
  for path in paths:
   record=read(path.parent/'RESULTS.json');target=record['endpoints']['target'];reference=record['endpoints']['reference'];a=statistics(target);b=statistics(reference)
   for k in ['ids','labels','groups','sequence_sha256','lengths','n_tokens']:assert np.array_equal(a[k],b[k])
   assert target['endpoint']['draw']==reference['endpoint']['draw'];w,draw=weights_from_draws(resolve(target['endpoint']['draw'],mapping),a);pa,da,_=lm_numbers(a,draw,w);pb,db,_=lm_numbers(b,draw,w);points={'causal_nll':pa-pb,'perplexity':math.exp(pa)-math.exp(pb)};deltas={'causal_nll':da-db,'perplexity':np.exp(da)-np.exp(db)}
   with np.load(path.parent/'paired_draws.npz',allow_pickle=False) as saved:
    assert np.array_equal(saved['valid'],np.ones(2000,dtype=bool))
    for r in record['rows']:
     metric=r['metric'];name=r['family']+'/'+r['task']+'/'+r['split']+'/'+metric;compare('point',[points[metric]],[r['estimate']],name);compare('draw',deltas[metric],saved[metric],name);compare('CI',np.quantile(deltas[metric],[.025,.975],method='linear'),[r['ci_low'],r['ci_high']],name);vectors+=1;checks.append({'logical_id':r['logical_id'],'status':'PASS','attempted':2000,'valid':2000})
  assert vectors==70 and len([r for r in raw_routes if r.startswith('R3/')])==7
 else:raise ValueError(kind)
 return {'status':'PASS','kind':kind,'label':label,'paired_vectors':vectors,'paired_attempted_values':vectors*2000,'comparison_counts':counts,'max_abs_residuals':maxima,'worst_units':worst,'checks':checks,'historical_typed_LM_routes_verified':sorted(raw_routes),'recovery_fits':0,'new_LM_forwards':0,'producer_paths_used':False,'inherited_dependencies_new_download':False,'GPU_runtime_recreation':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--dependency-map',type=Path,required=True);p.add_argument('--kind',choices=['classifier','LM'],required=True);p.add_argument('--label',required=True);a=p.parse_args();events=[]
 def deny(event,args):
  if event in ['open','os.listdir','os.scandir'] and args and isinstance(args[0],(str,bytes,os.PathLike)):
   path=os.path.abspath(os.fsdecode(args[0]))
   if any(path==b or path.startswith(b+'/') for b in ['/workspace/meeting-artifacts','/workspace/agent-handoff','/workspace/wt-pod-a']):events.append(event);raise PermissionError('Producer-tree reads denied')
 sys.addaudithook(deny)
 try:open('/workspace/meeting-artifacts/A08-producer-denial-sentinel','rb')
 except PermissionError:pass
 else:raise AssertionError('Sentinel not rejected')
 out=main(a.root,read(a.dependency_map),a.kind,a.label);assert len(events)==1;out['producer_path_denial_active']=True;out['sentinel_rejection_proven']=True;print(json.dumps(out,allow_nan=False))
