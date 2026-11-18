from pathlib import Path
import hashlib,json,os
import numpy as np
from production_contract import read,put,digest,sha,require,LAYERS
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-002');CFG=read(C/'RUN_CONFIG.json');A=Path(CFG['artifacts']);R=Path(CFG['root_control']);C03=R/'attempts/A03-attempt-001';INPUTS=read(C/'A06_INPUTS.json');from scope6 import authorize;authorize('R5');H=Path('/workspace/recovery/POD_A')/R.name/'A03-attempt-001/restored/base_R1/multiretain-layers-v1-final-20261110T140836Z';CONTROL=Path('/workspace/recovery/POD_A')/R.name/'A03-attempt-001/restored/controls/benign-followup-v1';SEEDS=[42,17,1234];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy']
OLD_MAP={}
for dep,root in [('base_R1',H),('controls',CONTROL)]:
 for e in read(C03/('PAYLOAD_CHECKSUMS_'+dep+'.json'))['files']:OLD_MAP[str(root/e['path'])]=e
def checked_old(path):
 path=Path(path);entry=OLD_MAP[str(path)];require(path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],'Changed historical reference');return path
def cache(alias,split,key=None):
 root=A/'h3-cache'/alias/split
 if key is None:return np.load(root/'metadata.npz',allow_pickle=False)
 return np.load(root/(key+'.npy'),mmap_mode='r',allow_pickle=False)
def saved_folds(ids,seed):
 p=checked_old(H/'probes/H3/emp_H3'/('folds_seed'+str(seed)+'.json'));j=read(p);index={v:i for i,v in enumerate(ids)};folds=[(np.array([index[v] for v in f['train_ids']]),np.array([index[v] for v in f['validation_ids']])) for f in j]
 require(len(folds)==3 and sorted(np.concatenate([b for a,b in folds]).tolist())==list(range(len(ids))),'Frozen folds incomplete');return folds,p
def draws(split,ids,groups):
 p=checked_old(H/'probes/H3/emp_H3'/(split+'_resampling.npz'))
 with np.load(p,allow_pickle=False) as z:
  require(np.array_equal(z['ids'],ids),'Historical draw order differs');names,inverse=np.unique(groups,return_inverse=True);require(np.array_equal(names,z['group_names']) and np.array_equal(inverse,z['row_groups']) and int(z['seed'])==20261103,'Historical group/seed identity differs');draw=z['group_draws'];require(draw.shape==(2000,len(names)) and np.array_equal(draw,np.random.default_rng(20261103).integers(len(names),size=draw.shape,dtype=np.int32)),'Historical draws differ');weights=np.stack([np.bincount(d,minlength=len(names)) for d in draw])[:,inverse];return weights,p
def historical_predictions(key,seed,split,metadata):
 p=checked_old(H/'probes/H3/emp_H3'/key/('seed'+str(seed))/(split+'_predictions.npz'))
 with np.load(p,allow_pickle=False) as z:
  for field in ['ids','labels','groups','sequence_sha256']:require(np.array_equal(z[field],metadata[field]),'Historical reference pairing differs: '+field)
  require(np.array_equal(z['classes'],[0,1]),'Historical class columns differ');return {name:z[name] for name in ['prob_base_refit','prob_h3_only_refit','prob_h3_only_fixed_base']},p
def control_predictions(control,seed,split,metadata):
 p=checked_old(CONTROL/'tasks/emp_H3'/('4mer' if control=='kmer4' else control)/('seed'+str(seed))/(split+'_predictions.npz'))
 with np.load(p,allow_pickle=False) as z:
  for field in ['ids','labels','groups']:require(np.array_equal(z[field],metadata[field]),'Control pairing differs')
  require(np.array_equal(z['classes'],[0,1]),'Control class order differs');return z['probabilities'],p
def file_refs(root):return [{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.iterdir()) if p.is_file() and p.name not in ['PRODUCER_COMPLETE.json','COMPLETE.json','AUDIT.json','FAILED.json']]
def verify_refs(root,receipt):
 for e in receipt['files']:
  p=root/e['path'];require(p.is_file() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'Changed producer output')
