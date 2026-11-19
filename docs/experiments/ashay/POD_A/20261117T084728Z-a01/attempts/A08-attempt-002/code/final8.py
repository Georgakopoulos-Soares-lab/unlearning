"""Two-commit delivery, fresh metadata regeneration and separate final receipt."""
from common8 import *
from finish8 import quiet,seal,NEXT,STATUS
from delivery8 import deliver
from archive8 import safe_extract
from huggingface_hub import HfApi,hf_hub_download
import csv,shutil,tarfile,time,re,importlib.util,gzip,io,zipfile

def csvrows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def registry(root):
 j=read(root/'PRIVATE_PROVENANCE_MAP.json');out={}
 if not j.get('partitioned'):return j['artifacts']
 for shard in j['shards']:
  p=root/shard['path'];assert sha(p)==shard['sha256'];entries=read(p)['artifacts'];assert len(entries)==shard['entries'] and not set(entries)&set(out);out.update(entries)
 assert len(out)==j['entries'];return out

def public_proof():
 guard(dirty=False);head=git('rev-parse','HEAD');assert git('ls-remote','--heads','origin','POD_A').split()[0]==head;s=read(C/'PUBLICATION_SEAL.json');assert sha(D/'OUTPUT_SHA256SUMS')==s['manifest_sha256']
 for e in s['files']:
  p=D/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'] and gitb('show',head+':'+str(p.relative_to(W)))==p.read_bytes()
 for e in s['root_entrypoints']:
  p=B/e['path'];assert sha(p)==e['sha256'] and gitb('show',head+':'+str(p.relative_to(W)))==p.read_bytes()
 assert gitb('show',head+':'+str((D/'OUTPUT_SHA256SUMS').relative_to(W)))==(D/'OUTPUT_SHA256SUMS').read_bytes();assert all(owned(p) for p in git('diff','--name-only',cfg['research_head_before'],head).splitlines());return {'status':'PASS','commit':head,'remote_equal':True,'all_current_owned_committed_bytes_verified':True,'public_files_including_manifest':len(s['files'])+1,'manifest_sha256':s['manifest_sha256'],'prior_attempt_trees_main_index_status_other_refs_unchanged':True,'observed_utc':now()}

def metadata_commit():
 proof=public_proof();assert proof['commit']==read(C/'SCIENTIFIC_DELIVERY.json')['commit'];publish('METADATA_POST_PUSH_PROOF.json',proof);publish('DELIVERY_IDENTITY_CHAIN.json',{'scientific_commit':proof['commit'],'metadata_commit':'Recorded in separate returned Git delivery/private final receipt; never self-hashed','private_repository':REPO,'final_metadata_path':f'POD_A/{R.name}/A08/{C.name}/delivery-001/A08-R5-final-metadata-001.tar.gz','final_receipt_path':f'POD_A/{R.name}/A08/{C.name}/delivery-001/A08_R5_DELIVERY_RECEIPT.final.json','exact_final_receipt_revision':'Separate FINAL_CLOSEOUT.json and final response; no future/self-reference','A09_started':False,'next_state':NEXT});seal();r=deliver('A08 R5: bind exact scientific commit and final metadata readiness');put(C/'METADATA_DELIVERY.json',r);return r

def selector_validation():
 guard();entries=registry(D);mapping=read(C/'DESCRIPTOR_MEMBER_INDICES.json');checked_schemas={};count=0;files=0
 for d in entries.values():
  selector=d.get('array_selector')
  if not selector or not d.get('member','').endswith('.npz'):continue
  node=mapping['archives'][d['archive_sha256']];p=Path(node['consumer_root'])/d['member'];key=d['sha256']
  if key not in checked_schemas:
   assert sha(p)==key and p.stat().st_size==d['bytes']
   with zipfile.ZipFile(p) as z:names={n.removesuffix('.npy') for n in z.namelist()};assert all(n.endswith('.npy') for n in z.namelist())
   checked_schemas[key]=names;files+=1
  names=selector if isinstance(selector,list) else selector.split(',');assert set(names)<=checked_schemas[key],(d['member'],selector);count+=len(names)
 out={'status':'PASS','NPZ_file_schemas_hash_verified':files,'literal_array_selectors_checked':count,'no_placeholder_or_wrong_member_selector':True,'no_prediction_feature_loss_values_recalculated':True};put(C/'ARRAY_SELECTOR_VALIDATION.json',out);publish('ARRAY_SELECTOR_VALIDATION.json',out);return out

def regenerate(restored):
 sys.dont_write_bytecode=True;pub=restored/'public-final';spec=importlib.util.spec_from_file_location('fresh_A08_keys',restored/'code/key_contract5.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);expected={r['logical_id'] for r in module.table_keys(read(restored/'immutable-A05/TABLE_KEY_DESIGN.json'),cfg['coverage_plan_sha256'])};manifest=read(pub/'TABLE_PARTITIONS.json');actual=[];science={};new_science=[]
 for part in manifest['shards']:
  p=pub/part['path'];assert p.stat().st_size==part['bytes'] and p.stat().st_size<10*1024**2 and sha(p)==part['sha256'];rows=csvrows(p);assert len(rows)==part['rows'] and list(rows[0])==part['fields'];assert digest([r['logical_id'] for r in rows])==part['logical_id_sha256']
  for r in rows:actual.append(r['logical_id']);science[r['logical_id']]=r;new_science.append(r)
 for name in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv','LM_RESULTS.csv']:
  for r in csvrows(restored/'immutable-A06'/name):actual.append(r['logical_id']);science[r['logical_id']]=r
 assert len(actual)==len(set(actual))==33684 and set(actual)==expected
 # Original producer values AND status/lineage fields are preserved in A08 overlays.
 oldcount=0
 for name in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv']:
  for old in csvrows(restored/'immutable-A07'/name):
   row=science[old['logical_id']];assert all(row[k]==v for k,v in old.items());assert row['A08_release_status']=='VERIFIED';oldcount+=1
 assert oldcount==12300
 descriptors=registry(pub);indices=read(restored/'control/DESCRIPTOR_MEMBER_INDICES.json');git_blobs=read(restored/'GIT_DESCRIPTOR_BLOBS.json')['blobs'];joins=0
 for identity,d in descriptors.items():
  assert digest(d)==identity
  if d.get('storage_kind','IMMUTABLE_ARCHIVE_MEMBER')=='GIT_BLOB':
   e=git_blobs[d['commit']+':'+d['path']];p=restored/e['private_member'];assert sha(p)==d['sha256'] and p.stat().st_size==d['bytes']
  else:
   e=indices['member_indices'][d['archive_sha256']][d['member']];n=indices['archives'][d['archive_sha256']];assert e['sha256']==d['sha256'] and e['bytes']==d['bytes'] and all(d[k]==n[k] for k in ['repository','revision','archive_path'])
 rows_to_check=list(new_science)+csvrows(pub/'RELEASE_OVERLAY.csv')+csvrows(pub/'SCIENTIFIC_INPUT_BINDINGS.csv')
 for task in TASKS:rows_to_check.extend(csvrows(pub/('metadata/reference_cache_'+task+'.csv')))
 for r in rows_to_check:
  for field,value in r.items():
   if field.endswith('_locator') and value:
    prefix=field[:-8];d=descriptors[value.removeprefix('provenance:')];assert d['sha256']==r[prefix+'_sha256'] and d['hash_kind']==r[prefix+'_hash_kind'];joins+=1
 # Rebuild profile point identities from the exact immutable aggregate input snapshots.
 point_sources={};sourceinfo=read(restored/'PLOT_INPUT_SNAPSHOTS.json')['sources']
 for e in sourceinfo:
  path=restored/e['private_member'];assert sha(path)==e['sha256'];rs=csvrows(path)
  for ordinal,r in enumerate(rs,2):
   identity=r.get('logical_id') or 'historical:'+digest({k:r.get(k) for k in ['original_endpoint_id','checkpoint_alias','task','split','representation','CV_seed','policy','metric','protocol_sha256']});point_sources[identity]=(r,e['sha256'],ordinal)
 assert len(point_sources)==32760;profile_rows=0
 for task in TASKS:
  for r in csvrows(pub/('plot_data/points_'+task+'.csv')):
   source,h,line=point_sources[r['point_id']];assert r['source_sha256']==h and int(r['source_CSV_line'])==line;assert all(r[k]==source[k] for k in ['checkpoint_alias','task','split','representation','CV_seed','policy','metric','estimate']);profile_rows+=1
 assert profile_rows==32760;plotted=0;manifest_fig=read(pub/'FIGURE_MANIFEST.json');inclusion={(r['candidate'],r['task']):r for r in csvrows(pub/'INCLUSION_EXPOSURE_PLAN.csv')};coverage=csvrows(pub/'COVERAGE.csv')
 for fig in manifest_fig['figures']:
  dr=fig['plot_data'];assert sha(pub/dr['path'])==dr['sha256'];rows=csvrows(pub/dr['path']);assert len(rows)==dr['rows']
  for r in rows:
   if r.get('source_key'):
    original=point_sources[r['source_key']][0];assert float(r['estimate'])==float(original['estimate']);assert r['task']==original['task'] and r['policy']==original['policy'] and r['split']==original['split'] and r['representation']==original['representation'] and r['CV_seed']==str(original['CV_seed'])
   elif r.get('logical_id'):
    original=science[r['logical_id']]
    for k in ['estimate','ci_low','ci_high']:assert float(r[k])==float(original[k])
    for k in ['task','split','policy','metric','representation','CV_seed']:
     if r.get(k):assert r[k]==str(original[k])
   elif r.get('planned_heads'):
    n=sum(v['candidate']==r['checkpoint_alias'] and v['task']==r['task'] and v['kind']=='final_head' and v['independently_released']=='True' for v in coverage);assert n==int(r['released_heads']) and int(r['planned_heads'])==78
   elif r.get('declaration_state'):
    inc=inclusion.get((r['checkpoint_alias'],r['task']));value='Unknown / not delivered' if inc is None or r['checkpoint_alias']=='R2' else {'true':'Declared in supplied config','false':'Not declared in supplied config'}.get(inc['observed_selected_config_declares_family'].lower(),'Unknown / not delivered');assert r['declaration_state']==value and r['realized_exposure']=='UNKNOWN'
   else:raise AssertionError('Unmapped plot datum')
   plotted+=1
 assert {str(p.relative_to(restored)) for p in restored.rglob('*') if p.is_file()}=={e['path'] for e in read(restored/'MEMBER_MANIFEST.json')['files']}|{'MEMBER_MANIFEST.json'}
 return {'status':'PASS','amendment_keys_regenerated':33684,'original_A07_rows_preserved':12300,'typed_descriptors_verified':len(descriptors),'row_locator_hash_kind_joins':joins,'profile_points_regenerated':32760,'plotted_source_rows_verified':plotted,'figure_families':len(manifest_fig['figures']),'models_or_audits_refits_repeated':0}

def protect():
 no_science_imports();api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;proof=public_proof();state=quiet();back=read(C/'BACKUP_VERIFICATION.json');assert back['status']=='PASS';remote=[]
 for b in back['checkpoints']:
  obj=api.get_paths_info(REPO,[b['archive_path']],repo_type='dataset',revision=b['revision'])[0];assert obj.size==b['archive_bytes'] and obj.lfs.sha256==b['archive_sha256'];remote.append({'label':b['label'],'revision':b['revision'],'path':b['archive_path'],'sha256':b['archive_sha256'],'bytes':b['archive_bytes'],'remote_LFS_identity':'PASS','prior_fresh_file_and_computational_recovery_reused':True})
 root=A/'final-metadata-build-001/A08-R5-final-metadata-001';assert not root.exists();root.mkdir(parents=True);shutil.copytree(D,root/'public-final');shutil.copytree(A/'code',root/'code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(A/'logs',root/'logs',ignore=shutil.ignore_patterns('final-protect*'));shutil.copytree(C/'package',root/'prompt-package');shutil.copytree(C/'jobs',root/'control/jobs');shutil.copytree(C/'prior-run-root',root/'prior-run-root');(root/'run-root-current').mkdir();shutil.copyfile(R/'APPROVAL_LOG.jsonl',root/'ROOT_APPROVAL_LOG.jsonl');put(root/'ROOT_CONTROLLER_SNAPSHOT.json',read(R/'CONTROLLER_STATE.json'))
 for p in C.iterdir():
  if p.is_file() and p.suffix in ['.json','.jsonl','.md','.txt','.z','.patch','.gz']:shutil.copyfile(p,root/'control'/p.name)
 for name in cfg['allowed_root_files']:shutil.copyfile(B/name,root/'run-root-current'/name)
 (root/'immutable-A05').mkdir()
 for name in ['TABLE_KEY_DESIGN.json','AUDIT_PLAN.json','RESULT_SCHEMAS.json','COVERAGE_PLAN.json','EFFECTIVE_INPUTS.json','RECOVERY_DEPENDENCY_GRAPH.json','R3_COMPARABILITY.json','INCLUSION_EXPOSURE_PLAN.csv']:shutil.copyfile(D5/name,root/'immutable-A05'/name)
 (root/'immutable-A06').mkdir()
 for name in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv','LM_RESULTS.csv','PRIVATE_PROVENANCE_MAP.json']:shutil.copyfile(D6/name,root/'immutable-A06'/name)
 (root/'immutable-A07').mkdir()
 for name in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv']:shutil.copyfile(D7/name,root/'immutable-A07'/name)
 (root/'immutable-history').mkdir();shutil.copyfile(D80/'VERIFIED_METRICS.csv',root/'immutable-history/VERIFIED_METRICS.csv');snapshots=[]
 for src,member in [(D80/'VERIFIED_METRICS.csv','immutable-history/VERIFIED_METRICS.csv'),(D6/'RESULTS_LONG.csv','immutable-A06/RESULTS_LONG.csv'),(D7/'RESULTS_LONG.csv','immutable-A07/RESULTS_LONG.csv')]:snapshots.append({'source_path':str(src.relative_to(W)),'source_commit':cfg['research_head_before'],'sha256':sha(src),'private_member':member})
 put(root/'PLOT_INPUT_SNAPSHOTS.json',{'sources':snapshots,'scope':'Only immutable sanitized aggregate inputs necessary for deterministic plot-data regeneration; no history feature/head/weight repack'})
 descriptors=registry(D);blobs={}
 for d in descriptors.values():
  if d.get('storage_kind')!='GIT_BLOB':continue
  key=d['commit']+':'+d['path']
  if key in blobs:continue
  data=gitb('show',key);assert bh(data)==d['sha256'] and len(data)==d['bytes'];member='git-descriptor-blobs/'+d['sha256'];target=root/member;target.parent.mkdir(exist_ok=True);target.write_bytes(data);blobs[key]={'private_member':member,'sha256':d['sha256'],'bytes':d['bytes']}
 put(root/'GIT_DESCRIPTOR_BLOBS.json',{'blobs':blobs});put(root/'POST_PUSH_PROOF.json',proof);put(root/'SCIENTIFIC_PAYLOAD_REMOTE_READBACK.json',{'status':'PASS','objects':remote,'science_repacked':False});put(root/'PROCESS_STATE_AT_PROTECTION.json',state);files=[]
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():
   assert p.suffix not in ['.npz','.npy','.joblib','.distcp','.pt','.bin'];data=p.read_bytes();assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----)',data);files.append({'path':str(p.relative_to(root)),'bytes':len(data),'sha256':bh(data)})
 put(root/'MEMBER_MANIFEST.json',{'files':files,'self_excluded':True,'scope':'Final exact code/logs/control/public reports/figures and required immutable aggregate inputs only; nine scientific payloads remain separate'});archive=A/'A08-R5-final-metadata-001.tar.gz';assert not archive.exists();t=time.monotonic()
 with tarfile.open(archive,'w:gz',compresslevel=6) as tf:
  for p in sorted(root.rglob('*')):
   if p.is_file():tf.add(p,arcname=root.name+'/'+str(p.relative_to(root)),recursive=False)
 comp=time.monotonic()-t;h=sha(archive);key=f'POD_A/{R.name}/A08/{C.name}/delivery-001/'+archive.name;assert not api.file_exists(REPO,key,repo_type='dataset');t=time.monotonic();u=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect complete R5 A08 release, analysis, figures and exact metadata');upload=time.monotonic()-t;put(C/'FINAL_METADATA_UPLOADED.json',{'revision':u.oid,'path':key,'sha256':h,'bytes':archive.stat().st_size});freshbase=REC/'final-metadata-fresh-001';assert not freshbase.exists();freshbase.mkdir();t=time.monotonic();fresh=Path(hf_hub_download(REPO,key,repo_type='dataset',revision=u.oid,force_download=True,cache_dir=str(freshbase/'new-cache')));assert sha(fresh)==h and fresh.stat().st_size==archive.stat().st_size;num,hashsec=safe_extract(fresh,freshbase/'consumer');assert num==len(files)+1;restored=freshbase/'consumer';rebuilt=regenerate(restored)
 for p in (restored/'public-final').rglob('*'):
  if p.is_file():assert gitb('show',proof['commit']+':'+str((D/p.relative_to(restored/'public-final')).relative_to(W)))==p.read_bytes()
 assert public_proof()['commit']==proof['commit'] and api.repo_info(REPO,repo_type='dataset').private;after=quiet();meta={'status':'PASS','repository':REPO,'revision':u.oid,'archive_path':key,'archive_bytes':archive.stat().st_size,'archive_sha256':h,'member_manifest_sha256':sha(root/'MEMBER_MANIFEST.json'),'all_members_fresh_verified':num,'fresh_consumer':str(restored),'regenerated_keys_provenance_and_plot_data':rebuilt,'exact_public_commit':proof['commit'],'compression_seconds':comp,'upload_seconds':upload,'fresh_download_and_validation_seconds':time.monotonic()-t,'all_member_hash_seconds':hashsec,'scientific_payloads_repacked':False};receipt={'schema':'pod-a-R5-A08-final-delivery-v2','status':'PASS','stage_status':STATUS,'full_project_and_A04_status':'PARTIAL','run_id':cfg['run_id'],'attempt_id':C.name,'prompt_commit':cfg['prompt_commit'],'prompt_sha256':cfg['A08_prompt_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'audit_source_sha256':sha(C/'SOURCE_IDENTITY.json'),'contrast_source_sha256':sha(C/'CONTRAST_SOURCE_IDENTITY.json'),'scientific_delivery_commit':read(C/'SCIENTIFIC_DELIVERY.json')['commit'],'metadata_delivery_commit':proof['commit'],'public_proof':proof,'scientific_checkpoints':back,'final_metadata':meta,'stage_science_receipt':read(C/'A08_RECEIPT.json'),'processes':after,'observer':'STOPPED','pod_left_running':True,'A09_started':False,'time_policy':cfg['time_policy'],'next_state':NEXT,'receipt_revision_binding':'Returned immutable revision is recorded outside these bytes in FINAL_CLOSEOUT.json','completed_utc':now()};put(C/'DELIVERY_RECEIPT.json',receipt);rkey=f'POD_A/{R.name}/A08/{C.name}/delivery-001/A08_R5_DELIVERY_RECEIPT.final.json';assert not api.file_exists(REPO,rkey,repo_type='dataset');ur=api.upload_file(path_or_fileobj=str(C/'DELIVERY_RECEIPT.json'),path_in_repo=rkey,repo_id=REPO,repo_type='dataset',commit_message='Bind exact verified R5 A08 final delivery; stop before A09');fr=Path(hf_hub_download(REPO,rkey,repo_type='dataset',revision=ur.oid,force_download=True,cache_dir=str(REC/'final-receipt-fresh-cache')));assert fr.read_bytes()==(C/'DELIVERY_RECEIPT.json').read_bytes() and api.repo_info(REPO,repo_type='dataset').private;assert public_proof()['commit']==proof['commit'];final={'schema':'pod-a-R5-A08-final-closeout-v2','status':'PASS','stage_status':STATUS,'full_project_and_A04_status':'PARTIAL','prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'audit_source_sha256':sha(C/'SOURCE_IDENTITY.json'),'contrast_source_sha256':sha(C/'CONTRAST_SOURCE_IDENTITY.json'),'scientific_delivery_commit':receipt['scientific_delivery_commit'],'metadata_delivery_commit':proof['commit'],'scientific_checkpoint_refs':[{'label':b['label'],'revision':b['revision'],'path':b['archive_path'],'sha256':b['archive_sha256']} for b in back['checkpoints']],'final_metadata_revision':u.oid,'final_metadata_path':key,'final_metadata_sha256':h,'final_metadata_members_verified':num,'receipt_revision':ur.oid,'receipt_path':rkey,'receipt_sha256':sha(C/'DELIVERY_RECEIPT.json'),'receipt_fresh_readback':'PASS','regeneration':rebuilt,'all_prior_attempts_unchanged':True,'owned_jobs_quiet':True,'observer':'STOPPED','pod_left_running':True,'A09_started':False,'next_state':NEXT,'completed_utc':now()};put(C/'FINAL_CLOSEOUT.json',final);put(C/'FINAL_GIT_BYTE_PROOF.json',proof)
 for name in ['FINAL_CLOSEOUT.json','DELIVERY_RECEIPT.json']:put(R/name,read(C/name))
 for name in ['REMOTE_HANDOFF.json','RESUME_MANIFEST.json']:put(R/name,read(D/name)|{'final_closeout':final})
 md(R/'SESSION_HANDOFF.md',(D/'SESSION_HANDOFF.md').read_text());put(R/'CONTROLLER_STATE.json',read(D/'REMOTE_HANDOFF.json')|{'stage':'A08','attempt_id':C.name,'status':STATUS,'final_closeout':final,'automatic_resume':False,'next_state':NEXT});print(json.dumps(final))

def postexit():
 no_science_imports();proof=public_proof();final=read(C/'FINAL_CLOSEOUT.json');assert final['status']=='PASS' and final['metadata_delivery_commit']==proof['commit'];state=quiet();parsed={'JSON':0,'CSV':0,'JSONL':0,'gzip':0};nonempty=0
 for p in D.rglob('*'):
  if not p.is_file():continue
  assert p.stat().st_size>0 and not p.is_symlink();nonempty+=1
  if p.suffix=='.json':read(p);parsed['JSON']+=1
  elif p.suffix=='.csv':assert csvrows(p);assert p.stat().st_size<10*1024**2;parsed['CSV']+=1
  elif p.suffix=='.jsonl':
   for line in p.read_text().splitlines():json.loads(line)
   parsed['JSONL']+=1
  elif p.suffix=='.gz':assert gzip.decompress(p.read_bytes());parsed['gzip']+=1
 for name in ['SOURCE_IDENTITY.json','CONTRAST_SOURCE_IDENTITY.json']:
  for e in read(C/name)['files']:assert sha(A/'code'/e['path'])==e['sha256']
 record={'status':'PASS','stage_status':STATUS,'public_proof':proof,'public_nonempty_files':nonempty,'parse_counts':parsed,'frozen_numerical_sources_unchanged':True,'processes':state,'observer':'STOPPED','pod_left_running':True,'A09_started':False,'receipt_revision':final['receipt_revision'],'receipt_sha256':final['receipt_sha256'],'next_state':NEXT,'observed_utc':now()};put(C/'POST_EXIT_CHECK.json',record);print(json.dumps({k:record[k] for k in ['status','stage_status','public_nonempty_files','receipt_revision','next_state']}))

if __name__=='__main__':
 if sys.argv[1:]==['metadata-commit']:print(json.dumps(metadata_commit()))
 elif sys.argv[1:]==['selectors']:print(json.dumps(selector_validation()))
 elif sys.argv[1:]==['postexit']:postexit()
 else:protect()
