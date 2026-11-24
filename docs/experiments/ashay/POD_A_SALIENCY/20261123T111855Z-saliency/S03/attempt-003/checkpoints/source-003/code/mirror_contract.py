"""Pure exact-mirror admission and resume contracts; no network or model execution."""
from pathlib import PurePosixPath,Path
import hashlib,re,json,fcntl
ALLOWED={'.metadata','common.pt','metadata.json','run_config.yaml','sidecars/latest_checkpointed_iteration.txt','tokenizer/tokenizer.json','tokenizer/tokenizer_config.json','train_state.pt','__0_0.distcp'}
SHA=re.compile(r'^[0-9a-f]{64}$');REV=re.compile(r'^[0-9a-f]{40}$')
def need(v,msg):
 if not v:raise ValueError(msg)
def safe(name):
 p=PurePosixPath(name);need(isinstance(name,str) and bool(name) and not p.is_absolute() and '\\' not in name and name==str(p) and all(x not in ['.','..',''] for x in name.split('/')),'Unsafe or noncanonical member path');return name
def admit(handoff,receipt,manifest,selected,source_members):
 h=handoff;alias=h['alias'];need(selected.get(alias)==h['candidate_id'],'Candidate alias/discovery binding differs');need(REV.fullmatch(h['payload_revision']) and REV.fullmatch(h['receipt_revision']),'Unpinned HF revision')
 for key in ['alias','candidate_id','repo_id','repo_type','payload_revision','path','manifest_path','manifest_sha256','native_shard_sha256','payload_bytes','payload_files_verified','status','scientific_qualification']:
  need(receipt.get(key)==h.get(key),'Receipt/handoff mismatch: '+key)
 need(h['status']=='PASS_PRIVATE_MIRROR_BYTE_READBACK' and h['scientific_qualification']=='NOT_PERFORMED','Transport receipt is not scientific qualification');need(receipt['local_cache_used_for_readback'] is False and receipt['fresh_network_readback_files']==10,'Receipt readback scope differs');need(receipt.get('private_at_upload_and_readback') is True or receipt.get('private_at_upload_and_readback') is None and receipt.get('private_during_recovery_and_readback') is True,'Recovery/readback privacy not established')
 c=manifest['candidate'];need(c['alias']==alias and 'drive-checkpoint:'+c['folder_id']==h['candidate_id'],'Manifest original discovery differs');need(manifest['scientific_qualification']=='NOT_PERFORMED','Manifest scientific state differs');files=manifest['files'];need(isinstance(files,list) and len(files)==9,'Expected exact9payload members');names=[safe(f['path']) for f in files];need(len(set(names))==9 and set(names)==ALLOWED,'Missing, duplicate or unexpected mirror member');need(sum(f['bytes'] for f in files)==h['payload_bytes'],'Payload byte total differs')
 for f in files:
  need(isinstance(f['bytes'],int) and not isinstance(f['bytes'],bool) and f['bytes']>0 and SHA.fullmatch(f['sha256']),'Invalid size/digest');src=f['source_file_id'];need(src in source_members,'Original Drive source ID absent from sealed provenance');expected=source_members[src];need(f['path'].rsplit('/',1)[-1]==expected['name'],'Original member name differs')
  if expected.get('sha256') is not None:need(f['sha256']==expected['sha256'],'Sealed original SHA differs')
  if expected.get('bytes') is not None:need(f['bytes']==expected['bytes'],'Sealed original size differs')
  if f.get('expected_historical_sha256') is not None:need(f['sha256']==f['expected_historical_sha256'],'Supplied expected digest differs')
  meta=f.get('source_metadata',{});need(meta.get('id')==src and int(meta.get('size',0))==f['bytes'],'Transfer source metadata identity/size differs')
  if meta.get('sha256Checksum') is not None:need(meta['sha256Checksum']==f['sha256'],'Provider-declared transferred SHA differs')
 native=next(f for f in files if f['path']=='__0_0.distcp');need(native['source_file_id']==c['native_id'] and native['bytes']==c['native_bytes'] and native['sha256']==h['native_shard_sha256'],'Native shard binding differs')
 return {'alias':alias,'candidate_id':h['candidate_id'],'payload_revision':h['payload_revision'],'receipt_revision':h['receipt_revision'],'manifest_sha256':h['manifest_sha256'],'receipt_sha256':h['receipt_sha256'],'files':files,'payload_bytes':h['payload_bytes'],'private_original_upload':receipt.get('private_at_upload_and_readback'),'private_recovery_readback':True,'status':'REMOTE_EXACT_CONTENT_AND_SOURCE_JOINS_PASS'}
def compatible_resume(record,expected,partial_bytes):
 for k in ['repo_id','revision','remote_path','expected_bytes','expected_sha256']:need(record.get(k)==expected.get(k),'Partial transfer binding differs: '+k)
 need(0<=partial_bytes<expected['expected_bytes'],'Partial byte range invalid');return partial_bytes
def response_range(status,content_range,start,total):
 if start==0:need(status==200 and content_range is None,'Unexpected partial full-file response');return
 need(status==206,'Server ignored requested compatible range');m=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',content_range or '');need(m is not None and int(m[1])==start and int(m[2])==total-1 and int(m[3])==total,'Wrong resumed content range')
def verify_bytes(path,expected):
 p=Path(path);need(p.is_file() and not p.is_symlink() and p.stat().st_size==expected['bytes'],'Payload missing/size/link differs')
 with p.open('rb') as f:need(not f.read(128).startswith(b'version https://git-lfs.github.com/spec/v1'),'LFS pointer stub rejected')
 with p.open('rb') as f:need(hashlib.file_digest(f,'sha256').hexdigest()==expected['sha256'],'Payload full digest differs')
 return True
