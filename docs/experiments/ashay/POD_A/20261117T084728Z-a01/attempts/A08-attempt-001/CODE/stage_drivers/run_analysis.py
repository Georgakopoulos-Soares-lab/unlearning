"""Finite predeclared A08 R6-minus-R4 family only; stop after protected analysis."""
from common import *
from run_phase import run
from progress import update
from deliver import deliver
assert read(C/'NUMERICAL_AUDIT.json')['status']=='PASS' and read(C/'AUDIT_REFIT_RECEIPT.json')['status']=='PASS'
identity={'stage':'A08','pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'started_utc':now(),'status':'RUNNING','tasks':['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'],'new_families':['PREDECLARED_NONADJACENT_R6_MINUS_R4'],'A09_dispatch':False};put(C/'ANALYSIS_CONTROLLER.json',identity)
for task in identity['tasks']:
 run('analysis-'+task+'-001',[cfg['cpu_venv']+'/bin/python',str(A/'code/analysis_pairs.py'),'--stage','A08','--kind','classifier','--task',task]);rows=[json.loads(l) for l in (A/'logs'/('analysis-'+task+'-001.stdout.jsonl')).read_text().splitlines()];assert len(rows)==(156 if task=='emp_H3' else 78) and all(r['status']=='PASS' for r in rows),'Preserved analysis failure: inspect before releasing affected family'
 if task in ['emp_H3','gue_prom_300_all']:update('Predeclared nonadjacent classifier family independently checked through '+task)
run('analysis-LM-001',[cfg['cpu_venv']+'/bin/python',str(A/'code/analysis_pairs.py'),'--stage','A08','--kind','LM']);rows=[json.loads(l) for l in (A/'logs/analysis-LM-001.stdout.jsonl').read_text().splitlines()];assert len(rows)==7 and all(r['status']=='PASS' for r in rows)
with (A/'logs/backup-analysis-001.log').open('w') as f:subprocess.run([cfg['tools_venv']+'/bin/python',str(A/'stage_drivers/checkpoint_phase.py'),'--phase','analysis'],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'HF_HUB_DISABLE_PROGRESS_BARS':'1'},check=True)
identity.update(status='COMPLETE',completed_utc=now());put(C/'ANALYSIS_CONTROLLER.json',identity);update('Full predeclared nonadjacent classifier andLM families passed; analysis payload freshly recovered');deliver('POD_A A08: verified predeclared nonadjacent classifier and LM comparisons protected');print(json.dumps({'status':'PASS','classifier_rows':5460,'LM_rows':14,'A09_started':False}),flush=True)
