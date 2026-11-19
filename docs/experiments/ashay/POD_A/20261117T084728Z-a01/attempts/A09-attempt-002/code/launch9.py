"""Supervise one explicit finite reporting or consumer command; never dispatch another stage."""
from common9 import *
import resource,re,time

def main(specpath):
 specpath=Path(specpath);assert specpath.resolve().is_relative_to((C/'jobs').resolve());j=read(specpath);assert j['stage']=='A09' and j['prompt_commit']==cfg['prompt_commit'];argv=j['argv'];script=Path(argv[2] if argv[1]=='-B' else argv[1]);assert script.name in ['plot9.py','restore9.py','render_report9.py'] and sha(script)==j['script_sha256'];assert argv[0] in [cfg['cpu_python'],cfg['plot_python']];assert script.resolve().is_relative_to(A.resolve()) or script.resolve().is_relative_to(REC.resolve());result=C/'jobs'/(specpath.stem+'.result.json');assert not result.exists();env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME'] and not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=j['MPLCONFIGDIR']);t=time.monotonic()
 def bound():resource.setrlimit(resource.RLIMIT_AS,(cfg['worker_AS_bytes'],cfg['worker_AS_bytes']))
 logs=A/'logs';stdout=logs/(specpath.stem+'.stdout.log');stderr=logs/(specpath.stem+'.stderr.log')
 with stdout.open('x') as o,stderr.open('x') as e:
  p=subprocess.Popen(argv,stdout=o,stderr=e,env=env,cwd=j['cwd'],preexec_fn=bound);ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21];r={'stage':'A09','job_id':specpath.stem,'pid':p.pid,'proc_start_ticks':ticks,'argv':argv,'command_sha256':digest(argv),'script_sha256':j['script_sha256'],'status':'RUNNING','started_utc':now(),'GPU_visibility':'DISABLED','credential_environment_removed':True,'producer_PYTHONPATH_removed':True,'AS_bytes':cfg['worker_AS_bytes'],'BLAS_threads':4};put(C/'jobs'/(specpath.stem+'.active.json'),r);code=p.wait()
 r.update(exit_code=code,status='PASS_EXIT' if code==0 else 'FAILED_EXIT',wall_seconds=time.monotonic()-t,completed_utc=now(),stdout_sha256=sha(stdout),stderr_sha256=sha(stderr));put(result,r);put(C/'jobs'/(specpath.stem+'.active.json'),r);print(json.dumps({k:r[k] for k in ['job_id','status','pid','exit_code','wall_seconds']}));sys.exit(code)
if __name__=='__main__':main(sys.argv[1])
