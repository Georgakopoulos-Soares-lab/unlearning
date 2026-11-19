"""Append-only phase checkpoints, fresh all-member integrity and consumer recovery."""
from common8 import *
from archive8 import safe_extract
from huggingface_hub import HfApi,hf_hub_download
import shutil,tarfile,time,re,resource

def ref(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def dependency_map():
 i=read(C/'A08_INPUTS.json');return {'A06_features':i['A06_feature_dependency'],'A07_tasks':{b['task']:b for b in i['A07_task_backups']},'historical_graph':read(D5/'RECOVERY_DEPENDENCY_GRAPH.json'),'new_download':False,'producer_substitution':False,'immutable_saved_outputs':read(C/'INHERITED_IMMUTABLE_MAP.json') if (C/'INHERITED_IMMUTABLE_MAP.json').exists() else None}

def main(label,kind,task=None):
 guard();api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;proof=C/('BACKUP_'+label+'.json')
 if proof.exists():assert read(proof)['status']=='PASS';return read(proof)
 assert re.fullmatch(r'[A-Za-z0-9_-]+',label) and kind in ['audit','classifier','LM'];name='A08-'+label+'-checkpoint-001';build=A/'checkpoint-builds'/name;archive=A/'archives'/(name+'.tar.gz');upfile=C/('UPLOADED_'+label+'.json');protected=read(C/'PROTECTED_OBJECTS.json') if (C/'PROTECTED_OBJECTS.json').exists() else {'files':{}}
 if not upfile.exists():
  assert not build.exists();build.mkdir(parents=True);paths=[]
  if kind=='audit':
   assert task in TASKS[1:];audits=list((A/'audits/R5'/task).glob('*/seed*/COMPLETE.json'));refits=list((A/'refits/R5'/task).glob('*/seed*/COMPLETE.json'));assert len(audits)==78 and len(refits)==6
   for sub in ['audits/R5/'+task,'refits/R5/'+task]:paths.extend(p for p in (A/sub).rglob('*') if p.is_file())
   cache=set()
   for p in audits:
    for r in read(p.parent/'NUMERICAL_AUDIT.json')['reference_distribution_receipts']:cache.add(str(Path(r['path']).parent))
   for root in sorted(cache):paths.extend(p for p in Path(root).rglob('*') if p.is_file() and str(p) not in protected['files'])
  else:
   subtree=A/'contrasts'/('classifier/'+label.removeprefix('adjacent_') if kind=='classifier' else 'LM');assert subtree.is_dir();paths.extend(p for p in subtree.rglob('*') if p.is_file())
   if (A/'endpoint-cache').exists():paths.extend(p for p in (A/'endpoint-cache').rglob('*') if p.is_file() and str(p) not in protected['files'])
   if (A/'normalized-lm').exists():paths.extend(p for p in (A/'normalized-lm').rglob('*') if p.is_file() and str(p) not in protected['files'])
  assert paths
  for p in sorted(set(paths)):
   rel='artifacts/'+str(p.relative_to(A));dest=build/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest);assert sha(dest)==sha(p)
  shutil.copytree(A/'code',build/'artifacts/code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(C/'package',build/'control/package')
  for n in ['RUN_CONFIG.json','APPROVAL_RECORD.json','A08_INPUTS.json','A08_EXECUTION_MANIFEST.json','CONTRAST_EXECUTION_MANIFEST.json','SOURCE_IDENTITY.json','IMPLEMENTATION_VALIDATION.json','RECOVERY_PANEL.json','ENVIRONMENT_CHECK.json','CONTRAST_SOURCE_IDENTITY.json','LM_NORMALIZATION_INDEX.json','ENDPOINT_BINDINGS.json']:
   if (C/n).exists():shutil.copyfile(C/n,build/'control'/n)
  put(build/'DEPENDENCY_MAP.json',dependency_map());put(build/'EARLIER_NEW_OUTPUT_DEPENDENCIES.json',protected);put(build/'EXCLUSIONS.json',{'unchanged_historical_and_A06_A07_payloads':'Referenced via pinned existing freshly restored consumers; no redundant full download/repack','GPU_runtime_recreation':'Untested and excluded','new_recovery_fits':0,'next_stage':'A09 not started'})
  files=[ref(p)|{'path':str(p.relative_to(build))} for p in sorted(build.rglob('*')) if p.is_file()];put(build/'MEMBER_MANIFEST.json',{'files':files,'schema':'pod-a-A08-members-v2'});archive.parent.mkdir(exist_ok=True);t=time.monotonic()
  with tarfile.open(archive,'w:gz',compresslevel=1) as tf:
   for p in sorted(build.rglob('*')):
    if p.is_file():tf.add(p,arcname=name+'/'+str(p.relative_to(build)),recursive=False)
  comp=time.monotonic()-t;key=f'POD_A/{R.name}/A08/{C.name}/{label}-checkpoint-001/'+archive.name;assert not api.file_exists(REPO,key,repo_type='dataset');t=time.monotonic();up=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect A08 '+label+' independently verified outputs');upload=time.monotonic()-t;put(upfile,{'revision':up.oid,'path':key,'sha256':sha(archive),'bytes':archive.stat().st_size,'member_manifest_sha256':sha(build/'MEMBER_MANIFEST.json'),'compression_seconds':comp,'upload_seconds':upload})
 up=read(upfile);freshbase=REC/(label+'-fresh-001');assert not freshbase.exists(),'Preserve failed consumer and allocate explicit new recovery identity';t=time.monotonic();fresh=Path(hf_hub_download(REPO,up['path'],repo_type='dataset',revision=up['revision'],force_download=True,cache_dir=str(freshbase/'new-cache')));assert fresh.stat().st_size==up['bytes'] and sha(fresh)==up['sha256'];download=time.monotonic()-t;consumer=freshbase/'consumer';num,verifytime=safe_extract(fresh,consumer);assert sha(consumer/'MEMBER_MANIFEST.json')==up['member_manifest_sha256'];env={k:v for k,v in os.environ.items() if not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
 script='restore_audit8.py' if kind=='audit' else 'restore_contrasts8.py';argv=[cfg['cpu_venv']+'/bin/python','-B',str(consumer/'artifacts/code'/script),'--root',str(consumer),'--dependency-map',str(consumer/'DEPENDENCY_MAP.json')]+(['--task',task] if kind=='audit' else ['--kind',kind,'--label',label]);t=time.monotonic()
 def bound():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 result=subprocess.run(argv,cwd=consumer,env=env,preexec_fn=bound,capture_output=True,text=True);atomic(C/('RESTORE_'+label+'.stdout.json'),result.stdout.encode());atomic(C/('RESTORE_'+label+'.stderr.log'),result.stderr.encode());assert result.returncode==0,'Preserve checkpoint and diagnose portable recovery failure';checks=json.loads(result.stdout);assert checks['status']=='PASS' and api.repo_info(REPO,repo_type='dataset').private
 files=read(consumer/'MEMBER_MANIFEST.json')['files'];assert {str(p.relative_to(consumer)) for p in consumer.rglob('*') if p.is_file()}=={e['path'] for e in files}|{'MEMBER_MANIFEST.json'}
 receipt={'status':'PASS','kind':kind,'label':label,'task':task,'repository':REPO,'revision':up['revision'],'archive_path':up['path'],'archive_sha256':up['sha256'],'archive_bytes':up['bytes'],'member_manifest_sha256':up['member_manifest_sha256'],'all_files_verified':num,'fresh_download':True,'force_download':True,'consumer_root':str(consumer),'restored_computation':checks,'restore_command':argv,'private_at_write_and_closeout':True,'inherited_dependencies_new_download':False,'producer_substitution':False,'compression_seconds':up['compression_seconds'],'upload_seconds':up['upload_seconds'],'fresh_download_seconds':download,'all_member_verification_seconds':verifytime,'recovery_computation_seconds':time.monotonic()-t,'completed_utc':now()};put(proof,receipt)
 for e in files:
  if e['path'].startswith('artifacts/'):
   original=str(A/e['path'].removeprefix('artifacts/'))
   if original not in protected['files']:protected['files'][original]={'repository':REPO,'revision':up['revision'],'archive_path':up['path'],'archive_sha256':up['sha256'],'member':e['path'],'bytes':e['bytes'],'sha256':e['sha256'],'consumer_root':str(consumer)}
 put(C/'PROTECTED_OBJECTS.json',protected);return receipt
if __name__=='__main__':r=main(sys.argv[1],sys.argv[2],sys.argv[3] if len(sys.argv)>3 else None);print(json.dumps({k:r[k] for k in ['status','label','revision','all_files_verified']}))
