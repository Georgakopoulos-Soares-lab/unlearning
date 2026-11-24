"""Immutable finite CPU selector queue only. No remote clients, prompt fetch, publication or phase switch."""
from pathlib import Path
import sys,json,time,hashlib
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C));from ops import A,save,now
from dispatch_utils import complete
sys.path.insert(0,str(A/'code'));from s07_cpu import run_unit
from artifact_seals import process_identity,sha,need
qpath=Path(sys.argv[1]);expected=sys.argv[2];need(sha(qpath)==expected,'Finite queue bytes changed');q=json.loads(qpath.read_text());need(q['source_bundle_sha256']==sha(C/'SOURCE_IDENTITY.json'),'Finite queue numerical source changed');process=process_identity();state=C/(qpath.stem+'-UNITS_PROGRESS.json');records=[]
for selector in q['units']:
 a,t,r,s=selector['alias'],selector['task'],selector['representation'],selector['cv_seed']
 if complete(a,t,r,s):print('REUSED_EXACT_COMPLETED_S07_UNIT',a,t,r,s,flush=True);records.append({'planned_final_head_spec_id':selector['head_spec_id'],'reused_valid_unit':True})
 else:
  result=run_unit(C,a,t,r,s);records.append({'planned_final_head_spec_id':selector['head_spec_id'],'reused_valid_unit':False,'completion':result})
 save(state,{'schema_version':'s07-finite-worker-progress-v1','status':'RUNNING','queue_sha256':expected,'source_bundle_sha256':q['source_bundle_sha256'],'owned_process':process,'completed':records,'unfinished_head_spec_ids':[u['head_spec_id'] for u in q['units'][len(records):]],'next_action':'Only remaining exact units in this immutable S07 queue; no S08','updated_utc':now()})
save(state,{'schema_version':'s07-finite-worker-progress-v1','status':'COMPLETE','queue_sha256':expected,'owned_process':process,'completed':records,'unfinished_head_spec_ids':[],'updated_utc':now()});print('S07_FINITE_CPU_WORKER_DRAINED',qpath.stem,len(records),flush=True)
