"""Only approved H3 production heads: finite26x3 units per candidate, no other-five fitting."""
import argparse,concurrent.futures,datetime,time,warnings,resource,fcntl
import joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from h3_common import *
from production_contract import UnitLock
from producer_metrics import point_metrics,bootstrap_metrics
def train(x,y,c):
 attempts=[]
 for limit in [2000,10000]:
  model=make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',tol=1e-4,max_iter=limit,random_state=42));t=time.perf_counter()
  with warnings.catch_warnings(record=True) as caught:warnings.simplefilter('always');model.fit(x,y)
  attempts.append({'max_iter':limit,'n_iter':model[-1].n_iter_.tolist(),'seconds':time.perf_counter()-t,'warnings':[str(w.message) for w in caught]})
  if not any(issubclass(w.category,ConvergenceWarning) for w in caught):return model,attempts
 raise RuntimeError('Unresolved TRAIN convergence')
def distribution(p,y,classes,weights,cache_key):
 out=A/'reference-bootstrap-cache'/cache_key;out.parent.mkdir(parents=True,exist_ok=True)
 with out.with_suffix('.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if out.exists():
   with np.load(out,allow_pickle=False) as z:return {k:z[k] for k in METRICS},z['valid']
  result,valid=bootstrap_metrics(y,p,classes,weights);tmp=out.with_name(out.name+'.tmp')
  with tmp.open('wb') as f:np.savez_compressed(f,valid=valid,**result)
  os.replace(tmp,out);return result,valid
def fit_one(spec):
 alias,key,seed=spec;root=A/'h3'/alias/key/('seed'+str(seed));root.mkdir(parents=True,exist_ok=True)
 if (root/'PRODUCER_COMPLETE.json').exists():verify_refs(root,read(root/'PRODUCER_COMPLETE.json'));return {'candidate':alias,'layer':key,'seed':seed,'status':'REUSED_SEALED_PRODUCER'}
 require(not (root/'head.joblib').exists(),'Unsealed head preserved; explicit retry/quarantine required');start=time.monotonic();cpu=time.process_time();classes=np.array([0,1]);sc=read(C/'CPU_SOURCE_IDENTITY.json')
 for e in sc['files']:require(sha(A/'code'/e['path'])==e['sha256'],'CPU scientific source drift')
 with cache(alias,'train') as tr:ids=tr['ids'];y=tr['labels'];groups=tr['groups']
 x=cache(alias,'train',key);folds,fold_path=saved_folds(ids,seed);candidates=[];attempts_all=[]
 with threadpool_limits(limits=4):
  for regularization in [.1,1.,10.]:
   scores=[];convergence=[]
   for a,b in folds:
    require(not set(groups[a])&set(groups[b]),'Frozen fold leakage');model,attempts=train(x[a],y[a],regularization);require(not attempts[-1]['warnings'],'Unresolved classifier warning');scores.append(float(roc_auc_score(y[b],model.predict_proba(x[b])[:,1])));convergence.append(attempts)
   candidates.append({'C':regularization,'scores':scores,'mean_auroc':float(np.mean(scores)),'convergence':convergence});put(root/'CV.json',candidates)
  selected=max(candidates,key=lambda z:(z['mean_auroc'],-z['C']))['C'];model,attempts=train(x,y,selected);require(not attempts[-1]['warnings'] and np.array_equal(model[-1].classes_,classes),'Final class/convergence mismatch');joblib.dump(model,root/'head.joblib');put(root/'FINAL_FIT.json',{'C':selected,'attempts':attempts,'classes':[0,1],'fold_ref':{'path':str(fold_path),'sha256':sha(fold_path)},'train_ids_sha256':digest(ids.tolist()),'training_rows':len(y),'fit_wall_seconds':time.monotonic()-start})
  original=checked_old(H/'probes/H3/emp_H3'/key/('seed'+str(seed))/'base.joblib');base=joblib.load(original);require(np.array_equal(base[-1].classes_,classes),'Base head class mismatch')
  result_rows=[];contrast_rows=[]
  for split in ['dev','test']:
   with cache(alias,split) as meta:metadata={k:meta[k] for k in meta.files}
   xx=cache(alias,split,key);pfit=model.predict_proba(xx);pfixed=base.predict_proba(xx);reference,refpath=historical_predictions(key,seed,split,metadata)
   weights,drawpath=draws(split,metadata['ids'],metadata['groups']);target={'independent_refit':pfit,'fixed_original_base':pfixed};predfile=root/(split+'_predictions.npz');np.savez_compressed(predfile,ids=metadata['ids'],labels=metadata['labels'],groups=metadata['groups'],classes=classes,sequence_sha256=metadata['sequence_sha256'],**target);prediction_sha=sha(predfile);all_distributions={};valid_all=None
   for policy,p in target.items():
    point,_=point_metrics(metadata['labels'],p,classes);boot,valid=bootstrap_metrics(metadata['labels'],p,classes,weights);all_distributions.update({policy+'__'+k:v for k,v in boot.items()});valid_all=valid if valid_all is None else valid_all&valid
    for metric,value in point.items():
     vals=boot[metric][valid];lo,hi=np.quantile(vals,[.025,.975]) if len(vals) else [None,None];result_rows.append({'checkpoint_alias':alias,'checkpoint_content_id':INPUTS['checkpoint_identities'][alias]['model_tensor_content_sha256'],'lineage':'NEW','task':'emp_H3','split':'test_exploratory' if split=='test' else split,'representation':key,'CV_seed':seed,'policy':policy,'metric':metric,'estimate':value,'sample_count':len(metadata['ids']),'group_count':len(np.unique(metadata['groups'])),'target_count':None,'ci_low':None if lo is None else float(lo),'ci_high':None if hi is None else float(hi),'bootstrap_attempted':2000,'bootstrap_valid':int(valid.sum()),'bootstrap_invalid':int((~valid).sum()),'status':'COMPLETE_UNVERIFIED','missing_reason':None if len(vals) else 'No valid class-complete group draws','protocol_sha256':CFG['protocol_sha256'],'input_sha256':sha(A/'h3-cache'/alias/split/'COMPLETE.json'),'prediction_sha256':prediction_sha,'receipt':str((root/'COMPLETE.json').relative_to(A))})
    refs={'base':reference['prob_base_refit'],'R1':reference['prob_h3_only_refit' if policy=='independent_refit' else 'prob_h3_only_fixed_base']}
    if key in ['decoder_layer_16','final_norm']:
     for control in ['composition','kmer4']:
      cp,cp_path=control_predictions(control,seed,split,metadata);refs['control_'+control]=cp
    for refname,refprob in refs.items():
     rk=digest({'reference':refname,'p':hashlib.sha256(refprob.tobytes()).hexdigest(),'draws':sha(drawpath),'classes':[0,1]})+'.npz';refdist,refvalid=distribution(refprob,metadata['labels'],classes,weights,rk);refpoint,_=point_metrics(metadata['labels'],refprob,classes);common=valid&refvalid
     for metric in METRICS:
      delta=boot[metric]-refdist[metric];all_distributions[policy+'__minus_'+refname+'__'+metric]=delta;vals=delta[common];lo,hi=np.quantile(vals,[.025,.975]) if len(vals) else [None,None];contrast_rows.append({'candidate':alias,'reference':refname,'policy':policy,'split':split,'representation':key,'seed':seed,'metric':metric,'difference':point[metric]-refpoint[metric],'ci_low':None if lo is None else float(lo),'ci_high':None if hi is None else float(hi),'attempted':2000,'valid':int(common.sum()),'invalid':int((~common).sum()),'direction':'target-reference','orientation':'lower' if metric=='classification_cross_entropy' else 'higher','protocol_sha256':CFG['protocol_sha256'],'draw_sha256':sha(drawpath),'status':'COMPLETE_UNVERIFIED'})
   np.savez_compressed(root/(split+'_bootstrap.npz'),valid=valid_all,**all_distributions)
  put(root/'RESULTS.json',{'metrics':result_rows,'paired_contrasts':contrast_rows,'interpretation':'Pointwise exploratory paired exact/RC-group bootstrap, conditional on heads; no causal/multiplicity/equivalence or biological independence claim'})
 receipt={'schema':'pod-a-a06-h3-producer-v1','status':'PASS','candidate':alias,'task':'emp_H3','representation':key,'seed':seed,'head_count':1,'fixed_base_application_count':1,'original_base_head':{'path':str(original),'sha256':sha(original)},'fold_sha256':sha(fold_path),'CPU_source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'coverage_plan_sha256':CFG['coverage_plan_sha256'],'protocol_sha256':CFG['protocol_sha256'],'new_solver_fits':sum(len(at) for c in candidates for at in c['convergence'])+len(attempts),'files':file_refs(root),'wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cpu,'peak_RSS_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(root/'PRODUCER_COMPLETE.json',receipt);return {'candidate':alias,'layer':key,'seed':seed,'status':'PRODUCER_PASS','wall_seconds':receipt['wall_seconds']}
def main(alias):
 for split in ['train','dev','test']:require((A/'h3-cache'/alias/split/'COMPLETE.json').exists(),'H3 cache incomplete')
 specs=[(alias,key,seed) for key in LAYERS for seed in SEEDS]
 with UnitLock(A/'h3'/alias/'producer.lock'):
  with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
   for result in pool.map(fit_one,specs):print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',choices=['R4','R6'],required=True);main(p.parse_args().candidate)
