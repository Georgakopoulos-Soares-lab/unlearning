"""Owned A08 read-only input adapter and atomic independent audit output contract."""
from pathlib import Path
import json,hashlib,os,uuid,fcntl,importlib.metadata,sys
VERSIONS={'numpy':'2.5.4','scipy':'1.18.1','scikit-learn':'1.7.2','joblib':'1.5.2','threadpoolctl':'3.8.0'}
assert sys.version_info[:3]==(3,12,3) and {k:importlib.metadata.version(k) for k in VERSIONS}==VERSIONS,'Frozen CPU runtime drift'
import numpy as np
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A08-attempt-002');CFG=json.loads((C/'RUN_CONFIG.json').read_text());A=Path(CFG['artifacts']);R=Path(CFG['root_control']);D=Path(CFG['docs']);A7=A.parent/'A07-attempt-002';A6=A.parent/'A06-attempt-002';D7=D.parent/'A07-attempt-002';D6=D.parent/'A06-attempt-002';C3=R/'attempts/A03-attempt-001';C6=R/'attempts/A06-attempt-002';C7=R/'attempts/A07-attempt-002'
H=Path('/workspace/recovery/POD_A')/R.name/'A03-attempt-001/restored/base_R1/multiretain-layers-v1-final-20261110T140836Z';CONTROL=H.parent.parent/'controls/benign-followup-v1'
TASKS=['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];ALL_TASKS=['emp_H3']+TASKS;LAYERS=['decoder_layer_'+str(i) for i in range(25)]+['final_norm'];SEEDS=[42,17,1234];POLICIES=['independent_refit','fixed_original_base'];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy']
def require(condition,message):
 if not condition:raise ValueError(message)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def ref(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name('.'+p.name+'.'+uuid.uuid4().hex+'.tmp')
 with t.open('w') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def checked(e):
 p=Path(e['path']);require(p.is_file() and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'Dependency hash/size failure: '+str(p));return p
def owned(p,root=A):
 p=Path(p);require(not p.is_symlink() and p.resolve().is_relative_to(Path(root).resolve()) and p.resolve()!=Path(root).resolve(),'Output path escape');return p
class Lock:
 def __init__(self,p):self.path=owned(p)
 def __enter__(self):
  self.path.parent.mkdir(parents=True,exist_ok=True);self.fd=self.path.open('a')
  try:fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BaseException:self.fd.close();raise
  return self
 def __exit__(self,*args):fcntl.flock(self.fd,fcntl.LOCK_UN);self.fd.close()
def file_entries(root):return [{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(Path(root).rglob('*')) if p.is_file() and p.name!='COMPLETE.json']
def validate_members(root,receipt):
 root=Path(root);listed=[]
 for e in receipt['files']:
  p=owned(root/e['path'],root);require(p.is_file() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'Corrupt sealed member: '+str(p));listed.append(e['path'])
 require(len(listed)==len(set(listed)) and set(listed)=={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='COMPLETE.json'},'Extra/missing/duplicate sealed member')
def seal_check(root,identity):
 j=read(Path(root)/'COMPLETE.json');require(j['status']=='PASS' and j['identity']==identity,'Stale or unsuccessful audit seal');validate_members(root,j);return j
def workdir(root):
 root=owned(root);root.parent.mkdir(parents=True,exist_ok=True)
 for p in ([root] if root.exists() else [])+list(root.parent.glob('.'+root.name+'.work-*')):
  require(not (p/'COMPLETE.json').exists(),'Cannot overwrite an existing sealed audit');q=A/'quarantine'/root.relative_to(A);q=q.with_name(q.name+'-'+uuid.uuid4().hex);q.parent.mkdir(parents=True,exist_ok=True);os.replace(p,q)
 p=root.with_name('.'+root.name+'.work-'+uuid.uuid4().hex);p.mkdir();return p
def seal(tmp,root,receipt):
 require(not root.exists(),'Concurrent output publication');receipt={**receipt,'files':file_entries(tmp)};os.replace(tmp,root);put(root/'COMPLETE.json',receipt);return receipt
def source_check():
 require(CFG['stage']=='A08' and CFG['prompt_commit']=='d0d06888c3f4fa7aaa7fa20e0d1f24acde1990ad' and CFG['coverage_plan_sha256']=='06d290bdc76404a8dcfe25da6f057fc78f868364cc1d2e8aa6df77791f0bdfa3','Wrong stage, approved pin or plan');require(read(C/'A08_INPUTS.json')['R5_identity']['model_tensor_content_sha256']=='9cab388a46a873902317ff022ab0b9a43d3e42c8753d3842837f74f5dd474259','Wrong candidate content');require(sha(C/'APPROVAL_RECORD.json')==read(C/'A08_INPUTS.json')['approval_sha256'],'Approval receipt drift')
 require(sha(C/'A08_INPUTS.json')==read(C/'SOURCE_IDENTITY.json')['input_sha256'] and sha(C/'A08_EXECUTION_MANIFEST.json')==read(C/'SOURCE_IDENTITY.json')['manifest_sha256'],'Audit input/manifest identity drift')
 j=read(C/'SOURCE_IDENTITY.json');require(j['status']=='FROZEN','Audit source not qualified')
 for e in j['files']:require(sha(A/'code'/e['path'])==e['sha256'],'Audit source changed after freeze')
 return sha(C/'SOURCE_IDENTITY.json')
def classes_for(task):
 require(task in ALL_TASKS,'Unknown task');return np.array([0,1,2] if task=='gue_splice_reconstructed' else [0,1])
def canonical(key):return 'decoder.final_norm' if key=='final_norm' else key.replace('decoder_layer_','decoder.layers.')
def array_sha(x):return digest({'dtype':str(x.dtype),'shape':list(x.shape),'raw_sha256':hashlib.sha256(x.tobytes()).hexdigest()})
def probabilities_valid(p,y,classes):
 require(np.array_equal(classes,np.unique(y)) and np.array_equal(classes,np.sort(classes)),'Class columns differ');require(p.dtype==np.float64 and p.shape==(len(y),len(classes)) and np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and np.allclose(p.sum(1),1,atol=1e-12,rtol=0),'Invalid probability values or normalization')
def paired(z,meta,classes):
 for k in ['ids','labels','groups','sequence_sha256']:require(np.array_equal(z[k],meta[k]),'Cohort/row order mismatch: '+k)
 require(np.array_equal(z['classes'],classes),'Permuted class columns')
def features(alias,task,split,key):
 require(alias=='R5' and task in TASKS and split in ['train','dev'] and key in LAYERS,'Outside new R5 other-five audit feature scope')
 root=(A6/'h3-cache'/alias/split) if task=='emp_H3' else (A7/'cache'/alias/task/split);receipt=read(root/'COMPLETE.json')
 for name in [key+'.npy','metadata.npz']:
  e=next(e for e in receipt['files'] if e['path']==name);require(sha(root/name)==e['sha256'],'Feature cache member drift')
 x=np.load(root/(key+'.npy'),mmap_mode='r',allow_pickle=False)
 with np.load(root/'metadata.npz',allow_pickle=False) as z:meta={k:z[k] for k in z.files}
 require(x.dtype==np.float32 and x.shape==(len(meta['ids']),1920) and np.isfinite(x).all(),'Wrong feature geometry/dtype/finiteness');return x,meta,ref(root/'COMPLETE.json')
OLD={}
for dep,root in [('base_R1',H),('controls',CONTROL)]:
 for e in read(C3/('PAYLOAD_CHECKSUMS_'+dep+'.json'))['files']:OLD[str(root/e['path'])]=e
def old(p):
 p=Path(p);require(str(p) in OLD,'Unadmitted historical file');return checked({'path':str(p),**{k:OLD[str(p)][k] for k in ['bytes','sha256']}})
def task_root(task):return H/('probes/H3' if task=='emp_H3' else 'probes/other_five')/task
def folds(task,seed,meta):
 p=old(task_root(task)/('folds_seed'+str(seed)+'.json'));return validate_folds(read(p),meta,3 if task=='emp_H3' else 5,classes_for(task)),p
def validate_folds(saved,meta,count,classes):
 ids=meta['ids'];require(len(set(ids))==len(ids),'Repeated row IDs');index={str(v):i for i,v in enumerate(ids)};out=[];whole=set(ids)
 require(len(saved)==count,'Wrong fold count')
 for e in saved:
  tr,va=e['train_ids'],e['validation_ids'];require(len(set(tr))==len(tr) and len(set(va))==len(va) and set(tr).isdisjoint(va) and set(tr)|set(va)==whole,'Frozen fold complement/membership mismatch');a=np.array([index[str(v)] for v in tr]);b=np.array([index[str(v)] for v in va]);require(set(meta['groups'][a]).isdisjoint(meta['groups'][b]),'Fold group leakage');require(np.array_equal(np.unique(meta['labels'][a]),classes) and np.array_equal(np.unique(meta['labels'][b]),classes),'Missing fold class');out.append((a,b))
 require(sorted(np.concatenate([b for a,b in out]).tolist())==list(range(len(ids))),'Validation folds do not partition TRAIN');return out
def draw_weights(task,split,meta):
 p=old(task_root(task)/(split+'_resampling.npz'))
 with np.load(p,allow_pickle=False) as z:
  names,inverse=np.unique(meta['groups'],return_inverse=True);require(np.array_equal(z['ids'],meta['ids']) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse) and int(z['seed'])==20261103,'Draw population/order/seed mismatch');draw=z['group_draws'];require(draw.dtype==np.int32 and draw.shape==(2000,len(names)),'Draw shape/dtype mismatch');require(np.all((draw>=0)&(draw<len(names))),'Saved group index outside population');weights=np.zeros((2000,len(names)),dtype=np.int64)
  for i,d in enumerate(draw):np.add.at(weights[i],d,1)
  return weights[:,inverse],p
def historical_refs(task,key,seed,split,meta):
 p=old(task_root(task)/key/('seed'+str(seed))/(split+'_predictions.npz'))
 with np.load(p,allow_pickle=False) as z:paired(z,meta,classes_for(task));result={n:z[n] for n in ['prob_base_refit','prob_h3_only_refit','prob_h3_only_fixed_base']}
 return result,p
def controls(task,kind,seed,split,meta):
 p=old(CONTROL/'tasks'/task/('4mer' if kind=='kmer4' else kind)/('seed'+str(seed))/(split+'_predictions.npz'))
 with np.load(p,allow_pickle=False) as z:
  for k in ['ids','labels','groups']:require(np.array_equal(z[k],meta[k]),'Control row/label/group mismatch')
  require(np.array_equal(z['classes'],classes_for(task)),'Control classes differ');return z['probabilities'],p
def unit_spec(uid,stage='A08'):
 require(stage=='A08' and CFG['stage']=='A08','Cross-stage dispatch denied');manifest=read(C/'A08_EXECUTION_MANIFEST.json');require(uid.startswith('R5/') and '/emp_H3/' not in uid,'Outside R5 other-five audit scope');found=[u for u in manifest['audit_units'] if u['unit_id']==uid];require(len(found)==1,'Unit outside finite A08 manifest');return found[0]
