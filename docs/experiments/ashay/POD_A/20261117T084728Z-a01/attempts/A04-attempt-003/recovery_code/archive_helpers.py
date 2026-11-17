from pathlib import Path,PurePosixPath
import hashlib,shutil,tarfile
def sha(p):return hashlib.file_digest(Path(p).open("rb"),"sha256").hexdigest()

def verify_restore(fresh,consumer,payload_name,manifest,mh):
 assert not consumer.exists();consumer.mkdir(parents=True);seen=set();actual=set()
 with tarfile.open(fresh,'r:gz') as tf:
  members=tf.getmembers();assert sum(m.size for m in members)<1024**3
  for m in members:
   p=PurePosixPath(m.name);assert not p.is_absolute() and '..' not in p.parts and p.parts[0]==payload_name and str(p) not in seen and (m.isdir() or m.isfile());seen.add(str(p))
   if m.isfile():actual.add(str(PurePosixPath(*p.parts[1:])))
  assert actual=={r['path'] for r in manifest['files']}|{'MEMBER_MANIFEST.json'}
  for m in members:
   out=consumer/str(PurePosixPath(m.name));assert out.resolve().is_relative_to(consumer)
   if m.isdir():out.mkdir(parents=True,exist_ok=True)
   else:
    out.parent.mkdir(parents=True,exist_ok=True)
    with tf.extractfile(m) as inp,out.open('xb') as dst:shutil.copyfileobj(inp,dst)
 root=consumer/payload_name;assert sha(root/'MEMBER_MANIFEST.json')==mh
 for e in manifest['files']:p=root/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
 return root
