from pathlib import Path
import sys,json,os,hashlib
from ops import C,A,save,now
from long_run import execute
alias=sys.argv[1];stage=sys.argv[2];attempt=sys.argv[3] if len(sys.argv)>3 else '001';assert alias in {f'candidate_{i:02d}' for i in range(1,10)} and stage in ['GPU','LM','verify'];cfg=json.loads((C/'RUN_CONFIG.json').read_text());case=A/'candidates'/alias
if stage=='GPU':
 source=json.loads((C/'SOURCE_IDENTITY.json').read_text());completed=[v['alias'] for v in cfg['candidates'] if (C/(v['alias']+'-PRIVATE_RECOVERY_RECEIPT.json')).exists()];wfile=C/'COMPLETED_CASE_CAPACITY_WITNESSES.json';w=json.loads(wfile.read_text()) if wfile.exists() else {}
 for a in completed:
  if a in w:continue
  roots=[A/'candidates'/a,A/'private-checkpoints'/(a+'-other-five-001.tar.gz')]+list((A/'fresh-consumers').glob(a+'-*'));count=0;charge=0
  def add(p):
   global count,charge
   assert not p.is_symlink();s=p.lstat();count+=1;assert count<20000;charge+=max((s.st_size+4095)//4096*4096,s.st_blocks*512)
  for root in roots:
   add(root)
   if root.is_dir():
    for d,dirs,files in os.walk(root,followlinks=False):
     for n in dirs+files:add(Path(d)/n)
  assert charge<=8*1024**3,'Completed case exceeds admitted8GiB envelope; diagnose without broad scan';w[a]={'entries':count,'conservative_stat_charge_bytes':charge,'envelope_bytes':8*1024**3,'recovery_receipt_sha256':hashlib.sha256((C/(a+'-PRIVATE_RECOVERY_RECEIPT.json')).read_bytes()).hexdigest(),'immutable_after_recovery':True}
 save(wfile,w);cap=json.loads((C/'CAPACITY_ADMISSION.json').read_text());remaining=cap['usable_remaining_lower_bound_bytes'] if 'usable_remaining_lower_bound_bytes' in cap else cap['usable_remaining_lower_bound_bytes_after_owned_accounting'] if 'usable_remaining_lower_bound_bytes_after_owned_accounting' in cap else cap['usable_remaining_lower_bound_bytes'];remaining-=len(completed)*8*1024**3;assert remaining>=72*1024**3
 def memory():
  st={k:int(v) for k,v in (l.split() for l in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())};cur=int(Path('/sys/fs/cgroup/memory.current').read_text());mx=int(Path('/sys/fs/cgroup/memory.max').read_text());return {'current':cur,'maximum':mx,'headroom':mx-cur,'anon':st['anon'],'file':st['file']}
 before=memory();advised=[]
 if before['headroom']<64*1024**3:
  assert before['file']>48*1024**3,'Anonymous memory pressure; no cache-blind dispatch'
  natives=json.loads((C/'NATIVE_INPUT_BINDINGS.json').read_text())
  for a in completed:
   paths=[Path(v['path']) for v in natives[a] if v['path'].endswith('.distcp')]+list((A/'candidates'/a/'features').glob('*/*/chunk-*/features_and_lm.npz'))
   for r in (A/'fresh-consumers').glob(a+'-restored-*'):paths+=list((r/'candidate/features').glob('*/*/chunk-*/features_and_lm.npz'))
   assert len(paths)<150
   for p in paths:
    assert p.is_file() and not p.is_symlink();fd=os.open(p,os.O_RDONLY)
    try:os.posix_fadvise(fd,0,0,os.POSIX_FADV_DONTNEED)
    finally:os.close(fd)
    advised.append({'path':str(p),'bytes':p.stat().st_size,'action':'read-only POSIX_FADV_DONTNEED; no data mutation/deletion/hash'})
 after=memory();assert after['headroom']>=48*1024**3;save(C/(alias+'-DISPATCH_ADMISSION.json'),{'status':'PASS','alias':alias,'prior_completed_candidates':completed,'conservative_remaining_bytes_before_next_case':remaining,'next_case_envelope_bytes':8*1024**3,'reserve_bytes':64*1024**3,'memory_before':before,'memory_after':after,'read_only_cache_advice':advised,'initial_accounting_sha256':hashlib.sha256((C/'CAPACITY_ADMISSION.json').read_bytes()).hexdigest(),'cumulative_S05_resources_reused':True,'observed_utc':now()});env=json.loads((C/'GPU_WORKER_ENVIRONMENT.json').read_text());env['PYTHONPATH']=str(A/'code')+':'+env['PYTHONPATH'];env['CUDA_VISIBLE_DEVICES']='0';args=[cfg['runtime_python'],str(A/'code/s06_gpu.py')]
else:
 env={'PATH':str(Path(cfg['cpu_runtime_python']).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','PYTHONPATH':str(A/'code'),'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'};args=[cfg['cpu_runtime_python'],str(A/'code'/('s06_cpu.py' if stage=='LM' else 's06_verify.py'))]
execute('S06-'+stage+'-'+alias+'-'+attempt,args+['--control',str(C),'--alias',alias],env)
