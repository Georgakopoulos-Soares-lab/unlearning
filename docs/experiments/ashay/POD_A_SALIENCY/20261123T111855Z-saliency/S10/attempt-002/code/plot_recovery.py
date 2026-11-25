from pathlib import Path
import sys,os,runpy
root=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]).resolve();runtime=Path(sys.executable).parent.parent.resolve();code=Path(__file__).resolve().parent
def audit(event,args):
 if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
  p=Path(os.fsdecode(args[0])).resolve()
  if str(p).startswith('/workspace/pod-a-saliency') and not any(p==q or q in p.parents for q in [root,output,runtime,code]):raise PermissionError('Producer data fallback denied')
sys.addaudithook(audit);sys.argv=[str(code/'plot_logs.py'),str(root),str(output)];runpy.run_path(str(code/'plot_logs.py'),run_name='__main__')
