from asset_contract4 import *
import unittest,tempfile
class Checks(unittest.TestCase):
 def test_exact_eight_native_asset_paths(self):
  self.assertEqual(runtime_relative('tokenizer/tokenizer.json'),'tokenizer.json');self.assertEqual(runtime_relative('__0_0.distcp'),'__0_0.distcp')
 def test_unsafe_or_unselected_asset_rejected(self):
  for p in ['/tmp/payload','../weights','tokenizer/../config','tokenizer//tokenizer.json','tokenizer\\tokenizer.json','weights.pt']:
   with self.assertRaises(ValueError):runtime_relative(p)
 def test_mutable_or_short_revision_rejected(self):
  for r in ['main','POD_A','a64008e','A'*40,'0'*39]:
   with self.assertRaises(ValueError):immutable_revision(r)
  self.assertEqual(immutable_revision('a'*40),'a'*40)
 def test_exact_file_and_both_digests(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'file';p.write_bytes(b'qualified exact bytes');b=p.read_bytes();self.assertEqual(verify_file(p,len(b),hashlib.sha256(b).hexdigest(),hashlib.md5(b).hexdigest())['bytes'],len(b))
 def test_corruption_and_size_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'file';p.write_bytes(b'good')
   for size,h in [(5,hashlib.sha256(b'good').hexdigest()),(4,hashlib.sha256(b'evil').hexdigest())]:
    with self.assertRaises(ValueError):verify_file(p,size,h)
 def test_provider_digest_mismatch_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'file';p.write_bytes(b'good')
   with self.assertRaises(ValueError):verify_file(p,4,hashlib.sha256(b'good').hexdigest(),'0'*32)
 def test_symlink_asset_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'file';p.write_bytes(b'good');q=Path(d)/'alias';q.symlink_to(p)
   with self.assertRaises(ValueError):verify_file(q,4,hashlib.sha256(b'good').hexdigest())
if __name__=='__main__':unittest.main(verbosity=2)
