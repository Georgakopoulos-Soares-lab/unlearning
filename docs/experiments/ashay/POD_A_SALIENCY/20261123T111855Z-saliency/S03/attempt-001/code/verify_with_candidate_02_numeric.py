from pathlib import Path
import json,sys,hashlib
import numpy as np
from ops import C,A,save,now
sys.path.insert(0,str(A/'code'))
from qualification_contract import componentwise,LAYERS
rows=json.loads((C/'INITIAL_NUMERICAL_COMPARISONS.json').read_text())['comparisons']
assert all(r['status']=='PASS' for r in rows)
def compare(label,obs,ref):
 a=np.load(obs,allow_pickle=False);b=np.load(ref,allow_pickle=False)
 for k in ['ids','labels','split','task','groups','sequence_sha256','lengths','n_tokens']:
  assert np.array_equal(a[k],b[k]),(label,k)
 metrics={k:{j:v for j,v in componentwise(a[k],b[k]).items() if j not in ['worst_observed','worst_reference']} for k in LAYERS+['nll_sum']}
 rows.append({'comparison':label,'observed_sha256':hashlib.sha256(obs.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),'status':'PASS' if all(v['status']=='PASS' for v in metrics.values()) else 'FAIL','outputs':metrics})
for alias in ['candidate_02']:
 root=A/'qualification'/alias
 for variant in ['logical1','repeat8']:
  compare(alias+'/'+variant+'-vs-logical8',root/variant/'attempt-001/features_and_lm.npz',root/'logical8/attempt-001/features_and_lm.npz')
report={'schema':'pod-a-s03-initial-numeric-v1','status':'PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL','verified_utc':now(),'comparisons':rows,'tolerance':'Every coordinate abs(observed-reference) <= 1e-4 + 1e-5*abs(reference)','scope':'Only exact frozen12 TRAIN technical witnesses; no scientific measurements','outcome_ranking':False}
save(C/'INITIAL_NUMERICAL_COMPARISONS.with-candidate-02.json',report)
for r in rows:print(r['comparison'],r['status'],'max_abs',max(v['max_abs_residual'] for v in r['outputs'].values()),'max_scaled',max(v['max_scaled_residual'] for v in r['outputs'].values()),'failed',[k for k,v in r['outputs'].items() if v['status']!='PASS'])
print('AGGREGATE',report['status'])
