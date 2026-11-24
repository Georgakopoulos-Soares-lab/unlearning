"""One finite CPU worker with immutable selectors; no network/publication/phase authority."""
from pathlib import Path
import sys,json,hashlib,traceback,os,datetime
c=Path(sys.argv[1]);queue=Path(sys.argv[2]);expected=sys.argv[3]
assert hashlib.sha256(queue.read_bytes()).hexdigest()==expected
cfg=json.loads((c/'RUN_CONFIG.json').read_text());sys.path.insert(0,str(Path(cfg['artifacts_root'])/'code'))
from s08_shared import *
from s08_verify import unit
from s08_audit import audit
q=load(queue);need(q['phase']=='S08' and q['source_identity_sha256']==load(c/'SOURCE_IDENTITY.json')['verifier_source_identity_sha256'],'Worker queue source changed');need(1<=len(q['selectors'])<=78,'Unbounded worker queue');identity=process_identity();progress=c/(queue.stem+'-WORKER.json');put(progress,{'status':'RUNNING','identity':identity,'immutable_queue_sha256':expected,'completed':0,'total':len(q['selectors'])})
for i,selector in enumerate(q['selectors']):
    a,t,r,s=selector
    try:
        unit(c,a,t,r,s)
        if any(x['k']=='audit_refit' and (x['c'],x['t'],x['r'],x['s'])==(a,t,r,s) for x in audit_keys(str(c))):audit(c,a,t,r,s)
        put(progress,{'status':'RUNNING','identity':identity,'immutable_queue_sha256':expected,'completed':i+1,'total':len(q['selectors']),'last_completed_selector':selector,'updated_utc':now()})
    except Exception as error:
        directory=Path(cfg['artifacts_root'])/'candidates'/a/'failures';directory.mkdir(parents=True,exist_ok=True);name=t+'-'+key(r)+'-seed'+str(s)+'-'+str(os.getpid())+'.json';put(directory/name,{'status':'FAIL','selector':selector,'error_class':type(error).__name__,'reason':str(error),'source_identity_sha256':q['source_identity_sha256'],'runtime_lock_sha256':cfg['cpu_runtime_lock_sha256'],'owned_process':identity,'queue_sha256':expected,'traceback':traceback.format_exc(),'observed_utc':now(),'downstream_scope':'Affected head/apps/predictions/metrics and required shared audit dependencies; no release until diagnosed.'});put(progress,{'status':'FAILED','identity':identity,'completed':i,'failed_selector':selector,'failure_record':str(directory/name),'updated_utc':now()});raise
put(progress,{'status':'COMPLETE','identity':identity,'immutable_queue_sha256':expected,'completed':len(q['selectors']),'total':len(q['selectors']),'updated_utc':now()});print('S08_FINITE_WORKER_COMPLETE',queue.name,flush=True)
