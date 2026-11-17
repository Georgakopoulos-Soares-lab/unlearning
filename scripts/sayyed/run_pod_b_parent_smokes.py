"""Qualify recovered native inference using training-only fixed8 reference smokes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from scripts.sayyed.fit_maxent_benign import arrays

root = Path('/workspace/meeting-artifacts/relearning-benign-v1')
old = root / 'recovery/base_h3_archive/multiretain-layers-v1-final-20261110T140836Z'
if not (root/'PARENT_DOWNLOAD_COMPLETE.json').exists():
    raise ValueError('Parent weight qualification required')
manifest = root/'training_smoke_manifest.jsonl'
rows = [json.loads(x) for x in manifest.read_text().splitlines()]
assert len(rows)==12 and all(r['split']=='train' for r in rows)
plan = dict(status='DECLARED_BEFORE_EXECUTION',manifest=str(manifest),
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            variants={'b8':8,'b1':1,'repeat':8},physical_batch_size=8,representations=26,
            tolerance={'atol':1e-4,'rtol':1e-5},arms=['base','maxent'],
            reference=str(old/'smokes-fixed8'),new_heldout_access=False,
            note='Qualifies recovered known parents only; supplied adapter loader remains separate')
plan_path=root/'PARENT_SMOKE_PLAN.json'
if plan_path.exists():
    raise ValueError('Smoke plan already exists; inspect completed/partial runs before resume')
plan_path.write_text(json.dumps(plan,indent=2)+'\n')
env=os.environ.copy()
env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',TORCHINDUCTOR_COMPILE_THREADS='4')
started=time.monotonic()
for arm in plan['arms']:
    assets=root/'parents'/arm
    for variant,batch in plan['variants'].items():
        cutoff=datetime.datetime.fromisoformat(json.loads((root/'session_config.json').read_text())['SCIENTIFIC_STAGE_CUTOFF_UTC'])
        if datetime.datetime.now(datetime.timezone.utc)>=cutoff:
            raise RuntimeError('Scientific-stage cutoff reached; preserve partial smokes')
        target=root/'parent-smokes'/f'{arm}-{variant}'
        command=[sys.executable,'-m','scripts.sayyed.extract_multiretain_fixed',
                 '--checkpoint',str(assets),'--config',str(assets/'run_config.yaml'),
                 '--tokenizer',str(assets/'tokenizer.json'),'--manifest',str(manifest),
                 '--output',str(target),'--model-name',arm,'--smoke','--smoke-rows','12',
                 '--batch-size',str(batch),'--session-ledger',str(root/'session_gpu_budget.json'),
                 '--session-config',str(root/'session_config.json')]
        print('START',arm,variant,flush=True)
        with (root/f'parent-smoke-{arm}-{variant}.log').open('x') as log:
            subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        print('DONE',arm,variant,flush=True)
checks=[]
for arm in plan['arms']:
    baseline,identity=arrays(root/'parent-smokes'/f'{arm}-b8',rows)
    layers=[f'decoder_layer_{i}' for i in range(25)]+['final_norm','nll_sum']
    for label,folder in [('logical1',root/'parent-smokes'/f'{arm}-b1'),
                         ('repeat',root/'parent-smokes'/f'{arm}-repeat'),
                         ('historical',old/'smokes-fixed8'/f'{arm}-b8')]:
        data,other=arrays(folder,rows)
        for key in ['checkpoint_shards','config_sha256','tokenizer_sha256','hooks']:
            if identity[key]!=other[key]:
                raise ValueError('Reference smoke identity mismatch: '+key)
        for layer in layers:
            a,b=baseline[layer],data[layer]
            if a.shape!=b.shape or not np.isfinite(b).all() or not np.allclose(a,b,**plan['tolerance']):
                raise ValueError('Smoke numerical mismatch: '+arm+'/'+label+'/'+layer)
            checks.append(dict(arm=arm,comparison=label,representation=layer,
                               max_abs_difference=float(np.max(np.abs(a.astype(float)-b.astype(float))))))
        if not np.array_equal(baseline['n_tokens'],data['n_tokens']):
            raise ValueError('Valid next-token count mismatch')
if (root/'shared_ledger_at_start.json').read_bytes()!=Path('/workspace/meeting-artifacts/evo2-pilot.gpu-budget.json').read_bytes():
    raise ValueError('Historical shared ledger changed')
result=dict(status='PASS',checks=checks,comparisons=len(checks),training_rows=12,
            wall_seconds=time.monotonic()-started,scope='Recovered parent runtime only; no supplied adapter inference')
(root/'PARENT_SMOKE_VALIDATION.json').write_text(json.dumps(result,indent=2)+'\n')
print('PARENT SMOKE VALIDATION PASS',len(checks),flush=True)
