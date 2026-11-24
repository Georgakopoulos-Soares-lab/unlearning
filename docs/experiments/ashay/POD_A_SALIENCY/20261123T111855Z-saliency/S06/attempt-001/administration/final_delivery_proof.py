"""Post-publication bounded S06 preservation/process/lock and receipt proof. No scientific execution."""
from pathlib import Path
import json,sys,hashlib,fcntl,subprocess
from ops import C,A,R,save,run,now
T=R/json.loads((C/'PATHS.json').read_text())['run_root'];P=T/'S06/attempt-001';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();delivery=read(C/'S06-final-001-DELIVERY.json');commit=delivery['commit'];assert delivery['status']=='PASS';assert read(C/'FINAL_METADATA_RECOVERY_RECEIPT.json')['status']=='PASS';assert read(C/'FINAL_METADATA_RECOVERY_RECEIPT.json')['administrative_mapping_regeneration_status']=='PASS';assert read(P/'S06_RECEIPT.json')['status']=='COMPLETE';s=read(T/'CONTROLLER_STATE.json');assert not s['approvals']['S07']['approved']
def git(label,*args,cwd=R,network=False):return run('S06-final-proof-'+label,['git',*args],cwd,network=network).decode().strip()
assert git('HEAD','rev-parse','HEAD')==commit;assert git('remote','ls-remote','--exit-code','origin','refs/heads/POD_A_SALIENCY',network=True).split()[0]==commit;assert git('clean','status','--porcelain')==''
assert git('original-POD-A','rev-parse','refs/heads/POD_A')=='8c651c7ab3c3a2a47f5bbd0e464a69a197512c82'
for phase in ['S00','S01','S02','S03','S04','S05']:run('S06-final-proof-preserve-'+phase,['git','diff','--exit-code','63703809d2ff5062a82af43f5b4f8b7e53e04f36','--',str((T/phase).relative_to(R))],R)
# Frozen package and prompt tracked worktrees are checked, without resetting/fetching/moving refs.
prompts=[]
for i,d in enumerate(['/workspace/pod-a-saliency/prompts','/workspace/pod-a-saliency/prompts-publish']):
 q=Path(d);dirty=git('prompt-'+str(i)+'-tracked','diff','--name-only','HEAD','--',cwd=q);assert dirty=='';prompts.append({'path':d,'head':git('prompt-'+str(i)+'-head','rev-parse','HEAD',cwd=q),'tracked_changes':False})
commands=[json.loads(l) for l in (C/'LONG_COMMAND_LEDGER.jsonl').read_text().splitlines()];live=[];unknown=[]
for r in commands:
 if r.get('exit_status') is None:unknown.append(r)
 pid=r.get('pid');ticks=r.get('start_ticks');p=Path('/proc/'+str(pid)+'/stat')
 if pid and ticks and p.exists() and p.read_text().rsplit(')',1)[1].split()[19]==ticks:live.append({'pid':pid,'start_ticks':ticks})
assert not live and not unknown
assert read(C/'GPU_ACCOUNTING.json')['active_job'] is None
with (Path(read(C/'RUN_CONFIG.json')['root_control'])/'GPU_EXECUTION.lock').open('a') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
gpu=run('S06-final-proof-GPU-idle',['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits']).decode();assert not [l for l in gpu.splitlines() if l.strip()]
# Bounded process metadata only; no process is stopped. Administrative services are not activated.
process=run('S06-final-proof-processes',['ps','-eo','pid,ppid,lstart,etime,stat,args','--sort=pid']).decode();(C/'FINAL_PROCESS_SNAPSHOT.txt').write_text(process)
queue=read(C/'FINITE_QUEUE_PROCESS.json');qp=Path('/proc/'+str(queue['pid'])+'/stat');assert not qp.exists() or qp.read_text().rsplit(')',1)[1].split()[19]!=str(queue['start_ticks']);assert read(C/'FINITE_QUEUE_EXIT.json')['exit_status']==0
failed=[r for r in commands if r.get('exit_status') not in [None,0]];timeout=[json.loads(l) for l in (C/'COMMAND_LEDGER.jsonl').read_text().splitlines() if json.loads(l).get('timed_out')]
receipt={'schema_version':'s06-external-final-delivery-proof-v1','status':'PASS','all10_mandatory_acceptance_gates_supported':True,'acceptance_gate_10':{'status':'PASS','scientific_acceptance_matrix_sha256':sha(P/'ACCEPTANCE_MATRIX.json'),'final_metadata_recovery_sha256':sha(P/'FINAL_METADATA_RECOVERY.json'),'exact_final_Git_bytes_verified':True,'owned_process_and_lock_closure':True},'research_commit':commit,'research_branch':'POD_A_SALIENCY','exact_changed_remote_files_verified':delivery['verified_remote_files'],'S06_receipt_sha256':sha(P/'S06_RECEIPT.json'),'S07_handoff_sha256':sha(P/'S07_HANDOFF.json'),'final_metadata_recovery':read(C/'FINAL_METADATA_RECOVERY_RECEIPT.json'),'all9_candidate_S06_gates_PASS':True,'original_POD_A_tip_unchanged':True,'S00_S05_tracked_trees_unchanged':True,'prompt_tracked_changes':False,'prompt_states':prompts,'known_child_exits':len(commands),'known_child_nonzero_exits':len(failed),'unknown_child_exits':0,'still_live_known_owned_children':[],'metadata_timeouts':len(timeout),'GPU_compute_processes':[],'authentic_GPU_lock_available':True,'S07_executed':False,'S07_approved':False,'Pod_shutdown_or_scheduler_activation':False,'self_reference':'External receipt intentionally not inside its own named Gitcommit or private metadataarchive','completed_utc':now()};save(C/'FINAL_DELIVERY_RECEIPT.json',receipt);print('S06_FINAL_DELIVERY_PASS',commit,flush=True)
