"""Bounded train-only probe timing on recovered reference features; no held-out scores."""
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from threadpoolctl import threadpool_limits

from scripts.sayyed.h3_followup import train_model

root = Path('/workspace/meeting-artifacts/relearning-benign-v1')
reference = root / 'recovery/base_h3_archive/multiretain-layers-v1-final-20261110T140836Z'
records = []
for group, task, folds, expected in [('H3','emp_H3',3,11971),('other_five','gue_tf_0',5,1024)]:
    rows = [json.loads(line) for line in (reference/'manifests'/f'{group}.jsonl').read_text().splitlines()]
    selected = [row for row in rows if row['task']==task and row['split']=='train']
    assert len(selected)==expected
    pieces = []
    for path in sorted((reference/'features'/group/'base').glob('chunk_*.npz')):
        with np.load(path,allow_pickle=False) as a:
            mask = (a['split']=='train') & (a['task']==task)
            if not mask.any():
                continue
            pieces.append({key:a[key][mask] for key in ['ids','labels','groups','decoder_layer_16','final_norm']})
    arrays = {key:np.concatenate([p[key] for p in pieces]) for key in pieces[0]}
    assert arrays['ids'].tolist()==[r['id'] for r in selected]
    assert arrays['labels'].tolist()==[r['label'] for r in selected]
    y,groups = arrays['labels'],arrays['groups']
    tr,va = next(StratifiedGroupKFold(n_splits=folds,shuffle=True,random_state=42).split(np.zeros(len(y)),y,groups))
    assert not set(groups[tr]) & set(groups[va])
    for layer in ['decoder_layer_16','final_norm']:
        for c in [.1,10.]:
            started,cpu = time.monotonic(),time.process_time()
            with threadpool_limits(limits=1):
                model,attempts = train_model(arrays[layer][tr],y[tr],c)
            records.append(dict(task=task,layer=layer,C=c,training_rows=len(tr),
                                wall_seconds=time.monotonic()-started,cpu_seconds=time.process_time()-cpu,
                                attempts=attempts,converged=not attempts[-1]['warnings']))
            print(task,layer,c,records[-1]['wall_seconds'],flush=True)
            del model
result = dict(scope='Training-only timing on compatible historical base features; zero delivered-model performance scores',
              source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              fits=len(records),records=records,cv_seed=42,blas_threads=1,
              limitations='Reference timings are provisional; adapter-specific convergence and full bootstrap/audit/IO cost remain unmeasured')
(root/'TRAIN_ONLY_PROBE_TIMING.json').write_text(json.dumps(result,indent=2)+'\n')
