"""Training-only fixed8 gate for new model and cached-base compatibility."""
import argparse,json,hashlib,time
from pathlib import Path
import numpy as np
from scripts.sayyed.fit_maxent_benign import arrays
from scripts.sayyed.multiretain_support import atomic_json

def main():
 p=argparse.ArgumentParser();p.add_argument('--run',required=True);a=p.parse_args();r=Path(a.run);plan=json.loads((r/'SMOKE_PLAN.json').read_text());rows=[json.loads(x) for x in Path(plan['manifest']).read_text().splitlines()];assert all(x['split']=='train' for x in rows);checks=[]
 new,identity=arrays(r/'smokes/new-b8',rows)
 assert identity['physical_batch_size']==8 and identity['runtime']==json.loads((Path(plan['reference_run'])/'features/H3/base/identity.json').read_text())['runtime']
 for v in ['b1','repeat']:
  other,ii=arrays(r/'smokes'/('new-'+v),rows)
  for k in ['checkpoint_shards','config_sha256','tokenizer_sha256','hooks','runtime','source_sha256']:assert ii[k]==identity[k]
  for k in [f'decoder_layer_{i}' for i in range(25)]+['final_norm','nll_sum']:
   tol=plan['nll_tolerance' if k=='nll_sum' else 'pooling_tolerance'];assert new[k].shape==other[k].shape and np.isfinite(other[k]).all();assert np.allclose(new[k],other[k],**tol),(v,k,float(np.max(np.abs(new[k]-other[k]))));checks.append(dict(variant=v,array=k,max_abs_difference=float(np.max(np.abs(new[k].astype(float)-other[k].astype(float)))),tolerance=tol))
  assert np.array_equal(new['n_tokens'],other['n_tokens']);assert np.array_equal(new['ids'],other['ids'])
 for arm in ['base','maxent']:
  cached,ci=arrays(Path(plan['reference_run'])/'smokes-fixed8'/(arm+'-b8'),rows)
  assert ci['runtime']==identity['runtime'] and ci['hooks']==identity['hooks']
  for k in [f'decoder_layer_{i}' for i in range(25)]+['final_norm']:assert cached[k].shape==new[k].shape and np.isfinite(cached[k]).all()
 result=dict(status='PASS',comparisons=len(checks),checks=checks,rows=len(rows),scope='New model all26 fixed8 repeat/logicalbatch checks and unchanged runtime/hook compatibility with verified cached base/H3-only training smokes; strict loading/masks/filler handled by unchanged extractor',no_new_base_inference=True)
 atomic_json(r/'SMOKE_VALIDATION.json',result);print('PASS',len(checks))
if __name__=='__main__':main()
