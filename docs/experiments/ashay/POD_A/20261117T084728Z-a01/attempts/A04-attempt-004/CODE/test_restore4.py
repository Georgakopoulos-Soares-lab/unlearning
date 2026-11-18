import io,json,hashlib,tarfile,tempfile,unittest
from pathlib import Path
from restore4 import extract,safe
class Checks(unittest.TestCase):
 def archive(self,root,extra=None,corrupt=False,duplicate=False):
  data=b'sealed qualification metadata';manifest=json.dumps({'files':[{'path':'code.py','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}],'self_excluded':True}).encode();path=root/'archive.tar.gz'
  with tarfile.open(path,'w:gz') as tf:
   for name,raw in [('payload/code.py',b'wrong' if corrupt else data),('payload/MEMBER_MANIFEST.json',manifest)]:
    m=tarfile.TarInfo(name);m.size=len(raw);tf.addfile(m,io.BytesIO(raw))
   if duplicate:
    m=tarfile.TarInfo('payload/code.py');m.size=len(data);tf.addfile(m,io.BytesIO(data))
   if extra:
    m=tarfile.TarInfo(extra[0])
    if extra[1]=='symlink':m.type=tarfile.SYMTYPE;m.linkname='/tmp/escape';tf.addfile(m)
    elif extra[1]=='hardlink':m.type=tarfile.LNKTYPE;m.linkname='payload/code.py';tf.addfile(m)
    else:m.size=1;tf.addfile(m,io.BytesIO(b'x'))
  return path,hashlib.sha256(manifest).hexdigest()
 def test_exact_all_member_recovery(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);archive,m=self.archive(p);root,count,size=extract(archive,p/'consumer',m);self.assertEqual(count,2);self.assertEqual((root/'code.py').read_bytes(),b'sealed qualification metadata')
 def test_corrupt_member_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a,h=self.archive(p,corrupt=True)
   with self.assertRaises(AssertionError):extract(a,p/'consumer',h)
 def test_duplicate_member_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a,h=self.archive(p,duplicate=True)
   with self.assertRaises(AssertionError):extract(a,p/'consumer',h)
 def test_extra_undeclared_member_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a,h=self.archive(p,extra=('payload/extra','file'))
   with self.assertRaises(AssertionError):extract(a,p/'consumer',h)
 def test_traversal_absolute_noncanonical_paths_rejected(self):
  for name in ['../escape','/tmp/escape','payload/../escape','payload//escape','payload\\escape']:
   with self.assertRaises(ValueError):safe(name)
 def test_links_rejected(self):
  for kind in ['symlink','hardlink']:
   with tempfile.TemporaryDirectory() as d:
    p=Path(d);a,h=self.archive(p,extra=('payload/link',kind))
    with self.assertRaises(AssertionError):extract(a,p/'consumer',h)
 def test_wrong_manifest_binding_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);a,h=self.archive(p)
   with self.assertRaises(AssertionError):extract(a,p/'consumer','0'*64)
if __name__=='__main__':unittest.main(verbosity=2)
