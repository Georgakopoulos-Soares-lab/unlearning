"""NON_PRODUCTION: two predetermined TRAIN-only tasks, one layer/seed; no held-out reads."""
import sys,os,time,warnings,argparse,json,hashlib,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'stage_drivers'))
from common import *
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
def train(x,y,c):
 attempts=[]
 for limit in [2000,10000]:
  model=make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',tol=1e-4,max_iter=limit,random_state=42));t=time.perf_counter()
  with warnings.catch_warnings(record=True) as caught:warnings.simplefilter('always');model.fit(x,y)
  attempts.append({'max_iter':limit,'n_iter':model[-1].n_iter_.tolist(),'seconds':time.perf_counter()-t,'warnings':[str(w.message) for w in caught]})
  if not any(issubclass(w.category,ConvergenceWarning) for w in caught):return model,attempts
 raise RuntimeError('Unresolved TRAIN-only convergence failure')
def main():
 assert read(C/'INPUT_VERIFICATION.json')['status']=='PASS'
 out=A/'NON_PRODUCTION/cpu-calibration-001';assert not out.exists();out.mkdir(parents=True)
 root=Path('/workspace/recovery/POD_A/20261117T084728Z-a01/A03-attempt-001/restored/base_R1/multiretain-layers-v1-final-20261110T140836Z');manifest=root/'manifests/other_five.jsonl';assert sha(manifest)=='a270dd76f1a007b7685c012ca2c2a5bdcdbf67da1122f12c81caf292ae9c4126'
 # Stream opaque non-training lines without decoding their sequence/label fields.
 rows={}
 for i,line in enumerate(manifest.open()):
  if '"split": "train"' in line or '"split":"train"' in line:
   r=json.loads(line)
   if r['task'] in ['gue_tf_0','gue_splice_reconstructed']:rows[i]=r
 assert len(rows)==2048 and all(r['split']=='train' for r in rows.values())
 receipt=read(root/'features/other_five/base/FEATURE_UNIT_COMPLETE.json');lookup={Path(e['path']).name:e for e in receipt['files']};results=[]
 for task in ['gue_tf_0','gue_splice_reconstructed']:
  selected={i:r for i,r in rows.items() if r['task']==task};features=[];ordered=[];chunks=[];t=time.perf_counter()
  for start in sorted({i//8*8 for i in selected}):
   indices=list(range(start,start+8));assert all(i in selected for i in indices),'Mixed held-out chunk forbidden'
   p=root/'features/other_five/base'/f'chunk_{start:06d}.npz';e=lookup[p.name];assert sha(p)==e['sha256'];chunks.append(ref(p))
   with np.load(p,allow_pickle=False) as z:
    rr=[selected[i] for i in indices];assert z['ids'].tolist()==[r['id'] for r in rr] and z['split'].tolist()==['train']*8 and z['task'].tolist()==[task]*8
    assert z['labels'].tolist()==[r['label'] for r in rr] and z['groups'].tolist()==[r['exact_rc_group'] for r in rr]
    x=z['final_norm'];assert x.shape==(8,1920) and x.dtype==np.float32 and np.isfinite(x).all();features.append(x);ordered+=rr
  x=np.concatenate(features);y=np.array([r['label'] for r in ordered]);ids=[r['id'] for r in ordered];groups=np.array([r['exact_rc_group'] for r in ordered]);io=time.perf_counter()-t;assert len(ids)==1024
  folds_path=root/'probes/other_five'/task/'folds_seed42.json';folds=read(folds_path);ix={v:i for i,v in enumerate(ids)};frozen=[(np.array([ix[v] for v in f['train_ids']]),np.array([ix[v] for v in f['validation_ids']])) for f in folds];generated=list(StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=42).split(np.zeros(len(y)),y,groups));assert all(np.array_equal(a,c) and np.array_equal(b,d) for (a,b),(c,d) in zip(frozen,generated))
  t=time.perf_counter();cpu=time.process_time();candidates=[];all_attempts=[]
  with threadpool_limits(limits=4):
   for c in [.1,1.,10.]:
    scores=[]
    for a,b in frozen:
     assert not set(groups[a])&set(groups[b]);model,attempts=train(x[a],y[a],c);assert not attempts[-1]['warnings'];p=model.predict_proba(x[b]);scores.append(float(roc_auc_score(y[b],p[:,1])) if len(model.classes_)==2 else float(roc_auc_score(y[b],p,multi_class='ovr',average='macro',labels=model.classes_)));all_attempts.append(attempts)
    candidates.append({'C':c,'fold_scores':scores,'mean_auroc':float(np.mean(scores))})
   chosen=max(candidates,key=lambda r:(r['mean_auroc'],-r['C']))['C'];model,attempts=train(x,y,chosen);assert not attempts[-1]['warnings'];all_attempts.append(attempts)
  result={'task':task,'kind':'NON_PRODUCTION_TRAIN_ONLY_CALIBRATION','rows':1024,'checkpoint':'historical base','layer':'decoder.final_norm','seed':42,'CPU_wall_seconds':time.perf_counter()-t,'CPU_process_seconds':time.process_time()-cpu,'hash_read_decompress_seconds':io,'feature_bytes':x.nbytes,'fold_ref':ref(folds_path),'chunk_refs':chunks,'ordered_ids_sha256':hashlib.sha256(json.dumps(ids).encode()).hexdigest(),'solver_fits':sum(len(a) for a in all_attempts),'nominal_solver_fits':16,'candidates':candidates,'selected_C':chosen,'attempts':all_attempts,'new_production_heads':0,'heldout_rows_read':0,'model_saved':False}
  put(out/(task+'.json'),result);np.savez_compressed(out/(task+'_TRAIN_ONLY.npz'),features=x,labels=y,ids=np.array(ids),groups=groups);results.append(result);print(json.dumps({'task':task,'CPU_wall_seconds':result['CPU_wall_seconds'],'status':'PASS'}),flush=True)
 summary={'status':'PASS','scope':'2 predetermined TRAIN-only tasks, final_norm seed42; established grouped folds; no GPU/new production extraction or released performance','source_sha256':sha(__file__),'tasks':results,'new_calibration_final_fits':2,'new_production_heads':0,'heldout_rows_read':0,'peak_RSS_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'threads':4,'completed_utc':now()};put(C/'CPU_CALIBRATION.json',summary)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-training-calibration',action='store_true',required=True);p.parse_args();main()
