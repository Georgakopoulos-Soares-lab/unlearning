"""Single-owner finite A04 recovery progress/publication; never dispatches stages."""
from common4 import *
import argparse,fcntl,time,re
def service():
 root=Path('/workspace/agent-handoff/POD_A/review-loop');h=read(root/'heartbeat.json');p=Path('/proc')/str(h['pid'])/'stat';live=p.exists() and p.read_text().split()[2]!='Z' and p.read_text().split()[21]==h['proc_start_ticks'];assert not live and (root/'STOP').exists()
 return {'observer_status':'STOPPED','prior_pid':h['pid'],'prior_start_ticks':h['proc_start_ticks'],'identity_alive':False,'reviewer_status':'DRAFT_ONLY_NOT_RUNNING','publisher_status':'BLOCKED_NOT_RUNNING','restarted':False,'observed_utc':now()}
def export():
 for p in (A/'code').iterdir():
  if p.is_file() and p.suffix=='.py':publish('CODE/'+p.name,p.read_bytes())
  elif p.is_file() and p.suffix=='.patch':publish('CODE/'+p.name+'.json',{'schema':'lossless-UTF8-source-data-v1','original_filename':p.name,'original_sha256':sha(p),'original_bytes':p.stat().st_size,'encoding':'UTF-8 string; encode content directly to reconstruct exact bytes','content':p.read_text()})
 files=[{'path':str(p.relative_to(A)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((A/'code').glob('*')) if p.is_file()];put(C/'SOURCE_EXECUTION_MAP.json',{'schema':'pod-a-a04-source-execution-map-v1','qualification_source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'qualification_source_bytes_unchanged':True,'files':files,'public_patch_data_encoding':'CODE/owned_adapter.patch.json losslessly represents exact original patch bytes; private executed-source snapshot retains the native .patch','helper_versions_do_not_modify_qualified_numerics':True,'created_utc':now()});publish('SOURCE_EXECUTION_MAP.json',read(C/'SOURCE_EXECUTION_MAP.json'))
def progress(message,status='RUNNING'):
 with (C/'report.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard();obs=service();units=list((A/'qualification').glob('*/*/attempt-*/COMPLETE.json'));download=read(C/'DOWNLOAD_RECEIPTS.json') if (C/'DOWNLOAD_RECEIPTS.json').exists() else {'records':[]};num=read(C/'numerical-reports/SMOKE_RESULTS.json') if (C/'numerical-reports/SMOKE_RESULTS.json').exists() else {};fresh=read(C/'BACKUP_VERIFICATION.json') if (C/'BACKUP_VERIFICATION.json').exists() else {};counts={'new_qualification_variants_sealed':len(units),'new_comparison_rows_passed':num.get('passed',0),'new_comparison_rows_failed':num.get('failed',0),'preserved_qualification_variants':12,'preserved_comparison_rows':378,'verified_mirror_assets':len(download['records']),'expected_mirror_assets':16,'new_production_scores':0,'new_probe_heads':0,'heldout_forwards':0,'R2_pending_variants':3,'R2_pending_comparison_rows':54};event={'schema_version':1,'event_id':'A04-004-'+str(sum(1 for _ in (C/'PROGRESS_EVENTS.jsonl').open())+1 if (C/'PROGRESS_EVENTS.jsonl').exists() else 1).zfill(5),'run_id':cfg['run_id'],'stage':'A04','attempt_id':cfg['attempt_id'],'event_type':message,'observed_utc':now(),'approval_reference':'APPROVAL_RECORD.json','prompt_commit':cfg['prompt_commit'],'effective_hashes':{'A04_RUNTIME_LOADING.md':cfg['A04_prompt_sha256'],'a9.5.md':cfg['amendment_sha256']},'amendment_commit':cfg['amendment_commit'],'research_parent':git('rev-parse','HEAD'),'protocol_hash':read(R/'attempts/A09-attempt-001/RUN_CONFIG.json')['protocol_sha256'],'unit_counts':counts,'evidence_paths':['A04_INPUT_VERIFICATION.json','MIRROR_IDENTITY_VERIFICATION.json','PRESERVED_QUALIFICATION_UNITS.json'],'blockers':['R2 remains unidentified and discovery is excluded','Training ancestry/objective/exposure/source-label unknowns remain'],'scientific_job_state':'TRAINING_ONLY_QUALIFICATION' if status=='RUNNING' and units else 'PREPARING' if status=='RUNNING' else 'QUIESCENT','administrative_service_state':obs,'next_allowed_action':'A04 R3/R5 recovery and qualification only' if status=='RUNNING' else 'Review protected A05 scope proposal; no automatic stage start'};fp=digest({k:event[k] for k in ['event_type','unit_counts','prompt_commit']});events=[json.loads(l) for l in (C/'PROGRESS_EVENTS.jsonl').read_text().splitlines()] if (C/'PROGRESS_EVENTS.jsonl').exists() else []
  if not any(e.get('event_fingerprint')==fp for e in events):
   event['event_fingerprint']=fp
   with (C/'PROGRESS_EVENTS.jsonl').open('a') as f:f.write(json.dumps(event)+'\n')
  state={'schema':'pod-a-a04-recovery-state-v1','current_stage':'A04','run_id':cfg['run_id'],'attempt_id':cfg['attempt_id'],'status':status,'scope':'R3/R5 immutable-mirror recovery; 12 TRAIN rows only; R2 discovery excluded','prompt_commit':cfg['prompt_commit'],'amendment_commit':cfg['amendment_commit'],'effective_hashes':event['effective_hashes'],'unit_counts':counts,'administrative_services':obs,'time_policy':cfg['time_policy'],'previous_A09_release':{'status':'COMPLETE_QUALIFIED_REPORTING_SAVED_ANALYSIS','full_project_status':'PARTIAL','metadata_commit':'6552b2488525dd5fc5da4b30c1eff16c7712153e','report_delivery_commit':'409e860f03dc0b4a78fd47e6e83bd6ca8d0f34fd','path':'attempts/A09-attempt-001/SESSION_HANDOFF.md','unchanged_historical_release':True},'scientific_job_state':event['scientific_job_state'],'next_allowed_action':event['next_allowed_action'],'automatic_resume':False,'observed_utc':now()};put(C/'CONTROLLER_STATE.json',state)
  for name in ['CONTROLLER_STATE.json','SESSION_HANDOFF.md','REMOTE_HANDOFF.json','RESUME_MANIFEST.json']:
   p=R/name
   if p.exists() and not (C/('PRIOR_PRIVATE_'+name)).exists():shutil_copy=p.read_bytes();atomic(C/('PRIOR_PRIVATE_'+name),shutil_copy)
  put(R/'CONTROLLER_STATE.json',state)
  mdtext=f'''# A04 R3/R5 mirror recovery — {status}

Run `{cfg['run_id']}`, attempt `{cfg['attempt_id']}`. Observed UTC `{now()}`. Approved A04 package `{cfg['prompt_commit']}` and exact `a9.5.md` amendment `{cfg['amendment_commit']}` are pinned. Scope is acquisition and training-only qualification of selected R3/R5; R2 discovery is excluded. The observer remains STOPPED.

## Goals and finite units

| Goal | Target | New sealed/verified | Reused verified | Pending / limitation | Evidence |
|---|---:|---:|---:|---|---|
| Original mirror assets | 16 | {len(download['records'])} | Included separately by transfer receipt | Missing exact assets only | [Downloads](DOWNLOAD_RECEIPTS.json) |
| New R3/R5 qualification variants | 6 | {len(units)} | 0 | Features and LM gates remain separate | [Plan](RECOVERY_PLAN.json) |
| R3 historical + self-comparison rows | 135 | {sum(r['alias']=='R3' and r['status']=='PASS' for r in num.get('checks',[]))} | 0 | Exact same-checkpoint bridge | [Numerical results](SMOKE_RESULTS.json) |
| R5 self-comparison rows | 54 | {sum(r['alias']=='R5' and r['status']=='PASS' for r in num.get('checks',[]))} | 0 | No historical R5 equality claim | [Numerical results](SMOKE_RESULTS.json) |
| base/R1/R4/R6 qualification | 12 variants / 378 rows | 0 | 12 / 378 | No repeated GPU sweep | [Preserved units](PRESERVED_QUALIFICATION_UNITS.json) |
| Seven-endpoint qualification plan | 21 variants / 621 rows | {len(units)} / {num.get('passed',0)} | 12 / 378 | R2 3 variants / 54 rows stay pending | [Coverage proposal](A05_REQUIREMENTS.md) |
| Production heads, six tasks × 26 hooks × three seeds | 3276 | 0 | 2340 | R2/R5 production remains unmeasured | [Historical A09](../A09-attempt-001/TABLE_INDEX.json) |
| Separate unchanged-base applications | 3276 | 0 | 2340 | Both policies preserved | Historical A09 |
| Primary LM production units | 49 | 0 | 35 | Training smoke is not production LM | Historical A09 |
| Shared DNA controls | 36 | 0 | 36 | No fitting this attempt | Historical A09 |
| Paired uncertainty / independent metric verification | Frozen prior families | 0 | A08/A09 verified release | No new draws or scientific contrasts | Historical A09 |
| New evidence private recovery | One bounded checkpoint | {fresh.get('status','PENDING')} | Prior proofs reused | Immutable weight mirrors referenced without duplicate archives | [Recovery](BACKUP_VERIFICATION.json) |

## This attempt

{message}

There are zero new downstream scientific performance measurements, production extractions, probe fits, held-out forwards, bootstrap draws or scientific contrasts. Qualification uses only the frozen 12 TRAINING rows, all 26 hooks, physical batch 8, unchanged pooling/tokenization/precision and actual causal LM. Smoke residuals are numerical gates and do not rank model capabilities. The six tasks, 26 representations, three CV seeds, both policies, 36 controls, true LM and uncertainty standards remain frozen for any future approved production proposal.

## Historical release and missing scope

The completed [A09 report](../A09-attempt-001/RESULTS.md) and [gallery](../A09-attempt-001/FIGURE_GALLERY.md) remain immutable historical release at `6552b2488525dd5fc5da4b30c1eff16c7712153e`. The full 3276-head experiment and A04 remain PARTIAL while R2 is unresolved. All five adjacent families remain unmeasured in this attempt; qualification can change future eligibility only. R3−R1 and R6−R4 remain nonadjacent. Realized exposure, parent/objective and source-label interpretation gaps remain explicit; runtime PASS cannot establish forgetting or causal retain-mixture effects.

## Reproducibility, resources and processes

[Package](PACKAGE_VERIFICATION.json), [approval](APPROVAL_RECORD.json), [mirror identity](MIRROR_IDENTITY_VERIFICATION.json), [runtime lock](ENVIRONMENT_LOCK.json) and [source](SOURCE_IDENTITY.json) bind this attempt. Numerical source remains `e72bb12601855339bf4497d3854cbd90e1f052d1def08a7ed4bcbb1da2192c1c`; environment remains `401c96fdeb59783bf20954b153b24edaf913b87aa3d7607e1cc32c088d3ca294`. [Resource plan](RESOURCE_PLAN.json) uses fresh provider capacity and cgroup/GPU observations. One GPU qualification process and bounded CPU/BLAS workers only. No original/rental start, rate or cost is invented. No deadline, GPU cap or closure reserve is reinstated.

Observer **STOPPED**; reviewer **DRAFT_ONLY/not running**; publisher **BLOCKED/not running**. No scheduler is restarted. Owned transfer/GPU jobs are recorded separately by PID/start identity. The Pod stays running.

## Next action

{event['next_allowed_action']}. A protected proposal is required before a new A05 approval. No A05, production backfill, perturbation, Pod B work or replacement training runs here.
'''
  for name in ['APPROVAL_RECORD.json','PACKAGE_VERIFICATION.json','RECOVERY_PLAN.json','QUALIFICATION_PLAN.json','IMPLEMENTATION_VALIDATION.json','PRESERVED_WORK_INDEX.json','RESOURCE_PLAN.json','PROVIDER_RESOURCE_EVIDENCE.json','BACKUP_ACCESS_CHECK.json','A04_INPUT_VERIFICATION.json','MIRROR_IDENTITY_VERIFICATION.json','LIVE_RUNTIME_IDENTITY_CHECK.json','SOURCE_IDENTITY.json','ENVIRONMENT_LOCK.json','INVALIDATION_MAP.json','PRESERVED_QUALIFICATION_UNITS.json','CONTROLLER_STATE.json','DOWNLOAD_RECEIPTS.json','PAYLOAD_RECOVERY_INDEX.json','CHECKPOINT_HASHES.json','TRANSFER_DIAGNOSTICS.json']:
   if (C/name).exists():publish(name,(C/name).read_bytes())
  publish('PROGRESS.md',mdtext);publish('PROGRESS_EVENTS.jsonl',(C/'PROGRESS_EVENTS.jsonl').read_bytes());publish('SCOPE_AMENDMENT.a9.5.txt',(C/'SCOPE_AMENDMENT.a9.5.txt').read_bytes())
  for name in cfg['allowed_root_files']:
   p=C/'prior-run-root'/name
   if p.exists() and not (D/'preserved-prior-run-root'/name).exists():publish('preserved-prior-run-root/'+name,p.read_bytes())
  rootmd=mdtext.replace('](','](attempts/'+cfg['attempt_id']+'/');guard();md(B/'PROGRESS.md',rootmd);guard();put(B/'CONTROLLER_LATEST.json',state);guard();put(B/'LATEST_A04.json',{'stage':'A04','attempt_id':cfg['attempt_id'],'status':status,'path':str(D.relative_to(B)),'prompt_commit':cfg['prompt_commit'],'amendment_commit':cfg['amendment_commit']})
  current={'schema':'pod-a-current-handoff-v3','owner':'POD_A','run_id':cfg['run_id'],'current_stage':'A04','attempt_id':cfg['attempt_id'],'status':status,'current_attempt':str(D.relative_to(B)),'scope':state['scope'],'current_progress':str((D/'PROGRESS.md').relative_to(B)),'previous_A09_release':state['previous_A09_release'],'previous_admin_closeout_commit':'23d6497c0ba10abde9e83d836078b2f8d10cb668','administrative_services':obs,'time_policy':cfg['time_policy'],'new_production_measurements':0,'automatic_resume':False,'next_allowed_action':event['next_allowed_action'],'preserved_previous_entrypoints':str((D/'preserved-prior-run-root').relative_to(B)),'observed_utc':now()}
  for name in ['REMOTE_HANDOFF.json','RESUME_MANIFEST.json','TERMINAL_STATE_RECEIPT.json']:guard();put(B/name,{**current,'schema':current['schema']+'-'+name.split('.')[0].lower(),'terminal_state_note':'Current A04 attempt is RUNNING; prior A09 terminal delivery is historical' if status=='RUNNING' else 'Current A04 closed; previous A09 release remains unchanged'})
  guard();md(B/'SESSION_HANDOFF.md',f'''# Pod A current handoff — A04 R3/R5 recovery {status}

This run has a newly authorized, isolated **A04-attempt-004** for selected R3/R5 acquisition and training-only qualification. Read [current progress](attempts/{cfg['attempt_id']}/PROGRESS.md), [approval](attempts/{cfg['attempt_id']}/APPROVAL_RECORD.json), [recovery plan](attempts/{cfg['attempt_id']}/RECOVERY_PLAN.json), [machine handoff](REMOTE_HANDOFF.json) and [resume boundaries](RESUME_MANIFEST.json).

The completed [A09 scientific report](attempts/A09-attempt-001/RESULTS.md), [gallery](attempts/A09-attempt-001/FIGURE_GALLERY.md) and [saved-analysis restore instructions](attempts/A09-attempt-001/RESTORE.md) remain an immutable historical release. Original production coverage is unchanged: 2340/3276 heads, separate 2340/3276 fixed applications, 35/49 primary LM units and 36 controls. There are no new production results in this recovery attempt.

Current scope is six missing R3/R5 qualification variants and 189 comparison rows, reusing passed base/R1/R4/R6 12 variants/378 rows. R3 needs the exact historical shard and same-checkpoint bridge; R5 needs fresh provider-bound identity, strict loading and self/LM gates. R2 remains unresolved and discovery is excluded. No held-out forward, production extraction, fitting, new scientific contrast, perturbation, Pod B work or replacement training is authorized.

Approved base prompt `{cfg['prompt_commit']}`, exact amendment `{cfg['amendment_commit']}`. The no-deadline amendment persists; original/rental start, rate and cost remain unknown. Observer remains STOPPED, with no scheduler restart. The Pod remains running. Prior current entrypoints are preserved [here](attempts/{cfg['attempt_id']}/preserved-prior-run-root/SESSION_HANDOFF.md).

{event['next_allowed_action']}. No later stage starts automatically.
''')
  print(json.dumps({'status':status,'event':message,'counts':counts,'observer':'STOPPED'}))
def deliver(label):
 with (C/'publish.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard();remote=git('ls-remote','--heads','origin','POD_A').split()[0];assert remote==git('rev-parse','HEAD'),'Remote advanced; preserve work and wait';paths=[str(p.relative_to(W)) for p in D.rglob('*') if p.is_file()]+[str((B/n).relative_to(W)) for n in cfg['allowed_root_files'] if (B/n).exists()]
  for path in paths:
   p=W/path;data=p.read_bytes();assert owned(path) and p.resolve().is_relative_to(B.resolve()) and not p.is_symlink();assert len(data)<20*1024**2 and p.suffix not in ['.npz','.npy','.joblib','.distcp','.pt','.bin'];assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',data);assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',data)
  guard();subprocess.run(['git','-C',str(W),'add','--',*paths],check=True);changed=git('diff','--cached','--name-only').splitlines();assert changed and set(changed)<=set(paths);subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True);guard();assert git('ls-remote','--heads','origin','POD_A').split()[0]==remote
  subprocess.run(['git','-C',str(W),'-c','user.name=AshaySrivastava','-c','user.email=149273902+ashay-sriv-06@users.noreply.github.com','commit','-m',label],check=True,stdout=subprocess.PIPE);head=git('rev-parse','HEAD');guard(head=head);subprocess.run(['git','-C',str(W),'push','origin','HEAD:refs/heads/POD_A'],check=True);assert git('ls-remote','--heads','origin','POD_A').split()[0]==head;guard(dirty=False,head=head)
  for path in paths:assert gitb('show',head+':'+path)==(W/path).read_bytes()
  receipt={'status':'PASS','commit':head,'parent_remote':remote,'changed_paths':changed,'all_owned_committed_bytes_verified':True,'remote_equal':True,'delivered_utc':now()};put(C/('GIT_DELIVERY.'+head[:12]+'.json'),receipt);print(json.dumps({'status':'DELIVERED','commit':head,'files':len(changed)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['progress','export','deliver']);p.add_argument('--message',default='Preflight and exact mirror acquisition underway');p.add_argument('--status',default='RUNNING');v=p.parse_args()
 if v.operation=='progress':progress(v.message,v.status)
 elif v.operation=='export':export()
 else:deliver(v.message)
