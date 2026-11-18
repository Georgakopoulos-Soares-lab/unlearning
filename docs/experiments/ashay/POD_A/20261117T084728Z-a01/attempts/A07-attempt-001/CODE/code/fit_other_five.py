"""Finite A07 other-five CPU production; producer seals remain COMPLETE_UNVERIFIED."""
import argparse,concurrent.futures,time,warnings,datetime,resource,traceback
import joblib
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from other_five_common import *
from producer_metrics import point_metrics,bootstrap_metrics,decisions
def train(x,y,c,context):
 attempts=[]
 for limit in [2000,10000]:
  model=make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',tol=1e-4,max_iter=limit,random_state=42));t=time.monotonic();cpu=time.process_time()
  with warnings.catch_warnings(record=True) as caught:
   warnings.simplefilter('always');model.fit(x,y)
  converged=not any(issubclass(w.category,ConvergenceWarning) for w in caught);other=[w for w in caught if not issubclass(w.category,ConvergenceWarning)]
  attempts.append({'context':context,'C':c,'max_iter':limit,'n_iter':model[-1].n_iter_.tolist(),'wall_seconds':time.monotonic()-t,'CPU_process_seconds':time.process_time()-cpu,'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught],'converged':converged})
  require(not other,'Unclassified numerical/runtime warning; fit rejected')
  if converged:return model,attempts
 raise RuntimeError('FAILED_CONVERGENCE: retained 2000 and10000 attempts '+json.dumps(attempts))
def distribution(p,meta,classes,weights,drawpath,policy,source):
 identity={'stage':'A07','policy':policy,'probability_array_sha256':array_sha(p),'classes':classes.tolist(),'labels_sha256':array_sha(meta['labels']),'ids_sha256':array_sha(meta['ids']),'groups_sha256':array_sha(meta['groups']),'draw_sha256':sha(drawpath),'source':source,'metric_source_sha256':sha(A/'code/producer_metrics.py'),'protocol_sha256':CFG['protocol_sha256']};key=digest(identity);root=A/'reference-distributions'/key
 with UnitLock(A/'locks/reference-distributions'/(key+'.lock')):
  if (root/'COMPLETE.json').exists():verify_seal(root,identity)
  else:
   work=new_work(root);result,valid=bootstrap_metrics(meta['labels'],p,classes,weights);np.savez_compressed(work/'values.npz',valid=valid,**result);receipt={'status':'PASS','identity':identity,'files':members(work)};os.replace(work,root);put(root/'COMPLETE.json',receipt)
  with np.load(root/'values.npz',allow_pickle=False) as z:return {m:z[m] for m in METRICS},z['valid'],ref(root/'COMPLETE.json')
def quantile(values,valid):
 vals=values[valid]
 if not len(vals):return None,None
 a,b=np.quantile(vals,[.025,.975]);return float(a),float(b)
def fit_one(unit_id):
 alias,task,key,ss=unit_id.split('/');seed=int(ss[4:]);require(stage_spec(alias,task,key,seed)==unit_id,'Bad unit identity');manifest=read(C/'A07_EXECUTION_MANIFEST.json');entry=next(u for u in manifest['units'] if u['unit_id']==unit_id);frozen=entry['identity'];require(digest(frozen)==entry['identity_sha256'],'Manifest unit identity changed');spec={'fold':frozen['fold'],'original_base_head':frozen['original_base_head'],'historical_predictions':frozen['historical_predictions'],'draws':frozen['draw'],'feature_bundles':frozen['A06_bundles'],'dependencies':frozen['A05_dependencies'],'dependency_sha256':hashlib.sha256(json.dumps(frozen['A05_dependencies'],sort_keys=True).encode()).hexdigest()}
 source=source_check();root=A/'probes'/unit_id;start=time.monotonic();cpu=time.process_time();classes=classes_for(task)
 for e in [spec['fold'],spec['original_base_head'],spec['historical_predictions'],spec['draws'],*spec['feature_bundles'].values()]:check_ref(e)
 cache_receipts={split:ref(A/'cache'/alias/task/split/'COMPLETE.json') for split in ['train','dev']};identity={'stage':'A07','unit_id':unit_id,'plan_dependency_sha256':spec['dependency_sha256'],'spec_sha256':digest(spec),'CPU_source_identity_sha256':source,'protocol_sha256':CFG['protocol_sha256'],'coverage_plan_sha256':CFG['coverage_plan_sha256'],'feature_caches':cache_receipts}
 with UnitLock(A/'locks/probes'/(unit_id+'.lock')):
  if (root/'COMPLETE.json').exists():verify_seal(root,identity);return {'unit_id':unit_id,'status':'REUSED_SEALED_PRODUCER','receipt_sha256':sha(root/'COMPLETE.json')}
  work=new_work(root)
  try:
   tr=metadata(alias,task,'train');dev=metadata(alias,task,'dev');require(set(tr['ids']).isdisjoint(dev['ids']) and set(tr['groups']).isdisjoint(dev['groups']),'TRAIN/dev overlap');require(np.array_equal(np.unique(tr['labels']),classes),'TRAIN classes differ');folds,foldpath=folds_for(task,seed,tr);x=features(alias,task,'train',key);xx=features(alias,task,'dev',key);weights,drawpath=resampling(task,dev)
   require(len(np.unique(dev['groups']))==(511 if task=='gue_splice_reconstructed' else 512),'Unexpected dev exact/RC groups')
   cv=[]
   with threadpool_limits(limits=4):
    for regularization in [.1,1.,10.]:
     scores=[];attempts=[]
     for i,(a,b) in enumerate(folds):
      model,attempt=train(x[a],tr['labels'][a],regularization,'CV/fold'+str(i));pv=model.predict_proba(x[b]);score=roc_auc_score(tr['labels'][b],pv[:,1]) if len(classes)==2 else roc_auc_score(tr['labels'][b],pv,labels=classes,multi_class='ovr',average='macro');scores.append(float(score));attempts.append(attempt);put(work/'CV_IN_PROGRESS.json',{'completed_C':cv,'current_C':regularization,'fold_aurocs':scores,'attempts':attempts})
     cv.append({'C':regularization,'fold_aurocs':scores,'mean_auroc':float(np.mean(scores)),'convergence':attempts});put(work/'CV.json',cv)
    selected=max(cv,key=lambda z:(z['mean_auroc'],-z['C']))['C'];model,final_attempts=train(x,tr['labels'],selected,'FINAL_ALL_TRAIN');require(np.array_equal(model[-1].classes_,classes),'Final classes differ');joblib.dump(model,work/'head.joblib')
    base=joblib.load(check_ref(spec['original_base_head']));require(np.array_equal(base[-1].classes_,classes) and base[0].n_features_in_==1920,'Wrong base head classes/width');basehash=sha(spec['original_base_head']['path']);require(basehash==spec['dependencies']['original_base_head'],'Wrong fixed-base head')
    # Immutable original-base object is only applied. Reload producer head for serialization parity.
    target={'independent_refit':model.predict_proba(xx),'fixed_original_base':base.predict_proba(xx)};reloaded=joblib.load(work/'head.joblib');serialization_max=float(np.max(np.abs(reloaded.predict_proba(xx)-target['independent_refit'])));require(serialization_max<=1e-10,'Serialized head prediction mismatch');require(sha(spec['original_base_head']['path'])==basehash,'Base head mutated')
   for p in target.values():validate_prob(p,dev['labels'],classes)
   np.savez_compressed(work/'dev_predictions.npz',**{k:dev[k] for k in ['ids','labels','groups','sequence_sha256']},classes=classes,**target,**{policy+'__predicted_labels':decisions(p,classes) for policy,p in target.items()})
   psha=sha(work/'dev_predictions.npz');historical,histpath=references(task,key,seed,dev);metric_rows=[];paired_rows=[];boot_arrays={};validation={};valid_all=None;reference_map=[];endpoint=I6['checkpoint_identities'][alias]['candidate_id'];content=I6['checkpoint_identities'][alias]['model_tensor_content_sha256'];unitreceipt=str((root/'COMPLETE.json').relative_to(A));drawsha=sha(drawpath)
   contrast_ids={x['reference']:x for x in read(D6/'CONTRAST_PLAN.json')['contrasts'] if x['target']==alias and x['reference'] in ['base','R1']}
   for policy,p in target.items():
    point,diagnostics=point_metrics(dev['labels'],p,classes);boot,valid=bootstrap_metrics(dev['labels'],p,classes,weights);valid_all=valid if valid_all is None else valid_all&valid;boot_arrays.update({policy+'__'+m:boot[m] for m in METRICS});validation[policy]=diagnostics
    shared={'checkpoint_alias':alias,'checkpoint_content_id':content,'lineage':'NEW','ingestion_status':'NEW_IN_A07','task':task,'split':'dev','representation':'decoder.final_norm' if key=='final_norm' else key.replace('decoder_layer_','decoder.layers.'),'CV_seed':seed,'policy':policy,'sample_count':len(dev['ids']),'group_count':len(np.unique(dev['groups'])),'target_count':None,'bootstrap_attempted':2000,'bootstrap_valid':int(valid.sum()),'bootstrap_invalid':int((~valid).sum()),'status':'COMPLETE_UNVERIFIED','missing_reason':None,'protocol_sha256':CFG['protocol_sha256'],'input_sha256':cache_receipts['dev']['sha256'],'prediction_sha256':psha,'prediction_array_sha256':array_sha(p),'draw_sha256':drawsha,'receipt':unitreceipt,'producer_validation':'PASS'}
    for m in METRICS:
     lo,hi=quantile(boot[m],valid);metric_rows.append({**shared,'metric':m,'estimate':point[m],'ci_low':lo,'ci_high':hi})
    refs={'base':historical['prob_base_refit'],'R1':historical['prob_h3_only_refit' if policy=='independent_refit' else 'prob_h3_only_fixed_base']};ref_sources={k:ref(histpath) for k in refs}
    if key in ['decoder_layer_16','final_norm']:
     for control in ['composition','kmer4']:cp,cp_path=control_predictions(task,control,seed,dev);refs['control_'+control]=cp;ref_sources['control_'+control]=ref(cp_path)
    for refname,rp in refs.items():
     reference_policy='control' if refname.startswith('control_') else policy;rd,rv,rdreceipt=distribution(rp,dev,classes,weights,drawpath,reference_policy,ref_sources[refname]);common=valid&rv;require(np.array_equal(valid,rv),'Target/reference class completeness differs');rp_point,_=point_metrics(dev['labels'],rp,classes);reference_map.append({'policy':policy,'reference':refname,'reference_policy':reference_policy,'prediction':ref_sources[refname],'probability_array_sha256':array_sha(rp),'distribution_receipt':rdreceipt})
     refendpoint='control:'+refname.removeprefix('control_') if refname.startswith('control_') else contrast_ids[refname]['reference_endpoint_id'];logical=digest({'target_endpoint_id':endpoint,'reference_endpoint_id':refendpoint,'policy':policy,'reference_policy':reference_policy,'task':task,'split':'dev','representation':key,'seed':seed,'protocol_sha256':CFG['protocol_sha256'],'direction':'target-reference'})
     for m in METRICS:
      delta=boot[m]-rd[m];boot_arrays[policy+'__minus_'+refname+'__'+m]=delta;lo,hi=quantile(delta,common);paired_rows.append({**shared,'reference':refname,'metric':m,'estimate':point[m]-rp_point[m],'ci_low':lo,'ci_high':hi,'bootstrap_valid':int(common.sum()),'bootstrap_invalid':int((~common).sum()),'target_endpoint_id':endpoint,'reference_endpoint_id':refendpoint,'reference_policy':reference_policy,'reference_lineage':'REUSED','reference_prediction_sha256':ref_sources[refname]['sha256'],'reference_prediction_array_sha256':array_sha(rp),'reference_receipt':ref_sources[refname]['path'],'reference_distribution_receipt_sha256':rdreceipt['sha256'],'direction':'target-reference','metric_orientation':'lower' if m=='classification_cross_entropy' else 'higher','contrast_id':logical})
   np.savez_compressed(work/'dev_bootstrap.npz',valid=valid_all,**boot_arrays)
   paramhash=digest({'scaler_mean':array_sha(model[0].mean_),'scaler_var':array_sha(model[0].var_),'scaler_scale':array_sha(model[0].scale_),'coef':array_sha(model[-1].coef_),'intercept':array_sha(model[-1].intercept_),'classes':classes.tolist()})
   put(work/'FINAL_FIT.json',{'selected_C':selected,'attempts':final_attempts,'class_order':classes.tolist(),'train_rows':1024,'train_ids_sha256':array_sha(tr['ids']),'fold':ref(foldpath),'parameter_content_sha256':paramhash,'optimizer_random_state':42,'feature_dtype':'float32','standardizer_fitted_only_on':'TRAIN','original_base_head':spec['original_base_head']})
   put(work/'RESULTS.json',{'metrics':metric_rows,'paired_contrasts':paired_rows,'diagnostics':validation,'reference_map':reference_map,'status':'COMPLETE_UNVERIFIED','producer_validation':'PASS','independent_release_verification':'PENDING_A08'})
   with np.load(work/'dev_predictions.npz',allow_pickle=False) as z:
    pair(z,dev,classes)
    for policy,p in target.items():require(np.array_equal(z[policy],p),'Saved probability bytes differ')
   require(len(metric_rows)==10 and len(paired_rows)==(40 if key in ['decoder_layer_16','final_norm'] else 20),'Unexpected Cartesian result count')
   receipt={'schema':'pod-a-a07-producer-unit-v1','status':'COMPLETE_UNVERIFIED','producer_validation':'PASS','identity':identity,'candidate':alias,'task':task,'representation':key,'seed':seed,'head_count':1,'fixed_base_application_count':1,'selected_C':selected,'parameter_content_sha256':paramhash,'serialization_probability_max_abs':serialization_max,'planned_optimizer_fits':16,'actual_optimizer_fits':sum(len(at) for c in cv for at in c['convergence'])+len(final_attempts),'original_base_head':spec['original_base_head'],'fold':spec['fold'],'files':members(work),'wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cpu,'peak_RSS_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};os.replace(work,root);put(root/'COMPLETE.json',receipt)
   return {'unit_id':unit_id,'status':'COMPLETE_UNVERIFIED','producer_validation':'PASS','selected_C':selected,'wall_seconds':receipt['wall_seconds'],'actual_optimizer_fits':receipt['actual_optimizer_fits'],'receipt_sha256':sha(root/'COMPLETE.json')}
  except BaseException as exc:
   put(work/'FAILED.json',{'unit_id':unit_id,'type':type(exc).__name__,'reason':str(exc),'traceback':traceback.format_exc(),'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});q=A/'quarantine/failed-units'/unit_id;q=q.with_name(q.name+'-'+uuid.uuid4().hex);q.parent.mkdir(parents=True,exist_ok=True);os.replace(work,q);return {'unit_id':unit_id,'status':'FAILED','reason':str(exc),'failure_evidence':str(q/'FAILED.json')}
def main(args):
 require(args.stage=='A07','Cross-stage dispatch rejected');manifest=read(C/'A07_EXECUTION_MANIFEST.json');allowed={u['unit_id'] for u in manifest['units']};ids=args.unit or [u['unit_id'] for u in manifest['units'] if u['candidate']==args.candidate and u['task']==args.task];require(ids and len(ids)==len(set(ids)) and set(ids)<=allowed,'Unit outside finite approved manifest');require(read(C/'ADAPTER_VALIDATION.json')['status']=='PASS','Adapter tests required');require(read(C/'A08_AUDIT_HANDOFF_PLAN.json')['before_any_A07_dev_predictions'],'Audit plan missing');source_check()
 if not args.unit:require(read(C/'INITIAL_PRODUCTION_GATE.json')['status']=='PASS','Initial binary and splice gate required')
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 with UnitLock(A/'locks/pipeline.lock'):
  with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
   for result in pool.map(fit_one,ids):print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['A07'],required=True);p.add_argument('--candidate',choices=['R4','R6']);p.add_argument('--task',choices=TASKS);p.add_argument('--unit',action='append');main(p.parse_args())
