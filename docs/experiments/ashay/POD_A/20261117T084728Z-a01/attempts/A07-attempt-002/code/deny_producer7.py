"""Practical isolation check: restored CLI succeeds while producer tree reads are denied."""
import sys,os,json
from pathlib import Path
root=Path(sys.argv[1]);depmap=Path(sys.argv[2]);task=sys.argv[3]
blocked=['/workspace/meeting-artifacts','/workspace/agent-handoff','/workspace/wt-pod-a'];events=[]
def audit(event,args):
 if event in ['open','os.listdir','os.scandir'] and args and isinstance(args[0],(str,bytes,os.PathLike)):
  p=os.path.abspath(os.fsdecode(args[0]))
  if any(p==b or p.startswith(b+'/') for b in blocked):
   events.append({'event':event,'path':p});raise PermissionError('Producer access denied by recovery isolation test')
sys.addaudithook(audit)
try:open('/workspace/meeting-artifacts/A07-isolation-sentinel','rb')
except PermissionError:pass
else:raise AssertionError('Denial sentinel did not fire')
sys.path.insert(0,str(root/'artifacts/code'))
from restore7 import main
j=main(root,json.loads(depmap.read_text()),task);j.update(producer_path_denial_active=True,denied_sentinel_events=events,additional_fits=0,scope='Single already frozen TF task recovery panel:12 paths/240 paired vectors; isolation qualification only')
assert len(events)==1
print(json.dumps(j,allow_nan=False))
