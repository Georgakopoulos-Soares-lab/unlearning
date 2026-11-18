"""Exactly sixty prospective independent audit refits; never replace production heads."""
from audit_common import *
import argparse,concurrent.futures,time,warnings,resource,traceback,datetime
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import roc_auc_score
from threadpoolctl import threadpool_limits
from independent_math import reconstruct,metrics
from audit_units import residual
def fit_independent(x,y,c,context):
 attempts=[]
 for limit in [2000,10000]:
  scaler=StandardScaler();head=LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',tol=1e-4,max_iter=limit,random_state=42);t=time.monotonic();cpu=time.process_time()
  with warnings.catch_warnings(record=True) as caught:
   warnings.simplefilter('always');scaled=scaler.fit_transform(x);head.fit(scaled,y)
  convergence=[w for w in caught if issubclass(w.category,ConvergenceWarning)];other=[w for w in caught if not issubclass(w.category,ConvergenceWarning)];attempts.append({'context':context,'C':c,'max_iter':limit,'n_iter':head.n_iter_.tolist(),'converged':not convergence,'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught],'wall_seconds':time.monotonic()-t,'CPU_seconds':time.process_time()-cpu});require(not other,'Unclassified independent-refit warning')
  if not convergence:return make_pipeline(scaler,head),attempts
 raise ValueError('FAILED_CONVERGENCE: '+json.dumps(attempts))
def refit(uid):
 spec=unit_spec(uid);require(spec['sampled_refit_required'],'Outside prospective60unit refitpanel');source=source_check();auditroot=A/'audits'/uid;require(read(auditroot/'COMPLETE.json')['status']=='PASS','All-unit audit prerequisite failed');alias,task,key,ss=uid.split('/');seed=int(ss[4:]);root=A/'refits'/uid;identity={'stage':'A08','unit_id':uid,'source_sha256':source,'producer':spec['producer_receipt'],'audit_receipt_sha256':sha(auditroot/'COMPLETE.json'),'panel_manifest_sha256':sha(C/'A08_EXECUTION_MANIFEST.json')}
 with Lock(A/'locks/refit'/(uid+'.lock')):
  if (root/'COMPLETE.json').exists():seal_check(root,identity);return read(root/'AUDIT_REFIT.json')
  tmp=workdir(root);t=time.monotonic();cpu=time.process_time()
  try:
   x,tr,tc=features(alias,task,'train',key);xx,dev,dc=features(alias,task,'dev',key);classorder=classes_for(task);frozen,fp=folds(task,seed,tr);producer=Path(spec['producer_receipt']['path']).parent;original_cv=read(producer/'CV.json');traces=[];cv_error=0.
   with threadpool_limits(limits=4):
    for i,c in enumerate([.1,1.,10.]):
     scores=[];attempts=[]
     for fold,(a,b) in enumerate(frozen):
      model,at=fit_independent(x[a],tr['labels'][a],c,'C='+str(c)+'/fold'+str(fold));p=reconstruct(model,x[b]);score=roc_auc_score(tr['labels'][b],p[:,1]) if len(classorder)==2 else roc_auc_score(tr['labels'][b],p,labels=classorder,multi_class='ovr',average='macro');scores.append(float(score));attempts.append(at);put(tmp/'CV_IN_PROGRESS.json',{'completed':traces,'current_C':c,'scores':scores,'attempts':attempts})
     cv_error=max(cv_error,residual(scores,original_cv[i]['fold_aurocs']));traces.append({'C':c,'fold_aurocs':scores,'mean_auroc':float(np.mean(scores)),'convergence':attempts});put(tmp/'CV.json',traces)
    selected=max(traces,key=lambda z:(z['mean_auroc'],-z['C']))['C'];original=read(producer/'FINAL_FIT.json');require(selected==original['selected_C'],'Independent refit Cselection mismatch');model,at=fit_independent(x,tr['labels'],selected,'FINAL_ALL_TRAIN');joblib.dump(model,tmp/'audit_head.joblib');p=reconstruct(model,xx);np.savez_compressed(tmp/'audit_dev_probabilities.npz',ids=dev['ids'],labels=dev['labels'],groups=dev['groups'],classes=classorder,probabilities=p)
   with np.load(producer/'dev_predictions.npz',allow_pickle=False) as z:paired(z,dev,classorder);maxp=residual(p,z['independent_refit'],atol=1e-10)
   point,valid=metrics(dev['labels'],p,classorder,np.ones((1,len(p))));require(valid.all(),'Independent refit point class incompleteness');rows=read(producer/'RESULTS.json')['metrics'];maxm=max(residual([point[r['metric']][0]],[r['estimate']]) for r in rows if r['policy']=='independent_refit');prod=joblib.load(producer/'head.joblib');coeferr=float(np.max(np.abs(model[-1].coef_-prod[-1].coef_)));intercepterr=float(np.max(np.abs(model[-1].intercept_-prod[-1].intercept_)));actual=sum(len(attempts) for c in traces for attempts in c['convergence'])+len(at)
   record={'schema':'pod-a-a08-sampled-refit-v1','status':'PASS','unit_id':uid,'selected_C':selected,'fold_sha256':sha(fp),'CV_score_max_abs':cv_error,'probability_max_abs':maxp,'metric_max_abs':maxm,'coefficient_max_abs_diagnostic':coeferr,'intercept_max_abs_diagnostic':intercepterr,'planned_optimizer_fits':16,'actual_optimizer_fits':actual,'convergence_retries':actual-16,'final_attempts':at,'source_sha256':source,'producer_receipt':spec['producer_receipt'],'new_production_heads':0,'production_replaced':False,'wall_seconds':time.monotonic()-t,'CPU_seconds':time.process_time()-cpu,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(tmp/'AUDIT_REFIT.json',record);seal(tmp,root,{'status':'PASS','identity':identity});return record
  except Exception as exc:
   failure={'status':'FAILED','unit_id':uid,'reason':str(exc),'traceback':traceback.format_exc()};put(tmp/'FAILED.json',failure);q=A/'quarantine/refits'/uid;q=q.with_name(q.name+'-'+uuid.uuid4().hex);q.parent.mkdir(parents=True,exist_ok=True);os.replace(tmp,q);return failure
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',choices=['A08'],required=True);p.add_argument('--candidate',choices=['R4','R6'],required=True);v=p.parse_args();source_check();manifest=read(C/'A08_EXECUTION_MANIFEST.json');ids=[u['unit_id'] for u in manifest['audit_units'] if u['candidate']==v.candidate and u['sampled_refit_required']];require(len(ids)==30,'Panel cardinality mismatch');resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 with Lock(A/'locks/pipeline.lock'):
  with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
   for result in pool.map(refit,ids):print(json.dumps(result),flush=True)
