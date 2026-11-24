"""One finite candidate/task CPU stage, two immutable 39-selector workers."""
from pathlib import Path
import sys,json,hashlib,fcntl,resource,time
from concurrent.futures import ThreadPoolExecutor
from ops import C,A,save,now
from long_run import execute
cfg=json.loads((C/'RUN_CONFIG.json').read_text());a,t=sys.argv[1:];assert a in {v['alias'] for v in cfg['candidates']} and t in cfg['tasks'];dest=A/'candidates'/a/'groups';dest.mkdir(parents=True,exist_ok=True);seal=dest/(t+'.json')
if seal.exists():assert json.loads(seal.read_text())['status']=='PASS';print('S08_GROUP_REUSED',a,t);raise SystemExit(0)
source=json.loads((C/'SOURCE_IDENTITY.json').read_text())['verifier_source_identity_sha256'];items=[[a,t,r,s] for r in cfg['representations'] for s in cfg['seeds']];assert len(items)==78;queues=C/'queues';queues.mkdir(exist_ok=True);env={'PATH':str(Path(cfg['cpu_runtime_python']).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','HF_HUB_OFFLINE':'1'};started=time.monotonic();headroom=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert headroom>=cfg['host_headroom_bytes'];parentrss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;assert 2*cfg['worker_RSS_limit_bytes']+parentrss<=cfg['stage_RSS_limit_bytes']
with (C/'CPU_STAGE.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);jobs=[]
    for i in range(2):
        path=queues/(a+'-'+t+'-worker'+str(i)+'-001.json');part=items[i*39:(i+1)*39];payload={'phase':'S08','source_identity_sha256':source,'selectors':part}
        if path.exists():assert json.loads(path.read_text())==payload
        else:save(path,payload)
        jobs.append(('S08-'+a+'-'+t+'-worker'+str(i)+'-001',[cfg['cpu_runtime_python'],str(C/'worker_entry.py'),str(C),str(path),hashlib.sha256(path.read_bytes()).hexdigest()]))
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda j:execute(j[0],j[1],env),jobs))
    assert all(x['exit_status']==0 for x in results)
records=[];auditcount=0;acalls=0;pretries=0
for _,_,r,s in items:
    key='final_norm' if r=='decoder.final_norm' else 'decoder_layer_'+r.rsplit('.',1)[1];root=A/'candidates'/a/'verification'/t/key/('seed'+str(s));record=json.loads((root/'VERIFICATION.json').read_text());assert (root/'COMPLETE.json').is_file();records.append({'selector':[a,t,r,s],'receipt_sha256':hashlib.sha256((root/'COMPLETE.json').read_bytes()).hexdigest()});pretries+=record['head']['retries'];ar=A/'candidates'/a/'audits'/t/key/('seed'+str(s))/'AUDIT.json'
    if record['audit_panel_member']:ad=json.loads(ar.read_text());assert ad['status']=='PASS';auditcount+=1;acalls+=ad['actual_optimizer_calls']
save(seal,{'schema_version':'s08-finite-group-v1','status':'PASS','alias':a,'task':t,'source_identity_sha256':source,'heads':78,'applications':78,'paths':156,'metrics':780,'producer_initial_calls':1248,'producer_retries':pretries,'original_audits':auditcount,'audit_initial_calls':auditcount*16,'audit_actual_calls':acalls,'records':records,'stage_wall_seconds':time.monotonic()-started,'admitted_host_headroom_bytes':headroom,'parent_RSS_bytes':parentrss,'conservative_stage_RSS_bound_bytes':2*cfg['worker_RSS_limit_bytes']+parentrss,'workers':[{'pid':x['pid'],'start_ticks':x['start_ticks'],'boot_id':x['boot_id'],'exit_status':x['exit_status']} for x in results],'completed_utc':now()});print('S08_GROUP_PASS',a,t,156,auditcount,flush=True)
