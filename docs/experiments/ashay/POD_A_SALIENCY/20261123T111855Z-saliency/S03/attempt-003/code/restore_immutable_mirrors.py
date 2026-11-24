from pathlib import Path
import os,json,hashlib,urllib.request,urllib.parse,urllib.error,time,shutil,fcntl,signal,re,sys
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['HF_HUB_ETAG_TIMEOUT']='45';os.environ['HF_HUB_DOWNLOAD_TIMEOUT']='45'
from huggingface_hub import HfApi,hf_hub_url,get_token
from ops import C,A,R,save,now
from mirror_contract import compatible_resume,response_range,safe
old=C.with_name('attempt-001');bound=json.loads((C/'FINITE_RESOURCE_BOUND.json').read_text());admissions=json.loads((C/'MIRROR_ADMISSION.json').read_text())['records'];handoff={r['alias']:r for r in json.loads((C/'MIRROR_HANDOFF.json').read_text())};cache=json.loads((old/'VERIFIED_FILE_STAT_CACHE.json').read_text());api=HfApi();token=get_token();assert token
lock=(C/'MIRROR_TRANSFER.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);proc={'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  out=super().redirect_request(req,fp,code,msg,headers,newurl)
  if out and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:out.remove_header('Authorization')
  return out
opener=urllib.request.build_opener(Redirect());progress={'schema_version':'s03-exact-mirror-transfer-progress-v1','owned_process':proc,'started_utc':now(),'records':[],'active':None,'finite_candidates':9,'physical_network_bytes':None};assert not (C/'MIRROR_TRANSFER_PROGRESS.json').exists();local_admission={'schema_version':'s03-local-mirror-admission-v1','records':[]};save(C/'MIRROR_LOCAL_ADMISSION.json',local_admission)
# Static loader path map has immutable per-file pins. Only the single transfer owner writes receipts/admission.
manifest={'schema':'s03-HF-immutable-native-input-paths-v1','items':[],'small_assets':[],'checkpoint_roots':{}};downloads={'records':[]};smallnames=['.metadata','run_config.yaml','metadata.json','tokenizer.json','tokenizer_config.json']
for m in admissions:
 alias=m['alias'];root=A/('native-'+alias);root.mkdir();manifest['checkpoint_roots'][alias]=str(root)
 for f in m['files']:
  name=f['path'].rsplit('/',1)[-1]
  if name=='__0_0.distcp':manifest['items'].append({'alias':alias,'file_id':f['source_file_id'],'name':name,'expected_bytes':f['bytes'],'expected_historical_sha256':f['sha256'],'sha256_origin':'Exact immutable HF manifest joined to original Drive identity; locally verified at restoration','target':str(root/name)})
  if name in smallnames:manifest['small_assets'].append({'alias':alias,'file_id':f['source_file_id'],'name':name,'bytes':f['bytes'],'sha256':f['sha256'],'path':str(root/name),'status':'REUSED_VERIFIED_SMALL_ASSET','evidence':'MIRROR_LOCAL_ADMISSION.json'})
save(C/'ASSET_TRANSFER_MANIFEST.json',manifest);save(C/'DOWNLOAD_RECEIPTS.json',downloads)
def checkpoint():
 progress['updated_utc']=now();progress['verified_download_body_bytes']=sum(r.get('new_body_bytes',0) for r in progress['records'] if r['status']=='VERIFIED');progress['local_reused_bytes']=sum(r['bytes'] for r in progress['records'] if r['status']=='VERIFIED' and r.get('reused_local'));save(C/'MIRROR_TRANSFER_PROGRESS.json',progress)
def download(h,f,root):
 name=f['path'];safe(name);dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);expected={'repo_id':h['repo_id'],'revision':h['payload_revision'],'remote_path':h['path']+'/'+name,'expected_bytes':f['bytes'],'expected_sha256':f['sha256']};row={'alias':h['alias'],'file_id':f['source_file_id'],'member_path':name,'bytes':f['bytes'],'sha256':f['sha256'],'destination':str(dest),'revision':h['payload_revision'],'remote_path':expected['remote_path'],'status':'RUNNING','started_utc':now(),'reused_local':False,'new_body_bytes':0,'resumed_bytes':0};progress['active']=row;checkpoint()
 # Reuse only the old pilot native blob, whose complete digest and current stat binding were reconciled. Other raw copies are fresh native recovery consumers.
 if h['alias']=='candidate_01' and name=='__0_0.distcp':
  p=A.with_name('attempt-001')/'native-pilot/__0_0.distcp';v=cache[str(p)];s=p.stat();assert v['sha256']==f['sha256'] and [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]==v['stat'];row.update(status='VERIFIED',destination=str(p),reused_local=True,new_body_bytes=0,verification='Prior full SHA256 + current unchanged inode/time binding, exact mirror SHA match');return row
 # All other new consumers receive an actual immutable-revision network GET; no prior cache fallback.
 tmp=dest.with_name(dest.name+'.partial');binding=dest.with_name(dest.name+'.partial.binding.json');assert not dest.exists();start=tmp.stat().st_size if tmp.exists() else 0
 if start:compatible_resume(json.loads(binding.read_text()),expected,start)
 else:assert not tmp.exists();save(binding,expected)
 digest=hashlib.sha256();md5=hashlib.md5(usedforsecurity=False)
 if start:
  with tmp.open('rb') as inp:
   while True:
    b=inp.read(8*1024**2)
    if not b:break
    digest.update(b);md5.update(b)
 row['resumed_bytes']=start;last=time.monotonic();began=last
 for retry in range(2):
  headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache','User-Agent':'Pod-A-authorized-S03-exact-recovery'}
  if start:headers['Range']='bytes='+str(start)+'-'
  req=urllib.request.Request(hf_hub_url(repo_id=h['repo_id'],repo_type='dataset',filename=expected['remote_path'],revision=h['payload_revision']),headers=headers)
  try:response=opener.open(req,timeout=45);break
  except urllib.error.HTTPError as e:
   if retry==0 and e.code in [429,500,502,503,504]:
    wait=e.headers.get('Retry-After');wait=min(45,max(1,int(wait))) if wait and wait.isdigit() else 3;row['transient_retry']={'HTTP_status':e.code,'bounded_backoff_seconds':wait};checkpoint();time.sleep(wait);continue
   raise
 count=start
 with response,tmp.open('ab' if start else 'xb') as out:
  response_range(response.status,response.headers.get('Content-Range'),start,f['bytes']);typ=response.headers.get('Content-Type','');assert 'text/html' not in typ,'HTML/error response rejected';length=response.headers.get('Content-Length');assert length is None or int(length)==f['bytes']-start
  while True:
   b=response.read(8*1024**2)
   if not b:break
   if count==0:assert not b.startswith(b'version https://git-lfs.github.com/spec/v1'),'LFS pointer stub'
   count+=len(b);assert count<=f['bytes'];out.write(b);digest.update(b);md5.update(b)
   if time.monotonic()-last>=20:
    assert shutil.disk_usage(A).free>=bound['shared_free_reserve_bytes'];row.update(received_bytes=count,new_body_bytes=count-start,elapsed_seconds=time.monotonic()-began);checkpoint();print('TRANSFER',h['alias'],name,count,'/',f['bytes'],flush=True);last=time.monotonic()
  out.flush();os.fsync(out.fileno())
 assert count==f['bytes'] and digest.hexdigest()==f['sha256'],'Complete received payload SHA/size differs'
 if f.get('md5'):assert md5.hexdigest()==f['md5'],'Received MD5 differs'
 assert tmp.stat().st_size==f['bytes'];tmp.rename(dest);row.update(status='VERIFIED',new_body_bytes=count-start,received_bytes=count,elapsed_seconds=time.monotonic()-began,verification='Full streamed SHA256 and supplied MD5 checked before atomic promotion; immutable remote revision, fresh consumer',md5=md5.hexdigest());return row
for m in admissions:
 alias=m['alias'];h=handoff[alias];root=A/('native-'+alias);current=[];failed=False
 try:
  # Bounded exact namespace tree inspection, never whole repository discovery.
  nodes=list(api.list_repo_tree(repo_id=h['repo_id'],repo_type='dataset',revision=h['payload_revision'],path_in_repo=h['path'],recursive=True));assert len(nodes)<=32;files=[n for n in nodes if type(n).__name__=='RepoFile'];actual={n.path for n in files};expected={h['path']+'/'+f['path'] for f in m['files']};assert actual==expected,'Immutable namespace member set differs';by_path={n.path:n for n in files}
  for f in m['files']:
   n=by_path[h['path']+'/'+f['path']];assert n.size==f['bytes'];lfs=getattr(n,'lfs',None);digest=getattr(lfs,'sha256',None) if lfs is not None else None
   if digest is None and isinstance(lfs,dict):digest=lfs.get('sha256') or lfs.get('oid')
   if digest is not None:assert digest==f['sha256'],'HF LFS declared content digest differs'
  # Verify small format inputs before the single large native stream.
  for f in sorted(m['files'],key=lambda f:(f['bytes']>1024**2,f['path'])):
   row=download(h,f,root);row['completed_utc']=now();progress['records'].append(row);current.append(row);progress['active']=None;checkpoint()
  assert len(current)==9 and sum(r['bytes'] for r in current)==h['payload_bytes']
  # Byte-preserving local tokenizer aliases adapt mirror packaging to the unchanged trusted loader. No tensor conversion or tokenizer edits.
  materialized=[]
  for name in ['tokenizer.json','tokenizer_config.json']:
   source=root/'tokenizer'/name;target=root/name;data=source.read_bytes();assert not target.exists();target.write_bytes(data);materialized.append({'source_member':'tokenizer/'+name,'loader_path':str(target),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'byte_identical':True})
  native=next(r for r in current if r['member_path']=='__0_0.distcp')
  # Pilot has a split local member map and retains its original complete model root for reuse; it is never reloaded here.
  if alias=='candidate_01':manifest['checkpoint_roots'][alias]=str(A.with_name('attempt-001')/'native-pilot');next(r for r in manifest['items'] if r['alias']==alias)['target']=native['destination'];manifest['small_assets']=[r for r in manifest['small_assets'] if r['alias']!=alias]
  downloads['records'].append({'file_id':native['file_id'],'status':'VERIFIED','sha256':native['sha256'],'bytes':native['bytes'],'path':native['destination']});save(C/'DOWNLOAD_RECEIPTS.json',downloads);save(C/'ASSET_TRANSFER_MANIFEST.json',manifest)
  receipt={'alias':alias,'candidate_id':h['candidate_id'],'status':'LOCAL_NATIVE_SHA256_AND_MAPPING_PASS','payload_revision':h['payload_revision'],'manifest_sha256':h['manifest_sha256'],'receipt_sha256':h['receipt_sha256'],'files':current,'tokenizer_materializations':materialized,'local_checkpoint_root':manifest['checkpoint_roots'][alias],'all9member_bytes_verified_or_validly_reused':True,'native_sha256':h['native_shard_sha256'],'fresh_native_network_restore':alias!='candidate_01','provider_origin_limit':'No current Drive query. Mirror/source integrity does not establish immediate parents, intervention law, exposure or all-Drive completeness.','completed_utc':now()};local_admission['records'].append(receipt);save(C/'MIRROR_LOCAL_ADMISSION.json',local_admission);print('LOCAL_NATIVE_ADMISSION_PASS',alias,'fresh_native',receipt['fresh_native_network_restore'],flush=True)
 except Exception as e:
  msg=re.sub(r'https?://\S+','[URL REDACTED]',str(e));msg=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',msg);failure={'alias':alias,'candidate_id':h['candidate_id'],'status':'FAILED_PRESERVED','error_class':type(e).__name__,'reason':msg,'completed_member_records':current,'active_failed_file':progress.get('active'),'observed_utc':now()};local_admission['records'].append(failure);save(C/'MIRROR_LOCAL_ADMISSION.json',local_admission);progress['records'].append(failure);progress['active']=None;checkpoint();print('LOCAL_NATIVE_ADMISSION_FAILED',alias,type(e).__name__,msg,flush=True)
progress.update(status='FINITE_NATIVE_RESTORATION_DRAINED',completed_utc=now());checkpoint();print('FINITE_EXACT9MIRROR_NATIVE_RESTORATION_DRAINED',len(local_admission['records']),flush=True)
