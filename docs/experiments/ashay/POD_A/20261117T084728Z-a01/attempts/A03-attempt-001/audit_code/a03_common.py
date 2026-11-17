"""Owned read-only A03 recovery helpers. No model loading, inference, or fitting."""
from pathlib import Path
import argparse,collections,csv,datetime,hashlib,json,os,time
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from historical_independent_math import reconstruct,metrics
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']
LAYERS=[f'decoder_layer_{i}' for i in range(25)]+['final_norm']
SEEDS=[42,17,1234];ANCHORS=['decoder_layer_16','final_norm'];NAMES=['auroc','accuracy','balanced_accuracy','average_precision','classification_cross_entropy']
HASHES={'H3':'de2c348126fa84771ceeff38225703231848ac860f8b59a3ed41d9eb0b3f0938','other_five':'a270dd76f1a007b7685c012ca2c2a5bdcdbf67da1122f12c81caf292ae9c4126'}
SMOKE_SHA='42d64d32b77e946bc962c32d2b801e485d41a095221af49a492079ff0f76fd30'
def forbidden(*args,**kwargs):raise RuntimeError('A03 forbids fitting')
LogisticRegression.fit=forbidden;StandardScaler.fit=forbidden

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def jread(p):return json.loads(Path(p).read_text())
def put(p,v):
 p=Path(p);p.parent.mkdir(exist_ok=True,parents=True);t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');os.replace(t,p)
def write_csv(p,rows):
 assert rows
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def seqsha(row):return row.get('sequence_sha256',row.get('scored_prefix_sha256',hashlib.sha256(row['sequence'].encode()).hexdigest()))
def group(task):return 'H3' if task=='emp_H3' else 'other_five'
def splits(task):return ['dev','test'] if task=='emp_H3' else ['dev']
def hook(k):return 'decoder.final_norm' if k=='final_norm' else 'decoder.layers.'+k.rsplit('_',1)[1]
def ensure(condition,message):
 if not condition:raise ValueError(message)
def identity_digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
def maxerr(a,b):
 ensure(np.shape(a)==np.shape(b),'Shape differs in residual')
 ensure(np.isfinite(a).all() and np.isfinite(b).all(),'Nonfinite numerical residual input')
 return float(np.max(np.abs(a-b)))

class Context:
 def __init__(self,control):
  self.c=Path(control).resolve();self.cfg=jread(self.c/'RUN_CONFIG.json');self.a=Path(self.cfg['artifacts']);self.rec=Path(self.cfg['recovery']);self.out=self.a/'audits';self.out.mkdir(exist_ok=True);self.cache=self.a/'audit-cache';self.cache.mkdir(exist_ok=True)
  restore=jread(self.c/'RESTORE_VALIDATION.json');ensure(len(restore['dependencies'])==4 and all(d['status']=='VERIFIED' for d in restore['dependencies']),'All four required archives must pass before audit')
  self.roots={d['dependency_id']:Path(d['payload_root']) for d in restore['dependencies']};self.mapping=jread(self.c/'PATH_TRANSLATION.json')['mappings'];self.lookup={}
  for key,root in self.roots.items():
   manifest=jread(self.c/f'PAYLOAD_CHECKSUMS_{key}.json')
   for e in manifest['files']:self.lookup[root/e['path']]=e
   self.lookup[root/'CHECKSUMS.sha256']={'sha256':manifest['checksum_file']['sha256'],'bytes':(root/'CHECKSUMS.sha256').stat().st_size}
  self.started=time.monotonic();self.cpu=time.process_time()
 def resolve(self,p):
  p=Path(p)
  if p in self.lookup:return p
  for m in sorted(self.mapping,key=lambda m:len(m['original_root']),reverse=True):
   old=Path(m['original_root'])
   if p.is_relative_to(old):
    target=Path(m['restored_root'])/p.relative_to(old);ensure(target.is_relative_to(Path(m['restored_root'])),'Escaping mapping');return target
  raise ValueError('Unmapped historical dependency: '+str(p))
 def verified(self,p,expected=None,size=None):
  p=self.resolve(p);ensure(p in self.lookup,'Not covered by complete all-byte restore: '+str(p));entry=self.lookup[p]
  ensure(p.is_file() and not p.is_symlink(),'Nonregular audit dependency')
  ensure(p.stat().st_size==entry['bytes'],'Payload size changed since all-byte validation')
  if expected:ensure(entry['sha256']==expected,'Historical receipt conflicts with payload manifest: '+str(p))
  if size is not None:ensure(entry['bytes']==size,'Receipt byte size differs')
  return p
 def receipt(self,p,expected=None):
  p=self.verified(p,expected);v=jread(p);ensure(v['status'] in ['COMPLETE','NEW'],'Unsealed unit')
  if isinstance(v['files'],list):
   for e in v['files']:self.verified(e['path'],e['sha256'],e['bytes'])
  else:
   for name,h in v['files'].items():self.verified(p.parent/name,h)
  return v
 def ref(self,p):
  p=self.verified(p);return {'path':str(p),'sha256':self.lookup[p]['sha256'],'bytes':self.lookup[p]['bytes']}
 def rows(self,g):
  p=self.verified(self.roots['base_R1']/'manifests'/f'{g}.jsonl',HASHES[g]);ensure(sha(p)==HASHES[g],'Raw frozen cohort hash mismatch');return [json.loads(l) for l in p.read_text().splitlines()]
 def done(self,name,obj):
  obj={'schema':'pod-a-a03-'+name.lower().replace('_','-')+'-v1',**obj,'source_sha256':sha(Path(__file__).with_name('a03_'+self.family+'.py')),'wall_seconds':time.monotonic()-self.started,'cpu_process_seconds':time.process_time()-self.cpu};put(self.out/(name+'.json'),obj);put(self.c/(name+'.json'),obj)
 def log(self,event,**kw):
  row={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'family':self.family,'event':event,**kw};print(json.dumps(row),flush=True)
  with (self.c/'AUDIT_EVENTS.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')

def validate_model(model,classes,width):
 scaler,head=model[0],model[-1]
 ensure(isinstance(scaler,StandardScaler) and isinstance(head,LogisticRegression),'Unexpected CPU estimator class')
 ensure(np.array_equal(head.classes_,classes),'Estimator numeric class order mismatch')
 ensure(scaler.mean_.shape==scaler.var_.shape==scaler.scale_.shape==(width,),'Scaler shape mismatch')
 ensure(head.coef_.shape==((1 if len(classes)==2 else len(classes)),width),'Head coefficient shape mismatch')
 ensure(head.intercept_.shape==(head.coef_.shape[0],),'Intercept shape mismatch')
 ensure(all(np.isfinite(x).all() for x in [scaler.mean_,scaler.var_,scaler.scale_,head.coef_,head.intercept_]),'Nonfinite estimator')
 ensure(np.all(scaler.var_>=0) and np.all(scaler.scale_>0),'Invalid scaling statistics')
 ensure(head.solver=='lbfgs' and head.class_weight=='balanced' and head.penalty=='l2' and head.tol==1e-4,'Estimator protocol mismatch')
 ensure(head.random_state==42 and head.max_iter in [2000,10000],'Optimizer seed/iterations changed')
 ensure(head.n_iter_.max()<head.max_iter,'Unresolved optimizer limit')
 ensure(scaler.with_mean and scaler.with_std,'Unexpected scaler mode')
 return scaler,head

def selection(candidates,fold_count,selected,convergence):
 ensure([x['C'] for x in candidates]==[.1,1.,10.],'C grid changed')
 for c in candidates:
  ensure(len(c['scores'])==fold_count and len(c['convergence'])==fold_count,'Fold selection accounting')
  ensure(np.isfinite(c['scores']).all() and abs(np.mean(c['scores'])-c['mean_auroc'])<=1e-14,'CV mean mismatch')
  ensure(all(not logs[-1]['warnings'] for logs in c['convergence']),'Unresolved CV warning')
  ensure(all(1<=len(logs)<=2 for logs in c['convergence']),'CV retry accounting')
 expected=sorted(candidates,key=lambda c:(-c['mean_auroc'],c['C']))[0]['C'];ensure(expected==selected,'Training-only smaller-C tie rule mismatch');ensure(not convergence[-1]['warnings'],'Unresolved refit warnings');return expected

if __name__=='__main__':raise SystemExit('Import helper only; choose an explicit A03 audit family')
