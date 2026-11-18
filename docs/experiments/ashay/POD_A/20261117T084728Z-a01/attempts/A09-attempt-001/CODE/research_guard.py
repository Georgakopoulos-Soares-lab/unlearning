"""POD_A-only guards, immutable predecessor baseline and exact expected HEAD."""
from pathlib import Path
import json,subprocess
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A09-attempt-001')
def identity(root,common,origin,push,branch):
 if (root,common,origin,push,branch)!=('/workspace/wt-pod-a','/workspace/repos/unlearning-pod-a/.git','https://github.com/Georgakopoulos-Soares-lab/unlearning.git','https://github.com/Georgakopoulos-Soares-lab/unlearning.git','POD_A'):raise ValueError('Wrong repository/worktree/branch/push identity')
def owned(path,allowed):return any(path==p or path.startswith(p+'/') for p in allowed)
def guard(allow_dirty=False,expected_head=None):
 cfg=json.loads((C/'RUN_CONFIG.json').read_text());W=Path(cfg['worktree']);D=Path(cfg['docs']);BASE=D.parent.parent;M=Path('/workspace/repos/unlearning-pod-a')
 def g(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args])
 root=g('rev-parse','--show-toplevel').decode().strip();common=str(Path(g('rev-parse','--git-common-dir').decode().strip()).resolve());identity(root,common,g('remote','get-url','origin').decode().strip(),g('remote','get-url','--push','origin').decode().strip(),g('branch','--show-current').decode().strip());assert W.resolve()==W
 assert g('ls-files','--stage','-z',cwd=M)==(C/'MAIN_INDEX_BEFORE.z').read_bytes();assert g('status','--porcelain=v1','-z',cwd=M)==(C/'MAIN_STATUS_BEFORE.z').read_bytes()
 before={l.split()[0]:l.split()[1] for l in (C/'REFS_BEFORE.txt').read_text().splitlines()};current={l.split()[0]:l.split()[1] for l in g('for-each-ref','--format=%(refname) %(objectname)').decode().splitlines()};allowedrefs={'refs/heads/POD_A','refs/remotes/origin/POD_A'};assert {k:v for k,v in before.items() if k not in allowedrefs}=={k:v for k,v in current.items() if k not in allowedrefs}
 deliveries=[json.loads(p.read_text()) for p in C.glob('DELIVERY_*.json') if p.name!='DELIVERY_RECEIPT.json'];known=max(deliveries,key=lambda j:j['delivered_utc'])['commit'] if deliveries else cfg['research_head_before'];head=g('rev-parse','HEAD').decode().strip();assert head==(expected_head or known),'Unexpected research HEAD'
 allowed=[str(D.relative_to(W))]+[str((BASE/n).relative_to(W)) for n in ['PROGRESS.md','CONTROLLER_LATEST.json','LATEST_A09.json']];status=g('status','--porcelain=v1','-z')
 if not allow_dirty:assert not status
 else:
  for entry in status.split(b'\0'):
   if entry:assert owned(entry[3:].decode(),allowed),'Unowned dirty path'
 return {'status':'PASS','head':head,'worktree':root,'common_git_directory':common,'branch':'POD_A','main_index_and_status_unchanged':True,'other_refs_unchanged':True,'owned_paths':allowed}
