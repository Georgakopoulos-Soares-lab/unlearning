"""S06 append-only private checkpoint, explicit fresh HTTPS restore, fixed CPU replay panel. No stage dispatch."""
from pathlib import Path,PurePosixPath
import os,sys,json,hashlib,tarfile,io,uuid,re,urllib.request,urllib.parse,time,shutil
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['HF_HUB_DISABLE_XET']='1';os.environ['HF_HUB_DOWNLOAD_TIMEOUT']='45'
from huggingface_hub import HfApi,hf_hub_url,get_token
from ops import C,A,save,now
from long_run import execute
alias=sys.argv[1];attempt=int(sys.argv[2]);assert alias in {f'candidate_{i:02d}' for i in range(1,10)} and attempt in [1,2]
def safe_failure(kind,value,tb):
 reason=re.sub(r'https?://\S+','[URL REDACTED]',str(value));reason=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',reason);save(C/(alias+'-PRIVATE_RECOVERY_FAILED-'+str(attempt)+'.json'),{'status':'FAILED_PRESERVED','exception':kind.__name__,'reason':reason,'observed_utc':now()});print('S06_PRIVATE_RECOVERY_FAILED',alias,kind.__name__,reason,flush=True)
sys.excepthook=safe_failure
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest();cfg=read(C/'RUN_CONFIG.json');case=A/'candidates'/alias;verification=read(case/'verification/VERIFICATION.json');assert verification['status']=='PASS' and verification['representation_matrices_verified']==260 and verification['LM_units_verified']==10 and verification['S07_refit_identities_resolved']==390;source=read(C/'SOURCE_IDENTITY.json');archive=A/'private-checkpoints'/(alias+'-other-five-001.tar.gz');archive.parent.mkdir(exist_ok=True);snapshot=C/(alias+'-PRIVATE_SNAPSHOT.json');statefile=C/(alias+'-PRIVATE_RECOVERY_PROGRESS.json');locfile=C/(alias+'-PRIVATE_RECOVERY_LOCATORS.json');F=Path(cfg['frozen_root']);C3=C.parent.parent/'S03/attempt-003';C1=C.parent.parent/'S03/attempt-001';started=time.monotonic()
if not archive.exists():
 entries={}
 def add(name,p):
  q=PurePosixPath(name);assert not q.is_absolute() and '..' not in q.parts and '\\' not in name and name not in entries;assert p.is_file() and not p.is_symlink() and p.stat().st_size<128*1024**2;entries[name]=p
 for p in sorted(case.rglob('*')):
  if p.is_file() and not p.name.endswith('.lock') and not p.name.startswith('distributed_init_'):add('candidate/'+str(p.relative_to(case)),p)
 for p in sorted(Path(cfg['inputs_root']).rglob('*')):
  if p.is_file():add('inputs/'+str(p.relative_to(cfg['inputs_root'])),p)
 for f in source['files']:add('code/'+f['path'],Path(source['code_root'])/f['path'])
 for n in ['RUN_CONFIG.json','SOURCE_IDENTITY.json','ENVIRONMENT_LOCK.json','CPU_ENVIRONMENT_LOCK.json','READINESS.json','RECOVERY_CONTRACT.json','FINITE_EXECUTION_MANIFEST.jsonl','INPUT_BINDINGS.json','CAPACITY_ADMISSION.json']:add('control/'+n,C/n)
 for n in ['H3_AUDIT_SUBSET.json','S04_RECEIPT.json','S05_HANDOFF.json','BOOTSTRAP_PLAN.json']:add('frozen/'+n,F/n)
 # Exact immutable native/runtime/S04dependency graph; no model/runtime payload reupload and no raw sequences.
 native=next(v for v in read(C3/'MIRROR_HANDOFF.json') if v['alias']==alias);dependencies={'schema_version':'s06-exact-recovery-dependencies-v1','candidate_native_mirror':native,'S03_final_metadata':read(C3/'FINAL_METADATA_BACKUP_LOCATORS.json'),'unchanged_GPU_runtime':read(C1/'MINIMUM_PRIVATE_CHECKPOINT_LOCATORS.json'),'unchanged_CPU_runtime_install_plan':read(C1/'CPU_REFERENCE_RUNTIME_PLAN.json'),'unchanged_CPU_runtime_install_report':read(C1/'CPU_REFERENCE_INSTALL_REPORT.json'),'S04_planning_checkpoint':read(C.parent.parent/'S04/attempt-001/PRIVATE_PLANNING_BACKUP_LOCATORS.json'),'S05_H3_immutable_checkpoint':read(C.parent.parent/'S05/attempt-001'/(alias+'-PRIVATE_RECOVERY_LOCATORS.json')),'S05_final_metadata':read(C.parent.parent/'S05/attempt-001/FINAL_METADATA_BACKUP_LOCATORS.json'),'original_base_archive_001':read(C1/'qualification-checkpoint-002-DEPENDENCY_GRAPH.json')['historical_archives']['historical-archive-001'],'scope':'Existing qualified CPU runtime for reconstruction; no GPU replay or cleanruntime recreation. Rawweights/runtime referenced, not repacked; current candidate all other-five features/statistics/identity arrays and exact draws/folds included; original-base scaler/heads referenced by exact members.','restore_steps':['Verify immutablearchive SHA/size/safemember set','Use freshconsumer code/inputs/candidate only, no producerfallback','Run restored real S07 reader all260matrices and all10LMpoints/all5devdraws,masks,CIs; resolve390refit+390fixedidentities without fitting or head application','Rebuild runtime only from qualified immutabledependencies/declaredwheelhashes if needed; untested cleanmachine level remains explicit']};dep=C/(alias+'-EXACT_RECOVERY_DEPENDENCIES.json');save(dep,dependencies);add('DEPENDENCIES.json',dep)
 assert len(entries)<20000 and sum(p.stat().st_size for p in entries.values())<4*1024**3;manifest_entries={};last=time.monotonic();done=0
 staging=archive.with_name(archive.name+'.packing-attempt-'+str(attempt));assert not staging.exists()
 with tarfile.open(staging,'w:gz',compresslevel=1) as tar:
  for name,p in entries.items():
   h=sha(p);size=p.stat().st_size;manifest_entries[name]={'bytes':size,'sha256':h};member=tarfile.TarInfo(name);member.size=size;member.mode=0o644;member.mtime=0
   with p.open('rb') as f:tar.addfile(member,f)
   done+=1
   if time.monotonic()-last>=20:save(statefile,{'status':'FINITE_CHECKPOINT_PACKING','alias':alias,'members_done':done,'members_total':len(entries),'elapsed_seconds':time.monotonic()-started,'updated_utc':now()});print('S06_PRIVATE_PACK_PROGRESS',alias,done,'of',len(entries),flush=True);last=time.monotonic()
  manifest={'schema_version':'s06-private-other-five-checkpoint-v1','alias':alias,'files':manifest_entries,'protocol_semantic_sha256':cfg['protocol_semantic_sha256'],'source_bundle_sha256':sha(C/'SOURCE_IDENTITY.json'),'candidate_content_sha256':next(v['model_tensor_content_sha256'] for v in cfg['candidates'] if v['alias']==alias),'private_CPU_replay_panel':'All10bundles/all260matrices/all10LMpointpairs/all5devuncertainty;390+390futurebindings; no fits/head applications/GPU','raw_sequences_or_native_weights_included':False,'timestamp':now(),'self_reference':'Futureupload/readback/gate receipts external to this archive'};raw=(json.dumps(manifest,indent=2)+'\n').encode();member=tarfile.TarInfo('MEMBER_MANIFEST.json');member.size=len(raw);member.mode=0o644;member.mtime=0;tar.addfile(member,io.BytesIO(raw))
 save(snapshot,manifest);os.replace(staging,archive)
else:
 manifest=read(snapshot)
 for n,r in manifest['files'].items():
  if n.startswith('candidate/'):assert sha(case/n[len('candidate/'):])==r['sha256'],'Frozen completedscientific bytes changed; no silent rebind'
print('S06_PRIVATE_ARCHIVE_HASH_START',alias,archive.stat().st_size,flush=True);h=sha(archive);size=archive.stat().st_size;repo=read(C3/'BACKUP_ROUTE_CURRENT.json')['repository'];api=HfApi();info=api.repo_info(repo_id=repo,repo_type='dataset',timeout=45);assert info.private is True
if not locfile.exists():
 intentfile=C/(alias+'-PRIVATE_UPLOAD_INTENT.json')
 if intentfile.exists():
  intent=read(intentfile);assert intent['archive_sha256']==h and intent['archive_bytes']==size;remote=intent['remote_object']
 else:
  remote='POD_A_SALIENCY/20261123T111855Z-saliency/S06/attempt-001/'+alias+'-'+uuid.uuid4().hex+'/'+archive.name;save(intentfile,{'repository':repo,'remote_object':remote,'archive_sha256':h,'archive_bytes':size,'created_utc':now(),'policy':'Sameexactownedobjectpath on diagnosedretry; never manufactureanotherprefixoroverwriteunrelatedobjects'})
 save(statefile,{'status':'SEALED_AWAITING_APPEND_ONLY_PRIVATE_UPLOAD','alias':alias,'archive_sha256':h,'archive_bytes':size,'expected_members':len(manifest['files']),'updated_utc':now()});print('S06_PRIVATE_UPLOAD_START',alias,size,flush=True);result=api.upload_file(repo_id=repo,repo_type='dataset',path_or_fileobj=str(archive),path_in_repo=remote,parent_commit=info.sha,commit_message='Protect source-bound Pod A S06 other-five candidate results');rev=result.oid;assert re.fullmatch('[0-9a-f]{40}',rev);save(locfile,{'repository':repo,'revision':rev,'remote_object':remote,'archive_sha256':h,'archive_bytes':size})
else:
 loc=read(locfile);assert loc['repository']==repo and loc['archive_sha256']==h and loc['archive_bytes']==size;rev=loc['revision'];remote=loc['remote_object']
assert api.repo_info(repo_id=repo,repo_type='dataset',revision=rev,timeout=45).private is True;save(statefile,{'status':'UPLOADED_AWAITING_EXPLICIT_FRESH_READBACK','alias':alias,'immutable_revision':rev,'archive_sha256':h,'archive_bytes':size,'updated_utc':now()});consumer=A/'fresh-consumers'/(alias+'-HTTP-'+str(attempt).zfill(3));restored=A/'fresh-consumers'/(alias+'-restored-'+str(attempt).zfill(3));assert not consumer.exists() and not restored.exists();consumer.mkdir(parents=True);partial=consumer/'checkpoint.tar.gz.partial';token=get_token();assert token
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  nxt=super().redirect_request(req,fp,code,msg,headers,newurl)
  if nxt and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:nxt.remove_header('Authorization')
  return nxt
request=urllib.request.Request(hf_hub_url(repo_id=repo,repo_type='dataset',revision=rev,filename=remote),headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache','Pragma':'no-cache'});count=0;digest=hashlib.sha256();last=time.monotonic();read_started=last
with urllib.request.build_opener(Redirect()).open(request,timeout=45) as response,partial.open('xb') as f:
 assert response.status==200 and response.headers.get('Content-Range') is None and 'html' not in response.headers.get('Content-Type','');declared=response.headers.get('Content-Length');assert declared is None or int(declared)==size
 while True:
  block=response.read(1024**2)
  if not block:break
  count+=len(block);assert count<=size;digest.update(block);f.write(block)
  if time.monotonic()-last>=20:save(statefile,{'status':'FINITE_EXPLICIT_HTTP_BODY_READ','alias':alias,'immutable_revision':rev,'received_bytes':count,'expected_bytes':size,'elapsed_seconds':time.monotonic()-read_started,'updated_utc':now()});print('S06_PRIVATE_READBACK_PROGRESS',alias,count,'of',size,flush=True);last=time.monotonic()
 f.flush();os.fsync(f.fileno())
assert count==size and digest.hexdigest()==h;download=consumer/'checkpoint.tar.gz';partial.rename(download);restored.mkdir();seen=set();expanded=0;membercount=0;last=time.monotonic()
with tarfile.open(download,'r|gz') as tar:
 for member in tar:
  q=PurePosixPath(member.name);assert member.isfile() and not q.is_absolute() and '..' not in q.parts and '\\' not in member.name and member.name not in seen;seen.add(member.name);expanded+=member.size;assert expanded<4*1024**3 and member.size<128*1024**2;dest=restored/member.name;dest.parent.mkdir(parents=True,exist_ok=True);dg=hashlib.sha256();n=0
  with tar.extractfile(member) as inp,dest.open('xb') as out:
   while True:
    b=inp.read(4*1024**2)
    if not b:break
    n+=len(b);dg.update(b);out.write(b)
  if member.name=='MEMBER_MANIFEST.json':assert read(dest)==manifest
  else:assert member.name in manifest['files'] and n==manifest['files'][member.name]['bytes'] and dg.hexdigest()==manifest['files'][member.name]['sha256']
  membercount+=1
  if time.monotonic()-last>=20:print('S06_FRESH_SAFE_RESTORE_PROGRESS',alias,membercount,expanded,flush=True);last=time.monotonic()
assert seen==set(manifest['files'])|{'MEMBER_MANIFEST.json'};print('S06_EXACT_PRIVATE_MEMBER_RESTORE_PASS',alias,rev,len(manifest['files']),flush=True)
# Resolve original-base member metadata through an explicit immutable archive graph, without downloading/applying heads.
deps=read(restored/'DEPENDENCIES.json');original=deps['original_base_archive_001'];assert original['revision']=='e75b95d9ca579ddb85fe354bea52bb9a78215b16' and original['archive_sha256']=='26db00fcaae93fae959ed225ff3b1775630f85644a188192e822182f002f319e' and original['archive_bytes']==10108100047
refs=read(restored/'inputs/ORIGINAL_BASE_REFERENCE_DEPENDENCIES.json');assert len(refs)==390
for ref in refs:
 dep=ref['external_original_head'];assert dep['archive_id']=='historical-archive-001' and dep['member'].startswith('probes/') and dep['bytes']>0 and re.fullmatch('[0-9a-f]{64}',dep['sha256'])
# Minimal offline CPU-only environment. All numerical inputs/source are restored; only the qualified interpreter is external.
env={'PATH':str(Path(cfg['cpu_runtime_python']).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','PYTHONPATH':str(restored/'code'),'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'};job=execute('fresh-CPU-recovery-'+alias+'-'+str(attempt),[cfg['cpu_runtime_python'],str(restored/'code/s06_verify.py'),'--control',str(C),'--alias',alias,'--consumer',str(restored)],env);replay=read(restored/'fresh-verification/VERIFICATION.json');assert replay['status']=='PASS' and replay['representation_matrices_verified']==260 and replay['LM_units_verified']==10 and replay['primary_dev_uncertainty_units_verified']==5 and replay['S07_refit_identities_resolved']==390 and replay['producer_input_fallback'] is False;assert api.repo_info(repo_id=repo,repo_type='dataset',revision=rev,timeout=45).private is True
receipt={'schema_version':'s06-private-recovery-proof-v1','status':'PASS','alias':alias,'candidate_content_sha256':manifest['candidate_content_sha256'],'immutable_revision':rev,'archive_sha256':h,'archive_bytes':size,'uploaded_application_bytes':size,'explicit_HTTP_body_readback_bytes':count,'SDK_file_or_Xet_download_cache_used':False,'private_at_write_and_readback':True,'exact_regular_members_verified':len(manifest['files']),'uncompressed_bytes_verified':expanded,'member_integrity_status':'PASS','metadata_contract_status':'PASS','numerical_replay_status':'PASS','restored_feature_bundles':10,'restored_representation_matrices':260,'restored_LM_units':10,'restored_dev_uncertainty_units':5,'resolved_S07_refit_identities':390,'resolved_S07_fixed_application_identities':390,'head_operations_executed':0,'fresh_CPU_replay_receipt_sha256':sha(restored/'fresh-verification/VERIFICATION.json'),'max_LM_point_draw_interval_abs_residual':replay['max_abs_residual'],'metric_draw_interval_atol':1e-12,'rtol':0,'CPU_child_exit_status':job['exit_status'],'producer_input_fallback':False,'native_or_runtime_payload_reuploaded':False,'clean_runtime_or_GPU_recreation':False,'scope':'Fullmemberbytes plus all10bundles/all260matrices/all10LMpointpairs/all5devdraws+masks+CIs/all390refit+390fixedidentities in existing qualified CPU runtime; no fitting/head application/GPU replay/clean runtime recreation','restored_consumer':str(restored),'total_private_protection_wall_seconds':time.monotonic()-started,'network_overhead_or_cost':None,'completed_utc':now()};save(C/(alias+'-PRIVATE_RECOVERY_RECEIPT.json'),receipt);save(statefile,receipt);print('S06_PRIVATE_NUMERICAL_RECOVERY_PASS',alias,rev,260,flush=True)
