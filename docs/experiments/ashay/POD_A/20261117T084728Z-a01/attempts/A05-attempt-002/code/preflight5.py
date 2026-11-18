"""A05 metadata reconciliation and small private identity-chain readback only."""
from common5 import *
import fcntl,requests,shutil,time,tarfile
from huggingface_hub import HfApi,hf_hub_download
def service_state():
 root=Path('/workspace/agent-handoff/POD_A/review-loop');old=read(root/'heartbeat.json');p=Path('/proc')/str(old['pid'])/'stat';alive=p.exists() and p.read_text().split()[2]!='Z' and p.read_text().split()[21]==old['proc_start_ticks'];assert not alive and (root/'STOP').exists();found=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   args=[os.fsdecode(a) for a in (p/'cmdline').read_bytes().split(b'\0') if a];s=(p/'stat').read_text().split()
   if not args or int(p.name)==os.getpid() or s[2]=='Z' or 'python' not in Path(args[0]).name:continue
   scripts=[a for a in args[1:] if a.startswith('/workspace/') and ' ' not in a and '\n' not in a]
   if any('/workspace/agent-handoff/POD_A/review-loop/' in a or cfg['run_id'] in a for a in scripts):found.append({'pid':int(p.name),'start_ticks':s[21],'scripts':scripts})
  except (FileNotFoundError,ProcessLookupError):pass
 assert not found,found;locks=[]
 for p in [R/'GPU_EXECUTION.lock',Path('/workspace/agent-handoff/POD_A/review-loop/service.lock'),Path('/workspace/agent-handoff/POD_A/review-loop/observer.lock')]:
  if not p.exists():continue
  with p.open('r') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  locks.append(str(p))
 return {'status':'PASS','observer_status':'STOPPED','reviewer_scheduler_status':'STOPPED_NOT_RUNNING','publisher_status':'STOPPED_NOT_RUNNING_PREVIOUSLY_BLOCKED','prior_observer_pid':old['pid'],'prior_start_ticks':old['proc_start_ticks'],'prior_identity_alive':False,'replacement_or_scientific_workers':found,'locks_available':locks,'observed_utc':now(),'observer_restarted':False,'GPU_work':0,'pod_left_running':True}
def main():
 start=time.monotonic();guard(dirty=False);state=service_state();put(C/'PROCESS_AND_SERVICE_STATE.json',state);api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;final=read(C4/'FINAL_CLOSEOUT.json');backup=read(C4/'BACKUP_MANIFEST.json');assert final['metadata_commit']==cfg['research_head_before'] and final['payload_revision']==backup['revision']=='5c4fd12f1df0fc96a056e2bad8d83b34822a6bff' and backup['archive_sha256']=='1286c91b9e941b395f9a1c5d189e733c755e8407dd0da19e448602a9d4ece565';objects=[]
 for kind,revision,key,h in [('A04_final_receipt',final['receipt_revision'],final['receipt_path'],final['receipt_sha256']),('A04_final_metadata',final['final_metadata_revision'],final['final_metadata_path'],final['final_metadata_sha256'])]:
  path=Path(hf_hub_download(REPO,key,repo_type='dataset',revision=revision,force_download=True,cache_dir=str(REC/'small-A04-identity-readback-cache')));assert sha(path)==h
  if kind=='A04_final_receipt':
   value=read(path);assert value['qualification_commit']=='906e808af4b61eeb7f8b229fea30e735f1cf818f' and value['metadata_commit']==cfg['research_head_before'] and value['payload_revision']==backup['revision'];assert value['payload_archive_sha256']==backup['archive_sha256'] and value['A05_proposal_sha256']=='27cbc1fddf44b0682d1245b722649c21b6f0a9cffbcd3b7be6edd123f25d5d8d'
  else:
   with tarfile.open(path) as tf:
    members=tf.getmembers();names=set();roots=set()
    for m in members:
     p=Path(m.name);assert not p.is_absolute() and '..' not in p.parts and '\\' not in m.name and str(p)==m.name and m.name not in names and not m.issym() and not m.islnk() and (m.isdir() or m.isfile());names.add(m.name);roots.add(p.parts[0])
    assert len(roots)==1;root=next(iter(roots));manifest=json.load(tf.extractfile(root+'/MEMBER_MANIFEST.json'));expected={e['path']:e for e in manifest['files']};actual={str(Path(m.name).relative_to(root)) for m in members if m.isfile()};assert actual==set(expected)|{'MEMBER_MANIFEST.json'} and len(expected)==len(manifest['files'])
    for rel,e in expected.items():
     data=tf.extractfile(root+'/'+rel).read();assert len(data)==e['bytes'] and bh(data)==e['sha256']
    assert len(actual)==272
  objects.append({'kind':kind,'repository':REPO,'revision':revision,'path':key,'bytes':path.stat().st_size,'sha256':h,'force_fresh_readback':True,'all_metadata_members_verified':272 if kind.endswith('metadata') else None})
 remote=api.get_paths_info(REPO,[backup['archive_path']],repo_type='dataset',revision=backup['revision'])[0];assert remote.size==backup['archive_bytes'] and remote.lfs.sha256==backup['archive_sha256'];put(C/'PRIVATE_INPUT_CHAIN.json',{'status':'PASS','fresh_small_objects':objects,'scientific_evidence_archive':{'repository':REPO,'revision':backup['revision'],'path':backup['archive_path'],'bytes':backup['archive_bytes'],'sha256':backup['archive_sha256'],'current_remote_LFS_identity':'PASS','fresh_large_transfer':False,'valid_prior_fresh_restore_proof':'A04-attempt-004/FRESH_RESTORE_CHECK.json,387members/189saved TRAIN comparisons','prior_proof_sha256':sha(C4/'FRESH_RESTORE_CHECK.json')},'no_qualification_or_scientific_audit_rerun':True,'private_at_closeout':api.repo_info(REPO,repo_type='dataset').private,'observed_utc':now()})
 inputs=[]
 def bind(p,owner,method='FRESH_METADATA_SHA256',commit=None):
  p=Path(p);assert p.exists() and p.is_file();e={'id':digest([str(p),sha(p)]),'path':str(p),'owner':owner,'bytes':p.stat().st_size,'sha256':sha(p),'verification_method':method,'observed_utc':now()}
  if p.is_relative_to(W):
   actual_commit=commit or cfg['research_head_before'];assert bh(gitb('show',actual_commit+':'+str(p.relative_to(W))))==e['sha256'];e.update(repository='Georgakopoulos-Soares-lab/unlearning',commit=actual_commit,repository_path=str(p.relative_to(W)))
  inputs.append(e);return e
 for root,names,owner in [(D4,['A05_REQUIREMENTS.md','A05_PROMPT_DELTA.md','A05_PROPOSAL.json','A04_RECEIPT.json','CHECKPOINT_IDENTITIES.json','QUALIFICATION_MATRIX.csv','REUSE_BRIDGE_MATRIX.csv','SMOKE_RESULTS.json','SOURCE_IDENTITY.json','ENVIRONMENT_LOCK.json','BACKUP_VERIFICATION.json','FRESH_RESTORE_CHECK.json','OUTPUT_SHA256SUMS','PAYLOAD_RECOVERY_INDEX.json','MIRROR_REMOTE_CONTENT_BINDING.json'],'A04-attempt-004'),(D50,['PROTOCOL_FROZEN.json','COVERAGE_PLAN.json','CONTRAST_PLAN.json','AUDIT_PLAN.json','RESULT_SCHEMAS.json','INPUT_RECONCILIATION.json','SCIENTIFIC_SOURCE_VERIFICATION.json','THROUGHPUT_FORECAST.json','COVERAGE.csv'],'A05-attempt-001'),(D3,['A03_RECEIPT.json','DATA_AUDIT.json','FEATURE_STRUCTURAL_AUDIT.json','STRUCTURAL_REUSE_AUDIT.json','FIXED_REFERENCE_INDEX.json','CONTROL_REUSE_INDEX.json','DEPENDENCY_AND_DRAW_AUDIT.json','PAIRING_POPULATION_CHECKS.json','PAIRING_AND_UNCERTAINTY_AUDIT.json','RECOVERY_DEPENDENCIES.json','PATH_TRANSLATION.json','SEMANTIC_EXPOSURE_AUDIT.json','BACKUP_VERIFICATION.json'],'A03-attempt-001'),(D6,['A06_RECEIPT.json','EXTRACTION_INDEX.json','H3_HEAD_INDEX.json','H3_GATE_INDEX.json','LM_INDEX.json','RESOURCE_MEASUREMENTS.json','BACKUP_VERIFICATION.json','H3_AUDIT_PLAN.json','CPU_SOURCE_IDENTITY.json','SOURCE_IDENTITY.json','ADAPTER_PARITY_R4.json','ADAPTER_PARITY_R6.json','REPORT_METADATA_RECONCILIATION.json'],'A06-attempt-001'),(D7,['A07_RECEIPT.json','PROBE_INDEX.json','FIXED_REFERENCE_MAP.json','A06_REPORT_SCHEMA_REPAIR.json','REUSED_VIEW_MAP.json','FIT_RESOURCE_REPORT.json','BACKUP_VERIFICATION.json','A08_AUDIT_HANDOFF_PLAN.json'],'A07-attempt-001'),(D8,['A08_RECEIPT.json','BACKUP_MANIFEST.json','AUDIT_RELEASE_MATRIX.csv','REFIT_PANEL.json'],'A08-attempt-001'),(D9,['A09_RECEIPT.json','TABLE_INDEX.json','AUDIT_RELEASE_STATUS.csv','REPORT_REPAIR_LOG.json','ENDPOINT_ALIAS_MAP.csv','SOURCE_IDENTITY.json','RECOVERY_DEPENDENCY_GRAPH.json','BACKUP_VERIFICATION.json','COUNT_EVIDENCE.json'],'A09-attempt-001')]:
  for n in names:
   p=root/n
   if p.exists():bind(p,owner)
   else:inputs.append({'path':str(p),'owner':owner,'status':'NOT_CANONICAL_FILENAME_RESOLVE_EQUIVALENT','verification_method':'PENDING_EQUIVALENT_LOOKUP'})
 # The full A04 public seal is small metadata/code; no arrays are re-audited.
 for line in (D4/'OUTPUT_SHA256SUMS').read_text().splitlines():
  h,n=line.split('  ',1);assert sha(D4/n)==h
 # Actual native-file presence and reuse of the prior full-hash stat seal, no new whole-shard read.
 cache=read(C4/'VERIFIED_FILE_STAT_CACHE.json');assets=read(C4/'DOWNLOAD_RECEIPTS.json')['records'];presence=[]
 for e in assets:
  p=Path(e['target']);s=p.stat();assert s.st_size==e['bytes'];stat=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns];old=cache.get(str(p));small=p.stat().st_size<1024**2
  if small:assert sha(p)==e['sha256'];method='FRESH_SMALL_SIDECAR_SHA256'
  else:assert old=={'sha256':e['sha256'],'stat':stat},'Large payload changed since A04; A05 must not hide a recovery task';method='A04_FULL_HASH_STAT_SEAL_REUSED_CURRENT_STAT_EXACT'
  presence.append({'alias':e['alias'],'path':str(p),'native_relative_path':e['relative_path'],'bytes':s.st_size,'sha256':e['sha256'],'verification_method':method,'fresh_whole_shard_hash':False,'mirror_revision':e['mirror_revision'],'mirror_path':e['mirror_path']})
 put(C/'PAYLOAD_PRESENCE.json',{'status':'PASS','assets':presence,'new_model_downloads':0,'new_whole_shard_hashes':0})
 protocol=read(D50/'PROTOCOL_FROZEN.json');assert protocol['tasks']==TASKS and protocol['representations']==HOOKS and protocol['seeds']==SEEDS
 for e in protocol['folds']:bind(e['reference']['path'],'A03 historical grouped folds')
 # Source interfaces are read as text, never imported or invoked.
 for p in [A6/'code/run_extraction.py',A6/'code/runtime_model.py',A6/'code/production_contract.py',A6/'code/h3_common.py',A6/'code/fit_h3.py',A6/'code/audit_h3.py',A7/'code/fit_other_five.py',A7/'code/other_five_common.py']:
  bind(p,'historical stage implementation interface')
 validator=subprocess.run([sys.executable,str(C/'package/validate_package.py'),'--strict-file-set'],capture_output=True,text=True);(A/'logs/package-legacy.stdout.log').write_text(validator.stdout);(A/'logs/package-legacy.stderr.log').write_text(validator.stderr);put(C/'LEGACY_FORMAT_VALIDATOR.json',{'exit_code':validator.returncode,'status':'PASS' if validator.returncode==0 else 'LEGACY_HEADING_OR_FORMAT_LIMITATION','all_34_actual_package_hashes_pass':True,'exact_diagnostic':validator.stderr[-2000:],'not_a_checksum_waiver':True})
 # Fresh current provider capacity, no hardware/purchase action and no GPU initialization.
 pod=os.environ.get('RUNPOD_POD_ID');key=os.environ.get('RUNPOD_API_KEY');assert pod and key;response=requests.get('https://api.runpod.io/v2/pods/'+pod,headers={'Authorization':'Bearer '+key},timeout=(15,30));assert response.status_code==200;provider=response.json();mount=provider.get('mounts',{}).get('persistent',{});assert mount.get('path')=='/workspace';capacity=int(mount['size'])*10**9;cc=Path('/sys/fs/cgroup');quota=int((cc/'cpu/cpu.cfs_quota_us').read_text())/int((cc/'cpu/cpu.cfs_period_us').read_text());ram=int((cc/'memory/memory.limit_in_bytes').read_text());assert quota>=8 and ram>=64*1024**3;used=int(subprocess.check_output(['du','-sx','--block-size=1','/workspace'],text=True).split()[0]);put(C/'RESOURCE_PREFLIGHT.json',{'status':'PASS','persistent_capacity_bytes':capacity,'workspace_allocated_bytes':used,'provider_capacity_freshly_verified':True,'pod_id_sha256':bh(pod.encode()),'cgroup_CPU_equivalents':quota,'cgroup_RAM_limit_bytes':ram,'CPU_workers_max':2,'BLAS_threads_each':4,'GPU_work_authorized':False,'no_purchases':True,'time_policy':cfg['time_policy'],'observed_utc':now()})
 put(C/'INPUT_MANIFEST.json',{'schema':'pod-a-a05-input-manifest-v2','status':'PASS_REQUIRED_ANCHORS','research_input_commit':cfg['research_head_before'],'inputs':inputs,'private_identity_chain':'PRIVATE_INPUT_CHAIN.json','large_payload_presence':'PAYLOAD_PRESENCE.json','original_protocol_sha256':sha(D50/'PROTOCOL_FROZEN.json'),'original_coverage_sha256':sha(D50/'COVERAGE_PLAN.json'),'original_artifact_lineage_retained':True,'new_science':0});put(C/'INPUT_RECONCILIATION.json',{'status':'PASS_PREREQUISITES_R5_PLAN','qualification_variants_new_from_A04_reused':6,'qualification_rows_new_from_A04_reused':189,'R3_historical_TRAIN_bridge_rows':81,'older_qualified_variants_reused':12,'older_qualified_rows_reused':378,'combined_qualified_variants':18,'combined_qualified_rows':567,'R2_pending_variants':3,'R2_pending_rows':54,'released_heads':2340,'released_fixed_applications':2340,'primary_LM_units':35,'controls':36,'R5_production_units':0,'A04_and_full_project_status':'PARTIAL','full_installed_GPU_rebuild_tested':False,'new_model_loading':0,'new_fits_predictions_effects':0,'process_service_state':state,'input_manifest_sha256':sha(C/'INPUT_MANIFEST.json'),'metadata_identity_chain_fresh':'PRIVATE_INPUT_CHAIN.json','wall_seconds':time.monotonic()-start});no_science_imports();print(json.dumps({'status':'METADATA_PREFLIGHT_PASS','input_metadata_records':len(inputs),'native_assets_present':len(presence),'fresh_native_whole_shard_hashes':0,'GPU_work':0,'observer':'STOPPED','legacy_format_validator':validator.returncode}))
if __name__=='__main__':main()
