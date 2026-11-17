"""Seal/fresh-restore bounded A03 evidence; inherited archives remain exact external dependencies."""
from pathlib import Path,PurePosixPath
import argparse,datetime,hashlib,json,os,shutil,subprocess,tarfile,time,uuid
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 p=Path(p);p.parent.mkdir(exist_ok=True,parents=True);t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');os.replace(t,p)
def jread(p):return json.loads(Path(p).read_text())
def safe(s):
 p=PurePosixPath(s)
 if p.is_absolute() or '..' in p.parts or not p.parts:raise ValueError('Unsafe checkpoint path')
 return str(p)
def main(control):
 c=Path(control).resolve();cfg=jread(c/'RUN_CONFIG.json');a=Path(cfg['artifacts']);rec=Path(cfg['recovery']);started=time.monotonic();cpu=time.process_time();stamp=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat();job={'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_utc':stamp(),'command_fingerprint':hashlib.sha256(('a03_checkpoint.py --control '+str(c)).encode()).hexdigest(),'source_sha256':sha(__file__),'status':'RUNNING'};put(c/'CHECKPOINT_JOB.json',job)
 prefix=f"POD_A/{cfg['run_id']}/A03/{cfg['attempt_id']}/checkpoint-001";repo='ashay-sriv/undo-evo2-pilot-backup-20261020';api=HfApi();assert api.repo_info(repo,repo_type='dataset').private
 payload=a/'checkpoint-build-001'/'A03-checkpoint-001';assert not payload.exists();payload.mkdir(parents=True)
 shutil.copytree(a/'publication',payload/'public');shutil.copytree(a/'audit_code',payload/'audit_code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(a/'a04-training-only',payload/'a04-training-only')
 control_names=['RUN_CONFIG.json','APPROVAL_RECORD.json','PACKAGE_VALIDATION.json','RECENT_FILE_SELECTION.json','A02_INPUT_VERIFICATION.json','BUDGET_SUPERSESSION.json','RECOVERY_DEPENDENCIES.json','PATH_TRANSLATION.json','RESTORE_VALIDATION.json','CPU_ENVIRONMENT.json','NUMERICAL_RECOVERY_PLAN.json','REPRESENTATIVE_RECOVERY_INPUTS.json','HISTORICAL_COUNT_RECONCILIATION.json','SMOKE_EXECUTION_SOURCE_RECOVERY.json','SCHEMA_DIAGNOSIS_001.json','SCHEMA_DIAGNOSIS_002.json','RECOVERY_EVENTS.jsonl','AUDIT_EVENTS.jsonl']
 control_names += [p.name for p in c.glob('PAYLOAD_CHECKSUMS_*.json')]+[p.name for p in c.glob('MEMBERS_*.json')]
 (payload/'control').mkdir()
 for name in control_names:shutil.copyfile(c/name,payload/'control'/name)
 for folder in ['recent-upload','accepted-a02','source-receipts']:shutil.copytree(c/folder,payload/'control'/folder)
 put(payload/'EXCLUSIONS.json',{'excluded':['All model weights/checkpoint objects','Installed CPU/GPU runtime/credential and account stores','Large inherited scientific features/heads/predictions/draws, referenced by exact immutable archive identity','A02 raw provider caches; already sealed in A02 checkpoint','Untouched test data; training bundle contains only12previously authorized train rows'],'inherited_dependencies':'public/RECOVERY_DEPENDENCIES.json','stage_scope':'A03 only; no A04 executor/approval'})
 files=[]
 for p in sorted(payload.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():files.append({'path':str(p.relative_to(payload)),'bytes':p.stat().st_size,'sha256':sha(p)})
 manifest={'schema':'pod-a-a03-private-member-manifest-v1','files':files,'file_count':len(files),'self_hash_rule':'MEMBER_MANIFEST.json is excluded from its own file list; exact self identity is anchored by archive hash/remote LFS and post-upload receipt','inherited_science':'Four separately pinned archives, all bytes freshly downloaded/verified in this A03; not repackaged in this bounded checkpoint'};put(payload/'MEMBER_MANIFEST.json',manifest);manifest_sha=sha(payload/'MEMBER_MANIFEST.json')
 archive=a/'a03-checkpoint-001.tar.gz';assert not archive.exists()
 with tarfile.open(archive,'w:gz',compresslevel=6) as tf:tf.add(payload,arcname=payload.name,recursive=True)
 ah=sha(archive);size=archive.stat().st_size;assert size<100*1024**2;sidecar=a/'a03-checkpoint-001.tar.gz.sha256';sidecar.write_text(ah+'  '+archive.name+'\n');put(c/'CHECKPOINT_UPLOAD_PLAN.json',{'remote_prefix':prefix,'files':len(files)+1,'compressed_bytes':size,'sha256':ah,'member_manifest_sha256':manifest_sha,'created_utc':stamp(),'no_large_archive_repack':True})
 remote_files=[(archive,prefix+'/'+archive.name),(sidecar,prefix+'/'+sidecar.name)]
 for _,remote in remote_files:assert not api.file_exists(repo,remote,repo_type='dataset')
 # The unique prefix is additive; parent guards prevent silently displacing concurrent updates.
 head=api.repo_info(repo,repo_type='dataset').sha
 result=api.create_commit(repo_id=repo,repo_type='dataset',operations=[CommitOperationAdd(path_in_repo=p,path_or_fileobj=str(local)) for local,p in remote_files],commit_message='Seal POD_A A03 historical CPU recovery and training-only handoff',parent_commit=head)
 revision=result.oid;put(c/'CHECKPOINT_UPLOADED.json',{'repository':repo,'revision':revision,'archive_path':remote_files[0][1],'archive_bytes':size,'archive_sha256':ah,'member_manifest_sha256':manifest_sha,'uploaded_utc':stamp()})
 cache=rec/'checkpoint-fresh-consumer-cache-001';assert not cache.exists();fresh=Path(hf_hub_download(repo,remote_files[0][1],repo_type='dataset',revision=revision,cache_dir=str(cache),force_download=True));fresh_side=Path(hf_hub_download(repo,remote_files[1][1],repo_type='dataset',revision=revision,cache_dir=str(cache),force_download=True));assert fresh.stat().st_size==size and sha(fresh)==ah and fresh_side.read_text().split()[0]==ah
 consumer=rec/'checkpoint-fresh-consumer-001';assert not consumer.exists();consumer.mkdir();seen=set();total=0;member_names=set()
 with tarfile.open(fresh,'r:gz') as tf:
  for m in tf:
   n=safe(m.name);assert n not in seen;seen.add(n);assert PurePosixPath(n).parts[0]==payload.name;assert m.isdir() or m.isfile();assert m.size<100*1024**2;total+=m.size;assert total<250*1024**2
   if m.isfile():member_names.add(str(PurePosixPath(*PurePosixPath(n).parts[1:])))
  assert member_names=={e['path'] for e in files}|{'MEMBER_MANIFEST.json'}
  for m in tf.getmembers():
   dst=consumer/safe(m.name);assert dst.resolve().is_relative_to(consumer)
   if m.isdir():dst.mkdir(parents=True,exist_ok=True)
   else:
    dst.parent.mkdir(parents=True,exist_ok=True)
    with tf.extractfile(m) as inp,dst.open('xb') as out:shutil.copyfileobj(inp,out)
 restored=consumer/payload.name;assert sha(restored/'MEMBER_MANIFEST.json')==manifest_sha;fm=jread(restored/'MEMBER_MANIFEST.json');assert fm==manifest
 for e in fm['files']:
  p=restored/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
 env={**os.environ,'PYTHONPATH':str(restored/'audit_code'),'CUDA_VISIBLE_DEVICES':'','OPENBLAS_NUM_THREADS':'4','OMP_NUM_THREADS':'4','MKL_NUM_THREADS':'4'};cp=subprocess.run(['/workspace/venvs/a03-cpu-audit-20261117/bin/python',str(restored/'audit_code/a03_representative.py'),'--root',str(restored)],env=env,text=True,capture_output=True);(c/'FRESH_REPRESENTATIVE_STDOUT.json').write_text(cp.stdout);(c/'FRESH_REPRESENTATIVE_STDERR.log').write_text(cp.stderr);assert cp.returncode==0,'Representative restored computation failed; logs preserved';representative=json.loads(cp.stdout);assert representative['status']=='PASS';privacy=api.repo_info(repo,repo_type='dataset').private;assert privacy
 report={'schema':'pod-a-a03-backup-verification-v1','status':'PASS','repository':repo,'repository_type':'dataset','private_at_write':True,'private_at_closeout':privacy,'revision':revision,'archive_path':remote_files[0][1],'sidecar_path':remote_files[1][1],'archive_bytes':size,'archive_sha256':ah,'fresh_download':True,'force_download':True,'new_consumer_and_cache':True,'all_included_files_verified':len(files)+1,'payload_files':len(files),'checksum_manifest_self_sha256':manifest_sha,'exact_member_set':True,'safe_restore':'PASS; no links/devices/traversal/duplicate normalized names','fresh_consumer_root':str(restored),'representative_reconstruction':representative,'inherited_archive_bytes_repacked':0,'inherited_dependencies':'RECOVERY_DEPENDENCIES.json, four immutable archives; representative reads their already freshly retrieved/verified local payloads','exclusions':jread(payload/'EXCLUSIONS.json')['excluded'],'scope':'All new checkpoint bytes and one restored-code/mapping saved-head reconstruction; no fullA09 or GPU reproduction','post_upload_receipt_rule':'This verification/delivery receipt is produced after sealing/upload; it is published separately, outside the archive self-hash cycle','wall_seconds':time.monotonic()-started,'cpu_process_seconds':time.process_time()-cpu,'completed_utc':stamp(),'source_sha256':sha(__file__)};put(c/'BACKUP_VERIFICATION.json',report);put(a/'audits/BACKUP_VERIFICATION.json',report);job.update(status='EXITING_SUCCESS',completed_utc=stamp());put(c/'CHECKPOINT_JOB.json',job);print(json.dumps({k:report[k] for k in ['status','revision','archive_bytes','archive_sha256','all_included_files_verified','wall_seconds']}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);a=p.parse_args();main(a.control)
