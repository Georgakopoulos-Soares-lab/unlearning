from ops import run
import sys,fcntl
sys.path.insert(0,'/workspace/pod-a-saliency/artifacts/20261123T111855Z-saliency/S10/attempt-001/code')
from common import *
science=read(C/'S10-science-001-DELIVERY.json');final=read(C/'S10-final-001-DELIVERY.json');meta=read(C/'FINAL_METADATA_RECOVERY_RECEIPT.json');assert science['status']==final['status']==meta['status']=='PASS';commit=final['commit']
def git(s,*args,cwd=R,network=False):return run('S10-final-proof-'+s,['git',*args],cwd,network=network).decode().strip()
assert git('HEAD','rev-parse','HEAD')==commit and git('remote','ls-remote','--exit-code','origin','refs/heads/POD_A_SALIENCY',network=True).split()[0]==commit and git('clean','status','--porcelain')=='';assert git('original-POD-A','rev-parse','POD_A')=='8c651c7ab3c3a2a47f5bbd0e464a69a197512c82'
for phase in range(10):run('S10-final-proof-preserve-'+str(phase),['git','diff','--exit-code',PRIOR,'--',str((T/('S'+str(phase).zfill(2))).relative_to(R))],R)
promptstates=[]
for i,path in enumerate([BASE/'prompts',BASE/'prompts-publish']):
 assert git('prompt-clean-'+str(i),'diff','--name-only','HEAD',cwd=path)=='';promptstates.append({'path':str(path),'HEAD':git('prompt-HEAD-'+str(i),'rev-parse','HEAD',cwd=path),'tracked_changes':False})
receipt=read(P/'S10_RECEIPT.json');assert receipt['status']=='LIMITED_SCOPE_COMPLETE' and receipt['verified_units']==9
for name,h in receipt['output_sha256'].items():assert sha(P/name)==h
state=read(T/'CONTROLLER_STATE.json');assert not state['approvals']['S11']['approved'] and state['phase_state']['S10']['external_dependency_disposition']=='PENDING';handoff=read(P/'S11_HANDOFF.json');assert handoff['S11_permitted_scope']=='RETAIN_ONLY_WITH_EXTERNAL_FORGET_INTEGRATION_PENDING' and handoff['scientific_integration']=='PENDING' and not handoff['S11_executed']
commands=rows(C/'LONG_COMMAND_LEDGER.jsonl');live=[]
for row in commands:
 assert row.get('exit_status') is not None
 p=Path('/proc/'+str(row['pid'])+'/stat')
 if p.exists() and p.read_text().rsplit(')',1)[1].split()[19]==str(row['start_ticks']):live.append({'pid':row['pid'],'start_ticks':row['start_ticks'],'boot_id':row['boot_id']})
assert not live
required=['S10-preflight-001','S10-focused-qualification-001','S10-readiness-001','S10-build-assessment-001','S10-independent-assessment-001','S10-output-validation-001','S10-private-assessment-protection-001','S10-fresh-assessment-regeneration-001','S10-canonical-close-resume-002','S10-scientific-publication-001','S10-final-metadata-protection-001','S10-final-publication-001']
for label in required:
 records=[r for r in commands if r['stage']==label];assert len(records)==1 and records[0]['exit_status']==0,label
locks=[]
for name in ['WRITER.lock','PRIVATE_RECOVERY.lock','RESEARCH_PUBLICATION.lock']:
 with (C/name).open('a') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(lock,fcntl.LOCK_UN)
 locks.append(name)
timeouts=[x for x in rows(C/'COMMAND_LEDGER.jsonl') if x.get('timed_out')];failures=[x for x in commands if x['exit_status']!=0];gpu=run('S10-final-proof-GPU-process-metadata',['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits']).decode();process=run('S10-final-proof-process-metadata',['ps','-eo','pid,ppid,lstart,etime,stat,comm','--sort=pid']).decode();textfile(C/'FINAL_PROCESS_SNAPSHOT.txt',process)
proof={'schema_version':'s10-external-final-delivery-v1','status':'PASS','canonical_package_commit':PACKAGE,'supplement_commit':SUPPLEMENT,'supplement_sha256':SUPP_SHA,'scientific_commit':science['commit'],'final_metadata_commit':commit,'branch':'POD_A_SALIENCY','administrative_disposition':'LIMITED_SCOPE_COMPLETE','scientific_integration':'PENDING','external_dependency_disposition':'PENDING','S11_scope':'RETAIN_ONLY_WITH_EXTERNAL_FORGET_INTEGRATION_PENDING','counts':handoff['counts'],'S10_receipt_sha256':sha(P/'S10_RECEIPT.json'),'S11_handoff_sha256':sha(P/'S11_HANDOFF.json'),'scientific_publication':science,'final_publication':final,'private_assessment_recovery':read(C/'PRIVATE_RECOVERY_RECEIPT.json'),'private_final_metadata_recovery':meta,'verification':read(P/'VERIFICATION.json'),'whole_delivery_inventory':'PARTIAL','actual_layerwise_forget_evidence_available':False,'new_forget_scientific_findings_added':False,'unsent_request_path':str((P/'UNSENT_COLLABORATOR_REQUEST.md').relative_to(R)),'collaborator_messages_sent':0,'S11_executed_or_approved':False,'prior_S00_S09_and_original_POD_A_preserved':True,'prompt_states':promptstates,'known_owned_commands_with_actual_exits':len(commands),'preserved_nonzero_exit_labels':[r['stage'] for r in failures],'metadata_timeouts':len(timeouts),'still_running_known_owned_children':live,'unknown_exits':0,'locks_available':locks,'GPU_metadata_lines':[x for x in gpu.splitlines() if x.strip()],'S10_model_downloads_inference_fits_forget_evaluations':0,'scheduler_observer_shutdown_resize':False,'no_deadline':True,'remaining_limits':read(A/'inputs/LIMITATIONS.json'),'next_direct_approval':'APPROVE S11 at '+PACKAGE,'self_reference':'ExternaltofinalGit/privatearchives; actualexitofthisproofcommandobservedseparatelybylong_run/tool','completed_utc':now()};save(C/'FINAL_DELIVERY_RECEIPT.json',proof);print('S10_FINAL_DELIVERY_VERIFIED',commit,'LIMITED_SCOPE_COMPLETE','scientificintegrationPENDING',flush=True)
