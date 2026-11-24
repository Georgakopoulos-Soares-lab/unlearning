import unittest,json,copy
from pathlib import Path
from s03_entry_guard import validate_continuation_paths
C=Path('/workspace/pod-a-saliency/control/20261123T111855Z-saliency/S03/attempt-003')
class ContinuationGuard(unittest.TestCase):
 def setUp(self):self.cfg=json.loads((C/'RUN_CONFIG.json').read_text());self.state={'run_id':'20261123T111855Z-saliency'}
 def test_actual_valid_scope(self):self.assertTrue(validate_continuation_paths(C,self.cfg,self.state))
 def test_old_attempt_denied(self):
  self.cfg['attempt_id']='attempt-001'
  with self.assertRaises(ValueError):validate_continuation_paths(C,self.cfg,self.state)
 def test_wrong_control_denied(self):
  with self.assertRaises(ValueError):validate_continuation_paths(C.with_name('attempt-002'),self.cfg,self.state)
 def test_wrong_artifact_root_denied(self):
  self.cfg['artifacts']='/workspace/unrelated'
  with self.assertRaises(ValueError):validate_continuation_paths(C,self.cfg,self.state)
 def test_runtime_substitution_denied(self):
  self.cfg['runtime_venv']='/usr/local'
  with self.assertRaises(ValueError):validate_continuation_paths(C,self.cfg,self.state)
 def test_changed_prompt_denied(self):
  self.cfg['mirror_prompt_sha256']='0'*64
  with self.assertRaises(ValueError):validate_continuation_paths(C,self.cfg,self.state)
 def test_changed_run_denied(self):
  self.state['run_id']='another-run'
  with self.assertRaises(ValueError):validate_continuation_paths(C,self.cfg,self.state)
if __name__=='__main__':unittest.main()
