"""Exercise unsafe archive rejection and exact-byte safe restore in disposable fixtures."""
import unittest,tempfile,tarfile,io,json,hashlib
from pathlib import Path
from restore import unpack,safe
class RestoreTests(unittest.TestCase):
 def make(self,base,items):
  p=base/'payload.tar'
  with tarfile.open(p,'w') as tf:
   for name,body,kind in items:
    m=tarfile.TarInfo(name)
    if kind=='link':m.type=tarfile.SYMTYPE;m.linkname='/tmp/forbidden';tf.addfile(m)
    else:m.size=len(body);tf.addfile(m,io.BytesIO(body))
  return p
 def test_unsafe_paths(self):
  for p in ['../escape','/absolute','root/../escape','root//alias','root\\alias']:
   with self.assertRaises(ValueError):safe(p)
 def test_duplicate_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=self.make(root,[('pkg/a',b'x','file'),('pkg/a',b'x','file')])
   with self.assertRaises(AssertionError):unpack(a,root/'consumer',{'a':{'bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}})
 def test_link_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=self.make(root,[('pkg/link',b'','link')])
   with self.assertRaises(AssertionError):unpack(a,root/'consumer',{})
 def test_extra_member_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=self.make(root,[('pkg/a',b'x','file'),('pkg/extra',b'y','file')])
   with self.assertRaises(AssertionError):unpack(a,root/'consumer',{'a':{'bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}})
 def test_corrupt_member_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);a=self.make(root,[('pkg/a',b'y','file')])
   with self.assertRaises(AssertionError):unpack(a,root/'consumer',{'a':{'bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}})
 def test_safe_payload_all_bytes(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);data=b'checked';member={'path':'a','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};mm=json.dumps({'files':[member]}).encode();a=self.make(root,[('pkg/a',data,'file'),('pkg/MEMBER_MANIFEST.json',mm,'file')]);p,n,size=unpack(a,root/'consumer');self.assertEqual(n,2);self.assertEqual((p/'a').read_bytes(),data)
if __name__=='__main__':unittest.main(verbosity=2)
