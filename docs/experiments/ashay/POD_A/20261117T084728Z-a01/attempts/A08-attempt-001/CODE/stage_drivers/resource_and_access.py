"""Read resource evidence; small unique-prefix private checkpoint access proof."""
from common import *
from huggingface_hub import HfApi,hf_hub_download
import requests
repo='ashay-sriv/undo-evo2-pilot-backup-20261020';api=HfApi();assert api.repo_info(repo,repo_type='dataset').private
if not (C/'PRIVATE_ACCESS_PROBE.json').exists():
 p=C/'PRIVATE_ACCESS_PAYLOAD.json';put(p,{'run_id':R.name,'attempt_id':C.name,'stage':'A08','observed_utc':now(),'purpose':'unique-prefix private upload/fresh-download proof; no data'})
 key=f'POD_A/{R.name}/A08/{C.name}/access-001/'+p.name;assert not api.file_exists(repo,key,repo_type='dataset');up=api.upload_file(path_or_fileobj=str(p),path_in_repo=key,repo_id=repo,repo_type='dataset',commit_message='POD_A A08 private access proof');fresh=Path(hf_hub_download(repo,key,repo_type='dataset',revision=up.oid,force_download=True,cache_dir=cfg['recovery']+'/access-001/cache'));assert sha(fresh)==sha(p);assert api.repo_info(repo,repo_type='dataset').private
 put(C/'PRIVATE_ACCESS_PROBE.json',{'status':'PASS','repository':repo,'private_at_write_and_readback':True,'revision':up.oid,'path':key,'sha256':sha(p),'bytes':p.stat().st_size,'fresh_download':True})
quota=int(Path('/sys/fs/cgroup/cpu/cpu.cfs_quota_us').read_text())/int(Path('/sys/fs/cgroup/cpu/cpu.cfs_period_us').read_text());ram=int(Path('/sys/fs/cgroup/memory/memory.limit_in_bytes').read_text());usedram=int(Path('/sys/fs/cgroup/memory/memory.usage_in_bytes').read_text());used=int((C/'WORKSPACE_USED.txt').read_text().split()[0]);persistent=None
if os.getenv('RUNPOD_API_KEY') and os.getenv('RUNPOD_POD_ID'):
 try:
  response=requests.get('https://rest.runpod.io/v1/pods/'+os.environ['RUNPOD_POD_ID'],headers={'Authorization':'Bearer '+os.environ['RUNPOD_API_KEY']},timeout=30);response.raise_for_status();info=response.json();persistent={'networkVolume':info.get('networkVolume'),'volumeInGb':info.get('volumeInGb'),'containerDiskInGb':info.get('containerDiskInGb')}
 except requests.RequestException as exc:persistent={'fresh_provider_status':'UNAVAILABLE','reason':type(exc).__name__,'existing_verified_capacity_reused':True}
prior=read(C.parent/'A06-attempt-001/RESOURCE_PREFLIGHT.json');capacity=prior['persistent']['size']*10**9
assert quota>=8 and ram-usedram>=32*1024**3 and capacity-used>=20*10**9
put(C/'RESOURCE_PREFLIGHT.json',{'status':'PASS','observed_utc':now(),'cgroup_CPU_cores':quota,'cgroup_RAM_limit_bytes':ram,'cgroup_RAM_current_bytes':usedram,'workspace_used_bytes':used,'provider_readonly_evidence':persistent,'persistent_capacity_bytes':capacity,'capacity_basis':'Existing verified provider 500GB allocation; fresh response recorded if available','conservative_remaining_bytes':capacity-used,'growth_allowance_bytes':20*10**9,'CPU_workers':2,'BLAS_threads_per_worker':4,'per_worker_RLIMIT_AS_bytes':32*1024**3,'GPU_work':0,'original_start':None,'rental_start':None,'hourly_rate':None,'cost':None,'deadline':None,'closure_reserve':None,'purchases':False})
print(json.dumps({'private_access':'PASS','CPU_cores':quota,'RAM_GB':ram/10**9,'workspace_used_GB':used/10**9,'capacity_GB':capacity/10**9}))
