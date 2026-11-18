"""One finite approved CPU phase, actual argv and process/resource receipts."""
from common import *
import argparse,resource,time
def run(name,argv):
 out=A/'logs'/(name+'.stdout.jsonl');err=A/'logs'/(name+'.stderr.log');assert not out.exists() and not err.exists(),'Reconcile existing invocation; never overwrite logs';t=time.monotonic();env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','NUMEXPR_NUM_THREADS':'4','PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':''}
 with out.open('w') as f,err.open('w') as e:
  process=subprocess.Popen(argv,stdout=f,stderr=e,env=env);start=Path('/proc/'+str(process.pid)+'/stat').read_text().split()[21];job={'name':name,'stage':'A08','pid':process.pid,'proc_start_ticks':start,'argv':argv,'command_sha256':digest(argv),'started_utc':now(),'status':'RUNNING','source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'allowed_scope':'Finite approved A08 units only','GPU_work':0};put(C/('JOB_'+name+'.json'),job)
  state=read(R/'CONTROLLER_STATE.json');state.update(status='RUNNING',scientific_job_state='RUNNING',owned_job=job);put(R/'CONTROLLER_STATE.json',state);put(C/'CONTROLLER_STATE.json',state);rc=process.wait()
 job.update(status='EXITED_PASS' if rc==0 else 'EXITED_FAILED',exit_code=rc,completed_utc=now(),wall_seconds=time.monotonic()-t,children_CPU_user_seconds=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime,children_CPU_system_seconds=resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime,stdout=ref(out),stderr=ref(err));put(C/('JOB_'+name+'.json'),job)
 with (C/'RESOURCE_LEDGER.jsonl').open('a') as f:f.write(json.dumps(job)+'\n')
 state=read(R/'CONTROLLER_STATE.json');state.update(scientific_job_state='QUIET',owned_job=None);put(R/'CONTROLLER_STATE.json',state);put(C/'CONTROLLER_STATE.json',state);print(json.dumps({'name':name,'exit_code':rc,'seconds':job['wall_seconds']}),flush=True);assert rc==0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('argv',nargs=argparse.REMAINDER);v=p.parse_args();run(v.name,v.argv[1:] if v.argv and v.argv[0]=='--' else v.argv)
