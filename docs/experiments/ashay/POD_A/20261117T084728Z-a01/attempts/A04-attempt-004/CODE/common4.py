"""A04-attempt-004 isolated control/report primitives; no historical writes or dispatch."""
from pathlib import Path
import csv,datetime,hashlib,json,os,subprocess,sys
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A04-attempt-004');cfg=json.loads((C/'RUN_CONFIG.json').read_text());A=Path(cfg['artifacts']);REC=Path(cfg['recovery']);D=Path(cfg['docs']);R=Path(cfg['root_control']);B=Path(cfg['run_docs']);W=Path(cfg['worktree']);C2=C.parent/'A04-attempt-002';C3=C.parent/'A04-attempt-003';A2=A.parent/'A04-attempt-002';A3=A.parent/'A04-attempt-003';D2=D.parent/'A04-attempt-002';D3=D.parent/'A04-attempt-003';BACKUP_REPO='ashay-sriv/undo-evo2-pilot-backup-20261020';MIRROR_REPO='ashay-sriv/unlearning-checkpoint-mirror'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bh(b):return hashlib.sha256(b).hexdigest()
def digest(v):return bh(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def atomic(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name('.'+p.name+'.tmp');q.write_bytes(b);os.replace(q,p)
def put(p,v):
 if not isinstance(v,(dict,list)):raise TypeError('JSON object/array required')
 atomic(p,(json.dumps(v,indent=2,allow_nan=False)+'\n').encode())
def md(p,v):
 if not isinstance(v,str) or not v.startswith('# ') or '\n\n' not in v:raise TypeError('Plain Markdown heading and newlines required')
 atomic(p,(v.rstrip()+'\n').encode())
def git(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args],text=True).strip()
def gitb(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args])
def owned(path):return path.startswith(str(D.relative_to(W))+'/') or path in [str((B/n).relative_to(W)) for n in cfg['allowed_root_files']]
def guard(dirty=True,head=None):
 assert W.resolve()==W and git('rev-parse','--show-toplevel')==str(W) and git('branch','--show-current')=='POD_A' and str(Path(git('rev-parse','--git-common-dir')).resolve())==cfg['common_git_directory']
 assert git('remote','get-url','origin')==git('remote','get-url','--push','origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git'
 M=Path('/workspace/repos/unlearning-pod-a');assert gitb('ls-files','--stage','-z',cwd=M)==(C/'MAIN_INDEX_BEFORE.z').read_bytes() and gitb('status','--porcelain=v1','-z',cwd=M)==(C/'MAIN_STATUS_BEFORE.z').read_bytes()
 before=dict(l.split() for l in (C/'REFS_BEFORE.txt').read_text().splitlines());after=dict(l.split() for l in git('for-each-ref','--format=%(refname) %(objectname)').splitlines());allowed={'refs/heads/POD_A','refs/remotes/origin/POD_A'};assert {k:v for k,v in before.items() if k not in allowed}=={k:v for k,v in after.items() if k not in allowed}
 deliveries=[read(p) for p in C.glob('GIT_DELIVERY.*.json')];known=max(deliveries,key=lambda d:d['delivered_utc'])['commit'] if deliveries else cfg['research_head_before'];actual=git('rev-parse','HEAD');assert actual==(head or known),'Unreconciled research HEAD'
 for name,tree in read(C/'PRESERVED_WORK_INDEX.json')['existing_attempt_tree_ids'].items():assert git('rev-parse',actual+':'+str((B/'attempts'/name).relative_to(W)))==tree
 status=gitb('status','--porcelain=v1','-z','--untracked-files=all');assert dirty or not status
 for e in status.split(b'\0'):
  if e:assert owned(e[3:].decode()),'Unowned concurrent change'
 return {'status':'PASS','head':actual,'branch':'POD_A','worktree':str(W),'main_index_status_and_other_refs_unchanged':True,'previous_A01_A09_attempt_trees_unchanged':True}
def publish(name,value):
 guard();p=D/name;assert p.resolve().is_relative_to(D.resolve())
 if p.suffix=='.md':md(p,value.decode() if isinstance(value,bytes) else value)
 elif isinstance(value,(dict,list)):put(p,value)
 elif isinstance(value,bytes):atomic(p,value)
 else:atomic(p,value.encode())
def table(name,rows,fields=None):
 guard();p=D/name;p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name('.'+p.name+'.tmp')
 with q.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
 os.replace(q,p)
