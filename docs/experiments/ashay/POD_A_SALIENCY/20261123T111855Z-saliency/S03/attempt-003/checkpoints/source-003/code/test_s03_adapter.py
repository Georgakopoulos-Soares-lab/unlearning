import unittest,json
from pathlib import Path
import numpy as np
from qualification_contract import corpus_likelihood,componentwise,validate_alias
from s03_entry_guard import verify_approved_S03
C=Path('/workspace/pod-a-saliency/control/20261123T111855Z-saliency/S03/attempt-001')
class S03AdapterTests(unittest.TestCase):
 def test_exact_experimental_scope_and_original_reference(self):
  registry=json.loads((C/'ACCEPTED_CHECKPOINT_REGISTRY.json').read_text())['selected_by_stage']
  self.assertEqual(len(registry),10)
  for alias,candidate in registry.items():
   validate_alias(alias,candidate,registry)
   with self.assertRaises(ValueError):validate_alias(alias,'substituted-id',registry)
  with self.assertRaises(ValueError):validate_alias('R4','legacy',{'R4':'legacy'})
 def test_required_perplexity_overflow_preserves_finite_NLL(self):
  nll,ppl,reason=corpus_likelihood(np.array([1000,2000],dtype=np.float32),np.array([1,2]))
  self.assertEqual(nll,1000.0);self.assertIsNone(ppl);self.assertTrue(reason)
 def test_corpus_ratio_not_average_per_row_or_perplexity(self):
  nll,ppl,reason=corpus_likelihood(np.array([4,18],dtype=np.float32),np.array([2,6]))
  self.assertEqual(nll,2.75);self.assertAlmostEqual(ppl,np.exp(2.75));self.assertIsNone(reason)
  with self.assertRaises(ValueError):corpus_likelihood(np.array([1],dtype=np.float32),np.array([0]))
 def test_scaled_elementwise_failure_not_mean_residual(self):
  ref=np.zeros((12,1920),dtype=np.float32);x=ref.copy();x[11,1919]=0.000101
  r=componentwise(x,ref);self.assertEqual(r['status'],'FAIL');self.assertEqual(r['violations'],1);self.assertEqual(r['worst_index'],[11,1919]);self.assertGreater(r['max_scaled_residual'],1.0)
 def test_actual_readonly_approved_guard_and_legacy_rejection(self):
  r=verify_approved_S03(C,'candidate_01');self.assertEqual(r['candidate_id'],'drive-checkpoint:11_zYtoYf9dBSTHuTb5F1o_One48l8Lrw');self.assertFalse(r['dispatch'])
  with self.assertRaises(ValueError):verify_approved_S03(C,'R4')
if __name__=='__main__':unittest.main(verbosity=2)
