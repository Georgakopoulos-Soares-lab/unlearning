from common9 import *
import tarfile,time
def safe_extract(archive,destination):
 dest=Path(destination);assert not dest.exists();t=time.monotonic()
 with tarfile.open(archive) as tf:
  members=tf.getmembers();names=set();roots=set()
  for m in members:
   p=Path(m.name);assert m.isfile() and not m.issym() and not m.islnk() and not p.is_absolute() and '..' not in p.parts and '\\' not in m.name and str(p)==m.name and m.name not in names;names.add(m.name);roots.add(p.parts[0])
  assert len(roots)==1;root=next(iter(roots));manifest=json.load(tf.extractfile(root+'/MEMBER_MANIFEST.json'));expected={e['path']:e for e in manifest['files']};assert len(expected)==len(manifest['files']);assert {str(Path(m.name).relative_to(root)) for m in members}==set(expected)|{'MEMBER_MANIFEST.json'}
  # Validate all bytes before accepting extracted output; preserve failed consumer paths.
  dest.mkdir(parents=True)
  for m in members:
   rel=str(Path(m.name).relative_to(root));target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
   with tf.extractfile(m) as src,target.open('wb') as out:
    import hashlib
    h=hashlib.sha256();size=0
    while b:=src.read(8*1024**2):out.write(b);h.update(b);size+=len(b)
   if rel!='MEMBER_MANIFEST.json':assert h.hexdigest()==expected[rel]['sha256'] and size==expected[rel]['bytes'],rel
 return len(members),time.monotonic()-t
