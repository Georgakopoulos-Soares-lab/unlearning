"""Protect exact terminal A09 metadata, then stop only the identified owned observer."""
from common import *
from research_guard import guard
from final_delivery import verify_public
from progress import service
from restore import unpack
from huggingface_hub import HfApi,hf_hub_download
import fcntl,re,shutil,tarfile,time

def identity_alive(pid,ticks):
 p=Path('/proc')/str(pid)/'stat'
 try:s=p.read_text().split();return s[2]!='Z' and s[21]==str(ticks)
 except FileNotFoundError:return False

def remaining_jobs():
 result=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   args=(p/'cmdline').read_bytes().split(b'\0');stat=(p/'stat').read_text().split()
   if int(p.name)==os.getpid() or not args or stat[2]=='Z':continue
   if b'python' in Path(os.fsdecode(args[0])).name.encode() and any(R.name.encode() in a for a in args):result.append({'pid':int(p.name),'start_ticks':stat[21],'argv':[os.fsdecode(a) for a in args if a]})
  except (FileNotFoundError,ProcessLookupError):pass
 return result

def stop_observer():
 root=Path('/workspace/agent-handoff/POD_A/review-loop');h=read(root/'heartbeat.json');pid=h['pid'];ticks=h['proc_start_ticks'];assert (pid,str(ticks))==(33071,'8476919')
 alive=identity_alive(pid,ticks);assert alive,'Unexpected owned observer identity/state; preserve it and request steering'
 args=(Path('/proc')/str(pid)/'cmdline').read_bytes().split(b'\0');assert str(root/'review_loop.v2.py').encode() in args and b'serve' in args
 assert not (root/'STOP').exists();atomic(root/'STOP',b'A09 terminal report, exact Git delivery and final metadata remote recovery verified. Stop owned administrative loop only.\n')
 t=time.monotonic()
 while identity_alive(pid,ticks) and time.monotonic()-t<55:time.sleep(0.25)
 assert not identity_alive(pid,ticks),'Observer has not stopped; do not kill another identity'
 locks=[]
 for p in [root/'service.lock',root/'observer.lock',C/'report.lock']:
  with p.open('a') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN);locks.append(str(p))
 assert not remaining_jobs();tmux=subprocess.run(['tmux','has-session','-t','pod-a-prompt-observer'],capture_output=True,text=True)
 proof={'schema':'pod-a-a09-owned-observer-stop-v1','status':'PASS','observer_status':'STOPPED','pid':pid,'proc_start_ticks':ticks,'identity_verified_before_stop':True,'identity_alive_after_stop':False,'graceful_STOP_file':str(root/'STOP'),'no_signal_or_unrelated_process_stop':True,'locks_verified_free':locks,'reviewer_status':'DRAFT_ONLY','publisher_status':'BLOCKED','tmux_session_exists_after_stop':tmux.returncode==0,'owned_scientific_jobs':'QUIESCENT','other_owned_python_jobs':[],'pod_left_running':True,'completed_utc':now()};put(C/'STOP_VERIFICATION.json',proof);return proof

def main():
 started=time.monotonic();j={'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'status':'RUNNING_FINAL_ADMINISTRATIVE_PROTECTION','started_utc':now()};put(C/'FINAL_PROTECTION_JOB.json',j)
 with (C/'final-delivery.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);proof=verify_public();put(C/'FINAL_GIT_BYTE_PROOF.json',proof);commit=proof['commit'];assert not remaining_jobs()
  api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private
  root=A/'delivery-build-001/A09-delivery-metadata-001';assert not root.exists();root.mkdir(parents=True);shutil.copytree(D,root/'public-final');shutil.copytree(A/'code',root/'code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(C/'prompt',root/'prompt')
  shutil.copytree(A/'logs',root/'logs',ignore=shutil.ignore_patterns('protect_final*'));shutil.copytree(A/'source-versions',root/'source-versions');(root/'control-final').mkdir();(root/'run-metadata').mkdir()
  for p in C.iterdir():
   if p.is_file() and p.suffix in ['.json','.jsonl','.txt','.md','.z']:shutil.copyfile(p,root/'control-final'/p.name)
  for n in ['PROGRESS.md','CONTROLLER_LATEST.json','LATEST_A09.json']:shutil.copyfile(BASE/n,root/'run-metadata'/n)
  obsroot=Path('/workspace/agent-handoff/POD_A/review-loop');(root/'observer-before-stop').mkdir()
  for p in obsroot.iterdir():
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py','.md']:shutil.copyfile(p,root/'observer-before-stop'/p.name)
  receipt={'schema':'pod-a-a09-final-delivery-receipt-v1','status':'PASS_REPORT_GIT_AND_SAVED_ANALYSIS_DELIVERY','run_id':R.name,'stage':'A09','attempt_id':C.name,'scientific_commit':cfg['scientific_commit'],'report_delivery_commit':read(C/'REPORT_DELIVERY_PROOF.json')['commit'],'metadata_commit':commit,'prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'protocol_sha256':cfg['protocol_sha256'],'payload_revision':read(C/'BACKUP_MANIFEST.json')['revision'],'receipt_revision':None,'receipt_revision_binding':'Actual returned immutable receipt revision is in separate FINAL_CLOSEOUT.json to avoid a self-hash cycle','scope_booleans':read(C/'A09_RECEIPT.json')['scope_booleans'],'full_project_status':'PARTIAL','A04_status':'PARTIAL','public_git_proof':proof,'saved_analysis_backup':read(C/'BACKUP_VERIFICATION.json'),'owned_scientific_jobs':'QUIESCENT','administrative_service_as_of_report_publication':service(),'no_automatic_resume':True,'no_A10':True,'pod_left_running':True,'created_utc':now()};put(root/'A09_DELIVERY_RECEIPT.before-final-protection.json',receipt)
  files=[]
  for p in sorted(root.rglob('*')):
   assert not p.is_symlink()
   if p.is_file():
    data=p.read_bytes();assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',data);files.append({'path':str(p.relative_to(root)),'bytes':len(data),'sha256':sha(p)})
  put(root/'MEMBER_MANIFEST.json',{'files':files,'self_excluded':True});archive=A/'a09-delivery-metadata-001.tar.gz';assert not archive.exists();t=time.monotonic()
  with tarfile.open(archive,'w:gz',compresslevel=6) as tf:tf.add(root,arcname=root.name)
  compression=time.monotonic()-t;h=sha(archive);prefix=f'POD_A/{R.name}/A09/{C.name}/delivery-001';key=prefix+'/'+archive.name;assert not api.file_exists(REPO,key,repo_type='dataset');t=time.monotonic();up=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect exact A09 terminal reports, Git proof, source and finite recovery handoff');upload=time.monotonic()-t
  dest=REC/'delivery-fresh-001';assert not dest.exists();dest.mkdir();t=time.monotonic();fresh=Path(hf_hub_download(REPO,key,repo_type='dataset',revision=up.oid,force_download=True,cache_dir=str(dest/'empty-cache')));assert fresh.stat().st_size==archive.stat().st_size and sha(fresh)==h
  expected={e['path']:e for e in files};expected['MEMBER_MANIFEST.json']={'bytes':(root/'MEMBER_MANIFEST.json').stat().st_size,'sha256':sha(root/'MEMBER_MANIFEST.json')};restored,count,raw=unpack(fresh,dest/'consumer',expected);assert count==len(expected);restore_seconds=time.monotonic()-t;assert api.repo_info(REPO,repo_type='dataset').private;assert verify_public()['commit']==commit
  receipt.update(final_metadata_revision=up.oid,final_metadata_path=key,final_metadata_bytes=archive.stat().st_size,final_metadata_sha256=h,final_metadata_member_manifest_sha256=sha(root/'MEMBER_MANIFEST.json'),final_metadata_files_verified=count,final_metadata_uncompressed_bytes=raw,force_fresh_metadata_recovery=True,metadata_fresh_destination=str(restored),metadata_compression_seconds=compression,metadata_upload_seconds=upload,metadata_fresh_download_and_verification_seconds=restore_seconds)
  put(C/'FINAL_METADATA_VERIFICATION.json',receipt)
  # Report delivery and both private payload recoveries are now verified. The only
  # remaining transfer records the terminal administrative exit; it cannot start science.
  stop=stop_observer();receipt.update(administrative_services=stop,terminal_status='STOPPED: POD_A HANDOFF DELIVERED',completed_utc=now(),elapsed_wall_seconds_before_final_receipt=time.monotonic()-started)
  receipt_path=C/'DELIVERY_RECEIPT.json';put(receipt_path,receipt);receipt_key=prefix+'/A09_DELIVERY_RECEIPT.final.json';assert not api.file_exists(REPO,receipt_key,repo_type='dataset');t=time.monotonic();up2=api.upload_file(path_or_fileobj=str(receipt_path),path_in_repo=receipt_key,repo_id=REPO,repo_type='dataset',commit_message='Record verified A09 terminal delivery and graceful owned observer stop');fresh_receipt=Path(hf_hub_download(REPO,receipt_key,repo_type='dataset',revision=up2.oid,force_download=True,cache_dir=str(REC/'delivery-receipt-fresh-cache-001')));assert fresh_receipt.read_bytes()==receipt_path.read_bytes() and api.repo_info(REPO,repo_type='dataset').private;assert verify_public()['commit']==commit
  final={'schema':'pod-a-a09-final-closeout-v1','status':'PASS','terminal_status':'STOPPED: POD_A HANDOFF DELIVERED','scientific_commit':cfg['scientific_commit'],'report_delivery_commit':receipt['report_delivery_commit'],'metadata_commit':commit,'payload_revision':receipt['payload_revision'],'final_metadata_revision':up.oid,'final_metadata_path':key,'final_metadata_sha256':h,'receipt_revision':up2.oid,'receipt_path':receipt_key,'receipt_sha256':sha(receipt_path),'receipt_upload_and_force_fresh_readback_seconds':time.monotonic()-t,'receipt_bytes_verified':True,'administrative_services':stop,'scope_booleans':receipt['scope_booleans'],'full_project_status':'PARTIAL','A04_status':'PARTIAL','completed_utc':now()};put(C/'FINAL_CLOSEOUT.json',final);put(R/'FINAL_CLOSEOUT.json',final);shutil.copyfile(receipt_path,R/'DELIVERY_RECEIPT.json');j.update(status='COMPLETED_AWAITING_PROCESS_EXIT',completed_utc=now(),wall_seconds=time.monotonic()-started);put(C/'FINAL_PROTECTION_JOB.json',j);print(json.dumps(final))
if __name__=='__main__':main()
