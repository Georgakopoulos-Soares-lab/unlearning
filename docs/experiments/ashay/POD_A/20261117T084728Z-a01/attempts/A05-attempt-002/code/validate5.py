"""Meaningful synthetic identity/authority failures and finite plan verification."""
from common5 import *
from metadata_contract5 import *
from keys5 import coverage_rows,table_keys,csv_bytes,compressed_keys
from collections import Counter
import copy,tempfile,zipfile,io,time,tarfile
from restore5 import safe_members
def main():
 start=time.monotonic();guard();tests=[]
 def reject(name,call):
  try:call()
  except (ValueError,AssertionError,KeyError):tests.append({'case':name,'status':'PASS_REJECTED'});return
  raise AssertionError('Negative case accepted: '+name)
 def check(name,value):
  assert value,name;tests.append({'case':name,'status':'PASS'})
 original=read(D50/'PROTOCOL_FROZEN.json');design=read(D/'TABLE_KEY_DESIGN.json');plan=read(D/'COVERAGE_PLAN.json');h=sha(D/'COVERAGE_PLAN.json');ex=read(D/'R5_EXECUTION_MANIFEST.json');audit=read(D/'AUDIT_PLAN.json');expected=read(D/'EXPECTED_TABLE_KEYS.json')
 check('direct approval exact new attempt/prompt bytes',validate_approval(read(C/'APPROVAL_RECORD.json'),{'prompt_commit':cfg['prompt_commit'],'attempt_id':cfg['attempt_id'],'A05_sha256':cfg['A05_prompt_sha256']}))
 for field in ['prompt_commit','attempt_id','A05_sha256']:
  bad=read(C/'APPROVAL_RECORD.json');bad[field]='old/replayed';reject('replayed approval '+field,lambda b=bad:validate_approval(b,{'prompt_commit':cfg['prompt_commit'],'attempt_id':cfg['attempt_id'],'A05_sha256':cfg['A05_prompt_sha256']}))
 good={'candidate':'R5','model_content_sha256':plan['R5_model_identity']['model_tensor_content_sha256'],'cohort_sha256':original['cohorts']['H3'],'ordered_identity_sha256':'a'*64,'classes':[0,1],'policy':'independent_refit','draw_sha256':'b'*64,'manifest_sha256':'c'*64,'coverage_plan_sha256':h,'producer_status':'COMPLETE_UNVERIFIED'};check('exact complete identity accepted without release claim',validate_unit(good,good))
 for field,badvalue in [('model_content_sha256','0'*64),('cohort_sha256','0'*64),('ordered_identity_sha256','0'*64),('classes',[1,0]),('policy','refit_base_again'),('draw_sha256','0'*64),('manifest_sha256','0'*64),('coverage_plan_sha256','0'*64),('producer_status','PARTIAL'),('candidate','R2')]:
  bad={**good,field:badvalue};reject('wrong/incomplete '+field,lambda b=bad:validate_unit(b,good))
 reject('extra task',lambda:validate_design(TASKS+['new'],HOOKS,SEEDS,POLICIES));reject('extra seed',lambda:validate_design(TASKS,HOOKS,SEEDS+[9],POLICIES));reject('changed policy',lambda:validate_design(TASKS,HOOKS,SEEDS,['independent_refit','renormalized']))
 for path in [str(D3.relative_to(W))+'/result.json',str(D.relative_to(W))+'/../A03-attempt-001/x',str(D/'x'),str(D.relative_to(W))+'//x']:
  check('historical/unsafe write rejected '+path,not owned(path))
 gate={k:True for k in plan['other_five_gate_required']};check('complete technical gate accepted',h3_gate(gate))
 for field in gate:reject('other-five gate missing '+field,lambda k=field:h3_gate({**gate,k:False}))
 evidence={k:True for k in ['native_config_tokenizer_identity','historical_source_runtime_hook_semantics','TRAIN_bridge','ordered_cohort_classes','saved_fold','original_base_head','saved_draws','historical_independent_release']};check('R3 all domain evidence eligible',r3_eligibility(evidence)=='ELIGIBLE_FOR_SAVED_OUTPUT_COMPARISON')
 check('R3 TRAIN bridge alone insufficient',r3_eligibility({'TRAIN_bridge':True})=='NEEDS_SPECIFIC_REPAIR')
 for field in evidence:check('failed R3 dependency '+field,r3_eligibility({**evidence,field:False})=='NEEDS_SPECIFIC_REPAIR')
 # Synthetic identity fields only. Probability member intentionally invalid bytes:
 # success proves the metadata reader never deserializes it.
 import numpy as np
 with tempfile.TemporaryDirectory(prefix='a05-metadata-tests-',dir=A) as tmp:
  tmp=Path(tmp);npz=tmp/'synthetic.npz';s=io.BytesIO();np.savez(s,ids=np.array(['x','y']),labels=np.array([0,1]),groups=np.array(['g1','g2']),sequence_sha256=np.array(['a','b']),classes=np.array([0,1]));npz.write_bytes(s.getvalue())
  with zipfile.ZipFile(npz,'a') as z:z.writestr('prob_new_refit.npy',b'NOT_A_NUMPY_ARRAY_MUST_NOT_BE_READ')
  m=metadata_only(npz);check('forbidden probability member untouched',m['rows']==2 and m['probability_feature_loss_values_read'] is False);reject('explicit scientific-array read blocked',lambda:metadata_only(npz,['prob_new_refit']));check('exact metadata pair passes',pair_identity(m,m))
  for field in ['ids','labels','groups','sequence_sha256','classes']:
   bad=copy.deepcopy(m);bad['fields'][field]['canonical_value_sha256']='0'*64;reject('metadata mismatch '+field,lambda b=bad:pair_identity(m,b))
  bad=copy.deepcopy(m);bad['rows']=1;reject('silent row intersection',lambda:pair_identity(m,bad));refhash=sha(npz);reject('stale seal wrong digest',lambda:validate_original_file(npz,npz.stat().st_size,'0'*64));check('valid metadata seal',validate_original_file(npz,npz.stat().st_size,refhash));npz.write_bytes(npz.read_bytes()+b'corrupt');reject('corruption/stale size',lambda:validate_original_file(npz,npz.stat().st_size-7,refhash))
 rows=coverage_rows();check('full exact6637 coverage set',len(rows)==6637);check('R2 missing943',Counter(r['status'] for r in rows)['MISSING_R2']==943);check('R5 proposed943',Counter(r['status'] for r in rows)['PROPOSED_R5']==943);check('old4751 preserved',Counter(r['status'] for r in rows)['REUSED_RELEASED']==4751);unique_keys(rows,['unit_id']);reject('duplicate unit',lambda:unique_keys(rows+[rows[0]],['unit_id']))
 keys=table_keys(design,h);unique_keys(keys,['logical_id']);check('exact33684 derived table keys',len(keys)==33684);check('deterministic canonical compressed table',compressed_keys(keys)==(D/'EXPECTED_TABLE_KEYS.csv.gz').read_bytes());check('expected table byte sha',bh(csv_bytes(keys))==expected['uncompressed_sha256']);check('exact5460 marginal rows',sum(r['table_kind']=='classifier_marginal' for r in keys)==5460);check('exact28140 paired classifier rows',sum(r['table_kind']=='classifier_paired' for r in keys)==28140);check('LM14 points70pairs no layerseed',Counter(r['table_kind'] for r in keys)['LM_marginal']==14 and Counter(r['table_kind'] for r in keys)['LM_paired']==70 and all(r['representation']=='N/A' and r['CV_seed']=='N/A' for r in keys if r['table_kind'].startswith('LM')))
 check('13 bundles22645rows89chunks2833forwards19fillers',len(ex['bundles'])==13 and sum(e['rows'] for e in ex['bundles'])==22645 and sum(e['chunks'] for e in ex['bundles'])==89 and sum(e['physical_forwards'] for e in ex['bundles'])==2833 and sum(e['fillers_excluded'] for e in ex['bundles'])==19);check('468 frozen heads7020 initialsolvercalls',len(ex['head_application_units'])==468 and sum(e['initial_CV_plus_final_optimizer_fits'] for e in ex['head_application_units'])==7020);check('predeclared36 fullCV audits540initialcalls',len(audit['prospective_refit_panel'])==36 and sum(e['initial_optimizer_fits'] for e in audit['prospective_refit_panel'])==540);check('no old scientific import',not any(k in sys.modules for k in ['torch','joblib','sklearn','bionemo','megatron']));check('source metric AP canonical average_precision',original['metrics']==METRICS)
 continuity=read(D/'PROTOCOL_CONTINUITY.json');science={k:original[k] for k in continuity['frozen_settings']};science=json.loads(json.dumps(science));science['runtime'].pop('qualified_checkpoint_metadata');check('scientific continuity independent subset reconstruction',digest(science)==continuity['effective_scientific_subset_sha256']==continuity['original_scientific_subset_sha256']);check('original hashes unchanged',sha(D50/'PROTOCOL_FROZEN.json')=='73648f333dd619b2305a5bf22ff185292addc9071c7aa9de5188c23f9e2c1cf7' and sha(D50/'COVERAGE_PLAN.json')=='0845be199a96d3bdcfa4d7ac990263120f8a43c506e499b2d69f22c7b59c3eb4')
 for path in (A/'code').glob('*.py'):compile(path.read_bytes(),str(path),'exec')
 def testtar(entries,manifest):
  s=io.BytesIO()
  with tarfile.open(fileobj=s,mode='w') as tf:
   for name,data,kind in entries+([('root/MEMBER_MANIFEST.json',json.dumps(manifest).encode(),'file')] if manifest is not None else []):
    t=tarfile.TarInfo(name);t.size=len(data)
    if kind=='link':t.type=tarfile.SYMTYPE;t.linkname='/etc/passwd';t.size=0
    tf.addfile(t,io.BytesIO(data) if kind=='file' else None)
  s.seek(0)
  with tarfile.open(fileobj=s) as tf:return safe_members(tf)
 manifest={'files':[{'path':'ok.json','bytes':2,'sha256':bh(b'{}')}]};check('safe exact archive accepted',testtar([('root/ok.json',b'{}','file')],manifest)[0]=='root')
 reject('archive traversal',lambda:testtar([('root/../evil',b'x','file')],manifest));reject('archive symlink',lambda:testtar([('root/evil',b'','link')],manifest));reject('archive duplicate',lambda:testtar([('root/ok.json',b'{}','file'),('root/ok.json',b'{}','file')],manifest));reject('archive missing member',lambda:testtar([],manifest));reject('archive corrupt member',lambda:testtar([('root/ok.json',b'[]','file')],manifest));reject('archive extra member',lambda:testtar([('root/ok.json',b'{}','file'),('root/extra',b'x','file')],manifest))
 publish('PLAN_VALIDATION.json',{'status':'PASS','test_count':len(tests),'cases':tests,'scope':'Synthetic/metadata identity, authority, safety gates, deterministic finite key enumeration and scientific continuity; zero scientific computation','coverage_plan_sha256':h,'new_scientific_measurements':0,'wall_seconds':time.monotonic()-start,'legacy_validator':read(C/'LEGACY_FORMAT_VALIDATOR.json')})
 for name in ['common5.py','metadata_contract5.py','keys5.py','validate5.py','restore5.py']:publish('code/'+name,(A/'code'/name).read_bytes())
 print(json.dumps({'status':'PASS','checks':len(tests),'coverage_plan_sha256':h}))
if __name__=='__main__':main()
