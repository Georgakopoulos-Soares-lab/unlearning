from ops import run
import sys,shutil,fcntl,importlib.metadata as md
sys.path.insert(0,'/workspace/pod-a-saliency/artifacts/20261123T111855Z-saliency/S10/attempt-001/code')
from common import *
with (C/'WRITER.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def git(label,*args,cwd=R,network=False):return run('S10-preflight-'+label,['git',*args],cwd,network=network).decode().strip()
 assert git('origin','remote','get-url','origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git' and git('branch','branch','--show-current')=='POD_A_SALIENCY';assert git('HEAD','rev-parse','HEAD')==PRIOR and git('POD_A','rev-parse','POD_A')=='8c651c7ab3c3a2a47f5bbd0e464a69a197512c82';assert git('clean','status','--porcelain')=='';run('S10-preflight-ancestry',['git','merge-base','--is-ancestor','8c651c7ab3c3a2a47f5bbd0e464a69a197512c82','HEAD'],R);assert git('remote-head','ls-remote','--exit-code','origin','refs/heads/POD_A_SALIENCY',network=True).split()[0]==PRIOR
 promptstates=[]
 for i,d in enumerate([BASE/'prompts',BASE/'prompts-publish']):
  assert git('prompt-origin-'+str(i),'remote','get-url','origin',cwd=d)=='https://github.com/ashay-sriv-06/test-prompts-push.git';assert git('prompt-clean-'+str(i),'diff','--name-only','HEAD',cwd=d)=='';promptstates.append({'path':str(d),'HEAD':git('prompt-HEAD-'+str(i),'rev-parse','HEAD',cwd=d),'tracked_changes':False})
 assert git('supplement-object','rev-parse',SUPPLEMENT+'^{commit}',cwd=BASE/'prompts')==SUPPLEMENT;blob=run('S10-preflight-supplement-git-show',['git','show',SUPPLEMENT+':s10.md'],BASE/'prompts');assert hashlib.sha256(blob).hexdigest()==sha(C/'PROMPT.md')==SUPP_SHA
 assert sha(PKG/'S_SHA256SUMS')==PACKAGE_SHA
 package_members=[]
 for line in (PKG/'S_SHA256SUMS').read_text().splitlines():
  h,n=line.split(None,1);assert sha(PKG/n)==h;package_members.append(n)
 # Reuse completed S09 numerical and full-archive recovery witnesses; only recheck consumed metadata/seals.
 c9=C.parent.parent/'S09/attempt-001';p9=T/'S09/attempt-001';proof=read(c9/'FINAL_DELIVERY_RECEIPT.json');witness=read(c9/'FINAL_ACTUAL_EXIT_WITNESS.json');assert proof['status']==witness['status']=='PASS' and proof['final_metadata_commit']==PRIOR and witness['final_proof_actual_exit']==0 and witness['final_proof_sha256']==sha(c9/'FINAL_DELIVERY_RECEIPT.json');assert not proof['still_running_known_owned_children']
 for row in rows(c9/'LONG_COMMAND_LEDGER.jsonl'):
  q=Path('/proc/'+str(row['pid'])+'/stat');assert row['exit_status'] is not None and (not q.exists() or q.read_text().rsplit(')',1)[1].split()[19]!=str(row['start_ticks']))
 prior_receipt=read(p9/'S09_RECEIPT.json');state=read(T/'CONTROLLER_STATE.json');assert state['phase_receipts']['S09']['sha256']==sha(p9/'S09_RECEIPT.json');handoff=read(p9/'S10_HANDOFF.json');assert sha(p9/'S10_HANDOFF.json')=='cd7de3bd268d6f9671d90986d7bf2a0df21f1852f1820cf791129737393c625e';assert prior_receipt['verified_units']==handoff['all_admitted_keys']==48924 and handoff['all_deferred_keys']==42228 and handoff['reused_classification_metrics']==42120 and handoff['reused_LM_units']==108 and handoff['reused_LM_metric_rows']==216 and len(handoff['candidates'])==9
 ir=A/'inputs';ir.mkdir();consumed={}
 for name in ['S10_HANDOFF.json','S10_INPUT_REQUIREMENTS.json','COMPARISON_DISPOSITION.json','LIMITATIONS.json','CANDIDATES.json','PRIVATE_RECOVERY_PROOF.json','FINAL_METADATA_RECOVERY.json','DELIVERY_CONTEXT.json','FINAL_RESOURCE_RECONCILIATION.json']:
  path=p9/name
  if name in prior_receipt['output_sha256']:assert sha(path)==prior_receipt['output_sha256'][name]
  shutil.copy2(path,ir/name);consumed[str(path.relative_to(R))]={'sha256':sha(path),'commit':PRIOR,'bytes':path.stat().st_size}
 payloads=read(T/'S03/attempt-003/PAYLOAD_IDENTITIES.json');assert len(payloads['payloads'])==9;qualified=[]
 for candidate in handoff['candidates']:
  v=next(x for x in payloads['payloads'] if x['alias']==candidate['alias']);assert v['model_tensor_content_sha256']==candidate['content_sha256'] and v['candidate_id']==candidate['candidate_id'];members={x['relative_payload_member']:x for x in v['members']};qualified.append({**candidate,'identity_type':'logical_model_tensor_content_sha256','native_shard_sha256':v['native_shard_sha256'],'config_sha256':members['run_config.yaml']['SHA256'],'tokenizer_sha256':members['tokenizer/tokenizer.json']['SHA256'],'payload_manifest_sha256':v['manifest_sha256'],'conversion_or_adapter_identity':None,'conversion_null_reason':'No additional S10 conversion/adapter binding supplied; use established native S03 mapping only','immediate_parent_id':None,'parent_null_reason':'Unresolved; does not block checkpoint-specific description, blocks parent-relative claims'})
 save(ir/'CANDIDATE_BINDINGS.json',qualified)
 # Freeze a finite discovery scope. Names only outside explicitly safe committed metadata.
 metadata=rows(T/'S01/attempt-001/REMOTE_OBJECTS.jsonl');assert len(metadata)==148
 tokenhits=[x for x in metadata if any(k in x['object_name'].lower() for k in ['forget','evaluation','aggregate','result','metric','.csv','.tsv'])]
 assert not tokenhits,'A possible supplied aggregate must be assessed before no-data admission'
 topnames={}
 for label,path in [('research_run',T),('control_run',C.parent.parent),('artifact_run',A.parent.parent)]:
  entries=list(path.iterdir());assert len(entries)<128;topnames[label]=[{'name':p.name,'type':'directory' if p.is_dir() else 'file'} for p in sorted(entries)]
 evidence=[]
 for phase,name in [('S01/attempt-001','UNRESOLVED_INPUTS.json'),('S01/attempt-001','REMOTE_OBJECTS.jsonl'),('S01/attempt-001','LISTING_COVERAGE.json')]:
  q=T/phase/name;evidence.append({'path':str(q.relative_to(R)),'commit':PRIOR,'sha256':sha(q),'bytes':q.stat().st_size});shutil.copy2(q,ir/name)
 scope={'schema_version':'s10-bounded-discovery-v1','status':'FROZEN_NO_AGGREGATE_SUPPLIED_IN_INSPECTED_SCOPE','latest_chat_aggregate_attachments_or_data_locators':[],'S09_external_state':read(ir/'S10_INPUT_REQUIREMENTS.json')['external_state'],'S01_snapshot_objects_observed':148,'S01_snapshot_possible_aggregate_name_hits':[],'S01_snapshot_is_partial_and_not_current_Drive_listing':True,'existing_provenance_records':evidence,'one_level_locations_inspected':topnames,'external_aggregate_sources':[],'external_source_records':[],'new_remote_Drive_or_account_searches':0,'recursion_outside_owned_attempt':False,'excluded':'No raw/per-example forget datasets, predictions, losses, model archives or training-config dataset paths opened. No inference of absence outside this finite snapshot/chat/handoff scope.','new_inputs_policy':'New later inputs require versioned source manifest/new authorized attempt; do not poll','frozen_utc':now()};save(ir/'DISCOVERY_MANIFEST.json',scope)
 baseline=read(ir/'FINAL_RESOURCE_RECONCILIATION.json')['remaining_conservative_lower_bound_bytes'];envelope=1024**3;assert baseline-envelope>64*1024**3;cg={n:Path('/sys/fs/cgroup/'+n).read_text().strip() for n in ['cpu.max','memory.max','memory.current']};headroom=int(cg['memory.max'])-int(cg['memory.current']);assert headroom>2*1024**3
 save(C/'RESOURCE_ADMISSION.json',{'status':'PASS','starting_precharged_S09_remaining_lower_bound_bytes':baseline,'new_S10_envelope_bytes':envelope,'remaining_after_envelope_bytes':baseline-envelope,'storage_reserve_bytes':64*1024**3,'metadata_only_worker_limit':1,'thread_limit':1,'worker_RSS_limit_bytes':1024**3,'minimum_memory_headroom_bytes':2*1024**3,'observed_cgroup_headroom_bytes':headroom,'cgroups':cg,'provider_quota_and_billing':None,'shared_df_not_provider_quota':True,'no_GPU_or_scientific_runtime_modification':True,'observed_utc':now()})
 save(C/'PROMPT_RECEIPT.json',{'repository':'https://github.com/ashay-sriv-06/test-prompts-push.git','path':'s10.md','supplement_commit':SUPPLEMENT,'supplement_sha256':SUPP_SHA,'bytes':len(blob),'canonical_package_commit':PACKAGE,'canonical_package_digest':PACKAGE_SHA,'read_in_full':True,'preferred_connector_fetch_succeeded':True,'verbatim_exact_Git_blob':'PROMPT.md','prompt_checkouts_preserved':promptstates,'observed_utc':now()})
 message='''Given everything we have accomplished so far, give me all the most rigorous, robust, awesome, long horizon, highest level of precision execution to make sure that we get the most solid work out in s10 - https://github.com/ashay-sriv-06/test-prompts-push/blob/POD-A-Saliency/s10.mdAPPROVE S10 at 7007ebd05bf59432bf69109e5f69baad31ec0d3a

This is my direct chat authorization to execute S10 now, including its prescribed verification, private recovery and publication.

Fetch, read fully and execute this exact supplement:
https://github.com/ashay-sriv-06/test-prompts-push/blob/dea058fb1ed5c7f475f8de5d25d93b6af23ec730/s10.md

The supplement commit is distinct from the canonical approval pin above. Record both identities and the supplement SHA256.

Resume valid existing work. Run the entry guard using THIS chat authorization, then continue through the entire authorized S10 scope without stopping at preview readiness or requesting approval between batches. Resolve routine implementation failures, preserve their evidence, and reverify affected outputs without repeating unaffected completed work.

If collaborator forget aggregates are absent or incompatible, follow the prescribed LIMITED_SCOPE_COMPLETE path: finish the assessment, pending-input ledger, unsent collaborator request, recovery, publication and S11 handoff. Keep scientific integration explicitly pending; do not wait indefinitely or fabricate results.

Provide concise progress updates and persist resumable checkpoints. Stop early only for a concrete blocker that prevents further authorized work, explaining exactly what is needed.

Preserve prior results, frozen methods, branch boundaries and the no-deadline amendment. No raw forget evaluation or collaborator messages.

Finish with verified delivery identities, exact coverage, remaining dependencies and process/lock status. Stop before S11.'''
 save(C/'APPROVAL_RECORD.json',{'phase':'S10','package_commit':PACKAGE,'source':'direct_chat','message':'APPROVE S10 at '+PACKAGE,'verbatim_user_message':message,'supplement_commit':SUPPLEMENT,'supplement_sha256':SUPP_SHA,'ordinary_repair_recovery_publication_authorized':True,'collaborator_messages_authorized':False,'no_deadline':True,'observed_utc':now()})
 save(C/'PREDECESSOR_REUSE.json',{'status':'PASS','S09_final_commit':PRIOR,'S09_scientific_commit':proof['scientific_commit'],'final_delivery_proof_sha256':sha(c9/'FINAL_DELIVERY_RECEIPT.json'),'actual_exit_witness_sha256':sha(c9/'FINAL_ACTUAL_EXIT_WITNESS.json'),'consumed_metadata':consumed,'large_scientific_payloads_rehashed':False,'completed_probes_draws_figures_recomputed':False,'canonical_package_members_verified':len(package_members),'unchanged_passing_self_tests_reused':True,'prompt_states':promptstates})
 save(C/'CONTROLLER_STATE.before-S10.json',state);state['approvals']['S10']={'approved':True,'package_commit':PACKAGE,'source':'direct_chat','message':'APPROVE S10 at '+PACKAGE,'observed_utc':now(),'scope_candidates':[x['candidate_id'] for x in qualified]};state['phase_state']['S10'].update(status='PINNED',approved=True,attempt_id='attempt-001');assert not state['approvals']['S11']['approved'];state['resume_binding'].update(phase='S10',attempt_id='attempt-001',package_commit=PACKAGE,supplement_commit=SUPPLEMENT,unfinished_units=['Finite bounded aggregate assessment','Independent verification','Private metadata/integration recovery','Publication and S11 handoff'],transfer_totals={},owned_processes=[],unresolved_decisions=['No collaborator aggregate supplied in bounded available scope; layerwise forget remains absent'],next_action='Validate S10 entry under this directchatapproval, qualify metadata pipeline, finish no-data disposition unless a supplied aggregate is explicitly identified.',prerequisites=['Preserve S09 science, deferred contrasts and all canonical pins'],reconciled_utc=now(),single_writer_verified=True);save(T/'CONTROLLER_STATE.json',state)
 result=json.loads(run('S10-canonical-entry-001',['/usr/local/bin/python3',str(PKG/'S_validate_package.py'),'--root',str(PKG),'--entry','S10','--state',str(T/'CONTROLLER_STATE.json'),'--research-worktree',str(R)]));assert result['entry']['status']=='ENTRY_PASS';save(C/'ENTRY_VALIDATION.json',result)
 gpu=run('S10-preflight-GPU-metadata',['nvidia-smi','--query-gpu=name,memory.total,memory.used','--format=csv,noheader,nounits']).decode();process=run('S10-preflight-process-metadata',['ps','-eo','pid,ppid,lstart,etime,stat,comm','--sort=pid']).decode();textfile(C/'PROCESS_METADATA.txt',process);save(C/'RUNTIME_METADATA.json',{'metadata_python':sys.executable,'jsonschema_version':md.version('jsonschema'),'GPU_metadata_only':gpu.strip(),'S09_numerical_runtime_untouched':True,'new_runtime_installs':0})
 P.mkdir(parents=True);progress('ENTRY_PASS_BOUNDED_SCOPE_FROZEN','Qualify producer/parser and separate independent reconciler fixtures, then finalize assessment readiness; do not execute S11.',completed_units=['immutable supplemental retrieval/read','predecessor seal reconciliation','bounded source snapshot','canonical entry guard'],unfinished_units=state['resume_binding']['unfinished_units'],owned_processes=[],transfers={'new_model_download_bytes':0,'new_aggregate_download_bytes':0})
 for name in ['APPROVAL_RECORD.json','PROMPT_RECEIPT.json','ENTRY_VALIDATION.json','PREDECESSOR_REUSE.json','RESOURCE_ADMISSION.json']:shutil.copy2(C/name,P/name)
 print('S10_ENTRY_PASS',SUPPLEMENT,SUPP_SHA,'bounded_external_sources',0,flush=True)
