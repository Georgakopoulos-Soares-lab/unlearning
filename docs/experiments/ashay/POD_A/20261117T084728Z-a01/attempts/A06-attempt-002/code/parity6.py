"""Same R5 physical8/logical8 TRAIN comparisons; no production/model loading."""
from common6 import *
from qualification_contract import componentwise,LAYERS
import numpy as np
def check_pair(observed,reference,label):
 checks=[]
 with np.load(observed,allow_pickle=False) as o,np.load(reference,allow_pickle=False) as r:
  for field in ['ids','labels','groups','sequence_sha256','lengths','n_tokens']:assert np.array_equal(o[field],r[field]),label+' metadata '+field
  assert len(o['ids'])==12 and np.array_equal(o['n_tokens'],o['lengths']-1)
  for key in [*LAYERS,'nll_sum']:
   assert o[key].dtype==np.float32 and np.isfinite(o[key]).all();forward=componentwise(r[key],o[key]);reverse=componentwise(o[key],r[key]);assert forward['status']==reverse['status']=='PASS',(label,key,forward,reverse);checks.append({'comparison':label,'array':key,'status':'PASS','shape':list(o[key].shape),'forward':forward,'reverse':reverse})
 return checks
def main(repeat=False):
 guard();refs=read(C/'TRAIN_QUALIFICATION_REFERENCES.json');r=next(e for e in refs if e['variant']=='logical8');root=Path(r['receipt_path']).parent;first=A/'parity/R5/parity-001';assert read(first/'COMPLETE.json')['source_identity_sha256']==sha(C/'SOURCE_IDENTITY.json')
 for e in read(first/'COMPLETE.json')['files']:assert sha(first/e['path'])==e['sha256']
 report={'status':'PASS_FIRST_COMPARISON','candidate':'R5','source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'CPU_source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'manifest_sha256':read(C/'A06_INPUTS.json')['training_smoke']['sha256'],'physical_batch':8,'logical_batch':8,'atol':1e-4,'rtol':1e-5,'comparisons':check_pair(first/'features_and_lm.npz',root/'features_and_lm.npz','fresh_vs_A04_R5_logical8'),'raw_heldout_inputs_opened':False,'production_forwards':0,'completed_utc':now()}
 if repeat:
  rep=A/'parity/R5/repeat-001';rr=next(e for e in refs if e['variant']=='repeat8');assert read(rep/'COMPLETE.json')['source_identity_sha256']==sha(C/'SOURCE_IDENTITY.json')
  for e in read(rep/'COMPLETE.json')['files']:assert sha(rep/e['path'])==e['sha256']
  report['comparisons']+=check_pair(rep/'features_and_lm.npz',Path(rr['receipt_path']).parent/'features_and_lm.npz','repeat_vs_A04_R5_repeat8')+check_pair(rep/'features_and_lm.npz',first/'features_and_lm.npz','new_repeat_vs_new_first');report.update(status='PASS',new_parity_forwards=4,new_parity_real_rows=24,new_parity_fillers=8,numerical_comparison_rows=len(report['comparisons']),all_26_hooks_and_actual_LM=True,same_corresponding_packing=True)
  put(C/'ADAPTER_PARITY_R5.json',report);put(C/'TRAIN_PARITY.json',report);put(C/'ADAPTER_VALIDATION.json',{'status':'PASS','candidate':'R5','source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'CPU_source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'synthetic_validation_sha256':sha(C/'SYNTHETIC_VALIDATION.json'),'TRAIN_parity_sha256':sha(C/'TRAIN_PARITY.json'),'model_tensor_content_sha256':read(C/'A06_INPUTS.json')['checkpoint_identities']['R5']['model_tensor_content_sha256'],'strict_loaded_values_all_verified':True,'qualification_scope':'Same R5 exact12TRAIN rows, physical8/logical8 first/repeat,81 bidirectional array comparisons. No R3 requalification or production.','probability_reconstruction_tolerance_later':1e-10,'metric_draw_interval_tolerance_later':1e-12,'completed_utc':now()})
  for n in ['ADAPTER_VALIDATION.json','TRAIN_PARITY.json']:publish(n,read(C/n))
 else:put(C/'TRAIN_PARITY_FIRST.json',report)
 print(json.dumps({'status':report['status'],'array_comparisons':len(report['comparisons']),'max_abs':max(e['forward']['max_abs_residual'] for e in report['comparisons'])}))
if __name__=='__main__':main('--repeat' in sys.argv)
