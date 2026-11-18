"""Portable A08 CPU recovery checks using only fresh/restored consumer roots."""
from pathlib import Path
import json,hashlib,argparse,math
import numpy as np
import joblib
from independent_math import reconstruct,metrics
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load_features(root,alias,task,key):
 bundle=read(root/'artifacts/features'/alias/task/'dev/COMPLETE.json');chunks=[];meta={k:[] for k in ['ids','labels','groups','sequence_sha256']}
 for entry in bundle['chunks']:
  p=root/'artifacts'/entry['path'];assert sha(p/'COMPLETE.json')==entry['receipt_sha256'];r=read(p/'COMPLETE.json')
  for e in r['files']:assert sha(p/e['path'])==e['sha256']
  with np.load(p/'features_and_lm.npz',allow_pickle=False) as z:
   chunks.append(z[key])
   for k in meta:meta[k].append(z[k])
 return np.concatenate(chunks),{k:np.concatenate(v) for k,v in meta.items()}
def candidate_check(root,alias):
 deps=read(root/'DEPENDENCIES.json');feature_root=Path(deps['A06_consumer_roots'][alias]);a07root=Path(deps['A07_consumer_roots'][alias+'/gue_tf_0']);checks=[];refit_checks=[]
 for task in ['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']:
  producer_root=Path(deps['A07_consumer_roots'][alias+'/'+task]);classes=np.array([0,1,2] if task=='gue_splice_reconstructed' else [0,1])
  for key in ['decoder_layer_16','final_norm']:
   x,meta=load_features(feature_root,alias,task,key);assert x.dtype==np.float32;unit=root/'artifacts/audits'/alias/task/key/'seed42';producer=producer_root/'artifacts/probes'/alias/task/key/'seed42';head=joblib.load(producer/'head.joblib');base=joblib.load(producer_root/'dependencies/base-heads'/key/'base.joblib');record=read(unit/'NUMERICAL_AUDIT.json');assert record['status']=='PASS'
   with np.load(unit/'independent_predictions.npz',allow_pickle=False) as z:
    for k in meta:assert np.array_equal(z[k],meta[k])
    for policy,model in [('independent_refit',head),('fixed_original_base',base)]:
     p=reconstruct(model,x);dp=float(np.max(np.abs(p-z[policy])));assert dp<=1e-10;point,valid=metrics(meta['labels'],p,classes,np.ones((1,len(p))));assert valid.all();dm=max(abs(float(point[m][0])-record['independent_point_values'][policy][m]) for m in point);assert dm<=1e-12;checks.append({'candidate':alias,'task':task,'representation':key,'seed':42,'policy':policy,'probability_max_abs':dp,'metric_max_abs':dm,'rows':len(p),'groups':len(np.unique(meta['groups'])),'status':'PASS'})
   if task=='gue_tf_0' and key=='final_norm':
    rr=root/'artifacts/refits'/alias/task/key/'seed42';model=joblib.load(rr/'audit_head.joblib');p=reconstruct(model,x)
    with np.load(rr/'audit_dev_probabilities.npz',allow_pickle=False) as z:diff=float(np.max(np.abs(p-z['probabilities'])));assert diff<=1e-10
    refit_checks.append({'candidate':alias,'task':task,'representation':key,'seed':42,'restored_audit_refit':True,'probability_max_abs':diff})
 return {'status':'PASS','candidate':alias,'policy_paths':checks,'restored_refit_checks':refit_checks,'all_paths_consumer_relative':True,'original_producer_paths_used':False,'GPU_work':0}
def analysis_check(root):
 deps=read(root/'DEPENDENCIES.json');audit_roots={alias:Path(deps['A08_candidate_consumers'][alias]) for alias in ['R4','R6']};unit=root/'artifacts/analysis/R6_minus_R4/gue_tf_0/dev/decoder_layer_16/seed42';record=read(unit/'ANALYSIS.json');res=0.
 for row in record['rows']:
  policy=row['policy'];metric=row['metric'];a6=read(audit_roots['R6']/'artifacts/audits/R6/gue_tf_0/decoder_layer_16/seed42/NUMERICAL_AUDIT.json');a4=read(audit_roots['R4']/'artifacts/audits/R4/gue_tf_0/decoder_layer_16/seed42/NUMERICAL_AUDIT.json');res=max(res,abs(a6['independent_point_values'][policy][metric]-a4['independent_point_values'][policy][metric]-row['estimate']))
 assert res<=1e-12
 for row in record['rows']:
  policy=row['policy'];metric=row['metric']
  with np.load(audit_roots['R6']/'artifacts/audits/R6/gue_tf_0/decoder_layer_16/seed42/bootstrap_independent.npz',allow_pickle=False) as x6,np.load(audit_roots['R4']/'artifacts/audits/R4/gue_tf_0/decoder_layer_16/seed42/bootstrap_independent.npz',allow_pickle=False) as x4,np.load(unit/'paired_draws.npz',allow_pickle=False) as delta:assert np.max(np.abs(x6[policy+'__'+metric]-x4[policy+'__'+metric]-delta[policy+'__'+metric]))<=1e-12
 lmroot=root/'artifacts/analysis/LM_R6_minus_R4/gue_tf_0/dev';lm=read(lmroot/'ANALYSIS.json');values={}
 for alias in ['R4','R6']:
  p=Path(deps['A06_consumer_roots'][alias])/'artifacts/lm'/alias/'gue_tf_0/dev/sufficient_statistics.npz'
  with np.load(p,allow_pickle=False) as z:values[alias]=math.fsum(float(v) for v in z['nll_sum'])/sum(int(v) for v in z['n_tokens'])
 lmres=max(abs((values['R6']-values['R4'] if row['metric']=='causal_nll' else math.exp(values['R6'])-math.exp(values['R4']))-row['estimate']) for row in lm['rows']);assert lmres<=1e-12
 return {'status':'PASS','restored_new_classifier_contrast':'gue_tf_0/layer16/seed42/bothpolicies/all5metrics/all2000draws','classifier_max_abs':res,'restored_new_LM_contrast':'gue_tf_0/dev/NLL_and_PPL','LM_point_max_abs':lmres,'original_producer_paths_used':False,'GPU_work':0}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--candidate',choices=['R4','R6']);p.add_argument('--analysis',action='store_true');v=p.parse_args();print(json.dumps(analysis_check(v.root) if v.analysis else candidate_check(v.root,v.candidate)))
