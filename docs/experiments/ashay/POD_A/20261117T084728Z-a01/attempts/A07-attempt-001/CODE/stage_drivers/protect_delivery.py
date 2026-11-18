from common import *
from research_guard import guard
import tarfile,shutil,time
from huggingface_hub import HfApi,hf_hub_download,CommitOperationAdd
def main():
 guard();commit=git('rev-parse','HEAD');assert git('ls-remote','--heads','origin','POD_A').split()[0]==commit
 seal=read(C/'PUBLICATION_SEAL.json')
 for e in seal['files']:assert sha(D/e['path'])==e['sha256']
 assert sha(D/'OUTPUT_SHA256SUMS')==seal['output_manifest_sha256']
 for e in seal['files']:
  blob=subprocess.check_output(['git','-C',str(W),'show',commit+':'+str((D/e['path']).relative_to(W))])
  assert hashlib.sha256(blob).hexdigest()==e['sha256'],'Committed public bytes differ from seal'
 diff=git('diff','--name-only',cfg['research_head_before'],'HEAD').splitlines();allow=[str(D.relative_to(W)),str((BASE/'PROGRESS.md').relative_to(W)),str((BASE/'CONTROLLER_LATEST.json').relative_to(W)),str((BASE/'LATEST_A07.json').relative_to(W))]
 assert all(any(p==q or p.startswith(q+'/') for q in allow) for p in diff)
 repo='ashay-sriv/undo-evo2-pilot-backup-20261020';api=HfApi();assert api.repo_info(repo,repo_type='dataset').private
 payload=A/'delivery-build-001/A07-delivery-metadata-001';assert not payload.exists();payload.mkdir(parents=True);shutil.copytree(D,payload/'public-final');shutil.copytree(A/'stage_drivers',payload/'stage_drivers',ignore=shutil.ignore_patterns('__pycache__'))
 (payload/'run-metadata').mkdir()
 for name in ['PROGRESS.md','CONTROLLER_LATEST.json']:shutil.copyfile(BASE/name,payload/'run-metadata'/name)
 (payload/'control-final').mkdir()
 for p in C.iterdir():
  if p.is_file() and p.suffix in ['.json','.jsonl','.txt','.md','.z']:shutil.copyfile(p,payload/'control-final'/p.name)
 receipt={'schema':'pod-a-a07-delivery-receipt-v1','status':'PASS','run_id':R.name,'stage':'A07','attempt_id':C.name,'research_commit':commit,'remote_equal':True,'research_branch':'POD_A','prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'protocol_sha256':cfg['protocol_sha256'],'public_manifest_sha256':seal['output_manifest_sha256'],'public_files_verified':len(seal['files']),'scientific_checkpoint':read(C/'BACKUP_VERIFICATION.json'),'scientific_jobs':'QUIESCENT','administrative_services':{k:v for k,v in read(C/'OBSERVER_STATUS.json').items() if k.endswith('_status')},'next_state':'WAITING_FOR_APPROVAL: A08','A08_started':False,'main_index_status_other_refs_unchanged':True,'prompt_cache_worktree_unchanged':not subprocess.check_output(['git','-C','/workspace/test-prompts-push','status','--porcelain']).strip(),'delivered_utc':now(),'post_delivery_metadata_protection':'Separate immutable final metadata archive and receipt, avoiding self-hash cycles'}
 put(payload/'A07_DELIVERY_RECEIPT.json',receipt)
 files=[{'path':str(p.relative_to(payload)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(payload.rglob('*')) if p.is_file()];assert not any(p.is_symlink() for p in payload.rglob('*'));put(payload/'MEMBER_MANIFEST.json',{'files':files,'self_excluded':True});archive=A/'a07-delivery-metadata-001.tar.gz'
 with tarfile.open(archive,'w:gz',compresslevel=6) as tf:tf.add(payload,arcname=payload.name)
 ah=sha(archive);prefix=f'POD_A/{R.name}/A07/{C.name}/delivery-001';remote=prefix+'/'+archive.name;assert not api.file_exists(repo,remote,repo_type='dataset');up=api.upload_file(path_or_fileobj=str(archive),path_in_repo=remote,repo_id=repo,repo_type='dataset',commit_message='Protect final POD_A A07 delivery, progress and approval boundary');fresh=Path(hf_hub_download(repo,remote,repo_type='dataset',revision=up.oid,force_download=True,cache_dir=str(Path(cfg['recovery'])/'delivery-fresh-cache-001')));assert sha(fresh)==ah
 with tarfile.open(fresh) as tf:
  members=tf.getmembers();actual=[]
  for m in members:
   p=Path(m.name);assert not p.is_absolute() and '..' not in p.parts and p.parts[0]==payload.name and not m.issym() and not m.islnk() and (m.isdir() or m.isfile())
   if m.isfile():actual.append(str(p.relative_to(payload.name)))
  assert len(actual)==len(set(actual)) and set(actual)=={e['path'] for e in files}|{'MEMBER_MANIFEST.json'}
  for e in files:
   data=tf.extractfile(payload.name+'/'+e['path']).read();assert len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256']
 receipt.update(final_metadata_revision=up.oid,final_metadata_path=remote,final_metadata_sha256=ah,final_metadata_bytes=archive.stat().st_size,final_metadata_files_verified=len(files)+1,final_metadata_fresh_readback=True)
 receipt_path=C/'DELIVERY_RECEIPT.json';put(receipt_path,receipt);remote_receipt=prefix+'/A07_DELIVERY_RECEIPT.final.json';assert not api.file_exists(repo,remote_receipt,repo_type='dataset');up2=api.upload_file(path_or_fileobj=str(receipt_path),path_in_repo=remote_receipt,repo_id=repo,repo_type='dataset',commit_message='Anchor exact final A07 delivery and frozen coverage identities');fresh_receipt=Path(hf_hub_download(repo,remote_receipt,repo_type='dataset',revision=up2.oid,force_download=True,cache_dir=str(Path(cfg['recovery'])/'delivery-receipt-fresh-cache-001')));assert sha(fresh_receipt)==sha(receipt_path);assert api.repo_info(repo,repo_type='dataset').private;guard();assert git('ls-remote','--heads','origin','POD_A').split()[0]==commit
 put(C/'FINAL_CLOSEOUT.json',{'status':'PASS','research_commit':commit,'delivery_receipt_revision':up2.oid,'delivery_receipt_path':remote_receipt,'delivery_receipt_sha256':sha(receipt_path),'final_metadata_revision':up.oid,'science_jobs':'QUIESCENT','A08_started':False,'coverage_plan_sha256':receipt['coverage_plan_sha256'],'completed_utc':now()});shutil.copyfile(receipt_path,R/'DELIVERY_RECEIPT.json');print(json.dumps({'status':'PASS','research_commit':commit,'coverage_plan_sha256':receipt['coverage_plan_sha256'],'delivery_receipt_revision':up2.oid,'final_metadata_files_verified':len(files)+1}))
if __name__=='__main__':main()
