"""Discriminating binary/multiclass head checks from the fresh downloaded payload."""
from pathlib import Path
import json,sys,time,hashlib
import numpy as np
import joblib
r=Path('/workspace/meeting-artifacts/multiretain-layers-v1');backup=json.loads((r/'NEW_BACKUP_VERIFICATION.json').read_text());assert backup['status']=='VERIFIED_PRIVATE_FRESH_DOWNLOAD';payload=Path(backup['fresh_payload_root']);sys.path.insert(0,str(payload/'source'))
from scripts.sayyed import multiretain_independent as independent
assert Path(independent.__file__).is_relative_to(payload/'source')
started=time.monotonic();cases=[]
for group,task in [('H3','emp_H3'),('other_five','gue_splice_reconstructed')]:
 unit=payload/'probes'/group/task/'decoder_layer_0/seed42';saved=np.load(unit/'dev_predictions.npz',allow_pickle=False);ids=saved['ids'][:12].tolist();manifest=[json.loads(line) for line in (payload/'manifests'/(group+'.jsonl')).read_text().splitlines()];lookup={row['id']:i for i,row in enumerate(manifest)};features={}
 for arm in ['base','maxent']:
  rows=[]
  for identity in ids:
   index=lookup[identity];start=(index//8)*8
   with np.load(payload/'features'/group/arm/f'chunk_{start:06d}.npz',allow_pickle=False) as chunk:
    offset=index-start;assert str(chunk['ids'][offset])==identity;rows.append(chunk['decoder_layer_0'][offset])
  features[arm]=np.stack(rows)
 models={'base':joblib.load(unit/'base.joblib'),'post':joblib.load(unit/'h3_only_maxent.joblib')}
 for policy,model,arm in [('base_refit','base','base'),('h3_only_refit','post','maxent'),('h3_only_fixed_base','base','maxent')]:
  assert np.array_equal(models[model][-1].classes_,saved['classes']);actual=independent.reconstruct(models[model],features[arm]);expected=saved['prob_'+policy][:12];delta=float(np.max(np.abs(actual-expected)));assert delta<=1e-10;cases.append(dict(task=task,split='dev',layer='decoder.layers.0',cv_seed=42,policy=policy,rows=12,classes=saved['classes'].tolist(),max_probability_delta=delta))
result=dict(status='PASS',fresh_payload_root=str(payload),remote_revision=backup['remote_revision'],cases=cases,source_module=str(independent.__file__),source_sha256=hashlib.sha256(Path(independent.__file__).read_bytes()).hexdigest(),wall_seconds=time.monotonic()-started,scope='Actual fresh payload source/features/models/predictions; binary and three-class task; all three policies; supplements complete archive/payload hash roundtrip and prior full audit; no GPU regeneration')
(r/'FRESH_RESTORE_COMPUTATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
