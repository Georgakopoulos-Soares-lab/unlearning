"""Portable, finite private saved-analysis restore. No production science dispatch."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tarfile,time
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,j):Path(p).write_text(json.dumps(j,indent=2,allow_nan=False)+'\n')
def safe(name):
 p=Path(name)
 if not name or p.is_absolute() or '..' in p.parts or '\\' in name or str(p)!=name:raise ValueError('Unsafe or noncanonical path')
 return p
def unpack(archive,dest,expected=None,max_bytes=3*1024**3):
 assert not dest.exists();dest.mkdir(parents=True)
 with tarfile.open(archive) as tf:
  members=tf.getmembers();seen=set();roots=set();actual=[];total=0
  for m in members:
   p=safe(m.name);assert m.name not in seen and not m.issym() and not m.islnk() and (m.isdir() or m.isfile());seen.add(m.name);roots.add(p.parts[0]);total+=m.size
   if m.isfile():actual.append('/'.join(p.parts[1:]))
  assert len(roots)==1 and total<=max_bytes and len(actual)==len(set(actual))
  if expected is not None:assert set(actual)==set(expected)
  tf.extractall(dest,filter='data')
 root=dest/next(iter(roots))
 if expected is None:
  manifest=read(root/'MEMBER_MANIFEST.json');expected={e['path']:e for e in manifest['files']};assert len(expected)==len(manifest['files']) and set(actual)==set(expected)|{'MEMBER_MANIFEST.json'}
 for rel,e in expected.items():
  safe(rel);p=root/rel;assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
 return root,len(actual),total
def main(args):
 from huggingface_hub import HfApi,hf_hub_download
 t=time.monotonic();backup=read(args.backup);repo=backup['repository'];dest=args.destination.resolve();assert args.destination.is_absolute() and not dest.exists();dest.mkdir(parents=True);api=HfApi();assert api.repo_info(repo,repo_type='dataset').private;transfers=[]
 def fetch(path,revision,h,size,cache):
  p=Path(hf_hub_download(repo,path,repo_type='dataset',revision=revision,force_download=True,cache_dir=str(cache)));assert p.stat().st_size==size and sha(p)==h;transfers.append({'path':path,'revision':revision,'bytes':size,'sha256':h,'force_download':True});return p
 archive=fetch(backup['archive_path'],backup['revision'],backup['archive_sha256'],backup['archive_bytes'],dest/'payload-cache');root,members,uncompressed=unpack(archive,dest/'payload-consumer');context=read(args.context or root/'DEPENDENCY_CONTEXT.json');graph=read(root/'public/RECOVERY_DEPENDENCY_GRAPH.json')
 if args.restore_dependencies:
  required=sum(n['bytes'] for n in graph['nodes'])
  for node,indexfile in context['indexes'].items():required+=sum(e['bytes'] for e in read(root/indexfile)['files'])
  available=min(shutil.disk_usage(dest).free,args.available_bytes) if args.available_bytes is not None else shutil.disk_usage(dest).free;assert available>required+5*1024**3,'Insufficient measured free capacity; check actual provider volume quota too'
  newroots={}
  for n in graph['nodes']:
   label=hashlib.sha256(n['id'].encode()).hexdigest()[:16];p=fetch(n['remote_path'],n['revision'],n['sha256'],n['bytes'],dest/'dependency-caches'/label)
   if n['kind']=='archive':
    index=read(root/context['indexes'][n['id']]);expected={e['path']:e for e in index['files']};expected.update(index['self_members']);target,count,raw=unpack(p,dest/'dependencies'/label,expected,max_bytes=sum(e['bytes'] for e in expected.values())+1024**2);newroots[n['id']]=str(target)
   else:
    target=dest/'dependency-objects'/label;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target);newroots[n['id']]=str(target)
  context['roots']=newroots
 elif not args.use_recorded_dependencies and args.context is None:raise ValueError('Choose existing recorded roots, supplied translated context, or fresh dependency restore')
 translated=dest/'TRANSLATED_DEPENDENCY_CONTEXT.json';put(translated,context);env=read(root/'public/ENVIRONMENT_CHECK.json');python=args.cpu_python or env['cpu_executable'];argv=[python,str(root/'code/consumer.py'),'--root',str(root),'--context',str(translated)];process=subprocess.run(argv,text=True,capture_output=True,env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':''});(dest/'consumer.stdout.json').write_text(process.stdout);(dest/'consumer.stderr.log').write_text(process.stderr);assert process.returncode==0,'Consumer panel failed; preserve diagnostics and do not weaken gates';checks=json.loads(process.stdout);assert checks['status']=='PASS' and api.repo_info(repo,repo_type='dataset').private
 proof={'schema':'pod-a-a09-fresh-restore-v1','status':'PASS','repository':repo,'payload_revision':backup['revision'],'archive_path':backup['archive_path'],'archive_sha256':backup['archive_sha256'],'archive_bytes':backup['archive_bytes'],'fresh_empty_destination':str(dest),'fresh_consumer_root':str(root),'force_download':True,'safe_exact_member_set':True,'all_payload_files_verified':members,'payload_uncompressed_bytes':uncompressed,'consumer_checks':checks,'consumer_command':argv,'prior_dependency_proofs_reused':not args.restore_dependencies,'new_full_dependency_transfer':args.restore_dependencies,'transfers':transfers,'private_at_read_and_closeout':True,'wall_seconds':time.monotonic()-t};put(dest/'FRESH_RESTORE_CHECK.json',proof);print(json.dumps(proof))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--backup',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);group=p.add_mutually_exclusive_group();group.add_argument('--use-recorded-dependencies',action='store_true');group.add_argument('--restore-dependencies',action='store_true');p.add_argument('--context',type=Path);p.add_argument('--cpu-python');p.add_argument('--available-bytes',type=int,help='Actual provider quota remaining, if below filesystem free-space value');main(p.parse_args())
