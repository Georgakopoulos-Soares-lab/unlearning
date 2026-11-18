"""Finite A06 input, chunk and atomic resume contracts. No model or stage dispatch."""
from pathlib import Path
import hashlib,json,os,time,uuid,fcntl
import numpy as np
from qualification_contract import LAYERS,HOOKS,check_real_population,require,digest,sha
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']
def read(p):return json.loads(Path(p).read_text())
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.'+uuid.uuid4().hex+'.tmp')
 with t.open('w') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
 os.replace(t,p)
def owned(p,root):
 p=Path(p);root=Path(root).resolve();require(p.resolve().is_relative_to(root) and p.resolve()!=root,'Write-path escape');require(not p.is_symlink(),'Symlink output rejected');return p
def validate_rows(rows,task,split):
 require(task in TASKS and split in (['train','dev','test'] if task=='emp_H3' else ['train','dev']),'Unknown task/split')
 require(len(rows)>0 and len({r['id'] for r in rows})==len(rows),'Empty or duplicate row identity')
 for r in rows:
  require(r['task']==task and r['split']==split,'Cross-task/split manifest error');s=r['sequence'];require(2<=len(s)<=1000 and not set(s)-set('ACGTN'),'Unsupported sequence')
  h=hashlib.sha256(s.encode()).hexdigest();require(h==r.get('sequence_sha256',r.get('scored_prefix_sha256')),'Sequence digest/order differs');rc=s.translate(str.maketrans('ACGTN','TGCAN'))[::-1];require(hashlib.sha256(min(s,rc).encode()).hexdigest()==r['exact_rc_group'],'Unknown or changed group');require(isinstance(r['label'],int) and not isinstance(r['label'],bool),'Label schema differs')
 return rows
def validate_arrays(z,rows):
 for k,values in [('ids',[r['id'] for r in rows]),('labels',[r['label'] for r in rows]),('groups',[r['exact_rc_group'] for r in rows]),('split',[r['split'] for r in rows]),('task',[r['task'] for r in rows]),('sequence_sha256',[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows]),('lengths',[len(r['sequence']) for r in rows])]:require(z[k].tolist()==values,'Chunk '+k+' mismatch/filler leakage')
 check_real_population(z['ids'],[r['id'] for r in rows],{k:z[k] for k in LAYERS},z['nll_sum'],z['n_tokens'],z['lengths'])
 require(set(z)==set(LAYERS)|{'ids','labels','groups','split','task','sequence_sha256','lengths','nll_sum','n_tokens'},'Missing/unexpected arrays')
def payload(rows,features,sums,counts):
 return dict(ids=np.array([r['id'] for r in rows]),labels=np.array([r['label'] for r in rows]),groups=np.array([r['exact_rc_group'] for r in rows]),split=np.array([r['split'] for r in rows]),task=np.array([r['task'] for r in rows]),sequence_sha256=np.array([hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows]),lengths=np.array([len(r['sequence']) for r in rows]),nll_sum=np.asarray(sums),n_tokens=np.asarray(counts),**features)
def verify_chunk(path,identity,rows):
 path=Path(path);r=read(path/'COMPLETE.json');require(r['status']=='PASS' and r['identity']==identity,'Sealed chunk identity changed');require(r['rows']==len(rows),'Sealed chunk count differs')
 for e in r['files']:
  q=owned(path/e['path'],path);require(q.is_file() and q.stat().st_size==e['bytes'] and sha(q)==e['sha256'],'Corrupt sealed member')
 require([e['path'] for e in r['files']]==['features_and_lm.npz'],'Unexpected member set')
 with np.load(path/'features_and_lm.npz',allow_pickle=False) as z:validate_arrays(z,rows)
 return r
def prepare_chunk(path,identity,rows,quarantine):
 path=Path(path)
 if (path/'COMPLETE.json').exists():return 'REUSE',verify_chunk(path,identity,rows)
 if path.exists():
  owned(path,path.parent);require(not path.is_symlink(),'Unsafe partial path');quarantine=Path(quarantine);quarantine.mkdir(parents=True,exist_ok=True);os.replace(path,quarantine/(path.name+'-partial-'+uuid.uuid4().hex))
 return 'NEW',None
def seal_chunk(path,identity,rows,arrays,timing,quarantine,interrupt=None):
 path=Path(path);require(not path.exists(),'Would overwrite existing chunk');validate_arrays(arrays,rows);path.parent.mkdir(parents=True,exist_ok=True);temp=path.parent/('.'+path.name+'.work-'+uuid.uuid4().hex);temp.mkdir();p=temp/'features_and_lm.npz'
 with p.open('wb') as f:np.savez_compressed(f,**arrays);f.flush();os.fsync(f.fileno())
 if interrupt=='before_rename':raise InterruptedError('Synthetic pre-rename interruption')
 os.replace(temp,path)
 if interrupt=='after_rename':raise InterruptedError('Synthetic post-rename interruption')
 receipt={'schema':'pod-a-a06-chunk-v1','status':'PASS','identity':identity,'rows':len(rows),'files':[{'path':p.name,'bytes':(path/p.name).stat().st_size,'sha256':sha(path/p.name)}],'timing':timing};put(path/'COMPLETE.json',receipt);return receipt
def quarantine_temporaries(root,quarantine):
 root=Path(root);quarantine=Path(quarantine);quarantine.mkdir(parents=True,exist_ok=True)
 for p in root.glob('.*.work-*'):
  require(not p.is_symlink(),'Symlink temporary rejected');os.replace(p,quarantine/(p.name+'-'+uuid.uuid4().hex))
def require_gate(candidate,task,control):
 if task=='emp_H3':return
 p=Path(control)/('H3_GATE_'+candidate+'.json');require(p.is_file(),'Other-five extraction denied before H3 gate');j=read(p);require(j['status']=='PASS' and j['candidate']==candidate and j['backup_status']=='PASS','Unpassed/unprotected H3 gate')
def process_identity(pid,start):
 p=Path('/proc')/str(pid)/'stat';return p.exists() and p.read_text().split()[21]==str(start)
class UnitLock:
 def __init__(self,path):self.path=Path(path)
 def __enter__(self):
  self.path.parent.mkdir(parents=True,exist_ok=True);self.fd=self.path.open('a')
  try:fcntl.flock(self.fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BaseException:self.fd.close();raise
  return self
 def __exit__(self,*args):fcntl.flock(self.fd,fcntl.LOCK_UN);self.fd.close()

def safe_archive_members(members,root_name):
 from pathlib import PurePosixPath
 names=set()
 for member in members:
  require(member.name not in names,'Duplicate archive member');names.add(member.name)
  p=PurePosixPath(member.name);require(not p.is_absolute() and '..' not in p.parts and p.parts and p.parts[0]==root_name and (member.isfile() or member.isdir()) and not member.issym() and not member.islnk(),'Unsafe archive member')
 return True
