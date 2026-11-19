"""Typed immutable file resolution; metadata only, no array/model imports."""
from common8 import *
from collections import defaultdict
class Registry:
 def __init__(self):
  self.artifacts={};self.lookup=defaultdict(list);self.nodes={};self.member_indices={};graph=read(D5/'RECOVERY_DEPENDENCY_GRAPH.json')
  for n in graph['nodes']:
   if n.get('kind')!='archive' or not n.get('consumer_root'):continue
   root=Path(n['consumer_root']);idx=Path(n['member_index']) if n.get('member_index') else root/'MEMBER_MANIFEST.json'
   if not idx.exists():continue
   data=read(idx);entries=data['files'] if isinstance(data,dict) else data;archive={'repository':n['repository'],'revision':n['revision'],'archive_path':n['remote_path'],'archive_sha256':n['sha256'],'consumer_root':str(root)};self.add_archive(archive,entries)
  for p in [C6/'BACKUP_R5_H3.json',C6/'BACKUP_R5_other_five.json']:
   b=read(p);root=Path(b['fresh_consumer']);self.add_archive(b|{'consumer_root':str(root)},read(root/'MEMBER_MANIFEST.json')['files'])
  for b in read(C7/'BACKUP_VERIFICATION.json')['checkpoints']:
   root=Path(b['consumer_root']);self.add_archive(b,read(root/'MEMBER_MANIFEST.json')['files'])
  for p in C.glob('BACKUP_*.json'):
   if p.name=='BACKUP_VERIFICATION.json':continue
   b=read(p)
   if b.get('status')=='PASS':self.add_archive(b,read(Path(b['consumer_root'])/'MEMBER_MANIFEST.json')['files'])
  self.bindings={e['local_input_path']:e for e in graph['input_bindings']};self.graph=graph
 def add_archive(self,b,entries):
  node={k:b[k] for k in ['repository','revision','archive_path','archive_sha256']};node['consumer_root']=b['consumer_root'];key=b['archive_sha256'];self.nodes[key]=node;ix={e['path']:e for e in entries};assert len(ix)==len(entries);self.member_indices[key]=ix
  for e in entries:self.lookup[(e['sha256'],e['bytes'])].append(node|{'member':e['path'],'sha256':e['sha256'],'bytes':e['bytes']})
 def file(self,path,kind,selector=None,expected=None):
  p=Path(path);h=sha(p);size=p.stat().st_size;assert not p.is_symlink()
  if expected:assert h==expected
  if p.is_relative_to(W):
   rel=str(p.relative_to(W));commit=cfg['research_head_before'];assert gitb('show',commit+':'+rel)==p.read_bytes();d={'storage_kind':'GIT_BLOB','repository':'Georgakopoulos-Soares-lab/unlearning','commit':commit,'path':rel,'sha256':h,'bytes':size}
  else:
   candidates=self.lookup.get((h,size),[]);assert candidates,'No immutable archive/member for '+str(p)
   # Prefer the actual consumer/member route; identical byte aliases remain valid file identities.
   same=[e for e in candidates if str(p)==str(Path(e['consumer_root'])/e['member'])];named=[e for e in candidates if Path(e['member']).name==p.name];chosen=(same or named or candidates)[0];d={k:chosen[k] for k in ['repository','revision','archive_path','archive_sha256','member','sha256','bytes']};d['storage_kind']='IMMUTABLE_ARCHIVE_MEMBER'
  d.update(hash_kind=kind,array_selector=selector);identity=digest(d);self.artifacts[identity]=d;return 'provenance:'+identity
 def descriptor(self,path,kind,selector=None,expected=None):return self.artifacts[self.file(path,kind,selector,expected).removeprefix('provenance:')]
 def validate(self):
  for identity,d in self.artifacts.items():
   assert identity==digest(d)
   if d['storage_kind']=='IMMUTABLE_ARCHIVE_MEMBER':
    e=self.member_indices[d['archive_sha256']][d['member']];n=self.nodes[d['archive_sha256']];assert all(d[k]==n[k] for k in ['repository','revision','archive_path']);assert e['sha256']==d['sha256'] and e['bytes']==d['bytes']
  return {'status':'PASS','typed_descriptors':len(self.artifacts),'resolved_archive_member_indices':len(self.member_indices),'no_object_kind_substitution':True}
 def immutable_map(self):return {'archives':self.nodes,'member_indices':self.member_indices,'producer_paths_allowed':False,'new_inherited_download':False}

def consume_descriptor(d,mapping):
 assert d['storage_kind']=='IMMUTABLE_ARCHIVE_MEMBER';node=mapping['archives'][d['archive_sha256']];assert all(d[k]==node[k] for k in ['repository','revision','archive_path']);root=Path(node['consumer_root']);p=root/d['member'];assert p.resolve().is_relative_to(root.resolve()) and ('/consumer' in str(root) or '/restored/' in str(root));assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];return p
