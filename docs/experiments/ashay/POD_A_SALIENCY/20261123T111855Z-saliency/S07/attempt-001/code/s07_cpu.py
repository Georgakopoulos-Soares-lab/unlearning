"""Finite source-bound S07 TRAIN-only producer. Independent scientific release/audits belong to S08."""
from s07_contract import *
import time,resource,warnings,argparse
import joblib
from inherited_fit import pipeline
from inherited_metrics import point_metrics,bootstrap_metrics
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits

def parameter_digest(pipe):
 h=hashlib.sha256()
 for name,x in [('mean',pipe[0].mean_),('scale',pipe[0].scale_),('var',pipe[0].var_),('coef',pipe[-1].coef_),('intercept',pipe[-1].intercept_),('classes',pipe[-1].classes_)]:
  a=np.asarray(x);need(np.isfinite(a).all(),'Nonfinite estimator parameter');h.update(json.dumps([name,str(a.dtype),list(a.shape)],separators=(',',':')).encode()+b'\0');h.update(a.tobytes(order='C'))
 return h.hexdigest()
def auroc(y,p,classes):return float(roc_auc_score(y,p[:,1]) if len(classes)==2 else roc_auc_score(y,p,labels=classes,multi_class='ovr',average='macro'))
def choose(rows):return max(rows,key=lambda r:(r['mean_fold_AUROC'],-r['C']))['C']

def fit_call(root,ident,x,y,C,classes,validation=None):
 root=Path(root)
 if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['model.joblib','TRACE.json']);return joblib.load(root/'model.joblib'),load(root/'TRACE.json'),True
 need(not root.exists(),'Incomplete fit call preserved; explicit versioned repair required');root.mkdir(parents=True);history=[]
 for limit in [2000,10000]:
  model=pipeline(C,limit);start=time.perf_counter();cpu=time.process_time()
  with warnings.catch_warnings(record=True) as caught:warnings.simplefilter('always');model.fit(x,y)
  history.append({'max_iter':limit,'n_iter':model[-1].n_iter_.tolist(),'wall_seconds':time.perf_counter()-start,'CPU_seconds':time.process_time()-cpu,'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught]});put(root/'ATTEMPTS.partial.json',history);need(all(issubclass(w.category,ConvergenceWarning) for w in caught),'Non-convergence-independent warning blocks this call')
  if not caught:break
 else:raise RuntimeError('Persistent inherited ConvergenceWarning after2000/10000; preserve both attempts')
 need(model[-1].classes_.tolist()==classes and model[0].n_features_in_==x.shape[1],'Class order/width changed');need(model[0].transform(x[:2]).dtype==np.float32,'Inherited scaler transform arithmetic changed');score=None
 if validation is not None:score=auroc(validation[1],model.predict_proba(validation[0]),model[-1].classes_)
 tmp=root/'model.joblib.partial';joblib.dump(model,tmp);os.replace(tmp,root/'model.joblib');roundtrip=joblib.load(root/'model.joblib');need(parameter_digest(roundtrip)==parameter_digest(model),'Serialization parameter content changed');need(np.array_equal(model.predict_proba(x[:2]),roundtrip.predict_proba(x[:2])),'Serialization function changed');trace={'schema_version':'s07-solver-call-v1','status':'COMPLETE_UNVERIFIED','identity':ident,'C':C,'attempts':history,'fit_rows':len(y),'fit_input_sha256':hashlib.sha256(x.tobytes()).hexdigest(),'fit_labels_sha256':hashlib.sha256(y.tobytes()).hexdigest(),'parameter_content_sha256':parameter_digest(model),'validation_AUROC':score,'TRAIN_only':True,'class_order':classes,'serialization_roundtrip':'PASS','source_max_iter_rule':'Fresh2000; only ConvergenceWarning permits fresh10000; no warm start','scaler_training_mean_max_residual':float(np.max(np.abs(model[0].mean_-np.mean(x,axis=0,dtype=np.float64))))};need(trace['scaler_training_mean_max_residual']<=1e-12,'Fold scaler not trained on exact fitting rows');put(root/'TRACE.json',trace);write_seal(root,ident,['model.joblib','TRACE.json'],{'initial_optimizer_calls':1,'actual_optimizer_calls':len(history),'retries':len(history)-1});return model,trace,False

def select_train(c,cfg,v,alias,t,rep,seed,rows,case):
 x,y,ids=matrix(c,alias,t,rep,'train');classes=cfg['feature_config']['cohorts'][t]['train']['class_order'];fs=folds(cfg,t,seed,ids);pid=sid(rows,'final_head',r=rep,s=seed,p='independent_refit');ident=base_identity(cfg,v,t,rep,seed,pid);root=case/'tasks'/t/'production'/KEYS[HOOKS.index(rep)]/('seed'+str(seed))
 if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json']);return root,load(root/'SUMMARY.json'),True
 root.mkdir(parents=True,exist_ok=True);entries=[];candidates=[]
 for j,C in enumerate(cfg['C_grid']):
  scores=[]
  for i,(tr,va) in enumerate(fs):
   need(sorted(set(y[tr].tolist()))==sorted(set(y[va].tolist()))==classes,'Required fold classes missing');cid=sid(rows,'optimizer_call',r=rep,s=seed,p='independent_refit',j=j,fold=i);cr=root/'cv'/('C'+str(j)+'-fold'+str(i));callident={**ident,'planned_spec_id':cid,'C':C,'fold':i,'training_IDs_sha256':digest([ids[k] for k in tr]),'validation_IDs_sha256':digest([ids[k] for k in va])};_,trc,reused=fit_call(cr,callident,x[tr],y[tr],C,classes,(x[va],y[va]));scores.append(trc['validation_AUROC']);entries.append({'planned_spec_id':cid,'relative_root':str(cr.relative_to(root)),'receipt_sha256':sha(cr/'COMPLETE.json'),'optimizer_calls':len(trc['attempts']),'reused_this_invocation':reused});print('S07_CV_CALL_SEALED',alias,t,rep,seed,j,i,'REUSED' if reused else 'NEW',flush=True)
  candidates.append({'C':C,'fold_AUROC':scores,'mean_fold_AUROC':float(np.mean(scores))});put(root/'CV_SELECTION.partial.json',candidates)
 selected=choose(candidates);cid=sid(rows,'optimizer_call',r=rep,s=seed,p='independent_refit',j=None,fold=None);cr=root/'final';pipe,trc,reused=fit_call(cr,{**ident,'planned_spec_id':cid,'C':selected,'fold':None,'training_IDs_sha256':digest(ids)},x,y,selected,classes);entries.append({'planned_spec_id':cid,'relative_root':'final','receipt_sha256':sha(cr/'COMPLETE.json'),'optimizer_calls':len(trc['attempts']),'reused_this_invocation':reused});(root/'head.joblib').write_bytes((cr/'model.joblib').read_bytes());np.savez(root/'PARAMETERS.npz',scaler_mean=pipe[0].mean_,scaler_scale=pipe[0].scale_,scaler_var=pipe[0].var_,coef=pipe[-1].coef_,intercept=pipe[-1].intercept_,classes=pipe[-1].classes_);summary={'schema_version':'s07-final-head-v1','status':'COMPLETE_UNVERIFIED','identity':ident,'planned_spec_id':pid,'selected_C':selected,'CV':candidates,'parameter_content_sha256':parameter_digest(pipe),'head_serialization_sha256':sha(root/'head.joblib'),'initial_optimizer_calls':16,'actual_optimizer_calls':sum(e['optimizer_calls'] for e in entries),'retries':sum(e['optimizer_calls']-1 for e in entries),'fit_rows':1024,'dev_used_for_selection':False,'class_order':classes,'scaler_transform_semantics':'Qualified sklearn preserves float32 transformed features; no extra cast/normalization','serialization_roundtrip':'PASS'};put(root/'SUMMARY.json',summary);put(root/'CV_INDEX.json',{'calls':entries});write_seal(root,ident,['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json'],{'final_heads':1,'initial_optimizer_calls':16,'actual_optimizer_calls':summary['actual_optimizer_calls'],'retries':summary['retries']});return root,summary,False

def canonical_metric(uid,name,value,ci,reason,source,n,g,nvalid,drawsha):return {'unit_id':uid,'reference_unit_id':None,'metric':name,'direction':'lower_better' if name=='cross_entropy' else 'higher_better','estimate':value,'ci_low':None if ci is None else float(ci[0]),'ci_high':None if ci is None else float(ci[1]),'missing_reason':reason,'sample_count':n,'group_count':g,'valid_targets':None,'bootstrap_attempted':2000,'bootstrap_valid':nvalid,'bootstrap_invalid':2000-nvalid,'draw_sha256':drawsha,'common_mask_sha256':None,'uncertainty':'pointwise_exploratory_conditional','source_sha256':source}

def predict_unit(c,cfg,v,alias,t,rep,seed,rows,case,policy,headroot):
 x,y,ids=matrix(c,alias,t,rep,'dev');path=headroot/'head.joblib' if policy=='independent_refit' else reference(cfg,t,rep,seed)[0];before=sha(path);pipe=joblib.load(path);classes=cfg['feature_config']['cohorts'][t]['dev']['class_order'];need(pipe[-1].classes_.tolist()==classes and pipe[0].n_features_in_==1920,'Probability class columns incompatible');pid=sid(rows,'prediction',r=rep,s=seed,p=policy,split='dev');ident={**base_identity(cfg,v,t,rep,seed,pid),'split':'dev','policy':policy,'head_sha256':before,'head_parameter_content_sha256':parameter_digest(pipe),'DEV_extraction_planned_id':next(x['d'] for x in rows if x['k']=='fixed_application' and x['r']==rep and x['s']==seed),'dev_draw_sha256':cfg['feature_config']['draws'][t]['file_sha256']};root=case/'tasks'/t/'probabilities'/KEYS[HOOKS.index(rep)]/('seed'+str(seed))/policy
 if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['predictions.npz','draws.npz','METRICS.json']);return load(root/'METRICS.json'),True
 need(not root.exists(),'Incomplete probability unit preserved');root.mkdir(parents=True);p=pipe.predict_proba(x);validate_probabilities(p,pipe[-1].classes_,classes,512);need(p.dtype==np.float64 and p.shape==(512,len(classes)) and np.isfinite(p).all() and np.allclose(p.sum(1),1,atol=1e-12,rtol=0),'Invalid probability matrix');need(np.array_equal(p,joblib.load(path).predict_proba(x)),'Producer serialized-pipeline prediction roundtrip differs');w,drawsha=weights(c,t);points,diagnostic=point_metrics(y,p,pipe[-1].classes_);dist,sharedvalid=bootstrap_metrics(y,p,pipe[-1].classes_,w);records=[];vectors={}
 for name in METRICS:
  d=np.asarray(dist[NAME_MAP[name]],dtype=np.float64);valid=sharedvalid&np.isfinite(d);need(np.array_equal(valid,sharedvalid) and np.isnan(d[~valid]).all(),'Unexpected per-quantity invalid draw');ci=np.quantile(d[valid],[.025,.975],method='linear') if valid.any() else None;value=points[NAME_MAP[name]];reason=None if np.isfinite(value) and valid.any() else 'Undefined required numeric point or no classcomplete valid draws';need(np.isfinite(value),'Required numeric point missing');record=canonical_metric(digest(ident),name,float(value),ci,reason,cfg['_source'],512,cfg['feature_config']['cohorts'][t]['dev']['groups'],int(valid.sum()),drawsha);records.append({'planned_spec_id':sid(rows,'classifier_metric',r=rep,s=seed,p=policy,split='dev',m=name),'source_row_id':digest({'prediction_unit_id':digest(ident),'metric':name}),'canonical_metric':record,'bootstrap_vector_sha256':hashlib.sha256(d.tobytes()).hexdigest(),'valid_mask_sha256':hashlib.sha256(valid.tobytes()).hexdigest(),'distribution_selector':name,'validity_selector':name+'_valid','release_status':'COMPLETE_UNVERIFIED'});vectors[name]=d;vectors[name+'_valid']=valid
 meta=metadata(cfg,t,'dev');np.savez(root/'predictions.npz',ids=np.array(ids),labels=y,groups=np.array([r['group'] for r in meta]),classes=np.array(classes),probabilities=p);np.savez(root/'draws.npz',**vectors)
 for n in ['predictions.npz','draws.npz']:
  with np.load(root/n,allow_pickle=False) as z:
   if n=='predictions.npz':need(np.array_equal(z['probabilities'],p) and z['ids'].tolist()==ids and z['classes'].tolist()==classes,'Producer probability serialization changed')
   else:
    for key,value in vectors.items():need(np.array_equal(z[key],value,equal_nan=True),'Draw serialization changed')
 need(sha(path)==before and parameter_digest(pipe)==ident['head_parameter_content_sha256'],'Head/scaler changed during application');result={'schema_version':'s07-probability-path-v1','status':'COMPLETE_UNVERIFIED','identity':ident,'actual_prediction_unit_id':digest(ident),'metrics':records,'point_diagnostics':diagnostic,'producer_serialization_validation':'PASS','independent_release':'PENDING_S08','new_contrasts_or_LM':False};put(root/'METRICS.json',result);write_seal(root,ident,['predictions.npz','draws.npz','METRICS.json'],{'dev_paths':1,'classifier_metric_records':5});return result,False

def run_unit(c,alias,t,rep,seed,gate=False):
 start=time.monotonic();cp=time.process_time();cfg,v=ready(c,alias,t,rep,seed,gate);rows=specs(str(c),alias,t);case=Path(cfg['artifacts_root'])/'candidates'/alias;lock=case/'locks'/(t+'-'+KEYS[HOOKS.index(rep)]+'-seed'+str(seed)+'.lock')
 with threadpool_limits(limits=4),exclusive(lock):
  head,summary,reused=select_train(c,cfg,v,alias,t,rep,seed,rows,case)
  for policy in POLICIES:
   result,_=predict_unit(c,cfg,v,alias,t,rep,seed,rows,case,policy,head)
   if policy=='fixed_original_base':
    pid=sid(rows,'fixed_application',r=rep,s=seed,p=policy);rr=case/'tasks'/t/'fixed-applications'/KEYS[HOOKS.index(rep)]/('seed'+str(seed));ident={**result['identity'],'planned_spec_id':pid,'prediction_planned_spec_id':result['identity']['planned_spec_id'],'fixed_reference_planned_identity':next(x['ref'] for x in rows if x['id']==pid),'new_reference_fits':0,'target_recentering_or_recalibration':False}
    if (rr/'COMPLETE.json').exists():verify_seal(rr,ident,required=['APPLICATION.json'])
    else:need(not rr.exists(),'Preserve incomplete fixed application');rr.mkdir(parents=True);put(rr/'APPLICATION.json',ident);write_seal(rr,ident,['APPLICATION.json'],{'fixed_base_applications':1,'new_reference_fits':0})
 rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;need(rss<=8*1024**3,'8GiB worker RSS ceiling exceeded');report={'schema_version':'s07-producer-unit-completion-v1','status':'COMPLETE_UNVERIFIED','producer_status':'PASS','alias':alias,'task':t,'representation':rep,'cv_seed':seed,'initial_optimizer_calls':16,'actual_optimizer_calls':summary['actual_optimizer_calls'],'retries':summary['retries'],'source_identity_sha256':cfg['_source'],'head_receipt_sha256':sha(head/'COMPLETE.json'),'producer_serialization_roundtrip':'PASS','wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cp,'peak_RSS_bytes':rss,'operational_gate':gate,'backbone_or_LM_calls':0,'independent_audits':0,'owned_process':process_identity()};put(case/'tasks'/t/'unit-completions'/(KEYS[HOOKS.index(rep)]+'-seed'+str(seed)+'.json'),report);print('S07_PRODUCER_UNIT_COMPLETE',alias,t,rep,seed,'retries',report['retries'],flush=True);return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--control',required=True);p.add_argument('--alias',required=True);p.add_argument('--task',required=True);p.add_argument('--representation',required=True);p.add_argument('--seed',required=True,type=int);p.add_argument('--operational-gate',action='store_true');a=p.parse_args();run_unit(Path(a.control),a.alias,a.task,a.representation,a.seed,a.operational_gate)
