"""Two qualified CPU workers/four BLAS threads each; one finite78-unit candidate-task batch."""
from pathlib import Path
import json,sys,os,concurrent.futures,time,hashlib,fcntl,resource
from ops import C,A,save,now
from long_run import execute
from dispatch_utils import complete
sys.path.insert(0,str(A/'code'));from artifact_seals import sha,need,load
stage_lock=(C/'CPU_PRODUCTION_STAGE.lock').open('a');fcntl.flock(stage_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
alias,t=sys.argv[1:3];cfg=load(C/'RUN_CONFIG.json');need(alias in {v['alias'] for v in cfg['candidates']} and t in cfg['tasks'],'Unapproved finite task group');need(load(C/'FIRST_PRODUCTION_GATES.json')['status']=='PASS','Operational gates missing');stat={k:int(v) for k,v in (l.split() for l in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())};maximum=int(Path('/sys/fs/cgroup/memory.max').read_text());current=int(Path('/sys/fs/cgroup/memory.current').read_text());advice=[]
if maximum-current<60*1024**3:
 need(stat['file']>32*1024**3,'Anonymous memory pressure requires diagnosis');C6=C.parent.parent/'S06/attempt-001';native=load(C6/'NATIVE_INPUT_BINDINGS.json');files=[Path(v['path']) for a in native.values() for v in a if v['path'].endswith('.distcp')]
 # Read-only eviction advice on known finished native-shard pages, never deletion/global cache drop.
 for p in files:
  need(p.is_file() and not p.is_symlink(),'Changed owned native cache file');fd=os.open(p,os.O_RDONLY)
  try:os.posix_fadvise(fd,0,0,os.POSIX_FADV_DONTNEED)
  finally:os.close(fd)
  advice.append({'path':str(p),'bytes':p.stat().st_size})
current=int(Path('/sys/fs/cgroup/memory.current').read_text());need(maximum-current>=48*1024**3,'Frozen48GiB batch admission headroom unavailable');cap=load(C/'CAPACITY_ADMISSION.json');protected=sum((C/(v['alias']+'-PRIVATE_RECOVERY_RECEIPT.json')).exists() for v in cfg['candidates']);remaining=cap['usable_remaining_lower_bound_bytes']-protected*40*1024**3;need(remaining>=104*1024**3,'Next40GiBcase plus64GiBreserve unavailable');save(C/(alias+'-'+t+'-BATCH_ADMISSION.json'),{'status':'PASS','cgroup_current':current,'cgroup_max':maximum,'headroom':maximum-current,'CPU_max':Path('/sys/fs/cgroup/cpu.max').read_text().strip(),'CPU_effective_cpuset':Path('/sys/fs/cgroup/cpuset.cpus.effective').read_text().strip(),'workers':2,'BLAS_threads_each':4,'worker_RSS_limit':8*1024**3,'stage_RSS_limit':24*1024**3,'remaining_accounting_lower_bound':remaining,'next_case_envelope':40*1024**3,'reserve':64*1024**3,'read_only_cache_advice':advice,'observed_utc':now()})
master=[json.loads(l) for l in (C/'FINITE_EXECUTION_MANIFEST.jsonl').open()];units=[];reused=[]
for rep in cfg['representations']:
 for seed in cfg['seeds']:
  key=next(r['id'] for r in master if r['k']=='final_head' and (r['c'],r['t'],r['r'],r['s'])==(alias,t,rep,seed));s={'alias':alias,'task':t,'representation':rep,'cv_seed':seed,'head_spec_id':key}
  if complete(alias,t,rep,seed):reused.append(s)
  else:units.append(s)
assert len(units)+len(reused)==78;env={'PATH':str(Path(cfg['cpu_runtime_python']).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','PYTHONPATH':str(A/'code'),'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'};qdir=C/'queues';qdir.mkdir(exist_ok=True);jobs=[];start=time.monotonic()
for worker in range(2):
 subset=units[worker::2]
 if not subset:continue
 p=qdir/(alias+'-'+t+'-worker'+str(worker)+'-001.json');need(not p.exists(),'Reconcile preserved worker queue before resumption; explicit new attempt suffix required');save(p,{'schema_version':'s07-finite-worker-queue-v1','source_bundle_sha256':sha(C/'SOURCE_IDENTITY.json'),'worker_entry_source_sha256':sha(C/'worker_entry.py'),'units':subset});p.chmod(0o444);jobs.append((p,sha(p),worker))
def work(job):
 p,h,i=job;return execute('S07-'+alias+'-'+t+'-CPU'+str(i)+'-001',[cfg['cpu_runtime_python'],str(C/'worker_entry.py'),str(p),h],env)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(work,jobs))
for rep in cfg['representations']:
 for seed in cfg['seeds']:need(complete(alias,t,rep,seed),'Task group has incomplete required unit')
need(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024+2*8*1024**3<=24*1024**3,'Stage RSS budget exceeded');case=A/'candidates'/alias/'tasks'/t;save(case/'GROUP_PRODUCTION.json',{'schema_version':'s07-group-production-v1','status':'COMPLETE_UNVERIFIED','producer_status':'PASS','alias':alias,'task':t,'heads':78,'applications':78,'prediction_paths':156,'metric_records':780,'initial_optimizer_call_specs':1248,'exact_specifications':2340,'retained_prior_completed_units':len(reused),'worker_exit_statuses':[r['exit_status'] for r in results],'stage_wall_seconds':time.monotonic()-start,'parent_peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'stage_RSS_conservative_upper_bound_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024+2*8*1024**3,'administrative_group_source_sha256':sha(Path(__file__)),'source_bundle_sha256':sha(C/'SOURCE_IDENTITY.json'),'backbone_or_LM_calls':0,'S08_release':'PENDING','completed_utc':now()});print('S07_CANDIDATE_TASK_PRODUCTION_COMPLETE',alias,t,78,flush=True)
