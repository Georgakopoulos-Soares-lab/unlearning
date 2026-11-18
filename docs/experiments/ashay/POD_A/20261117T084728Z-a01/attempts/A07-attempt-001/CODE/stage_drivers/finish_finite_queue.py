"""Controller for the remaining nine explicitly enumerated A07 task batches only."""
from common import *
import time
from progress import update
from deliver import deliver
queue=[('R4','gue_prom_core_all'),('R4','gue_prom_300_all'),('R4','gue_splice_reconstructed'),('R4','gue_mouse_0'),('R6','gue_tf_0'),('R6','gue_prom_core_all'),('R6','gue_prom_300_all'),('R6','gue_splice_reconstructed'),('R6','gue_mouse_0')]
assert read(C/'INITIAL_PRODUCTION_GATE.json')['status']=='PASS' and read(C/'BACKUP_R4_gue_tf_0.json')['status']=='PASS'
identity={'stage':'A07','pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_utc':now(),'finite_queue':queue,'status':'RUNNING','no_next_stage_dispatch':True};put(C/'FINITE_QUEUE_CONTROLLER.json',identity)
for alias,task in queue:
 stem=alias+'-'+task
 with (A/'logs'/('controller-'+stem+'.log')).open('w') as log:
  subprocess.run([sys.executable,str(A/'stage_drivers/produce_task.py'),'--candidate',alias,'--task',task],stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run([cfg['tools_venv']+'/bin/python',str(A/'stage_drivers/checkpoint_task.py'),'--candidate',alias,'--task',task],stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'HF_HUB_DISABLE_PROGRESS_BARS':'1'},check=True)
 if task=='gue_mouse_0':
  update(alias+' all five task batches producer-complete and privately restored; A08 verification pending');deliver('POD_A A07: '+alias+' 390 probes and fixed-base applications protected; audit pending')
identity.update(status='COMPLETE',completed_utc=now());put(C/'FINITE_QUEUE_CONTROLLER.json',identity);print(json.dumps({'status':'COMPLETE','remaining_task_batches':9,'A08_started':False}),flush=True)
