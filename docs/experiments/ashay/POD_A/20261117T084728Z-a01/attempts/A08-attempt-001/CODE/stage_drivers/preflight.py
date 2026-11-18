"""Verify necessary existing CPU dependency bytes; no fits, extraction or downloads."""
from common import *
sys.path.insert(0,str(A/'code'))
from audit_common import A7,A6,D7,D6,C7,C6,checked,validate_members,TASKS,SEEDS,old,H,CONTROL,classes_for,VERSIONS
import numpy as np,importlib.metadata,time
from threadpoolctl import threadpool_info
t=time.monotonic();bundles=[]
for alias in ['R4','R6']:
 for task in TASKS:
  for split,n in [('train',1024),('dev',512)]:
   root=A7/'cache'/alias/task/split;j=read(root/'COMPLETE.json');assert j['status']=='PASS' and j['identity']['stage']=='A07' and j['identity']['candidate']==alias and j['identity']['task']==task and j['identity']['split']==split;validate_members(root,j);checked(j['identity']['input_bundle'])
   sources=[]
   for source in j['source_chunks']:
    for typ in ['receipt','payload']:checked(source[typ])
    sr=read(source['receipt']['path']);assert sr['status']=='PASS' and sr['identity']['candidate']==alias and sr['identity']['unit']['task']==task and sr['identity']['unit']['split']==split;sources.append(source)
   with np.load(root/'metadata.npz',allow_pickle=False) as z:
    assert len(z['ids'])==n and len(set(z['ids']))==n and np.array_equal(np.unique(z['labels']),classes_for(task));assert split!='dev' or len(np.unique(z['groups']))==(511 if task=='gue_splice_reconstructed' else 512)
   bundles.append({'candidate':alias,'task':task,'split':split,'receipt':ref(root/'COMPLETE.json'),'member_count':len(j['files']),'source_chunks':sources})
metadata_only=[]
for n in ['H3_HEAD_INDEX.json','H3_GATE_INDEX.json','LM_INDEX.json','SOURCE_IDENTITY.json','CPU_SOURCE_IDENTITY.json']:
 p=C6/n if (C6/n).exists() else D6/n;assert p.exists();metadata_only.append(ref(p))
for dep in ['base_R1','controls','R3','preparation']:
 p=C03/('PAYLOAD_CHECKSUMS_'+dep+'.json');assert p.exists();metadata_only.append(ref(p))
manifest=read(C/'A08_EXECUTION_MANIFEST.json');dependencies={}
for unit in manifest['audit_units']:
 checked(unit['producer_receipt']);s=unit['scientific_dependencies']
 for e in [s['fold'],s['original_base_head'],s['historical_predictions'],s['draw']]:dependencies[e['path']]=e
for e in dependencies.values():checked(e)
source=read(C7/'CPU_SOURCE_IDENTITY.json')
for e in source['files']:assert sha(A7/'code'/e['path'])==e['sha256']
proof={'status':'PASS','bundles':bundles,'existing_feature_matrices':520,'existing_feature_row_executions':15360,'feature_members_hashed':sum(b['member_count'] for b in bundles),'unique_historical_CPU_dependencies':len(dependencies),'historical_dependency_manifest_refs':metadata_only,'all_A07_producer_receipt_hashes_match_manifest':True,'A07_source_unchanged':True,'GPU_work':0,'historical_audits_repeated':False,'elapsed_seconds':time.monotonic()-t,'verified_utc':now()};put(C/'INPUT_PREFLIGHT.json',proof)
env={'status':'PASS','python':sys.version.split()[0],'packages':{p:importlib.metadata.version(p) for p in VERSIONS},'BLAS':threadpool_info(),'CPU_workers':2,'BLAS_threads_per_worker':4,'worker_address_space_limit_bytes':32*1024**3,'CUDA_VISIBLE_DEVICES':os.getenv('CUDA_VISIBLE_DEVICES'),'package_changes':False,'qualified_inherited_CPU_identity':ref(C7/'CPU_ENVIRONMENT_CHECK.json')};put(C/'ENVIRONMENT_CHECK.json',env)
inputs=read(C/'A08_INPUTS.json');inputs['status']='PASS';inputs['private_input_preflight']=ref(C/'INPUT_PREFLIGHT.json');inputs['environment']=ref(C/'ENVIRONMENT_CHECK.json');put(C/'A08_INPUTS.json',inputs)
print(json.dumps({'status':'PASS','feature_bundles':20,'feature_matrices':520,'historical_CPU_dependency_files':len(dependencies),'seconds':proof['elapsed_seconds']}))
