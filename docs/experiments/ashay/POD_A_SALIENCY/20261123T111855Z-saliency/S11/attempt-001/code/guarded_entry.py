"""Explicit fresh-consumer file-access boundary for reporting child programs."""
from pathlib import Path
import sys,os,runpy
root=Path(sys.argv[1]).resolve();target=Path(sys.argv[2]).resolve();args=sys.argv[3:];allowed=[root]
for value in os.environ.get('S11_REUSED_SOFTWARE_ROOTS','').split(os.pathsep):
 if value:allowed.append(Path(value).resolve())
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve();name=str(p)
  if name.startswith('/workspace/pod-a-saliency') or name.startswith('/root/.cache'):
   if not any(p==q or q in p.parents for q in allowed):raise PermissionError('Unrecorded producer path or cache fallback denied')
sys.addaudithook(audit);sys.path.insert(0,str(target.parent));sys.argv=[str(target),*args];runpy.run_path(str(target),run_name='__main__')
