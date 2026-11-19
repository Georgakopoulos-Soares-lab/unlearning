"""Render a fresh main figure with producer paths inaccessible and exact source-key checks."""
from pathlib import Path
import argparse,os,sys,json,csv,hashlib,importlib.util
import matplotlib
matplotlib.use('Agg')
import plot9

def read(p):return json.loads(Path(p).read_text())
def main(root,output):
 plot=read(root/'public/plot_data/main_figures.json');cov=list(csv.DictReader((root/'public/COVERAGE.csv').open()));inc={(r['candidate'],r['task']):r for r in csv.DictReader((root/'public/INCLUSION_EXPOSURE_PLAN.csv').open())}
 for r in plot['coverage']:
  n=sum(v['candidate']==r['checkpoint_alias'] and v['task']==r['task'] and v['kind']=='final_head' and v['independently_released']=='True' for v in cov);assert n==r['released_heads'] and int(n==78)==r['value']
 for r in plot['declarations']:
  s=inc.get((r['checkpoint_alias'],r['task']));v=2 if s is None or r['checkpoint_alias']=='R2' else {'true':1,'false':0}.get(s['observed_selected_config_declares_family'].lower(),2);assert v==r['value'] and r['realized_exposure']=='UNKNOWN'
 plot9.main(root/'public/plot_data/main_figures.json',output,'main_coverage');report=read(output/'FIGURE_RENDER.json');assert len(report['figures'])==1;return {'status':'PASS','figure':'main_coverage','source_rows_regenerated':True,'coverage_declaration_cells':84,'rendered_output':str(output),'matplotlib':matplotlib.__version__,'new_science':0}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();events=[]
 def deny(event,args):
  if event in ['open','os.listdir','os.scandir'] and args and isinstance(args[0],(str,bytes,os.PathLike)):
   q=os.path.abspath(os.fsdecode(args[0]))
   if any(q==b or q.startswith(b+'/') for b in ['/workspace/meeting-artifacts','/workspace/agent-handoff','/workspace/wt-pod-a']):events.append(event);raise PermissionError('A09 renderer producer paths denied')
 sys.addaudithook(deny)
 try:open('/workspace/meeting-artifacts/A09-renderer-denial-sentinel','rb')
 except PermissionError:pass
 else:raise AssertionError('Denial sentinel not rejected')
 # Capture the renderer's routine progress line so stdout remains one exact JSON object.
 import contextlib,io
 with contextlib.redirect_stdout(io.StringIO()):r=main(a.root,a.output)
 assert len(events)==1;r['producer_path_denial_active']=True;r['sentinel_rejection_proven']=True;print(json.dumps(r))
