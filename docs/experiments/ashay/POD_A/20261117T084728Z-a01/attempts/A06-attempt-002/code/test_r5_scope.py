import unittest,copy,tempfile
from pathlib import Path
from unittest.mock import patch
import scope6
from scope6 import authorize,h3_specs,verify_gate,PLAN,MODEL
from production_contract import put,sha
from lm_records import canonical_input
class ScopeTests(unittest.TestCase):
 def test_exact_R5_and_finite_H3(self):self.assertEqual(len(h3_specs('R5')),78)
 def test_foreign_candidates_fail_before_model(self):
  for c in ['base','R1','R2','R3','R4','R6','R5-copy']:
   with self.assertRaises(ValueError):authorize(c)
 def test_A07_manifest_injection_rejected(self):
  original=scope6.read
  def bad(p):
   j=original(p)
   if Path(p).name=='A06_EXECUTION_MANIFEST.json':j['H3_head_application_units'][0]['task']='gue_tf_0'
   return j
  with patch.object(scope6,'read',side_effect=bad):
   with self.assertRaises(ValueError):h3_specs('R5')
 def test_wrong_stage_or_approval_or_model(self):
  original=scope6.read
  for filename,key,value in [('RUN_CONFIG.json','stage','A07'),('RUN_CONFIG.json','coverage_plan_sha256','0'*64),('APPROVAL_RECORD.json','prompt_commit','old'),('APPROVAL_RECORD.json','direct_user_message','file approval'),('A06_INPUTS.json','checkpoint_identities',{'R5':{'model_tensor_content_sha256':'0'*64}})]:
   def bad(p):
    j=original(p)
    if Path(p).name==filename:j[key]=value
    return j
   with patch.object(scope6,'read',side_effect=bad):
    with self.assertRaises(ValueError):authorize('R5')
 def test_gate_exact_all_components_and_seals(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);deps=[]
   for i in range(3):p=root/str(i);p.write_text('sealed');deps.append({'path':str(p),'sha256':sha(p)})
   gate={'status':'PASS','candidate':'R5','backup_status':'PASS','coverage_plan_sha256':PLAN,'model_content_sha256':MODEL,'components':{k:True for k in ['adapter','features','heads78','applications78','all_unit_audit','six_full_CV_refits','LM','private_fresh_recovery']},'local_dependencies':deps}
   with patch.object(scope6,'C',root):
    put(root/'H3_GATE_R5.json',gate);verify_gate('R5','gue_tf_0',root)
    for k in gate['components']:
     bad=copy.deepcopy(gate);bad['components'][k]=False;put(root/'H3_GATE_R5.json',bad)
     with self.assertRaises(ValueError):verify_gate('R5','gue_tf_0',root)
    put(root/'H3_GATE_R5.json',gate);(root/'0').write_text('corrupted')
    with self.assertRaises(ValueError):verify_gate('R5','gue_tf_0',root)
 def test_typed_LM_provenance_normalization(self):
  historical=canonical_input('RAW_COHORT_MANIFEST','a'*64,'a'*64,'b'*64);modern=canonical_input('EXTRACTION_BUNDLE_RECEIPT','c'*64,'a'*64,'b'*64);self.assertEqual(historical,modern)
  with self.assertRaises(ValueError):canonical_input('RAW_COHORT_MANIFEST','c'*64,'a'*64,'b'*64)
  self.assertNotEqual(modern,canonical_input('EXTRACTION_BUNDLE_RECEIPT','c'*64,'a'*64,'d'*64))
if __name__=='__main__':unittest.main()
