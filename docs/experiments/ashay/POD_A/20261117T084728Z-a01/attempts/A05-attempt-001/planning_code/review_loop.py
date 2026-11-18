"""Deterministic administrative observer. Fetches data only; never executes or publishes it."""
from pathlib import Path,PurePosixPath
import argparse,datetime,fcntl,hashlib,json,logging,logging.handlers,os,subprocess,time
ORIGIN='https://github.com/ashay-sriv-06/test-prompts-push.git'
PIN='eb861427378e14aedce307348fa9eab3fa989ca2'
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
 if not isinstance(stage,(dict,list)):raise ValueError('Bad stage map')
 # Known numbered canonical stage paths must all be represented; no unsupported numbered stage mapping.
 encoded=json.dumps(stage)
 for n in range(1,10):
  if f'A{n:02d}' not in encoded:raise ValueError('Incomplete stage map')
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
 if (ROOT/'DISABLED').exists():return {'status':'PAUSED','observed_utc':now()}
 with (ROOT/'observer.lock').open('a') as f:
  try:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:return {'status':'SKIPPED_BUSY','observed_utc':now()}
  if CACHE.resolve()!=CACHE or g('remote','get-url','origin').decode().strip()!=ORIGIN:raise ValueError('Wrong cache/origin')
  g('fetch','--no-tags','origin','refs/heads/POD_A:refs/remotes/origin/POD_A')
  head=g('rev-parse','refs/remotes/origin/POD_A').decode().strip()
  def readfile(p):return g('show',head+':'+safe_path(p))
  def mode(p):return g('ls-tree',head,'--',safe_path(p)).decode().split()[0]
  hashes=validate_package(readfile,mode);old=json.loads((ROOT/'heartbeat.json').read_text()) if (ROOT/'heartbeat.json').exists() else {}
  changed=[p for p,h in hashes.items() if old.get('effective_hashes',{}).get(p)!=h]
  state={'schema_version':1,'status':'PASS','observed_utc':now(),'old_commit':old.get('commit'),'commit':head,'active_approved_pin':PIN,'effective_hashes':hashes,'package_checksums':'PASS','changed_paths':changed,'availability':'AVAILABLE_FOR_REVIEW' if head!=PIN else 'APPROVED_PIN_OBSERVED','science_execution':False,'publication':False,'next_tick_epoch':time.time()+1200,'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21]}
  inbox=ROOT/'inbox';inbox.mkdir(exist_ok=True);entry=inbox/(head+'.json')
  if not entry.exists():put(entry,state)
  put(ROOT/'heartbeat.json',state)
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
    put(ROOT/'last_error.json',{'observed_utc':now(),'error_type':type(e).__name__,'returncode':getattr(e,'returncode',None),'status':'ERROR','science_execution':False});log.error(type(e).__name__)
   for _ in range(1200):
    if (ROOT/'STOP').exists():return
    time.sleep(1)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('operation',choices=['tick','serve']);args=p.parse_args()
 if args.operation=='tick':print(json.dumps(tick()))
 else:serve()
