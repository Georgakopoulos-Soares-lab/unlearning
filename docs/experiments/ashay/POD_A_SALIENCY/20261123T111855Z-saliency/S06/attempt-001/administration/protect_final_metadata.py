"""Finite S06 final administrative metadata checkpoint and fresh exact byte restoration; no model/scoring."""
from pathlib import Path,PurePosixPath
import os,sys,json,hashlib,tarfile,io,uuid,urllib.request,urllib.parse,re,time
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import HfApi,hf_hub_url,get_token
from ops import C,A,R,save,now
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.file_digest(p.open('rb'),'sha256').hexdigest();T=R/read(C/'PATHS.json')['run_root'];P=T/'S06/attempt-001';C3=C.parent.parent/'S03/attempt-003';assert read(P/'S06_RECEIPT.json')['status']=='COMPLETE';assert len(read(P/'S07_HANDOFF.json')['eligible_candidates'])==9
archive=A/'private-checkpoints/S06-final-metadata-001.tar.gz';snapshot=C/'FINAL_METADATA_SNAPSHOT.json';started=time.monotonic()
def safe_failure(kind,value,tb):
 reason=re.sub(r'https?://\S+','[URL REDACTED]',str(value));reason=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',reason);save(C/'FINAL_METADATA_FAILED.json',{'type':kind.__name__,'reason':reason,'timestamp':now()});print('S06_FINAL_METADATA_FAILED',kind.__name__,reason,flush=True)
sys.excepthook=safe_failure
if not archive.exists():
 entries={}
 def add(n,p):
  q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts and n not in entries and p.is_file() and not p.is_symlink();assert p.stat().st_size<32*1024**2;assert not re.search(rb'\bhf_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+',p.read_bytes()),'Credential-bearing bytes excluded';entries[n]=p
 for p in sorted(P.rglob('*')):
  if p.is_file() and p.name!='OUTPUT_SHA256SUMS':add('research/S06/attempt-001/'+str(p.relative_to(P)),p)
 for n in ['CONTROLLER_STATE.json','EVENTS.jsonl','PROGRESS.md','SESSION_HANDOFF.md']:add('research/'+n,T/n)
 for p in sorted(C.iterdir()):
  if p.is_file() and p.suffix in ['.py','.md','.json','.jsonl'] and not p.name.startswith('FINAL_METADATA_') and not (p.name.endswith('-PROGRESS.json') and read(p).get('status')=='RUNNING'):add('private-control/'+p.name,p)
 deps={'S04':read(C.parent.parent/'S04/attempt-001/PRIVATE_PLANNING_BACKUP_LOCATORS.json'),'S03':read(C3/'FINAL_METADATA_BACKUP_LOCATORS.json'),'other_five_candidates':{v['alias']:read(C/(v['alias']+'-PRIVATE_RECOVERY_LOCATORS.json')) for v in read(C/'RUN_CONFIG.json')['candidates']},'prior_S05_science_and_metadata':read(C.parent.parent/'S05/attempt-001/FINAL_METADATA_BACKUP_LOCATORS.json'),'scope':'Final published S06metadata+controller and exactcandidate externaldependency locators. Candidate science payloads remain in nine previously verified immutable archives, not repacked.'};save(C/'FINAL_METADATA_DEPENDENCIES.json',deps);add('DEPENDENCIES.json',C/'FINAL_METADATA_DEPENDENCIES.json');assert len(entries)<2000
 manifest={'schema_version':'s06-final-metadata-checkpoint-v1','files':{n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in entries.items()},'S06_receipt_sha256':sha(P/'S06_RECEIPT.json'),'S06_handoff_sha256':sha(P/'S07_HANDOFF.json'),'self_reference':'Finalupload/readback/Gitproof external to this sealedarchive; no recursivefuturehashes','created_utc':now()};staging=archive.with_name(archive.name+'.packing');assert not staging.exists()
 with tarfile.open(staging,'w:gz',compresslevel=1) as tar:
  for n,p in entries.items():
   member=tarfile.TarInfo(n);member.size=p.stat().st_size;member.mode=0o600;member.mtime=0
   with p.open('rb') as f:tar.addfile(member,f)
  b=(json.dumps(manifest,indent=2)+'\n').encode();m=tarfile.TarInfo('MEMBER_MANIFEST.json');m.size=len(b);m.mode=0o600;m.mtime=0;tar.addfile(m,io.BytesIO(b))
 save(snapshot,manifest);os.replace(staging,archive)
else:manifest=read(snapshot)
api=HfApi();repo=read(C3/'BACKUP_ROUTE_CURRENT.json')['repository'];info=api.repo_info(repo_id=repo,repo_type='dataset',timeout=45);assert info.private is True;h=sha(archive);size=archive.stat().st_size;locfile=C/'FINAL_METADATA_BACKUP_LOCATORS.json';intentfile=C/'FINAL_METADATA_UPLOAD_INTENT.json'
if not locfile.exists():
 if intentfile.exists():intent=read(intentfile);assert intent['archive_sha256']==h and intent['archive_bytes']==size;remote=intent['remote_object']
 else:
  remote='POD_A_SALIENCY/20261123T111855Z-saliency/S06/final-metadata-'+uuid.uuid4().hex+'/'+archive.name;save(intentfile,{'repository':repo,'remote_object':remote,'archive_sha256':h,'archive_bytes':size})
 print('S06_FINAL_METADATA_UPLOAD_START',size,flush=True);result=api.upload_file(repo_id=repo,repo_type='dataset',path_or_fileobj=str(archive),path_in_repo=remote,parent_commit=info.sha,commit_message='Protect complete S06 other-five handoff and administrative metadata');rev=result.oid;save(locfile,{'repository':repo,'revision':rev,'remote_object':remote,'archive_sha256':h,'archive_bytes':size})
else:loc=read(locfile);assert loc['archive_sha256']==h and loc['archive_bytes']==size;remote=loc['remote_object'];rev=loc['revision']
assert api.repo_info(repo_id=repo,repo_type='dataset',revision=rev,timeout=45).private is True;consumer=A/'final-metadata-fresh-consumer-001';assert not consumer.exists();consumer.mkdir();download=consumer/'checkpoint.tar.gz';token=get_token();assert token
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  nxt=super().redirect_request(req,fp,code,msg,headers,newurl)
  if nxt and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:nxt.remove_header('Authorization')
  return nxt
req=urllib.request.Request(hf_hub_url(repo_id=repo,repo_type='dataset',revision=rev,filename=remote),headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache'});count=0;digest=hashlib.sha256()
with urllib.request.build_opener(Redirect()).open(req,timeout=45) as response,download.open('xb') as f:
 assert response.status==200 and response.headers.get('Content-Range') is None
 while True:
  b=response.read(1024**2)
  if not b:break
  f.write(b);count+=len(b);digest.update(b);assert count<=size
 f.flush();os.fsync(f.fileno())
assert count==size and digest.hexdigest()==h;seen=set();expanded=0
with tarfile.open(download,'r|gz') as tar:
 for m in tar:
  q=PurePosixPath(m.name);assert m.isfile() and not q.is_absolute() and '..' not in q.parts and '\\' not in m.name and m.name not in seen and m.size<32*1024**2;seen.add(m.name);expanded+=m.size;assert expanded<256*1024**2;dest=consumer/'restored'/m.name;dest.parent.mkdir(parents=True,exist_ok=True);data=tar.extractfile(m).read();assert len(data)==m.size;dest.write_bytes(data)
  if m.name=='MEMBER_MANIFEST.json':assert json.loads(data)==manifest
  else:r=manifest['files'][m.name];assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
assert seen==set(manifest['files'])|{'MEMBER_MANIFEST.json'};restored=consumer/'restored/research';assert read(restored/'S06/attempt-001/S06_RECEIPT.json')['status']=='COMPLETE';assert sha(restored/'S06/attempt-001/S06_RECEIPT.json')==manifest['S06_receipt_sha256'];assert sha(restored/'S06/attempt-001/S07_HANDOFF.json')==manifest['S06_handoff_sha256'];assert api.repo_info(repo_id=repo,repo_type='dataset',revision=rev,timeout=45).private is True
# Administrative deterministic regeneration from restored saved metadata only; no scientific replay.
from long_run import execute
base=consumer/'restored';private=base/'private-control';public=base/'research/S06/attempt-001';regen=base/'regenerated-public-mappings';config=read(private/'RUN_CONFIG.json');env={'PATH':str(Path(config['cpu_runtime_python']).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','HF_HUB_OFFLINE':'1'}
job=execute('S06-final-metadata-mapping-regeneration-001',[config['cpu_runtime_python'],str(private/'assemble_metadata.py'),str(public),str(private/'RUN_CONFIG.json'),str(private/'FINITE_EXECUTION_MANIFEST.jsonl'),str(regen)],env)
mapnames=['OTHER_FIVE_FEATURE_INDEX.json','LM_SUFFICIENT_STATISTICS_INDEX.json','ROW_IDENTITY_VERIFICATION.json','EXTRACTION_UNIT_RECEIPTS.jsonl','ALL_UNIT_RECEIPTS.jsonl','LM_MARGINALS.jsonl','COVERAGE_VALIDATION.json','RESOURCE_SUMMARY.json','S07_HANDOFF.json'];regenerated={}
for name in mapnames:
 assert sha(regen/name)==sha(public/name),'Final metadata mapping regeneration differs: '+name
 regenerated[name]=sha(regen/name)
proof={'schema_version':'s06-final-administrative-recovery-v1','status':'PASS','immutable_revision':rev,'archive_sha256':h,'archive_bytes':size,'explicit_HTTP_readback_bytes':count,'exact_regular_members_verified':len(manifest['files']),'expanded_bytes_verified':expanded,'S06_receipt_sha256':manifest['S06_receipt_sha256'],'S06_handoff_sha256':manifest['S06_handoff_sha256'],'all9_candidate_science_recovery_previously_verified':True,'private_at_upload_and_readback':True,'SDK_download_cache_used':False,'no_scientific_execution':True,'administrative_mapping_regeneration_status':'PASS','regenerated_exact_public_mappings':regenerated,'mapping_regeneration_CPU_exit_status':job['exit_status'],'producer_path_fallback':False,'scope':'Exact final administrative metadata/controller/S06receipt/S06handoff restored; candidate scientific archives referenced by immutable verified dependency graph; no extra replay or refits','wall_seconds':time.monotonic()-started,'completed_utc':now()};save(C/'FINAL_METADATA_RECOVERY_RECEIPT.json',proof);save(P/'FINAL_METADATA_RECOVERY.json',proof);print('S06_FINAL_METADATA_FRESH_RESTORE_PASS',rev,size,len(manifest['files']),flush=True)
