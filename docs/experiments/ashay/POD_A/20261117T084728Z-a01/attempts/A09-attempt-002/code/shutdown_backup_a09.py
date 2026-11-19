from pathlib import Path
import hashlib,json,tarfile,datetime,os
from huggingface_hub import HfApi,hf_hub_download

RUN='20261117T084728Z-a01'
SRC=Path('/workspace/agent-handoff/POD_A')/RUN
OUT=Path('/workspace/meeting-artifacts/POD_A')/RUN/'A09-attempt-002'/'shutdown-backup-001'
REPO='ashay-sriv/undo-evo2-pilot-backup-20261020'
KEY=f'POD_A/{RUN}/A09/A09-attempt-002/shutdown-001/run-control-full-001.tar.gz'
OUT.mkdir(parents=True,exist_ok=True)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
files=[];excluded_symlinks=[]
for p in sorted(SRC.rglob('*')):
 if p.is_file():
  if p.is_symlink():excluded_symlinks.append(str(p.relative_to(SRC)));continue
  files.append({'path':str(p.relative_to(SRC)),'bytes':p.stat().st_size,'sha256':sha(p)})
extras=[Path('/workspace/meeting-artifacts/POD_A')/RUN/'A09-attempt-002'/'code',Path('/workspace/meeting-artifacts/POD_A')/RUN/'A09-attempt-002'/'report-build-005']
extra_files=[]
for root in extras:
 for p in sorted(root.rglob('*')):
  if p.is_file() and p.suffix in ['.py','.json','.md','.png','.pdf']:
   assert not p.is_symlink();extra_files.append({'path':str(p.relative_to(root.parent)),'bytes':p.stat().st_size,'sha256':sha(p)})
manifest={'schema':'pod-a-shutdown-run-control-full-v1','run_id':RUN,'control_files':files,'extra_files':extra_files,'excluded_cache_symlinks':excluded_symlinks,'control_root':str(SRC),'reason':'Shutdown supplement; original full run control including A09 regenerable caches and post-exit proof','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'Git_repository':'https://github.com/Georgakopoulos-Soares-lab/unlearning.git','Git_branch':'POD_A','Git_head_at_seal':'94ddc1ca40efe058ffdf63411c5656a33a29f85f'}
mp=OUT/'MANIFEST.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');arc=OUT/'run-control-full-001.tar.gz'
assert not arc.exists()
with tarfile.open(arc,'w:gz',compresslevel=6) as tar:
 tar.add(mp,arcname='shutdown-001/MANIFEST.json',recursive=False)
 for e in files:tar.add(SRC/e['path'],arcname='shutdown-001/control/'+e['path'],recursive=False)
 for root in extras:
  for p in sorted(root.rglob('*')):
   if p.is_file() and p.suffix in ['.py','.json','.md','.png','.pdf']:tar.add(p,arcname='shutdown-001/meeting/'+str(p.relative_to(root.parent)),recursive=False)
api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;assert not api.file_exists(REPO,KEY,repo_type='dataset')
obj=api.upload_file(path_or_fileobj=str(arc),path_in_repo=KEY,repo_id=REPO,repo_type='dataset',commit_message='Protect complete Pod A run control before pod shutdown')
remote=api.get_paths_info(REPO,[KEY],repo_type='dataset',revision=obj.oid)[0]
assert remote.size==arc.stat().st_size and remote.lfs.sha256==sha(arc)
download=Path(hf_hub_download(REPO,KEY,repo_type='dataset',revision=obj.oid,force_download=True,cache_dir=str(OUT/'fresh-cache')))
assert download.stat().st_size==arc.stat().st_size and sha(download)==sha(arc)
with tarfile.open(download) as tar:
 members=tar.getmembers();expected={'shutdown-001/MANIFEST.json'}|{'shutdown-001/control/'+e['path'] for e in files}|{'shutdown-001/meeting/'+e['path'] for e in extra_files};assert {m.name for m in members}==expected and all(m.isfile() for m in members)
 for m in members:
  if m.name=='shutdown-001/MANIFEST.json':assert hashlib.sha256(tar.extractfile(m).read()).hexdigest()==sha(mp);continue
  e=next((v for v in files if m.name=='shutdown-001/control/'+v['path']),None) or next((v for v in extra_files if m.name=='shutdown-001/meeting/'+v['path']),None)
  h=hashlib.sha256();size=0
  with tar.extractfile(m) as stream:
   while b:=stream.read(8*1024*1024):h.update(b);size+=len(b)
  assert size==e['bytes'] and h.hexdigest()==e['sha256'],m.name
result={'status':'PASS','repository':REPO,'revision':obj.oid,'path':KEY,'archive_bytes':arc.stat().st_size,'archive_sha256':sha(arc),'manifest_sha256':sha(mp),'control_files':len(files),'extra_files':len(extra_files),'all_members_fresh_verified':len(members),'private':True,'observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(OUT/'RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
