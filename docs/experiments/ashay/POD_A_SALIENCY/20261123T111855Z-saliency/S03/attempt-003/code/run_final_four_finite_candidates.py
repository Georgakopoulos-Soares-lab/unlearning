"""Finite approved remaining12GPUunits and their recovery checkpoints. No phase switching/watchers."""
from pathlib import Path
import os,sys,json,hashlib,subprocess
from ops import C,A,R,save,run,now
from long_run import execute
aliases=['candidate_06','candidate_07','candidate_08','candidate_09'];assert all(any(r['alias']==a and r['status']=='LOCAL_NATIVE_SHA256_AND_MAPPING_PASS' for r in json.loads((C/'MIRROR_LOCAL_ADMISSION.json').read_text())['records']) for a in aliases);oldA=A.with_name('attempt-001');cpu=oldA/'cpu-reference-runtime/bin/python';hf=Path('/workspace/pod-a-saliency/tools/hf/bin/python');master={'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()};save(C/'remaining-final-four-GPU_QUEUE.json',{'status':'RUNNING','owned_process':master,'finite_aliases':aliases,'maximum_GPU_units':12,'next_phase_dispatch':False,'started_utc':now()});os.chdir(C)
for alias in aliases:
 protected=C/'PROTECTED_CANDIDATES.json'
 if protected.exists() and any(r['alias']==alias and r['status']=='QUALIFIED_PRIVATE_NATIVE_AND_OUTPUT_RECOVERY_PASS' for r in json.loads(protected.read_text())['records']):print('REUSE_ALREADY_PROTECTED_CANDIDATE',alias,flush=True);continue
 try:execute('finite-GPU-parent-'+alias+'-001',[sys.executable,str(C/'run_candidate_units.py'),alias])
 except RuntimeError:
  # A source/authority/runtime shared failure stops dependent dispatch; an actual candidate model failure is preserved and does not poison others.
  failed=list((A/'qualification'/alias).glob('*/attempt-001/FAILED.json')) if (A/'qualification'/alias).exists() else []
  shared=not failed or any(any(word in json.loads(p.read_text()).get('reason','').lower() for word in ['source changed','package','gpu is owned','runtime interpreter']) for p in failed)
  save(C/(alias+'-FINITE_PIPELINE_FAILURE.json'),{'status':'FAILED_PRESERVED','stage':'GPU','shared_failure':shared,'actual_failed_receipts':[str(p) for p in failed],'observed_utc':now()})
  if shared:raise
  print('CANDIDATE_SPECIFIC_GPU_FAILURE_PRESERVED',alias,flush=True);continue
 numeric=C/(alias+'-NUMERIC_QUALIFICATION.json')
 if not numeric.exists():
  try:run('numeric-'+alias+'-001',[str(cpu),str(C/'verify_candidate_numeric.py'),alias])
  except RuntimeError:print('CANDIDATE_NUMERIC_GATE_FAILED_PRESERVED',alias,flush=True);continue
 else:assert json.loads(numeric.read_text())['status']=='PASS'
 backup=C/(alias+'-PRIVATE_BACKUP_RECEIPT.json')
 if not backup.exists():execute('protect-'+alias+'-output-001',[str(hf),str(C/'protect_candidate_outputs.py'),alias])
 rec=json.loads(backup.read_text());assert rec['exact_member_hash_set_verified'] and rec['force_fresh_network_read'] and rec['destination_private'];restore=C/(alias+'-RESTORED_CPU_REPLAY.json')
 if not restore.exists():run('fresh-CPU-replay-'+alias+'-001',[str(cpu),str(C/'verify_candidate_numeric.py'),alias,rec['restored_consumer_root']])
 else:assert json.loads(restore.read_text())['status']=='PASS'
 run('close-protected-'+alias+'-001',[sys.executable,str(C/'close_protected_candidate.py'),alias]);print('FINITE_CANDIDATE_FULLY_QUALIFIED_AND_PROTECTED',alias,flush=True)
save(C/'remaining-final-four-GPU_QUEUE.json',{'status':'FINITE_QUEUE_DRAINED','owned_process':master,'finite_aliases':aliases,'exit_status':0,'completed_utc':now(),'next_phase_dispatch':False});print('FINAL_FOUR_FINITE_S03_CANDIDATES_DRAINED_NO_S04',flush=True)
