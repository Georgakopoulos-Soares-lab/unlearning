from pathlib import Path
import os,json,hashlib,itertools
import numpy as np
import joblib,sklearn
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from scipy.special import expit,softmax
from ops import C,A,save,now
assert sklearn.__version__=='1.7.2'
root=A/'restored-minimum/historical-archive-001';records=json.loads((A/'historical-runtime-metadata-2.json').read_text())['references'];z=np.load(A/'qualification/base/logical8/attempt-001/features_and_lm.npz',allow_pickle=False)
tasks=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];reps=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];expected=set(itertools.product(tasks,reps,[42,17,1234]));assert {(r['task'],r['representation'],r['cv_seed']) for r in records}==expected and len(records)==468
verified={};joins={};out=[]
def artifact(r,k):
 e=r[k];p=root/e['path'].split('multiretain-layers-v1-final-20261110T140836Z/')[1]
 if str(p) not in verified:
  assert p.is_file() and p.stat().st_size==e['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==e['sha256'];verified[str(p)]=e['sha256']
 else:assert verified[str(p)]==e['sha256']
 return p
for r in records:
 key=(r['task'],r['representation'],r['cv_seed']);p=artifact(r,'head');foldp=artifact(r,'fold');ip=artifact(r,'identity');identity=json.loads(ip.read_text());assert r['task'] in identity['tasks'] and r['array_key'] in identity['layers'] and r['cv_seed'] in identity['seeds'];assert identity['packages']['scikit-learn']=='1.7.2'
 join=(r['task'],r['cv_seed'])
 if join not in joins:
  fs=json.loads(foldp.read_text());assert isinstance(fs,list) and len(fs)==(3 if r['task']=='emp_H3' else 5)
  # CV fold IDs are metadata only; no evaluation arrays/examples/predictions opened.
  validations=[];train_universe=None
  for f in fs:
   assert 'train_ids' in f;vk=next(k for k in ['valid_ids','validation_ids','val_ids','test_ids'] if k in f);tr=list(f['train_ids']);va=list(f[vk]);assert len(set(tr))==len(tr) and len(set(va))==len(va) and not set(tr)&set(va)
   u=set(tr)|set(va);assert train_universe is None or u==train_universe;train_universe=u;validations+=va
  assert len(validations)==len(set(validations))==len(train_universe)
  smoke_ids=set(z['ids'][z['task']==r['task']]);assert smoke_ids<=train_universe
  joins[join]={'fold_count':len(fs),'training_cohort_size':len(train_universe),'ordered_validation_ids_sha256':hashlib.sha256(json.dumps(validations,separators=(',',':')).encode()).hexdigest(),'smoke_train_membership':True}
 pipe=joblib.load(p);assert type(pipe) is Pipeline and [type(v) for _,v in pipe.steps]==[StandardScaler,LogisticRegression];s=pipe.steps[0][1];h=pipe.steps[1][1];assert s.with_mean and s.with_std and s.n_features_in_==h.n_features_in_==1920 and h.random_state==42;classes=h.classes_;assert classes.dtype.kind in 'iu' and np.array_equal(classes,np.arange(len(classes))) and len(classes) in [2,3]
 for a in [s.mean_,s.scale_,s.var_,h.coef_,h.intercept_]:assert np.isfinite(a).all()
 assert s.mean_.shape==s.scale_.shape==s.var_.shape==(1920,) and (s.scale_>0).all() and (s.var_>=0).all();assert h.coef_.shape==((1 if len(classes)==2 else len(classes)),1920) and h.intercept_.shape==(h.coef_.shape[0],)
 x=z[r['array_key']][z['task']==r['task']].astype(np.float64);assert x.shape==(2,1920);scaled=(x-s.mean_)/s.scale_;logits=scaled@h.coef_.T+h.intercept_
 if len(classes)==2:
  q=expit(logits[:,0]);manual=np.column_stack([1-q,q])
 else:manual=softmax(logits,axis=1)
 actual=pipe.predict_proba(x);delta=np.abs(actual-manual);assert np.isfinite(actual).all() and actual.shape==(2,len(classes)) and np.max(delta)<=1e-10
 out.append({'task':r['task'],'representation':r['representation'],'array_key':r['array_key'],'cv_seed':r['cv_seed'],'head_sha256':r['head']['sha256'],'fold_sha256':r['fold']['sha256'],'producer_identity_sha256':r['identity']['sha256'],'producer_source_sha256':identity['source_sha256'],'producer_training_source_sha256':identity['training_source_sha256'],'manifest_sha256':identity['manifest_sha256'],'class_order':[int(v) for v in classes],'classifier_random_state':int(h.random_state),'seed_roles':'cv_seed selects folds; saved classifier random_state is42 for every protocol seed','width':1920,'preprocessing':'Exact original saved StandardScaler unchanged, then original saved LogisticRegression','training_cohort_size':joins[join]['training_cohort_size'],'fold_count':joins[join]['fold_count'],'status':'PASS','witness_rows':2,'numerical_witness':'Pipeline versus independent scaler/linear/logistic calculation, original-base frozen TRAIN features only','max_abs_residual':float(delta.max()),'atol':1e-10,'rtol':0,'saved_heldout_probability_replay':'NOT_RUN_NO_HELDOUT_ACCESS','fit_executed':False,'future_policy':'unchanged_reference','scope':'Structural recovery and TRAIN-only compatible application; S04 binds original exact identities'})
 if len(out)%78==0:print('REFERENCE_PROGRESS',len(out),flush=True)
report={'schema':'pod-a-s03-reference-qualification-v1','status':'PASS','qualified_heads':len(out),'unique_verified_input_files':len(verified),'task_count':6,'representations':26,'cv_seeds':[42,17,1234],'qualified_utc':now(),'source_reference_index_sha256':hashlib.sha256((A/'historical-runtime-metadata-2.json').read_bytes()).hexdigest(),'witness_features_sha256':hashlib.sha256((A/'qualification/base/logical8/attempt-001/features_and_lm.npz').read_bytes()).hexdigest(),'maximum_CPU_probability_residual':max(r['max_abs_residual'] for r in out),'references':out,'limitations':['No heldout probability arrays opened; no new fit or heldout evaluation','TRAIN witness is pipeline-versus-independent-formula, not saved-heldout-output equality','R3 bridge and R5 release remain restricted to their original source-bound domains']}
save(C/'SAVED_REFERENCE_QUALIFICATION.json',report);print('PASS_SAVED_REFERENCES',len(out),'maxresidual',report['maximum_CPU_probability_residual'])
