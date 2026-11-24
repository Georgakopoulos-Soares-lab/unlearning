"""Append-only immutable private bundle, fresh HTTP recovery and exhaustive regeneration."""
from pathlib import Path,PurePosixPath
import os,sys,json,hashlib,tarfile,uuid,time,urllib.request,urllib.parse,re,fcntl
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import HfApi,hf_hub_url,get_token,CommitOperationAdd
from ops import C,A,save,now
from long_run import execute
R=Path('/workspace/pod-a-saliency/research-POD_A_SALIENCY');T=R/'docs/experiments/ashay/POD_A_SALIENCY/20261123T111855Z-saliency';P=T/'S09/attempt-001';read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
attempt=sys.argv[1];assert re.fullmatch('[0-9]{3}',attempt);label='S09-science-'+attempt
def error(kind,value,tb):
 reason=re.sub(r'https?://\S+','[URL REDACTED]',str(value));reason=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',reason);save(C/(label+'-FAILED.json'),{'status':'FAILED_PRESERVED','exception':kind.__name__,'reason':reason,'utc':now()});print('S09_PRIVATE_RECOVERY_FAILED',kind.__name__,reason,flush=True)
sys.excepthook=error
limits=read(C/'RECOVERY_CONTRACT.json')['archive_limits'];archive=A/'private-checkpoints/S09-scientific-evidence-001.tar.gz';archive.parent.mkdir(exist_ok=True);snapshot=C/'SCIENCE_PRIVATE_SNAPSHOT.json';locfile=C/'SCIENCE_PRIVATE_LOCATORS.json'
with (C/'PRIVATE_RECOVERY.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if not archive.exists():
  entries={}
  def add(n,p):
   p=Path(p);q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts and '\\' not in n and str(q)==n and p.is_file() and not p.is_symlink() and p.stat().st_size<=limits['member_bytes'];assert n not in entries;entries[n]=p
  for directory in ['endpoints','contrasts','reporting-inputs','code']:
   for p in sorted((A/directory).rglob('*')):
    if p.is_file() and '__pycache__' not in p.parts:add(str(p.relative_to(A)),p)
  for name in ['FROZEN_ADMITTED_KEYS.jsonl','FROZEN_DEFERRED_KEYS.jsonl']:add('frozen/'+name,C/name)
  for p in sorted(P.rglob('*')):
   if p.is_file() and not p.name.endswith('.lock'):add('public/'+str(p.relative_to(P)),p)
  for name in ['RECOVERY_CONTRACT.json','SOURCE_IDENTITY.json','READINESS.json','APPROVAL_RECORD.json','CPU_ENVIRONMENT_LOCK.json','PLOT_ENVIRONMENT_LOCK.json','PLOT_INSTALL_REPORT.json','REPORTING_PLAN.json','RESOURCE_ADMISSION.json','REFERENCE_RECOVERY_RECEIPT.json']:add('control/'+name,C/name)
  deps={'source_phases':{},'original_reference_archives':read(C.parent.parent/'S03/attempt-001/qualification-checkpoint-002-DEPENDENCY_GRAPH.json')['historical_archives'],'CPU_runtime_install_report':read(C.parent.parent/'S03/attempt-001/CPU_REFERENCE_INSTALL_REPORT.json'),'scope':'Compact endpointstatistics/originalDEVdraws/rowmetadata reproduceallS09contrasts. Nativeweights/features/originalheadsunchanged byexactpriorprivatereferences; no repack/fitting/GPU/cleanruntimeclaim.'}
  for phase in ['S05','S06','S07','S08']:
   cc=C.parent.parent/(phase+'/attempt-001');deps['source_phases'][phase]={'candidates':{p.name.split('-PRIVATE_RECOVERY_LOCATORS.json')[0]:read(p) for p in sorted(cc.glob('candidate_*-PRIVATE_RECOVERY_LOCATORS.json'))},'final_metadata':read(cc/'FINAL_METADATA_BACKUP_LOCATORS.json')}
  save(C/'EXACT_RECOVERY_DEPENDENCIES.json',deps);add('DEPENDENCIES.json',C/'EXACT_RECOVERY_DEPENDENCIES.json')
  expanded=sum(p.stat().st_size for p in entries.values());assert len(entries)<=limits['members'] and expanded<=limits['expanded_bytes'];manifest={n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in entries.items()};save(snapshot,{'files':manifest,'expanded_bytes':expanded,'scope':'AllnewS09sufficientendpoints/contrasts/source/code/publicfigures and metadata','created_utc':now()});tmp=archive.with_name(archive.name+'.partial');assert not tmp.exists();last=time.monotonic()
  with tarfile.open(tmp,'w:gz',compresslevel=1) as tar:
   for i,(name,p) in enumerate(entries.items()):
    m=tarfile.TarInfo(name);m.size=p.stat().st_size;m.mode=0o600;m.mtime=0
    with p.open('rb') as f:tar.addfile(m,f)
    if time.monotonic()-last>=20:print('S09_PRIVATE_PACK',i+1,len(entries),flush=True);last=time.monotonic()
  os.replace(tmp,archive)
 else:manifest=read(snapshot)['files']
 h=sha(archive);size=archive.stat().st_size;api=HfApi();repo=read(C.parent.parent/'S03/attempt-003/BACKUP_ROUTE_CURRENT.json')['repository'];info=api.repo_info(repo_id=repo,repo_type='dataset',timeout=45);assert info.private is True
 if locfile.exists():
  loc=read(locfile);assert loc['archive_sha256']==h and loc['archive_bytes']==size
 else:
  intent=C/'SCIENCE_PRIVATE_UPLOAD_INTENT.json'
  if intent.exists():remote=read(intent)['remote_object'];assert read(intent)['archive_sha256']==h
  else:remote='POD_A_SALIENCY/20261123T111855Z-saliency/S09/attempt-001/science-'+uuid.uuid4().hex+'/'+archive.name;save(intent,{'remote_object':remote,'archive_sha256':h,'created_utc':now()})
  print('S09_PRIVATE_UPLOAD',size,flush=True);result=api.create_commit(repo_id=repo,repo_type='dataset',operations=[CommitOperationAdd(path_in_repo=remote,path_or_fileobj=str(archive)),CommitOperationAdd(path_in_repo=remote+'.manifest.json',path_or_fileobj=str(snapshot))],parent_commit=info.sha,num_threads=2,commit_message='Protect S09 exhaustive paired benign analysis, endpoint evidence and complete figure atlas');loc={'repository':repo,'revision':result.oid,'remote_object':remote,'archive_sha256':h,'archive_bytes':size,'manifest_remote_object':remote+'.manifest.json','manifest_sha256':sha(snapshot),'manifest_bytes':snapshot.stat().st_size};save(locfile,loc)
 assert api.repo_info(repo_id=repo,repo_type='dataset',revision=loc['revision'],timeout=45).private is True
 consumer=A/'fresh-consumers'/('science-HTTP-'+attempt);assert not consumer.exists();consumer.mkdir(parents=True);token=get_token();assert token
 class Redirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,req,fp,code,msg,headers,url):
   nxt=super().redirect_request(req,fp,code,msg,headers,url)
   if nxt and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(url).hostname:nxt.remove_header('Authorization')
   return nxt
 def download(remote,dest,expected_size,expected_sha):
  req=urllib.request.Request(hf_hub_url(repo_id=repo,repo_type='dataset',revision=loc['revision'],filename=remote),headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache'});count=0;digest=hashlib.sha256();last=time.monotonic()
  with urllib.request.build_opener(Redirect()).open(req,timeout=45) as response,dest.open('xb') as f:
   assert response.status==200 and response.headers.get('Content-Range') is None
   while True:
    b=response.read(1024**2)
    if not b:break
    count+=len(b);assert count<=expected_size;f.write(b);digest.update(b)
    if time.monotonic()-last>=20:print('S09_PRIVATE_FRESH_BODY',count,expected_size,flush=True);last=time.monotonic()
   f.flush();os.fsync(f.fileno())
  assert count==expected_size and digest.hexdigest()==expected_sha
 download(loc['remote_object'],consumer/'checkpoint.tar.gz',size,h);download(loc['manifest_remote_object'],consumer/'manifest.json',loc['manifest_bytes'],loc['manifest_sha256']);assert read(consumer/'manifest.json')==read(snapshot)
 sys.path.insert(0,str(A/'code'));from safe_archive import restore
 restored=consumer/'restored';stats=restore(consumer/'checkpoint.tar.gz',read(consumer/'manifest.json')['files'],restored,limits);print('S09_EXACT_RESTORE_PASS',stats,flush=True)
 cpu=str(A.parent.parent/'S03/attempt-001/cpu-reference-runtime/bin/python');plot=str(A/'plot-runtime/bin/python');env={'PATH':str(Path(cpu).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','HF_HUB_OFFLINE':'1','MPLCONFIGDIR':str(consumer/'plot-config')}
 with (C/'CPU_STAGE.lock').open('a') as cpu_lock:
  fcntl.flock(cpu_lock,fcntl.LOCK_EX|fcntl.LOCK_NB);job=execute('S09-exhaustive-fresh-numerics-'+attempt,[cpu,str(restored/'code/recovery_numeric.py'),str(restored)],env)
 replay=read(restored/'regenerated/NUMERICAL_RECOVERY.json');assert replay['status']=='PASS' and replay['regenerated_specifications']==48924 and replay['attempted_draw_differences']==97848000
 render=execute('S09-exhaustive-fresh-render-'+attempt,[plot,str(restored/'code/render_figures.py'),str(restored/'regenerated/tables'),str(restored/'regenerated/tables/figures')],env);fresh=read(restored/'regenerated/tables/FIGURE_MANIFEST.json');old=read(restored/'public/FIGURE_MANIFEST.json');assert fresh['figures']==old['figures']==111
 matches={ext:0 for ext in ['png','pdf','svg']}
 for a,b in zip(old['records'],fresh['records']):
  assert all(a[k]==b[k] for k in ['id','family','spec_sha256','source_rows_sha256','checked_artist_point_or_cell_values','checked_interval_bounds','png_dimensions'])
  for x,y in zip(a['exports'],b['exports']):
   if x['sha256']==y['sha256']:matches[x['path'].rsplit('.',1)[1]]+=1
 gallery_job=execute('S09-exhaustive-fresh-gallery-'+attempt,[cpu,str(restored/'code/gallery.py'),str(restored/'regenerated/tables')],env)
 for n in ['FIGURE_GALLERY.md','FIGURE_GALLERY.html','FIGURE_CAPTIONS.json']:assert sha(restored/'regenerated/tables'/n)==sha(restored/'public'/n)
 assert api.repo_info(repo_id=repo,repo_type='dataset',revision=loc['revision'],timeout=45).private is True
 receipt={'schema_version':'s09-exhaustive-private-recovery-v1','status':'PASS','immutable_revision':loc['revision'],'archive_sha256':h,'archive_bytes':size,'manifest_sha256':loc['manifest_sha256'],'manifest_bytes':loc['manifest_bytes'],'private_at_upload_and_readback':True,'fresh_HTTP_and_not_SDK_cache':True,'safe_exact_member_bytes':stats,'numerical_regeneration':replay,'figure_replay':{'figures':111,'all_artist_values_and_bounds_equal':True,'source_specs_and_dimensions_equal':True,'byte_equal_exports_by_format':matches,'nondeterministic_metadata':'Byteequivalenceonlyreportedwhereobserved; rendergeometry/sourcevaluesequalforalldeclaredexports'},'CPU_actual_child_exit':job['exit_status'],'plot_actual_child_exit':render['exit_status'],'uploaded_application_bytes':size+loc['manifest_bytes'],'fresh_HTTP_body_bytes':size+loc['manifest_bytes'],'producer_path_fallback':False,'no_new_fits_or_GPU':True,'private_locator_record_sha256':sha(locfile),'completed_utc':now()};save(C/'SCIENCE_PRIVATE_RECOVERY_RECEIPT.json',receipt);save(P/'PRIVATE_RECOVERY_PROOF.json',receipt);print('S09_EXHAUSTIVE_PRIVATE_RECOVERY_PASS',loc['revision'],flush=True)
