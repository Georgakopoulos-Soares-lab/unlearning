from pathlib import Path
import json,datetime,subprocess,os,signal
C=Path('/workspace/pod-a-saliency/control/20261123T111855Z-saliency/S03/attempt-003')
A=Path('/workspace/pod-a-saliency/artifacts/20261123T111855Z-saliency/S03/attempt-003');L=A/'operation-logs';L.mkdir(exist_ok=True)
R=Path('/workspace/pod-a-saliency/research-POD_A_SALIENCY')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,v):
 t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(v,indent=2)+'\n' if not isinstance(v,str) else v);t.replace(p)
def run(label,args,cwd=None,network=False,allowed=(0,)):
 limit=45 if network else 15;start=now();print(start+' START '+label,flush=True)
 p=subprocess.Popen(args,cwd=cwd,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'},stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:start_ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19]
 except OSError:start_ticks=None
 timed=False
 try:out,err=p.communicate(timeout=limit)
 except subprocess.TimeoutExpired:
  timed=True;os.killpg(p.pid,signal.SIGTERM)
  try:out,err=p.communicate(timeout=3)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);out,err=p.communicate(timeout=3)
 (L/(label+'.stdout')).write_bytes(out);(L/(label+'.stderr')).write_bytes(err)
 row={'operation':label,'argv':args,'cwd':str(cwd) if cwd else None,'pid':p.pid,'process_start_ticks':start_ticks,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'start_utc':start,'end_utc':now(),'exit_status':p.returncode,'exited':p.poll() is not None,'timed_out':timed,'timeout_seconds':limit,'stdout_log':str(L/(label+'.stdout')),'stderr_log':str(L/(label+'.stderr'))}
 with (C/'COMMAND_LEDGER.jsonl').open('a') as f:f.write(json.dumps(row)+'\n')
 print(now()+' END '+label+' rc='+str(p.returncode)+' timeout='+str(timed),flush=True)
 if timed or p.returncode not in allowed:raise RuntimeError(label+' failed; exact owned process disposition/logs retained')
 return out
