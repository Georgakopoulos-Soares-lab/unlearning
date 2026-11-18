"""Portable private A04 evidence restore and CPU-only saved TRAIN qualification checks."""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,os,subprocess,sys,tarfile,time
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def safe(name):
 p=PurePosixPath(name)
 if not name or p.is_absolute() or '..' in p.parts or '\\' in name or str(p)!=name:raise ValueError('Unsafe/noncanonical archive path')
 return p
def extract(archive,destination,manifest_sha256):
 assert not destination.exists();destination.mkdir(parents=True)
 with tarfile.open(archive) as tf:
  members=tf.getmembers();seen=set();roots=set();actual=set();total=0
  for m in members:
   p=safe(m.name);assert m.name not in seen and not m.issym() and not m.islnk() and (m.isdir() or m.isfile());seen.add(m.name);roots.add(p.parts[0]);total+=m.size
   if m.isfile():
    rel='/'.join(p.parts[1:]);assert rel not in actual;actual.add(rel)
  assert len(roots)==1 and total<1024**3;root=next(iter(roots));raw=tf.extractfile(root+'/MEMBER_MANIFEST.json').read();assert hashlib.sha256(raw).hexdigest()==manifest_sha256;manifest=json.loads(raw);expected={e['path']:e for e in manifest['files']};assert len(expected)==len(manifest['files']) and actual==set(expected)|{'MEMBER_MANIFEST.json'}
  for name,e in expected.items():
   safe(name);data=tf.extractfile(root+'/'+name).read();assert len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256']
  tf.extractall(destination,filter='data')
 restored=destination/root
 for name,e in expected.items():assert (restored/name).stat().st_size==e['bytes'] and sha(restored/name)==e['sha256']
 return restored,len(actual),total
def main(args):
 from huggingface_hub import HfApi,hf_hub_download
 start=time.monotonic();backup=read(args.backup);dest=args.destination;assert dest.is_absolute() and not dest.exists();dest.mkdir(parents=True);api=HfApi();assert api.repo_info(backup['repository'],repo_type='dataset').private
 archive=Path(hf_hub_download(backup['repository'],backup['archive_path'],repo_type='dataset',revision=backup['revision'],force_download=True,cache_dir=str(dest/'new-empty-cache')));assert archive.stat().st_size==backup['archive_bytes'] and sha(archive)==backup['archive_sha256'];root,count,raw=extract(archive,dest/'consumer',backup['member_manifest_sha256']);reports=dest/'CPU-comparison';argv=[args.cpu_python,str(root/'artifacts/code/compare4.py'),'--control',str(root/'control'),'--artifacts',str(root/'artifacts'),'--report',str(reports),'--anchor-root',str(root/'anchors')];proc=subprocess.run(argv,capture_output=True,text=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONDONTWRITEBYTECODE':'1'});(dest/'CPU.stdout.json').write_text(proc.stdout);(dest/'CPU.stderr.log').write_text(proc.stderr);assert proc.returncode==0,'Fresh restored saved-TRAIN comparison failed; preserve diagnostics';out=read(reports/'SMOKE_RESULTS.json');producer=read(root/'control/numerical-reports/SMOKE_RESULTS.json');assert out==producer and out['status']=='PASS' and out['sealed_units']==6 and out['comparison_rows']==189 and not out['torch_loaded_in_CPU_verifier'];assert (reports/'SMOKE_COMPARISONS.csv').read_bytes()==(root/'control/numerical-reports/SMOKE_COMPARISONS.csv').read_bytes();assert api.repo_info(backup['repository'],repo_type='dataset').private
 proof={'schema':'pod-a-a04-fresh-evidence-restore-v1','status':'PASS','payload_revision':backup['revision'],'archive_path':backup['archive_path'],'archive_sha256':backup['archive_sha256'],'force_fresh_download':True,'new_empty_cache_and_consumer':str(dest),'all_member_files_verified':count,'uncompressed_bytes':raw,'restored_root':str(root),'safe_exact_member_set':True,'CPU_command':argv,'CPU_comparison_results_identical_to_producer':True,'CPU_comparison_CSV_identical_to_producer':True,'restored_variants':6,'comparison_rows':189,'feature_coordinates_compared':out['feature_coordinates_compared'],'LM_values_compared':out['LM_values_compared'],'actual_logit_witness_rows':len(out['actual_logit_CPU_checks']),'R3_anchor_source':'Three restored same-checkpoint TRAIN anchor bundles','only_restored_analysis_inputs_used':True,'original_producer_array_paths_used':False,'GPU_recreation_tested':False,'new_forwards_or_fits':0,'model_weights_in_this_archive':False,'weights_are_verified_immutable_mirror_dependencies':True,'private_at_read_and_closeout':True,'wall_seconds':time.monotonic()-start};put(dest/'FRESH_RESTORE_CHECK.json',proof);print(json.dumps(proof))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--backup',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--cpu-python',default='/workspace/venvs/a03-cpu-audit-20261117/bin/python');main(p.parse_args())
