"""Adversarial reporting/source/restore acceptance; no fitting or new statistical tests."""
from common9 import *
from canonical9 import accept_source,context,unique_add
from portable_math8 import resolve
from archive9 import safe_extract
import tempfile,tarfile,io,fcntl,copy

def main():
 no_model_imports();checks=[];root=A/'qualification-002';root.mkdir(exist_ok=False);identity=read(C/'IDENTITY_CONTEXT.json');idx=read(D/'TABLE_INDEX.json');r=rows(D/idx['partitions'][0]['path'])[0];source=rows(W/r['A09_source_table'])[int(r['A09_source_CSV_line'])-2];kind=source.get('table_kind') or r['A09_table_kind']
 def trial(name,fn,reject=False):
  try:fn()
  except (AssertionError,KeyError,FileNotFoundError,PermissionError,ValueError,tarfile.ReadError,BlockingIOError,EOFError):assert reject,name
  else:assert not reject,name
  checks.append({'case':name,'status':'PASS','expected_rejection':reject})
 good=lambda:accept_source(r,source,kind,identity['endpoint_content_ids'],identity['protocol_sha256']);trial('valid immutable source row accepted',good)
 for field,value in [('estimate',str(float(r['estimate'])+.001)),('policy','wrong_policy'),('A09_scientific_key_sha256','0'*64),('A09_row_id','bad_identity')]:
  bad=r.copy();bad[field]=value;trial('changed canonical '+field+' rejected',lambda bad=bad:accept_source(bad,source,kind,identity['endpoint_content_ids'],identity['protocol_sha256']),True)
 badsource=source.copy();badsource['estimate']=str(float(source['estimate'])+.001);trial('changed original source value rejected',lambda:accept_source(r,badsource,kind,identity['endpoint_content_ids'],identity['protocol_sha256']),True)
 trial('outcome never enters canonical identity',lambda:(_ for _ in ()).throw(AssertionError()) if context(source,kind,identity['endpoint_content_ids'],identity['protocol_sha256'])!=context(badsource,kind,identity['endpoint_content_ids'],identity['protocol_sha256']) else None)
 trial('duplicate canonical keys rejected',lambda:unique_add({'x':1},'x',2),True)
 consumer=root/'consumer';consumer.mkdir();outside=root/'outside.txt';outside.write_text('fixture only');(consumer/'safe.txt').write_text('ok');(consumer/'escape').symlink_to(outside)
 desc={'storage_kind':'IMMUTABLE_ARCHIVE_MEMBER','archive_sha256':'a','repository':'test','revision':'r','archive_path':'a.tar.gz','member':'safe.txt','bytes':2,'sha256':bh(b'ok')};mapping={'archives':{'a':{'repository':'test','revision':'r','archive_path':'a.tar.gz','consumer_root':str(consumer)}}}
 trial('valid immutable member accepted',lambda:resolve(desc,mapping));trial('missing required dependency rejected',lambda:resolve(desc,{'archives':{}}),True)
 for name,changed in [('wrong object kind',{'storage_kind':'GIT_BLOB'}),('path escape',{'member':'../outside.txt'}),('symlink escape',{'member':'escape'}),('corrupt hash',{'sha256':'0'*64}),('wrong archive revision',{'revision':'bad'})]:trial(name+' rejected',lambda changed=changed:resolve(desc|changed,mapping),True)
 import common9
 original_git=common9.git
 def override(argspec,value):
  def fake(*a,**kw):return value if a==argspec else original_git(*a,**kw)
  common9.git=fake
  try:guard()
  finally:common9.git=original_git
 trial('wrong research branch rejected before mutation',lambda:override(('branch','--show-current'),'main'),True);trial('wrong origin rejected before mutation',lambda:override(('remote','get-url','origin'),'https://github.com/example/wrong.git'),True)
 lock=root/'publisher.lock';lock.write_text('')
 def excluded():
  with lock.open('r') as a,lock.open('r') as b:fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
 trial('concurrent publisher lock rejected',excluded,True)
 def make_tar(label,extra=None,missing=False,truncated=False):
  p=root/(label+'.tar.gz');payload=b'harmless fixture';manifest=json.dumps({'files':[{'path':'data.txt','bytes':len(payload),'sha256':bh(payload)}]}).encode();members=[('case/MEMBER_MANIFEST.json',manifest),('case/data.txt',payload)]
  if missing:members.pop()
  if extra:members.append(extra)
  with tarfile.open(p,'w:gz') as tf:
   for name,data in members:
    e=tarfile.TarInfo(name)
    if data is None:e.type=tarfile.SYMTYPE;e.linkname='../../outside.txt';tf.addfile(e)
    else:e.size=len(data);tf.addfile(e,io.BytesIO(data))
  if truncated:p.write_bytes(p.read_bytes()[:20])
  return p
 trial('valid exact-member archive accepted',lambda:safe_extract(make_tar('valid'),root/'valid-out'))
 for name,extra in [('absolute',('/case/escape',b'x')),('traversal',('case/../escape',b'x')),('duplicate',('case/data.txt',b'other')),('symlink',('case/link',None)),('undeclared',('case/extra.txt',b'x'))]:trial('archive '+name+' rejected',lambda name=name,extra=extra:safe_extract(make_tar(name,extra),root/(name+'-out')),True)
 trial('missing declared archive member rejected',lambda:safe_extract(make_tar('missing',missing=True),root/'missing-out'),True);trial('interrupted truncated archive rejected',lambda:safe_extract(make_tar('partial',truncated=True),root/'partial-out'),True)
 for p in (A/'code').glob('*.py'):compile(p.read_text(),str(p),'exec')
 result={'status':'PASS','checks':checks,'case_count':len(checks),'new_fits_forwards_draws_or_numerical_audits':0,'qualification_scope':'New source/key/path/archive/publication contracts only; unchanged A08 numerical qualifications reused'};put(C/'IMPLEMENTATION_VALIDATION.json',result);print(json.dumps({'status':'PASS','cases':len(checks),'fits':0}))
if __name__=='__main__':main()
