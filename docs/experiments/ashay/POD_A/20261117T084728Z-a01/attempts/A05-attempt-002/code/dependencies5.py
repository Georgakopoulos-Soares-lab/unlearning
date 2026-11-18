"""Refresh immutable dependency identities without restoring historical payloads."""
from common5 import *
from collections import defaultdict,Counter
from huggingface_hub import HfApi,hf_hub_download
import time,tarfile
def main():
 start=time.monotonic();guard();api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private and api.repo_info(MIRROR,repo_type='dataset').private;old=read(D9/'RECOVERY_DEPENDENCY_GRAPH.json');nodes=json.loads(json.dumps(old['nodes']));hash_index=defaultdict(list);index_records=[]
 for n in nodes:
  n['prior_A09_remote_check']=n.pop('current_remote',None);n['prior_A09_local_hash_proof']=n.pop('current_local',None);current=api.get_paths_info(n['repository'],[n['remote_path']],repo_type='dataset',revision=n['revision'])[0];assert current.size==n['bytes'];lfs=getattr(current,'lfs',None)
  if lfs:assert lfs.sha256==n['sha256'];method='CURRENT_IMMUTABLE_REMOTE_LFS_SHA256_SIZE_NO_PAYLOAD_TRANSFER'
  else:
   assert current.size<2*1024**2,'No hidden historical payload download';path=Path(hf_hub_download(n['repository'],n['remote_path'],repo_type='dataset',revision=n['revision'],force_download=True,cache_dir=str(REC/'small-dependency-metadata-cache')));assert sha(path)==n['sha256'];method='FRESH_SMALL_IMMUTABLE_OBJECT_SHA256'
  n['A05_remote_check']={'status':'PASS','method':method,'checked_utc':now(),'new_large_transfer':False};root=n.get('consumer_root')
  if not root:continue
  p=Path(n['member_index']) if n.get('member_index') else Path(root)/'MEMBER_MANIFEST.json'
  if not p.exists():p=Path(root)/'PAYLOAD_MANIFEST.json'
  assert p.is_file();oldindex=(n.get('prior_A09_local_hash_proof') or {}).get('member_index');h=sha(p)
  if oldindex:assert h==oldindex['sha256']
  elif n.get('member_manifest_sha256') and p.name=='MEMBER_MANIFEST.json':assert h==n['member_manifest_sha256']
  data=read(p);entries=data['files'];entries=[dict(v,path=k) for k,v in entries.items()] if isinstance(entries,dict) else entries
  for e in entries:hash_index[(e['sha256'],e['bytes'])].append({'dependency_id':n['id'],'member':e['path']})
  # Embed checksum metadata only, never historical payloads.
  rel='dependency-indexes/'+digest([n['id'],h])+'.json';put(A/rel,{'dependency_id':n['id'],'source_index_sha256':h,'files':entries});n['protected_index']=rel;rawrel='dependency-indexes/original-'+h+'.json';atomic(A/rawrel,p.read_bytes());n['protected_source_index']={'path':rawrel,'bytes':p.stat().st_size,'sha256':h};index_records.append({'node':n['id'],'path':str(p),'sha256':h,'files':len(entries),'identity_unchanged':True})
 # A04 new qualification/final metadata identity chain was freshly checked earlier this attempt.
 chain=read(C/'PRIVATE_INPUT_CHAIN.json')
 for e in chain['fresh_small_objects']:
  n={'id':e['kind'],'kind':'archive' if e['kind'].endswith('metadata') else 'object','repository':e['repository'],'revision':e['revision'],'remote_path':e['path'],'bytes':e['bytes'],'sha256':e['sha256'],'dependencies':['A04_new_qualification_evidence'] if e['kind'].endswith('metadata') else ['A04_final_metadata'],'A05_remote_check':{'status':'PASS','method':'FRESH_SMALL_IDENTITY_CHAIN_FROM_PREFLIGHT'}};nodes.append(n)
  if n['kind']=='archive':
   path=Path(hf_hub_download(e['repository'],e['path'],repo_type='dataset',revision=e['revision'],local_files_only=True,cache_dir=str(REC/'small-A04-identity-readback-cache')))
   with tarfile.open(path) as tf:
    entry=next(m for m in tf.getmembers() if m.name.endswith('/MEMBER_MANIFEST.json'));raw=tf.extractfile(entry).read();data=json.loads(raw);entries=data['files'];rawrel='dependency-indexes/original-'+bh(raw)+'.json';atomic(A/rawrel,raw);n['protected_source_index']={'path':rawrel,'bytes':len(raw),'sha256':bh(raw)}
    for x in entries:hash_index[(x['sha256'],x['bytes'])].append({'dependency_id':n['id'],'member':x['path']})
    rel='dependency-indexes/'+digest([n['id'],sha(path)])+'.json';put(A/rel,{'dependency_id':n['id'],'source_archive_sha256':sha(path),'files':entries});n['protected_index']=rel
 e=chain['scientific_evidence_archive'];nodes.append({'id':'A04_new_qualification_evidence','kind':'archive','repository':e['repository'],'revision':e['revision'],'remote_path':e['path'],'bytes':e['bytes'],'sha256':e['sha256'],'dependencies':['A04-attempt-003'],'A05_remote_check':{'status':'PASS','method':'CURRENT_IMMUTABLE_REMOTE_LFS_IDENTITY_PRIOR_387MEMBER_189COMPARISON_FRESH_PROOF_REUSED'},'prior_fresh_proof_sha256':e['prior_proof_sha256']})
 # Bind all 16 native source assets to their pinned mirror objects; only metadata APIs.
 for e in read(C/'PAYLOAD_PRESENCE.json')['assets']:
  n={'id':'native/'+e['alias']+'/'+e['native_relative_path'],'kind':'object','repository':MIRROR,'revision':e['mirror_revision'],'remote_path':e['mirror_path'],'bytes':e['bytes'],'sha256':e['sha256'],'dependencies':[],'integrity_method':e['verification_method']};info=api.get_paths_info(MIRROR,[n['remote_path']],repo_type='dataset',revision=n['revision'])[0];assert info.size==n['bytes']
  if info.lfs:assert info.lfs.sha256==n['sha256']
  # Native sidecars are already freshly hashed in preflight; native shards reuse exact prior stat seals.
  n['A05_remote_check']={'status':'PASS','method':'PINNED_MIRROR_SIZE_LFS_IF_PRESENT_PLUS_PREFLIGHT_SMALL_HASH_OR_NATIVE_STAT_SEAL'};nodes.append(n)
 ids={n['id'] for n in nodes};assert len(ids)==len(nodes)
 visiting=set();done=set()
 def visit(key):
  assert key in ids
  if key in done:return
  assert key not in visiting,'Dependency cycle';visiting.add(key)
  for d in next(n for n in nodes if n['id']==key)['dependencies']:visit(d)
  visiting.remove(key);done.add(key)
 for n in nodes:visit(n['id'])
 # Resolve local producer paths via content/size into immutable archive members or public Git blobs.
 inputs=read(C/'INPUT_MANIFEST.json');public_by_hash={};resolved=[];missing=[]
 for e in inputs['inputs']:
  if e.get('repository_path'):public_by_hash[(e['sha256'],e['bytes'])]={'kind':'GIT_BLOB','repository':e['repository'],'commit':e['commit'],'path':e['repository_path'],'sha256':e['sha256'],'bytes':e['bytes']}
 for e in inputs['inputs']:
  key=(e['sha256'],e['bytes']);p=Path(e['path']);binding=public_by_hash.get(key)
  if binding is None and p.is_relative_to(W):
   rel=str(p.relative_to(W));assert bh(gitb('show',cfg['research_head_before']+':'+rel))==e['sha256'];binding={'kind':'GIT_BLOB','repository':'Georgakopoulos-Soares-lab/unlearning','commit':cfg['research_head_before'],'path':rel,'sha256':e['sha256'],'bytes':e['bytes']}
  if binding is None and key in hash_index:binding={'kind':'IMMUTABLE_ARCHIVE_MEMBER','candidates':hash_index[key],'sha256':e['sha256'],'bytes':e['bytes'],'selection':'Every listed member has identical SHA256 and bytes; candidate list preserves legitimate content aliases'}
  if binding is None:
   # Public source code can be a byte-identical derivative of its private stage source.
   for root in [D3,D4,D50,D6,D7,D8,D9]:
    candidate=root/'code'/p.name
    if candidate.exists() and candidate.stat().st_size==e['bytes'] and sha(candidate)==e['sha256']:
     rel=str(candidate.relative_to(W));assert bh(gitb('show',cfg['research_head_before']+':'+rel))==e['sha256'];binding={'kind':'GIT_BLOB','repository':'Georgakopoulos-Soares-lab/unlearning','commit':cfg['research_head_before'],'path':rel,'sha256':e['sha256'],'bytes':e['bytes']};break
  if binding is None:missing.append(e)
  else:resolved.append({'local_input_path':e['path'],'sha256':e['sha256'],'bytes':e['bytes'],'binding':binding})
 put(C/'UNRESOLVED_DEPENDENCIES.json',missing);assert not missing,[(e['path'],e['sha256']) for e in missing[:12]]
 graph={'schema':'pod-a-a05-amendment-recovery-graph-v1','status':'PASS','input_research_commit':cfg['research_head_before'],'prior_A09_graph':{'path':str((D9/'RECOVERY_DEPENDENCY_GRAPH.json').relative_to(W)),'sha256':sha(D9/'RECOVERY_DEPENDENCY_GRAPH.json')},'nodes':nodes,'all_dependencies_acyclic_resolved':True,'input_bindings':resolved,'input_binding_count':len(resolved),'metadata_index_records':index_records,'prior_scientific_arrays_and_weights_repacked':False,'prior_large_archives_downloaded':False,'old_scientific_audits_repeated':False,'scope':'Planning dependency identity resolution using immutable Git/blob and remote archive/member identities; prior full fresh recovery/numerical proofs explicitly reused. Not a full GPU/runtime rebuild.','wall_seconds':time.monotonic()-start};put(C/'RECOVERY_DEPENDENCY_GRAPH.json',graph);publish('RECOVERY_DEPENDENCY_GRAPH.json',graph);publish('code/dependencies5.py',(A/'code/dependencies5.py').read_bytes());no_science_imports();print(json.dumps({'status':'PASS','nodes':len(nodes),'bound_inputs':len(resolved),'seconds':graph['wall_seconds']}))
if __name__=='__main__':main()
