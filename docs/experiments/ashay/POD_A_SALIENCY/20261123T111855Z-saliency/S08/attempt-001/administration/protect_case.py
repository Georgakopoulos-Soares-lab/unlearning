"""Append-only private S08 new artifacts, fresh exact restore and declared CPU replay."""
from pathlib import Path,PurePosixPath
import os,sys,json,hashlib,tarfile,uuid,re,time,urllib.request,urllib.parse
os.environ['HF_HUB_DISABLE_PROGRESS_BARS']='1';os.environ['HF_HUB_DISABLE_XET']='1'
from huggingface_hub import HfApi,hf_hub_url,get_token,CommitOperationAdd
from ops import C,A,save,now
from long_run import execute
alias=sys.argv[1];attempt=int(sys.argv[2]);read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest();cfg=read(C/'RUN_CONFIG.json');assert alias in {v['alias'] for v in cfg['candidates']} and attempt in [1,2];case=A/'candidates'/alias;coverage=read(case/'eligible/COVERAGE.json');assert coverage['heads']==390 and coverage['prediction_paths']==780;source=read(C/'SOURCE_IDENTITY.json');c7=C.parent.parent/'S07/attempt-001';c3=C.parent.parent/'S03/attempt-003';c1=C.parent.parent/'S03/attempt-001';started=time.monotonic();statefile=C/(alias+'-PRIVATE_RECOVERY_PROGRESS.json');archive=A/'private-checkpoints'/(alias+'-S08-001.tar.gz');snapshot=C/(alias+'-PRIVATE_SNAPSHOT.json');locfile=C/(alias+'-PRIVATE_RECOVERY_LOCATORS.json')
def safe_failure(kind,value,tb):
    reason=re.sub(r'https?://\S+','[URL REDACTED]',str(value));reason=re.sub(r'(?:hf_|ghp_|github_pat_)[A-Za-z0-9_]+','[CREDENTIAL REDACTED]',reason);save(C/(alias+'-RECOVERY_FAILED-'+str(attempt)+'.json'),{'status':'FAILED_PRESERVED','exception':kind.__name__,'reason':reason,'observed_utc':now()});print('S08_PRIVATE_RECOVERY_FAILED',alias,kind.__name__,reason,flush=True)
sys.excepthook=safe_failure
panel=read(C/'RECOVERY_CONTRACT.json')['panel'][alias];limits=read(C/'RECOVERY_CONTRACT.json')['archive_limits']
if not archive.exists():
    entries={}
    def add(n,p):
        p=Path(p);q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts and '\\' not in n and str(q)==n;assert p.is_file() and not p.is_symlink() and p.stat().st_size<limits['member_bytes'];assert n not in entries or entries[n]==p;entries[n]=p
    for p in sorted(case.rglob('*')):
        if p.is_file() and not p.name.endswith('.lock') and 'recovery-inputs' not in p.relative_to(case).parts:add('candidate/'+str(p.relative_to(case)),p)
    for p in sorted((A/'operation-logs').glob('S08-'+alias+'-*')):
        if p.is_file() and any(s in p.name for s in ['-group-001.','-worker0-001.','-worker1-001.']):add('execution-logs/'+p.name,p)
    for p in sorted((case/'recovery-inputs').iterdir()):
        if p.is_file():add('recovery-inputs/'+p.name,p)
    for p in sorted((Path(cfg['inputs_root'])/'s06').rglob('*')):
        if p.is_file():add('inputs/s06/'+str(p.relative_to(Path(cfg['inputs_root'])/'s06')),p)
    add('inputs/ORIGINAL_BASE_HEADS.json',Path(cfg['inputs_root'])/'ORIGINAL_BASE_HEADS.json')
    refs=read(Path(cfg['inputs_root'])/'ORIGINAL_BASE_HEADS.json');prod=Path(cfg['producer_artifacts_root'])/'candidates'/alias
    for s in panel:
        t=s['task'];r=s['representation'];seed=s['cv_seed'];key='final_norm' if r=='decoder.final_norm' else 'decoder_layer_'+r.rsplit('.',1)[1];pr=prod/'tasks'/t/'probabilities'/key/('seed'+str(seed))/s['policy']
        for name in ['predictions.npz','draws.npz','METRICS.json','COMPLETE.json']:add('producer/'+str((pr/name).relative_to(prod)),pr/name)
        if s['policy']=='independent_refit':
            h=prod/'tasks'/t/'production'/key/('seed'+str(seed))
            for name in ['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json','COMPLETE.json']:add('producer/'+str((h/name).relative_to(prod)),h/name)
        else:
            ref=next(x for x in refs if (x['task'],x['representation'],x['cv_seed'])==(t,r,seed));add('inputs/'+ref['relative_path'],Path(cfg['producer_inputs_root'])/ref['relative_path'])
    for f in source['files']:add('code/'+f['path'],Path(source['code_root'])/f['path'])
    for n in ['RUN_CONFIG.json','SOURCE_IDENTITY.json','CPU_ENVIRONMENT_LOCK.json','READINESS.json','RECOVERY_CONTRACT.json','ORIGINAL_AUDIT_KEYS.json','RESOURCE_ADMISSION.json','APPROVAL_RECORD.json','PROMPT_RECEIPT.json']:add('control/'+n,C/n)
    add('control/CASE_EXPECTED.jsonl',cfg['case_bindings'][alias]['expected']['path']);add('control/CASE_PRODUCER.jsonl',cfg['case_bindings'][alias]['producer']['path'])
    deps={'schema_version':'s08-immutable-recovery-dependencies-v1','S07_candidate_all_producer_bytes':read(c7/(alias+'-PRIVATE_RECOVERY_LOCATORS.json')),'S07_final_metadata':read(c7/'FINAL_METADATA_BACKUP_LOCATORS.json'),'S06_features':read(C.parent.parent/'S06/attempt-001'/(alias+'-PRIVATE_RECOVERY_LOCATORS.json')),'S05_H3':read(C.parent.parent/'S05/attempt-001'/(alias+'-PRIVATE_RECOVERY_LOCATORS.json')),'S04_frozen_planning':read(C.parent.parent/'S04/attempt-001/PRIVATE_PLANNING_BACKUP_LOCATORS.json'),'original_base_archive':read(c1/'qualification-checkpoint-002-DEPENDENCY_GRAPH.json')['historical_archives']['historical-archive-001'],'CPU_runtime_install_plan':read(c1/'CPU_REFERENCE_RUNTIME_PLAN.json'),'CPU_runtime_install_report':read(c1/'CPU_REFERENCE_INSTALL_REPORT.json'),'scope':'AllnewS08auditestimators/calls/finalheads/verificationrecords plusoriginalpanelboundedS06devprojections, selectedS07heads/savedpaths/draws andoriginalbaseheads. OtherunchangedS07/S06/H3/base/control/native/runtime dependencies by exactimmutable refs; no raw sequences/nativeweights repacked.'};dep=C/(alias+'-EXACT_RECOVERY_DEPENDENCIES.json');save(dep,deps);add('DEPENDENCIES.json',dep);assert len(entries)<limits['members'] and sum(p.stat().st_size for p in entries.values())<limits['expanded_bytes'];manifest={n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in entries.items()};staging=archive.with_name(archive.name+'.packing-'+str(attempt));assert not staging.exists();last=time.monotonic()
    with tarfile.open(staging,'w:gz',compresslevel=1) as tar:
        for i,(n,p) in enumerate(entries.items()):
            m=tarfile.TarInfo(n);m.size=p.stat().st_size;m.mode=0o600;m.mtime=0
            with p.open('rb') as f:tar.addfile(m,f)
            if time.monotonic()-last>=20:print('S08_PRIVATE_PACK_PROGRESS',alias,i+1,len(entries),flush=True);last=time.monotonic()
    save(snapshot,{'files':manifest,'source_identity_sha256':source['verifier_source_identity_sha256'],'selection':panel,'created_utc':now()});os.replace(staging,archive)
else:manifest=read(snapshot)['files']
h=sha(archive);size=archive.stat().st_size;repo=read(c3/'BACKUP_ROUTE_CURRENT.json')['repository'];api=HfApi();info=api.repo_info(repo_id=repo,repo_type='dataset',timeout=45);assert info.private is True
if locfile.exists():
    loc=read(locfile);assert loc['archive_sha256']==h and loc['archive_bytes']==size;remote=loc['remote_object'];rev=loc['revision']
else:
    intentfile=C/(alias+'-PRIVATE_UPLOAD_INTENT.json')
    if intentfile.exists():intent=read(intentfile);assert intent['archive_sha256']==h;remote=intent['remote_object']
    else:remote='POD_A_SALIENCY/20261123T111855Z-saliency/S08/attempt-001/'+alias+'-'+uuid.uuid4().hex+'/'+archive.name;save(intentfile,{'repository':repo,'remote_object':remote,'archive_sha256':h,'archive_bytes':size,'created_utc':now()})
    print('S08_PRIVATE_UPLOAD_START',alias,size,flush=True);result=api.create_commit(repo_id=repo,repo_type='dataset',operations=[CommitOperationAdd(path_in_repo=remote,path_or_fileobj=str(archive)),CommitOperationAdd(path_in_repo=remote+'.manifest.json',path_or_fileobj=str(snapshot))],parent_commit=info.sha,num_threads=2,commit_message='Protect independently checked S08 probe evidence, original CV audits and exact member manifest');rev=result.oid;save(locfile,{'repository':repo,'revision':rev,'remote_object':remote,'manifest_remote_object':remote+'.manifest.json','manifest_sha256':sha(snapshot),'manifest_bytes':snapshot.stat().st_size,'archive_sha256':h,'archive_bytes':size})
assert api.repo_info(repo_id=repo,repo_type='dataset',revision=rev,timeout=45).private is True;consumer=A/'fresh-consumers'/(alias+'-HTTP-'+str(attempt).zfill(3));assert not consumer.exists();consumer.mkdir(parents=True);download=consumer/'checkpoint.tar.gz';token=get_token();assert token
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        nxt=super().redirect_request(req,fp,code,msg,headers,newurl)
        if nxt and urllib.parse.urlparse(req.full_url).hostname!=urllib.parse.urlparse(newurl).hostname:nxt.remove_header('Authorization')
        return nxt
request=urllib.request.Request(hf_hub_url(repo_id=repo,repo_type='dataset',revision=rev,filename=remote),headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache'});count=0;digest=hashlib.sha256();last=time.monotonic()
with urllib.request.build_opener(Redirect()).open(request,timeout=45) as response,download.open('xb') as f:
    assert response.status==200 and response.headers.get('Content-Range') is None
    while True:
        b=response.read(1024**2)
        if not b:break
        count+=len(b);assert count<=size;f.write(b);digest.update(b)
        if time.monotonic()-last>=20:print('S08_PRIVATE_FRESH_READBACK',alias,count,size,flush=True);last=time.monotonic()
    f.flush();os.fsync(f.fileno())
assert count==size and digest.hexdigest()==h
# Manifest is a separately addressed object at the same immutable commit, avoiding a self-hash cycle.
loc=read(locfile);sidecar=consumer/'member-manifest.json';req=urllib.request.Request(hf_hub_url(repo_id=repo,repo_type='dataset',revision=rev,filename=loc['manifest_remote_object']),headers={'Authorization':'Bearer '+token,'Accept-Encoding':'identity','Cache-Control':'no-cache'})
with urllib.request.build_opener(Redirect()).open(req,timeout=45) as response,sidecar.open('xb') as f:
    assert response.status==200 and response.headers.get('Content-Range') is None;data=response.read(loc['manifest_bytes']+1);assert len(data)==loc['manifest_bytes'];f.write(data);f.flush();os.fsync(f.fileno())
assert sha(sidecar)==loc['manifest_sha256'] and read(sidecar)==read(snapshot);manifest=read(sidecar)['files'];sys.path.insert(0,str(A/'code'));from safe_archive import restore
restored=consumer/'restored';restored_stats=restore(download,manifest,restored,limits);print('S08_EXACT_PRIVATE_MEMBERS_RESTORED',alias,restored_stats['members'],flush=True)
env={'PATH':str(Path(cfg['cpu_runtime_python']).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','HF_HUB_OFFLINE':'1'}
# Serialize numerical replay with fitting/verification stages; transfer and packing do not acquire GPU authority.
import fcntl
with (C/'CPU_STAGE.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);job=execute('S08-'+alias+'-fresh-recovery-'+str(attempt),[cfg['cpu_runtime_python'],str(restored/'code/s08_recovery.py'),str(restored),alias],env)
replay=read(restored/'NUMERICAL_RECOVERY.json');assert replay['status']=='PASS' and replay['restored_saved_prediction_paths']==len(panel) and replay['fresh_audit_heads_reconstructed']*2==len(panel) and replay['producer_path_fallback'] is False;assert api.repo_info(repo_id=repo,repo_type='dataset',revision=rev,timeout=45).private is True;receipt={'schema_version':'s08-private-case-recovery-v1','status':'PASS','alias':alias,'immutable_revision':rev,'archive_sha256':h,'archive_bytes':size,'member_manifest_sha256':loc['manifest_sha256'],'member_manifest_bytes':loc['manifest_bytes'],'member_manifest_fresh_readback_verified':True,'uploaded_application_bytes':size+loc['manifest_bytes'],'fresh_HTTP_body_bytes':count+loc['manifest_bytes'],'private_at_write_and_readback':True,'SDK_download_cache_used':False,'exact_regular_members_verified':restored_stats['members'],'expanded_bytes_verified':restored_stats['expanded_bytes'],'numerical_panel':{k:replay[k] for k in ['restored_saved_prediction_paths','restored_marginal_vectors','attempted_draw_values','fresh_audit_heads_reconstructed','new_CV_calls','max_probability_abs_residual','max_metric_draw_CI_abs_residual','regenerated_mappings']},'fresh_CPU_receipt_sha256':sha(restored/'NUMERICAL_RECOVERY.json'),'CPU_child_exit_status':job['exit_status'],'producer_path_fallback':False,'GPU_replay_or_clean_runtime_recreation':False,'private_locator_record_sha256':sha(locfile),'source_identity_sha256':source['verifier_source_identity_sha256'],'executed_administrative_recipe_sha256':sha(Path(__file__)),'wall_seconds':time.monotonic()-started,'completed_utc':now()};save(C/(alias+'-PRIVATE_RECOVERY_RECEIPT.json'),receipt);save(statefile,receipt);print('S08_PRIVATE_RECOVERY_PASS',alias,rev,len(panel),flush=True)
