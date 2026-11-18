"""Exactly one approved candidate/task batch: cache then missing finite units."""
from common import *
from run_phase import run
import argparse
p=argparse.ArgumentParser();p.add_argument('--candidate',choices=['R4','R6'],required=True);p.add_argument('--task',choices=['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'],required=True);v=p.parse_args()
stem=v.candidate+'-'+v.task
run('cache-'+stem+'-001',[cfg['cpu_venv']+'/bin/python',str(A/'code/build_other_five_cache.py'),'--candidate',v.candidate,'--task',v.task])
run('fit-'+stem+'-001',[cfg['cpu_venv']+'/bin/python',str(A/'code/fit_other_five.py'),'--stage','A07','--candidate',v.candidate,'--task',v.task])
rows=[json.loads(l) for l in (A/'logs'/('fit-'+stem+'-001.stdout.jsonl')).read_text().splitlines()];assert len(rows)==78 and all(r['status'] in ['COMPLETE_UNVERIFIED','REUSED_SEALED_PRODUCER'] for r in rows),'Some task units failed; preserve and reconcile before next batch'
print(json.dumps({'candidate':v.candidate,'task':v.task,'status':'PRODUCER_COMPLETE','heads':78,'fixed_base_applications':78}),flush=True)
