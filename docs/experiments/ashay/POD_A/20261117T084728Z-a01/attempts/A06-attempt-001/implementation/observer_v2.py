"""Deterministic administrative observer. Fetches data only; never executes or publishes it."""
from pathlib import Path,PurePosixPath
import argparse,datetime,fcntl,hashlib,json,logging,logging.handlers,os,subprocess,time
ORIGIN='https://github.com/ashay-sriv-06/test-prompts-push.git'
CONTROLLER=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/CONTROLLER_STATE.json')
CANONICAL=['A01_WORKSPACE_RECONCILIATION.md','A02_CHECKPOINT_INVENTORY.md','A03_RECOVERY_DATA_AUDIT.md','A04_RUNTIME_LOADING.md','A05_PROTOCOL_COVERAGE_FREEZE.md','A06_EXTRACTION_H3_GATE.md','A07_PROBES_FIXED_REFERENCE.md','A08_VERIFICATION_ANALYSIS.md','A09_REPORTING_RECOVERY.md']
def approved_context():
 state=json.loads(CONTROLLER.read_text());control=Path(state['paths']['control']);approval=json.loads((control/'APPROVAL_RECORD.json').read_text());config=json.loads((control/'RUN_CONFIG.json').read_text());pin=state['prompt_commit']
 if pin!=approval['prompt_commit'] or pin!=config['prompt_commit'] or state['stage']!=approval['stage'] or state['stage']!=config['stage']:raise ValueError('Controller/approval/pin inconsistency')
 package=json.loads((control/'PACKAGE_VERIFICATION.json').read_text());entries=package.get('files',package.get('results'));return pin,{e['path']:e['sha256'] for e in entries},state['stage']
def validate_mapping(stage):
 if not isinstance(stage,dict) or [(s.get('id'),s.get('file')) for s in stage.get('stages',[])]!=[(f'A{i:02d}',p) for i,p in enumerate(CANONICAL,1)]:raise ValueError('Unsupported canonical stage map')
 if stage.get('execution_on_install') is not False or stage.get('administrative_loop',{}).get('stage_dispatch') is not False:raise ValueError('Unauthorized dispatch mapping')
def validate_identity(origin,pushurl,ref):
 if origin!=ORIGIN or pushurl!='DISABLED_OBSERVER_READ_ONLY' or ref!='refs/heads/POD_A':raise ValueError('Wrong repository/ref/observer push policy')
def health_status(success,error,now_epoch):
 if error and (not success or error['observed_utc']>success['observed_utc']):return 'ERROR_NEWER_THAN_SUCCESS'
 if not success:return 'NO_SUCCESS'
 age=now_epoch-datetime.datetime.fromisoformat(success['observed_utc']).timestamp();return 'STALE_SUCCESS' if age>1500 else 'ACTIVE'
ROOT=Path('/workspace/agent-handoff/POD_A/review-loop');CACHE=Path('/workspace/repos/pod-a-observer-cache.git')
STAGES={'A05_PROTOCOL_COVERAGE_FREEZE.md','A06_EXTRACTION_H3_GATE.md','A07_PROBES_FIXED_REFERENCE.md','A08_VERIFICATION_ANALYSIS.md','A09_REPORTING_RECOVERY.md'}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(p,v):
 t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n');os.replace(t,p)
def safe_path(s):
 p=PurePosixPath(s)
 if not s or p.is_absolute() or '..' in p.parts or str(p)!=s or '\\' in s or '\n' in s:raise ValueError('Unsafe path')
 return s
def validate_package(readfile,mode):
 package=json.loads(readfile('PACKAGE_FILES.json'));files=package['files']
 if len(files)!=len(set(files)):raise ValueError('Duplicate package path')
 for p in files:safe_path(p)
 sums={}
 for l in readfile('SHA256SUMS').decode().splitlines():
  if not l:continue
  if len(l)<67 or l[64:66]!='  ':raise ValueError('Malformed checksum')
  h,p=l[:64],safe_path(l[66:])
  if p in sums or len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Duplicate/invalid digest')
  sums[p]=h
 if set(sums)!=set(files):raise ValueError('Package/checksum mismatch')
 for p,h in sums.items():
  if mode(p)!='100644' or hashlib.sha256(readfile(p)).hexdigest()!=h:raise ValueError('Bad bytes/mode: '+p)
 stage=json.loads(readfile('STAGE_MAP.json'))
 validate_mapping(stage)
 return sums
def publish_boundary(paths,active,next_stage,expected_head,actual_head):
 if expected_head!=actual_head:raise ValueError('Remote advance')
 if next_stage==active or next_stage not in STAGES:raise ValueError('Active/unsupported stage')
 if paths.count(next_stage)!=1 or paths.count('SHA256SUMS')!=1:raise ValueError('Missing atomic stage/checksum')
 for p in paths:
  safe_path(p)
  if p not in [next_stage,'SHA256SUMS'] and not p.startswith('reviews/'):raise ValueError('Forbidden publication path')
 return 'VALIDATED_DRAFT_ONLY'
def g(*args):
 # Fixed origin/ref only. No inherited terminal prompt, hooks or Git write operation.
 env={**os.environ,'GIT_TERMINAL_PROMPT':'0'}
 return subprocess.check_output(['git','-c','core.hooksPath=/dev/null','-C',str(CACHE),*args],env=env,stderr=subprocess.PIPE,timeout=120)
def tick():
 ROOT.mkdir(parents=True,exist_ok=True)
 if (ROOT/'STOP').exists():return {'status':'STOPPED','observed_utc':now()}
 if (ROOT/'DISABLED').exists():return {'status':'PAUSED','observed_utc':now()}
 with (ROOT/'observer.lock').open('a') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return {'status':'SKIPPED_BUSY','observed_utc':now()}
  if CACHE.resolve()!=CACHE or g('remote','get-url','origin').decode().strip()!=ORIGIN:raise ValueError('Wrong cache/origin')
  validate_identity(g('remote','get-url','origin').decode().strip(),g('remote','get-url','--push','origin').decode().strip(),'refs/heads/POD_A')
  active_pin,active_hashes,active_stage=approved_context()
  g('fetch','--no-tags','origin','refs/heads/POD_A:refs/remotes/origin/POD_A')
  head=g('rev-parse','refs/remotes/origin/POD_A').decode().strip()
  def readfile(p):return g('show',head+':'+safe_path(p))
  def mode(p):return g('ls-tree',head,'--',safe_path(p)).decode().split()[0]
  hashes=validate_package(readfile,mode);old=json.loads((ROOT/'heartbeat.json').read_text()) if (ROOT/'heartbeat.json').exists() else {}
  changed=[p for p,h in hashes.items() if old.get('effective_hashes',{}).get(p)!=h]
  state={'schema_version':1,'status':'PASS','observed_utc':now(),'old_commit':old.get('commit'),'commit':head,'active_approved_pin':active_pin,'active_stage':active_stage,'active_effective_hashes':active_hashes,'effective_changed_from_active':[p for p,h in hashes.items() if active_hashes.get(p)!=h],'effective_hashes':hashes,'package_checksums':'PASS','changed_paths':changed,'availability':'AVAILABLE_FOR_REVIEW' if head!=active_pin else 'APPROVED_PIN_OBSERVED','science_execution':False,'publication':False,'next_tick_epoch':time.time()+1200,'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21]}
  inbox=ROOT/'inbox';inbox.mkdir(exist_ok=True);entry=inbox/(head+'.json')
  if not entry.exists():put(entry,state)
  put(ROOT/'heartbeat.json',state)
  put(ROOT/'latest_attempt.json',{'status':'PASS','observed_utc':state['observed_utc'],'commit':head,'science_execution':False})
  with (ROOT/'observer_events.jsonl').open('a') as events:events.write(json.dumps({k:v for k,v in state.items() if k!='effective_hashes'})+'\n')
  return state
def serve():
 log=logging.getLogger('observer');log.setLevel(logging.INFO);h=logging.handlers.RotatingFileHandler(ROOT/'observer.log',maxBytes=1048576,backupCount=3);log.addHandler(h)
 with (ROOT/'service.lock').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while not (ROOT/'STOP').exists():
   try:state=tick();log.info(json.dumps({k:v for k,v in state.items() if k!='effective_hashes'}))
   except Exception as e:
    # Do not write subprocess stderr: credential helper output is not a safe diagnostic.
    error={'observed_utc':now(),'error_type':type(e).__name__,'returncode':getattr(e,'returncode',None),'status':'ERROR','science_execution':False};put(ROOT/'last_error.json',error);put(ROOT/'latest_attempt.json',error);log.error(type(e).__name__)
   for _ in range(1200):
    if (ROOT/'STOP').exists():return
    time.sleep(1)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['tick','serve']);args=p.parse_args()
 if args.operation=='tick':print(json.dumps(tick()))
 else:serve()
