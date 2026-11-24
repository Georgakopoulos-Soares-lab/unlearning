"""S05 TRAIN-only production probes and separate full-CV audit orchestration. No contrast execution."""
from pathlib import Path
import os,sys,json,time,resource,argparse,warnings
from s05_contract import *

def parameter_digest(pipe):
 import numpy as np,hashlib
 h=hashlib.sha256()
 for name,x in [('mean',pipe[0].mean_),('scale',pipe[0].scale_),('var',pipe[0].var_),('coef',pipe[-1].coef_),('intercept',pipe[-1].intercept_),('classes',pipe[-1].classes_)]:
  a=np.asarray(x);need(np.isfinite(a).all(),'Nonfinite estimator parameter');h.update(json.dumps([name,str(a.dtype),list(a.shape)],separators=(',',':')).encode()+b'\0');h.update(a.tobytes(order='C'))
 return h.hexdigest()

def fit_call_producer(root,identity,x,y,C,validation=None):
 import joblib,numpy as np
 from sklearn.exceptions import ConvergenceWarning
 from sklearn.metrics import roc_auc_score
 from inherited_fit import pipeline
 root=Path(root)
 if (root/'COMPLETE.json').exists():
  verify_seal(root,identity,required=['model.joblib','TRACE.json']);trace=load(root/'TRACE.json');return joblib.load(root/'model.joblib'),trace,True
 need(not root.exists(),'Preserve incomplete producer fitcall; explicit newattempt repair required');root.mkdir(parents=True);attempts=[]
 for limit in [2000,10000]:
  model=pipeline(C,limit);start=time.perf_counter();cpu=time.process_time()
  with warnings.catch_warnings(record=True) as caught:warnings.simplefilter('always');model.fit(x,y)
  conv=[w for w in caught if issubclass(w.category,ConvergenceWarning)];attempts.append({'max_iter':limit,'n_iter':model[-1].n_iter_.tolist(),'seconds':time.perf_counter()-start,'CPU_seconds':time.process_time()-cpu,'warnings':[str(w.message) for w in caught]});put(root/'ATTEMPTS.partial.json',attempts)
  if not conv:
   need(not caught,'Persistent nonconvergence-independent warning blocks fit');break
 else:raise RuntimeError('Unresolved inherited TRAIN-only convergence after2000/10000')
 need(model[-1].classes_.tolist()==[0,1] and model[0].n_features_in_==x.shape[1],'Estimator class/width changed');trace={'attempts':attempts,'C':C,'parameter_content_sha256':parameter_digest(model),'fit_rows':len(y),'selected_from':'TRAINonly','validation_AUROC':None}
 if validation is not None:xx,yy=validation;trace['validation_AUROC']=float(roc_auc_score(yy,model.predict_proba(xx)[:,1]))
 tmp=root/'model.joblib.partial';joblib.dump(model,tmp);os.replace(tmp,root/'model.joblib');roundtrip=joblib.load(root/'model.joblib');need(parameter_digest(roundtrip)==trace['parameter_content_sha256'] and roundtrip[-1].C==C,'Estimator serialization roundtrip changed parameters');put(root/'TRACE.json',trace);write_seal(root,identity,['model.joblib','TRACE.json'],{'optimizer_calls':len(attempts),'retries':len(attempts)-1});return model,trace,False

def fit_call_auditor(root,identity,x,y,C,validation=None):
 """Separate orchestration and estimator construction; same frozen mathematical estimator semantics."""
 import joblib,numpy as np
 from sklearn.pipeline import make_pipeline
 from sklearn.preprocessing import StandardScaler
 from sklearn.linear_model import LogisticRegression
 from sklearn.exceptions import ConvergenceWarning
 from sklearn.metrics import roc_auc_score
 root=Path(root)
 if (root/'COMPLETE.json').exists():verify_seal(root,identity,required=['model.joblib','TRACE.json']);return joblib.load(root/'model.joblib'),load(root/'TRACE.json'),True
 need(not root.exists(),'Preserve incomplete auditfitcall');root.mkdir(parents=True);history=[];result=None
 for maximum in (2000,10000):
  estimator=make_pipeline(StandardScaler(),LogisticRegression(C=C,class_weight='balanced',solver='lbfgs',tol=1e-4,max_iter=maximum,random_state=42));tick=time.perf_counter();cp=time.process_time()
  with warnings.catch_warnings(record=True) as records:warnings.simplefilter('always');estimator.fit(x,y)
  history.append({'max_iter':maximum,'n_iter':estimator[-1].n_iter_.tolist(),'seconds':time.perf_counter()-tick,'CPU_seconds':time.process_time()-cp,'warnings':[str(r.message) for r in records]});put(root/'ATTEMPTS.partial.json',history)
  if any(issubclass(r.category,ConvergenceWarning) for r in records):continue
  need(not records,'Audit nonconvergence-independent warning');result=estimator;break
 need(result is not None,'Audit failed inherited convergence policy');need(result[-1].classes_.tolist()==[0,1],'Audit class ordering changed');score=None
 if validation is not None:score=float(roc_auc_score(validation[1],result.predict_proba(validation[0])[:,1]))
 trace={'attempts':history,'C':C,'parameter_content_sha256':parameter_digest(result),'fit_rows':len(y),'selected_from':'TRAINonly','validation_AUROC':score};tmp=root/'model.joblib.partial';joblib.dump(result,tmp);os.replace(tmp,root/'model.joblib');roundtrip=joblib.load(root/'model.joblib');need(parameter_digest(roundtrip)==trace['parameter_content_sha256'] and roundtrip[-1].C==C,'Estimator serialization roundtrip changed parameters');put(root/'TRACE.json',trace);write_seal(root,identity,['model.joblib','TRACE.json'],{'optimizer_calls':len(history),'retries':len(history)-1});return result,trace,False

def select_train_only(cfg,alias,rep,seed,source,case,lookup,audit=False):
 import numpy as np,joblib
 key=KEYS[HOOKS.index(rep)];train,y,ids,_,_,feature_seals=load_layer(case,cfg,'train',key);need(train.dtype==np.float32 and train.shape==(11971,1920) and np.unique(y).tolist()==[0,1],'Wrong H3 TRAIN input');folds=fold_indices(cfg,seed,ids);mode='audits' if audit else 'production';root=Path(case)/mode/key/('seed'+str(seed));k='audit_refit' if audit else 'final_head';pid=spec_id(lookup,k,c=alias,t='emp_H3',r=rep,s=seed,p='independent_refit');ident={'planned_spec_id':pid,'candidate_id':next(v['candidate_id'] for v in cfg['candidates'] if v['alias']==alias),'source_identity_sha256':source,'runtime_lock_sha256':cfg['runtime_lock_sha256'],'feature_bundle_seals_sha256':feature_seals,'fold_sha256':next(f['sha256'] for f in cfg['folds'] if f['cv_seed']==seed),'representation':rep,'cv_seed':seed,'TRAIN_rows':11971,'policy':'independent_refit','audit_separate_from_production':audit}
 if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json']);return root,load(root/'SUMMARY.json'),True
 root.mkdir(parents=True,exist_ok=True);entries=[];candidates=[];fitfn=fit_call_auditor if audit else fit_call_producer;executed=0;reused=0;optimizer_kind='audit_optimizer_call' if audit else 'optimizer_call'
 # Production and audit take separate saved call paths and fit implementations. No dev inputs are available to selection.
 for j,Cvalue in enumerate([0.1,1,10]):
  scores=[]
  for fold,(tr,va) in enumerate(folds):
   callid=spec_id(lookup,optimizer_kind,c=alias,t='emp_H3',r=rep,s=seed,p='independent_refit',j=j,fold=fold);callroot=root/'cv'/('C'+str(j)+'-fold'+str(fold));callident={**ident,'planned_spec_id':callid,'C':Cvalue,'fold':fold,'training_IDs_sha256':digest([ids[i] for i in tr]),'validation_IDs_sha256':digest([ids[i] for i in va])};_,trace,was_reused=fitfn(callroot,callident,train[tr],y[tr],Cvalue,(train[va],y[va]));scores.append(trace['validation_AUROC']);entries.append({'planned_spec_id':callid,'relative_root':str(callroot.relative_to(root)),'receipt_sha256':sha(callroot/'COMPLETE.json'),'optimizer_calls':len(trace['attempts']),'reused_this_invocation':was_reused});executed+=0 if was_reused else len(trace['attempts']);reused+=int(was_reused);print('S05_AUDIT_FITCALL' if audit else 'S05_TRAIN_FITCALL',alias,key,seed,j,fold,'REUSED' if was_reused else 'SEALED',flush=True)
  candidates.append({'C':Cvalue,'fold_AUROC':scores,'mean_fold_AUROC':float(np.mean(scores))});put(root/'CV_SELECTION.partial.json',candidates)
 selected=max(candidates,key=lambda r:(r['mean_fold_AUROC'],-r['C']))['C'];callid=spec_id(lookup,optimizer_kind,c=alias,t='emp_H3',r=rep,s=seed,p='independent_refit',j=None,fold=None);callroot=root/'final';pipe,trace,was_reused=fitfn(callroot,{**ident,'planned_spec_id':callid,'C':selected,'fold':None,'training_IDs_sha256':digest(ids)},train,y,selected);entries.append({'planned_spec_id':callid,'relative_root':'final','receipt_sha256':sha(callroot/'COMPLETE.json'),'optimizer_calls':len(trace['attempts']),'reused_this_invocation':was_reused});executed+=0 if was_reused else len(trace['attempts']);reused+=int(was_reused);(root/'head.joblib').write_bytes((callroot/'model.joblib').read_bytes())
 with (root/'PARAMETERS.npz').open('wb') as f:np.savez(f,scaler_mean=pipe[0].mean_,scaler_scale=pipe[0].scale_,scaler_var=pipe[0].var_,coef=pipe[-1].coef_,intercept=pipe[-1].intercept_,classes=pipe[-1].classes_)
 summary={'planned_spec_id':pid,'selected_C':selected,'CV':candidates,'parameter_content_sha256':parameter_digest(pipe),'head_serialization_sha256':sha(root/'head.joblib'),'initial_optimizer_calls':10,'actual_optimizer_calls_in_saved_unit':sum(e['optimizer_calls'] for e in entries),'actual_optimizer_calls_this_invocation':executed,'reused_optimizer_call_units_this_invocation':reused,'retries_in_saved_unit':sum(e['optimizer_calls']-1 for e in entries),'fit_rows':11971,'feature_dtype':'float32','scaler_transform_semantics':'Inherited sklearn1.7.2 StandardScaler preserves float32 transformedinput; LRcoef float64','dev_used_for_selection':False,'audit':audit,'peak_host_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024};need(summary['peak_host_RSS_bytes']<=8*1024**3,'CPUworker8GiBRSS ceiling exceeded');put(root/'SUMMARY.json',summary);put(root/'CV_INDEX.json',{'calls':entries});write_seal(root,ident,['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json'],{'initial_optimizer_calls':10,'actual_optimizer_calls':summary['actual_optimizer_calls_in_saved_unit'],'final_heads':1});return root,summary,False

NAME_MAP={'AUROC':'auroc','AP':'average_precision','accuracy':'accuracy','balanced_accuracy':'balanced_accuracy','cross_entropy':'classification_cross_entropy'}
def canonical_metric(actual_id,name,estimate,ci,reason,source,rows,groups,attempted,valid,draw_sha):return {'unit_id':actual_id,'reference_unit_id':None,'metric':name,'direction':'lower_better' if name in ['cross_entropy','LM_NLL','LM_PPL'] else 'higher_better','estimate':estimate,'ci_low':None if ci is None else float(ci[0]),'ci_high':None if ci is None else float(ci[1]),'missing_reason':reason,'sample_count':rows,'group_count':groups,'valid_targets':None,'bootstrap_attempted':attempted,'bootstrap_valid':valid,'bootstrap_invalid':attempted-valid,'draw_sha256':draw_sha,'common_mask_sha256':None,'uncertainty':'pointwise_exploratory_conditional' if attempted else 'none','source_sha256':source}

def probability_unit(cfg,alias,rep,seed,source,case,lookup,policy,headroot):
 import numpy as np,joblib
 from inherited_metrics import point_metrics,bootstrap_metrics
 key=KEYS[HOOKS.index(rep)];root=Path(case)/'probabilities'/key/('seed'+str(seed))/policy;pid=spec_id(lookup,'prediction',c=alias,t='emp_H3',r=rep,s=seed,p=policy,split='dev');ref=next(r for r in cfg['fixed_heads'] if r['representation']==rep and r['cv_seed']==seed);path=Path(headroot)/'head.joblib' if policy=='independent_refit' else Path(ref['path']);need(path.is_file(),'Missing exact fixed/referencehead')
 if policy=='fixed_original_base':need(sha(path)==ref['sha256'],'Original-base head replaced')
 x,y,ids,_,_,features=load_layer(case,cfg,'dev',key);pipe=joblib.load(path);need(pipe[-1].classes_.tolist()==[0,1] and pipe[0].n_features_in_==1920,'Class/width changed');weights,drawy,draw_sha=draw_weights(cfg);need(np.array_equal(y,drawy),'Draw/label order changed');ident={'planned_spec_id':pid,'candidate_alias':alias,'candidate_id':next(v['candidate_id'] for v in cfg['candidates'] if v['alias']==alias),'representation':rep,'cv_seed':seed,'policy':policy,'head_sha256':sha(path),'head_parameter_content_sha256':parameter_digest(pipe),'source_identity_sha256':source,'runtime_lock_sha256':cfg['runtime_lock_sha256'],'DEV_feature_seals_sha256':features,'cohort_sha256':cfg['cohorts']['dev']['ordered_metadata_sha256'],'dev_draw_sha256':draw_sha};actual_id=digest(ident)
 if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['predictions.npz','draws.npz','METRICS.json']);return load(root/'METRICS.json'),True
 need(not root.exists(),'Incomplete prior probabilityunit preserved');root.mkdir(parents=True);p=pipe.predict_proba(x);need(p.dtype==np.float64 and p.shape==(1497,2) and np.isfinite(p).all(),'Invalid fullprecision probability output');points,_=point_metrics(y,p,pipe[-1].classes_);distributions,valid=bootstrap_metrics(y,p,pipe[-1].classes_,weights);need(valid.shape==(2000,),'Wrong marginal validmask');valid_count=int(valid.sum());rows=[];vectors={}
 for name in METRICS:
  d=np.asarray(distributions[NAME_MAP[name]],dtype=np.float64);need(np.isfinite(d[valid]).all() and np.isnan(d[~valid]).all(),'Unexpected nonfinite required draw');ci=np.quantile(d[valid],[.025,.975]) if valid_count else None;record=canonical_metric(actual_id,name,float(points[NAME_MAP[name]]),ci,None if valid_count else 'No classcomplete valid bootstrapdraws; affected interval releaseblocked',source,1497,cfg['cohorts']['dev']['groups'],2000,valid_count,draw_sha);rows.append({'planned_spec_id':spec_id(lookup,'classifier_metric',c=alias,t='emp_H3',r=rep,s=seed,p=policy,split='dev',m=name),'source_row_id':digest({'actual_prediction_unit_id':actual_id,'metric':name}),'canonical_metric':record,'distribution_selector':name,'bootstrap_vector_sha256':hashlib.sha256(d.tobytes()).hexdigest(),'valid_mask_sha256':hashlib.sha256(valid.tobytes()).hexdigest()});vectors[name]=d
 meta=metadata(cfg,'dev')
 with (root/'predictions.npz').open('wb') as f:np.savez(f,ids=np.array(ids),labels=y,groups=np.array([r['group'] for r in meta]),classes=pipe[-1].classes_,probabilities=p)
 with (root/'draws.npz').open('wb') as f:np.savez(f,valid=valid,**vectors)
 result={'schema_version':'s05-marginal-metric-path-v1','status':'COMPLETE_UNVERIFIED','identity':ident,'actual_prediction_unit_id':actual_id,'metrics':rows,'inference_eligible':valid_count>0,'paired_or_S09_contrast_executed':False};put(root/'METRICS.json',result);write_seal(root,ident,['predictions.npz','draws.npz','METRICS.json'],{'dev_probability_paths':1,'classifier_metric_records':5,'independent_verification_pending':1});return result,False

def LM_units(cfg,alias,source,case,lookup):
 import numpy as np
 from qualification_contract import corpus_likelihood
 weights,drawy,draw_sha=draw_weights(cfg);result=[]
 for split in ['train','dev']:
  root=Path(case)/'LM'/split;pid=spec_id(lookup,'LM',c=alias,t='emp_H3',split=split,r=None,s=None,p='LM');_,y,ids,sums,targets,seals=load_layer(case,cfg,split,'final_norm');ident={'planned_spec_id':pid,'alias':alias,'split':split,'representation':None,'cv_seed':None,'policy':'LM','source_identity_sha256':source,'runtime_lock_sha256':cfg['runtime_lock_sha256'],'feature_seals_sha256':seals,'ordered_cohort_sha256':cfg['cohorts'][split]['ordered_metadata_sha256']};actual=digest(ident)
  if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['statistics.npz','draws.npz','METRICS.json']);result.append(load(root/'METRICS.json'));continue
  need(not root.exists(),'Preserve incomplete LMunit');root.mkdir(parents=True);nll,ppl,overflow=corpus_likelihood(sums,targets);vectors={};rows=[]
  if split=='dev':
   need(np.array_equal(y,drawy),'LMdrawpopulation mismatch');boot=(weights@sums.astype(np.float64))/(weights@targets.astype(np.float64));vectors['LM_NLL']=boot
   with np.errstate(over='ignore',invalid='ignore'):vectors['LM_PPL']=np.exp(boot)
  for name,value in [('LM_NLL',nll),('LM_PPL',ppl)]:
   d=vectors.get(name,np.array([],dtype=np.float64));valid=np.isfinite(d);ci=np.quantile(d[valid],[.025,.975]) if valid.any() else None;attempted=2000 if split=='dev' else 0;reason=overflow if value is None else ('No finite bootstrapdraws' if attempted and not valid.any() else None);metric=canonical_metric(actual,name,value,ci,reason,source,len(ids),cfg['cohorts'][split]['groups'],attempted,int(valid.sum()),draw_sha if attempted else None);metric['valid_targets']=int(targets.sum());rows.append({'planned_spec_id':spec_id(lookup,'LM_metric',c=alias,t='emp_H3',split=split,r=None,s=None,p='LM',m=name),'source_row_id':digest({'actual_LM_unit_id':actual,'metric':name}),'canonical_metric':metric,'valid_mask_sha256':hashlib.sha256(valid.tobytes()).hexdigest()});vectors[name+'_valid']=valid
  with (root/'statistics.npz').open('wb') as f:np.savez(f,ids=np.array(ids),nll_sum=sums,n_tokens=targets)
  with (root/'draws.npz').open('wb') as f:np.savez(f,**vectors)
  rec={'schema_version':'s05-LM-unit-v1','status':'COMPLETE_UNVERIFIED','identity':ident,'actual_LM_unit_id':actual,'metrics':rows,'TRAIN_diagnostic_no_draw_generation':split=='train','per_example_sum_dtype':'float32','corpus_aggregation_dtype':'float64'};put(root/'METRICS.json',rec);write_seal(root,ident,['statistics.npz','draws.npz','METRICS.json'],{'LM_units':1,'LM_metric_records':2,'rows':len(ids),'valid_targets':int(targets.sum())});result.append(rec)
 return result

def main(c,alias,mode,rep=None,seed=None):
 cfg,v,source=readiness(c,alias,role='auditor' if mode=='audit' else 'producer');scope(cfg,alias,representation=rep,seed=seed,policies=POLICIES);need(mode in ['production','audit','LM'],'Unknown S05CPUmode');need(str(Path(sys.executable).absolute())==cfg['cpu_runtime_python'],'Wrong CPUruntime');cfg['_source']=source;case=Path(cfg['artifacts_root'])/'candidates'/alias;lookup=planned(c);start=time.monotonic();cpu=time.process_time()
 import numpy as np
 from threadpoolctl import threadpool_limits
 with threadpool_limits(limits=4):
  if mode=='LM':LM_units(cfg,alias,source,case,lookup)
  else:
   need(rep in HOOKS and seed in SEEDS,'Missing exact headkey')
   if mode=='audit':audit_membership(load(Path(cfg['frozen_root'])/'H3_AUDIT_SUBSET.json')['units'],alias,rep,seed)
   key=KEYS[HOOKS.index(rep)];lock=case/('AUDIT_' if mode=='audit' else 'PRODUCER_')/(key+'-seed'+str(seed)+'.lock')
   with exclusive(lock):
    root,summary,reused=select_train_only(cfg,alias,rep,seed,source,case,lookup,audit=mode=='audit')
    if mode=='production':
     for policy in POLICIES:probability_unit(cfg,alias,rep,seed,source,case,lookup,policy,root)
  rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;need(rss<=8*1024**3,'CPU8GiBRSS ceiling exceeded')
 print(json.dumps({'status':'S05_CPU_UNIT_DRAINED','alias':alias,'mode':mode,'representation':rep,'cv_seed':seed,'wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cpu,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'other_tasks_or_test':False}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);p.add_argument('--alias',required=True);p.add_argument('--mode',choices=['production','audit','LM'],required=True);p.add_argument('--representation');p.add_argument('--seed',type=int);a=p.parse_args();main(Path(a.control),a.alias,a.mode,a.representation,a.seed)
