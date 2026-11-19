"""A09 reporting ownership, atomic publication and immutable predecessor guards."""
from pathlib import Path
import csv,datetime,hashlib,json,os,subprocess,sys
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A09-attempt-002');cfg=json.loads((C/'RUN_CONFIG.json').read_text());A=Path(cfg['artifacts']);D=Path(cfg['docs']);REC=Path(cfg['recovery']);R=Path(cfg['root_control']);B=Path(cfg['run_docs']);W=Path(cfg['worktree']);D8=B/'attempts/A08-attempt-002';C8=R/'attempts/A08-attempt-002';A8=A.parent/'A08-attempt-002';D80=B/'attempts/A08-attempt-001';D90=B/'attempts/A09-attempt-001';D5=B/'attempts/A05-attempt-002';D6=B/'attempts/A06-attempt-002';D7=B/'attempts/A07-attempt-002';REPO='ashay-sriv/undo-evo2-pilot-backup-20261020'
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];HOOKS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];ANCHORS=['decoder.layers.16','decoder.final_norm'];SEEDS=[42,17,1234];POLICIES=['independent_refit','fixed_original_base'];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy'];MODELS=['base','R1','R3','R4','R5','R6']
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bh(b):return hashlib.sha256(b).hexdigest()
def digest(v):return bh(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def atomic(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name('.'+p.name+'.tmp');q.write_bytes(b);os.replace(q,p)
def put(p,v):atomic(p,(json.dumps(v,indent=2,allow_nan=False)+'\n').encode())
def md(p,s):
 assert isinstance(s,str) and s.startswith('# ') and '\n\n' in s;atomic(p,(s.rstrip()+'\n').encode())
def git(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args],text=True).strip()
def gitb(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args])
def rows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def owned(path):
 p=Path(path);return not p.is_absolute() and '..' not in p.parts and '\\' not in path and str(p)==path and (path.startswith(str(D.relative_to(W))+'/') or path in [str((B/n).relative_to(W)) for n in cfg['allowed_root_files']])
def guard(dirty=True,head=None):
 assert W.resolve()==W and git('rev-parse','--show-toplevel')==str(W) and git('branch','--show-current')=='POD_A';assert str(Path(git('rev-parse','--git-common-dir')).resolve())==cfg['common_git_directory'];assert git('remote','get-url','origin')==git('remote','get-url','--push','origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git'
 M=Path('/workspace/repos/unlearning-pod-a');assert gitb('ls-files','--stage','-z',cwd=M)==(C/'MAIN_INDEX_BEFORE.z').read_bytes();assert gitb('status','--porcelain=v1','-z',cwd=M)==(C/'MAIN_STATUS_BEFORE.z').read_bytes();before=dict(s.split() for s in (C/'REFS_BEFORE.txt').read_text().splitlines());after=dict(s.split() for s in git('for-each-ref','--format=%(refname) %(objectname)').splitlines());allow={'refs/heads/POD_A','refs/remotes/origin/POD_A'};assert {k:v for k,v in before.items() if k not in allow}=={k:v for k,v in after.items() if k not in allow}
 receipts=[read(p) for p in C.glob('GIT_DELIVERY.*.json')];expected=max(receipts,key=lambda j:j['delivered_utc'])['commit'] if receipts else cfg['research_head_before'];actual=git('rev-parse','HEAD');assert actual==(head or expected),'Unreconciled research HEAD'
 baseline=read(C/'PRESERVATION_BASELINE.json')
 for name,tree in baseline['existing_attempt_tree_ids'].items():assert git('rev-parse',actual+':'+str((B/'attempts'/name).relative_to(W)))==tree
 assert git('rev-parse',actual+':'+str((B/'administrative-closeout').relative_to(W)))==baseline['administrative_closeout_tree']
 status=gitb('status','--porcelain=v1','-z','--untracked-files=all');assert dirty or not status
 for e in status.split(b'\0'):
  if e:assert owned(e[3:].decode()),'Unowned dirty path'
 return {'status':'PASS','head':actual,'branch':'POD_A','all_prior_attempt_trees_and_administrative_closeout_unchanged':True,'main_index_status_other_refs_preserved':True}
def publish(name,value):
 guard();p=D/name;assert p.resolve().is_relative_to(D.resolve())
 if p.suffix=='.md':md(p,value.decode() if isinstance(value,bytes) else value)
 elif isinstance(value,(dict,list)):put(p,value)
 else:atomic(p,value if isinstance(value,bytes) else value.encode())
def table(name,data,fields=None):
 guard();p=D/name;p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name('.'+p.name+'.tmp');assert data or fields
 with q.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields or list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
 os.replace(q,p)
def check_committed_files(paths,commit):
 proc=subprocess.Popen(['git','-C',str(W),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE);out=[]
 for p in paths:
  p=Path(p);rel=str(p.relative_to(W));proc.stdin.write((commit+':'+rel+'\n').encode());proc.stdin.flush();header=proc.stdout.readline().decode().split();assert len(header)==3 and header[1]=='blob',rel;data=proc.stdout.read(int(header[2]));assert len(data)==int(header[2]) and proc.stdout.read(1)==b'\n' and data==p.read_bytes(),rel;out.append({'path':rel,'bytes':len(data),'sha256':bh(data),'commit':commit})
 proc.stdin.close();assert proc.wait()==0;return out
def no_model_imports():assert not any(n in sys.modules for n in ['torch','bionemo','megatron'])
