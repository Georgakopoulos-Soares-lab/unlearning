"""One finite candidate audit/refit queue and verified checkpoint; A08 only."""
from common import *
from run_phase import run
from progress import update
from deliver import deliver
import argparse
p=argparse.ArgumentParser();p.add_argument('--candidate',choices=['R4','R6'],required=True);v=p.parse_args();alias=v.candidate
for task in ['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']:
 name='audit-'+alias+'-'+task+'-001';receipt=C/('JOB_'+name+'.json')
 if receipt.exists():assert read(receipt)['status']=='EXITED_PASS'
 else:run(name,[cfg['cpu_venv']+'/bin/python',str(A/'code/audit_units.py'),'--stage','A08','--candidate',alias,'--task',task])
 seals=list((A/'audits'/alias/task).glob('*/seed*/COMPLETE.json'));assert len(seals)==78 and all(read(p)['status']=='PASS' for p in seals),'Localized failures retained; do not claim task released'
 if task in ['gue_prom_core_all','gue_mouse_0']:update(alias+'/'+task+' all-unit independent probability/metric/every-draw audit passed')
run('sampled-refits-'+alias+'-001',[cfg['cpu_venv']+'/bin/python',str(A/'code/refit_panel.py'),'--stage','A08','--candidate',alias])
seals=list((A/'refits'/alias).glob('*/*/seed*/COMPLETE.json'));assert len(seals)==30 and all(read(p)['status']=='PASS' for p in seals),'Sampled refit failure preserved; investigate before release'
with (A/'logs'/('backup-'+alias+'-001.log')).open('w') as f:subprocess.run([cfg['tools_venv']+'/bin/python',str(A/'stage_drivers/checkpoint_phase.py'),'--phase',alias],stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'HF_HUB_DISABLE_PROGRESS_BARS':'1'},check=True)
update(alias+'390all-unit audits and30prospective refits passed; private checkpoint freshly restored');deliver('POD_A A08: '+alias+' independent audits, sampled refits and fresh recovery passed');print(json.dumps({'candidate':alias,'status':'PASS','audits':390,'sampled_refits':30,'private_backup':'PASS'}),flush=True)
