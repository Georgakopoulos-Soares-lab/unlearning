"""Append-only private metadata/integration backup, fresh exact restore and declared regeneration."""
from ops import C,A,R
from long_run import execute
from pathlib import Path,PurePosixPath
import sys,os,json,hashlib,tarfile,uuid,time,re,urllib.request,urllib.parse,fcntl
sys.path.insert(0,str(A/'code'));from common import P,T,BASE,RUN,read,rows,sha,save,now,digest
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import HfApi,hf_hub_url,get_token,CommitOperationAdd
mode,attempt=sys.argv[1:];assert mode in ['science','final'] and re.fullmatch('[0-9]{3}',attempt);prefix='PRIVATE_SCIENCE' if mode=='science' else 'FINAL_METADATA';locfile=C/('PRIVATE_SCIENCE_LOCATORS.json' if mode=='science' else 'FINAL_METADATA_BACKUP_LOCATORS.json');snapshot=C/(prefix+'_MEMBER_MANIFEST.json');archive=A/'private-checkpoints'/('S10-'+mode+'-'+attempt+'.tar.gz');archive.parent.mkdir(exist_ok=True);limits=read(C/'RECOVERY_CONTRACT.json')['limits']
def failure(kind,value,tb):
 message=re.sub(r'https?://\S+','[URL REDACTED]',str(value));message=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',message);save(C/(prefix+'-FAILED-'+attempt+'.json'),{'status':'FAILED_PRESERVED','type':kind.__name__,'reason':message,'utc':now()});print('S10_PRIVATE_RECOVERY_FAILED',mode,kind.__name__,message,flush=True)
sys.excepthook=failure
with (C/'PRIVATE_RECOVERY.lock').open('a') as writer:
 fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert read(C/'OUTPUT_VALIDATION.json')['status']=='PASS'
 if mode=='final':assert read(P/'S10_RECEIPT.json')['status']=='LIMITED_SCOPE_COMPLETE' and read(C/'S10-science-001-DELIVERY.json')['status']=='PASS'
 if not archive.exists():
  entries={}
  def add(name,p):
   p=Path(p);q=PurePosixPath(name);assert not q.is_absolute() and '..' not in q.parts and '\\' not in name and str(q)==name and name not in entries and p.is_file() and not p.is_symlink() and p.stat().st_size<=limits['member_bytes'];entries[name]=p
  for directory in ['inputs','code']:
   for p in sorted((A/directory).rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:add(directory+'/'+str(p.relative_to(A/directory)),p)
  for p in sorted(P.rglob('*')):
   if p.is_file():add('public/'+str(p.relative_to(P)),p)
  for p in sorted(C.iterdir()):
   if p.is_file() and p.suffix in ['.json','.jsonl','.md','.py'] and not p.name.startswith(prefix) and not(p.name.endswith('-PROGRESS.json') and read(p).get('status')=='RUNNING'):add('control/'+p.name,p)
  if mode=='final':
   for name in ['CONTROLLER_STATE.json','PROGRESS.md','SESSION_HANDOFF.md','EVENTS.jsonl','OUTPUT_SHA256SUMS']:add('root/'+name,T/name)
   for p in sorted((C/'administrative-revisions').rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:add('control/'+str(p.relative_to(C)),p)
   for stem in ['S10-canonical-seal-001','S10-canonical-global-close-001','S10-canonical-close-resume-002','S10-canonical-global-close-002']:
    for suffix in ['.stdout','.stderr']:
     p=A/'operation-logs'/(stem+suffix)
     if p.is_file():add('repair-logs/'+p.name,p)
  c9=C.parent.parent/'S09/attempt-001';deps={'S09_final_commit':'3c39552d43c2e4c8aaf223ca97e3b8f6ee33d11c','S09_scientific_payload':read(c9/'SCIENCE_PRIVATE_LOCATORS.json'),'S09_final_metadata':read(c9/'FINAL_METADATA_BACKUP_LOCATORS.json'),'S09_external_actual_exit_witness':read(c9/'FINAL_ACTUAL_EXIT_WITNESS.json'),'scope':'ExactpreviouslargeS09dependenciesbyimmutable receipts; no weights/probabilities/draw payloads repacked or rehashed. NewS10inputs/code/metadata assessment only.','self_reference':'Currentarchive/upload/readback/futureGitproof external, no recursive future hashes'}
  if mode=='final':deps['S10_assessment_payload']=read(C/'PRIVATE_SCIENCE_LOCATORS.json');deps['S10_assessment_recovery']=read(C/'PRIVATE_RECOVERY_RECEIPT.json')
  dep=C/(prefix+'_DEPENDENCIES.json');save(dep,deps);add('DEPENDENCIES.json',dep);expanded=sum(p.stat().st_size for p in entries.values());assert len(entries)<=limits['members'] and expanded<=limits['expanded_bytes'];manifest={'files':{n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in entries.items()},'expanded_bytes':expanded,'mode':mode,'S11_handoff_sha256':sha(P/'S11_HANDOFF.json'),'S10_science_commit':read(C/'S10-science-001-DELIVERY.json')['commit'] if mode=='final' else None,'created_utc':now()};save(snapshot,manifest);tmp=archive.with_name(archive.name+'.partial');assert not tmp.exists()
  with tarfile.open(tmp,'w:gz',compresslevel=1) as tar:
   for name,p in entries.items():
    member=tarfile.TarInfo(name);member.size=p.stat().st_size;member.mode=0o600;member.mtime=0
    with p.open('rb') as f:tar.addfile(member,f)
  os.replace(tmp,archive)
 else:manifest=read(snapshot)
 api=HfApi();repo=read(C.parent.parent/'S03/attempt-003/BACKUP_ROUTE_CURRENT.json')['repository'];info=api.repo_info(repo_id=repo,repo_type='dataset',timeout=45);assert info.private is True;archive_sha=sha(archive);size=archive.stat().st_size
 if locfile.exists():loc=read(locfile);assert loc['archive_sha256']==archive_sha and loc['archive_bytes']==size
 else:
  intent=C/(prefix+'_UPLOAD_INTENT.json')
  if intent.exists():remote=read(intent)['remote_object'];assert read(intent)['archive_sha256']==archive_sha
  else:remote='POD_A_SALIENCY/'+RUN+'/S10/attempt-001/'+mode+'-'+uuid.uuid4().hex+'/'+archive.name;save(intent,{'remote_object':remote,'archive_sha256':archive_sha,'archive_bytes':size,'created_utc':now()})
  print('S10_PRIVATE_UPLOAD',mode,size,flush=True);result=api.create_commit(repo_id=repo,repo_type='dataset',operations=[CommitOperationAdd(path_in_repo=remote,path_or_fileobj=str(archive)),CommitOperationAdd(path_in_repo=remote+'.manifest.json',path_or_fileobj=str(snapshot))],parent_commit=info.sha,num_threads=1,commit_message='Protect S10 '+mode+' external-evidence assessment and exact retain-only S11 handoff');loc={'repository':repo,'revision':result.oid,'remote_object':remote,'archive_sha256':archive_sha,'archive_bytes':size,'manifest_remote_object':remote+'.manifest.json','manifest_sha256':sha(snapshot),'manifest_bytes':snapshot.stat().st_size};save(locfile,loc)
 assert api.repo_info(repo_id=repo,repo_type='dataset',revision=loc['revision'],timeout=45).private is True;consumer=A/'fresh-consumers'/(mode+'-HTTP-'+attempt);assert not consumer.exists();consumer.mkdir(parents=True);token=get_token();assert token
 class Redirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,req,fp,code,msg,headers,newurl):
   request=super().redirect_request(req,fp,code,msg,headers,newurl)
   if request and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:request.remove_header('Authorization')
   return request
 def download(remote,dest,expected_size,expected_sha):
  request=urllib.request.Request(hf_hub_url(repo_id=repo,repo_type='dataset',revision=loc['revision'],filename=remote),headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache'});count=0;h=hashlib.sha256()
  with urllib.request.build_opener(Redirect()).open(request,timeout=45) as response,dest.open('xb') as f:
   assert response.status==200 and response.headers.get('Content-Range') is None
   while True:
    b=response.read(1024**2)
    if not b:break
    count+=len(b);assert count<=expected_size;f.write(b);h.update(b)
   f.flush();os.fsync(f.fileno())
  assert count==expected_size and h.hexdigest()==expected_sha
 download(loc['remote_object'],consumer/'checkpoint.tar.gz',size,archive_sha);download(loc['manifest_remote_object'],consumer/'member-manifest.json',loc['manifest_bytes'],loc['manifest_sha256']);assert read(consumer/'member-manifest.json')==manifest
 from safe_archive import restore
 restored=consumer/'restored';stats=restore(consumer/'checkpoint.tar.gz',manifest['files'],restored,limits);print('S10_EXACT_PRIVATE_RESTORE_PASS',mode,stats['members'],flush=True)
 if mode=='science':
  environment={'PATH':'/usr/local/bin:/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','PYTHONNOUSERSITE':'1','HF_HUB_OFFLINE':'1'}
  child=execute('S10-fresh-assessment-regeneration-'+attempt,['/usr/local/bin/python3',str(restored/'code/recover.py'),str(restored)],environment);replay=read(restored/'RECOVERY_RESULT.json');assert child['exit_status']==0 and replay['status']=='PASS' and replay['candidate_assessments_regenerated']==9 and replay['external_source_records']==0
 else:
  pub=restored/'public';phase=read(pub/'S10_RECEIPT.json');assert phase['status']=='LIMITED_SCOPE_COMPLETE' and phase['verified_units']==9
  for n,h in phase['output_sha256'].items():assert sha(pub/n)==h
  s11=read(pub/'S11_HANDOFF.json');assert sha(pub/'S11_HANDOFF.json')==manifest['S11_handoff_sha256'] and s11['S11_permitted_scope']=='RETAIN_ONLY_WITH_EXTERNAL_FORGET_INTEGRATION_PENDING' and not s11['S11_approved'];state=read(restored/'root/CONTROLLER_STATE.json');assert not state['approvals']['S11']['approved'] and state['phase_state']['S10']['external_dependency_disposition']=='PENDING'
  joined=read(pub/'EXACT_JOIN_ELIGIBILITY.json');replay={'status':'PASS','candidate_assessments_reconciled':len(joined['candidate_coverage']),'source_record_joins':len(joined['record_join_decisions']),'all_phase_receipt_output_hashes_verified':True,'S11_handoff_sha256':sha(pub/'S11_HANDOFF.json'),'actual_scientific_commit':manifest['S10_science_commit'],'dependency_disposition':'PENDING','S11_scope':s11['S11_permitted_scope'],'scientific_or_external_evaluation_repeated':False};assert replay['candidate_assessments_reconciled']==9 and replay['source_record_joins']==0
 assert api.repo_info(repo_id=repo,repo_type='dataset',revision=loc['revision'],timeout=45).private is True
 proof={'schema_version':'s10-'+mode+'-private-recovery-v1','status':'PASS','immutable_revision':loc['revision'],'archive_sha256':archive_sha,'archive_bytes':size,'member_manifest_sha256':loc['manifest_sha256'],'member_manifest_bytes':loc['manifest_bytes'],'private_at_upload_and_readback':True,'fresh_HTTP_body_bytes':size+loc['manifest_bytes'],'uploaded_application_bytes':size+loc['manifest_bytes'],'SDK_download_cache_used':False,'exact_safe_regular_members':stats,'regeneration_or_reconciliation':replay,'producer_data_fallback':False,'model_probe_bootstrap_external_evaluation_replay':False,'clean_runtime_recreation_claim':False,'actual_child_exit_status':child['exit_status'] if mode=='science' else None,'administrative_recipe_sha256':sha(Path(__file__)),'completed_utc':now()};dest=C/('PRIVATE_RECOVERY_RECEIPT.json' if mode=='science' else 'FINAL_METADATA_RECOVERY_RECEIPT.json');save(dest,proof);save(P/('PRIVATE_RECOVERY_PROOF.json' if mode=='science' else 'FINAL_METADATA_RECOVERY.json'),proof);print('S10_PRIVATE_RECOVERY_PASS',mode,loc['revision'],flush=True)
