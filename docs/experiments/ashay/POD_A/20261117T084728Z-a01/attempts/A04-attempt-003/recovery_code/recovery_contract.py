"""Pure recovery receipt gates: no network, configuration execution, fitting or GPU side effects."""
import hashlib,json,re
from urllib.parse import urlparse,urlunparse

def require(value,reason):
 if not value:raise ValueError(reason)
def payload_gate(record,expected,pre,post):
 require(record.get('status')=='VERIFIED','Unverified/blocked response is not a payload')
 require(record.get('file_id')==expected['file_id'] and pre['id']==post['id']==expected['file_id'],'Provider file identity differs')
 require(record.get('http_status')==200 and 'html' not in record.get('content_type','').lower(),'HTML/error/range response is not complete native payload')
 require(record.get('bytes')==expected['bytes']==int(pre['size'])==int(post['size']),'Payload size differs')
 require(pre.get('modified_time')==post.get('modified_time'),'Provider source changed during transfer')
 require(record.get('prefix_hex')=='504b0304','Unsupported native payload signature')
 require(bool(re.fullmatch('[0-9a-f]{64}',record.get('sha256',''))),'Full SHA256 missing')
 require(expected.get('sha256') is None or record['sha256']==expected['sha256'],'Historical full payload digest differs')
 return True

def resume_gate(offset,status,content_range,source_before,source_now,total):
 require(source_before==source_now,'Partial transfer source identity changed')
 require(bool(source_before.get('immutable_revision') or source_before.get('strong_etag')),'No stable source identity for range resume')
 if offset:
  require(status==206,'Never append full200 response to partial bytes')
  m=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',content_range or '')
  require(m is not None and int(m[1])==offset and offset<=int(m[2])<total and int(m[3])==total,'Invalid content-range offset/length/total')
 else:require(status==200,'Initial complete transfer must return200')
 return True

def identity_gate(unit,expected):
 for key in ['candidate_id','manifest_sha256','runtime_sha256','source_sha256','physical_batch']:
  require(unit.get(key)==expected.get(key),'Qualification identity mismatch: '+key)
 require(unit.get('physical_batch')==8,'Physical8 required')
 return True

def owned_relative(name):
 from pathlib import PurePosixPath
 p=PurePosixPath(name);require(bool(p.parts) and not p.is_absolute() and '..' not in p.parts,'Unsafe recovery path');return str(p)
