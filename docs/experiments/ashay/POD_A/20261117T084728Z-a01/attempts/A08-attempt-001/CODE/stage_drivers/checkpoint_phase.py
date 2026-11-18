"""Append-only independent-audit checkpoints with force-fresh full-member recovery."""
from common import *
import argparse,shutil,tarfile,time
from huggingface_hub import HfApi,hf_hub_download
repo='ashay-sriv/undo-evo2-pilot-backup-20261020'
def main(phase):
 api=HfApi();assert api.repo_info(repo,repo_type='dataset').private;name='A08-'+phase+'-checkpoint-001';build=A/'checkpoint-builds'/name;assert not build.exists(),'Reconcile existing immutable checkpoint rather than overwrite';build.mkdir(parents=True);deps={'A06_archives':{},'A07_archives':{},'A06_consumer_roots':{},'A07_consumer_roots':{},'A08_candidate_consumers':{}}
 aliases=[phase] if phase in ['R4','R6'] else ['R4','R6']
 for alias in aliases:
  b=read(C.parent/'A06-attempt-001'/('BACKUP_'+alias+'_other_five.json'));root=Path(b['CPU_restored_checks']['root']);assert sha(root/'MEMBER_MANIFEST.json')==b['member_manifest_sha256'];deps['A06_archives'][alias]=b;deps['A06_consumer_roots'][alias]=str(root)
  for task in ['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']:
   b=read(C.parent/'A07-attempt-001'/('BACKUP_'+alias+'_'+task+'.json'));root=Path(b['CPU_restored_checks']['new_A07_consumer']);assert sha(root/'MEMBER_MANIFEST.json')==b['member_manifest_sha256'];deps['A07_archives'][alias+'/'+task]=b;deps['A07_consumer_roots'][alias+'/'+task]=str(root)
 if phase in ['R4','R6']:
  audits=list((A/'audits'/phase).glob('*/*/seed*/COMPLETE.json'));refits=list((A/'refits'/phase).glob('*/*/seed*/COMPLETE.json'));assert len(audits)==390 and len(refits)==30
  for p in audits+refits:
   j=read(p);assert j['status']=='PASS'
   for e in j['files']:q=p.parent/e['path'];assert sha(q)==e['sha256'] and q.stat().st_size==e['bytes']
  shutil.copytree(A/'audits'/phase,build/'artifacts/audits'/phase);shutil.copytree(A/'refits'/phase,build/'artifacts/refits'/phase)
 else:
  assert phase=='analysis';pairs=list((A/'analysis/R6_minus_R4').glob('*/*/*/seed*/COMPLETE.json'));lms=list((A/'analysis/LM_R6_minus_R4').glob('*/*/COMPLETE.json'));assert len(pairs)==546 and len(lms)==7;shutil.copytree(A/'analysis',build/'artifacts/analysis')
  for alias in ['R4','R6']:b=read(C/('BACKUP_'+alias+'.json'));deps['A08_candidate_consumers'][alias]=b['fresh_consumer_root']
 for key in ['A06_consumer_roots','A07_consumer_roots']:
  for label,path in deps[key].items():
   root=Path(path);proof=C/('DEPENDENCY_CONSUMER_'+digest(path)[:16]+'.json')
   if not proof.exists():
    mm=read(root/'MEMBER_MANIFEST.json')
    for e in mm['files']:p=root/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
    put(proof,{'status':'PASS','root':path,'member_manifest_sha256':sha(root/'MEMBER_MANIFEST.json'),'all_members_verified':len(mm['files']),'reused_immutable_consumer':True,'new_download':False,'observed_utc':now()})
 shutil.copytree(A/'code',build/'artifacts/code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(A/'source-versions',build/'artifacts/source-versions');shutil.copytree(A/'stage_drivers',build/'artifacts/stage_drivers',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(C/'prompt',build/'control/prompt')
 for p in C.glob('*.json'):
  if p.name.startswith('PRIOR_CURRENT_'):continue
  shutil.copyfile(p,build/'control'/p.name)
 for n in ['PROTOCOL_FROZEN.json','COVERAGE_PLAN.json']:dest=build/'control/inherited-A05'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(D.parent/'A05-attempt-001'/n,dest)
 for n in ['RESTORE_VALIDATION.json','BACKUP_VERIFICATION.json']:shutil.copyfile(C03/n,build/'control'/('A03_'+n))
 put(build/'DEPENDENCIES.json',deps);put(build/'EXCLUSIONS.json',{'GPU_model_weights_runtime':'Excluded. No GPU recreation claimed. Exact native/tensor/config/tokenizer/qualified runtime identities are in immutable A04/A06 dependency archives.','unchanged_history_and_features':'Referenced through exact A03/A06/A07 immutable archive revision/member hashes and existing reverified fresh consumers; not repacked.','derived_independent_reference_caches':'Regenerable from frozen historical probabilities, draws, source and protocol. All new target/paired audit distributions and analysis distributions are included.','scope':'Independent A08 audits/refits or predeclared contrasts; no new production head fitting or A09 execution'})
 files=[{'path':str(p.relative_to(build)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(build.rglob('*')) if p.is_file()];put(build/'MEMBER_MANIFEST.json',{'files':files,'self_excluded':True});mh=sha(build/'MEMBER_MANIFEST.json');archive=A/'archives'/(name+'.tar.gz');archive.parent.mkdir(exist_ok=True);t=time.monotonic()
 with tarfile.open(archive,'w:gz',compresslevel=1) as tf:tf.add(build,arcname=name)
 compression=time.monotonic()-t;ah=sha(archive);key=f'POD_A/{R.name}/A08/{C.name}/{phase}-checkpoint-001/'+archive.name;assert not api.file_exists(repo,key,repo_type='dataset');t=time.monotonic();up=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=repo,repo_type='dataset',commit_message='Protect POD_A A08 '+phase+' independent verification and recovery');upload=time.monotonic()-t;put(C/('UPLOADED_'+phase+'.json'),{'revision':up.oid,'path':key,'sha256':ah,'bytes':archive.stat().st_size});freshbase=Path(cfg['recovery'])/(phase+'-fresh-001');assert not freshbase.exists();t=time.monotonic();fresh=Path(hf_hub_download(repo,key,repo_type='dataset',revision=up.oid,force_download=True,cache_dir=str(freshbase/'cache')));assert sha(fresh)==ah and fresh.stat().st_size==archive.stat().st_size;download=time.monotonic()-t;consumer=freshbase/'consumer';consumer.mkdir();t=time.monotonic()
 with tarfile.open(fresh) as tf:
  members=tf.getmembers();actual=[]
  for m in members:
   p=Path(m.name);assert not p.is_absolute() and '..' not in p.parts and p.parts[0]==name and not m.issym() and not m.islnk() and (m.isfile() or m.isdir())
   if m.isfile():actual.append(str(p.relative_to(name)))
  assert len(actual)==len(set(actual)) and set(actual)=={e['path'] for e in files}|{'MEMBER_MANIFEST.json'};tf.extractall(consumer,filter='data')
 root=consumer/name;assert sha(root/'MEMBER_MANIFEST.json')==mh
 for e in files:q=root/e['path'];assert q.stat().st_size==e['bytes'] and sha(q)==e['sha256']
 verify=time.monotonic()-t;argv=[cfg['cpu_venv']+'/bin/python',str(root/'artifacts/code/restore_audit.py'),'--root',str(root)]+(['--candidate',phase] if phase in ['R4','R6'] else ['--analysis']);env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':''};run=subprocess.run(argv,env=env,text=True,capture_output=True);(C/('RESTORE_'+phase+'.stdout.json')).write_text(run.stdout);(C/('RESTORE_'+phase+'.stderr.log')).write_text(run.stderr);assert run.returncode==0,'Portable A08 recovery failed; preserve all evidence';checks=json.loads(run.stdout);assert checks['status']=='PASS' and api.repo_info(repo,repo_type='dataset').private
 proof={'schema':'pod-a-a08-private-checkpoint-v1','status':'PASS','phase':phase,'repository':repo,'private_at_write_and_closeout':True,'revision':up.oid,'archive_path':key,'archive_sha256':ah,'archive_bytes':archive.stat().st_size,'member_manifest_sha256':mh,'all_files_verified':len(files)+1,'fresh_download':True,'force_download':True,'fresh_consumer_root':str(root),'safe_exact_member_set':True,'portable_CPU_checks':checks,'restore_command':argv,'original_producer_paths_substituted':False,'compression_seconds':compression,'upload_seconds':upload,'fresh_download_seconds':download,'all_member_verification_seconds':verify,'completed_utc':now()};put(C/('BACKUP_'+phase+'.json'),proof);print(json.dumps({'status':'PASS','phase':phase,'revision':up.oid,'bytes':archive.stat().st_size,'members':len(files)+1}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['R4','R6','analysis'],required=True);main(p.parse_args().phase)
