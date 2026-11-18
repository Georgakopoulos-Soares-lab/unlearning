"""Two finite private R5 scientific checkpoints, exact-member/fresh CPU recovery."""
from common6 import *
import shutil,tarfile,re,time,resource,fcntl
from huggingface_hub import HfApi,hf_hub_download
def copy(src,dst):
 src=Path(src);dst=Path(dst);assert src.is_file() and not src.is_symlink();dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(dst)==sha(src)
def safe_extract(archive,destination):
 dest=Path(destination);assert not dest.exists();t=time.monotonic()
 with tarfile.open(archive) as tf:
  members=tf.getmembers();names=set();roots=set()
  for m in members:
   p=Path(m.name);assert m.isfile() and not m.issym() and not m.islnk() and not p.is_absolute() and '..' not in p.parts and '\\' not in m.name and str(p)==m.name and m.name not in names;names.add(m.name);roots.add(p.parts[0])
  assert len(roots)==1;root=next(iter(roots));manifest=json.load(tf.extractfile(root+'/MEMBER_MANIFEST.json'));expected={e['path']:e for e in manifest['files']};assert len(expected)==len(manifest['files']);assert {str(Path(m.name).relative_to(root)) for m in members}==set(expected)|{'MEMBER_MANIFEST.json'}
  # Validate all bytes before accepting extracted output; preserve failed consumer paths.
  dest.mkdir(parents=True)
  for m in members:
   rel=str(Path(m.name).relative_to(root));target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
   with tf.extractfile(m) as src,target.open('wb') as out:
    import hashlib
    h=hashlib.sha256();size=0
    while b:=src.read(8*1024**2):out.write(b);h.update(b);size+=len(b)
   if rel!='MEMBER_MANIFEST.json':assert h.hexdigest()==expected[rel]['sha256'] and size==expected[rel]['bytes'],rel
 return len(members),time.monotonic()-t
def build(group,root):
 inp=read(C/'A06_INPUTS.json');env={k:v for k,v in os.environ.items() if not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};subprocess.run([cfg['cpu_venv']+'/bin/python',str(A/'code/slice_refs6.py'),group],check=True,env=env,stdout=subprocess.PIPE);units=[u for u in inp['extraction_units'] if (u['task']=='emp_H3')==(group=='H3')];art=root/'artifacts';assert not root.exists();root.mkdir(parents=True);slices=read(C/('FEATURE_SLICE_REFERENCES_R5_'+group+'.json'));maps={'stage':'A06','candidate':'R5','group':group,'producer_artifact_root':str(A),'mapping_kind':'External mapping only; original receipts remain unchanged','manifests':[],'selected_historical_dependencies':[],'source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'coverage_plan_sha256':cfg['coverage_plan_sha256']}
 for u in units:
  source=A/'features/R5'/u['task']/u['split'];bundle=read(source/'COMPLETE.json');assert bundle['status']=='PASS';shutil.copytree(source,art/'features/R5'/u['task']/u['split'],ignore=shutil.ignore_patterns('*.lock'));manifest=Path(u['manifest']['path']);copy(manifest,root/'manifests'/(u['task']+'__'+u['split']+'.jsonl'));maps['manifests'].append(u['manifest'])
  shutil.copytree(A/'lm/R5'/u['task']/u['split'],art/'lm/R5'/u['task']/u['split'])
 for job in (A/'features/R5/jobs').glob('*'):
  resource_file=job/'RESOURCE_MEASUREMENTS.json'
  if resource_file.is_file() and read(resource_file)['group']==group:shutil.copytree(job,art/'features/R5/jobs'/job.name,ignore=shutil.ignore_patterns('distributed_init'))
 if group=='H3':
  shutil.copytree(A/'h3/R5',art/'h3/R5',ignore=shutil.ignore_patterns('*.lock'));shutil.copytree(A/'audit-refits/R5',art/'audit-refits/R5');shutil.copytree(A/'parity/R5',art/'parity/R5',ignore=shutil.ignore_patterns('distributed_init'))
  for split in ['train','dev','test']:
   for name in ['COMPLETE.json','metadata.npz']:copy(A/'h3-cache/R5'/split/name,art/'h3-cache/R5'/split/name)
  H=Path('/workspace/recovery/POD_A')/cfg['run_id']/'A03-attempt-001/restored/base_R1/multiretain-layers-v1-final-20261110T140836Z';CT=H.parent.parent/'controls/benign-followup-v1'
  for key in ['decoder_layer_16','final_norm']:
   for seed in [42,17,1234]:
    src=H/'probes/H3/emp_H3'/key/('seed'+str(seed))/'base.joblib';dst=root/'dependencies/base-heads'/key/('seed'+str(seed))/'base.joblib';copy(src,dst);maps['selected_historical_dependencies'].append({'original_path':str(src),'member':str(dst.relative_to(root)),'sha256':sha(src),'prior_immutable_archive':'historical/base_R1 in A05 RECOVERY_DEPENDENCY_GRAPH'})
    for split in ['dev','test']:
     src=H/'probes/H3/emp_H3'/key/('seed'+str(seed))/(split+'_predictions.npz');dst=root/'dependencies/reference-predictions'/key/('seed'+str(seed))/src.name;copy(src,dst);maps['selected_historical_dependencies'].append({'original_path':str(src),'member':str(dst.relative_to(root)),'sha256':sha(src),'prior_immutable_archive':'historical/base_R1 in A05 RECOVERY_DEPENDENCY_GRAPH'})
  for control in ['composition','kmer4']:
   for seed in [42,17,1234]:
    for split in ['dev','test']:
     src=CT/'tasks/emp_H3'/('4mer' if control=='kmer4' else control)/('seed'+str(seed))/(split+'_predictions.npz');copy(src,root/'dependencies/control-predictions'/control/('seed'+str(seed))/src.name)
  for split in ['dev','test']:copy(H/'probes/H3/emp_H3'/(split+'_resampling.npz'),root/'dependencies/draws'/(split+'_resampling.npz'))
  for seed in [42,17,1234]:copy(H/'probes/H3/emp_H3'/('folds_seed'+str(seed)+'.json'),root/'dependencies/folds'/('folds_seed'+str(seed)+'.json'))
  pinned=[];nodes=read(D5/'RECOVERY_DEPENDENCY_GRAPH.json')['nodes']
  for dep,source in [('base_R1',H),('controls',CT)]:
   index=C.parent/'A03-attempt-001'/('PAYLOAD_CHECKSUMS_'+dep+'.json');node=next(n for n in nodes if n['id']=='historical/'+dep);expected=node['prior_A09_local_hash_proof']['member_index']['sha256'];assert sha(index)==expected;copy(index,root/'dependencies/source-indexes'/(dep+'.json'));entries={str(source/e['path']):e for e in read(index)['files']}
   # Determine original dependencies from the declared restored layout, not mutable summaries.
   for target in (root/'dependencies').rglob('*'):
    if not target.is_file() or 'source-indexes' in target.parts:continue
    rel=target.relative_to(root/'dependencies');src=None
    if dep=='base_R1':
     if rel.parts[0] in ['base-heads','reference-predictions']:src=source/'probes/H3/emp_H3'/Path(*rel.parts[1:])
     elif rel.parts[0] in ['draws','folds']:src=source/'probes/H3/emp_H3'/target.name
    elif rel.parts[0]=='control-predictions':src=source/'tasks/emp_H3'/('4mer' if rel.parts[1]=='kmer4' else rel.parts[1])/Path(*rel.parts[2:])
    if src is not None:
     original=entries[str(src)];assert target.stat().st_size==original['bytes'] and sha(target)==original['sha256'];pinned.append({'member':str(target.relative_to(root)),'historical_dependency':dep,'historical_member':original['path'],'bytes':original['bytes'],'sha256':original['sha256']})
   maps.setdefault('historical_archives',[]).append({'id':dep,'repository':node['repository'],'revision':node['revision'],'archive_path':node['remote_path'],'archive_bytes':node['bytes'],'archive_sha256':node['sha256'],'original_checksum_index_sha256':expected,'protected_checksum_index':'dependencies/source-indexes/'+dep+'.json'})
  put(root/'PINNED_HISTORICAL_DEPENDENCIES.json',{'status':'PASS','files':pinned,'old_archives_repacked':False,'scope':'Only exact dependencies needed by declared restored H3 panel, plus original checksum metadata; no hidden old-array substitution.'})
 shutil.copytree(A/'code',art/'code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(C/'package',root/'prompt-package');(root/'control').mkdir()
 for p in C.iterdir():
  if p.is_file() and p.suffix in ['.json','.md','.txt','.jsonl']:copy(p,root/'control'/p.name)
 copy(D4/'ENVIRONMENT_LOCK.json',root/'control/ORIGINAL_QUALIFIED_ENVIRONMENT_LOCK.json');copy(D4/'SOURCE_IDENTITY.json',root/'control/ORIGINAL_QUALIFIED_SOURCE_IDENTITY.json')
 put(root/'RESTORE_MAP.json',maps);put(root/'FEATURE_SLICE_REFERENCES.json',slices);put(root/'EXCLUSIONS.json',{'native_weights':'Excluded; exact all8 assets/native/model/config/tokenizer/provider/mirror refs in control/A06_INPUTS.json. Existing verified local payload reused; no weight repack.','installed_GPU_runtime':'Excluded; exact A04 environment/source lock refs retained. CPU recovery does not test rebuilding GPU runtime.','derived_H3_cache':'Excluded; reconstruct bit-for-bit float32 by concatenating included chunks without numerical transformation.','old_scientific_archives':'Not repacked; only declared small selected head/prediction/draw/fold dependencies included for self-contained H3 panel. Immutable original lineage retained.','other_stage_work':'No A07 heads/applications, other-five refits, adjacent/LM contrasts'});files=[]
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():
   assert p.suffix not in ['.distcp','.pt'];
   if p.suffix in ['.py','.json','.md','.txt','.patch']:assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)',p.read_bytes())
   files.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)})
 put(root/'MEMBER_MANIFEST.json',{'files':files,'self_excluded':True,'group':group,'science_scope':'R5 A06 only'});return len(files)+1
def main(group):
 guard();assert group in ['H3','other_five'];api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;name='R5_'+group;uploaded=C/('BACKUP_UPLOADED_'+name+'.json');total=time.monotonic()
 job={'status':'RUNNING','phase':'PRIVATE_CHECKPOINT_AND_FRESH_RECOVERY','group':group,'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'helper_source_sha256':sha(__file__),'scientific_source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'started_utc':now()};put(C/('BACKUP_JOB_'+name+'.json'),job)
 with (C/('backup-'+name+'.lock')).open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if uploaded.exists():entry=read(uploaded);assert entry['source_identity_sha256']==sha(C/'SOURCE_IDENTITY.json');archive=Path(entry['local_archive']);assert sha(archive)==entry['archive_sha256']
  else:
   root=A/('backup-'+name+'-build-001')/('A06-'+name+'-checkpoint-001');members=build(group,root);archive=A/('A06-'+name+'-checkpoint-001.tar.gz');assert not archive.exists();t=time.monotonic()
   with tarfile.open(archive,'w:gz',compresslevel=1) as tf:
    for p in sorted(root.rglob('*')):
     if p.is_file():tf.add(p,arcname=root.name+'/'+str(p.relative_to(root)),recursive=False)
   compression=time.monotonic()-t;key='POD_A/'+cfg['run_id']+'/A06/'+cfg['attempt_id']+'/R5/'+group+'-checkpoint-001/'+archive.name;assert not api.file_exists(REPO,key,repo_type='dataset');t=time.monotonic();u=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect verified R5 '+group+' A06 scientific evidence and finite CPU recovery panel');entry={'status':'UPLOADED_PENDING_FRESH_RECOVERY','repository':REPO,'revision':u.oid,'archive_path':key,'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive),'member_manifest_sha256':sha(root/'MEMBER_MANIFEST.json'),'members_expected':members,'source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'group':group,'local_archive':str(archive),'compression_seconds':compression,'upload_seconds':time.monotonic()-t};put(uploaded,entry)
  freshbase=REC/(name+'-fresh-001');assert not freshbase.exists(),'Preserve old consumer and explicitly allocate bounded recovery retry';freshbase.mkdir();t=time.monotonic();fresh=Path(hf_hub_download(REPO,entry['archive_path'],repo_type='dataset',revision=entry['revision'],force_download=True,cache_dir=str(freshbase/'brand-new-cache')));assert fresh.stat().st_size==entry['archive_bytes'] and sha(fresh)==entry['archive_sha256'];download=time.monotonic()-t;members,hash_seconds=safe_extract(fresh,freshbase/'consumer');assert members==entry['members_expected'];root=freshbase/'consumer';script=root/'artifacts/code/restore_panel6.py';argv=[cfg['cpu_venv']+'/bin/python','-I',str(script),'--root',str(root),'--group',group];env={k:v for k,v in os.environ.items() if not re.search(r'TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|AUTH_SOCK|CREDENTIAL',k,re.I)};env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',MKL_NUM_THREADS='4')
  def bound():resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
  t=time.monotonic();process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env,cwd=root,preexec_fn=bound);identity={'status':'RUNNING','pid':process.pid,'proc_start_ticks':Path('/proc/'+str(process.pid)+'/stat').read_text().split()[21],'argv':argv,'consumer_source_sha256':sha(script),'started_utc':now()};put(C/('RESTORE_JOB_'+name+'.json'),identity);stdout,stderr=process.communicate();identity.update(status='EXITED_PASS' if process.returncode==0 else 'EXITED_FAILED',exit_code=process.returncode,completed_utc=now());put(C/('RESTORE_JOB_'+name+'.json'),identity);(A/'logs'/('restore-'+name+'.stdout.log')).write_text(stdout);(A/'logs'/('restore-'+name+'.stderr.log')).write_text(stderr);assert process.returncode==0,'Fresh CPU recovery failed; see preserved logs';result=read(root/'FRESH_COMPUTATIONAL_RESTORE.json');assert result['status']=='PASS' and result['external_producer_paths_used'] is False;assert api.repo_info(REPO,repo_type='dataset').private;record=entry|{'status':'PASS','force_fresh_download':True,'empty_consumer':True,'fresh_consumer':str(root),'all_member_hashes_verified':members,'fresh_download_seconds':download,'all_member_validation_seconds':hash_seconds,'restored_computational_seconds':time.monotonic()-t,'restored_computation':result,'consumer_source_sha256':sha(script),'privacy_at_write_and_closeout':True,'no_GPU_runtime_recreation_claim':True,'total_wall_seconds':time.monotonic()-total,'completed_utc':now()};put(C/('BACKUP_'+name+'.json'),record);existing=[read(p) for p in C.glob('BACKUP_R5_*.json')];put(C/'BACKUP_VERIFICATION.json',{'status':'PASS' if len(existing)==2 else 'H3_PASS_REMAINING_FEATURE_CHECKPOINT_PENDING','checkpoints':existing,'new_scientific_archives_only':True,'weights_not_repacked':True,'GPU_runtime_recreation_tested':False});job.update(status='COMPLETED_AWAITING_PROCESS_EXIT',completed_utc=now());put(C/('BACKUP_JOB_'+name+'.json'),job);print(json.dumps({'status':'PASS','group':group,'revision':record['revision'],'archive_sha256':record['archive_sha256'],'members':members,'restored_paths':result['restored_policy_prediction_metric_paths']}))
if __name__=='__main__':main(sys.argv[1])
