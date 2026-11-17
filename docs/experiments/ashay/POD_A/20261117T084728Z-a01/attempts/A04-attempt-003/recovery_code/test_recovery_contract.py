import copy,hashlib,unittest
from recovery_contract import *
class Checks(unittest.TestCase):
 def fixture(self):
  h=hashlib.sha256(b'PK\x03\x04synthetic').hexdigest();expected={'file_id':'selected','bytes':13,'sha256':h};meta={'id':'selected','size':'13','modified_time':'frozen'};r={'status':'VERIFIED','file_id':'selected','http_status':200,'content_type':'application/octet-stream','bytes':13,'prefix_hex':'504b0304','sha256':h};return r,expected,meta
 def test_complete_positive(self):
  r,e,m=self.fixture();self.assertTrue(payload_gate(r,e,m,m))
 def test_quota_HTML_and_login_rejected(self):
  for field,value in [('status','BLOCKED'),('content_type','text/html'),('http_status',403),('prefix_hex','3c68746d')]:
   r,e,m=self.fixture();r[field]=value
   with self.assertRaises(ValueError):payload_gate(r,e,m,m)
 def test_wrong_size_identity_and_historical_hash_rejected(self):
  for field,value in [('file_id','replacement'),('bytes',12),('sha256','0'*64)]:
   r,e,m=self.fixture();r[field]=value
   with self.assertRaises(ValueError):payload_gate(r,e,m,m)
 def test_source_change_rejected(self):
  r,e,m=self.fixture();post=dict(m,modified_time='changed')
  with self.assertRaises(ValueError):payload_gate(r,e,m,post)
 def test_valid_resume(self):
  s={'file_id':'selected','strong_etag':'pinned'};self.assertTrue(resume_gate(5,206,'bytes 5-12/13',s,s,13))
 def test_range_200_bad_offsets_changed_identity_rejected(self):
  s={'strong_etag':'pinned'}
  for status,rg,now in [(200,None,s),(206,'bytes 4-12/13',s),(206,'bytes 5-12/14',s),(206,'bytes 5-12/13',{'strong_etag':'changed'})]:
   with self.assertRaises(ValueError):resume_gate(5,status,rg,s,now,13)
  with self.assertRaises(ValueError):resume_gate(5,206,'bytes 5-12/13',{}, {},13)
 def test_changed_qualification_identity_rejected(self):
  expected={'candidate_id':'selected','manifest_sha256':'frozen','runtime_sha256':'same','source_sha256':'same','physical_batch':8};self.assertTrue(identity_gate(expected,expected))
  for k in expected:
   changed=dict(expected);changed[k]=1
   with self.assertRaises(ValueError):identity_gate(changed,expected)
 def test_restore_paths_rejected(self):
  self.assertEqual(owned_relative('R3/metadata.json'),'R3/metadata.json')
  for p in ['/tmp/foreign','../../escape','']:
   with self.assertRaises(ValueError):owned_relative(p)
if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));raise SystemExit(not result.wasSuccessful())
