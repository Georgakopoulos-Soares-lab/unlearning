"""Prepare small, provenance-pinned historical-head recovery examples."""
import hashlib
import json
from pathlib import Path
import shutil

import joblib
import numpy as np
from threadpoolctl import threadpool_limits

from scripts.sayyed.multiretain_independent import reconstruct

root=Path('/workspace/meeting-artifacts/relearning-benign-v1')
ref=root/'recovery/base_h3_archive/multiretain-layers-v1-final-20261110T140836Z'
out=root/'restored-head-smoke'
out.mkdir(exist_ok=False)
reports=[]
with threadpool_limits(limits=1):
    for group,task,layer in [('H3','emp_H3','decoder_layer_16'),('other_five','gue_splice_reconstructed','final_norm')]:
        source=ref/'probes'/group/task/layer/'seed42/base.joblib'
        target=out/(task+'.joblib')
        shutil.copyfile(source,target)
        rows=[]
        for path in sorted((ref/'features'/group/'base').glob('chunk_*.npz')):
            with np.load(path,allow_pickle=False) as a:
                mask=(a['task']==task)&(a['split']=='train')
                if mask.any():
                    rows.extend(zip(a['ids'][mask].tolist(),a[layer][mask],a['labels'][mask].tolist()))
            if len(rows)>=12:
                break
        rows=rows[:12]
        assert len(rows)==12
        x=np.stack([row[1] for row in rows])
        model=joblib.load(source)
        p=model.predict_proba(x)
        independent=reconstruct(model,x)
        assert np.max(np.abs(p-independent))<=1e-12
        np.savez(out/(task+'.npz'),features=x,ids=np.array([row[0] for row in rows]),
                 labels=np.array([row[2] for row in rows]),expected_probabilities=p,classes=model[-1].classes_)
        reports.append(dict(task=task,layer=layer,rows=12,split='train',
                            original_head=str(source),head_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                            original_archive_revision='e75b95d9ca579ddb85fe354bea52bb9a78215b16',
                            maximum_independent_probability_delta=float(np.max(np.abs(p-independent)))))
(out/'PROVENANCE.json').write_text(json.dumps(dict(examples=reports,
    scope='Previously fitted historical heads and training features only; recovery diagnostics, not supplied-model measurements'),indent=2)+'\n')
print('Prepared binary and multiclass saved-head recovery examples')
