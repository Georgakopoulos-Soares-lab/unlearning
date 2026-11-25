from ops import run
import sys
sys.path.insert(0,'/workspace/pod-a-saliency/artifacts/20261123T111855Z-saliency/S10/attempt-001/code')
from common import *
state=read(T/'CONTROLLER_STATE.json');assert state['phase_state']['S10']['external_dependency_disposition']=='PENDING' and read(P/'PENDING_FORGET_INPUTS.json')['status']=='PENDING' and read(P/'S11_HANDOFF.json')['scientific_integration']=='PENDING';assert read(C/'PRIVATE_RECOVERY_RECEIPT.json')['status']=='PASS'
sys.path.insert(0,str(PKG));import S_validate_package as canonical;canonical.validate_record(PKG,'phase_receipt',read(P/'S10_RECEIPT.json'))
for n,h in read(P/'S10_RECEIPT.json')['output_sha256'].items():assert sha(P/n)==h
result=json.loads(run('S10-canonical-global-close-002',['/usr/local/bin/python3',str(PKG/'S_validate_package.py'),'--root',str(PKG),'--entry','S10','--action','close','--state',str(T/'CONTROLLER_STATE.json'),'--research-worktree',str(R)]));assert result['entry']['status']=='ENTRY_PASS';save(C/'PHASE_SEAL_VALIDATION.json',{'status':'PASS','canonical_receipt_schema':'PASS','canonical_global_close':'ENTRY_PASS','S10_receipt_sha256':sha(P/'S10_RECEIPT.json'),'S11_handoff_sha256':sha(P/'S11_HANDOFF.json'),'scientific_integration':'PENDING','prior_failed_close_preserved':'administrative-revisions/controller-schema-repair-002','observed_utc':now()})
event={'event':'S10_LIMITED_SCOPE_ADMINISTRATIVE_SEAL_AFTER_SCHEMA_REPAIR','timestamp':now(),'receipt_sha256':sha(P/'S10_RECEIPT.json'),'S11_handoff_sha256':sha(P/'S11_HANDOFF.json'),'scientific_integration':'PENDING','S11_approved':False}
for path in [C/'EVENTS.jsonl',T/'EVENTS.jsonl']:
 with path.open('a') as f:f.write(json.dumps(event)+'\n')
print('S10_CANONICAL_LIMITED_SCOPE_CLOSE_PASS_REUSED_ASSESSMENT',flush=True)
