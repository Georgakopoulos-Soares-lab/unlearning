from ops import C,A,save,now
from pathlib import Path
import json,hashlib,sys
import numpy as np
sys.path.insert(0,str(A/'code'));from qualification_contract import componentwise,LAYERS
old=A/'qualification/candidate_01/logical8/attempt-001';new=A/'qualification/candidate_01/logical8/attempt-002'
r=json.loads((new/'COMPLETE.json').read_text());assert r['status']=='PASS'
for f in r['files']:assert (new/f['path']).stat().st_size==f['bytes'] and hashlib.sha256((new/f['path']).read_bytes()).hexdigest()==f['sha256']
a=np.load(new/'features_and_lm.npz',allow_pickle=False);b=np.load(old/'features_and_lm.npz',allow_pickle=False)
for k in ['ids','task','labels','split','groups','sequence_sha256','lengths','n_tokens']:assert np.array_equal(a[k],b[k])
metrics={k:{n:v for n,v in componentwise(a[k],b[k]).items() if n not in ['worst_observed','worst_reference']} for k in LAYERS+['nll_sum']};assert all(v['status']=='PASS' for v in metrics.values())
for name in ['native_inventory.json']:
 x=json.loads((old/name).read_text());y=json.loads((new/name).read_text());assert x['model_tensor_content_sha256']==y['model_tensor_content_sha256']
report={'schema':'pod-a-s03-fresh-process-replay-v1','status':'PASS','completed_utc':now(),'fresh_complete_receipt_sha256':hashlib.sha256((new/'COMPLETE.json').read_bytes()).hexdigest(),'producer_complete_receipt_sha256':hashlib.sha256((old/'COMPLETE.json').read_bytes()).hexdigest(),'source_identity_sha256':r['identity']['source_identity_sha256'],'runtime_lock_sha256':r['identity']['runtime_lock_sha256'],'producer_fallback':False,'raw_weights_fresh_reacquisition':True,'metadata_restored_from_private_checkpoint':'8ef16935e5057e1e6497aa2a0c83af828c77d82a','model_reconstructed':True,'designated_smoke_replayed':True,'clean_runtime_rebuild':False,'recovery_level':'Fresh process/model/smoke replay in existing pinned runtime, raw weights reacquired with exactSHA and small metadata restored from immutable private checkpoint','outputs':metrics,'model_tensor_content_sha256':y['model_tensor_content_sha256']};save(C/'PILOT_FRESH_MODEL_REPLAY.json',report);print('FRESH_PROCESS_PILOT_REPLAY_PASS',max(v['max_abs_residual'] for v in metrics.values()))
