from pathlib import Path
import json,hashlib,os,datetime
from ops import C,A,save,now
cfg=json.loads((C/'RUN_CONFIG.json').read_text());T=Path(cfg['research_run_root']);P=T/'S06/attempt-001';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();manifest=[json.loads(l) for l in (C/'FINITE_EXECUTION_MANIFEST.jsonl').read_text().splitlines()];completed=[];candidates=[];bundles=0;rows=0;LM=0;matrices=0
for v in cfg['candidates']:
 alias=v['alias'];case=A/'candidates'/alias;state={'alias':alias,'candidate_id':v['candidate_id'],'scientific':'PENDING','recovery':'PENDING','publication':'PENDING'}
 for t in cfg['tasks']:
  for sp in cfg['allowed_splits']:
   p=case/'features'/t/sp/'COMPLETE.json'
   if p.exists():r=read(p);completed.append({'planned_spec_id':r['identity']['planned_spec_id'],'receipt_path':str(p),'receipt_sha256':sha(p),'status':'COMPLETE_UNVERIFIED'});bundles+=1;rows+=cfg['cohorts'][t][sp]['rows'];matrices+=26
   q=case/'LM'/t/sp/'COMPLETE.json'
   if q.exists():r=read(q);LM+=1;completed.append({'planned_spec_id':r['identity']['planned_spec_id'],'receipt_path':str(q),'receipt_sha256':sha(q),'status':'COMPLETE_UNVERIFIED'});metrics=read(q.parent/'METRICS.json');completed.extend({'planned_spec_id':x['planned_spec_id'],'receipt_path':str(q),'receipt_sha256':sha(q),'status':'COMPLETE_UNVERIFIED'} for x in metrics['metrics'])
 p=case/'verification/VERIFICATION.json'
 if p.exists():state['scientific']=read(p)['status'];state['verification_sha256']=sha(p)
 p=C/(alias+'-PRIVATE_RECOVERY_RECEIPT.json')
 if p.exists():state['recovery']=read(p)['status'];state['private_revision']=read(p)['immutable_revision'];state['recovery_receipt_sha256']=sha(p)
 p=P/'candidates'/alias/'S06_GATE.json'
 if p.exists():
  state['publication']='PREPARED';state['public_gate_sha256']=sha(p)
  delivery=C/('S06-'+alias+'-001-DELIVERY.json')
  if delivery.exists():
   d=read(delivery);needhash=d.get('file_sha256',{}).get(str(p.relative_to(Path(cfg['research_worktree']))));assert d['status']=='PASS' and needhash==sha(p);state['publication']='PASS';state['research_publication_commit']=d['commit']
 candidates.append(state)
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip();owned=[]
for p in sorted(C.glob('*-PROGRESS.json')):
 r=read(p)
 if not r.get('pid'):continue
 live=False
 try:live=r['boot_id']==boot and Path('/proc/'+str(r['pid'])+'/stat').read_text().rsplit(')',1)[1].split()[19]==str(r['start_ticks'])
 except OSError:pass
 owned.append({k:r.get(k) for k in ['stage','pid','start_ticks','boot_id','status','exit_status','elapsed_seconds']}|{'live_matching_identity':live})
queuefile=C/'FINITE_QUEUE_PROCESS.json'
if queuefile.exists():
 q=read(queuefile);live=False
 try:live=q['boot_id']==boot and Path('/proc/'+str(q['pid'])+'/stat').read_text().rsplit(')',1)[1].split()[19]==str(q['start_ticks'])
 except OSError:pass
 owned.append({**q,'stage':'S06-finite-approved-candidate-queue','live_matching_identity':live})
seen={x['planned_spec_id'] for x in completed};pending=[x['id'] for x in manifest if x['id'] not in seen];protected=sum(v['recovery']=='PASS' for v in candidates);resume={'schema_version':'s06-interruption-resume-v1','run_id':cfg['run_id'],'phase':'S06','attempt':'attempt-001','package_commit':'7007ebd05bf59432bf69109e5f69baad31ec0d3a','supplement_sha256':sha(C/'PROMPT.md'),'source_bundle_sha256':sha(C/'SOURCE_IDENTITY.json'),'runtime_lock_sha256':cfg['runtime_lock_sha256'],'cpu_runtime_lock_sha256':cfg['cpu_runtime_lock_sha256'],'protocol_semantic_sha256':cfg['protocol_semantic_sha256'],'completed_units':completed,'pending_exact_spec_ids':pending,'candidates':candidates,'owned_processes':owned,'GPU_progress':read(C/'GPU_PROGRESS.json') if (C/'GPU_PROGRESS.json').exists() else None,'transfer_progress':[{ 'alias':v['alias'],'state':read(C/(v['alias']+'-PRIVATE_RECOVERY_PROGRESS.json'))} for v in cfg['candidates'] if (C/(v['alias']+'-PRIVATE_RECOVERY_PROGRESS.json')).exists()],'next_permitted_action':'Continue only finite approved S06 missing units after reconciling seals/PID-start identities/locks/capacity; private recovery before next candidate. No S07.','prerequisites':'R1-R5 PASS; own H3 gate/recovery; source/runtime hashes unchanged; 48GiB memory headroom and 64GiB storage reserve after next8GiB envelope','unresolved_decisions':read(T/'CONTROLLER_STATE.json')['resume_binding']['unresolved_decisions'],'no_deadline':True,'updated_utc':now()};save(C/'RESUME_MANIFEST.json',resume)
# Public summary omits local dataset identities and private locators.
public={k:resume[k] for k in ['schema_version','run_id','phase','attempt','package_commit','supplement_sha256','source_bundle_sha256','runtime_lock_sha256','cpu_runtime_lock_sha256','protocol_semantic_sha256','pending_exact_spec_ids','owned_processes','next_permitted_action','prerequisites','no_deadline','updated_utc']};public.update(completed_spec_ids=sorted(seen),candidates=candidates);save(P/'RESUME_MANIFEST.json',public)
progress=f'''S06 RUNNING — {now()}

New scope: {bundles}/90 extraction bundles; {rows}/69120 logical rows; {matrices}/2340 representation matrices; {LM}/90 LM units; {len(seen)}/360 sealed specification keys. Scientific verification and private protection remain separate: {protected}/9 candidates protected.

S05 reuse: 18 H3 bundles, 121212 logical rows, 468 matrices, 702 heads and 702 fixed applications, 21 audits. No S05 work replayed. S04 freeze and no-deadline amendment preserved.

Readiness R1–R5 PASS. Current operation and exact unfinished keys are in RESUME_MANIFEST.json. Continue S06 only; stop before S07. Parent/intervention/exposure/replication/forget-evidence limitations remain unchanged. Billing unknown.
''';save(P/'PROGRESS.md',progress);save(P/'SESSION_HANDOFF.md',progress+'\nResume with the private control manifest and actual artifact/process reconciliation. Never repeat valid completed chunks or upload an already protected exact revision.\n');save(T/'PROGRESS.md',progress);save(T/'SESSION_HANDOFF.md',f'Current approved phase: S06, attempt-001.\n\nRead S06/attempt-001/SESSION_HANDOFF.md and RESUME_MANIFEST.json. Preserve all S00–S05 bytes. Canonical7007; S04 semantic417707c70843eecf0183f367d503800baee3569db10626fa0362186505c89b22. No S07 authorization.\n')
print('S06_RESUME_CHECKPOINT',bundles,LM,protected,len(pending),flush=True)
