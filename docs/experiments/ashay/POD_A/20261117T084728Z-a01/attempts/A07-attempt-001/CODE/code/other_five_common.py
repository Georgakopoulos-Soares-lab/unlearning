"""A07-only immutable inputs, task-aware identities and verified CPU caches."""
from pathlib import Path
import importlib.metadata,sys,json,hashlib,os,uuid,fcntl,contextlib
EXPECTED={'numpy':'2.5.4','scipy':'1.18.1','scikit-learn':'1.7.2','joblib':'1.5.2','threadpoolctl':'3.8.0'}
assert sys.version_info[:3]==(3,12,3), 'Frozen Python changed'
assert {p:importlib.metadata.version(p) for p in EXPECTED}==EXPECTED,'Frozen CPU packages changed'
import numpy as np
from production_contract import read,put,sha,digest,require,owned,UnitLock,LAYERS,validate_rows,verify_chunk
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A07-attempt-001');CFG=read(C/'RUN_CONFIG.json');A=Path(CFG['artifacts']);R=Path(CFG['root_control']);A6=A.parent/'A06-attempt-001';C6=R/'attempts/A06-attempt-001';D=Path(CFG['docs']);D5=D.parent/'A05-attempt-001';D6=D.parent/'A06-attempt-001';C3=R/'attempts/A03-attempt-001'
H=Path('/workspace/recovery/POD_A')/R.name/'A03-attempt-001/restored/base_R1/multiretain-layers-v1-final-20261110T140836Z';CONTROL=H.parent.parent/'controls/benign-followup-v1'
TASKS=['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];SEEDS=[42,17,1234];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy'];POLICIES=['independent_refit','fixed_original_base']
I6=read(C6/'A06_INPUTS.json');OLD_MAP={}
for dep,root in [('base_R1',H),('controls',CONTROL)]:
 for e in read(C3/('PAYLOAD_CHECKSUMS_'+dep+'.json'))['files']:OLD_MAP[str(root/e['path'])]=e
def ref(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def checked_old(p):
 p=Path(p);e=OLD_MAP[str(p)];require(p.is_file() and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'Historical byte identity failed: '+str(p));return p
def check_ref(e):
 p=Path(e['path']);require(p.is_file() and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'Dependency changed: '+str(p));return p
def members(root):return [dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(Path(root).rglob('*')) if p.is_file() and p.name!='COMPLETE.json']
def verify_seal(root,identity=None):
 root=Path(root);j=read(root/'COMPLETE.json');require(j['status'] in ['PASS','COMPLETE_UNVERIFIED'],'Unaccepted seal status')
 if identity is not None:require(j['identity']==identity,'Sealed scientific identity mismatch')
 paths=[]
 for e in j['files']:
  p=owned(root/e['path'],root);require(p.is_file() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'Corrupt sealed cache/unit member: '+str(p));paths.append(e['path'])
 require(len(paths)==len(set(paths)),'Duplicate sealed members');require(set(paths)=={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='COMPLETE.json'},'Unexpected unsealed members');return j
def new_work(root):
 root=owned(root,A);root.parent.mkdir(parents=True,exist_ok=True)
 if root.exists():
  require(not (root/'COMPLETE.json').exists(),'Cannot replace sealed output');q=A/'quarantine'/root.relative_to(A);q=q.with_name(q.name+'-'+uuid.uuid4().hex);q.parent.mkdir(parents=True,exist_ok=True);os.replace(root,q)
 for p in root.parent.glob('.'+root.name+'.work-*'):
  q=A/'quarantine'/root.relative_to(A);q=q.with_name(q.name+'-'+uuid.uuid4().hex);q.parent.mkdir(parents=True,exist_ok=True);os.replace(p,q)
 tmp=root.with_name('.'+root.name+'.work-'+uuid.uuid4().hex);tmp.mkdir();return tmp
def finish(tmp,root,receipt):
 require(not root.exists(),'Another writer published this output');receipt={**receipt,'files':members(tmp)};os.replace(tmp,root);put(root/'COMPLETE.json',receipt);return receipt
def stage_spec(alias,task,key,seed,stage='A07'):
 require(stage=='A07' and CFG['stage']=='A07','Cross-stage dispatch denied');require(alias in ['R4','R6'] and task in TASKS and key in LAYERS and seed in SEEDS,'Unapproved unit');return '/'.join([alias,task,key,'seed'+str(seed)])
def classes_for(task):require(task in TASKS,'Unknown task');return np.array([0,1,2] if task=='gue_splice_reconstructed' else [0,1])
def validate_prob(p,y,classes):
 require(np.array_equal(classes,np.unique(y)),'Unsorted or mismatched class columns');require(p.dtype==np.float64 and p.shape==(len(y),len(classes)) and np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and np.allclose(p.sum(1),1,atol=1e-12,rtol=0),'Invalid probability support')
def pair(z,meta,classes):
 for n in ['ids','labels','groups','sequence_sha256']:require(np.array_equal(z[n],meta[n]),'Pairing/order differs: '+n)
 require(np.array_equal(z['classes'],classes),'Class column mismatch')
def metadata(alias,task,split):
 with np.load(A/'cache'/alias/task/split/'metadata.npz',allow_pickle=False) as z:return {k:z[k] for k in z.files}
def features(alias,task,split,key,verify=True):
 root=A/'cache'/alias/task/split;j=read(root/'COMPLETE.json');p=root/(key+'.npy')
 if verify:
  for name in [key+'.npy','metadata.npz']:
   e=next(e for e in j['files'] if e['path']==name);require(sha(root/name)==e['sha256'],'Changed CPU feature cache')
 x=np.load(p,mmap_mode='r',allow_pickle=False);require(x.dtype==np.float32 and x.shape==((1024 if split=='train' else 512),1920) and np.isfinite(x).all(),'Feature shape/dtype/nonfinite');return x
def folds_for(task,seed,meta):
 p=checked_old(H/'probes/other_five'/task/('folds_seed'+str(seed)+'.json'));folds=validate_folds(read(p),meta,5,classes_for(task));return folds,p
def validate_folds(saved,meta,count,classes):
 ids=meta['ids'];require(len(set(ids))==len(ids),'Duplicate TRAIN IDs');index={v:i for i,v in enumerate(ids)};out=[];allids=set(ids)
 require(len(saved)==count,'Wrong fold count')
 for f in saved:
  tr,va=f['train_ids'],f['validation_ids'];require(len(set(tr))==len(tr) and len(set(va))==len(va) and set(tr).isdisjoint(va) and set(tr)|set(va)==allids,'Fold membership/complement differs')
  a,b=np.array([index[v] for v in tr]),np.array([index[v] for v in va]);require(set(meta['groups'][a]).isdisjoint(meta['groups'][b]),'Fold group leakage');require(np.array_equal(np.unique(meta['labels'][a]),classes) and np.array_equal(np.unique(meta['labels'][b]),classes),'Missing fold class');out.append((a,b))
 require(sorted(np.concatenate([b for a,b in out]).tolist())==list(range(len(ids))),'Validation folds do not partition TRAIN exactly once');return out
def resampling(task,meta):
 p=checked_old(H/'probes/other_five'/task/'dev_resampling.npz')
 with np.load(p,allow_pickle=False) as z:
  names,inverse=np.unique(meta['groups'],return_inverse=True);require(np.array_equal(z['ids'],meta['ids']) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse) and int(z['seed'])==20261103,'Frozen draw identity mismatch');draw=z['group_draws'];require(draw.shape==(2000,len(names)) and draw.dtype==np.int32 and np.all((draw>=0)&(draw<len(names))),'Bad historical draws');weights=np.stack([np.bincount(x,minlength=len(names)) for x in draw])[:,inverse];return weights,p
def references(task,key,seed,meta):
 p=checked_old(H/'probes/other_five'/task/key/('seed'+str(seed))/'dev_predictions.npz');classes=classes_for(task)
 with np.load(p,allow_pickle=False) as z:
  pair(z,meta,classes);result={n:z[n] for n in ['prob_base_refit','prob_h3_only_refit','prob_h3_only_fixed_base']}
 for v in result.values():validate_prob(v,meta['labels'],classes)
 return result,p
def control_predictions(task,control,seed,meta):
 p=checked_old(CONTROL/'tasks'/task/('4mer' if control=='kmer4' else control)/('seed'+str(seed))/'dev_predictions.npz')
 with np.load(p,allow_pickle=False) as z:
  for n in ['ids','labels','groups']:require(np.array_equal(z[n],meta[n]),'Control order differs')
  require(np.array_equal(z['classes'],classes_for(task)),'Control class columns differ');v=z['probabilities'];validate_prob(v,meta['labels'],classes_for(task));return v,p
def array_sha(x):return digest({'dtype':str(x.dtype),'shape':list(x.shape),'raw_sha256':hashlib.sha256(x.tobytes()).hexdigest()})
def source_check():
 j=read(C/'CPU_SOURCE_IDENTITY.json')
 for e in j['files']:require(sha(A/'code'/e['path'])==e['sha256'],'A07 CPU source changed after freeze')
 return sha(C/'CPU_SOURCE_IDENTITY.json')
