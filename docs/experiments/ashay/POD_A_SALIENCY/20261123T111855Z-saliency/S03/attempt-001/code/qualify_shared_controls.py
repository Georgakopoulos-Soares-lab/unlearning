from pathlib import Path
import os,json,hashlib,itertools
import numpy as np,joblib
from scipy.special import expit,softmax
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from ops import C,A,save,now
root=A/'restored-minimum/historical-archive-002';index=json.loads((C/'HISTORICAL_CONTROL_REUSE_INDEX.json').read_text());smoke=[json.loads(l) for l in (A/'restored-minimum/historical-archive-005/a04-training-only/training_smoke_manifest.jsonl').read_text().splitlines()];rows=[]
for r in index['units']:
 p=root/r['head']['path'].split('/controls/')[1];assert p.stat().st_size==r['head']['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['head']['sha256'];receipt=root/r['receipt']['path'].split('/controls/')[1];assert hashlib.sha256(receipt.read_bytes()).hexdigest()==r['receipt']['sha256'];identity=json.loads(receipt.read_text());assert identity['task']==r['task'] and identity['control']==r['control'] and identity['seed']==r['seed'] and identity['files']['model.joblib']==r['head']['sha256'];pipe=joblib.load(p);assert type(pipe) is Pipeline and [type(v) for _,v in pipe.steps]==[StandardScaler,LogisticRegression];s,h=[v for _,v in pipe.steps];width=r['feature_width'];assert s.n_features_in_==h.n_features_in_==width;assert h.classes_.dtype.kind in 'iu' and np.array_equal(h.classes_,np.arange(len(h.classes_)))
 for x in [s.mean_,s.scale_,s.var_,h.coef_,h.intercept_]:assert np.isfinite(x).all()
 assert (s.scale_>0).all();xs=[]
 for witness in [v for v in smoke if v['task']==r['task']]:
  seq=witness['sequence'];assert witness['split']=='train';v=np.zeros(width,dtype=np.float64)
  if r['control']=='composition':
   for i,k in enumerate('ACGT'):v[i]=seq.count(k)
  elif r['control']=='4mer':
   pos={''.join(x):i for i,x in enumerate(itertools.product('ACGT',repeat=4))}
   for i in range(len(seq)-3):
    k=seq[i:i+4]
    if k in pos:v[pos[k]]+=1
  else:raise ValueError('Unknown control')
  assert v.sum()>0;v/=v.sum();xs.append(v)
 x=np.array(xs);assert x.shape==(2,width);actual=pipe.predict_proba(x);logits=((x-s.mean_)/s.scale_)@h.coef_.T+h.intercept_
 if len(h.classes_)==2:
  q=expit(logits[:,0]);manual=np.column_stack([1-q,q])
 else:manual=softmax(logits,axis=1)
 delta=float(np.max(np.abs(actual-manual)));assert delta<=1e-10
 rows.append({'task':r['task'],'control':r['control'],'cv_seed':r['seed'],'head_sha256':r['head']['sha256'],'receipt_sha256':r['receipt']['sha256'],'feature_width':width,'class_order':[int(v) for v in h.classes_],'classifier_random_state':int(h.random_state),'feature_definition':r['feature_definition'],'status':'PASS','max_CPU_formula_probability_residual':delta,'atol':1e-10,'rtol':0,'witness_rows':2,'original_models_unchanged':True,'fit_executed':False,'heldout_predictions_opened':False,'historical_source_bound_saved_output_receipts_reused':True,'current_saved_heldout_replay_performed':False})
assert len(rows)==36 and len({(r['task'],r['control'],r['cv_seed']) for r in rows})==36
save(C/'SHARED_CONTROL_QUALIFICATION.json',{'schema':'s03-shared-control-recovery-v1','status':'PASS','control_units':36,'controls_shared_across_layers_and_candidates':True,'controls':rows,'source_index_sha256':hashlib.sha256((C/'HISTORICAL_CONTROL_REUSE_INDEX.json').read_bytes()).hexdigest(),'scope':'Exact unchanged saved models, structural recovery and TRAIN-only formula check; historical source-bound output audit reused, no new heldout replay','verified_utc':now()});print('SHARED_CONTROLS_PASS',len(rows),max(r['max_CPU_formula_probability_residual'] for r in rows))
