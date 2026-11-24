"""Bounded direct-HTTP immutable archive readback; bypasses SDK file/Xet caches."""
from pathlib import Path,PurePosixPath
import os,sys,json,hashlib,urllib.request,urllib.parse,tarfile,re
from huggingface_hub import HfApi,hf_hub_url,get_token
from ops import C,A,save,now
# Preserve useful failure identity without ever printing signed redirect URLs or credentials.
def sanitized_failure(kind,value,tb):
 message=re.sub(r'https?://\S+','[URL REDACTED]',str(value));message=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',message)
 print('EXPLICIT_NETWORK_READBACK_FAILED',kind.__name__,message,flush=True)
 if len(sys.argv)>1:save(C/(sys.argv[1]+'-HTTP_READBACK_FAILURE.json'),{'status':'FAILED_PRESERVED','exception_type':kind.__name__,'reason':message,'observed_utc':now()})
sys.excepthook=sanitized_failure
target=sys.argv[1];old=C.with_name('attempt-001')
if target=='prior-candidate01':locfile=old/'qualification-checkpoint-001-LOCATORS.json';evidence=old/'qualification-checkpoint-001-RECEIPT.json'
elif target=='prior-reference02':locfile=old/'qualification-checkpoint-002-LOCATORS.json';evidence=old/'qualification-checkpoint-002-RECEIPT.json'
else:
 assert target in {f'candidate_{i:02d}' for i in range(2,10)};locfile=C/(target+'-PRIVATE_BACKUP_LOCATORS.json');evidence=C/(target+'-PRIVATE_BACKUP_RECEIPT.json')
loc=json.loads(locfile.read_text());expected=json.loads(evidence.read_text());revision=loc.get('revision',loc.get('immutable_revision'));assert re.fullmatch('[0-9a-f]{40}',revision);h=loc['archive_sha256'];size=expected['archive_bytes'];assert h==expected['archive_sha256'] and size<32*1024**2;consumer=A/'fresh-consumers'/(target+'-explicit-http-001');restored=A/'fresh-consumers'/(target+'-explicit-http-restored-001');assert not consumer.exists() and not restored.exists();consumer.mkdir(parents=True);path=consumer/'archive.tar.gz';tmp=consumer/'archive.tar.gz.partial';api=HfApi();assert api.repo_info(repo_id=loc['repository'],repo_type='dataset',revision=revision,timeout=45).private is True;token=get_token();assert token
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  nxt=super().redirect_request(req,fp,code,msg,headers,newurl)
  if nxt and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:nxt.remove_header('Authorization')
  return nxt
opener=urllib.request.build_opener(Redirect());url=hf_hub_url(repo_id=loc['repository'],repo_type='dataset',revision=revision,filename=loc['remote_object']);request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache','Pragma':'no-cache'});count=0;digest=hashlib.sha256()
with opener.open(request,timeout=45) as response,tmp.open('xb') as out:
 assert response.status==200 and response.headers.get('Content-Range') is None and 'text/html' not in response.headers.get('Content-Type','');length=response.headers.get('Content-Length');assert length is None or int(length)==size
 while True:
  chunk=response.read(1024**2)
  if not chunk:break
  count+=len(chunk);assert count<=size;out.write(chunk);digest.update(chunk)
 out.flush();os.fsync(out.fileno())
assert count==size and digest.hexdigest()==h;tmp.rename(path);restored.mkdir();seen=set();total=0
with tarfile.open(path,'r:gz') as tar:
 members=tar.getmembers();man=tar.extractfile('MEMBER_MANIFEST.json').read();manifest=json.loads(man);files=manifest['files'];assert {m.name for m in members}==set(files)|{'MEMBER_MANIFEST.json'}
 for m in members:
  p=PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and '\\' not in m.name and m.name not in seen;seen.add(m.name);total+=m.size;assert total<32*1024**2 and m.size<8*1024**2;data=tar.extractfile(m).read();dest=restored/m.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
  if m.name!='MEMBER_MANIFEST.json':assert len(data)==files[m.name]['bytes'] and hashlib.sha256(data).hexdigest()==files[m.name]['sha256']
assert api.repo_info(repo_id=loc['repository'],repo_type='dataset',revision=revision,timeout=45).private is True
result={'schema_version':'s03-explicit-network-readback-v1','target':target,'status':'EXPLICIT_HTTP_NETWORK_EXACT_MEMBER_RESTORE_PASS','immutable_revision':revision,'archive_sha256':h,'archive_bytes':size,'HTTP_body_bytes_received':count,'file_or_Xet_cache_used':False,'fresh_network_transport':'Direct urllib HTTPS GET from exact HF revision with cache-control/no-cache, new consumer, explicit body read; no SDK download/file/chunk cache path','destination_private':True,'exact_member_hash_set_verified':True,'payload_members':len(files),'restored_root':str(restored),'producer_fallback':False,'source_previous_byte_readback_receipt_sha256':hashlib.sha256(evidence.read_bytes()).hexdigest(),'reason_for_additional_trust_boundary':'Installed Hub download can use Xet chunk caching even with force_download. Earlier API-forced downloads remain hash-valid; this direct transport strengthens the fresh-network claim. No GPU rerun.','completed_utc':now()};save(C/(target+'-HTTP_READBACK_RECEIPT.json'),result);print('EXPLICIT_NETWORK_READBACK_PASS',target,revision,count,len(files),flush=True)
