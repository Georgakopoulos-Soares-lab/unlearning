"""Finite approved S08 final delivery. S09 is never dispatched."""
from pathlib import Path
import os,json,fcntl
from ops import C,save,now
from long_run import execute
assert json.loads((C/'FINITE_RECOVERY_EXIT.json').read_text())['exit_status']==0
record=C/'FINITE_CLOSEOUT_PROCESS.json'
if record.exists():
    old=json.loads(record.read_text());p=Path('/proc/'+str(old['pid'])+'/stat');assert not p.exists() or p.read_text().rsplit(')',1)[1].split()[19]!=str(old['start_ticks']),'Prior exact closeout still live'
with (C/'CLOSEOUT.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);save(record,{'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'phase':'S08','scope':'Finite final validation/scientific seal/publication/final metadata recovery/external delivery proof; no S09','started_utc':now()})
    py='/usr/local/bin/python3'
    execute('S08-final-output-validation-001',[py,str(C/'validate_report.py')])
    execute('S08-final-phase-seal-001',[py,str(C/'seal_phase_delivery.py')])
    execute('S08-scientific-publication-001',[py,str(C/'publish_checkpoint.py'),'S08-science-001','Seal complete independently verified S08 release and exact S09 handoff'])
    execute('S08-final-administrative-recovery-001',['/workspace/pod-a-saliency/tools/hf/bin/python',str(C/'protect_final_metadata.py')])
    execute('S08-final-recovery-record-001',[py,str(C/'record_final_recovery.py')])
    execute('S08-final-publication-001',[py,str(C/'publish_checkpoint.py'),'S08-final-001','Record verified S08 final administrative recovery and source-bound S09 handoff'])
    execute('S08-final-delivery-proof-001',[py,str(C/'final_delivery_proof.py')])
print('S08_FINITE_CLOSEOUT_DRAINED_STOP_BEFORE_S09',flush=True)
