"""Exactly six already-approved TRAIN qualification units, sequential fresh processes."""
from common4 import *
import fcntl,time
def main():
 assert read(C/'A04_INPUT_VERIFICATION.json')['status']=='PASS';assert read(C/'IMPLEMENTATION_VALIDATION.json')['status']=='PASS';payload=read(C/'PAYLOAD_RECOVERY_INDEX.json');targets={r['alias']:r for r in payload['targets']};source=read(C/'SOURCE_IDENTITY.json')
 for e in source['owned_source_files']:assert sha(A/'code'/e['path'])==e['sha256']
 env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','TOKENIZERS_PARALLELISM':'false','PYTHONDONTWRITEBYTECODE':'1'};events=[];job={'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'status':'RUNNING','stage':'A04 only R3/R5 TRAIN qualification','source_sha256':sha(__file__),'started_utc':now()};put(C/'QUALIFICATION_CONTROLLER_JOB.json',job)
 with (C/'qualification-controller.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for alias in ['R3','R5']:
   if targets[alias]['payload_integrity_status']!='PASS':events.append({'alias':alias,'status':'BLOCKED_PAYLOAD','variants_pending':3});continue
   for variant in ['logical1','logical8','repeat8']:
    parent=A/'qualification'/alias/variant;prior=list(parent.glob('attempt-*'));assert not list(parent.glob('attempt-*/COMPLETE.json')),'Completed new-attempt units require explicit checked resume, not a duplicate run';n=max([int(p.name.split('-')[1]) for p in prior],default=0)+1;log=A/'logs'/f'qualification-{alias}-{variant}-attempt-{n:03d}.log';assert not log.exists();argv=[cfg['runtime_venv']+'/bin/python',str(A/'code/run_qualification.py'),'--control',str(C),'--alias',alias,'--variant',variant,'--unit-attempt',str(n),'--mode','qualification'];start=time.monotonic();print(json.dumps({'event':'UNIT_START','alias':alias,'variant':variant,'unit_attempt':n}),flush=True)
    with log.open('x') as f:p=subprocess.run(argv,stdout=f,stderr=subprocess.STDOUT,env=env)
    receipt=parent/f'attempt-{n:03d}'/('COMPLETE.json' if p.returncode==0 else 'FAILED.json');event={'alias':alias,'variant':variant,'unit_attempt':n,'status':'PASS' if p.returncode==0 else 'FAIL','returncode':p.returncode,'receipt':str(receipt),'log':str(log),'wall_seconds':time.monotonic()-start,'ended_utc':now()};events.append(event);put(C/'QUALIFICATION_CONTROLLER_EVENTS.json',{'events':events,'future_stage_dispatch':False});print(json.dumps(event),flush=True)
    if p.returncode!=0:
     # Do not repeat the same failed load three times; preserve it and continue the other candidate.
     break
  job.update(status='COMPLETED_AWAITING_PROCESS_EXIT',events=len(events),completed_utc=now());put(C/'QUALIFICATION_CONTROLLER_JOB.json',job);print(json.dumps({'status':'FINISHED_FINITE_UNITS','passed':sum(e['status']=='PASS' for e in events),'failed':sum(e['status']=='FAIL' for e in events),'next_stage_started':False}),flush=True)
if __name__=='__main__':main()
