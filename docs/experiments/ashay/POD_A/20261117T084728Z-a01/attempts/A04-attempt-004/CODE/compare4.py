"""CPU-only comparison of sealed A04 qualification arrays; no fitting or model forwards."""
from pathlib import Path
import argparse,json,sys,hashlib,csv
import numpy as np

def run(control,artifacts=None,report=None,anchor_root=None):
 C=Path(control);cfg=json.loads((C/'RUN_CONFIG.json').read_text());A=Path(artifacts or cfg['artifacts']);sys.path.insert(0,str(A/'code'));from qualification_contract import sha,require,componentwise,independent_cross_entropy,validate_manifest,check_real_population,LAYERS,ALIASES,VARIANTS,SMOKE_SHA
 fixture=Path(anchor_root)/'training_smoke_manifest.jsonl' if anchor_root else Path(json.loads((C/'INHERITED_TRAINING_BUNDLE_MANIFEST.json').read_text())['root'])/'training_smoke_manifest.jsonl';frozen=validate_manifest(fixture)
 R=Path(report or C/'numerical-reports');R.mkdir(exist_ok=True,parents=True);rows=[];units={};witness_checks=[];discrete=['ids','task','split','labels','groups','sequence_sha256','lengths','n_tokens'];historical=json.loads((C/'INHERITED_RUNTIME_INPUTS.json').read_text())['anchor_families']
 def comparison(alias,kind,variant,value,reference,identity,reference_sha):
  for key in discrete:require(np.array_equal(value[key],reference[key]),f'{alias}/{kind}/{variant}: discrete mismatch {key}')
  for key in LAYERS+['nll_sum']:
   # Original verifier np.allclose(reference,value): value is second argument.
   primary=componentwise(reference[key],value[key]);reverse=componentwise(value[key],reference[key]);row=dict(alias=alias,kind=kind,variant=variant,array=key,qualification_identity=identity,reference_sha256=reference_sha,**primary,reverse_direction_status=reverse['status'],reverse_direction_violations=reverse['violations']);row['status']='PASS' if primary['status']==reverse['status']=='PASS' else 'FAIL';row['comparison_direction']='Pinned np.allclose(reference,value); also require reverse direction with unchanged tolerances';rows.append(row)
 for alias in ALIASES:
  for variant in VARIANTS:
   dirs=sorted((A/'qualification'/alias/variant).glob('attempt-*/COMPLETE.json'))
   if not dirs:continue
   p=dirs[-1];complete=json.loads(p.read_text());root=p.parent
   for f in complete['files']:require(sha(root/f['path'])==f['sha256'],'Sealed unit changed: '+f['path'])
   identity=complete['identity'];require(identity['manifest_sha256']==SMOKE_SHA,'Wrong smoke manifest');data=np.load(root/'features_and_lm.npz',allow_pickle=False);units[(alias,variant)]=(data,complete,sha(root/'features_and_lm.npz'),root)
   expected={'ids':[r['id'] for r in frozen],'task':[r['task'] for r in frozen],'split':['train']*12,'labels':[r['label'] for r in frozen],'groups':[r['exact_rc_group'] for r in frozen],'sequence_sha256':[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in frozen],'lengths':[len(r['sequence']) for r in frozen]}
   for key,value in expected.items():require(np.array_equal(data[key],np.array(value)),'NPZ frozen manifest identity differs: '+key)
   check_real_population(data['ids'],expected['ids'],{k:data[k] for k in LAYERS},data['nll_sum'],data['n_tokens'],data['lengths'])
   w=np.load(root/'actual_logits_witness.npz',allow_pickle=False)
   for i in range(12):
    pre='row'+str(i);ind=independent_cross_entropy(w[pre+'_logits'],w[pre+'_targets']);check=componentwise(ind,w[pre+'_production_losses']);require(check['status']=='PASS','Restored actual-logit CE failed');take=w[pre+'_positions'];expected=np.arange(int(data['lengths'][i])-1) if i in [0,11] else np.arange(min(4,int(data['lengths'][i])-1));require(np.array_equal(take,expected),'Witness selection changed');witness_checks.append(dict(alias=alias,variant=variant,row=i,**check))
    if i in [0,11]:
     fullsum=componentwise(np.array([ind.sum(dtype=np.float64)]),data['nll_sum'][i:i+1]);require(fullsum['status']=='PASS','Restored fullrow independent CE sum failed');witness_checks[-1]['full_row_sum_comparison']=fullsum
   require(np.array_equal(data['n_tokens'],data['lengths']-1),'Target counts wrong')
   if alias in ['base','R1','R3']:
    h=next(h for h in historical if h['role']==alias and h['variant']=={'logical1':'b1','logical8':'b8','repeat8':'repeat'}[variant]);path=Path(anchor_root)/Path(h['bundle_path']).name if anchor_root else Path(h['bundle_path']);require(sha(path)==h['bundle_sha256'],'Historical anchor changed');old=np.load(path,allow_pickle=False);comparison(alias,'same_checkpoint_historical',variant,data,old,identity['qualification_identity'],h['bundle_sha256'])
 for alias in ALIASES:
  if (alias,'logical8') not in units:continue
  baseline,bcomp,bsha,_=units[(alias,'logical8')]
  for v in ['logical1','repeat8']:
   if (alias,v) in units:
    data,comp,h,_=units[(alias,v)];require(comp['identity']['assets']==bcomp['identity']['assets'],'Same alias content changed');comparison(alias,'batch' if v=='logical1' else 'fresh_process_repeat',v,data,baseline,comp['qualification_identity'],bsha)
 fields=['alias','kind','variant','array','qualification_identity','reference_sha256','status','denominator','violations','max_abs_residual','max_relative_residual_finite','relative_undefined_nonzero_at_reference_zero','worst_index','worst_observed','worst_reference','worst_allowed_abs_error','atol','rtol','comparison_direction','reverse_direction_status','reverse_direction_violations']
 with (R/'SMOKE_COMPARISONS.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 result={'schema':'pod-a-a04-numerical-results-v1','status':'PASS' if rows and all(r['status']=='PASS' for r in rows) else 'FAIL' if rows else 'PENDING','sealed_units':len(units),'comparison_rows':len(rows),'passed':sum(r['status']=='PASS' for r in rows),'failed':sum(r['status']=='FAIL' for r in rows),'feature_coordinates_compared':sum(r['denominator'] for r in rows if r['array']!='nll_sum'),'LM_values_compared':sum(r['denominator'] for r in rows if r['array']=='nll_sum'),'comparison_direction':'Pinned verifier reference,value; require both directions conservatively; no tolerance change','atol':1e-4,'rtol':1e-5,'checks':rows,'actual_logit_CPU_checks':witness_checks,'new_fitted_heads':0,'heldout_forwards':0,'numpy_version':np.__version__,'torch_loaded_in_CPU_verifier':'torch' in sys.modules}
 (R/'SMOKE_RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['checks','actual_logit_CPU_checks']}));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--control',required=True);p.add_argument('--artifacts');p.add_argument('--report');p.add_argument('--anchor-root');a=p.parse_args();run(a.control,a.artifacts,a.report,a.anchor_root)
