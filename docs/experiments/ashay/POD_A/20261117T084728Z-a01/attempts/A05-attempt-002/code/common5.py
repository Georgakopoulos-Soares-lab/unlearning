"""Isolated metadata-only A05 attempt. No model/fit/effect imports or stage dispatcher."""
from pathlib import Path
import csv,datetime,hashlib,json,os,subprocess,sys
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A05-attempt-002');cfg=json.loads((C/'RUN_CONFIG.json').read_text());A=Path(cfg['artifacts']);REC=Path(cfg['recovery']);D=Path(cfg['docs']);R=Path(cfg['root_control']);B=Path(cfg['run_docs']);W=Path(cfg['worktree']);D3=D.parent/'A03-attempt-001';D4=D.parent/'A04-attempt-004';D50=D.parent/'A05-attempt-001';D6=D.parent/'A06-attempt-001';D7=D.parent/'A07-attempt-001';D8=D.parent/'A08-attempt-001';D9=D.parent/'A09-attempt-001';C4=C.parent/'A04-attempt-004';A4=A.parent/'A04-attempt-004';A6=A.parent/'A06-attempt-001';A7=A.parent/'A07-attempt-001';A8=A.parent/'A08-attempt-001';REPO='ashay-sriv/undo-evo2-pilot-backup-20261020';MIRROR='ashay-sriv/unlearning-checkpoint-mirror'
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];SEEDS=[42,17,1234];HOOKS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];POLICIES=['independent_refit','fixed_original_base'];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy'];ANCHORS=['decoder.layers.16','decoder.final_norm']
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
 if not isinstance(v,str) or not v.startswith('# ') or '\n\n' not in v:raise TypeError('Plain Markdown required')
 atomic(p,(v.rstrip()+'\n').encode())
def git(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args],text=True).strip()
def gitb(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args])
def owned(path):
 p=Path(path)
 if p.is_absolute() or '..' in p.parts or '\\' in path or str(p)!=path:return False
 return path.startswith(str(D.relative_to(W))+'/') or path in [str((B/n).relative_to(W)) for n in cfg['allowed_root_files']]
def guard(dirty=True,head=None):
 assert W.resolve()==W and git('rev-parse','--show-toplevel')==str(W) and git('branch','--show-current')=='POD_A' and str(Path(git('rev-parse','--git-common-dir')).resolve())==cfg['common_git_directory'];assert git('remote','get-url','origin')==git('remote','get-url','--push','origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git'
 M=Path('/workspace/repos/unlearning-pod-a');assert gitb('ls-files','--stage','-z',cwd=M)==(C/'MAIN_INDEX_BEFORE.z').read_bytes() and gitb('status','--porcelain=v1','-z',cwd=M)==(C/'MAIN_STATUS_BEFORE.z').read_bytes();before=dict(l.split() for l in (C/'REFS_BEFORE.txt').read_text().splitlines());after=dict(l.split() for l in git('for-each-ref','--format=%(refname) %(objectname)').splitlines());allowed={'refs/heads/POD_A','refs/remotes/origin/POD_A'};assert {k:v for k,v in before.items() if k not in allowed}=={k:v for k,v in after.items() if k not in allowed}
 deliveries=[read(p) for p in C.glob('GIT_DELIVERY.*.json')];expected=max(deliveries,key=lambda j:j['delivered_utc'])['commit'] if deliveries else cfg['research_head_before'];actual=git('rev-parse','HEAD');assert actual==(head or expected),'Unreconciled research HEAD'
 for name,tree in read(C/'PRESERVATION_BASELINE.json')['existing_attempt_tree_ids'].items():assert git('rev-parse',actual+':'+str((B/'attempts'/name).relative_to(W)))==tree
 status=gitb('status','--porcelain=v1','-z','--untracked-files=all');assert dirty or not status
 for e in status.split(b'\0'):
  if e:assert owned(e[3:].decode()),'Unowned concurrent change'
 return {'status':'PASS','head':actual,'branch':'POD_A','canonical_worktree':str(W),'main_index_status_and_other_refs_unchanged':True,'all_prior_attempt_trees_unchanged':True}
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
def no_science_imports():assert not any(n in sys.modules for n in ['torch','sklearn','joblib','bionemo','megatron'])
def reporting_splits(task):return ['dev','test_exploratory'] if task=='emp_H3' else ['dev']
def original_split(split):return 'test' if split=='test_exploratory' else split
