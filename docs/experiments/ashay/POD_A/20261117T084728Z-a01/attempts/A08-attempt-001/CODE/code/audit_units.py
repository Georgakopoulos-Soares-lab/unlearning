"""All-unit A08 independent reconstruction, point, every-draw and interval audit."""
from audit_common import *
import time,datetime,traceback,resource,concurrent.futures,argparse
import joblib
from threadpoolctl import threadpool_limits
from independent_math import metrics,reconstruct
def distribution(p,meta,classes,weights,drawpath,policy,origin):
 identity={'policy':policy,'probabilities':array_sha(p),'classes':classes.tolist(),'ids':array_sha(meta['ids']),'labels':array_sha(meta['labels']),'groups':array_sha(meta['groups']),'draw':ref(drawpath),'source':origin,'audit_source':source_check(),'protocol':CFG['protocol_sha256']};key=digest(identity);root=A/'independent-reference-cache'/key
 with Lock(A/'locks/reference-cache'/(key+'.lock')):
  if (root/'COMPLETE.json').exists():seal_check(root,identity)
  else:
   tmp=workdir(root);values,valid=metrics(meta['labels'],p,classes,weights);np.savez_compressed(tmp/'distributions.npz',valid=valid,**values);seal(tmp,root,{'status':'PASS','identity':identity})
  with np.load(root/'distributions.npz',allow_pickle=False) as z:return {m:z[m] for m in METRICS},z['valid'],ref(root/'COMPLETE.json')
def residual(a,b,valid=None,atol=1e-12):
 a=np.asarray(a);b=np.asarray(b);require(a.shape==b.shape,'Numerical shape mismatch')
 if valid is None:valid=np.ones(a.shape,dtype=bool)
 require(np.array_equal(np.isfinite(a[valid]),np.isfinite(b[valid])) and np.isfinite(a[valid]).all(),'Nonfinite numerical comparison');value=float(np.max(np.abs(a[valid]-b[valid]))) if np.any(valid) else 0.;
 if value>atol:
  out=A/'numeric-discrepancies'/(uuid.uuid4().hex+'.npz');out.parent.mkdir(exist_ok=True);np.savez_compressed(out,audit=a,producer=b,valid=valid);raise ValueError(f'Numerical tolerance failed: {value:.17g}>{atol:.17g}; private discrepancy {out}')
 return value
def check_attempts(attempts):
 require(len(attempts) in [1,2] and attempts[0]['max_iter']==2000 and attempts[-1]['converged'],'Convergence evidence invalid')
 if len(attempts)==2:require(attempts[1]['max_iter']==10000 and not attempts[0]['converged'] and any(w['category']=='ConvergenceWarning' for w in attempts[0]['warnings']),'Retry evidence invalid')
 require(not attempts[-1]['warnings'],'Accepted final fit retained warnings');return len(attempts)-1
def audit(uid):
 spec=unit_spec(uid);alias,task,key,ss=uid.split('/');seed=int(ss[4:]);producer=checked(spec['producer_receipt']);s=spec['scientific_dependencies'];src=source_check();root=A/'audits'/uid;identity={'stage':'A08','unit_id':uid,'producer_receipt':spec['producer_receipt'],'spec_sha256':digest(spec),'audit_source_sha256':src,'protocol_sha256':CFG['protocol_sha256']}
 with Lock(A/'locks/audit'/(uid+'.lock')):
  if (root/'COMPLETE.json').exists():seal_check(root,identity);return read(root/'NUMERICAL_AUDIT.json')
  tmp=workdir(root);t=time.monotonic();cpu=time.process_time()
  try:
   p_root=producer.parent;pr=read(producer);validate_members(p_root,pr);require(pr['status']=='COMPLETE_UNVERIFIED' and pr['producer_validation']=='PASS','Producer not accepted');require(pr['identity']==spec['producer_identity'],'Producer identity drift');require(pr['fold']==s['fold'] and pr['original_base_head']==s['original_base_head'],'Fold/base dependency drift')
   x,tr,trcache=features(alias,task,'train',key);xx,dev,decache=features(alias,task,'dev',key);require(set(tr['ids']).isdisjoint(dev['ids']) and set(tr['groups']).isdisjoint(dev['groups']),'TRAIN/dev pairing leakage');require(len(tr['ids'])==1024 and len(dev['ids'])==512,'Cohort count drift');classes=classes_for(task);fold_list,fp=folds(task,seed,tr);require(ref(fp)==s['fold'],'Frozen fold hash mismatch');w,drawpath=draw_weights(task,'dev',dev);require(ref(drawpath)==s['draw'],'Frozen draw hash mismatch')
   for split,cache_ref in [('train',trcache),('dev',decache)]:require(cache_ref==pr['identity']['feature_caches'][split],'Feature cache identity mismatch')
   cv=read(p_root/'CV.json');final=read(p_root/'FINAL_FIT.json');require([c['C'] for c in cv]==[.1,1.,10.] and final['train_ids_sha256']==array_sha(tr['ids']),'TRAIN membership/C grid drift');retries=0
   for c in cv:
    require(len(c['fold_aurocs'])==5 and all(np.isfinite(c['fold_aurocs'])) and c['mean_auroc']==float(np.mean(c['fold_aurocs'])),'CV aggregation mismatch');require(len(c['convergence'])==5,'CV attempts missing')
    for attempts in c['convergence']:retries+=check_attempts(attempts)
   retries+=check_attempts(final['attempts']);selected=max(cv,key=lambda e:(e['mean_auroc'],-e['C']))['C'];require(selected==pr['selected_C']==final['selected_C'] and pr['actual_optimizer_fits']==16+retries,'Selection/retry accounting failed')
   model=joblib.load(p_root/'head.joblib');basepath=checked(s['original_base_head']);base=joblib.load(basepath);basehash=sha(basepath);require(np.array_equal(model[-1].classes_,classes) and np.array_equal(base[-1].classes_,classes) and model[0].n_features_in_==1920 and base[0].n_features_in_==1920,'Head class/width mismatch');mean=np.mean(x,axis=0,dtype=np.float64);variance=np.var(x,axis=0,dtype=np.float64);mean_error=float(np.max(np.abs(mean-model[0].mean_)));var_error=float(np.max(np.abs(variance-model[0].var_)));require(np.allclose(mean,model[0].mean_,rtol=1e-12,atol=1e-12) and np.allclose(variance,model[0].var_,rtol=1e-12,atol=1e-12) and int(model[0].n_samples_seen_)==1024,'Final scaler TRAIN moments mismatch')
   parameter_hash=digest({'scaler_mean':array_sha(model[0].mean_),'scaler_var':array_sha(model[0].var_),'scaler_scale':array_sha(model[0].scale_),'coef':array_sha(model[-1].coef_),'intercept':array_sha(model[-1].intercept_),'classes':classes.tolist()});require(parameter_hash==final['parameter_content_sha256']==pr['parameter_content_sha256'],'Parameter content signature mismatch');head=model[-1];require(head.C==selected and head.solver=='lbfgs' and head.class_weight=='balanced' and head.penalty=='l2' and head.tol==1e-4 and head.random_state==42 and head.max_iter==final['attempts'][-1]['max_iter'],'Saved estimator configuration differs');paramhash=digest({'scaler_mean':array_sha(model[0].mean_),'scaler_var':array_sha(model[0].var_),'scaler_scale':array_sha(model[0].scale_),'coef':array_sha(head.coef_),'intercept':array_sha(head.intercept_),'classes':classes.tolist()});require(paramhash==final['parameter_content_sha256']==pr['parameter_content_sha256'],'Parameter content hash mismatch')
   reconstructed={p:reconstruct(head,xx) for p,head in [('independent_refit',model),('fixed_original_base',base)]};maxp=0.;worst={};saved_array_hashes={}
   np.savez_compressed(tmp/'independent_predictions.npz',**{k:dev[k] for k in ['ids','labels','groups','sequence_sha256']},classes=classes,**reconstructed)
   with np.load(p_root/'dev_predictions.npz',allow_pickle=False) as saved:
    paired(saved,dev,classes)
    for p in POLICIES:
     probabilities_valid(saved[p],dev['labels'],classes);probabilities_valid(reconstructed[p],dev['labels'],classes);maxp=max(maxp,residual(reconstructed[p],saved[p],atol=1e-10));where=np.unravel_index(np.argmax(np.abs(reconstructed[p]-saved[p])),saved[p].shape);saved_array_hashes[p]=array_sha(saved[p]);worst[p]={'row_index':int(where[0]),'class_column':int(where[1])}
   require(sha(basepath)==basehash,'Original base head changed');historical,histpath=historical_refs(task,key,seed,'dev',dev);result=read(p_root/'RESULTS.json');mrows={(r['policy'],r['metric']):r for r in result['metrics']};crows={(r['policy'],r['reference'],r['metric']):r for r in result['paired_contrasts']};require(len(mrows)==10 and len(crows)==(40 if key in ['decoder_layer_16','final_norm'] else 20),'Unexpected result keys');arrays={};maxpoint=0.;maxdraw=0.;maxci=0.;tested=[];refreceipts=[];pointvalues={};valid_all=None
   with np.load(p_root/'dev_bootstrap.npz',allow_pickle=False) as saved:
    for policy,p in reconstructed.items():
     point,pvalid=metrics(dev['labels'],p,classes,np.ones((1,len(p))));require(pvalid.all(),'Undefined point metric');boot,valid=metrics(dev['labels'],p,classes,w);require(np.array_equal(valid,saved['valid']),'Bootstrap validity mask differs');valid_all=valid if valid_all is None else valid_all&valid;pointvalues[policy]={m:float(point[m][0]) for m in METRICS}
     for m in METRICS:
      row=mrows[policy,m];require(row['prediction_array_sha256']==saved_array_hashes[policy] and row['input_sha256']==decache['sha256'] and row['sample_count']==len(dev['ids']) and row['group_count']==len(np.unique(dev['groups'])),'Marginal provenance/count mismatch');maxpoint=max(maxpoint,residual([point[m][0]],[row['estimate']]));maxdraw=max(maxdraw,residual(boot[m],saved[policy+'__'+m],valid));require(np.isnan(saved[policy+'__'+m][~valid]).all(),'Invalid draws must remain undefined');ci=np.quantile(boot[m][valid],[.025,.975]);maxci=max(maxci,residual(ci,[row['ci_low'],row['ci_high']]));require(row['bootstrap_attempted']==2000 and row['bootstrap_valid']==int(valid.sum()) and row['bootstrap_invalid']==int((~valid).sum()),'Marginal draw counts mismatch');arrays[policy+'__'+m]=boot[m];tested.append({'kind':'marginal','policy':policy,'reference':None,'metric':m,'attempted':2000,'valid':int(valid.sum()),'invalid':int((~valid).sum())})
     refs={'base':historical['prob_base_refit'],'R1':historical['prob_h3_only_refit' if policy=='independent_refit' else 'prob_h3_only_fixed_base']};origins={n:ref(histpath) for n in refs}
     if key in ['decoder_layer_16','final_norm']:
      for kind in ['composition','kmer4']:v,path=controls(task,kind,seed,'dev',dev);refs['control_'+kind]=v;origins['control_'+kind]=ref(path)
     for name,rp in refs.items():
      probabilities_valid(rp,dev['labels'],classes);rp_point,rvalid=metrics(dev['labels'],rp,classes,np.ones((1,len(rp))));rd,rv,rc=distribution(rp,dev,classes,w,drawpath,'control' if name.startswith('control_') else policy,origins[name]);require(np.array_equal(valid,rv),'Paired missing-class masks differ');refreceipts.append(rc)
      for m in METRICS:
       row=crows[policy,name,m];require(row['reference_prediction_sha256']==origins[name]['sha256'] and row['reference_prediction_array_sha256']==array_sha(rp) and row['draw_sha256']==sha(drawpath),'Reference probability/draw identity mismatch');delta=boot[m]-rd[m];keyname=policy+'__minus_'+name+'__'+m;maxpoint=max(maxpoint,residual([point[m][0]-rp_point[m][0]],[row['estimate']]));maxdraw=max(maxdraw,residual(delta,saved[keyname],valid));require(np.isnan(saved[keyname][~valid]).all(),'Invalid paired draws must remain undefined');ci=np.quantile(delta[valid],[.025,.975]);maxci=max(maxci,residual(ci,[row['ci_low'],row['ci_high']]));require(row['bootstrap_attempted']==2000 and row['bootstrap_valid']==int(valid.sum()) and row['bootstrap_invalid']==int((~valid).sum()),'Paired draw count mismatch');arrays[keyname]=delta;tested.append({'kind':'paired','policy':policy,'reference':name,'metric':m,'attempted':2000,'valid':int(valid.sum()),'invalid':int((~valid).sum())})
   np.savez_compressed(tmp/'independent_predictions.npz',**{k:dev[k] for k in ['ids','labels','groups','sequence_sha256']},classes=classes,**reconstructed);np.savez_compressed(tmp/'bootstrap_independent.npz',valid=valid_all,**arrays)
   audit_record={'schema':'pod-a-a08-independent-unit-audit-v1','status':'PASS','unit_id':uid,'producer_receipt':spec['producer_receipt'],'audit_source_sha256':src,'probability_paths':2,'probability_max_abs':maxp,'worst_probability_coordinates':worst,'metric_max_abs':maxpoint,'bootstrap_draw_max_abs':maxdraw,'interval_max_abs':maxci,'scaler_mean_max_abs':mean_error,'scaler_variance_max_abs':var_error,'fold_sha256':sha(fp),'fold_count':5,'selected_C':selected,'producer_retry_count':retries,'producer_optimizer_fits':16+retries,'new_production_fits':0,'distribution_checks':tested,'attempted_distribution_values':sum(e['attempted'] for e in tested),'valid_distribution_values':sum(e['valid'] for e in tested),'invalid_distribution_values':sum(e['invalid'] for e in tested),'independent_point_values':pointvalues,'reference_distribution_receipts':refreceipts,'rows':512,'groups':len(np.unique(dev['groups'])),'class_order':classes.tolist(),'sampled_refit_required':spec['sampled_refit_required'],'sampled_refit_executed_here':False,'wall_seconds':time.monotonic()-t,'CPU_process_seconds':time.process_time()-cpu,'peak_RSS_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(tmp/'NUMERICAL_AUDIT.json',audit_record);seal(tmp,root,{'status':'PASS','identity':identity});return {k:audit_record[k] for k in ['status','unit_id','probability_max_abs','metric_max_abs','bootstrap_draw_max_abs','interval_max_abs','wall_seconds']}
  except BaseException as exc:
   failure={'status':'FAILED','unit_id':uid,'reason':str(exc),'traceback':traceback.format_exc(),'audit_source_sha256':src};put(tmp/'FAILED.json',failure);q=A/'quarantine/failed-audits'/uid;q=q.with_name(q.name+'-'+uuid.uuid4().hex);q.parent.mkdir(parents=True,exist_ok=True);os.replace(tmp,q);return failure
def main(args):
 require(args.stage=='A08','Wrong stage');source_check();require(read(C/'IMPLEMENTATION_VALIDATION.json')['status']=='PASS','Synthetic qualification required');ids=args.unit or [u['unit_id'] for u in read(C/'A08_EXECUTION_MANIFEST.json')['audit_units'] if u['candidate']==args.candidate and u['task']==args.task];require(ids and len(ids)==len(set(ids)),'Empty/duplicate queue')
 for uid in ids:unit_spec(uid)
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 with Lock(A/'locks/audit-pipeline.lock'):
  with threadpool_limits(limits=4),concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
   for result in pool.map(audit,ids):print(json.dumps(result),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['A08'],required=True);p.add_argument('--candidate',choices=['R4','R6']);p.add_argument('--task',choices=TASKS);p.add_argument('--unit',action='append');main(p.parse_args())
