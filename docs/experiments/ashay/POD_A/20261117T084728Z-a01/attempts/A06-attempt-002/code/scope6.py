"""Direct-approval, immutable-manifest and stage-owned write guards; no model import."""
from pathlib import Path
import json,hashlib,os
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-002')
PIN='4ff94e09b72a02d6e3082af064669c98adda6008';PLAN='06d290bdc76404a8dcfe25da6f057fc78f868364cc1d2e8aa6df77791f0bdfa3';MODEL='9cab388a46a873902317ff022ab0b9a43d3e42c8753d3842837f74f5dd474259'
def require(v,why):
 if not v:raise ValueError(why)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def authorize(candidate):
 require(candidate=='R5','Only R5 authorized');cfg=read(C/'RUN_CONFIG.json');ap=read(C/'APPROVAL_RECORD.json');inp=read(C/'A06_INPUTS.json');require(cfg['stage']==ap['stage']=='A06' and cfg['attempt_id']==ap['attempt_id']=='A06-attempt-002','Wrong stage/attempt');require(cfg['prompt_commit']==ap['prompt_commit']==PIN and cfg['coverage_plan_sha256']==ap['coverage_plan_sha256']==PLAN,'Stale prompt/plan');require(ap.get('direct_user_message','').startswith('👍 A06 at '+PIN),'No exact direct approval');require(sha(C/'APPROVAL_RECORD.json')==inp['approval']['sha256'],'Approval receipt changed');require(inp['checkpoint_identities']['R5']['model_tensor_content_sha256']==MODEL,'Wrong R5 content');require(Path(cfg['control']).resolve()==C and Path(cfg['artifacts']).resolve()==Path('/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002'),'Historical/root escape');return cfg,inp
def h3_specs(candidate):
 authorize(candidate);manifest=read(C/'A06_EXECUTION_MANIFEST.json');units=manifest['H3_head_application_units'];specs=[(candidate,e['array_key'],e['seed']) for e in units];require(len(specs)==78 and len(set(specs))==78 and all(e['owner_stage']=='A06' and e['task']=='emp_H3' and e['coverage_plan_sha256']==PLAN for e in units),'Wrong H3 finite unit set');return specs
def verify_gate(candidate,task,control):
 require(candidate=='R5','Foreign candidate gate');require(Path(control).resolve()==C,'Wrong gate control')
 if task=='emp_H3':return
 require(task in ['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'],'Unknown task');p=C/'H3_GATE_R5.json';require(p.is_file(),'Other-five denied before H3 gate');j=read(p);require(j.get('status')=='PASS' and j.get('candidate')=='R5' and j.get('backup_status')=='PASS' and j.get('coverage_plan_sha256')==PLAN and j.get('model_content_sha256')==MODEL,'Unpassed/stale/unprotected R5 gate');require(all(j.get('components',{}).get(k) is True for k in ['adapter','features','heads78','applications78','all_unit_audit','six_full_CV_refits','LM','private_fresh_recovery']),'Incomplete technical gate')
 for e in j.get('local_dependencies',[]):require(sha(e['path'])==e['sha256'],'Gate dependency changed')
 require(len(j.get('local_dependencies',[]))>=3,'Missing exact gate dependency seals')
