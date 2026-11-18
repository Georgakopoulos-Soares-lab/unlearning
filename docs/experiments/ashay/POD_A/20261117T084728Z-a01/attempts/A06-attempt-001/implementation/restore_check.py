"""Portable CPU-only checks using exclusively fresh-restored A06 payload members."""
from pathlib import Path
import argparse,hashlib,json,sys,math
import numpy as np,joblib
from threadpoolctl import threadpool_limits
from independent_math import reconstruct,metrics
def read(p):return json.loads(Path(p).read_text())
def main(root,candidate,group):
 art=root/'artifacts';checked=0;head_checks=[];lm=[]
 for done in (art/'features'/candidate).glob('*/*/COMPLETE.json'):
  task=done.parent.parent.name
  if (task=='emp_H3')!=(group=='H3'):continue
  bundle=read(done);loss=[];count=[];ids=[]
  for e in bundle['chunks']:
   p=art/e['path']/'features_and_lm.npz'
   with np.load(p,allow_pickle=False) as z:
    ids.extend(z['ids'].tolist());loss.extend(z['nll_sum'].astype(np.float64).tolist());count.extend(z['n_tokens'].tolist());assert np.array_equal(z['n_tokens'],z['lengths']-1)
  assert len(ids)==bundle['rows'] and len(set(ids))==len(ids);nll=math.fsum(loss)/math.fsum(count);saved=read(art/'lm'/candidate/task/done.parent.name/'RESULTS.json');assert abs(nll-saved['NLL'])<=1e-12;lm.append({'task':task,'split':done.parent.name,'rows':len(ids),'NLL_abs_residual':abs(nll-saved['NLL'])})
 if group=='H3':
  for key in ['decoder_layer_16','final_norm']:
   unit=art/'h3'/candidate/key/'seed42';head=joblib.load(unit/'head.joblib');base=joblib.load(root/'dependencies/base-heads'/key/'seed42/base.joblib')
   for split in ['dev','test']:
    bundle=read(art/'features'/candidate/'emp_H3'/split/'COMPLETE.json');parts=[];ids=[];labels=[]
    for e in bundle['chunks']:
     with np.load(art/e['path']/'features_and_lm.npz',allow_pickle=False) as z:parts.append(z[key]);ids.extend(z['ids'].tolist());labels.extend(z['labels'].tolist())
    x=np.concatenate(parts);y=np.array(labels);maxp=0.;maxmetric=0.
    with np.load(unit/(split+'_predictions.npz'),allow_pickle=False) as z:
     assert z['ids'].tolist()==ids and z['labels'].tolist()==labels
     for policy,model in [('independent_refit',head),('fixed_original_base',base)]:
      prob=reconstruct(model,x);diff=float(np.max(np.abs(prob-z[policy])));assert diff<=1e-10;maxp=max(maxp,diff);values,valid=metrics(y,prob,z['classes'],np.ones((1,len(y))));assert valid.all();report=read(unit/'RESULTS.json')
      for row in report['metrics']:
       if row['policy']==policy and row['split']==('test_exploratory' if split=='test' else split):d=abs(float(values[row['metric']][0])-row['estimate']);assert d<=1e-12;maxmetric=max(maxmetric,d)
    head_checks.append({'key':key,'seed':42,'split':split,'rows':len(ids),'policies':2,'probability_max_abs':maxp,'metric_max_abs':maxmetric})
 assert len(lm)==(3 if group=='H3' else 10);assert len(head_checks)==(4 if group=='H3' else 0);print(json.dumps({'status':'PASS','candidate':candidate,'group':group,'restored_head_checks':head_checks,'restored_LM_aggregations':lm,'root':str(root),'GPU_loads':0,'external_producer_paths_used':False}))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--candidate',choices=['R4','R6'],required=True);p.add_argument('--group',choices=['H3','other_five'],required=True);a=p.parse_args()
 with threadpool_limits(limits=4):main(a.root,a.candidate,a.group)
