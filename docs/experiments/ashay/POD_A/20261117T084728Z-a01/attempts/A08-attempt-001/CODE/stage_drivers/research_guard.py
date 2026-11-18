"""Explicit POD_A-only research guards. Read-only until guarded publication calls."""
from pathlib import Path
import hashlib,json,subprocess
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A08-attempt-001');cfg=json.loads((C/'RUN_CONFIG.json').read_text());W=Path(cfg['worktree']);D=Path(cfg['docs']);BASE=D.parent.parent;MAIN=Path('/workspace/repos/unlearning-pod-a');ORIGIN='https://github.com/Georgakopoulos-Soares-lab/unlearning.git'
def git(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args])
def guard(allow_dirty=False,expected_head=None):
 assert W.resolve()==Path('/workspace/wt-pod-a') and git('rev-parse','--show-toplevel').decode().strip()==str(W);common=Path(git('rev-parse','--git-common-dir').decode().strip());assert common.resolve()==MAIN/'.git';assert git('remote','get-url','origin').decode().strip()==ORIGIN and git('remote','get-url','--push','origin').decode().strip()==ORIGIN;assert git('branch','--show-current').decode().strip()=='POD_A';assert git('ls-files','--stage','-z',cwd=MAIN)==(C/'MAIN_INDEX_BEFORE.z').read_bytes();assert git('status','--porcelain=v1','-z',cwd=MAIN)==(C/'MAIN_STATUS_BEFORE.z').read_bytes()
 refs={l.split()[0]:l.split()[1] for l in git('for-each-ref','--format=%(refname) %(objectname)').decode().splitlines()};before={l.split()[0]:l.split()[1] for l in (C/'REFS_BEFORE.txt').read_text().splitlines()};allowedrefs={'refs/heads/POD_A','refs/remotes/origin/POD_A'};assert {k:v for k,v in refs.items() if k not in allowedrefs}=={k:v for k,v in before.items() if k not in allowedrefs};head=git('rev-parse','HEAD').decode().strip();deliveries=[json.loads(p.read_text()) for p in C.glob('DELIVERY_*.json') if p.name!='DELIVERY_RECEIPT.json'];known=max(deliveries,key=lambda j:j['delivered_utc'])['commit'] if deliveries else cfg['research_head_before'];assert head==(expected_head if expected_head is not None else known),'Unexpected research HEAD; inspect compatible descendants before any mutation'
 status=git('status','--porcelain=v1','-z');allowed=[str(D.relative_to(W)),str((BASE/'LATEST_A08.json').relative_to(W)),str((BASE/'PROGRESS.md').relative_to(W)),str((BASE/'CONTROLLER_LATEST.json').relative_to(W))]
 if (C/'BACKFILL_REPORT_PATHS.json').exists():allowed+=json.loads((C/'BACKFILL_REPORT_PATHS.json').read_text())
 if not allow_dirty:assert not status
 else:
  for entry in status.split(b'\0'):
   if not entry:continue
   path=entry[3:].decode();assert any(path==p or path.startswith(p+'/') for p in allowed),'Unowned dirty path: '+path
 return {'status':'PASS','worktree':str(W),'common_git_directory':str(common),'branch':'POD_A','origin':ORIGIN,'head':head,'main_index_and_status_unchanged':True,'other_refs_unchanged':True,'dirty_scope_allowed':allow_dirty,'scoped_paths':allowed,'AGENTS_reconciliation':'Current explicit userA08 approval and pinnedstage supersede historicalAGENTS oldbranch/venv/timeledger instructions; historical artifacts/ledgers remainread-only'}
if __name__=='__main__':print(json.dumps(guard(expected_head=cfg['research_head_before']),indent=2))
