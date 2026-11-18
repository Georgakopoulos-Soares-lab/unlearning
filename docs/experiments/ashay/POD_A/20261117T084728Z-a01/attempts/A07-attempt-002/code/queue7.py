"""Finite approved A07 R5 queue only; no next-stage dispatch."""
from common7 import *
from launch7 import launch
from backup7 import main as backup
from report7 import progress

def main():
 assert read(C/'INITIAL_PRODUCTION_GATE.json')['status']=='PASS'
 for task in TASKS[1:]:
  if task=='gue_tf_0':
   assert read(C/'jobs/fit-tf-001.result.json')['status']=='PASS_EXIT'
  else:
   if task!='gue_splice_reconstructed':launch('cache-'+task+'-001','build_other_five_cache.py',['--candidate','R5','--task',task])
   launch('fit-'+task+'-001','fit_other_five.py',['--stage','A07','--candidate','R5','--task',task])
  receipts=list((A/'probes/R5'/task).glob('*/seed*/COMPLETE.json'));assert len(receipts)==78
  for p in receipts:assert read(p)['status']=='COMPLETE_UNVERIFIED' and read(p)['producer_validation']=='PASS'
  r=backup(task);assert r['status']=='PASS';publish('BACKUP_R5_'+task+'.json',r);publish('INITIAL_PRODUCTION_GATE.json',read(C/'INITIAL_PRODUCTION_GATE.json'))
  progress(task+': 78 heads and applications accepted; fresh task recovery PASS (12 paths, 240 paired vectors).')
 put(C/'FINITE_QUEUE_RESULT.json',{'status':'PASS','heads':390,'applications':390,'task_checkpoints':5,'A08_started':False,'completed_utc':now()})
 print('FINITE_A07_QUEUE_PASS',flush=True)
if __name__=='__main__':main()
