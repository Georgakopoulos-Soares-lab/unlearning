"""Read-only S03 authority/source/recovery-scope guard. Never fetches or dispatches."""
from pathlib import Path
import json,hashlib,subprocess

def verify_approved_S03(control,alias):
 c=Path(control);cfg=json.loads((c/'RUN_CONFIG.json').read_text());plan=json.loads((c/'PATHS.json').read_text());reg=json.loads((c/'ACCEPTED_CHECKPOINT_REGISTRY.json').read_text());require=lambda value,message: None if value else (_ for _ in ()).throw(ValueError(message))
 require(alias in reg['selected_by_stage'],'Alias outside finite approved S03 scope')
 a=Path(cfg['artifacts']);R=Path(cfg['research_worktree']);T=R/plan['run_root'];state=json.loads((T/'CONTROLLER_STATE.json').read_text())
 require(state['package_commit']==cfg['package_commit']=='7007ebd05bf59432bf69109e5f69baad31ec0d3a','Immutable approved package changed')
 require(cfg['run_id']==state['run_id'] and cfg['attempt_id']=='attempt-001','Run or attempt identity changed')
 require(c.resolve()==Path('/workspace/pod-a-saliency/control')/state['run_id']/'S03'/cfg['attempt_id'],'Unowned control root')
 require(a.resolve()==Path('/workspace/pod-a-saliency/artifacts')/state['run_id']/'S03'/cfg['attempt_id'],'Unowned artifact root')
 require(set(state['approvals']['S03']['scope_candidates'])==set(reg['experimental_candidate_ids']),'Experimental candidate scope changed')
 require(alias=='base' or reg['selected_by_stage'][alias] in state['approvals']['S03']['scope_candidates'],'Unapproved candidate')
 require(alias!='base' or reg['selected_by_stage'][alias]==reg['shared_original_base_reference'],'Original pretrained reference substituted')
 require(json.loads((c/'PARENT_TRAINING_MEMBERSHIP_VERIFICATION.json').read_text())['status']=='PASS_INDEPENDENT_FROZEN_PARENT_TRAIN_MEMBERSHIP','Training-only witness membership not qualified')
 protection=json.loads((c/'MINIMUM_PRIVATE_CHECKPOINT_RECEIPT.json').read_text());require(protection['status']=='MINIMUM_ACTUAL_ARTIFACTS_PRIVATE_FRESH_RESTORE_VERIFIED' and protection['destination_private'] and protection['fresh_network_download'] and protection['rebuilt_TE_wheel_protected'],'Actual minimum private protection missing')
 require(hashlib.sha256((c/'MINIMUM_PRIVATE_CHECKPOINT_RECEIPT.json').read_bytes()).hexdigest()==cfg['minimum_private_protection_receipt_sha256'],'Private protection receipt changed')
 root=Path(plan['package_root']);checked=subprocess.run([cfg['validator_python'],str(root/'S_validate_package.py'),'--root',str(root),'--entry','S03','--action','substantial_compute','--state',str(T/'CONTROLLER_STATE.json'),'--research-worktree',str(R)],capture_output=True,text=True,timeout=15);require(checked.returncode==0,'Actual S03 guard rejected entry: '+checked.stdout[:1000])
 return {'package_commit':state['package_commit'],'alias':alias,'candidate_id':reg['selected_by_stage'][alias],'source_worktree':str(R),'dispatch':False}
