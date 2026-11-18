"""Finite immutable dependency inventory; current remote identity and local all-byte checks."""
from common import *
import argparse,concurrent.futures,tarfile,time,resource
from huggingface_hub import HfApi,hf_hub_download

def safe(name):
 p=Path(name)
 if not name or p.is_absolute() or '..' in p.parts or '\\' in name or str(p)!=name:raise ValueError('Unsafe member/path')
 return p
def extract_checked(archive,destination,expected_root=None):
 destination=Path(destination);assert not destination.exists();destination.mkdir(parents=True)
 with tarfile.open(archive) as tf:
  seen=set();roots=set()
  for m in tf.getmembers():
   p=safe(m.name);assert m.name not in seen and not m.issym() and not m.islnk() and (m.isfile() or m.isdir());seen.add(m.name);roots.add(p.parts[0])
  assert len(roots)==1 and (expected_root is None or roots=={expected_root});tf.extractall(destination,filter='data')
 return destination/next(iter(roots))
def inventory():
 nodes=[];cc=lambda st:C.parent/st
 def add(label,b,root,receipt,index=None):
  nodes.append({'id':label,'kind':'archive','repository':REPO,'revision':b['revision'],'remote_path':b['archive_path'],'bytes':b['archive_bytes'],'sha256':b['archive_sha256'],'consumer_root':str(root),'member_manifest_sha256':b.get('member_manifest_sha256',b.get('checksum_manifest_self_sha256')),'prior_fresh_restore_proof':ref(receipt),'prior_restore_completed_utc':b.get('completed_utc'),'member_index':str(index) if index else None,'dependencies':[],'required_for':'Saved feature/readout analysis and provenance; excluded weights are not claimed recovered'})
 legacy=read(cc('A03-attempt-001')/'RESTORE_VALIDATION.json')['dependencies']
 for b in legacy:add('historical/'+b['dependency_id'],{'revision':b['archive_revision'],'archive_path':b['archive_path'],'archive_bytes':b['expected_bytes'],'archive_sha256':b['expected_sha256'],'member_manifest_sha256':b['checksum_manifest_self_sha256'],'completed_utc':b['completed_utc']},b['payload_root'],cc('A03-attempt-001')/('RESTORE_'+b['dependency_id']+'.json'),cc('A03-attempt-001')/('PAYLOAD_CHECKSUMS_'+b['dependency_id']+'.json'))
 for st in ['A02-attempt-001','A03-attempt-001','A04-attempt-002','A04-attempt-003','A05-attempt-001']:
  receipt=cc(st)/'BACKUP_VERIFICATION.json';b=read(receipt)
  if st.startswith('A02'):root=Path(b['local_recovery_path'])/'extracted/a02-provenance'
  elif b.get('fresh_consumer_root'):root=Path(b['fresh_consumer_root'])
  elif st.startswith('A04'):root=Path(b['restored_CPU_command'][b['restored_CPU_command'].index('--root')+1])
  else:root=Path(b['restored_CPU_command'][1]).parents[1]
  add(st,b,root,receipt)
 for stage,pattern in [('A06','BACKUP_R*.json'),('A07','BACKUP_R*.json'),('A08','BACKUP_*.json')]:
  for receipt in sorted(cc(stage+'-attempt-001').glob(pattern)):
   b=read(receipt)
   if 'archive_path' not in b:continue
   if stage=='A06':root=b['CPU_restored_checks']['root']
   elif stage=='A07':root=b['CPU_restored_checks']['new_A07_consumer']
   else:root=b['fresh_consumer_root']
   add(stage+'/'+receipt.stem.removeprefix('BACKUP_'),b,root,receipt)
 final=read(C8/'DELIVERY_RECEIPT.json');close=read(C8/'FINAL_CLOSEOUT.json');add('A08/final_metadata',{'revision':final['final_metadata_revision'],'archive_path':final['final_metadata_path'],'archive_bytes':final['final_metadata_bytes'],'archive_sha256':final['final_metadata_sha256'],'completed_utc':final['delivered_utc']},REC/'inherited-A08-metadata-fresh-001/consumer/A08-delivery-metadata-001',C8/'DELIVERY_RECEIPT.json')
 nodes.append({'id':'A08/final_delivery_receipt','kind':'object','repository':REPO,'revision':close['delivery_receipt_revision'],'remote_path':close['delivery_receipt_path'],'sha256':close['delivery_receipt_sha256'],'bytes':(C8/'DELIVERY_RECEIPT.json').stat().st_size,'local_file':str(C8/'DELIVERY_RECEIPT.json'),'prior_fresh_restore_proof':ref(C8/'FINAL_CLOSEOUT.json'),'dependencies':['A08/final_metadata'],'required_for':'Exact final A08 research commit and metadata archive binding'})
 side=read(cc('A04-attempt-003')/'PAYLOAD_RECOVERY_INDEX.json')
 for i,e in enumerate(side['assets']):nodes.append({'id':'A04/sidecar/'+str(i),'kind':'object','repository':REPO,'revision':e['revision'],'remote_path':e['remote_path'],'bytes':e['bytes'],'sha256':e['sha256'],'local_file':e['fresh_path'],'prior_fresh_restore_proof':ref(cc('A04-attempt-003')/'PAYLOAD_RECOVERY_INDEX.json'),'dependencies':[],'required_for':'Historical qualification sidecar metadata only; not native model payloads'})
 ids={n['id'] for n in nodes};assert len(ids)==len(nodes)
 for n in nodes:
  k=n['id']
  if k=='A03-attempt-001':n['dependencies']=['historical/base_R1','historical/R3','historical/controls','historical/preparation']
  elif k=='A04-attempt-002':n['dependencies']=['A03-attempt-001']
  elif k=='A04-attempt-003':n['dependencies']=['A04-attempt-002']+[s['id'] for s in nodes if s['id'].startswith('A04/sidecar/')]
  elif k=='A05-attempt-001':n['dependencies']=['A04-attempt-003']
  elif k.startswith('A06/'):n['dependencies']=['A05-attempt-001','historical/base_R1','historical/controls']
  elif k.startswith('A07/'):n['dependencies']=['A06/'+k.split('/')[1].split('_',1)[0]+'_other_five','historical/base_R1','historical/controls']
  elif k in ['A08/R4','A08/R6']:n['dependencies']=[x for x in ids if x.startswith('A07/'+k.split('/')[1]+'_')]+['A06/'+k.split('/')[1]+'_other_five']
  elif k=='A08/analysis':n['dependencies']=['A08/R4','A08/R6','A06/R4_H3','A06/R6_H3','A06/R4_other_five','A06/R6_other_five']
  elif k=='A08/final_metadata':n['dependencies']=['A08/R4','A08/R6','A08/analysis','A03-attempt-001','A04-attempt-003','A05-attempt-001']
  assert set(n['dependencies'])<=ids
 graph={'schema':'pod-a-a09-recovery-graph-v1','status':'INVENTORIED_PENDING_CURRENT_CHECKS','repository':REPO,'nodes':nodes,'roots':['A08/final_delivery_receipt'],'A09_report_dependencies':[n['id'] for n in nodes],'scientific_commit':cfg['scientific_commit'],'A08_metadata_commit':cfg['research_head_before'],'source_archives_repacked':False,'new_payload_pending':True,'GPU_weights_runtime_excluded':True,'scope':'Saved-analysis recovery, not GPU/model recreation'};put(C/'RECOVERY_DEPENDENCY_GRAPH.json',graph);return graph

def current_remote(api,node):
 info=api.get_paths_info(REPO,[node['remote_path']],repo_type='dataset',revision=node['revision'])
 assert len(info)==1 and info[0].path==node['remote_path'] and info[0].size==node['bytes'];f=info[0];lfs=f.lfs;h=(lfs.get('sha256') if isinstance(lfs,dict) else getattr(lfs,'sha256',None)) if lfs else None
 if h:assert h==node['sha256'];route='LFS_SHA256_AND_SIZE'
 else:
  p=Path(node['local_file']) if node['kind']=='object' else None
  if p and p.exists():data=p.read_bytes()
  else:data=Path(hf_hub_download(REPO,node['remote_path'],repo_type='dataset',revision=node['revision'],cache_dir=str(REC/'small-metadata-cache'))).read_bytes()
  assert hashlib.sha256(data).hexdigest()==node['sha256'];assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==f.blob_id;route='GIT_BLOB_ID_AND_LOCAL_SHA256'
 return {'status':'PASS','route':route,'remote_size':f.size,'remote_LFS_sha256':h,'remote_blob_id':f.blob_id,'checked_utc':now(),'new_payload_transfer':False}

def check_local(node):
 t=time.monotonic()
 if node['kind']=='object':
  p=Path(node['local_file']);assert p.stat().st_size==node['bytes'] and sha(p)==node['sha256'];return {'status':'PASS','files_checked':1,'bytes_hashed':p.stat().st_size,'local_path':str(p),'new_transfer':False,'seconds':time.monotonic()-t}
 root=Path(node['consumer_root']);assert root.is_dir(),str(root)
 if node.get('member_index'):
  index=Path(node['member_index']);j=read(index);entries=j['files'];check=j.get('checksum_file','CHECKSUMS.sha256');self_path=root/(check['path'] if isinstance(check,dict) else check)
  if not self_path.exists():self_path=next(root.glob('*SHA256*'),None)
  # The old all-byte receipt binds the checksum manifest's own identity.
  if self_path is not None:assert sha(self_path)==node['member_manifest_sha256']
 elif (root/'MEMBER_MANIFEST.json').exists():
  index=root/'MEMBER_MANIFEST.json';assert not node.get('member_manifest_sha256') or sha(index)==node['member_manifest_sha256'];entries=read(index)['files']
 elif (root/'PAYLOAD_MANIFEST.json').exists():
  index=root/'PAYLOAD_MANIFEST.json';raw=read(index)['files'];entries=[{'path':k,**v} for k,v in raw.items()];sums={n:h for h,n in (s.split(maxsplit=1) for s in (root/'CHECKSUMS.sha256').read_text().splitlines())};assert sha(index)==sums['PAYLOAD_MANIFEST.json']
 else:raise ValueError('No declared inherited member index: '+str(root))
 expected=set();total=0
 for e in entries:
  rel=safe(e['path']);assert str(rel) not in expected;expected.add(str(rel));p=root/rel;assert p.resolve().is_relative_to(root.resolve()) and p.is_file() and not p.is_symlink();assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],str(p);total+=e['bytes']
 return {'status':'PASS','files_checked':len(entries),'bytes_hashed':total,'consumer_root':str(root),'member_index':ref(index),'new_transfer':False,'prior_fresh_restore_proof_reused':True,'seconds':time.monotonic()-t}

def main():
 resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));t=time.monotonic();api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;quota=int(Path('/sys/fs/cgroup/cpu/cpu.cfs_quota_us').read_text())/int(Path('/sys/fs/cgroup/cpu/cpu.cfs_period_us').read_text());ram=int(Path('/sys/fs/cgroup/memory/memory.limit_in_bytes').read_text());usedram=int(Path('/sys/fs/cgroup/memory/memory.usage_in_bytes').read_text());used=int(subprocess.check_output(['du','-sb','/workspace'],text=True).split()[0]);assert quota>=8 and ram-usedram>16*1024**3 and 500000000000-used>5*1024**3
 put(C/'RESOURCE_PREFLIGHT.json',{'status':'PASS','checked_utc':now(),'CPU_cores':quota,'RAM_limit_bytes':ram,'RAM_current_bytes':usedram,'workspace_used_bytes':used,'persistent_capacity_bytes':500000000000,'capacity_basis':'Reused verified provider500GBallocation; no fresh provider availability claim','growth_allowance_bytes':5*1024**3,'workers':2,'BLAS_threads':4,'RLIMIT_AS':32*1024**3,'GPU_work':0,'original_start':None,'rental_start':None,'rate':None,'cost':None,'deadline':None,'reserve':None})
 probe=C/'PRIVATE_ACCESS_PAYLOAD.json';put(probe,{'stage':'A09','run_id':R.name,'attempt_id':C.name,'purpose':'Unique-prefix private write/fresh-read proof','utc':now()});key=f'POD_A/{R.name}/A09/{C.name}/access-001/probe.json';assert not api.file_exists(REPO,key,repo_type='dataset');up=api.upload_file(path_or_fileobj=str(probe),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='POD_A A09 private checkpoint access proof');fresh=Path(hf_hub_download(REPO,key,repo_type='dataset',revision=up.oid,force_download=True,cache_dir=str(REC/'access-fresh-cache-001')));assert sha(fresh)==sha(probe);put(C/'PRIVATE_ACCESS_PROBE.json',{'status':'PASS','private':True,'revision':up.oid,'path':key,'sha256':sha(probe),'force_fresh_read':True})
 graph=inventory();special=next(n for n in graph['nodes'] if n['id']=='A08/final_metadata');freshbase=REC/'inherited-A08-metadata-fresh-001';archive=Path(hf_hub_download(REPO,special['remote_path'],repo_type='dataset',revision=special['revision'],force_download=True,cache_dir=str(freshbase/'cache')));assert archive.stat().st_size==special['bytes'] and sha(archive)==special['sha256'];root=extract_checked(archive,freshbase/'consumer','A08-delivery-metadata-001');assert str(root)==special['consumer_root'];special['new_A09_inherited_metadata_download']=True
 results=[]
 # Metadata calls are sequential; at most two ordinary hashing workers run.
 for n in graph['nodes']:
  try:n['current_remote']=current_remote(api,n)
  except Exception as e:n['current_remote']={'status':'FAILED','error_type':type(e).__name__,'reason':str(e)[:300]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures={pool.submit(check_local,n):n for n in graph['nodes']}
  for future,n in [(f,futures[f]) for f in concurrent.futures.as_completed(futures)]:
   try:n['current_local']=future.result()
   except Exception as e:n['current_local']={'status':'FAILED','error_type':type(e).__name__,'reason':str(e)[:350]}
   results.append({'id':n['id'],'remote':n['current_remote']['status'],'local':n['current_local']['status']});put(C/'DEPENDENCY_PROGRESS.json',{'checked':len(results),'total':len(graph['nodes']),'results':results,'utc':now()})
 final_receipt=read(C8/'DELIVERY_RECEIPT.json');assert final_receipt['research_commit']==cfg['research_head_before'] and final_receipt['final_metadata_sha256']==special['sha256'];assert api.repo_info(REPO,repo_type='dataset').private
 graph['status']='PASS' if all(n['current_local']['status']==n['current_remote']['status']=='PASS' for n in graph['nodes']) else 'PARTIAL';graph['verification_wall_seconds']=time.monotonic()-t;graph['verification_CPU_seconds']=time.process_time();graph['bytes_rehashed']=sum(n['current_local'].get('bytes_hashed',0) for n in graph['nodes']);graph['inherited_new_transfer_bytes']=special['bytes'];graph['private_at_read_write_closeout']=True;graph['verified_utc']=now();put(C/'RECOVERY_DEPENDENCY_GRAPH.json',graph);print(json.dumps({'status':graph['status'],'nodes':len(graph['nodes']),'bytes_rehashed':graph['bytes_rehashed'],'new_transfer_bytes':special['bytes'],'failures':[r for r in results if r['remote']!='PASS' or r['local']!='PASS']}),flush=True)
if __name__=='__main__':main()
