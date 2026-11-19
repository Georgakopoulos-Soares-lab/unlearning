"""Restore six saved audit heads per task; consumer-only, zero fitting."""
from pathlib import Path
import argparse,json,hashlib,os,sys
import numpy as np
import joblib
from independent_math import reconstruct,metrics

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def index(root,expected):
 assert sha(root/'MEMBER_MANIFEST.json')==expected;return {e['path']:e for e in read(root/'MEMBER_MANIFEST.json')['files']}
def checked(root,rel,ix):
 p=root/rel;e=ix[rel];assert p.resolve().is_relative_to(root.resolve()) and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];return p

def main(root,dep,task):
 fr=Path(dep['A06_features']['consumer_root']);tr=Path(dep['A07_tasks'][task]['consumer_root']);fi=index(fr,dep['A06_features']['member_manifest_sha256']);ti=index(tr,dep['A07_tasks'][task]['member_manifest_sha256']);assert '/consumer' in str(fr) and '/consumer' in str(tr)
 bp=checked(fr,f'artifacts/features/R5/{task}/dev/COMPLETE.json',fi);bundle=read(bp);x={k:[] for k in ['decoder_layer_16','final_norm']};meta={k:[] for k in ['ids','labels','groups','sequence_sha256']}
 for c in bundle['chunks']:
  rel='artifacts/'+c['path'];p=checked(fr,rel+'/COMPLETE.json',fi);assert sha(p)==c['receipt_sha256'];j=read(p)
  for e in j['files']:checked(fr,rel+'/'+e['path'],fi)
  with np.load(fr/rel/'features_and_lm.npz',allow_pickle=False) as z:
   for k in x:assert z[k].dtype==np.float32;x[k].append(z[k])
   for k in meta:meta[k].append(z[k])
 x={k:np.concatenate(v) for k,v in x.items()};meta={k:np.concatenate(v) for k,v in meta.items()};classes=np.array([0,1,2] if task=='gue_splice_reconstructed' else [0,1]);adeps=read(tr/'DEPENDENCIES.json');checks=[];maxp=maxm=maxcv=0.;worst={};calls=0
 for key in x:
  for seed in [42,17,1234]:
   uid=f'R5/{task}/{key}/seed{seed}';rr=root/'artifacts/refits'/uid;ar=root/'artifacts/audits'/uid;pr=tr/'artifacts/probes'/uid;rf=read(rr/'AUDIT_REFIT.json');assert rf['status']=='PASS';calls+=rf['actual_optimizer_fits'];cv=read(rr/'CV.json');pcv=read(pr/'CV.json');assert len(cv)==3
   for a,b in zip(cv,pcv):
    assert a['C']==b['C'] and len(a['fold_aurocs'])==len(b['fold_aurocs'])==5;e=float(np.max(np.abs(np.array(a['fold_aurocs'])-b['fold_aurocs'])));assert e<=1e-12;maxcv=max(maxcv,e)
   assert max(cv,key=lambda a:(a['mean_auroc'],-a['C']))['C']==rf['selected_C']==read(pr/'FINAL_FIT.json')['selected_C']
   base=adeps['base_heads'][key+'/seed'+str(seed)];checked(tr,base['path'],ti);models={'independent_refit':joblib.load(rr/'audit_head.joblib'),'fixed_original_base':joblib.load(tr/base['path'])};audit=read(ar/'NUMERICAL_AUDIT.json')
   with np.load(ar/'independent_predictions.npz',allow_pickle=False) as a,np.load(pr/'dev_predictions.npz',allow_pickle=False) as prod,np.load(rr/'audit_dev_probabilities.npz',allow_pickle=False) as saved:
    for k in meta:assert np.array_equal(a[k],meta[k]) and np.array_equal(prod[k],meta[k])
    for policy,model in models.items():
     assert np.array_equal(model[-1].classes_,classes);p=reconstruct(model,x[key]);errs=[float(np.max(np.abs(p-a[policy]))),float(np.max(np.abs(p-prod[policy])))];e=max(errs);assert e<=1e-10
     if policy=='independent_refit':assert float(np.max(np.abs(p-saved['probabilities'])))<=1e-10
     values,valid=metrics(meta['labels'],p,classes,np.ones((1,512)));assert valid.all();me=max(abs(float(values[m][0])-audit['independent_point_values'][policy][m]) for m in values);assert me<=1e-12
     if e>=maxp:maxp=e;worst['probability']=uid+'/'+policy
     if me>=maxm:maxm=me;worst['metric']=uid+'/'+policy
     checks.append({'unit_id':uid,'policy':policy,'probability_max_abs':e,'metric_max_abs':me,'status':'PASS'})
 assert len(checks)==12
 return {'status':'PASS','task':task,'checks':checks,'restored_audit_refit_heads':6,'policy_paths':12,'point_metric_comparisons':60,'recorded_refit_solver_calls':calls,'probability_max_abs':maxp,'metric_max_abs':maxm,'CV_score_max_abs':maxcv,'worst_units':worst,'recovery_fits':0,'producer_paths_used':False,'inherited_dependencies_new_download':False,'GPU_runtime_recreation':False}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);parser.add_argument('--dependency-map',type=Path,required=True);parser.add_argument('--task',required=True);v=parser.parse_args();events=[]
 def deny(event,args):
  if event in ['open','os.listdir','os.scandir'] and args and isinstance(args[0],(str,bytes,os.PathLike)):
   p=os.path.abspath(os.fsdecode(args[0]))
   if any(p==b or p.startswith(b+'/') for b in ['/workspace/meeting-artifacts','/workspace/agent-handoff','/workspace/wt-pod-a']):events.append(event);raise PermissionError('Producer-tree access denied')
 sys.addaudithook(deny)
 try:open('/workspace/meeting-artifacts/A08-producer-denial-sentinel','rb')
 except PermissionError:pass
 else:raise AssertionError('Sentinel was not rejected')
 result=main(v.root,read(v.dependency_map),v.task);assert len(events)==1;result['producer_path_denial_active']=True;result['sentinel_rejection_proven']=True;print(json.dumps(result,allow_nan=False))
