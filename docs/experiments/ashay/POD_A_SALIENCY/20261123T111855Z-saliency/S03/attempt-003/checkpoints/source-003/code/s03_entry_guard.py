"""Read-only S03 authority/source/recovery-scope guard. Never fetches or dispatches."""
from pathlib import Path
import json,hashlib,subprocess

def verify_pinned_package(root):
 root=Path(root);expected='3b089d6b7d7ab16812272a500519db269050c855f0a0f29e3333752d9a62a5e9';raw=(root/'S_SHA256SUMS').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Package checksum-file digest differs from direct approved package')
 checks={}
 for line in raw.decode().splitlines():
  sha,name=line.split('  ',1);p=root/name
  if name in checks or Path(name).is_absolute() or '..' in Path(name).parts or p.is_symlink() or not p.resolve().is_relative_to(root.resolve()):raise ValueError('Unsafe or duplicate approved-package member')
  if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Approved package member bytes changed: '+name)
  checks[name]=sha
 manifest=json.loads((root/'S_PACKAGE_FILES.json').read_text())
 if set(checks)!=set(manifest['files'])|{'S_PACKAGE_FILES.json'}:raise ValueError('Approved package exact member closure differs')
 return expected

def validate_continuation_paths(control,cfg,state):
 c=Path(control);run='20261123T111855Z-saliency';attempt='attempt-003'
 checks=[(cfg['run_id']==state['run_id']==run,'Run identity changed'),(cfg['attempt_id']==attempt,'Wrong continuation attempt'),(c.resolve()==Path('/workspace/pod-a-saliency/control')/run/'S03'/attempt,'Wrong continuation control root'),(Path(cfg['artifacts']).resolve()==Path('/workspace/pod-a-saliency/artifacts')/run/'S03'/attempt,'Wrong continuation artifact root'),(Path(cfg['runtime_venv'])==Path('/workspace/pod-a-saliency/artifacts')/run/'S03/attempt-001/runtime','Pinned inherited runtime changed'),(cfg['mirror_prompt_sha256']=='883a1245a3baa22284aae1261d9f27080ba53bfbe1b2837397dfc633a34b103b','Wrong approved mirror prompt')]
 for value,message in checks:
  if not value:raise ValueError(message)
 return True

def verify_approved_S03(control,alias):
 c=Path(control);cfg=json.loads((c/'RUN_CONFIG.json').read_text());plan=json.loads((c/'PATHS.json').read_text());reg=json.loads((c/'ACCEPTED_CHECKPOINT_REGISTRY.json').read_text());require=lambda value,message: None if value else (_ for _ in ()).throw(ValueError(message))
 require(alias in reg['selected_by_stage'],'Alias outside finite approved S03 scope')
 a=Path(cfg['artifacts']);R=Path(cfg['research_worktree']);T=R/plan['run_root'];state=json.loads((T/'CONTROLLER_STATE.json').read_text())
 require(state['package_commit']==cfg['package_commit']=='7007ebd05bf59432bf69109e5f69baad31ec0d3a','Immutable approved package changed')
 validate_continuation_paths(c,cfg,state)
 require(c.resolve()==Path('/workspace/pod-a-saliency/control')/state['run_id']/'S03'/cfg['attempt_id'],'Unowned control root')
 require(a.resolve()==Path('/workspace/pod-a-saliency/artifacts')/state['run_id']/'S03'/cfg['attempt_id'],'Unowned artifact root')
 require(set(state['approvals']['S03']['scope_candidates'])==set(reg['experimental_candidate_ids']),'Experimental candidate scope changed')
 require(alias=='base' or reg['selected_by_stage'][alias] in state['approvals']['S03']['scope_candidates'],'Unapproved candidate')
 require(alias!='base' or reg['selected_by_stage'][alias]==reg['shared_original_base_reference'],'Original pretrained reference substituted')
 require(json.loads((c/'PARENT_TRAINING_MEMBERSHIP_VERIFICATION.json').read_text())['status']=='PASS_INDEPENDENT_FROZEN_PARENT_TRAIN_MEMBERSHIP','Training-only witness membership not qualified')
 protection=json.loads((c/'MINIMUM_PRIVATE_CHECKPOINT_RECEIPT.json').read_text());require(protection['status']=='MINIMUM_ACTUAL_ARTIFACTS_PRIVATE_FRESH_RESTORE_VERIFIED' and protection['destination_private'] and protection['fresh_network_download'] and protection['rebuilt_TE_wheel_protected'],'Actual minimum private protection missing')
 require(hashlib.sha256((c/'MINIMUM_PRIVATE_CHECKPOINT_RECEIPT.json').read_bytes()).hexdigest()==cfg['minimum_private_protection_receipt_sha256'],'Private protection receipt changed')
 require(hashlib.sha256((c/'PROMPT.md').read_bytes()).hexdigest()==cfg['mirror_prompt_sha256'],'Checksum-pinned continuation prompt changed')
 require(hashlib.sha256((c/'MIRROR_ADMISSION.json').read_bytes()).hexdigest()==cfg['mirror_admission_sha256'],'Exact remote mirror admission binding changed')
 approved=next((v for v in json.loads((c/'MIRROR_ADMISSION.json').read_text())['records'] if v['alias']==alias),None);require(approved is not None and approved['candidate_id']==reg['selected_by_stage'][alias],'Alias lacks exact approved mirror')
 local=next((v for v in json.loads((c/'MIRROR_LOCAL_ADMISSION.json').read_text())['records'] if v['alias']==alias),None);require(local is not None and local['status']=='LOCAL_NATIVE_SHA256_AND_MAPPING_PASS' and local['manifest_sha256']==approved['manifest_sha256'] and local['payload_revision']==approved['payload_revision'],'Actual immutable local native recovery not verified')
 expected=next(v for v in approved['files'] if v['path']=='__0_0.distcp');require(local['native_sha256']==expected['sha256'],'Recovered native identity changed')
 root=Path(plan['package_root']);verify_pinned_package(root);checked=subprocess.run([cfg['validator_python'],str(root/'S_validate_package.py'),'--root',str(root),'--entry','S03','--action','substantial_compute','--state',str(T/'CONTROLLER_STATE.json'),'--research-worktree',str(R)],capture_output=True,text=True,timeout=15);require(checked.returncode==0,'Actual S03 guard rejected entry: '+checked.stdout[:1000])
 return {'package_commit':state['package_commit'],'alias':alias,'candidate_id':reg['selected_by_stage'][alias],'source_worktree':str(R),'dispatch':False}
