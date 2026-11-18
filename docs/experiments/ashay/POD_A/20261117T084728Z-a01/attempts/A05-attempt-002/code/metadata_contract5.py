"""Planning-only identity and key contracts. No prediction or effect calculation."""
from pathlib import Path
import io,json,hashlib,zipfile
METADATA_FIELDS=['ids','labels','groups','sequence_sha256','classes','lengths']
def canonical_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def metadata_only(path,fields=None):
 import numpy as np
 selected=METADATA_FIELDS if fields is None else fields
 if not set(selected)<=set(METADATA_FIELDS):raise ValueError('Scientific prediction/feature/loss array access forbidden in A05')
 result={};members=[]
 with zipfile.ZipFile(path) as z:
  members=z.namelist()
  if len(members)!=len(set(members)):raise ValueError('Duplicate metadata archive member')
  for name in selected:
   key=name+'.npy'
   if key not in members:continue
   info=z.getinfo(key)
   if info.file_size>8*1024**2:raise ValueError('Unbounded identity metadata')
   raw=z.read(key);values=np.lib.format.read_array(io.BytesIO(raw),allow_pickle=False)
   if values.ndim!=1:raise ValueError('Identity metadata must be ordered one-dimensional arrays')
   result[name]={'canonical_value_sha256':canonical_sha(values.tolist()),'raw_NPY_sha256':hashlib.sha256(raw).hexdigest(),'shape':list(values.shape),'dtype':str(values.dtype)}
   if name=='classes':result[name]['values']=values.tolist()
   if name=='groups':result[name]['unique_groups']=len(set(values.tolist()))
 for required in ['ids','labels','groups','sequence_sha256']:
  if required not in result:raise ValueError('Missing required identity metadata: '+required)
 count=result['ids']['shape'][0]
 if any(result[k]['shape']!=[count] for k in ['labels','groups','sequence_sha256']):raise ValueError('Identity row-count mismatch')
 return {'rows':count,'fields':result,'available_member_names_only':members,'metadata_only':True,'probability_feature_loss_values_read':False}
def pair_identity(target,reference,require_classes=True):
 fields=['ids','labels','groups','sequence_sha256']+(['classes'] if require_classes else [])
 for name in fields:
  if name not in target['fields'] or name not in reference['fields'] or target['fields'][name]['canonical_value_sha256']!=reference['fields'][name]['canonical_value_sha256']:raise ValueError('Unmatched ordered identity: '+name)
 if target['rows']!=reference['rows']:raise ValueError('Row intersection/reduction forbidden')
 return True
def validate_design(tasks,hooks,seeds,policies):
 expected=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];rh=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm']
 if tasks!=expected or hooks!=rh or seeds!=[42,17,1234] or policies!=['independent_refit','fixed_original_base']:raise ValueError('Changed task/hook/seed/policy universe')
def h3_gate(gate):
 required=['direct_A06_approval','production_adapter_qualified','H3_features_sealed','H3_78_heads_complete','H3_78_fixed_applications_complete','H3_all_unit_independent_audit_PASS','H3_six_refit_checks_PASS','H3_LM_PASS','H3_private_fresh_recovery_PASS']
 if any(gate.get(k) is not True for k in required):raise ValueError('Other-five scheduling before complete technical H3 PASS forbidden')
 return True
def unique_keys(rows,fields):
 keys=[tuple(r[k] for k in fields) for r in rows]
 if len(keys)!=len(set(keys)):raise ValueError('Duplicate logical unit key')
 return keys
def validate_original_file(path,expected_size,expected_sha):
 p=Path(path)
 if p.is_symlink() or p.stat().st_size!=expected_size:raise ValueError('Stale/unsafe metadata seal')
 with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
 if actual!=expected_sha:raise ValueError('Changed metadata manifest/digest')
 return True
def validate_approval(record,expected):
 for field in ['prompt_commit','attempt_id','A05_sha256']:
  if record.get(field)!=expected[field]:raise ValueError('Replayed or mismatched direct approval: '+field)
 if not record.get('direct_user_message') or expected['prompt_commit'] not in record['direct_user_message'] or 'A05' not in record['direct_user_message']:raise ValueError('Missing bound direct user approval')
 return True
def validate_unit(spec,expected):
 for field in ['model_content_sha256','cohort_sha256','ordered_identity_sha256','classes','policy','draw_sha256','manifest_sha256','coverage_plan_sha256']:
  if spec.get(field)!=expected[field]:raise ValueError('Wrong/stale unit identity: '+field)
 if spec.get('producer_status')!='COMPLETE_UNVERIFIED':raise ValueError('Incomplete unit or producer/release status conflated')
 if spec.get('candidate')=='R2':raise ValueError('Unadmitted R2')
 return True
def r3_eligibility(evidence):
 required=['native_config_tokenizer_identity','historical_source_runtime_hook_semantics','TRAIN_bridge','ordered_cohort_classes','saved_fold','original_base_head','saved_draws','historical_independent_release']
 return 'ELIGIBLE_FOR_SAVED_OUTPUT_COMPARISON' if all(evidence.get(k) is True for k in required) else 'NEEDS_SPECIFIC_REPAIR'
