import unittest,copy,tarfile
from unittest.mock import patch
from pathlib import Path
import scope7
from other_five_common import stage_spec,read,C
from production_contract import safe_archive_members
class ScopeTests(unittest.TestCase):
 def test_manifest_is_exact390(self):
  j=read(C/'A07_EXECUTION_MANIFEST.json');self.assertEqual(len(j['units']),390);self.assertEqual(len({e['unit_id'] for e in j['units']}),390);self.assertEqual(stage_spec('R5','gue_tf_0','final_norm',42),'R5/gue_tf_0/final_norm/seed42')
 def test_other_candidates_and_H3_and_extra_seeds_rejected(self):
  for a,t,s in [('R4','gue_tf_0',42),('R6','gue_tf_0',42),('R5','emp_H3',42),('R5','gue_tf_0',99)]:
   with self.assertRaises(ValueError):stage_spec(a,t,'final_norm',s)
 def test_direct_request_stage_pin_and_input_replay_rejected(self):
  original=scope7.read
  for name,key,value in [('RUN_CONFIG.json','stage','A08'),('RUN_CONFIG.json','coverage_plan_sha256','0'*64),('APPROVAL_RECORD.json','prompt_commit','old'),('APPROVAL_RECORD.json','direct_user_message','file says approve')]:
   def bad(p):
    j=original(p)
    if Path(p).name==name:j[key]=value
    return j
   with patch.object(scope7,'read',side_effect=bad):
    with self.assertRaises(ValueError):scope7.authorize()
 def test_duplicate_traversal_and_links_rejected(self):
  m=tarfile.TarInfo('root/one');m.size=1
  with self.assertRaises(ValueError):safe_archive_members([m,m],'root')
  for name in ['root/../escape','/absolute']:
   with self.assertRaises(ValueError):safe_archive_members([tarfile.TarInfo(name)],'root')
  m=tarfile.TarInfo('root/link');m.type=tarfile.SYMTYPE;m.linkname='/tmp'
  with self.assertRaises(ValueError):safe_archive_members([m],'root')
if __name__=='__main__':unittest.main()
