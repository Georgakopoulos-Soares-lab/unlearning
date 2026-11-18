"""Independent saved-parameter/pairwise metric route and metadata-selected fresh refits."""
import argparse,concurrent.futures,datetime,time,warnings,fcntl
import joblib
from scipy.special import expit
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from h3_common import *
from production_contract import UnitLock
from independent_math import reconstruct,metrics as independent_metrics
def independent_distribution(p,y,weights,key):
 out=A/'independent-reference-cache'/key;out.parent.mkdir(parents=True,exist_ok=True)
 with out.with_suffix('.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  if out.exists():
   with np.load(out,allow_pickle=False) as z:return {k:z[k] for k in METRICS},z['valid']
  result,valid=independent_metrics(y,p,np.array([0,1]),weights);temp=out.with_name(out.name+'.tmp')
  with temp.open('wb') as f:np.savez_compressed(f,valid=valid,**result)
  os.replace(temp,out);return result,valid
def fresh_fit(x,y,c):
 attempts=[]
 for limit in [2000,10000]:
  scaler=StandardScaler();z=scaler.fit_transform(x);head=LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',tol=1e-4,max_iter=limit,random_state=42)
  with warnings.catch_warnings(record=True) as caught:warnings.simplefilter('always');head.fit(z,y)
  attempts.append({'max_iter':limit,'n_iter':head.n_iter_.tolist(),'warnings':[str(w.message) for w in caught]})
  if not any(issubclass(w.category,ConvergenceWarning) for w in caught):return scaler,head,attempts
 raise RuntimeError('Independent refit convergence failure')
def predict_parts(scaler,head,x):
 z=scaler.transform(x);score=z@head.coef_.T+head.intercept_;positive=expit(score[:,0]);return np.column_stack([1-positive,positive])
def residual(a,b,tol,why):
 require(np.shape(a)==np.shape(b),'Shape mismatch: '+why);aa=np.asarray(a);bb=np.asarray(b);require(not np.isinf(aa).any() and not np.isinf(bb).any(),'Infinite residual input: '+why);require(np.array_equal(np.isnan(aa),np.isnan(bb)),'Undefined values mismatch: '+why);ok=np.isfinite(aa)&np.isfinite(bb);d=float(np.max(np.abs(aa[ok]-bb[ok]))) if ok.any() else 0.;require(d<=tol,why+' residual '+str(d));return d
def audit_one(spec):
 alias,key,seed=spec;unit=A/'h3'/alias/key/('seed'+str(seed));producer=read(unit/'PRODUCER_COMPLETE.json');verify_refs(unit,producer);require(producer['CPU_source_identity_sha256']==sha(C/'CPU_SOURCE_IDENTITY.json'),'Changed CPU source identity')
 if (unit/'COMPLETE.json').exists():
  final=read(unit/'COMPLETE.json');require(final['producer_sha256']==sha(unit/'PRODUCER_COMPLETE.json'),'Changed H3 producer');return {'candidate':alias,'key':key,'seed':seed,'status':'REUSED_VERIFIED'}
 t=time.monotonic();model=joblib.load(unit/'head.joblib');base_path=checked_old(producer['original_base_head']['path']);require(sha(base_path)==producer['original_base_head']['sha256'],'Fixed-base head changed');base=joblib.load(base_path);require(np.array_equal(model[-1].classes_,[0,1]) and np.array_equal(base[-1].classes_,[0,1]),'Class inversion');saved=read(unit/'RESULTS.json');maxprob=0.;maxmetric=0.;maxbootstrap=0.;maxinterval=0.;audited=0
 with cache(alias,'train') as z:trainmeta={k:z[k] for k in z.files}
 xtrain=cache(alias,'train',key);folds,foldpath=saved_folds(trainmeta['ids'],seed);require(sha(foldpath)==producer['fold_sha256'],'Fold provenance changed')
 # Saved StandardScaler must equal TRAIN-only moments, independent of saved producer summary.
 scaler_check=StandardScaler().fit(xtrain);require(np.array_equal(model[0].mean_,scaler_check.mean_) and np.array_equal(model[0].scale_,scaler_check.scale_),'Final scaler not fitted on exact TRAIN rows')
 for a,b in folds:require(not set(trainmeta['groups'][a])&set(trainmeta['groups'][b]),'Fold group leakage')
 trace=read(unit/'CV.json');finalfit=read(unit/'FINAL_FIT.json');require([t['C'] for t in trace]==[.1,1.,10.] and all(len(t['scores'])==3 and t['mean_auroc']==float(np.mean(t['scores'])) for t in trace),'CV trace schema/mean differs');require(max(trace,key=lambda t:(t['mean_auroc'],-t['C']))['C']==finalfit['C']==model[-1].C,'Recorded C/tie/model disagreement')
 selected_panel=key in ['decoder_layer_16','final_norm'];fresh=None;fresh_report=None
 if selected_panel:
  candidates=[]
  for c in [.1,1.,10.]:
   scores=[];attempts=[]
   for a,b in folds:
    ss,hh,at=fresh_fit(xtrain[a],trainmeta['labels'][a],c);p=predict_parts(ss,hh,xtrain[b]);scores.append(float(roc_auc_score(trainmeta['labels'][b],p[:,1])));attempts.append(at)
   candidates.append({'C':c,'scores':scores,'mean_auroc':float(np.mean(scores)),'attempts':attempts})
  chosen=max(candidates,key=lambda r:(r['mean_auroc'],-r['C']))['C'];selection={'selected_C':read(unit/'FINAL_FIT.json')['C'],'candidates':read(unit/'CV.json')};require(chosen==selection['selected_C'],'Independent C selection differs')
  for a,b in zip(candidates,selection['candidates']):residual(a['scores'],b['scores'],1e-12,'Independent CV AUROC')
  ss,hh,at=fresh_fit(xtrain,trainmeta['labels'],chosen);fresh=(ss,hh);fresh_report={'status':'PASS','candidate':alias,'key':key,'seed':seed,'selected_C':chosen,'candidates':candidates,'final_attempts':at,'new_production_heads':0,'supplemental_refits':1,'probability_max_abs':0.}
 for split in ['dev','test']:
  with cache(alias,split) as z:meta={k:z[k] for k in z.files}
  x=cache(alias,split,key);weights,drawpath=draws(split,meta['ids'],meta['groups']);old,oldpath=historical_predictions(key,seed,split,meta);target={'independent_refit':reconstruct(model,x),'fixed_original_base':reconstruct(base,x)}
  with np.load(unit/(split+'_predictions.npz'),allow_pickle=False) as z:
   for field in ['ids','labels','groups','sequence_sha256']:require(np.array_equal(z[field],meta[field]),'Saved prediction order/label mismatch')
   require(np.array_equal(z['classes'],[0,1]),'Saved class inversion')
   for policy,p in target.items():maxprob=max(maxprob,residual(p,z[policy],1e-10,'Saved head probabilities'))
   if fresh is not None:fresh_report['probability_max_abs']=max(fresh_report['probability_max_abs'],residual(predict_parts(*fresh,x),z['independent_refit'],1e-10,'Independent fresh-refit probabilities'))
  with np.load(unit/(split+'_bootstrap.npz'),allow_pickle=False) as archive:
   for policy,p in target.items():
    point,pointvalid=independent_metrics(meta['labels'],p,np.array([0,1]),np.ones((1,len(p))));boot,valid=independent_metrics(meta['labels'],p,np.array([0,1]),weights);require(np.array_equal(valid,archive['valid']),'Independent bootstrap validity mask differs');audited+=int(valid.sum())
    for metric in METRICS:
     maxbootstrap=max(maxbootstrap,residual(boot[metric],archive[policy+'__'+metric],1e-12,'Independent every bootstrap draw'))
     row=next(r for r in saved['metrics'] if r['split']==('test_exploratory' if split=='test' else split) and r['policy']==policy and r['metric']==metric);maxmetric=max(maxmetric,residual([point[metric][0]],[row['estimate']],1e-12,'Independent point metric'));ci=np.quantile(boot[metric][valid],[.025,.975]);maxinterval=max(maxinterval,residual(ci,[row['ci_low'],row['ci_high']],1e-12,'Independent metric interval'))
    refs={'base':old['prob_base_refit'],'R1':old['prob_h3_only_refit' if policy=='independent_refit' else 'prob_h3_only_fixed_base']}
    if key in ['decoder_layer_16','final_norm']:
     for control in ['composition','kmer4']:refs['control_'+control]=control_predictions(control,seed,split,meta)[0]
    for refname,refprob in refs.items():
     ck=digest({'p':hashlib.sha256(refprob.tobytes()).hexdigest(),'draws':sha(drawpath),'reference':refname})+'.npz';refboot,refvalid=independent_distribution(refprob,meta['labels'],weights,ck);refpoint,_=independent_metrics(meta['labels'],refprob,np.array([0,1]),np.ones((1,len(refprob))));common=valid&refvalid
     for metric in METRICS:
      delta=boot[metric][common]-refboot[metric][common];ci=np.quantile(delta,[.025,.975]);row=next(r for r in saved['paired_contrasts'] if r['split']==split and r['policy']==policy and r['reference']==refname and r['metric']==metric);maxinterval=max(maxinterval,residual(ci,[row['ci_low'],row['ci_high']],1e-12,'Independent paired contrast interval'));maxmetric=max(maxmetric,residual([point[metric][0]-refpoint[metric][0]],[row['difference']],1e-12,'Independent paired point delta'));require(row['valid']==int(common.sum()) and row['invalid']==int((~common).sum()),'Paired missing-class accounting mismatch')
 if fresh is not None:
  fresh_root=A/'audit-refits'/alias/key/('seed'+str(seed));fresh_root.mkdir(parents=True,exist_ok=True);require(not (fresh_root/'COMPLETE.json').exists(),'Existing independent refit preserved');joblib.dump(fresh,fresh_root/'independent_scaler_head.joblib');put(fresh_root/'FULL_CV_REFIT.json',fresh_report);put(fresh_root/'COMPLETE.json',{'status':'PASS','unit_id':alias+'/emp_H3/'+key+'/seed'+str(seed),'audit_kind':'INDEPENDENT_FULL_CV_AND_FINAL_REFIT','original_producer_sha256':sha(unit/'PRODUCER_COMPLETE.json'),'fold_sha256':sha(foldpath),'files':file_refs(fresh_root),'initial_solver_calls':10,'actual_solver_calls':sum(len(v) for c in fresh_report['candidates'] for v in c['attempts'])+len(fresh_report['final_attempts']),'production_replaced':False});fresh_report['independent_artifact_sha256']=sha(fresh_root/'COMPLETE.json')
 audit={'status':'PASS','candidate':alias,'key':key,'seed':seed,'producer_sha256':sha(unit/'PRODUCER_COMPLETE.json'),'all_probability_paths':4,'probability_max_abs':maxprob,'metric_max_abs':maxmetric,'bootstrap_draw_max_abs':maxbootstrap,'interval_max_abs':maxinterval,'bootstrap_policy_draws_checked':audited,'train_only_scaler_moments_exact':True,'fold_group_leakage':0,'fresh_refit':fresh_report,'wall_seconds':time.monotonic()-t,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(unit/'AUDIT.json',audit);put(unit/'COMPLETE.json',{'schema':'pod-a-a06-h3-verified-unit-v1','status':'VERIFIED','candidate':alias,'task':'emp_H3','key':key,'seed':seed,'production_heads':1,'fixed_base_applications':1,'producer_sha256':sha(unit/'PRODUCER_COMPLETE.json'),'audit_sha256':sha(unit/'AUDIT.json'),'completed_utc':audit['completed_utc']});return {k:audit[k] for k in ['status','candidate','key','seed','probability_max_abs','metric_max_abs','interval_max_abs','wall_seconds']}
def main(alias):
 from scope6 import authorize
 authorize(alias)
 from scope6 import h3_specs
 specs=h3_specs(alias)
 with UnitLock(A/'h3'/alias/'auditor.lock'):
  with threadpool_limits(limits=4):
   with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
    for result in pool.map(audit_one,specs):print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',choices=['R5'],required=True);main(p.parse_args().candidate)
