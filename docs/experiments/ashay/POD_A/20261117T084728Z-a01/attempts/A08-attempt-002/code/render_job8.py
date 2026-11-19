from common8 import *
import re,time,resource

def main():
 guard();assert (C/'PLOT_JOB.001.result.json').exists();argv=['/workspace/venvs/pod-a-a08-figures/bin/python',str(A/'code/plot_analysis8.py'),'--stage','A08','--repair-panels'];env={k:v for k,v in os.environ.items() if not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',MPLCONFIGDIR=str(A/'plot-config'));start=time.monotonic()
 def bound():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 with (A/'logs/plot-render.003.stdout.log').open('x') as o,(A/'logs/plot-render.003.stderr.log').open('x') as e:
  p=subprocess.Popen(argv,stdout=o,stderr=e,env=env,cwd=A/'code',preexec_fn=bound);record={'pid':p.pid,'proc_start_ticks':Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21],'argv':argv,'command_sha256':digest(argv),'script_sha256':sha(A/'code/plot_analysis8.py'),'started_utc':now(),'status':'RUNNING','credential_environment_removed':True,'GPU_disabled':True,'AS_bytes':32*1024**3};put(C/'PLOT_JOB.active.json',record);code=p.wait()
 record.update(exit_code=code,status='PASS_EXIT' if code==0 else 'FAILED_EXIT',wall_seconds=time.monotonic()-start,completed_utc=now());put(C/'PLOT_JOB.json',record);print(json.dumps(record));assert code==0
if __name__=='__main__':main()
