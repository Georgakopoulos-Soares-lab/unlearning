import unittest,copy,json,tempfile,hashlib
from pathlib import Path
from s03_delivery_contract import matrix,references,sealed_files
from ops import C,A
class BoundaryCases(unittest.TestCase):
 def setUp(self):
  self.m=json.loads((C/'FINAL_MATRIX_DRAFT.json').read_text());self.ids=[r['candidate_id'] for r in self.m['candidates']];self.h=json.loads((C/'SAVED_REFERENCE_QUALIFICATION.json').read_text());self.original=json.loads((A/'historical-runtime-metadata-2.json').read_text())['references']
 def test_real_data_passes(self):matrix(self.m,self.ids);references(self.h,self.original)
 def test_duplicate_discovery_rejected(self):
  self.m['candidates'][8]=copy.deepcopy(self.m['candidates'][0])
  with self.assertRaises(ValueError):matrix(self.m,self.ids)
 def test_unloaded_payload_cannot_pass(self):
  self.m['candidates'][3]['S04_eligible']=True
  with self.assertRaises(ValueError):matrix(self.m,self.ids)
 def test_route_or_bytes_only_not_model_recovery(self):
  self.m['candidates'][0]['fresh_process_model_replay']='NOT_RUN'
  with self.assertRaises(ValueError):matrix(self.m,self.ids)
 def test_tolerance_change_rejected(self):
  self.m['candidates'][0]['GPU_atol']=1e-2
  with self.assertRaises(ValueError):matrix(self.m,self.ids)
 def test_parent_fabrication_rejected(self):
  self.m['candidates'][0]['immediate_parent_identity']='original-base-guessed'
  with self.assertRaises(ValueError):matrix(self.m,self.ids)
 def test_head_substitution_rejected(self):
  self.h['references'][0]['head_sha256']=self.h['references'][1]['head_sha256']
  with self.assertRaises(ValueError):references(self.h,self.original)
 def test_probability_class_order_rejected(self):
  self.h['references'][0]['class_order']=[1,0]
  with self.assertRaises(ValueError):references(self.h,self.original)
 def test_same_size_corruption_rejected(self):
  with tempfile.TemporaryDirectory(dir=C) as d:
   p=Path(d)/'receipt.json';p.write_bytes(b'12');good=hashlib.sha256(b'12').hexdigest();sealed_files(d,{'receipt.json':good});p.write_bytes(b'21')
   with self.assertRaises(ValueError):sealed_files(d,{'receipt.json':good})
if __name__=='__main__':unittest.main()
