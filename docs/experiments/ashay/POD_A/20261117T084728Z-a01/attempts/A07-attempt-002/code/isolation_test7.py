from common7 import *
import resource,re,time

def main():
 guard();b=read(C/'BACKUP_R5_gue_tf_0.json');root=Path(b['consumer_root']);dep=root.parent/'DEPENDENCY_MAP.json';assert sha(root/'artifacts/code/restore7.py')==next(e['sha256'] for e in read(C/'CPU_SOURCE_IDENTITY.json')['files'] if e['path']=='restore7.py');argv=[cfg['cpu_venv']+'/bin/python','-I','-B',str(A/'code/deny_producer7.py'),str(root),str(dep),'gue_tf_0'];env={k:v for k,v in os.environ.items() if not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4');t=time.monotonic()
 def bounds():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 out=A/'logs/isolation.001.stdout.json';err=A/'logs/isolation.001.stderr.log';assert not out.exists()
 with out.open('x') as o,err.open('x') as e:
  p=subprocess.Popen(argv,stdout=o,stderr=e,env=env,cwd=root,preexec_fn=bounds);ticks=Path('/proc')/str(p.pid)/'stat';start=ticks.read_text().split()[21];code=p.wait()
 assert code==0,err.read_text();j=read(out);assert j['status']=='PASS' and j['producer_path_denial_active'] and len(j['denied_sentinel_events'])==1 and len(j['checks'])==12;put(C/'PRODUCER_PATH_DENIAL_TEST.json',{'status':'PASS','scope':'One task isolation qualification; no additional fit or full-grid release','task':'gue_tf_0','prediction_metric_paths':12,'paired_vectors':240,'producer_tree_reads_denied':True,'sentinel_rejection_proven':True,'all_non_sentinel_file_reads_succeeded_from_consumers':True,'additional_fits':0,'argv':argv,'pid':p.pid,'proc_start_ticks':start,'exit_code':code,'wall_seconds':time.monotonic()-t,'stdout_sha256':sha(out),'stderr_sha256':sha(err),'source_sha256':sha(A/'code/deny_producer7.py'),'observed_utc':now()});print('ISOLATION_PASS')
if __name__=='__main__':main()
