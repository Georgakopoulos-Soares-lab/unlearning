"""Finite S08 saved-output/original-audit queue only. No later stage dispatch."""
from pathlib import Path
import sys,json,fcntl,os,hashlib
from ops import C,A,R,save,now
from long_run import execute
cfg=json.loads((C/'RUN_CONFIG.json').read_text());P=Path(cfg['public_root']);T=Path(cfg['research_run_root']);source=json.loads((C/'SOURCE_IDENTITY.json').read_text())['verifier_source_identity_sha256'];identity={'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()};record=C/'FINITE_VERIFICATION_PROCESS.json'
if record.exists():
    old=json.loads(record.read_text());p=Path('/proc/'+str(old['pid'])+'/stat');assert not p.exists() or p.read_text().rsplit(')',1)[1].split()[19]!=str(old['start_ticks']),'Existing owned finite queue still live'
with (C/'WRITER.lock').open('a') as writer:
    fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB);save(record,{**identity,'phase':'S08','source_identity_sha256':source,'started_utc':now(),'finite_groups':45,'dispatch_S09':False});completed={}
    for v in cfg['candidates']:
        a=v['alias']
        for t in cfg['tasks']:
            seal=A/'candidates'/a/'groups'/(t+'.json')
            if not seal.exists():execute('S08-'+a+'-'+t+'-group-001',['/usr/local/bin/python3',str(C/'run_group.py'),a,t])
            row=json.loads(seal.read_text());assert row['status']=='PASS' and row['source_identity_sha256']==source;completed[a+'|'+t]={'path':str(seal),'sha256':hashlib.sha256(seal.read_bytes()).hexdigest(),'original_audits':row['original_audits'],'audit_actual_calls':row['audit_actual_calls']};save(C/'COMPLETED_GROUPS.json',completed);n=len(completed);audits=sum(x['original_audits'] for x in completed.values());progress=f'S08 independently checked {n}/45taskgroups: {n*156}/7020savedpaths and{n*780}/35100metricvectors; originalfullCVaudits{audits}/105. Private recovery/release/publication pending. S07producer rows unchanged COMPLETE_UNVERIFIED. Finite CPU queue; no S09.\n';save(C/'PROGRESS.md',progress);save(P/'PROGRESS.md',progress);save(T/'PROGRESS.md',progress);resume=json.loads((C/'RESUME_MANIFEST.json').read_text());resume.update(status='S08_FINITE_NUMERICAL_QUEUE_RUNNING',completed_group_receipts=completed,unfinished_scope={'candidate_task_groups':45-n,'saved_paths':7020-n*156,'metric_vectors':35100-n*780,'original_audits':105-audits,'private_recovery_cases':9,'release_overlay':'PENDING'},owned_processes=[identity],next_permitted_action='Continue only missing frozen S08 units; preserve source/runtime/artifacts. Then protect/verify/release/publish within S08; stop before S09.',updated_utc=now());save(C/'RESUME_MANIFEST.json',resume);state=json.loads((T/'CONTROLLER_STATE.json').read_text());state['phase_state']['S08'].update(status='RUNNING',numerical_task_groups_complete=n);state['resume_binding'].update(phase='S08',owned_processes=[identity],unfinished_units=[str(45-n)+' remaining candidate-taskgroups; private recovery/release/publication pending'],reconciled_utc=now());save(T/'CONTROLLER_STATE.json',state)
            with (C/'EVENTS.jsonl').open('a') as f:f.write(json.dumps({'event':'S08_FROZEN_GROUP_PASS','alias':a,'task':t,'completed_groups':n,'completed_original_audits':audits,'observed_utc':now()})+'\n')
        print('S08_CANDIDATE_NUMERICAL_CHECKS_AND_ORIGINAL_AUDITS_COMPLETE',a,flush=True)
print('S08_FINITE_NUMERICAL_QUEUE_DRAINED_PRIVATE_RECOVERY_AND_RELEASE_PENDING',flush=True)
