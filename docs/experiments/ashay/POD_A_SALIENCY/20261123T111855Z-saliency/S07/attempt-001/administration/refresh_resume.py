"""Bounded metadata checkpoint; no fitting, transfer, source mutation or phase dispatch."""
from pathlib import Path
import json,hashlib,os
from ops import C,A,R,save,now
cfg=json.loads((C/'RUN_CONFIG.json').read_text());T=Path(cfg['research_run_root']);P=T/'S07/attempt-001';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();heads=[];groups=[];candidates=[];calls=0;retries=0;CPU=0.;boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
for v in cfg['candidates']:
 a=v['alias'];case=A/'candidates'/a;candidate={'alias':a,'candidate_id':v['candidate_id'],'producer':'PENDING','private_recovery':'PENDING','publication':'PENDING','result_status':'COMPLETE_UNVERIFIED'}
 for t in cfg['tasks']:
  group=case/'tasks'/t/'GROUP_PRODUCTION.json'
  if group.exists():g=read(group);groups.append({'alias':a,'task':t,'receipt_sha256':sha(group),'status':g['status'],'producer_status':g['producer_status']})
  comp=case/'tasks'/t/'unit-completions'
  if comp.exists():
   for p in sorted(comp.glob('*.json')):
    r=read(p);assert r['status']=='COMPLETE_UNVERIFIED' and r['producer_status']=='PASS';heads.append({'alias':a,'task':t,'representation':r['representation'],'cv_seed':r['cv_seed'],'completion_receipt_sha256':sha(p),'head_receipt_sha256':r['head_receipt_sha256']});calls+=r['actual_optimizer_calls'];retries+=r['retries'];CPU+=r['CPU_process_seconds']
 q=case/'PRODUCER_VALIDATION.json'
 if q.exists():candidate['producer']=read(q)['status'];candidate['producer_validation_sha256']=sha(q)
 q=C/(a+'-PRIVATE_RECOVERY_RECEIPT.json')
 if q.exists():candidate['private_recovery']=read(q)['status'];candidate['recovery_revision']=read(q)['immutable_revision'];candidate['recovery_receipt_sha256']=sha(q)
 q=C/('S07-'+a+'-001-DELIVERY.json')
 if q.exists():candidate['publication']=read(q)['status'];candidate['publication_commit']=read(q)['commit']
 candidates.append(candidate)
owned=[]
for p in sorted(C.glob('*-PROGRESS.json')):
 r=read(p)
 if not r.get('pid'):continue
 live=False
 try:live=r['boot_id']==boot and Path('/proc/'+str(r['pid'])+'/stat').read_text().rsplit(')',1)[1].split()[19]==str(r['start_ticks'])
 except OSError:pass
 if live or r.get('exit_status') is None:owned.append({k:r.get(k) for k in ['stage','pid','start_ticks','boot_id','status','exit_status','elapsed_seconds']}|{'live_matching_identity':live})
q=C/'FINITE_QUEUE_PROCESS.json'
if q.exists():
 r=read(q);live=False
 try:live=r['boot_id']==boot and Path('/proc/'+str(r['pid'])+'/stat').read_text().rsplit(')',1)[1].split()[19]==str(r['start_ticks'])
 except OSError:pass
 if live:owned.append({**r,'live_matching_identity':True})
done={(r['alias'],r['task'],r['representation'],r['cv_seed']) for r in heads};pending=[]
for r in cfg['candidates']:
 for t in cfg['tasks']:
  for rep in cfg['representations']:
   for s in cfg['seeds']:
    if (r['alias'],t,rep,s) not in done:pending.append({'alias':r['alias'],'task':t,'representation':rep,'cv_seed':s})
state=read(T/'CONTROLLER_STATE.json');resume={'schema_version':'s07-resume-manifest-v1','run_id':cfg['run_id'],'phase':'S07','attempt_id':'attempt-001','package_commit':cfg['package_commit'],'supplement_sha256':sha(C/'PROMPT.md'),'source_bundle_sha256':sha(C/'SOURCE_IDENTITY.json'),'CPU_runtime_lock_sha256':cfg['cpu_runtime_lock_sha256'],'protocol_semantic_sha256':cfg['protocol_semantic_sha256'],'finite_spec_manifest_sha256':cfg['finite_manifest_sha256'],'completed_head_scopes':heads,'completed_task_groups':groups,'candidates':candidates,'unfinished_head_scopes':pending,'unfinished_spec_resolution':'Each unfinished head scope has30exact frozen keys in FINITE_EXECUTION_MANIFEST.jsonl. Reconcile actual saved CVcall seals for partially completed heads and reuse every valid call; do not restart fitting. Worker queue progress files preserve continuation state.','actual_solver_calls_in_completed_heads':calls,'convergence_retries_in_completed_heads':retries,'uncommitted_partial_solver_calls':'Inspect source-bound CV seals under unfinished heads before resumption; completed-head counts do not hide partial work.','transfer_states':{v['alias']:read(C/(v['alias']+'-PRIVATE_RECOVERY_PROGRESS.json')) for v in cfg['candidates'] if (C/(v['alias']+'-PRIVATE_RECOVERY_PROGRESS.json')).exists()},'owned_processes':owned,'unresolved_decisions':state['resume_binding']['unresolved_decisions'],'next_permitted_action':'Only remaining admitted S07 producer units, exact private sampled recovery and publication. Reconcile PID/start/boot and unit locks before scheduling missing work. Stop before S08.','prerequisites':['Pinned package/S04/source/runtime/S06 handoff','Own H3/S06 gates;R11firstbinary+multiclassPASS','Current48GiBhost/40GiBnextcase+64GiBstorage admission','No independent release/full-CV audit/backbone/LM/test/forget/contrasts'],'no_deadline':True,'updated_utc':now()};save(C/'RESUME_MANIFEST.json',resume)
public={k:resume[k] for k in ['schema_version','run_id','phase','attempt_id','package_commit','supplement_sha256','source_bundle_sha256','CPU_runtime_lock_sha256','protocol_semantic_sha256','finite_spec_manifest_sha256','completed_task_groups','candidates','unfinished_head_scopes','unfinished_spec_resolution','owned_processes','next_permitted_action','prerequisites','no_deadline','updated_utc']};public.update(completed_heads=len(heads),producer_spec_records_under_completed_heads=30*len(heads),actual_solver_calls_in_completed_heads=calls,convergence_retries_in_completed_heads=retries);save(P/'RESUME_MANIFEST.json',public);text=f'''S07 RUNNING — {now()}

Producer-complete heads: {len(heads)}/3510; applications: {len(heads)}/3510; dev paths: {2*len(heads)}/7020; marginal records: {10*len(heads)}/35100. Task checkpoints: {len(groups)}/45. Completed-head actual solver calls: {calls}, including {retries} convergence retries. Partial call seals remain separately preserved under unfinished heads. All new results COMPLETE_UNVERIFIED pending S08.

Producer-validated candidates: {sum(x['producer']=='PASS' for x in candidates)}/9; privately recovered: {sum(x['private_recovery']=='PASS' for x in candidates)}/9; published: {sum(x['publication']=='PASS' for x in candidates)}/9. Recovery and producer checks do not independently release the matrix. Actual owned process identities and remaining scopes are in RESUME_MANIFEST.json.

S05 H3 and S06 features/LM remain unchanged. No backbone/LM work or fresh audit refits. S04 scientific/audit/contrast freezes and no-deadline amendment remain active. Continue only finite approved S07; stop before S08.
''';save(P/'PROGRESS.md',text);save(T/'PROGRESS.md',text);state['phase_state']['S07'].update(completed_heads=len(heads),completed_task_groups=len(groups),protected_candidates=[x['alias'] for x in candidates if x['private_recovery']=='PASS']);state['resume_binding'].update(unfinished_units=[x['alias']+':'+x['task']+':'+x['representation']+':'+str(x['cv_seed']) for x in pending],owned_processes=[{'pid':x['pid'],'start_ticks':str(x['start_ticks']),'boot_id':x['boot_id']} for x in owned],next_action=resume['next_permitted_action'],prerequisites=resume['prerequisites'],reconciled_utc=now());save(T/'CONTROLLER_STATE.json',state);print('S07_RESUME_CHECKPOINT',len(heads),len(groups),sum(x['private_recovery']=='PASS' for x in candidates),flush=True)
