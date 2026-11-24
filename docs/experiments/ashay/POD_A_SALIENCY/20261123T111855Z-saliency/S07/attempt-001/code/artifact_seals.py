from pathlib import Path,PurePosixPath
import os,json,hashlib,datetime,fcntl,contextlib
_VALIDATED_FILES={}
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

def write_seal(root,identity,files,counts=None):
 root=Path(root);need(files,'Empty completion seal forbidden');entries=[]
 for name in files:
  safe_rel(name);p=root/name;need(p.is_file() and not p.is_symlink(),'Missing/nonregular output');
  with p.open('rb') as durable:os.fsync(durable.fileno())
  entries.append({'path':name,'bytes':p.stat().st_size,'sha256':sha(p),'verified_stat':file_stat(p)})
 need(len({x['path'] for x in entries})==len(entries),'Duplicate sealed member');receipt={'schema_version':'s07-private-unit-seal-v1','status':'COMPLETE_UNVERIFIED','identity':identity,'identity_sha256':digest(identity),'files':entries,'counts':counts or {},'completed_utc':now(),'completion_written_last':True};put(root/'COMPLETE.json',receipt);return receipt

def verify_seal(root,identity=None,required=None,full_hash=False,restored=False):
 root=Path(root);r=load(root/'COMPLETE.json');need(r.get('status')=='COMPLETE_UNVERIFIED' and r.get('completion_written_last') is True and r.get('files'),'False/incomplete completion receipt');need(r['identity_sha256']==digest(r['identity']),'Broken input identity seal');need(identity is None or r['identity_sha256']==digest(identity),'Changed source/input invalidates affected unit');names=[f['path'] for f in r['files']];need(len(names)==len(set(names)),'Duplicate completion member');need(required is None or set(names)==set(required),'Missing/extra required unit files')
 for f in r['files']:
  safe_rel(f['path']);p=root/f['path'];need(p.is_file() and not p.is_symlink() and p.stat().st_size==f['bytes'],'Missing/changed sealed bytes')
  current=file_stat(p);cachekey=str(p.resolve());witness=(f['sha256'],current)
  if full_hash or _VALIDATED_FILES.get(cachekey)!=witness:
   if full_hash or restored or current!=f['verified_stat']:need(sha(p)==f['sha256'],'Sealed file hash mismatch')
   _VALIDATED_FILES[cachekey]=witness
 return r

def strict_residual(actual,reference,atol,label):
 import numpy as np
 a=np.asarray(actual);b=np.asarray(reference);need(a.shape==b.shape and a.size>0 and np.isfinite(a).all() and np.isfinite(b).all(),'Missing/nonfinite comparison '+label);delta=np.abs(a.astype(np.float64)-b.astype(np.float64));bad=delta>atol;ix=np.unravel_index(int(delta.argmax()),delta.shape);out={'label':label,'status':'PASS' if not bad.any() else 'FAIL','atol':atol,'rtol':0,'coordinates':int(delta.size),'max_abs_residual':float(delta.max()),'violations':int(bad.sum()),'worst_index':[int(i) for i in ix]};need(not bad.any(),'Numerical gate failed '+json.dumps(out));return out
