"""Run one saved-head recovery check from a freshly restored A03 checkpoint mapping."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
from historical_independent_math import reconstruct,metrics

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def checked(ref):
 p=Path(ref['path']);assert p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256'];return p

def main(root):
 inputs=json.loads((root/'control/REPRESENTATIVE_RECOVERY_INPUTS.json').read_text());mappings=json.loads((root/'public/PATH_TRANSLATION.json').read_text())['mappings']
 def resolve(old):
  p=Path(old)
  for m in sorted(mappings,key=lambda m:len(m['original_root']),reverse=True):
   op=Path(m['original_root'])
   if p.is_relative_to(op):return Path(m['restored_root'])/p.relative_to(op)
  raise ValueError('Path outside restored dependency mapping')
 headref=inputs['head'];headpath=resolve(inputs['historical_head_path']);assert headpath==checked(headref);manifest=checked(inputs['cohort_manifest']);rows=[json.loads(l) for l in manifest.read_text().splitlines()];rr=[r for r in rows if r['task']==inputs['task'] and r['split']==inputs['split']];features=[];ids=[];labels=[]
 for ref in inputs['feature_chunks']:
  p=checked(ref)
  with np.load(p,allow_pickle=False) as z:
   mask=(z['task']==inputs['task'])&(z['split']==inputs['split']);features.append(z[inputs['array_key']][mask]);ids.extend(z['ids'][mask].tolist());labels.extend(z['labels'][mask].tolist())
 assert ids==[r['id'] for r in rr] and labels==[r['label'] for r in rr];x=np.concatenate(features);model=joblib.load(headpath)
 # Explicit saved scaler/coefficients; no estimator fitting, model backbone, or inference runtime.
 p=reconstruct(model,x)
 with np.load(checked(inputs['saved_predictions']),allow_pickle=False) as z:
  assert z['ids'].tolist()==ids and z['labels'].tolist()==labels;classes=z['classes'];assert np.array_equal(model[-1].classes_,classes);d=float(np.max(np.abs(p-z['prob_base_refit'])));assert d<=1e-10
  got,valid=metrics(np.array(labels),p,classes,np.ones((1,len(ids))));assert valid.all()
 result=json.loads(checked(inputs['saved_results']).read_text());md=0.
 for row in result['metrics']:
  if row['split']==inputs['split'] and row['policy']=='base_refit':md=max(md,abs(float(got[row['metric']][0])-row['value']))
 assert md<=1e-12
 out={'status':'PASS','checkpoint_root':str(root),'executed_code':str(Path(__file__).resolve()),'executed_code_sha256':sha(__file__),'task':inputs['task'],'split':inputs['split'],'layer':inputs['array_key'],'seed':42,'rows':len(ids),'probability_max_residual':d,'metric_max_residual':md,'head_sha256':headref['sha256'],'inherited_chunk_count':len(inputs['feature_chunks']),'source_scope':'New A03 checkpoint all bytes freshly downloaded and restored; computation uses its restored code/mapping plus already freshly retrieved/all-byte-verified inherited historical archive payloads. Historical14.58GB archives were not redownloaded for this small check.','not_full_A09_or_GPU_recovery':True}
 print(json.dumps(out));return out
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',required=True,type=Path);args=ap.parse_args()
 with threadpool_limits(limits=4):main(args.root.resolve())
