"""Portable representative A07 recovery check from consumer-relative paths only."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import joblib
from independent_math import reconstruct,metrics
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main(root,feature_root,alias,task):
 manifest=read(feature_root/'MEMBER_MANIFEST.json');entries=manifest['files'] if isinstance(manifest,dict) else manifest;index={e['path']:e for e in entries};bundle_rel=Path('artifacts/features')/alias/task/'dev/COMPLETE.json';bp=feature_root/bundle_rel;assert sha(bp)==index[str(bundle_rel)]['sha256'];bundle=read(bp);xx={k:[] for k in ['decoder_layer_16','final_norm']};meta={k:[] for k in ['ids','labels','groups','sequence_sha256']};source_checks=[]
 for chunk in bundle['chunks']:
  rel=Path('artifacts')/chunk['path'];cp=feature_root/rel;assert sha(cp/'COMPLETE.json')==chunk['receipt_sha256'];receipt=read(cp/'COMPLETE.json');source_checks.append({'receipt_relative_path':str(rel/'COMPLETE.json'),'sha256':chunk['receipt_sha256']})
  for e in receipt['files']:
   path=cp/e['path'];assert path.stat().st_size==e['bytes'] and sha(path)==e['sha256'];assert sha(path)==index[str(path.relative_to(feature_root))]['sha256']
  with np.load(cp/'features_and_lm.npz',allow_pickle=False) as z:
   for k in xx:assert z[k].dtype==np.float32;xx[k].append(z[k])
   for k in meta:meta[k].append(z[k])
 x={k:np.concatenate(v) for k,v in xx.items()};meta={k:np.concatenate(v) for k,v in meta.items()};checks=[]
 for key in ['decoder_layer_16','final_norm']:
  unit=root/'artifacts/probes'/alias/task/key/'seed42';receipt=read(unit/'COMPLETE.json');assert receipt['status']=='COMPLETE_UNVERIFIED' and receipt['producer_validation']=='PASS';head=joblib.load(unit/'head.joblib');base=joblib.load(root/'dependencies/base-heads'/key/'base.joblib');result=read(unit/'RESULTS.json');classes=np.array([0,1,2] if task=='gue_splice_reconstructed' else [0,1])
  with np.load(unit/'dev_predictions.npz',allow_pickle=False) as z:
   for k in meta:assert np.array_equal(z[k],meta[k])
   assert np.array_equal(z['classes'],classes)
   for policy,model in [('independent_refit',head),('fixed_original_base',base)]:
    assert np.array_equal(model[-1].classes_,classes);p=reconstruct(model,x[key]);delta=float(np.max(np.abs(p-z[policy])));assert delta<=1e-10;ind,valid=metrics(meta['labels'],p,classes,np.ones((1,len(p))));assert valid.all();residual=max(abs(float(ind[row['metric']][0])-row['estimate']) for row in result['metrics'] if row['policy']==policy);assert residual<=1e-12;checks.append({'candidate':alias,'task':task,'representation':key,'seed':42,'policy':policy,'probability_max_abs':delta,'metric_max_abs':residual,'rows':len(p),'groups':len(np.unique(meta['groups'])),'classes':classes.tolist(),'status':'PASS'})
 return {'status':'PASS','checks':checks,'new_A07_consumer':str(root),'reused_verified_A06_consumer':str(feature_root),'feature_chunks':source_checks,'producer_paths_used':False,'GPU_initialization':False,'independent_release_status':'PENDING_A08; representative recovery is not full-grid verification'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--features-root',type=Path,required=True);p.add_argument('--candidate',choices=['R4','R6'],required=True);p.add_argument('--task',required=True);v=p.parse_args();print(json.dumps(main(v.root,v.features_root,v.candidate,v.task)))
