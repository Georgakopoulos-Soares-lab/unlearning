"""One finite declared A07 command, supervised to exit; never a stage dispatcher."""
from common7 import *
import resource,re,time
ALLOWED={'build_other_five_cache.py','fit_other_five.py'}
def main(jobfile):
 guard();jobfile=Path(jobfile);assert jobfile.resolve().is_relative_to((C/'jobs').resolve()) and jobfile.suffix=='.json';j=read(jobfile);assert j['stage']=='A07' and j['candidate']=='R5' and j['coverage_plan_sha256']==cfg['coverage_plan_sha256'] and j['prompt_commit']==cfg['prompt_commit'];assert j['source_identity_sha256']==sha(C/'CPU_SOURCE_IDENTITY.json');argv=j['argv'];script=Path(argv[1]);assert script.parent==A/'code' and script.name in ALLOWED and sha(script)==j['script_sha256'];assert j['kind']=='CPU' and argv[0]==cfg['cpu_venv']+'/bin/python';assert '--candidate' in argv and argv[argv.index('--candidate')+1]=='R5';out=C/'jobs'/(jobfile.stem+'.result.json');assert not out.exists(),'Invocation identity already used; preserve diagnostic and explicitly allocate retry'
 env={k:v for k,v in os.environ.items() if not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',TOKENIZERS_PARALLELISM='false');start=time.monotonic();logs=A/'logs';stdout=logs/(jobfile.stem+'.stdout.log');stderr=logs/(jobfile.stem+'.stderr.log');pre=None
 if j['kind']=='CPU':
  def bound():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
  pre=bound
 with stdout.open('x') as o,stderr.open('x') as e:
  p=subprocess.Popen(argv,stdout=o,stderr=e,env=env,cwd=A/'code',preexec_fn=pre);ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21];record={'stage':'A07','candidate':'R5','pid':p.pid,'proc_start_ticks':ticks,'argv':argv,'command_sha256':digest(argv),'source_identity_sha256':j['source_identity_sha256'],'script_sha256':j['script_sha256'],'launcher_sha256':sha(__file__),'kind':j['kind'],'status':'RUNNING','started_utc':now(),'credential_environment_removed':True,'CPU_worker_AS_limit_bytes':32*1024**3 if j['kind']=='CPU' else None,'CPU_child_identities':[]};put(C/'jobs'/(jobfile.stem+'.active.json'),record);children={}
  while True:
   try:exitcode=p.wait(timeout=5);break
   except subprocess.TimeoutExpired:
    if j['kind']=='CPU':
     path=Path('/proc/'+str(p.pid)+'/task/'+str(p.pid)+'/children')
     for child in path.read_text().split() if path.exists() else []:
      try:
       stat=(Path('/proc')/child/'stat').read_text().split();children[child]={'pid':int(child),'proc_start_ticks':stat[21],'parent':p.pid,'scientific_script_sha256':j['script_sha256']}
      except FileNotFoundError:pass
     record['CPU_child_identities']=list(children.values());put(C/'jobs'/(jobfile.stem+'.active.json'),record)
 record.update(status='PASS_EXIT' if exitcode==0 else 'FAILED_EXIT',exit_code=exitcode,wall_seconds=time.monotonic()-start,completed_utc=now(),stdout_sha256=sha(stdout),stderr_sha256=sha(stderr));put(out,record)
 with (C/'RESOURCE_LEDGER.jsonl').open('a') as f:f.write(json.dumps(record|{'rate':None,'cost':None,'deadline':None})+'\n')
 print(json.dumps({k:record[k] for k in ['status','pid','exit_code','wall_seconds']}));sys.exit(exitcode)
if __name__=='__main__':main(sys.argv[1])
