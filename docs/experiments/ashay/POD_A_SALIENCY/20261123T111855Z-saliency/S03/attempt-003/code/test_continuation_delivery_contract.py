import unittest,json,hashlib
from pathlib import Path
from ops import C,A,R
from continuation_delivery_contract import validate_release
P=R/'docs/experiments/ashay/POD_A_SALIENCY/20261123T111855Z-saliency/S03/attempt-003'
class MixedSourceMirrorRelease(unittest.TestCase):
 def setUp(self):
  self.m=json.loads((P/'QUALIFICATION_MATRIX.json').read_text());self.p=json.loads((P/'PAYLOAD_IDENTITIES.json').read_text());self.proof=json.loads((P/'MODEL_CONTENT_IDENTITIES.json').read_text());self.h=json.loads((C/'MIRROR_HANDOFF.json').read_text());self.priv={r['alias']:True for r in self.h};self.old=hashlib.sha256((C.with_name('attempt-001')/'SOURCE_IDENTITY.json').read_bytes()).hexdigest();self.new=hashlib.sha256((C/'SOURCE_IDENTITY.json').read_bytes()).hexdigest();self.env=hashlib.sha256((C/'ENVIRONMENT_LOCK.json').read_bytes()).hexdigest()
 def check(self):return validate_release(self.m,self.p,self.proof,self.h,self.priv,self.old,self.new,self.env)
 def test_actual_release(self):self.check()
 def test_swapped_HF_revision_bindings(self):
  p=self.p['payloads'][0];p['payload_revision'],p['receipt_revision']=p['receipt_revision'],p['payload_revision']
  with self.assertRaises(ValueError):self.check()
 def test_reused_unit_cannot_be_relabelled_current_source(self):
  next(u for u in self.m['units'] if u['reused'])['actual_source_identity_sha256']=self.new
  with self.assertRaises(ValueError):self.check()
 def test_full_release_requires_private_CPU_replay(self):
  self.priv['candidate_09']=False
  with self.assertRaises(ValueError):self.check()
 def test_missing_new_variant_despite_claimed_counts(self):
  self.m['units']=[u for u in self.m['units'] if not (u['alias']=='candidate_08' and u['variant']=='repeat8')]
  with self.assertRaises(ValueError):self.check()
 def test_raw_shard_difference_not_effective_model_proof(self):
  self.proof['unique_reconstructed_parameter_contents']=9;self.proof['all9_same_tensor_layout_and_transform']=False
  with self.assertRaises(ValueError):self.check()
if __name__=='__main__':unittest.main()
