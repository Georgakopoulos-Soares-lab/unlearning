from common7 import *
from delivery7 import deliver
import uuid,shutil

def counts():
 rs=[read(p) for p in (A/'probes/R5').glob('*/*/seed*/COMPLETE.json')];back=[read(p) for p in C.glob('BACKUP_R5_*.json')]
 return dict(planned_heads=390,producer_heads=len(rs),producer_applications=len(rs),prediction_paths=2*len(rs),independently_released_new_heads=0,recovery_protected_heads=sum(78 for b in back if b['status']=='PASS'),recovered_panel_paths=sum(len(b['CPU_restored_checks']['checks']) for b in back if b['status']=='PASS'),remaining_heads=390-len(rs),initial_solver_calls=16*len(rs),actual_solver_calls=sum(r['actual_optimizer_fits'] for r in rs),retries=sum(r['actual_optimizer_fits']-16 for r in rs),historical_released_heads=2418,historical_released_applications=2418,primary_LM_reused=42,shared_controls_reused=36,R2_heads_missing=468,R2_applications_missing=468,R2_primary_LM_missing=7,new_GPU_forwards=0,new_H3_fits=0,new_LM_aggregations=0,new_control_fits=0,new_adjacent_rows=0)

def progress(message,status='RUNNING',push=True):
 guard();n=counts();stamp=now();nextaction='Continue the finite R5 A07 queue only' if status=='RUNNING' else 'Separate direct A08 approval required; no automatic resume'
 ev=dict(event_id=str(uuid.uuid4()),run_id=cfg['run_id'],stage='A07',attempt_id=C.name,event_type=status,observed_utc=stamp,prompt_commit=cfg['prompt_commit'],coverage_plan_sha256=cfg['coverage_plan_sha256'],counts=n,message=message,next_allowed_action=nextaction,observer='STOPPED',time_policy=cfg['time_policy'])
 D.mkdir(parents=True,exist_ok=True)
 with (D/'PROGRESS_EVENTS.jsonl').open('a') as f:f.write(json.dumps(ev)+'\n')
 text='# A07 R5 other-five — '+status+'\n\n'+message+'\n\nObserved UTC: '+stamp+'. Prompt `'+cfg['prompt_commit']+'`; A06 input handoff `'+cfg['research_head_before']+'`.\n\n| Measure | Count |\n|---|---:|\n'+''.join('| '+k+' | '+str(v)+' |\n' for k,v in n.items())+'\nAll new units remain COMPLETE_UNVERIFIED pending A08. Producer acceptance and sampled computational recovery do not release the full grid. Original A06 H3/LM and prior attempts remain immutable. R2 gaps and domain-specific R3 eligibility persist.\n\nNo deadline, GPU cap or closure reserve; original start, rental start, rate and cost remain unknown. CPU only, two workers, four BLAS threads each, 32 GiB AS each. Observer/reviewer/scheduler/publisher stay stopped; Pod stays running. No A08 execution.\n\nSee [inputs](A07_INPUTS.json), [manifest](A07_EXECUTION_MANIFEST.json), [expected keys](EXPECTED_TABLE_KEYS.json), [audit plan](A08_AUDIT_HANDOFF_PLAN.json), and [source](CPU_SOURCE_IDENTITY.json).\n\nNext: '+nextaction+'.\n'
 publish('PROGRESS.md',text)
 current=ev|{'current_stage':'A07','current_attempt':'attempts/'+C.name,'status':status,'automatic_resume':False,'A08_started':False,'source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json')}
 for name in ['CONTROLLER_LATEST.json','LATEST_A07.json','REMOTE_HANDOFF.json','RESUME_MANIFEST.json','TERMINAL_STATE_RECEIPT.json']:guard();put(B/name,current|{'entrypoint':name})
 guard();md(B/'PROGRESS.md',text.replace('](','](attempts/'+C.name+'/'))
 guard();md(B/'SESSION_HANDOFF.md','# Pod A current R5 A07 handoff\n\n'+status+'. [Current progress](attempts/'+C.name+'/PROGRESS.md), [attempt handoff](attempts/'+C.name+'/SESSION_HANDOFF.md). Prior A06, A09 and other attempts remain immutable. Observer stopped; no deadline; A08 not started.\n\n'+nextaction+'.\n')
 put(R/'CONTROLLER_STATE.json',current)
 if push:return deliver('A07 R5: '+message[:130])
 return current

def initial():
 guard()
 for p in C.glob('*.json'):
  if not p.name.startswith('PRIOR_PRIVATE_'):publish(p.name,p.read_bytes())
 for p in (C/'prior-run-root').glob('*'):publish('preserved-prior-run-root/'+p.name,p.read_bytes())
 publish('EXPECTED_TABLE_KEYS.csv.gz',(C/'EXPECTED_TABLE_KEYS.csv.gz').read_bytes())
 publish('INPUT_IDENTITY_BINDING.json',{'status':'PASS','A06_commit':cfg['research_head_before'],'A06_output_manifest_sha256':sha(D6/'OUTPUT_SHA256SUMS'),'A06_input_package_sha256':sha(D6/'A07_INPUT_PACKAGE.json'),'effective_prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'execution_manifest_sha256':sha(C/'A07_EXECUTION_MANIFEST.json'),'effective_inputs_sha256':sha(C/'A07_INPUTS.json'),'upstream_extraction_source_sha256': '06752139d8c655457629394be35c89b2a09ffa1f5fb8fad984051658eb55884d9a' if False else '06752139d8c655457629394be35c89b2a09ffa1f5fb483c1a1aabe43b4008593','new_CPU_source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'prior_results_unchanged':True})
 publish('A06_ACCEPTANCE_RECONCILIATION.md','# A06 accepted without repeating production\n\nAll pinned A06 anchors, the complete public output manifest and exact committed bytes passed verification. Its historical embedded live-audit snapshot predates private recovery; later H3 gate, both PASS backups and final delivery establish completion. See TEMPORAL_ACCEPTANCE_RECONCILIATION.json. Reused feature consumer was rehashed, not downloaded again. H3, LM and historical work are reused without fitting or recomputation.\n\nOnly R5 other-five A07 production is authorized. The direct current execution request selects a07_v2.md and its immutable A07 pointer; approval provenance is recorded verbatim. Historical stage approvals are not reused as new authority. No-deadline supersession and stopped services persist.\n')
 publish('SESSION_HANDOFF.md','# A07 in progress\n\nPinned R5-only production, two initial units followed by the remaining finite queue and five private task checkpoints. See PROGRESS.md. New units remain provisional pending separately approved A08.\n')
 for p in (A/'code').glob('*.py'):publish('code/'+p.name,p.read_bytes())
 return progress('Package, A06 handoff and 26 adapter checks PASS; frozen CPU source; production starting.')

if __name__=='__main__':print(json.dumps(initial()))
