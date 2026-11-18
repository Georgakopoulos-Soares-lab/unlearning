"""Append-only A07 task backup, full fresh readback and portable CPU recovery."""
from common import *
import argparse,shutil,tarfile,time
from huggingface_hub import HfApi,hf_hub_download
repo='ashay-sriv/undo-evo2-pilot-backup-20261020'
def main(alias,task):
 api=HfApi();assert api.repo_info(repo,repo_type='dataset').private;roots=list((A/'probes'/alias/task).glob('*/seed*/COMPLETE.json'));assert len(roots)==78
 for p in roots:
  j=read(p);assert j['status']=='COMPLETE_UNVERIFIED' and j['producer_validation']=='PASS'
  for e in j['files']:q=p.parent/e['path'];assert q.stat().st_size==e['bytes'] and sha(q)==e['sha256']
 name='A07-'+alias+'-'+task+'-checkpoint-001';build=A/'checkpoint-builds'/name;assert not build.exists(),'Reconcile immutable prior backup rather than overwrite';build.mkdir(parents=True)
 shutil.copytree(A/'probes'/alias/task,build/'artifacts/probes'/alias/task);shutil.copytree(A/'code',build/'artifacts/code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(A/'stage_drivers',build/'artifacts/stage_drivers',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(C/'prompt',build/'control/prompt')
 for p in C.glob('*.json'):
  if p.name.startswith('PRIOR_CURRENT_'):continue
  shutil.copyfile(p,build/'control'/p.name)
 shutil.copyfile(C/'A06_ACCEPTANCE_RECONCILIATION.md',build/'control/A06_ACCEPTANCE_RECONCILIATION.md');shutil.copyfile(C/'A06_PAIRED_CONTRASTS.normalized.v1.csv',build/'control/A06_PAIRED_CONTRASTS.normalized.v1.csv')
 manifest=read(C/'A07_EXECUTION_MANIFEST.json')
 for key in ['decoder_layer_16','final_norm']:
  u=next(u for u in manifest['units'] if u['unit_id']==f'{alias}/{task}/{key}/seed42');e=u['identity']['original_base_head'];assert sha(e['path'])==e['sha256'];dest=build/'dependencies/base-heads'/key/'base.joblib';dest.parent.mkdir(parents=True);shutil.copyfile(e['path'],dest)
 dep=read(C.parent/'A06-attempt-001'/('BACKUP_'+alias+'_other_five.json'));dep_root=Path(dep['CPU_restored_checks']['root']);assert sha(dep_root/'MEMBER_MANIFEST.json')==dep['member_manifest_sha256'];dep_manifest=read(dep_root/'MEMBER_MANIFEST.json');entries=dep_manifest['files'] if isinstance(dep_manifest,dict) else dep_manifest
 proof=C/('REUSED_A06_CONSUMER_'+alias+'.json')
 if not proof.exists():
  for e in entries:q=dep_root/e['path'];assert q.stat().st_size==e['bytes'] and sha(q)==e['sha256']
  put(proof,{'status':'PASS','reused_existing_fresh_consumer':str(dep_root),'archive_dependency':dep,'all_files_reverified':len(entries),'member_manifest_sha256':sha(dep_root/'MEMBER_MANIFEST.json'),'reverification_utc':now(),'new_download':False,'producer_substitution':False})
 else:assert read(proof)['member_manifest_sha256']==sha(dep_root/'MEMBER_MANIFEST.json')
 put(build/'DEPENDENCIES.json',{'A06_features':dep,'consumer_mapping':{'A06_features':str(dep_root)},'history':'A03 immutable dependency indexes and A06 receipt graph; unchanged payloads not repacked','CPU_source_identity':ref(C/'CPU_SOURCE_IDENTITY.json'),'A07_original_base_head_panel':'Two seed42 unchanged original-base heads included by exact A05/A03 digest'})
 put(build/'EXCLUSIONS.json',{'model_weights_and_GPU_runtime':'Excluded: no model recreation claimed. Exact reacquisition IDs, tensor/native/config/tokenizer/runtime hashes remain in A06 INPUTS and qualified A04 receipts. No GPU needed for this CPU recovery.','derived_caches':'Excluded: reconstruct same float32 arrays from verified A06 chunk dependencies','historical_payloads':'Referenced by immutable A03/A06 archive revision/hash; not repacked','A08':'Not started; all new units remain COMPLETE_UNVERIFIED'})
 files=[ref(p) | {'path':str(p.relative_to(build))} for p in sorted(build.rglob('*')) if p.is_file()];put(build/'MEMBER_MANIFEST.json',{'schema':'pod-a-a07-checkpoint-members-v1','files':files});mh=sha(build/'MEMBER_MANIFEST.json');archive=A/'archives'/(name+'.tar.gz');archive.parent.mkdir(exist_ok=True);t=time.monotonic()
 with tarfile.open(archive,'w:gz',compresslevel=1) as tf:tf.add(build,arcname=name)
 compression=time.monotonic()-t;ah=sha(archive);key=f'POD_A/{R.name}/A07/{C.name}/{alias}/{task}-checkpoint-001/'+archive.name;assert not api.file_exists(repo,key,repo_type='dataset');t=time.monotonic();up=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=repo,repo_type='dataset',commit_message='Protect POD_A A07 '+alias+' '+task+' producer-complete probes');upload=time.monotonic()-t;put(C/('UPLOADED_'+alias+'_'+task+'.json'),{'revision':up.oid,'path':key,'sha256':ah,'bytes':archive.stat().st_size})
 freshbase=Path(cfg['recovery'])/(alias+'-'+task+'-fresh-001');assert not freshbase.exists();t=time.monotonic();fresh=Path(hf_hub_download(repo,key,repo_type='dataset',revision=up.oid,force_download=True,cache_dir=str(freshbase/'cache')));assert sha(fresh)==ah;download=time.monotonic()-t;consumer=freshbase/'consumer';consumer.mkdir();t=time.monotonic()
 with tarfile.open(fresh) as tf:
  members=tf.getmembers();actual=[]
  for m in members:
   p=Path(m.name);assert not p.is_absolute() and '..' not in p.parts and p.parts[0]==name and not m.issym() and not m.islnk() and (m.isfile() or m.isdir())
   if m.isfile():actual.append(str(p.relative_to(name)))
  assert len(actual)==len(set(actual)) and set(actual)=={e['path'] for e in files}|{'MEMBER_MANIFEST.json'};tf.extractall(consumer,filter='data')
 root=consumer/name;assert sha(root/'MEMBER_MANIFEST.json')==mh
 for e in files:q=root/e['path'];assert q.stat().st_size==e['bytes'] and sha(q)==e['sha256']
 verifytime=time.monotonic()-t;env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':''};argv=[cfg['cpu_venv']+'/bin/python',str(root/'artifacts/code/restore_check.py'),'--root',str(root),'--features-root',str(dep_root),'--candidate',alias,'--task',task];result=subprocess.run(argv,env=env,text=True,capture_output=True);(C/('RESTORE_'+alias+'_'+task+'.stdout.json')).write_text(result.stdout);(C/('RESTORE_'+alias+'_'+task+'.stderr.log')).write_text(result.stderr);assert result.returncode==0,'Portable recovery failed; retain all local/remote evidence';checks=json.loads(result.stdout);assert checks['status']=='PASS' and len(checks['checks'])==4;assert api.repo_info(repo,repo_type='dataset').private
 proof={'schema':'pod-a-a07-task-backup-v1','status':'PASS','candidate':alias,'task':task,'repository':repo,'private_at_write_and_closeout':True,'revision':up.oid,'archive_path':key,'archive_sha256':ah,'archive_bytes':archive.stat().st_size,'member_manifest_sha256':mh,'all_files_verified':len(files)+1,'fresh_download':True,'force_download':True,'new_A07_consumer_and_cache':True,'safe_exact_member_set':True,'CPU_restored_checks':checks,'restore_command':argv,'producer_path_substitution':False,'reused_immutable_A06_consumer_receipt':ref(C/('REUSED_A06_CONSUMER_'+alias+'.json')),'compression_seconds':compression,'upload_seconds':upload,'fresh_download_seconds':download,'all_member_verification_seconds':verifytime,'completed_utc':now()};put(C/('BACKUP_'+alias+'_'+task+'.json'),proof);print(json.dumps({'status':'PASS','candidate':alias,'task':task,'revision':up.oid,'bytes':archive.stat().st_size,'members':len(files)+1,'restored_policy_paths':4}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',choices=['R4','R6'],required=True);p.add_argument('--task',required=True);v=p.parse_args();main(v.candidate,v.task)
