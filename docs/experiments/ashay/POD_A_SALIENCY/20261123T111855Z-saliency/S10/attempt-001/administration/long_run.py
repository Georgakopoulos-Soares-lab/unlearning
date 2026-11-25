from pathlib import Path
import os,sys,json,time,subprocess,signal
from ops import C,A,save,now

def execute(label,args,env=None):
 outpath=A/'operation-logs'/(label+'.stdout');errpath=A/'operation-logs'/(label+'.stderr');assert not outpath.exists() and not errpath.exists(),'Preserve prior logs; explicit new attempt identity required'
 with outpath.open('xb') as out,errpath.open('xb') as err:
  p=subprocess.Popen(args,env=env,stdout=out,stderr=err,start_new_session=True);started=time.monotonic();row={'stage':label,'pid':p.pid,'start_ticks':Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'argv':args,'started_utc':now(),'status':'RUNNING','stdout':str(outpath),'stderr':str(errpath),'finite_endpoint':True,'phase':'S10'};save(C/(label+'-PROGRESS.json'),row);print('START',label,'pid',p.pid,flush=True)
  while p.poll() is None:
   try:p.wait(timeout=20)
   except subprocess.TimeoutExpired:
    row.update(elapsed_seconds=time.monotonic()-started,log_bytes=outpath.stat().st_size+errpath.stat().st_size,updated_utc=now());save(C/(label+'-PROGRESS.json'),row);print('PROGRESS',label,round(row['elapsed_seconds'],1),row['log_bytes'],flush=True)
  row.update(exit_status=p.returncode,status='COMPLETE' if p.returncode==0 else 'FAILED',elapsed_seconds=time.monotonic()-started,ended_utc=now());save(C/(label+'-PROGRESS.json'),row)
  with (C/'LONG_COMMAND_LEDGER.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
  print('END',label,'exit',p.returncode,flush=True)
  if p.returncode:raise RuntimeError(label+' failed; actual exit and original logs preserved')
 return row
if __name__=='__main__':execute(sys.argv[1],sys.argv[2:])
