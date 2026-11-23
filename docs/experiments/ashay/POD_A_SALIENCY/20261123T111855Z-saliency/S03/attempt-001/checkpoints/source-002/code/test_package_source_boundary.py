import unittest,tempfile,json,hashlib
from pathlib import Path
from s03_entry_guard import verify_pinned_package,verify_approved_S03
C=Path('/workspace/pod-a-saliency/control/20261123T111855Z-saliency/S03/attempt-001')
class PackageBoundaryTests(unittest.TestCase):
 def test_external_hash_guard_rejects_corrupt_validator_before_execution(self):
  original=Path(json.loads((C/'PATHS.json').read_text())['package_root']);manifest=json.loads((original/'S_PACKAGE_FILES.json').read_text());self.assertEqual(verify_pinned_package(original),'3b089d6b7d7ab16812272a500519db269050c855f0a0f29e3333752d9a62a5e9')
  with tempfile.TemporaryDirectory(prefix='s03-package-boundary-',dir=C) as td:
   root=Path(td)
   for name in manifest['files']+['S_PACKAGE_FILES.json','S_SHA256SUMS']:
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((original/name).read_bytes())
   validator=root/'S_validate_package.py';validator.write_bytes(validator.read_bytes()+b'\n# simulated source drift\n')
   with self.assertRaises(ValueError):verify_pinned_package(root)
   lines=(root/'S_SHA256SUMS').read_text().splitlines();newsha=hashlib.sha256(validator.read_bytes()).hexdigest();(root/'S_SHA256SUMS').write_text('\n'.join(newsha+'  S_validate_package.py' if x.endswith('  S_validate_package.py') else x for x in lines)+'\n')
   with self.assertRaises(ValueError):verify_pinned_package(root)
 def test_real_actual_S03_guard_remains_pass_without_dispatch(self):
  self.assertFalse(verify_approved_S03(C,'candidate_01')['dispatch'])
if __name__=='__main__':unittest.main(verbosity=2)
