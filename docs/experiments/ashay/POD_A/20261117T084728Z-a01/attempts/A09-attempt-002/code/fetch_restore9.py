"""Standalone exact-revision report restore and finite saved-analysis verification."""
from pathlib import Path
import argparse,json,hashlib,os,sys,re,subprocess,time,resource
from huggingface_hub import hf_hub_download,HfApi
from archive_portable9 import safe_extract

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(args):
 destination=args.destination.resolve();assert not destination.exists(),'Use a new empty destination; preserve earlier restore attempts';destination.mkdir(parents=True);receipt=read(args.receipt);p=receipt['report_payload'];api=HfApi();assert api.repo_info(p['repository'],repo_type='dataset').private;t=time.monotonic();file=Path(hf_hub_download(p['repository'],p['archive_path'],repo_type='dataset',revision=p['revision'],force_download=True,cache_dir=str(destination/'new-cache')));assert file.stat().st_size==p['archive_bytes'] and sha(file)==p['archive_sha256'];download=time.monotonic()-t;consumer=destination/'consumer';number,seconds=safe_extract(file,consumer);assert sha(consumer/'MEMBER_MANIFEST.json')==p['member_manifest_sha256'];assert number==p['members'];env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME'] and not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(destination/'plot-config'));jobs=[]
 def bound():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 def execute(label,argv):
  before=time.monotonic()
  with (destination/(label+'.stdout.json')).open('x') as out,(destination/(label+'.stderr.log')).open('x') as err:
   child=subprocess.Popen(argv,cwd=consumer,env=env,stdout=out,stderr=err,preexec_fn=bound);ticks=Path('/proc/'+str(child.pid)+'/stat').read_text().split()[21];code=child.wait()
  job={'label':label,'pid':child.pid,'proc_start_ticks':ticks,'argv':argv,'exit_code':code,'wall_seconds':time.monotonic()-before,'GPU_visibility':'DISABLED','credential_and_producer_PYTHONPATH_removed':True};jobs.append(job);(destination/(label+'.job.json')).write_text(json.dumps(job,indent=2)+'\n');assert code==0,'Preserve failed consumer logs: '+label;return read(destination/(label+'.stdout.json'))
 argv=[str(args.cpu_python),'-B',str(consumer/'code/restore9.py'),'--root',str(consumer)]
 if args.dependency_roots:argv+=['--dependency-roots',str(args.dependency_roots.resolve())]
 checks=execute('numeric-consumer-001',argv);assert checks['status']=='PASS' and checks['prediction_paths']==24 and checks['classifier_vectors']==60 and checks['LM_vectors']==6
 # Renderer executes from the fresh consumer, under the same explicit producer-tree denial.
 runner=consumer/'code/render_consumer9.py';render=execute('figure-consumer-001',[str(args.plot_python),'-B',str(runner),'--root',str(consumer),'--output',str(destination/'rendered')]);assert render['status']=='PASS' and render['producer_path_denial_active'] and render['source_rows_regenerated']
 expected={e['path'] for e in read(consumer/'MEMBER_MANIFEST.json')['files']}|{'MEMBER_MANIFEST.json'};assert {str(q.relative_to(consumer)) for q in consumer.rglob('*') if q.is_file()}==expected;assert api.repo_info(p['repository'],repo_type='dataset').private
 result={'status':'PASS','report_payload':p,'fresh_consumer':str(consumer),'force_download':True,'archive_size_sha256':'PASS','all_members_verified':number,'fresh_download_seconds':download,'all_member_hash_seconds':seconds,'numeric_consumer':checks,'figure_consumer':render,'jobs':jobs,'all_new_payload_members_verified':True,'producer_paths_denied':True,'inherited_new_download_bytes':0,'full_GPU_recreation':False};(destination/'FRESH_RESTORE_CHECK.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps(result,allow_nan=False))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--cpu-python',type=Path,required=True);p.add_argument('--plot-python',type=Path,required=True);p.add_argument('--dependency-roots',type=Path);main(p.parse_args())
