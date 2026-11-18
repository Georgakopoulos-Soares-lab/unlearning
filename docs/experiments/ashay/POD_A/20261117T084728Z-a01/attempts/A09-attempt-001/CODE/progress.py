"""Single-writer A09 progress; no stage dispatcher or scientific work."""
from common import *
from research_guard import guard
import argparse,fcntl,time
def service():
 root=Path('/workspace/agent-handoff/POD_A/review-loop');h=read(root/'heartbeat.json');p=Path('/proc')/str(h['pid'])/'stat';alive=p.exists() and p.read_text().split()[2]!='Z' and p.read_text().split()[21]==h['proc_start_ticks'];age=time.time()-datetime.datetime.fromisoformat(h['observed_utc']).timestamp();stopped=(root/'STOP').exists() and not alive
 return {'observer_status':'STOPPED' if stopped else 'ACTIVE' if alive and age<1500 else 'BLOCKED','reviewer_status':'DRAFT_ONLY','publisher_status':'BLOCKED','observer_pid':h['pid'],'observer_start_ticks':h['proc_start_ticks'],'heartbeat_utc':h['observed_utc'],'heartbeat_age_seconds':age,'owned_service_alive':alive,'no_new_service_launched':True,'observed_utc':now()}
def append_event_once(path,event):
 fingerprint=digest({k:event[k] for k in ['event_type','prompt_commit','unit_counts','next_allowed_action']});prior=[json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
 if any(e.get('event_fingerprint')==fingerprint for e in prior):return False
 event['event_fingerprint']=fingerprint
 with path.open('a') as f:f.write(json.dumps(event)+'\n')
 return True
def update(event,status='RUNNING'):
 with (C/'report.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);obs=service();put(C/'SERVICE_STATUS.json',obs);state=read(C/'CONTROLLER_STATE.json');state.update(status=status,scientific_job_state='QUIESCENT',observed_utc=now(),administrative_service_state=obs,unit_counts={'new_scientific_measurements':0,'new_fits':0,'new_forwards':0,'available_heads_reused':2340,'available_fixed_applications_reused':2340,'pending_R2_heads':468,'pending_R5_heads':468,'LM_primary_reused':35,'LM_primary_pending':14,'controls_reused':36,'figure_pairs_reused':31},next_allowed_action='A09 finite reporting and recovery only' if status=='RUNNING' else 'Terminal handoff; no further work without a new explicitly scoped approval');put(C/'CONTROLLER_STATE.json',state);put(R/'CONTROLLER_STATE.json',state)
  p=C/'PROGRESS_EVENTS.jsonl';count=sum(1 for _ in p.open()) if p.exists() else 0;e={'schema_version':1,'event_id':'A09-'+str(count+1).zfill(5),'run_id':R.name,'stage':'A09','attempt_id':C.name,'event_type':event,'observed_utc':now(),'approval_reference':str(C/'APPROVAL_RECORD.json'),'prompt_commit':cfg['prompt_commit'],'effective_hashes':read(C/'APPROVAL_RECORD.json')['effective_hashes'],'research_parent':git('rev-parse','HEAD'),'protocol_hash':cfg['protocol_sha256'],'unit_counts':state['unit_counts'],'evidence_paths':['A09_INPUTS.json','INPUT_VALIDATION.json','A09_EXECUTION_MANIFEST.json'],'blockers':['Full sequence: R2delivery/admission, R5qualification, R3livebridge; parent/exposure metadata unknown'],'scientific_job_state':'QUIESCENT','administrative_service_state':obs,'next_allowed_action':state['next_allowed_action']}
  append_event_once(p,e)
  md=f'''# A09 progress — {status}

Run `{R.name}`, attempt `{C.name}`. Observed UTC `{now()}`; display timezone UTC. Direct approval pins prompt `{cfg['prompt_commit']}`. Accepted A08 research `{cfg['research_head_before']}`; current publication parent `{git('rev-parse','HEAD')}`. Scientific measurement queue is quiescent; only finite reporting/recovery work is authorized.

## Goals and coverage

| Goal | Target | New A09 science | Verified reused | Running science | Pending | Failed | Evidence / gap |
|---|---:|---:|---:|---:|---:|---:|---|
| Production heads, six tasks × 26 hooks × three seeds | 3276 | 0 | 2340 | 0 | 936 | 0 | [Coverage](COVERAGE.csv); R2/R5 each 468 |
| Unchanged-base applications, separate universe | 3276 | 0 | 2340 | 0 | 936 | 0 | Same frozen policies, no new fitting |
| Primary causal LM units | 49 | 0 | 35 | 0 | 14 | 0 | [Table index](TABLE_INDEX.json); no layer/seed axis |
| Shared input control fits | 36 | 0 | 36 | 0 | 0 | 0 | Repeated displays are not new fits |
| A08 independent saved-output audits | 780 | 0 | 780 | 0 | 0 | 0 | [Audit releases](AUDIT_RELEASE_STATUS.csv) |
| A08 sampled independent refits | 60 | 0 | 60 | 0 | 0 | 0 | 960 historical optimizer fits, not all-head refitting |
| R6−R4 paired rows, classifier / LM | 5460 / 14 | 0 | 5460 / 14 | 0 | 0 | 0 | Predeclared NONADJACENT family |
| Figure pairs | 31 | 0 | 31 | 0 | 0 | 0 | [Gallery](FIGURE_GALLERY.md); all seeds/layers retained |
| Fresh A09 saved-analysis recovery | Eight paths + two refit heads + contrasts | 0 | Prior proof separately attributed | 0 | Current check until sealed | 0 | [Recovery](BACKUP_VERIFICATION.json) |

## This attempt

{event}

A09 adds reports, presentation repairs and scoped recovery checks. It adds **zero scientific measurements, fits, forwards, bootstrap draws or interval families**. The historical handoff, frozen audit-plan statuses and typed control aliases are repaired only in A09-owned derivatives.

## Scientific findings and limits

The verified A08 tables show readout-policy divergence, mixed R6−R4 effects and LM/probe disagreement. [Results](RESULTS.md) uses both predeclared anchors, both policies and every seed/layer in the linked tables. All intervals remain pointwise and unadjusted, conditional on fitted heads; seed ranges are not confidence intervals. Higher scores before supplied configuration declaration do not establish unseen-training-data generalization. Missing parents, objectives and realized exposure prevent causal mixture attribution or an optimality/forgetting claim.

## Dependencies and reproducibility

The full 6637-unit ledger remains intact. R2 identity/delivery, R5 qualification and the R3 live-runtime bridge are distinct gaps. All five adjacent edges remain pending/blocked; R6−R4 cannot replace them. Historical R3 stays in its accepted domain and H3 exploratory test stays separate. A04 remains PARTIAL.

[Inputs](A09_INPUTS.json), [finite plan](A09_EXECUTION_MANIFEST.json), [input checks](INPUT_VALIDATION.json), [events](PROGRESS_EVENTS.jsonl) and [source](SOURCE_IDENTITY.json) bind coverage `{cfg['coverage_plan_sha256']}` and protocol `{cfg['protocol_sha256']}`. Recovery references immutable dependencies rather than repacking history.

## Resources and processes

At most two CPU workers × four BLAS threads and a 32-GiB address-space ceiling. Zero GPU work or purchases. Actual measurements and process identities are in [resource closeout](RESOURCE_CLOSEOUT.json). Original/rental starts, rate and cost remain null. No deadline, science cutoff or closure reserve was reinstated.

Observer **{obs['observer_status']}**; reviewer **DRAFT_ONLY**; publisher **BLOCKED**. Administrative services cannot approve or advance science. This run's owned observer will stop after verified terminal delivery; the Pod stays running.

## Next action

{state['next_allowed_action']}. The [resume manifest](RESUME_MANIFEST.json) and [restore instructions](RESTORE.md) exclude completed work. No A10 or automatic restart is authorized.
'''
  guard(allow_dirty=True)
  for n in ['APPROVAL_RECORD.json','PACKAGE_VERIFICATION.json','A09_INPUTS.json','INPUT_VALIDATION.json','A09_EXECUTION_MANIFEST.json','CONTROLLER_STATE.json','RESOURCE_PREFLIGHT.json','PRIVATE_ACCESS_PROBE.json','SERVICE_STATUS.json']:
   if (C/n).exists():publish(n,(C/n).read_bytes())
  publish('PROGRESS.md',md);publish('PROGRESS_EVENTS.jsonl',p.read_bytes());guard(allow_dirty=True);write_md(BASE/'PROGRESS.md',md.replace('](','](attempts/'+C.name+'/')+'\n## Stage history\n\n| Stage | Status |\n|---|---|\n| A01 | Accepted |\n| A02 | Accepted PARTIAL |\n| A03 | Accepted |\n| A04 | PARTIAL |\n| A05 | COMPLETE |\n| A06 | Completed qualified subset; reporting exception preserved |\n| A07 | COMPLETE producer |\n| A08 | COMPLETE qualified analysis |\n| A09 | '+status+' reporting/recovery |\n');put(BASE/'CONTROLLER_LATEST.json',state);put(BASE/'LATEST_A09.json',{'stage':'A09','status':status,'attempt_id':C.name,'path':str(D.relative_to(BASE)),'prompt_commit':cfg['prompt_commit']});print(json.dumps({'status':status,'event':event,'observer':obs['observer_status']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--event',required=True);p.add_argument('--status',default='RUNNING');v=p.parse_args();update(v.event,v.status)
