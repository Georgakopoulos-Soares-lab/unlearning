"""Same-pin input acceptance, preserved roots and small private-access qualification."""
from common9 import *
import re,time,fcntl,importlib.metadata,shutil
from huggingface_hub import HfApi,hf_hub_download

def service_state():
 root=Path('/workspace/agent-handoff/POD_A/review-loop');old=read(root/'heartbeat.json');p=Path('/proc')/str(old['pid'])/'stat';assert not (p.exists() and p.read_text().split()[2]!='Z' and p.read_text().split()[21]==old['proc_start_ticks']) and (root/'STOP').exists();found=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   argv=[os.fsdecode(a) for a in (p/'cmdline').read_bytes().split(b'\0') if a];s=(p/'stat').read_text().split()
   if not argv or int(p.name)==os.getpid() or s[2]=='Z' or 'python' not in Path(argv[0]).name:continue
   scripts=[a for a in argv[1:] if a.startswith('/workspace/') and ' ' not in a and '\n' not in a]
   if any('review-loop/' in a or cfg['run_id'] in a for a in scripts):found.append({'pid':int(p.name),'start_ticks':s[21],'scripts':scripts})
  except (FileNotFoundError,ProcessLookupError):pass
 assert not found,found
 for p in [R/'GPU_EXECUTION.lock',R/'REPOSITORY_DELIVERY.lock',root/'service.lock',root/'observer.lock']:
  if p.exists():
   with p.open('r') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
 return {'status':'PASS','observer':'STOPPED','reviewer':'STOPPED','scheduler':'STOPPED','publisher':'STOPPED','owned_scientific_workers':found,'checked_locks_free':True,'pod_left_running':True,'observed_utc':now()}
def main():
 t=time.monotonic();guard(dirty=False);state=service_state();put(C/'PROCESS_PREFLIGHT.json',state);anchors=[]
 for m in re.finditer(r'^([0-9a-f]{64})  ([A-Z][A-Z0-9_]*(?:\.md|\.json|))$',(C/'package/A09_REPORTING_RECOVERY.md').read_text(),re.M):
  h,name=m.groups();p=D8/name;assert sha(p)==h;anchors.append(p)
 assert len(anchors)==10;files=[]
 for line in (D8/'OUTPUT_SHA256SUMS').read_text().splitlines():
  h,name=line.split('  ',1);p=D8/name;assert p.is_file() and not p.is_symlink() and sha(p)==h;files.append(p)
 assert len(files)==358;verified=check_committed_files(files+[D8/'OUTPUT_SHA256SUMS'],cfg['research_head_before']);put(C/'A08_COMMITTED_INPUT_VERIFICATION.json',{'status':'PASS','files':verified,'short_anchors':10,'full_public_files_including_manifest':359,'numerical_audits_repeated':0})
 prior=read(C8/'FINAL_CLOSEOUT.json');assert prior['status']=='PASS' and prior['metadata_delivery_commit']==cfg['research_head_before'] and sha(C8/'DELIVERY_RECEIPT.json')==prior['receipt_sha256'];put(C/'A09_INPUTS.json',{'status':'PINNED','research_head':cfg['research_head_before'],'inherited_scientific_commit':cfg['scientific_input_commit'],'A08_prompt_commit':prior['prompt_commit'],'A08_source_sha256':prior['audit_source_sha256'],'A08_contrast_source_sha256':prior['contrast_source_sha256'],'A08_input_receipt_sha256':sha(C8/'DELIVERY_RECEIPT.json'),'coverage_plan_sha256':cfg['coverage_plan_sha256'],'protocol_sha256':cfg['protocol_sha256'],'A08_final_private_receipt_revision':prior['receipt_revision'],'A08_payloads':prior['scientific_checkpoint_refs'],'legacy_A09_table_index':{'path':str((D90/'TABLE_INDEX.json').relative_to(W)),'sha256':sha(D90/'TABLE_INDEX.json'),'commit':cfg['research_head_before']},'A08_exact_amendment':33684,'time_policy':cfg['time_policy']})
 cpu=json.loads(subprocess.check_output([cfg['cpu_python'],'-B','-c','import json,sys,importlib.metadata as m;print(json.dumps({"python":sys.version,"packages":{p:m.version(p) for p in ["numpy","scipy","scikit-learn","joblib","threadpoolctl"]}}))'],text=True));plot=json.loads(subprocess.check_output([cfg['plot_python'],'-B','-c','import json,sys,matplotlib,numpy,PIL;print(json.dumps({"python":sys.version,"matplotlib":matplotlib.__version__,"numpy":numpy.__version__,"Pillow":PIL.__version__}))'],text=True));put(C/'ENVIRONMENT_CHECK.json',{'status':'PASS','CPU':cpu,'plotting':plot,'existing_environments_reused':True,'installs_or_upgrades':0,'GPU_visibility_for_workers':'DISABLED'})
 cc=Path('/sys/fs/cgroup');quota=int((cc/'cpu/cpu.cfs_quota_us').read_text())/int((cc/'cpu/cpu.cfs_period_us').read_text());ram=int((cc/'memory/memory.limit_in_bytes').read_text());disk=shutil.disk_usage('/workspace');assert quota>=8 and ram>=64*1024**3 and disk.free>30*1024**3;put(C/'RESOURCE_PREFLIGHT.json',{'status':'PASS','CPU_quota':quota,'cgroup_RAM_bytes':ram,'filesystem_free_bytes':disk.free,'filesystem_size_bytes':disk.total,'filesystem_size_not_a_provider_purchased_capacity_claim':True,'CPU_workers_max':2,'BLAS_threads_each':4,'worker_AS_bytes':32*1024**3,'GPU_work':0,'original_start':None,'rental_start':None,'rate':None,'cost':None,'time_policy':cfg['time_policy'],'observed_utc':now()})
 api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;probe=A/'access-probe.json';put(probe,{'stage':'A09','attempt':C.name,'nonce':digest([now(),os.getpid()]),'sensitive_data':False});key=f'POD_A/{R.name}/A09/{C.name}/access-001/probe.json';assert not api.file_exists(REPO,key,repo_type='dataset');u=api.upload_file(path_or_fileobj=str(probe),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Verify private A09 reporting recovery access');p=Path(hf_hub_download(REPO,key,repo_type='dataset',revision=u.oid,force_download=True,cache_dir=str(REC/'access-new-cache')));assert p.read_bytes()==probe.read_bytes();put(C/'PRIVATE_ACCESS_CHECK.json',{'status':'PASS','private':True,'repository':REPO,'revision':u.oid,'path':key,'sha256':sha(probe),'fresh_readback':True})
 # Current-stage approval is appended once; no fabricated timestamp or automatic stage authority.
 with (R/'APPROVAL_LOG.jsonl').open('a+') as f:
  fcntl.flock(f,fcntl.LOCK_EX);f.seek(0);s=f.read();assert not any(json.loads(l).get('attempt_id')==C.name for l in s.splitlines());e={'event_id':digest([C.name,sha(C/'APPROVAL_RECORD.json')]),'stage':'A09','attempt_id':C.name,'prompt_commit':cfg['prompt_commit'],'approval_record_sha256':sha(C/'APPROVAL_RECORD.json'),'approval_verbatim':read(C/'APPROVAL_RECORD.json')['approval_verbatim'],'message_timestamp':None,'observed_utc':now()};f.write(json.dumps(e)+'\n');f.flush();os.fsync(f.fileno());fcntl.flock(f,fcntl.LOCK_UN)
 put(C/'APPROVAL_LOG_APPEND_RECEIPT.json',{'status':'PASS','prior_sha256':bh(s.encode()),'event':e,'current_sha256':sha(R/'APPROVAL_LOG.jsonl')});result={'status':'PASS','package_files':34,'A08_committed_public_files':359,'explicit_anchors':10,'prior_science_unchanged':True,'no_scientific_audit_repetition':True,'private_access':'PASS','service_state':'STOPPED','wall_seconds':time.monotonic()-t,'observed_utc':now()};put(C/'INPUT_VALIDATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
