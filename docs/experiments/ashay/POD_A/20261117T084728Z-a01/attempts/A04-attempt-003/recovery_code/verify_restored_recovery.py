"""CPU-only recovery verification through restored code and explicit immutable inherited dependencies."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np

def run(root,dependency):
 root=Path(root);dependency=Path(dependency);sys.path.insert(0,str(root/'artifacts/code'));from qualification_contract import componentwise,independent_cross_entropy,validate_manifest,check_real_population,require,LAYERS,sha
 C=root/'control';preserved=json.loads((C/'PRESERVED_WORK_INDEX.json').read_text());prior=preserved['prior_private_checkpoint'];require(sha(dependency/'MEMBER_MANIFEST.json')==prior['member_manifest_sha256'],'Inherited pinned member manifest differs');fixture=dependency/'dependencies/training-only/training_smoke_manifest.jsonl';rows=validate_manifest(fixture);index={r['id']:r for r in preserved['units']};units={};verified_files=0
 for variant in ['logical8','repeat8']:
  old=index['R1/'+variant];identity=json.loads((C/'RUN_CONFIG.json').read_text());rel=Path(old['receipt']).relative_to(Path(identity['prior_A04_artifacts']));p=dependency/'artifacts'/rel;require(sha(p)==old['receipt_sha256'],'Preserved unit receipt differs');d=json.loads(p.read_text());require(d['qualification_identity']==old['qualification_identity'],'Preserved qualification identity differs')
  for e in d['files']:require(sha(p.parent/e['path'])==e['sha256'],'Inherited sealed file differs');verified_files+=1
  data=np.load(p.parent/'features_and_lm.npz',allow_pickle=False);check_real_population(data['ids'],[r['id'] for r in rows],{k:data[k] for k in LAYERS},data['nll_sum'],data['n_tokens'],data['lengths']);require(data['ids'].tolist()==[r['id'] for r in rows],'Frozen row order differs');require(np.array_equal(data['lengths'],np.array([len(r['sequence']) for r in rows])) and np.array_equal(data['n_tokens'],data['lengths']-1),'Causal target count differs');units[variant]=(data,p.parent)
 reference,refroot=units['logical8'];repeat,_=units['repeat8'];checks=[]
 for key in ['ids','task','split','labels','groups','sequence_sha256','lengths','n_tokens']:require(np.array_equal(reference[key],repeat[key]),'Exact discrete metadata mismatch: '+key)
 source_sides=json.loads((C/'PAYLOAD_RECOVERY_INDEX.json').read_text())['assets']
 for e in source_sides:require(sha(e['fresh_path'])==e['sha256'] and Path(e['fresh_path']).stat().st_size==e['bytes'],'Freshsidecar dependency differs')
 for key in LAYERS+['nll_sum']:
  a=componentwise(reference[key],repeat[key]);b=componentwise(repeat[key],reference[key]);require(a['status']==b['status']=='PASS','Reused repeat comparison failed');checks.append({'kind':'reused_R1_fresh_process_repeat','array':key,**a,'reverse_status':b['status']})
 old_runtime=json.loads((C/'INHERITED_RUNTIME_INPUTS.json').read_text());h=next(e for e in old_runtime['anchor_families'] if e['role']=='R1' and e['variant']=='b8');anchor=dependency/'dependencies/training-only'/Path(h['bundle_path']).name;require(sha(anchor)==h['bundle_sha256'],'Inherited anchor hash differs');historical=np.load(anchor,allow_pickle=False)
 for key in LAYERS+['nll_sum']:
  a=componentwise(historical[key],reference[key]);b=componentwise(reference[key],historical[key]);require(a['status']==b['status']=='PASS','Reused historical comparison failed');checks.append({'kind':'reused_R1_same_checkpoint_historical','array':key,**a,'reverse_status':b['status']})
 witness=np.load(refroot/'actual_logits_witness.npz',allow_pickle=False);lm=[]
 for i,row in enumerate(rows):
  pre='row'+str(i);positions=witness[pre+'_positions'];expected=np.arange(len(row['sequence'])-1) if i in [0,11] else np.arange(min(4,len(row['sequence'])-1));require(np.array_equal(positions,expected),'Witness selection changed');targets=np.array([ord(row['sequence'][int(p)+1]) for p in positions]);require(np.array_equal(targets,witness[pre+'_targets']),'Actual causal targets differ');loss=independent_cross_entropy(witness[pre+'_logits'],targets);check=componentwise(loss,witness[pre+'_production_losses']);require(check['status']=='PASS','Independent actual-logit CE failed');entry={'row':i,'positions':len(positions),'all_valid_targets':i in [0,11],**check}
  if i in [0,11]:entry['full_row_sum']=componentwise(np.array([loss.sum(dtype=np.float64)]),reference['nll_sum'][i:i+1]);require(entry['full_row_sum']['status']=='PASS','Fullrow CE sum failed')
  lm.append(entry)
 require('torch' not in sys.modules,'CPU recovery must not import GPU runtime');return {'schema':'pod-a-a04-restored-recovery-CPU-v1','status':'PASS','scope':'Restored newcode/mapping verifies representative inherited R1 repeat+historical features/LM and actual-logit witnesses. Original successful units remain reused, not new qualification.','inherited_member_manifest_sha256':prior['member_manifest_sha256'],'inherited_unit_files_verified':verified_files,'comparison_rows':len(checks),'feature_coordinates':sum(r['denominator'] for r in checks if r['array']!='nll_sum'),'LM_sums':sum(r['denominator'] for r in checks if r['array']=='nll_sum'),'actual_logit_witness_rows':len(lm),'full_row_sum_checks':sum('full_row_sum' in r for r in lm),'checks':checks,'LM_witness_checks':lm,'GPU_runs':0,'new_qualification_variants':0,'new_scientific_measurements':0,'new_fitted_heads':0,'numpy_version':np.__version__,'torch_loaded':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--inherited-dependency',required=True);a=p.parse_args();print(json.dumps(run(a.root,a.inherited_dependency),allow_nan=False))
