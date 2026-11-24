"""Finite five-task S07 producer only, exact valid checkpoints reused; never dispatch S08."""
from pathlib import Path
import sys,json,hashlib,os
from ops import C,A,save,now
from long_run import execute
from dispatch_utils import complete
cfg=json.loads((C/'RUN_CONFIG.json').read_text());alias=sys.argv[1];assert alias in {v['alias'] for v in cfg['candidates']};source=hashlib.sha256((C/'SOURCE_IDENTITY.json').read_bytes()).hexdigest();save(C/(alias+'-PRODUCER_CONTROLLER.json'),{'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'status':'RUNNING','source_bundle_sha256':source,'finite_tasks':cfg['tasks'],'updated_utc':now()})
execute('S07-'+alias+'-feature-admission-001',[sys.executable,str(C/'admit_features.py'),alias])
for t in cfg['tasks']:
 p=A/'candidates'/alias/'tasks'/t/'GROUP_PRODUCTION.json'
 if p.exists():
  g=json.loads(p.read_text());assert g['producer_status']=='PASS' and g['status']=='COMPLETE_UNVERIFIED' and g['source_bundle_sha256']==source
  for rep in cfg['representations']:
   for seed in cfg['seeds']:assert complete(alias,t,rep,seed)
  print('REUSED_VALID_COMPLETE_S07_TASK_GROUP',alias,t,flush=True);continue
 execute('S07-'+alias+'-'+t+'-group-001',[sys.executable,str(C/'run_task_group.py'),alias,t])
 execute('S07-'+alias+'-'+t+'-resume-checkpoint-001',[sys.executable,str(C/'refresh_resume.py')])
 print('S07_PRODUCER_CHECKPOINT',alias,t,flush=True)
print('S07_FIVE_TASK_CANDIDATE_PRODUCTION_DRAINED',alias,flush=True)
