"""New private A09 aggregate payload; immutable sources, code and finite fresh recovery."""
from common9 import *
from huggingface_hub import HfApi
import shutil,tarfile,time,re

def copy(src,dst):
 src=Path(src);dst=Path(dst);assert src.is_file() and not src.is_symlink();dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(src)==sha(dst)

def archive(root,path):
 files=[]
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():
   assert p.suffix not in ['.npz','.npy','.joblib','.pt','.distcp','.bin']
   assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----)',p.read_bytes()),str(p)
   files.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)})
 assert not (root/'MEMBER_MANIFEST.json').exists();put(root/'MEMBER_MANIFEST.json',{'schema':'pod-a-safe-regular-members-v1','self_excluded':True,'files':files})
 with tarfile.open(path,'x:gz',compresslevel=6) as out:
  for p in sorted(root.rglob('*')):
   if p.is_file():out.add(p,arcname=str(Path(root.name)/p.relative_to(root)),recursive=False)
 return {'archive_bytes':path.stat().st_size,'archive_sha256':sha(path),'member_manifest_sha256':sha(root/'MEMBER_MANIFEST.json'),'members':len(files)+1}

def main():
 guard();start=time.monotonic();assert not (C/'REPORT_PAYLOAD_UPLOADED.json').exists()
 for name in ['COUNT_EVIDENCE.json','PUBLICATION_JOIN_VALIDATION.json','IMPLEMENTATION_VALIDATION.json','FIGURE_VALIDATION.json','REPORT_RENDER_VALIDATION.json']:
  assert read(C/name)['status'].startswith('PASS'),name
 assert sha(D/'REPORT.pdf')==read(C/'REPORT_RENDER_VALIDATION.json')['REPORT_pdf_sha256']
 api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private
 # Freeze the actual consumer before any fresh-consumer outcomes.
 identity={'status':'FROZEN_BEFORE_EXECUTION','observed_utc':now(),'sources':[{ 'path':p.name,'sha256':sha(p)} for p in sorted((A/'code').glob('*.py'))],'environment':read(C/'ENVIRONMENT_CHECK.json'),'recovery_panel':read(C/'A09_EXECUTION_MANIFEST.json'),'producer_denial':'open/listdir/scandir audit hook; required rejected sentinel; no producer PYTHONPATH','tolerances':{'probability_abs':1e-10,'point_draw_CI_abs':1e-12,'rtol':0}}
 put(C/'FROZEN_RECOVERY_IMPLEMENTATION.json',identity);publish('FROZEN_RECOVERY_IMPLEMENTATION.json',identity)
 for p in (A/'code').glob('*.py'):publish('code/'+p.name,p.read_bytes())
 build=A/'report-payload-build-001';assert not build.exists();root=build/'A09-report-payload-001';root.mkdir(parents=True)
 for p in D.rglob('*'):
  if p.is_file():copy(p,root/'public'/p.relative_to(D))
 for p in (A/'code').glob('*.py'):copy(p,root/'code'/p.name)
 excluded={'ORIGINAL_ROWS.json','CANONICAL_ROWS.json'}
 for p in C.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded:copy(p,root/'control'/p.relative_to(C))
 copy(D5/'TABLE_KEY_DESIGN.json',root/'immutable-design/TABLE_KEY_DESIGN.json')
 source_files={}
 for e in read(D/'SOURCE_TABLE_INDEX.json')['sources']:
  src=W/e['path'];assert sha(src)==e['sha256'] and src.stat().st_size==e['bytes'];member='immutable-sources/'+e['source_id']+'.csv';copy(src,root/member);source_files[e['source_id']]={'member':member,'sha256':e['sha256'],'original_path':e['path'],'commit':e['commit']}
 assert len(source_files)==127;put(root/'IMMUTABLE_SOURCE_FILES.json',{'files':source_files})
 for p in (A/'prior-proof-snapshots').glob('*'):copy(p,root/'prior-proof-snapshots'/p.name)
 for p in (A/'logs').glob('*'):
  if p.is_file():copy(p,root/'diagnostics/logs'/p.name)
 for p in A.glob('*.txt'):copy(p,root/'diagnostics/source-versions'/p.name)
 copy(R/'APPROVAL_LOG.jsonl',root/'approval-log-snapshot.jsonl')
 for name in cfg['allowed_root_files']:
  if (B/name).is_file():copy(B/name,root/'run-root-at-payload-seal'/name)
 put(root/'PAYLOAD_SCOPE.json',{'stage':'A09','report_inputs_complete':True,'unchanged_scientific_payloads_referenced_not_repacked':True,'excluded_regenerable_local_caches':sorted(excluded),'scientific_original_sources':127,'report_final_metadata_follows_separately':True,'new_fits_forwards_draws':0,'sealed_utc':now()})
 path=build/'A09-report-payload-001.tar.gz';obj=archive(root,path);key=f'POD_A/{R.name}/A09/{C.name}/report-001/'+path.name;assert not api.file_exists(REPO,key,repo_type='dataset');u=api.upload_file(path_or_fileobj=str(path),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect A09 complete aggregate report and finite recovery implementation');obj.update(repository=REPO,revision=u.oid,archive_path=key)
 receipt={'status':'UPLOADED_PENDING_FRESH_RESTORE','report_payload':obj,'local_archive':str(path),'local_build':str(root),'build_upload_wall_seconds':time.monotonic()-start,'uploaded_utc':now()};put(C/'REPORT_PAYLOAD_UPLOADED.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':main()
