"""Five immutable R5 task checkpoints with fresh exact-member consumer recovery."""
from common7 import *
from archive7 import safe_extract
from huggingface_hub import HfApi,hf_hub_download
import shutil,tarfile,time,re

def ref(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def main(task):
 guard();assert task in TASKS[1:];api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private
 proof=C/('BACKUP_R5_'+task+'.json')
 if proof.exists():assert read(proof)['status']=='PASS';return read(proof)
 name='A07-R5-'+task+'-checkpoint-001';build=A/'checkpoint-builds'/name;archive=A/'archives'/(name+'.tar.gz');uploaded=C/('UPLOADED_R5_'+task+'.json');dep=read(C/'REUSED_A06_FEATURE_CONSUMER.json')
 if not uploaded.exists():
  assert not build.exists(),'Preserve prior failed build and reconcile before retry';build.mkdir(parents=True)
  units=[e for e in read(C/'A07_EXECUTION_MANIFEST.json')['units'] if e['task']==task];assert len(units)==78
  deps={'base_heads':{},'reference_predictions':{},'saved_folds':{},'A06_feature_dependency':dep,'producer_path_substitution':False}
  def copy_dependency(p,relative,expected=None):
   p=Path(p);h=sha(p)
   if expected:assert h==expected
   target=build/relative;target.parent.mkdir(parents=True,exist_ok=True)
   if not target.exists():shutil.copyfile(p,target)
   assert sha(target)==h;return ref(target)|{'path':relative,'original_sha256':h}
  for u in units:
   uid=u['unit_id'];root=A/'probes'/uid;j=read(root/'COMPLETE.json');assert j['status']=='COMPLETE_UNVERIFIED' and j['producer_validation']=='PASS'
   assert {e['path'] for e in j['files']}=={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p.name!='COMPLETE.json'}
   for e in j['files']:assert (root/e['path']).stat().st_size==e['bytes'] and sha(root/e['path'])==e['sha256']
   shutil.copytree(root,build/'artifacts/probes'/uid)
   key=u['representation'];seed=u['seed'];identity=u['identity'];base=identity['original_base_head'];deps['base_heads'][key+'/seed'+str(seed)]=copy_dependency(base['path'],f'dependencies/base-heads/{key}/seed{seed}/base.joblib',base['sha256'])
   fold=identity['fold'];deps['saved_folds'][str(seed)]=copy_dependency(fold['path'],f'dependencies/folds/seed{seed}.json',fold['sha256'])
   draw=identity['draw'];deps['saved_draws']=copy_dependency(draw['path'],'dependencies/dev_resampling.npz',draw['sha256'])
   result=read(root/'RESULTS.json');refs={}
   for r in result['reference_map']:
    d=r['prediction'];short=r['reference'];relative=f'dependencies/predictions/{key}/seed{seed}/{short}.npz';obj=copy_dependency(d['path'],relative,d['sha256']);obj['selectors']={**refs.get(short,{}).get('selectors',{}),r['policy']:d['array_selector']};obj['reference']=short;refs[short]=obj
    dr=r['distribution_receipt'];drroot=Path(dr['path']).parent;dj=read(drroot/'COMPLETE.json');assert sha(drroot/'COMPLETE.json')==dr['sha256']
    dest=build/'artifacts/reference-distributions'/drroot.name
    if not dest.exists():
     for e in dj['files']:assert sha(drroot/e['path'])==e['sha256']
     shutil.copytree(drroot,dest)
   deps['reference_predictions'][key+'/seed'+str(seed)]=list(refs.values())
  for split in ['train','dev']:
   for filename in ['COMPLETE.json','metadata.npz']:copy_dependency(A/'cache/R5'/task/split/filename,f'artifacts/cache/R5/{task}/{split}/{filename}')
  shutil.copytree(A/'code',build/'artifacts/code',ignore=shutil.ignore_patterns('__pycache__'))
  shutil.copytree(C/'package',build/'control/package')
  for filename in ['RUN_CONFIG.json','APPROVAL_RECORD.json','A07_INPUTS.json','A07_EXECUTION_MANIFEST.json','CPU_SOURCE_IDENTITY.json','ADAPTER_VALIDATION.json','INITIAL_PRODUCTION_GATE.json','A08_AUDIT_HANDOFF_PLAN.json','RECOVERY_PANEL.json','EXPECTED_TABLE_KEYS.json','REUSED_A06_FEATURE_CONSUMER.json','ENVIRONMENT_CHECK.json']:copy_dependency(C/filename,'control/'+filename)
  put(build/'DEPENDENCIES.json',deps);put(build/'EXCLUSIONS.json',{'A06_features':'Reused pinned fresh consumer; no new download, no cache repack','GPU_runtime_recreation':'Untested and excluded; no GPU work','independent_full_grid_audit':'Pending separate A08 approval','derived_feature_cache':'Only metadata and seals included; matrices rebuild from A06 chunks'})
  files=[ref(p)|{'path':str(p.relative_to(build))} for p in sorted(build.rglob('*')) if p.is_file()];put(build/'MEMBER_MANIFEST.json',{'schema':'pod-a-a07-task-members-v2','files':files});archive.parent.mkdir(exist_ok=True);t=time.monotonic()
  with tarfile.open(archive,'w:gz',compresslevel=1) as tf:
   for p in sorted(build.rglob('*')):
    if p.is_file():tf.add(p,arcname=name+'/'+str(p.relative_to(build)),recursive=False)
  compression=time.monotonic()-t;key=f'POD_A/{R.name}/A07/{C.name}/R5/{task}-checkpoint-001/'+archive.name;assert not api.file_exists(REPO,key,repo_type='dataset');t=time.monotonic();up=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect R5 A07 '+task+' producer checkpoint');upload=time.monotonic()-t
  put(uploaded,{'repository':REPO,'revision':up.oid,'path':key,'sha256':sha(archive),'bytes':archive.stat().st_size,'member_manifest_sha256':sha(build/'MEMBER_MANIFEST.json'),'compression_seconds':compression,'upload_seconds':upload})
 up=read(uploaded);freshbase=REC/('R5-'+task+'-fresh-001');assert not freshbase.exists(),'Preserve failed consumer and explicitly reconcile new recovery identity';t=time.monotonic();fresh=Path(hf_hub_download(REPO,up['path'],repo_type='dataset',revision=up['revision'],force_download=True,cache_dir=str(freshbase/'cache')));assert fresh.stat().st_size==up['bytes'] and sha(fresh)==up['sha256'];download=time.monotonic()-t;consumer=freshbase/'consumer';num,verifytime=safe_extract(fresh,consumer);assert sha(consumer/'MEMBER_MANIFEST.json')==up['member_manifest_sha256']
 depmap={'A06_feature_consumer':dep['consumer_root'],'member_manifest_sha256':dep['member_manifest_sha256'],'repository':REPO,'revision':dep['revision'],'archive_path':dep['archive_path'],'archive_sha256':dep['archive_sha256'],'new_download':False};put(freshbase/'DEPENDENCY_MAP.json',depmap)
 env={k:v for k,v in os.environ.items() if not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4',PYTHONDONTWRITEBYTECODE='1');argv=[cfg['cpu_venv']+'/bin/python','-B',str(consumer/'artifacts/code/restore7.py'),'--root',str(consumer),'--dependency-map',str(freshbase/'DEPENDENCY_MAP.json'),'--task',task];t=time.monotonic();result=subprocess.run(argv,cwd=consumer,env=env,capture_output=True,text=True);atomic(C/('RESTORE_R5_'+task+'.stdout.json'),result.stdout.encode());atomic(C/('RESTORE_R5_'+task+'.stderr.log'),result.stderr.encode());assert result.returncode==0,'Portable consumer failed; preserve uploaded checkpoint and diagnose';checks=json.loads(result.stdout);assert checks['status']=='PASS' and len(checks['checks'])==12 and checks['paired_vectors']==240 and api.repo_info(REPO,repo_type='dataset').private
 receipt={'schema':'pod-a-a07-task-backup-v2','status':'PASS','task':task,'candidate':'R5','repository':REPO,'revision':up['revision'],'archive_path':up['path'],'archive_sha256':up['sha256'],'archive_bytes':up['bytes'],'member_manifest_sha256':up['member_manifest_sha256'],'all_files_verified':num,'fresh_download':True,'force_download':True,'consumer_root':str(consumer),'CPU_restored_checks':checks,'restore_command':argv,'private_at_write_and_closeout':True,'inherited_feature_dependency':depmap,'inherited_dependency_new_download':False,'producer_path_substitution':False,'compression_seconds':up['compression_seconds'],'upload_seconds':up['upload_seconds'],'fresh_download_seconds':download,'all_member_verification_seconds':verifytime,'restore_check_seconds':time.monotonic()-t,'completed_utc':now()};put(proof,receipt);return receipt
if __name__=='__main__':print(json.dumps(main(sys.argv[1]),allow_nan=False))
