import unittest,tarfile
from unittest.mock import patch
from pathlib import Path
from production_contract import safe_archive_members
import scope6
class ArchiveUnitTests(unittest.TestCase):
 def test_duplicate_archive_names_rejected(self):
  one=tarfile.TarInfo('root/one.json');one.size=1;two=tarfile.TarInfo('root/one.json');two.size=1
  with self.assertRaises(ValueError):safe_archive_members([one,two],'root')
 def test_duplicate_finite_H3_unit_rejected(self):
  original=scope6.read
  def duplicate(p):
   j=original(p)
   if Path(p).name=='A06_EXECUTION_MANIFEST.json':j['H3_head_application_units'][-1]=j['H3_head_application_units'][0]
   return j
  with patch.object(scope6,'read',side_effect=duplicate):
   with self.assertRaises(ValueError):scope6.h3_specs('R5')
if __name__=='__main__':unittest.main()
