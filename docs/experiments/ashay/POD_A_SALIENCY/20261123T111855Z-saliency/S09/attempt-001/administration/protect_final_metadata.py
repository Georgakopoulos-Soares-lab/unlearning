"""Final S09 metadata proof is external to sealed scientific commit; fresh exact restore."""
from ops import C,A,R,save,now
from pathlib import Path,PurePosixPath
import json,hashlib,tarfile,uuid,sys,os,time,urllib.request,urllib.parse,re,collections
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import HfApi,hf_hub_url,get_token,CommitOperationAdd
T=R/'docs/experiments/ashay/POD_A_SALIENCY/20261123T111855Z-saliency';P=T/'S09/attempt-001';read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest();attempt=sys.argv[1];assert re.fullmatch('[0-9]{3}',attempt)
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def error(kind,value,tb):
 reason=re.sub(r'https?://\S+','[URL REDACTED]',str(value));reason=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',reason);save(C/('FINAL_METADATA_FAILED-'+attempt+'.json'),{'status':'FAILED_PRESERVED','exception':kind.__name__,'reason':reason,'utc':now()});print('S09_FINAL_METADATA_RECOVERY_FAILED',kind.__name__,reason,flush=True)
sys.excepthook=error
assert read(P/'S09_RECEIPT.json')['status']=='LIMITED_SCOPE_COMPLETE' and read(C/'S09-science-001-DELIVERY.json')['status']=='PASS'
archive=A/'private-checkpoints/S09-final-metadata-001.tar.gz';snapshot=C/'FINAL_METADATA_SNAPSHOT.json';locfile=C/'FINAL_METADATA_BACKUP_LOCATORS.json';limits={'members':6000,'expanded_bytes':2*1024**3,'member_bytes':128*1024**2}
if not archive.exists():
 entries={}
 def add(name,p):
  q=PurePosixPath(name);assert not q.is_absolute() and '..' not in q.parts and '\\' not in name and name not in entries and p.is_file() and not p.is_symlink() and p.stat().st_size<=limits['member_bytes'];entries[name]=p
 for p in sorted(P.rglob('*')):
  if p.is_file():add('research/S09/attempt-001/'+str(p.relative_to(P)),p)
 for name in ['CONTROLLER_STATE.json','PROGRESS.md','SESSION_HANDOFF.md','EVENTS.jsonl','OUTPUT_SHA256SUMS']:add('research/'+name,T/name)
 for p in sorted(C.iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl','.md'] and not p.name.startswith('FINAL_METADATA_') and not(p.name.endswith('-PROGRESS.json') and read(p).get('status')=='RUNNING'):add('private-control/'+p.name,p)
 for p in sorted((C/'administrative-revisions').rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts:add('private-control/'+str(p.relative_to(C)),p)
 for p in sorted((A/'operation-logs').glob('*.stderr')):
  if p.stat().st_size<1024**2:add('execution-stderr/'+p.name,p)
 deps={'new_S09_scientific_bundle':read(C/'SCIENCE_PRIVATE_LOCATORS.json'),'new_S09_scientific_recovery':read(C/'SCIENCE_PRIVATE_RECOVERY_RECEIPT.json'),'exact_prior_dependencies':read(C/'EXACT_RECOVERY_DEPENDENCIES.json'),'self_reference':'Final metadata upload/readback and finalGitproof remainexternal; no future/selfhashcycles'};save(C/'FINAL_METADATA_DEPENDENCIES.json',deps);add('DEPENDENCIES.json',C/'FINAL_METADATA_DEPENDENCIES.json');expanded=sum(p.stat().st_size for p in entries.values());assert len(entries)<=limits['members'] and expanded<=limits['expanded_bytes'];manifest={'files':{n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in entries.items()},'S09_scientific_commit':read(C/'S09-science-001-DELIVERY.json')['commit'],'S09_receipt_sha256':sha(P/'S09_RECEIPT.json'),'S10_handoff_sha256':sha(P/'S10_HANDOFF.json'),'expanded_bytes':expanded,'created_utc':now()};save(snapshot,manifest);tmp=archive.with_name(archive.name+'.partial');assert not tmp.exists();last=time.monotonic()
 with tarfile.open(tmp,'w:gz',compresslevel=1) as tar:
  for i,(n,p) in enumerate(entries.items()):
   m=tarfile.TarInfo(n);m.size=p.stat().st_size;m.mode=0o600;m.mtime=0
   with p.open('rb') as f:tar.addfile(m,f)
   if time.monotonic()-last>20:print('S09_FINAL_METADATA_PACK',i+1,len(entries),flush=True);last=time.monotonic()
 os.replace(tmp,archive)
else:manifest=read(snapshot)
repo=read(C.parent.parent/'S03/attempt-003/BACKUP_ROUTE_CURRENT.json')['repository'];api=HfApi();info=api.repo_info(repo_id=repo,repo_type='dataset',timeout=45);assert info.private is True;h=sha(archive);size=archive.stat().st_size
if locfile.exists():loc=read(locfile);assert loc['archive_sha256']==h and loc['archive_bytes']==size
else:
 intent=C/'FINAL_METADATA_UPLOAD_INTENT.json'
 if intent.exists():remote=read(intent)['remote_object'];assert read(intent)['archive_sha256']==h
 else:remote='POD_A_SALIENCY/20261123T111855Z-saliency/S09/attempt-001/final-metadata-'+uuid.uuid4().hex+'/'+archive.name;save(intent,{'remote_object':remote,'archive_sha256':h,'archive_bytes':size,'created_utc':now()})
 print('S09_FINAL_METADATA_UPLOAD',size,flush=True);result=api.create_commit(repo_id=repo,repo_type='dataset',operations=[CommitOperationAdd(path_in_repo=remote,path_or_fileobj=str(archive)),CommitOperationAdd(path_in_repo=remote+'.manifest.json',path_or_fileobj=str(snapshot))],parent_commit=info.sha,num_threads=2,commit_message='Protect exact S09 scientific publication, S10 handoff and final administrative evidence');loc={'repository':repo,'revision':result.oid,'remote_object':remote,'archive_sha256':h,'archive_bytes':size,'manifest_remote_object':remote+'.manifest.json','manifest_sha256':sha(snapshot),'manifest_bytes':snapshot.stat().st_size};save(locfile,loc)
assert api.repo_info(repo_id=repo,repo_type='dataset',revision=loc['revision'],timeout=45).private is True;consumer=A/('final-metadata-fresh-consumer-'+attempt);assert not consumer.exists();consumer.mkdir();token=get_token();assert token
class Redirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,url):
  nxt=super().redirect_request(req,fp,code,msg,headers,url)
  if nxt and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(url).hostname:nxt.remove_header('Authorization')
  return nxt
def download(remote,dest,count_expected,sha_expected):
 req=urllib.request.Request(hf_hub_url(repo_id=repo,repo_type='dataset',revision=loc['revision'],filename=remote),headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache'});count=0;dg=hashlib.sha256()
 with urllib.request.build_opener(Redirect()).open(req,timeout=45) as response,dest.open('xb') as f:
  assert response.status==200 and response.headers.get('Content-Range') is None
  while True:
   b=response.read(1024**2)
   if not b:break
   count+=len(b);assert count<=count_expected;f.write(b);dg.update(b)
  f.flush();os.fsync(f.fileno())
 assert count==count_expected and dg.hexdigest()==sha_expected
download(loc['remote_object'],consumer/'checkpoint.tar.gz',size,h);download(loc['manifest_remote_object'],consumer/'manifest.json',loc['manifest_bytes'],loc['manifest_sha256']);assert read(consumer/'manifest.json')==manifest;sys.path.insert(0,str(A/'code'));from safe_archive import restore
restored=consumer/'restored';stats=restore(consumer/'checkpoint.tar.gz',manifest['files'],restored,limits);public=restored/'research/S09/attempt-001';assert sha(public/'S09_RECEIPT.json')==manifest['S09_receipt_sha256'] and sha(public/'S10_HANDOFF.json')==manifest['S10_handoff_sha256'];assert read(public/'PRIVATE_RECOVERY_PROOF.json')['status']=='PASS';admitted=[json.loads(l) for l in (public/'FROZEN_ADMITTED_KEYS.jsonl').read_text().splitlines()];deferred=[json.loads(l) for l in (public/'FROZEN_DEFERRED_KEYS.jsonl').read_text().splitlines()];actual=[]
for p in sorted((public/'contrasts').glob('*/*/CONTRASTS.jsonl')):actual.extend(json.loads(l) for l in p.read_text().splitlines())
assert len(actual)==len({r['id'] for r in actual})==48924 and {r['id'] for r in actual}=={r['id'] for r in admitted}
disposition={'admitted_counts':dict(collections.Counter(r['f'] for r in actual)),'deferred_counts':dict(collections.Counter(r['f'] for r in deferred)),'intended_keys':91152,'completed_admitted_exact_keys':48924,'deferred_exact_keys':42228,'admitted_set_sha256':digest(sorted(r['id'] for r in actual)),'deferred_set_sha256':digest(sorted(r['id'] for r in deferred)),'base_reference_is_not_immediate_parent':True};assert disposition==read(public/'COMPARISON_DISPOSITION.json')
regen=restored/'regenerated-mappings';regen.mkdir();save(regen/'COMPARISON_DISPOSITION.json',disposition);assert sha(regen/'COMPARISON_DISPOSITION.json')==sha(public/'COMPARISON_DISPOSITION.json')
handoff=read(public/'S10_HANDOFF.json');rebuilt=dict(handoff);rebuilt.update(verified_comparison_counts=disposition['admitted_counts'],deferred_comparison_counts=disposition['deferred_counts'],all_admitted_keys=len(actual),all_deferred_keys=len(deferred),all_intended_keys=len(actual)+len(deferred),draw_differences=sum(r['bootstrap_attempted'] for r in actual),figures=read(public/'FIGURE_MANIFEST.json')['figures'],comparison_verification_sha256=sha(public/'CONTRAST_VERIFICATION.json'),exact_worst_component_sha256=sha(public/'WORST_RESIDUAL_LOCATION.json'),comparison_disposition_sha256=sha(public/'COMPARISON_DISPOSITION.json'),private_recovery_proof_sha256=sha(public/'PRIVATE_RECOVERY_PROOF.json'),S10_requirements_sha256=sha(public/'S10_INPUT_REQUIREMENTS.json'),limits_sha256=sha(public/'LIMITATIONS.json'));assert rebuilt==handoff;save(regen/'S10_HANDOFF.json',rebuilt);assert sha(regen/'S10_HANDOFF.json')==sha(public/'S10_HANDOFF.json')
phase=read(public/'S09_RECEIPT.json');assert phase['status']=='LIMITED_SCOPE_COMPLETE' and phase['verified_units']==len(actual)
for n,h0 in phase['output_sha256'].items():assert sha(public/n)==h0,n
controller=read(restored/'research/CONTROLLER_STATE.json');assert not controller['approvals']['S10']['approved'] and controller['phase_receipts']['S09']['sha256']==sha(public/'S09_RECEIPT.json');assert api.repo_info(repo_id=repo,repo_type='dataset',revision=loc['revision'],timeout=45).private is True
receipt={'status':'PASS','immutable_revision':loc['revision'],'archive_sha256':h,'archive_bytes':size,'manifest_sha256':loc['manifest_sha256'],'manifest_bytes':loc['manifest_bytes'],'private_at_upload_and_readback':True,'fresh_HTTP_body_bytes':size+loc['manifest_bytes'],'SDK_download_cache_used':False,'exact_member_bytes':stats,'scientific_commit':manifest['S09_scientific_commit'],'S09_receipt_sha256':manifest['S09_receipt_sha256'],'S10_handoff_sha256':manifest['S10_handoff_sha256'],'regenerated_mappings':{n:sha(regen/n) for n in ['COMPARISON_DISPOSITION.json','S10_HANDOFF.json']},'all_receipt_output_hashes_reconciled':True,'S10_approved_or_executed':False,'scientific_replay_in_this_administrative_step':False,'prior_exhaustive_scientific_replay':'SCIENCE_PRIVATE_RECOVERY_RECEIPT.json all48924fullvectors and111figures PASS','producer_data_fallback':False,'executed_recipe_sha256':sha(Path(__file__)),'self_reference':'FinalGitpublication/proof external tothisarchive; no recursivefuture hashes','completed_utc':now()};save(C/'FINAL_METADATA_RECOVERY_RECEIPT.json',receipt);save(P/'FINAL_METADATA_RECOVERY.json',receipt);print('S09_FINAL_METADATA_FRESH_PROTECTED_RESTORE_PASS',loc['revision'],stats['members'],flush=True)
