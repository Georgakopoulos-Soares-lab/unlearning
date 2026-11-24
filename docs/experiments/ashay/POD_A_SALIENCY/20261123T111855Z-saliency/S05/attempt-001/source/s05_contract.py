"""S05 strict scope, identities, atomic seals and finite H3 input contracts. No model/import side effects."""
from pathlib import Path,PurePosixPath
import os,json,hashlib,fcntl,datetime,re,contextlib
HOOKS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];KEYS=[f'decoder_layer_{i}' for i in range(25)]+['final_norm'];SEEDS=[42,17,1234];POLICIES=['independent_refit','fixed_original_base'];METRICS=['AUROC','AP','accuracy','balanced_accuracy','cross_entropy'];_VALIDATED_FILES={}
def need(x,msg):
 if not x:raise ValueError(msg)
def load(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp-'+str(os.getpid()));b=(json.dumps(x,indent=2,allow_nan=False)+'\n').encode()
 with tmp.open('wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def process_identity():return {'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
def file_stat(p):
 s=Path(p).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
def safe_rel(n):
 p=PurePosixPath(n);need(bool(n) and not p.is_absolute() and '..' not in p.parts and '\\' not in n,'Unsafe artifact member');return n
@contextlib.contextmanager
def exclusive(p):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:yield
  finally:fcntl.flock(f,fcntl.LOCK_UN)
def source_verify(c,role):
 x=load(Path(c)/'SOURCE_IDENTITY.json');need(sha(Path(c)/'RUN_CONFIG.json')==x['configuration_sha256'],'Frozen execution configuration changed');root=Path(x['code_root'])
 for v in x['files']:need(sha(root/v['path'])==v['sha256'],'Executed source changed; scoped new identity required')
 need(role in x['roles'],'Unknown execution source role');return x['roles'][role]['source_identity_sha256']
def scope(cfg,alias,task='emp_H3',splits=('train','dev'),representation=None,seed=None,policies=None):
 need(cfg['precision_contract']=={'feature_dtype':'float32','backbone':'qualified_BF16_FP32','attention_backend':'TE_unfused'},'Unsupported precision/backend');need(cfg['phase']=='S05' and cfg['task']=='emp_H3' and task=='emp_H3','Other-task/stage dispatch prohibited before data/model opening');need(list(splits) and set(splits)<={'train','dev'},'Test/unknown split rejected before data/model opening');need(cfg['allowed_splits']==['train','dev'],'Split allowlist changed');need(cfg['probe_policies']==POLICIES and cfg['seeds']==SEEDS,'Frozen policy/CVseed contract changed');v=next((v for v in cfg['candidates'] if v['alias']==alias),None);need(v is not None and v['measurement_eligible'],'Unknown candidate');need(v['model_tensor_content_sha256'] and v['candidate_id'],'Missing exact content identity');need(cfg['representations']==HOOKS and cfg['width']==1920 and cfg['physical_batch']==8,'Unsupported hook/layer16/precision/batch geometry');need(representation is None or representation in HOOKS,'Unqualified representation');need(seed is None or seed in SEEDS,'Unknown CVseed');need(policies is None or list(policies)==POLICIES,'Third-policy/reference substitution prohibited');return v
def readiness(c,alias,role='producer'):
 c=Path(c);cfg=load(c/'RUN_CONFIG.json');v=scope(cfg,alias);g=load(c/'READINESS.json');need(all(g['gates'][k]['status']=='PASS' for k in ['R1','R2','R3','R4']),'Readiness gates incomplete; no scientific dispatch');need(g['protocol_semantic_sha256']==cfg['protocol_semantic_sha256'],'Readiness protocol changed');state=load(Path(cfg['research_run_root'])/'CONTROLLER_STATE.json');a=state['approvals']['S05'];need(a['approved'] is True and a['source']=='direct_chat' and a['message']=='APPROVE S05 at 7007ebd05bf59432bf69109e5f69baad31ec0d3a' and v['candidate_id'] in a['scope_candidates'],'Missing/mismatched direct S05scope');need(state['phase_receipts']['S04']['sha256']==g['S04_receipt_sha256'],'Frozen S04receipt changed');need(sha(Path(cfg['frozen_root'])/'S04_RECEIPT.json')==g['S04_receipt_sha256'],'Frozen S04seal changed');src=source_verify(c,role);bundle=load(c/'SOURCE_IDENTITY.json');cfg['_GPU_source']=bundle['roles']['GPU']['source_identity_sha256'];cfg['_producer_source']=bundle['roles']['producer']['source_identity_sha256'];cfg['_auditor_source']=bundle['roles']['auditor']['source_identity_sha256'];need(sha(c/'ENVIRONMENT_LOCK.json')==cfg['runtime_lock_sha256'],'GPU runtime source lock changed');cfg['_GPU_runtime_lock']=cfg['runtime_lock_sha256']
 if role!='GPU':need(sha(c/'CPU_ENVIRONMENT_LOCK.json')==cfg['cpu_runtime_lock_sha256'],'CPU runtime lock changed');cfg['runtime_lock_sha256']=cfg['cpu_runtime_lock_sha256']
 need(int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())>=48*1024**3,'Frozen48GiBhost headroom notavailable; no scientificdispatch');return cfg,v,src

def write_seal(root,identity,files,counts=None):
 root=Path(root);need(files,'Empty completion seal forbidden');entries=[]
 for name in files:
  safe_rel(name);p=root/name;need(p.is_file() and not p.is_symlink(),'Missing/nonregular output');
  with p.open('rb') as durable:os.fsync(durable.fileno())
  entries.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'verified_stat':file_stat(p)})
 need(len({x['path'] for x in entries})==len(entries),'Duplicate sealed member');receipt={'schema_version':'s05-private-unit-seal-v1','status':'COMPLETE_UNVERIFIED','identity':identity,'identity_sha256':digest(identity),'files':entries,'counts':counts or {},'completed_utc':now(),'completion_written_last':True};put(root/'COMPLETE.json',receipt);return receipt

def verify_seal(root,identity=None,required=None,full_hash=False,restored=False):
 root=Path(root);r=load(root/'COMPLETE.json');need(r.get('status')=='COMPLETE_UNVERIFIED' and r.get('completion_written_last') is True and r.get('files'),'False/incomplete completion receipt');need(r['identity_sha256']==digest(r['identity']),'Broken input identity seal');need(identity is None or r['identity_sha256']==digest(identity),'Changed source/input invalidates affected unit');names=[f['path'] for f in r['files']];need(len(names)==len(set(names)),'Duplicate completion member');need(required is None or set(names)==set(required),'Missing/extra required unit files')
 for f in r['files']:
  safe_rel(f['path']);p=root/f['path'];need(p.is_file() and not p.is_symlink() and p.stat().st_size==f['bytes'],'Missing/changed sealed bytes')
  current=file_stat(p);cachekey=str(p.resolve());witness=(f['sha256'],current)
  if full_hash or _VALIDATED_FILES.get(cachekey)!=witness:
   if full_hash or restored or current!=f['verified_stat']:need(sha(p)==f['sha256'],'Sealed file hash mismatch')
   _VALIDATED_FILES[cachekey]=witness
 return r

def metadata(cfg,split,inputs_root=None):
 need(split in ['train','dev'],'Test metadata rejected before opening');p=Path(inputs_root or cfg['inputs_root'])/('emp_H3-'+split+'-metadata.json');rows=load(p);need(len(rows)==cfg['cohorts'][split]['rows'] and digest(rows)==cfg['cohorts'][split]['ordered_metadata_sha256'],'H3 cohort/order/label/group changed');return rows

def sequences(cfg,alias,split,first,stop):
 scope(cfg,alias,splits=[split]);expected=metadata(cfg,split);need(0<=first<stop<=len(expected),'Chunk offsets outside frozen cohort');path=Path(cfg['original_manifest']);need(sha(path)==cfg['original_manifest_sha256'],'Original H3 manifest bytes changed');out=[];cursor=0;pattern=re.compile(r'"split"\s*:\s*"([^"]+)"')
 # Only selected approved split rows are decoded. Historical test rows are skipped lexically, never materialized or forwarded.
 for line in path.open():
  found=pattern.findall(line);need(len(found)==1,'Ambiguous source split')
  if found[0]!=split:continue
  if cursor<first:cursor+=1;continue
  if cursor>=stop:break
  row=json.loads(line);e=expected[cursor];need(row['task']=='emp_H3' and row['split']==split and {'id':row['id'],'label':row['label'],'group':row['exact_rc_group']}==e,'Exact row/cohort association mismatch');s=row['sequence'];need(isinstance(s,str) and 2<=len(s)<=1000 and not set(s)-set('ACGTN'),'Unexpected sequence handling/alphabet/length');need(hashlib.sha256(s.encode()).hexdigest()==row['sequence_sha256'],'Sequence digest mismatch');rc=s.translate(str.maketrans('ACGTN','TGCAN'))[::-1];need(hashlib.sha256(min(s,rc).encode()).hexdigest()==e['group'],'Sequence exactRC group mismatch');out.append(row);cursor+=1
 need(len(out)==stop-first,'Missing exact approved rows');return out

def chunks_for(n):return [(a,min(a+256,n)) for a in range(0,n,256)]
def signature(r):return tuple((k,r.get(k)) for k in ['k','c','t','r','s','p','split','m','j','fold'] if k in r)
def planned(c):
 data=[json.loads(l) for l in (Path(c)/'FINITE_EXECUTION_MANIFEST.jsonl').read_text().splitlines()];need(len(data)==17151 and len({r['id'] for r in data})==17151,'Frozen S05manifest missing/duplicate specs');return {signature(r):r['id'] for r in data}
def spec_id(lookup,k,**dims):return lookup[signature({'k':k,**dims})]
def chunk_identity(cfg,v,source,split,first,stop,extraction_id):return {'planned_spec_id':extraction_id,'candidate_id':v['candidate_id'],'candidate_content_sha256':v['model_tensor_content_sha256'],'task':'emp_H3','split':split,'first':first,'stop':stop,'protocol_semantic_sha256':cfg['protocol_semantic_sha256'],'source_identity_sha256':source,'runtime_lock_sha256':cfg['runtime_lock_sha256'],'cohort_order_sha256':cfg['cohorts'][split]['ordered_metadata_sha256'],'hooks':HOOKS,'width':1920,'physical_batch':8,'feature_dtype':'float32','LM_loss_dtype':'float32'}

def check_arrays(arr,expected,split):
 import numpy as np
 n=len(expected);need(arr['ids'].tolist()==[r['id'] for r in expected] and arr['labels'].tolist()==[r['label'] for r in expected] and arr['groups'].tolist()==[r['group'] for r in expected],'Order/class/group/filler leakage');need(arr['split'].tolist()==[split]*n and arr['task'].tolist()==['emp_H3']*n,'Test/other-task/filler contamination');need(arr['lengths'].shape==(n,) and np.all((arr['lengths']>=2)&(arr['lengths']<=1000)),'Invalid real row lengths');need(arr['nll_sum'].shape==(n,) and arr['nll_sum'].dtype==np.float32 and np.isfinite(arr['nll_sum']).all(),'Invalid actual LM sums');need(np.array_equal(arr['n_tokens'],arr['lengths']-1),'Valid target count/filler leakage');need(arr['n_tokens'].dtype.kind in 'iu','Noninteger target counts')
 for key in KEYS:need(key in arr and arr[key].shape==(n,1920) and arr[key].dtype==np.float32 and np.isfinite(arr[key]).all(),'Feature shape/dtype/finiteness/hooks changed: '+key)

def load_layer(case,cfg,split,key,inputs_root=None,restored=False):
 import numpy as np
 need(key in KEYS,'Unknown representation');expected=metadata(cfg,split,inputs_root);index=load(Path(case)/'features'/split/'INDEX.json');need(index['cohort_sha256']==cfg['cohorts'][split]['ordered_metadata_sha256'] and index['task']=='emp_H3' and index['split']==split,'Feature bundle scope changed');need(not cfg.get('_GPU_source') or index['source_identity_sha256']==cfg['_GPU_source'],'Feature source identity changed');need(not cfg.get('_GPU_runtime_lock') or index['runtime_lock_sha256']==cfg['_GPU_runtime_lock'],'Feature runtime binding changed');parts=[];ids=[];nll=[];targets=[];offset=0;seals=[]
 for v in index['chunks']:
  need(v['first']==offset and v['stop']>offset,'Missing/duplicate/noncontiguous chunk');root=Path(case)/v['relative_root'];need(sha(root/'COMPLETE.json')==v['seal_sha256'],'Chunk receipt changed');verify_seal(root,required=['features_and_lm.npz','RESOURCE.json'],restored=restored);stop=v['stop']
  with np.load(root/'features_and_lm.npz',allow_pickle=False) as z:
   need(z['ids'].tolist()==[r['id'] for r in expected[offset:stop]],'Feature roworder mismatch');need(z['labels'].tolist()==[r['label'] for r in expected[offset:stop]] and z['groups'].tolist()==[r['group'] for r in expected[offset:stop]],'Feature metadata mismatch');x=z[key];need(x.dtype==np.float32 and x.shape==(stop-offset,1920) and np.isfinite(x).all(),'Invalid float32 feature input');parts.append(x);ids+=z['ids'].tolist();nll.append(z['nll_sum']);targets.append(z['n_tokens'])
  offset=stop;seals.append(v['seal_sha256'])
 need(offset==len(expected),'Incomplete bundle denominator');return np.concatenate(parts),np.array([r['label'] for r in expected]),ids,np.concatenate(nll),np.concatenate(targets),digest(seals)

def fold_indices(cfg,seed,ids,inputs_root=None):
 import numpy as np
 need(seed in SEEDS,'Unknown CVseed');p=Path(inputs_root or cfg['inputs_root'])/('folds_seed'+str(seed)+'.json');e=next(f for f in cfg['folds'] if f['cv_seed']==seed);need(sha(p)==e['sha256'],'Frozen folds changed');rows=load(p);need(len(rows)==3,'H3 fold count changed');lookup={v:i for i,v in enumerate(ids)};need(len(lookup)==11971,'Wrong TRAIN population');val=[];out=[];meta=metadata(cfg,'train',inputs_root);group={r['id']:r['group'] for r in meta}
 for v in rows:
  tr=v['train_ids'];va=v['validation_ids'];need(set(tr)|set(va)==set(ids) and not set(tr)&set(va),'Invalid TRAIN partition');need(not {group[x] for x in tr}&{group[x] for x in va},'Fold group leakage');out.append((np.array([lookup[x] for x in tr]),np.array([lookup[x] for x in va])));val+=va
 need(len(val)==len(set(val))==11971,'Missing/duplicate validation membership');return out

def draw_weights(cfg,inputs_root=None):
 import numpy as np
 p=Path(inputs_root or cfg['inputs_root'])/'dev_resampling.npz';need(sha(p)==cfg['dev_draws']['sha256'],'Altered dev draw identity');rows=metadata(cfg,'dev',inputs_root)
 with np.load(p,allow_pickle=False) as z:
  need(z['ids'].tolist()==[r['id'] for r in rows] and int(z['seed'])==20261103,'Draw cohort/seed changed');names,inverse=np.unique([r['group'] for r in rows],return_inverse=True);need(np.array_equal(names,z['group_names']) and np.array_equal(inverse,z['row_groups']),'Draw group order changed');draws=z['group_draws'];need(draws.dtype==np.int32 and draws.shape==(2000,len(names)),'Draw count/dtype changed');weights=np.stack([np.bincount(d,minlength=len(names)) for d in draws])[:,inverse]
 return weights.astype(np.float64),np.array([r['label'] for r in rows]),cfg['dev_draws']['sha256']

def strict_residual(actual,reference,atol,label):
 import numpy as np
 a=np.asarray(actual);b=np.asarray(reference);need(a.shape==b.shape and a.size>0 and np.isfinite(a).all() and np.isfinite(b).all(),'Missing/nonfinite comparison '+label);delta=np.abs(a.astype(np.float64)-b.astype(np.float64));bad=delta>atol;ix=np.unravel_index(int(delta.argmax()),delta.shape);out={'label':label,'status':'PASS' if not bad.any() else 'FAIL','atol':atol,'rtol':0,'coordinates':int(delta.size),'max_abs_residual':float(delta.max()),'violations':int(bad.sum()),'worst_index':[int(i) for i in ix]};need(not bad.any(),'Numerical gate failed '+json.dumps(out));return out

def audit_membership(units,alias,representation,seed):
 need(any(z['c']==alias and z['r']==representation and z['s']==seed for z in units),'Unfrozen audit key rejected before fitting')
