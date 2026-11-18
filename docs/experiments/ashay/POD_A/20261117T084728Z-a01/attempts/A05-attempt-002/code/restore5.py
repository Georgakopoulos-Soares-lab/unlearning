"""Standalone metadata consumer. No producer control paths or scientific libraries."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,tarfile,subprocess,sys,importlib.util,time
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(b):return hashlib.sha256(b).hexdigest()
def safe_members(tf):
 members=tf.getmembers();names=set();roots=set();size=0
 for m in members:
  p=PurePosixPath(m.name)
  if not m.isfile() or m.issym() or m.islnk() or p.is_absolute() or '..' in p.parts or '\\' in m.name or str(p)!=m.name or len(p.parts)<2 or m.name in names:raise ValueError('Unsafe/duplicate/non-regular archive member')
  names.add(m.name);roots.add(p.parts[0]);size+=m.size
  if size>512*1024**2:raise ValueError('Not a bounded planning-only archive')
 if len(roots)!=1:raise ValueError('Expected exact single archive root')
 root=next(iter(roots));manifest=json.load(tf.extractfile(root+'/MEMBER_MANIFEST.json'));index={e['path']:e for e in manifest['files']}
 if len(index)!=len(manifest['files']) or {str(PurePosixPath(n).relative_to(root)) for n in names}!=set(index)|{'MEMBER_MANIFEST.json'}:raise ValueError('Missing/extra/duplicate archive members')
 for rel,e in index.items():
  raw=tf.extractfile(root+'/'+rel).read()
  if len(raw)!=e['bytes'] or digest(raw)!=e['sha256']:raise ValueError('Corrupted archive member: '+rel)
 return root,index,members
def consume(archive,expected_sha,destination,git_source,check_remote=False):
 start=time.monotonic();archive=Path(archive);dest=Path(destination)
 if sha(archive)!=expected_sha:raise ValueError('Archive checksum mismatch')
 if dest.exists():raise ValueError('Fresh consumer destination must not exist')
 with tarfile.open(archive) as tf:
  root,index,members=safe_members(tf);dest.mkdir(parents=True)
  for m in members:
   rel=PurePosixPath(m.name).relative_to(root);p=dest/str(rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(m).read())
 read=lambda p:json.loads(Path(p).read_text());public=dest/'public';identity=read(dest/'PAYLOAD_IDENTITY.json');plan=read(public/'COVERAGE_PLAN.json');h=sha(public/'COVERAGE_PLAN.json');assert h==identity['coverage_plan_sha256'];design=read(public/'TABLE_KEY_DESIGN.json');assert sha(public/'TABLE_KEY_DESIGN.json')==plan['table_key_design_sha256']
 path=dest/'artifacts/code/keys5.py';spec=importlib.util.spec_from_file_location('restored_planning_keys',path);keys_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(keys_module);rows=keys_module.table_keys(design,h);assert keys_module.compressed_keys(rows)==(public/'EXPECTED_TABLE_KEYS.csv.gz').read_bytes();coverage=keys_module.coverage_rows()
 import csv
 with (public/'EXPECTED_COVERAGE.csv').open() as f:actual=list(csv.DictReader(f))
 assert [x['unit_id'] for x in actual]==[x['unit_id'] for x in coverage] and len(actual)==6637 and all(x['coverage_plan_sha256']==h for x in actual)
 graph=read(public/'RECOVERY_DEPENDENCY_GRAPH.json');nodes={n['id']:n for n in graph['nodes']};seen=set();visiting=set()
 def visit(k):
  assert k in nodes
  if k in seen:return
  assert k not in visiting;visiting.add(k)
  for d in nodes[k]['dependencies']:visit(d)
  visiting.remove(k);seen.add(k)
 for k in nodes:visit(k)
 indices={}
 for k,n in nodes.items():
  if 'protected_source_index' not in n:continue
  ref=n['protected_source_index'];p=dest/'artifacts'/ref['path'];assert p.stat().st_size==ref['bytes'] and sha(p)==ref['sha256'];j=read(p);entries=j['files'];entries=[dict(e,path=r) for r,e in entries.items()] if isinstance(entries,dict) else entries;indices[k]={e['path']:(e['sha256'],e['bytes']) for e in entries}
 gitrefs={}
 for e in graph['input_bindings']:
  b=e['binding'];assert b['sha256']==e['sha256'] and b['bytes']==e['bytes']
  if b['kind']=='GIT_BLOB':gitrefs[(b['commit'],b['path'])]=(b['sha256'],b['bytes'])
  else:
   assert b['kind']=='IMMUTABLE_ARCHIVE_MEMBER' and b['candidates']
   for c in b['candidates']:assert indices[c['dependency_id']][c['member']]==(e['sha256'],e['bytes'])
 # This explicitly supplied object database is read-only and every object is immutable/pinned.
 for (commit,path),(expected,n) in gitrefs.items():
  raw=subprocess.check_output(['git','-C',str(git_source),'show',commit+':'+path]);assert digest(raw)==expected and len(raw)==n
 # New public payload bytes must also match the independently pinned planning commit.
 for path in public.rglob('*'):
  if path.is_file():assert subprocess.check_output(['git','-C',str(git_source),'show',identity['planning_commit']+':'+identity['research_attempt_path']+'/'+str(path.relative_to(public))])==path.read_bytes()
 remote_count=0
 if check_remote:
  from huggingface_hub import HfApi,hf_hub_download
  api=HfApi()
  for repo in {n['repository'] for n in nodes.values()}:assert api.repo_info(repo,repo_type='dataset').private
  for n in nodes.values():
   info=api.get_paths_info(n['repository'],[n['remote_path']],repo_type='dataset',revision=n['revision'])[0];assert info.size==n['bytes']
   if info.lfs:assert info.lfs.sha256==n['sha256']
   elif n.get('prior_A09_remote_check',{}).get('remote_blob_id'):assert info.blob_id==n['prior_A09_remote_check']['remote_blob_id']
   else:
    assert info.size<2*1024**2,'No large scientific dependency download in A05';p=Path(hf_hub_download(n['repository'],n['remote_path'],repo_type='dataset',revision=n['revision'],force_download=True,cache_dir=str(dest/'fresh-small-dependency-cache')));assert sha(p)==n['sha256']
   remote_count+=1
 assert not any(k in sys.modules for k in ['torch','sklearn','joblib','bionemo','megatron']);result={'status':'PASS','archive_sha256':expected_sha,'members_verified':len(index)+1,'all_members_exact_safe_regular_files':True,'restored_coverage_plan_sha256':h,'regenerated_ledger_units':len(coverage),'regenerated_expected_result_keys':len(rows),'immutable_input_bindings_resolved':len(graph['input_bindings']),'immutable_Git_input_blobs_verified':len(gitrefs),'dependency_nodes_acyclic':len(nodes),'remote_nodes_rechecked':remote_count,'new_public_bytes_match_planning_commit':identity['planning_commit'],'old_producer_paths_read':False,'scientific_arrays_or_weights_read':False,'new_fits_predictions_effects_forwards':0,'full_GPU_runtime_recreation_claimed':False,'seconds':time.monotonic()-start};(dest/'FRESH_CONSUMER_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--archive',required=True);p.add_argument('--sha256',required=True);p.add_argument('--destination',required=True);p.add_argument('--git-source',required=True);p.add_argument('--check-remote',action='store_true');a=p.parse_args();print(json.dumps(consume(a.archive,a.sha256,a.destination,a.git_source,a.check_remote)))
