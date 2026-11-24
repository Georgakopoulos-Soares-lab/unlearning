import unittest,copy,json,tempfile,fcntl,hashlib
from pathlib import Path
from ops import C
from mirror_contract import admit,compatible_resume,response_range,verify_bytes
class MirrorBoundaries(unittest.TestCase):
 def setUp(self):
  self.h=next(r for r in json.loads((C/'MIRROR_HANDOFF.json').read_text()) if r['alias']=='candidate_02');self.r=json.loads((C/'remote-evidence/candidate_02/receipt.json').read_text());self.m=json.loads((C/'remote-evidence/candidate_02/manifest.json').read_text());self.src=json.loads((C/'SEALED_SOURCE_MEMBER_MAP.json').read_text());self.selected={'candidate_02':self.h['candidate_id']}
 def accept(self):return admit(self.h,self.r,self.m,self.selected,self.src)
 def test_real_exact_metadata(self):self.accept()
 def test_wrong_discovery(self):
  self.m['candidate']['folder_id']='different'
  with self.assertRaises(ValueError):self.accept()
 def test_receipt_wrong_revision(self):
  self.r['payload_revision']='0'*40
  with self.assertRaises(ValueError):self.accept()
 def test_changed_native_hash(self):
  self.m['files'][-1]['sha256']='0'*64
  with self.assertRaises(ValueError):self.accept()
 def test_missing_member(self):
  self.m['files'].pop()
  with self.assertRaises(ValueError):self.accept()
 def test_extra_or_duplicate_member(self):
  self.m['files'][-1]=copy.deepcopy(self.m['files'][0])
  with self.assertRaises(ValueError):self.accept()
 def test_unsafe_path(self):
  self.m['files'][0]['path']='../.metadata'
  with self.assertRaises(ValueError):self.accept()
 def test_pointer_or_same_size_corruption(self):
  with tempfile.TemporaryDirectory(dir=C) as d:
   p=Path(d)/'f';data=b'version https://git-lfs.github.com/spec/v1\n';p.write_bytes(data)
   with self.assertRaises(ValueError):verify_bytes(p,{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
   p.write_bytes(b'12')
   with self.assertRaises(ValueError):verify_bytes(p,{'bytes':2,'sha256':hashlib.sha256(b'21').hexdigest()})
 def test_interrupted_transfer_binding(self):
  e={'repo_id':'private-route','revision':'1'*40,'remote_path':'x','expected_bytes':100,'expected_sha256':'2'*64};self.assertEqual(compatible_resume(e,e,40),40);wrong={**e,'revision':'3'*40}
  with self.assertRaises(ValueError):compatible_resume(wrong,e,40)
 def test_bad_resume_response(self):
  response_range(206,'bytes 40-99/100',40,100)
  for status,header in [(200,None),(206,'bytes 0-99/100'),(206,'bytes 40-99/101')]:
   with self.assertRaises(ValueError):response_range(status,header,40,100)
 def test_duplicate_writer_lock(self):
  with tempfile.TemporaryDirectory(dir=C) as d:
   p=Path(d)/'lock'
   with p.open('a') as a,p.open('a') as b:
    fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaises(BlockingIOError):fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
if __name__=='__main__':unittest.main()
