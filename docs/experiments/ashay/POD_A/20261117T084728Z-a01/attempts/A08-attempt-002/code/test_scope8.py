import unittest,io,tarfile,tempfile
from pathlib import Path
from unittest.mock import patch
import audit_common as ac
from archive8 import safe_extract

class ScopeTests(unittest.TestCase):
 def test_finite390_and_frozen30(self):
  j=ac.read(ac.C/'A08_EXECUTION_MANIFEST.json');self.assertEqual(len(j['audit_units']),390);self.assertEqual(sum(u['sampled_refit_required'] for u in j['audit_units']),30);self.assertTrue(all(u['candidate']=='R5' and u['task'] in ac.TASKS for u in j['audit_units']));self.assertEqual(ac.unit_spec('R5/gue_tf_0/final_norm/seed42')['seed'],42)
 def test_wrong_candidate_H3_unknown_seed(self):
  for uid in ['R4/gue_tf_0/final_norm/seed42','R6/gue_tf_0/final_norm/seed42','R5/emp_H3/final_norm/seed42','R5/gue_tf_0/final_norm/seed43']:
   with self.assertRaises(ValueError):ac.unit_spec(uid)
 def test_wrong_pin_and_plan(self):
  for key in ['stage','prompt_commit','coverage_plan_sha256']:
   with patch.dict(ac.CFG,{key:'invalid'}):
    with self.assertRaises(ValueError):ac.source_check()
 def test_unsafe_real_archive_reader(self):
  for names,kind in [(['root/../escape'],'file'),(['/root/absolute'],'file'),(['root/x','root/x'],'file'),(['root/link'],'symlink'),(['root/hard'],'hardlink'),(['root/./alias'],'file')]:
   with tempfile.TemporaryDirectory(dir=ac.A) as d:
    base=Path(d);p=base/'bad.tar'
    with tarfile.open(p,'w') as tf:
     for name in names:
      t=tarfile.TarInfo(name)
      if kind=='symlink':t.type=tarfile.SYMTYPE;t.linkname='/tmp/escape';tf.addfile(t)
      elif kind=='hardlink':t.type=tarfile.LNKTYPE;t.linkname='root/out';tf.addfile(t)
      else:t.size=1;tf.addfile(t,io.BytesIO(b'x'))
    with self.assertRaises((AssertionError,KeyError)):safe_extract(p,base/'consumer')
 def test_no_H3_or_old_candidate_feature_reads(self):
  for alias,task in [('R5','emp_H3'),('R4','gue_tf_0'),('R6','gue_tf_0')]:
   with self.assertRaises(ValueError):ac.features(alias,task,'dev','final_norm')
if __name__=='__main__':unittest.main()
