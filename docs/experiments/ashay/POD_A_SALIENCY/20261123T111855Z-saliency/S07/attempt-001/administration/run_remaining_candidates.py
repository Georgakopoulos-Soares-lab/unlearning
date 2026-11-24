"""Explicit finite S07 queue, all nine scopes; exact completed checkpoints reused. Never dispatch S08."""
from pathlib import Path
import sys,json,os,hashlib,fcntl
from ops import C,A,save,now
from long_run import execute
# A second invocation must reconcile, never overwrite, the live approved controller.
prior=C/'FINITE_QUEUE_PROCESS.json'
if prior.exists():
 old=json.loads(prior.read_text());p=Path('/proc/'+str(old['pid'])+'/stat')
 assert not (p.exists() and old['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip() and p.read_text().rsplit(')',1)[1].split()[19]==str(old['start_ticks'])),'Existing exact S07 controller is live; do not duplicate work'
phase_lock=(C/'WRITER.lock').open('a');fcntl.flock(phase_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
cfg=json.loads((C/'RUN_CONFIG.json').read_text());root=Path(cfg['research_run_root'])/'S07/attempt-001';identity={'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'script_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_bundle_sha256':hashlib.sha256((C/'SOURCE_IDENTITY.json').read_bytes()).hexdigest(),'status':'RUNNING','finite_candidate_order':[v['alias'] for v in cfg['candidates']],'scope':'Only approved S07 producer/private recovery/publication; stop before S08','observed_utc':now()};save(C/'FINITE_QUEUE_PROCESS.json',identity)
for v in cfg['candidates']:
 alias=v['alias'];delivery=C/('S07-'+alias+'-001-DELIVERY.json')
 if delivery.exists():
  d=json.loads(delivery.read_text());gate=root/'candidates'/alias/'CANDIDATE_GATE.json';assert d['status']=='PASS' and d['file_sha256'][str(gate.relative_to(Path(cfg['research_worktree'])))]==hashlib.sha256(gate.read_bytes()).hexdigest();print('REUSED_EXACT_PUBLISHED_PROTECTED_S07_CANDIDATE',alias,flush=True)
 else:
  execute('S07-'+alias+'-full-production-001',[sys.executable,str(C/'produce_candidate.py'),alias])
  execute('S07-'+alias+'-full-finish-001',[sys.executable,str(C/'finish_candidate.py'),alias])
 execute('S07-'+alias+'-closed-capacity-001',[sys.executable,str(C/'account_completed_case.py'),alias])
print('S07_FINITE_PRODUCER_PROTECTION_PUBLICATION_QUEUE_DRAINED_STOP_BEFORE_S08',flush=True)
