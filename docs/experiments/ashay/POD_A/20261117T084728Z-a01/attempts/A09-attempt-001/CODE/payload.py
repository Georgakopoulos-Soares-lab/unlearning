"""Build and qualify an A09 payload without repacking inherited scientific arrays."""
from common import *
import argparse,shutil,time
def index_for(node):
 path=Path(node['current_local']['member_index']['path']);j=read(path);raw=j['files'];entries=[{'path':k,**v} for k,v in raw.items()] if isinstance(raw,dict) else raw;root=Path(node['consumer_root']);listed={e['path'] for e in entries};extra={}
 for name in ['MEMBER_MANIFEST.json','PAYLOAD_MANIFEST.json','CHECKSUMS.sha256']:
  p=root/name
  if p.exists() and name not in listed:extra[name]={'bytes':p.stat().st_size,'sha256':sha(p)}
 return {'files':entries,'self_members':extra,'original_index':ref(path),'prior_fresh_proof':node['prior_fresh_restore_proof']}
def seal(root):
 files=[{'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.rglob('*')) if p.is_file() and p.name!='MEMBER_MANIFEST.json'];assert not any(p.is_symlink() for p in root.rglob('*'));put(root/'MEMBER_MANIFEST.json',{'schema':'pod-a-a09-payload-members-v1','files':files,'self_excluded':True});return files
def build(version):
 graph=read(C/'RECOVERY_DEPENDENCY_GRAPH.json');assert graph['status']=='PASS';root=A/('payload-build-'+version)/('A09-report-payload-'+version);assert not root.exists();root.mkdir(parents=True);shutil.copytree(D,root/'public');shutil.copytree(A/'code',root/'code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(C/'prompt',root/'prompt');(root/'control').mkdir();(root/'indexes').mkdir();context={'schema':'pod-a-a09-dependency-context-v1','roots':{},'indexes':{},'index_sha256':{},'proof_attribution':'Immutable prior force-fresh consumers and current all-byte/remote identity checks, separate from new A09 payload download'}
 for n in graph['nodes']:
  context['roots'][n['id']]=n['consumer_root'] if n['kind']=='archive' else n['local_file']
  if n['kind']=='archive':
   label=digest(n['id'])[:16];relative='indexes/'+label+'.json';put(root/relative,index_for(n));context['indexes'][n['id']]=relative;context['index_sha256'][n['id']]=sha(root/relative)
 put(root/'DEPENDENCY_CONTEXT.json',context)
 for p in C.iterdir():
  if p.is_file() and p.suffix in ['.json','.jsonl','.md','.z','.txt'] and not p.name.startswith('PRIOR_CURRENT_'):shutil.copyfile(p,root/'control'/p.name)
 recipes=root/'reacquisition-metadata';recipes.mkdir()
 for n in ['CHECKPOINT_HASHES.final.json','ASSET_TRANSFER_MANIFEST.json','ENVIRONMENT_LOCK.json','SOURCE_IDENTITY.json','RUNTIME_REBUILD.md','runtime-freeze.txt']:
  p=C.parent/'A04-attempt-002'/n
  if p.exists():shutil.copyfile(p,recipes/n)
 put(root/'EXCLUSIONS.json',{'scope':'New A09 reports/derivatives/code/control/prompts and exact dependency indexes, no duplicated historical arrays','excluded':['Credentials/account stores','All checkpoint model weights','Installed GPU/runtime binaries','Inherited scientific arrays and heads, referenced by exact pinned archive dependencies','Unrelated PodBdata and untouchedtests'],'reacquisition':'public/REACQUISITION_MAP.json and reacquisition-metadata/ exact manifests/recipe; no full GPU recreation claim','prior_immutable_dependencies':graph['nodes']});seal(root);put(C/('PAYLOAD_BUILD_'+version+'.json'),{'status':'BUILT','root':str(root),'version':version,'consumer_source_sha256':sha(root/'code/consumer.py')});print(json.dumps({'status':'BUILT','root':str(root)}));return root
def qualify(root):
 t=time.monotonic();argv=[cfg['cpu_venv']+'/bin/python',str(root/'code/consumer.py'),'--root',str(root)];p=subprocess.run(argv,text=True,capture_output=True,env={**os.environ,'OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONDONTWRITEBYTECODE':'1','CUDA_VISIBLE_DEVICES':''});name='consumer-local-'+root.name;(A/'logs'/(name+'.stdout.json')).write_text(p.stdout);(A/'logs'/(name+'.stderr.log')).write_text(p.stderr);put(C/('LOCAL_QUALIFICATION_'+root.name+'.json'),{'status':'PASS' if p.returncode==0 else 'FAILED','argv':argv,'exit_code':p.returncode,'wall_seconds':time.monotonic()-t,'fresh_remote_recovery':False,'new_fits_or_forwards':0,'source_sha256':sha(root/'code/consumer.py')});assert p.returncode==0,'Preserve failed local consumer, correct implementation and create a new version; do not weaken numerical gates';j=json.loads(p.stdout);assert j['status']=='PASS';print(json.dumps({'status':'LOCAL_CONSUMER_QUALIFIED','paths':j['path_count'],'probability_max_abs':j['probability_max_abs'],'metric_max_abs':j['metric_max_abs'],'source_sha256':sha(root/'code/consumer.py')}));return j
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['build','qualify']);p.add_argument('--version',default='001');p.add_argument('--root',type=Path);v=p.parse_args();build(v.version) if v.operation=='build' else qualify(v.root)
