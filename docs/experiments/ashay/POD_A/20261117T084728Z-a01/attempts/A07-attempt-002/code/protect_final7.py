"""Exact final public readback, private metadata recovery and separate delivery receipt."""
from common7 import *
from archive7 import safe_extract
from finish7 import quiet,seal,NEXT,STATUS
from delivery7 import deliver
from huggingface_hub import HfApi,hf_hub_download
import shutil,tarfile,time,re,importlib.util,csv

def public_proof():
 guard(dirty=False);head=git('rev-parse','HEAD');assert git('ls-remote','--heads','origin','POD_A').split()[0]==head;s=read(C/'PUBLICATION_SEAL.json');assert sha(D/'OUTPUT_SHA256SUMS')==s['manifest_sha256']
 for e in s['files']:
  p=D/e['path'];assert sha(p)==e['sha256'] and gitb('show',head+':'+str(p.relative_to(W)))==p.read_bytes()
 for e in s['root_entrypoints']:
  p=B/e['path'];assert sha(p)==e['sha256'] and gitb('show',head+':'+str(p.relative_to(W)))==p.read_bytes()
 assert gitb('show',head+':'+str((D/'OUTPUT_SHA256SUMS').relative_to(W)))==(D/'OUTPUT_SHA256SUMS').read_bytes();assert all(owned(p) for p in git('diff','--name-only',cfg['research_head_before'],head).splitlines())
 return {'status':'PASS','commit':head,'remote_equal':True,'exact_current_owned_committed_bytes':True,'public_files_including_manifest':len(s['files'])+1,'prior_attempts_main_index_status_other_refs_unchanged':True,'manifest_sha256':s['manifest_sha256'],'observed_utc':now()}

def metadata_commit():
 proof=public_proof();assert proof['commit']==read(C/'SCIENTIFIC_DELIVERY.json')['commit'];publish('REPORT_DELIVERY_REPAIR_EVIDENCE.json',read(C/'REPORT_DELIVERY_REPAIR_EVIDENCE.json'));publish('code/postexit7.py',(A/'code/postexit7.py').read_bytes());publish('code/protect_final7.py',(A/'code/protect_final7.py').read_bytes());publish('ORCHESTRATION_SOURCE_IDENTITY.json',{'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((A/'code').glob('*.py'))],'scientific_CPU_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'closing_metadata_only_source_snapshot':True});publish('METADATA_POST_PUSH_PROOF.json',proof|{'scientific_commit':proof['commit'],'metadata_commit':'Separate returned receipt; no future/self commit cycle','stage':STATUS,'next_state':NEXT});publish('DELIVERY_SEMANTICS.json',{'scientific_commit':proof['commit'],'science':'Five immutable task checkpoints, exact3900+8400 results and all source/approval/input seals','next_metadata_commit':'Contains this immutable scientific post-push proof; actual returned commit is recorded separately','private_final_metadata':'Fresh all-member recovery follows final Git push','private_final_receipt':'Separate checksummed object; its revision is returned outside its own bytes','private_final_receipt_repository':REPO,'private_final_receipt_path':f'POD_A/{R.name}/A07/{C.name}/delivery-001/A07_R5_DELIVERY_RECEIPT.final.json','independent_release':'PENDING_A08','A08_started':False});seal();r=deliver('A07 R5: bind verified scientific commit and final metadata handoff');put(C/'METADATA_DELIVERY.json',r);return r

def regenerate(restored):
 sys.dont_write_bytecode=True
 pub=restored/'public-final';p=restored/'code/key_contract5.py';spec=importlib.util.spec_from_file_location('fresh_A07_keys',p);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);expected={r['logical_id'] for r in mod.table_keys(read(restored/'immutable-A05-input-metadata/TABLE_KEY_DESIGN.json'),cfg['coverage_plan_sha256']) if r['owner_stage']=='A07'};actual=[];registry=read(pub/'PRIVATE_PROVENANCE_MAP.json')['artifacts'];joins=0;member_indices=read(restored/'IMMUTABLE_DESCRIPTOR_MEMBER_INDICES.json')['archives']
 for identity,d in registry.items():
  assert digest(d)==identity
  e=member_indices[d['archive_sha256']]['members'][d['member']];assert e['sha256']==d['sha256'] and e['bytes']==d['bytes'];assert member_indices[d['archive_sha256']]['revision']==d['revision']
 for name,count in [('RESULTS_LONG.csv',3900),('PAIRED_CONTRASTS.csv',8400)]:
  with (pub/name).open() as f:rows=list(csv.DictReader(f))
  assert len(rows)==count
  for r in rows:
   actual.append(r['logical_id']);assert r['status']=='COMPLETE_UNVERIFIED' and r['independent_audit_status']=='PENDING_A08'
   for k,v in r.items():
    if k.endswith('_locator') and v:
     prefix=k[:-8];d=registry[v.removeprefix('provenance:')];assert d['sha256']==r[prefix+'_sha256'] and d['hash_kind']==r[prefix+'_hash_kind'];joins+=1
 assert len(actual)==len(set(actual))==12300 and set(actual)==expected
 with (pub/'TASK_LAYER_SEED_VIEW.csv').open() as f:view=list(csv.DictReader(f))
 assert len(view)==3900 and len({r['logical_id'] for r in view})==3900
 assert {str(p.relative_to(restored)) for p in restored.rglob('*') if p.is_file()}=={e['path'] for e in read(restored/'MEMBER_MANIFEST.json')['files']}|{'MEMBER_MANIFEST.json'}
 return {'status':'PASS','exact_A07_keys':12300,'typed_descriptor_joins':joins,'view_rows':3900,'fresh_consumer':str(restored)}

def main():
 api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;proof=public_proof();state=quiet();back=read(C/'BACKUP_VERIFICATION.json');assert back['status']=='PASS';remote=[]
 for b in back['checkpoints']:
  x=api.get_paths_info(REPO,[b['archive_path']],repo_type='dataset',revision=b['revision'])[0];assert x.size==b['archive_bytes'] and x.lfs.sha256==b['archive_sha256'];remote.append({'task':b['task'],'revision':b['revision'],'path':b['archive_path'],'bytes':b['archive_bytes'],'sha256':b['archive_sha256'],'remote_LFS_identity':'PASS','prior_fresh_member_and_computational_recovery_reused':True})
 root=A/'final-metadata-build-001/A07-R5-final-metadata-001';assert not root.exists();root.mkdir(parents=True);shutil.copytree(D,root/'public-final');shutil.copytree(A/'code',root/'code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(A/'logs',root/'logs',ignore=shutil.ignore_patterns('final-protect*'));shutil.copytree(C/'package',root/'prompt-package');shutil.copytree(C/'jobs',root/'control/jobs');shutil.copytree(C/'prior-run-root',root/'prior-run-root');(root/'run-root-current').mkdir();shutil.copyfile(R/'APPROVAL_LOG.jsonl',root/'ROOT_APPROVAL_LOG.jsonl');put(root/'ROOT_CONTROLLER_AT_METADATA_PROTECTION.json',read(R/'CONTROLLER_STATE.json'))
 for p in C.iterdir():
  if p.is_file() and p.suffix in ['.json','.jsonl','.md','.txt','.z','.patch']:shutil.copyfile(p,root/'control'/p.name)
 for name in cfg['allowed_root_files']:shutil.copyfile(B/name,root/'run-root-current'/name)
 (root/'immutable-A05-input-metadata').mkdir()
 for name in ['TABLE_KEY_DESIGN.json','AUDIT_PLAN.json','RESULT_SCHEMAS.json','COVERAGE_PLAN.json','EFFECTIVE_INPUTS.json','RECOVERY_DEPENDENCY_GRAPH.json','R5_EXECUTION_MANIFEST.json']:shutil.copyfile(D5/name,root/'immutable-A05-input-metadata'/name)
 member_indices={}
 for b in back['checkpoints']:
  member_indices[b['archive_sha256']]={'revision':b['revision'],'members':{e['path']:e for e in read(Path(b['consumer_root'])/'MEMBER_MANIFEST.json')['files']}}
 dep=read(C/'REUSED_A06_FEATURE_CONSUMER.json');member_indices[dep['archive_sha256']]={'revision':dep['revision'],'members':{e['path']:e for e in read(Path(dep['consumer_root'])/'MEMBER_MANIFEST.json')['files']}}
 for n in read(D5/'RECOVERY_DEPENDENCY_GRAPH.json')['nodes']:
  if n['id'] in ['historical/base_R1','historical/controls']:member_indices[n['sha256']]={'revision':n['revision'],'members':{e['path']:e for e in read(n['member_index'])['files']}}
 put(root/'IMMUTABLE_DESCRIPTOR_MEMBER_INDICES.json',{'archives':member_indices,'historical_indices_reused_not_new_network_reads':True})
 put(root/'POST_PUSH_PROOF.json',proof);put(root/'PROCESS_STATE_AT_PROTECTION.json',state);put(root/'SCIENTIFIC_PAYLOAD_READBACK.json',{'status':'PASS','objects':remote,'science_repacked':False});files=[]
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():
   assert p.suffix not in ['.npz','.npy','.joblib','.distcp','.pt'];data=p.read_bytes();assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)',data);files.append({'path':str(p.relative_to(root)),'bytes':len(data),'sha256':bh(data)})
 put(root/'MEMBER_MANIFEST.json',{'files':files,'self_excluded':True,'scope':'Final metadata, code, logs and exact public/control state. Five scientific checkpoints remain separate immutable objects.'});archive=A/'A07-R5-final-metadata-001.tar.gz';assert not archive.exists();t=time.monotonic()
 with tarfile.open(archive,'w:gz',compresslevel=6) as tf:
  for p in sorted(root.rglob('*')):
   if p.is_file():tf.add(p,arcname=root.name+'/'+str(p.relative_to(root)),recursive=False)
 comp=time.monotonic()-t;h=sha(archive);key=f'POD_A/{R.name}/A07/{C.name}/delivery-001/'+archive.name;assert not api.file_exists(REPO,key,repo_type='dataset');t=time.monotonic();u=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect R5 A07 complete producer handoff and exact final metadata');upload=time.monotonic()-t;put(C/'FINAL_METADATA_UPLOADED.json',{'revision':u.oid,'path':key,'sha256':h,'bytes':archive.stat().st_size});freshbase=REC/'final-metadata-fresh-001';assert not freshbase.exists();freshbase.mkdir();t=time.monotonic();fresh=Path(hf_hub_download(REPO,key,repo_type='dataset',revision=u.oid,force_download=True,cache_dir=str(freshbase/'new-cache')));assert sha(fresh)==h and fresh.stat().st_size==archive.stat().st_size;num,hashsec=safe_extract(fresh,freshbase/'consumer');assert num==len(files)+1;restored=freshbase/'consumer';rebuild=regenerate(restored)
 for p in (restored/'public-final').rglob('*'):
  if p.is_file():assert gitb('show',proof['commit']+':'+str((D/p.relative_to(restored/'public-final')).relative_to(W)))==p.read_bytes()
 assert public_proof()['commit']==proof['commit'] and api.repo_info(REPO,repo_type='dataset').private;after=quiet();meta={'status':'PASS','repository':REPO,'revision':u.oid,'archive_path':key,'archive_bytes':archive.stat().st_size,'archive_sha256':h,'member_manifest_sha256':sha(root/'MEMBER_MANIFEST.json'),'all_members_fresh_verified':num,'fresh_consumer':str(restored),'regenerated_keys_and_joins':rebuild,'exact_restored_public_commit':proof['commit'],'compression_seconds':comp,'upload_seconds':upload,'fresh_download_and_validation_seconds':time.monotonic()-t,'all_member_hash_seconds':hashsec,'science_repacked':False}
 receipt={'schema':'pod-a-r5-a07-final-delivery-v1','status':'PASS','stage_status':STATUS,'full_A04_project_status':'PARTIAL','run_id':cfg['run_id'],'attempt_id':C.name,'prompt_commit':cfg['prompt_commit'],'prompt_sha256':cfg['A07_prompt_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'CPU_source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'scientific_delivery_commit':read(C/'SCIENTIFIC_DELIVERY.json')['commit'],'metadata_delivery_commit':proof['commit'],'public_proof':proof,'scientific_checkpoints':back,'final_metadata':meta,'coverage':read(C/'A07_RECEIPT.json'),'processes':after,'observer':'STOPPED','pod_left_running':True,'A08_started':False,'time_policy':cfg['time_policy'],'receipt_revision_binding':'Returned immutable revision in separate FINAL_CLOSEOUT.json; no self-reference','next_state':NEXT,'completed_utc':now()};put(C/'DELIVERY_RECEIPT.json',receipt);rkey=f'POD_A/{R.name}/A07/{C.name}/delivery-001/A07_R5_DELIVERY_RECEIPT.final.json';assert not api.file_exists(REPO,rkey,repo_type='dataset');ur=api.upload_file(path_or_fileobj=str(C/'DELIVERY_RECEIPT.json'),path_in_repo=rkey,repo_id=REPO,repo_type='dataset',commit_message='Bind exact protected R5 A07 delivery; stop before A08');fr=Path(hf_hub_download(REPO,rkey,repo_type='dataset',revision=ur.oid,force_download=True,cache_dir=str(REC/'final-receipt-fresh-cache')));assert fr.read_bytes()==(C/'DELIVERY_RECEIPT.json').read_bytes() and api.repo_info(REPO,repo_type='dataset').private;assert public_proof()['commit']==proof['commit']
 final={'schema':'pod-a-r5-a07-final-closeout-v1','status':'PASS','stage_status':STATUS,'full_A04_project_status':'PARTIAL','coverage_plan_sha256':cfg['coverage_plan_sha256'],'CPU_source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'scientific_delivery_commit':receipt['scientific_delivery_commit'],'metadata_delivery_commit':proof['commit'],'scientific_checkpoint_refs':[{'task':b['task'],'revision':b['revision'],'path':b['archive_path'],'sha256':b['archive_sha256']} for b in back['checkpoints']],'final_metadata_revision':u.oid,'final_metadata_path':key,'final_metadata_sha256':h,'final_metadata_members_verified':num,'receipt_revision':ur.oid,'receipt_path':rkey,'receipt_sha256':sha(C/'DELIVERY_RECEIPT.json'),'receipt_fresh_readback':'PASS','all_prior_attempts_unchanged':True,'owned_jobs_quiet':True,'observer':'STOPPED','pod_left_running':True,'A08_started':False,'next_state':NEXT,'completed_utc':now()};put(C/'FINAL_CLOSEOUT.json',final);put(C/'FINAL_GIT_BYTE_PROOF.json',proof)
 for name in ['FINAL_CLOSEOUT.json','DELIVERY_RECEIPT.json']:put(R/name,read(C/name))
 for name in ['REMOTE_HANDOFF.json','RESUME_MANIFEST.json']:put(R/name,read(D/name)|{'final_closeout':final})
 md(R/'SESSION_HANDOFF.md',(D/'SESSION_HANDOFF.md').read_text());put(R/'CONTROLLER_STATE.json',read(D/'REMOTE_HANDOFF.json')|{'status':STATUS,'stage':'A07','attempt_id':C.name,'final_closeout':final,'automatic_resume':False,'next_state':NEXT});print(json.dumps(final))
if __name__=='__main__':
 if sys.argv[1:] == ['metadata-commit']:print(json.dumps(metadata_commit()))
 else:main()
