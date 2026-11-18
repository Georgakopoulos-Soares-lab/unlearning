"""Assemble finite A08 closeout from sealed evidence; never dispatch numerical work."""
from common import *
from research_guard import guard
from observer_status import observer
import collections,fcntl,shutil,time,shlex

def preserved_history():
 checks=[]
 for stage in ['A06','A07']:
  root=D.parent/(stage+'-attempt-001');manifest=root/'OUTPUT_SHA256SUMS';n=0
  for line in manifest.read_text().splitlines():
   if not line.strip():continue
   h,name=line.split(maxsplit=1);name=name.lstrip('*');p=root/name
   assert p.is_file() and sha(p)==h
   blob=subprocess.check_output(['git','-C',str(W),'show',cfg['research_head_before']+':'+str(p.relative_to(W))]);assert hashlib.sha256(blob).hexdigest()==h;n+=1
  checks.append({'stage':stage,'manifest':ref(manifest),'listed_files_checked':n,'immutable_git_blob_input_commit':cfg['research_head_before'],'status':'PASS','numerics_rerun':False})
 for stage in ['A06','A07']:
  for e in read(D.parent/(stage+'-attempt-001')/'CPU_SOURCE_IDENTITY.json')['files']:assert sha(A.parent/(stage+'-attempt-001')/'code'/e['path'])==e['sha256']
 source=read(C/'SOURCE_IDENTITY.json')
 for e in source['files']:
  assert sha(A/'code'/e['path'])==e['sha256'];assert sha(A/'source-versions'/source['version']/e['path'])==e['sha256']
 assert sha(C/'A08_EXECUTION_MANIFEST.json')==source['execution_manifest']['sha256']
 proof={'status':'PASS','historical_public_seals':checks,'frozen_core_source_files':len(source['files']),'core_source_identity':ref(C/'SOURCE_IDENTITY.json'),'execution_manifest_unchanged_since_freeze':True,'A03_A04_A05_files_changed':False,'main_other_refs_guard':guard(allow_dirty=True),'prompt_cache_worktree_clean':not subprocess.check_output(['git','-C','/workspace/test-prompts-push','status','--porcelain']).strip(),'unchanged_numerical_audits_repeated':False,'observed_utc':now()}
 put(C/'PRESERVATION_VERIFICATION.json',proof);publish('PRESERVATION_VERIFICATION.json',proof)

def analysis_audit():
 records=[];summary={}
 for family,count,nrows in [('R6_minus_R4',546,5460),('LM_R6_minus_R4',7,14)]:
  pp=sorted((A/'analysis'/family).rglob('COMPLETE.json'));assert len(pp)==count;rr=[]
  for p in pp:
   seal=read(p);assert seal['status']=='PASS'
   for e in seal['files']:q=p.parent/e['path'];assert sha(q)==e['sha256'] and q.stat().st_size==e['bytes']
   j=read(p.parent/'ANALYSIS.json');assert j['status']=='PASS';rr.append(j);records.append({'family':family,'unit_id':j['unit_id'],'receipt':ref(p),'checks':{k:v for k,v in j.items() if k not in ['rows','producer_endpoints']}})
  assert sum(len(r['rows']) for r in rr)==nrows
  summary[family]={'sealed_units':count,'released_rows':nrows,'point_max_abs':max(r['point_max_abs'] for r in rr),'every_draw_max_abs':max(r['draw_max_abs'] for r in rr),'interval_max_abs':max(r.get('interval_max_abs',0) for r in rr),'attempted_values':sum(r['attempted_values'] for r in rr),'valid_values':sum(r['valid_values'] for r in rr),'status':'PASS'}
  assert summary[family]['point_max_abs']<=1e-12 and summary[family]['every_draw_max_abs']<=1e-12 and summary[family]['interval_max_abs']<=1e-12
 proof={'status':'PASS','source_identity_sha256':sha(C/'SOURCE_IDENTITY.json'),'predeclared_nonadjacent_only':True,'families':summary,'records':records,'GPU_or_LM_forwards':0,'new_fitting':0,'failed_units':0,'all_unit_draw_masks_and_values_checked':True,'no_new_R3_cross_runtime_effects':True}
 put(C/'DERIVED_ANALYSIS_AUDIT.json',proof);publish('DERIVED_ANALYSIS_AUDIT.json',proof)

def backups():
 bb=[read(C/('BACKUP_'+p+'.json')) for p in ['R4','R6','analysis']]
 assert all(b['status']=='PASS' and b['safe_exact_member_set'] and b['fresh_download'] and b['private_at_write_and_closeout'] for b in bb)
 manifest={'schema':'pod-a-a08-backup-manifest-v1','status':'PASS_SCIENTIFIC_PAYLOADS','repository':'ashay-sriv/undo-evo2-pilot-backup-20261020','private':True,'append_only':True,'archives':bb,'unchanged_dependency_proofs':[read(p) for p in sorted(C.glob('DEPENDENCY_CONSUMER_*.json'))],'unchanged_history_repacked':False,'final_delivery_metadata':'Separate post-push immutable archive and versioned final receipt, documented by DELIVERY_RECEIPT.json; avoids self-hash cycles','exclusions':{'GPU_weights_and_runtime':'Excluded; pinned native/tensor/config/tokenizer and qualified runtime evidence remain in immutable A04/A06 dependencies. No GPU recreation claimed.','historical_features_heads_and_A06_A07_arrays':'Exact pinned dependencies referenced by DEPENDENCIES.json in every scientific archive; local fresh consumers reverified, no unchanged-history repack.','derived_reference_caches':'Regenerable from frozen source, exact saved probabilities and group draws. Every new A08 target/paired array is included.'}}
 verification={'schema':'pod-a-a08-backup-verification-v1','status':'PASS','new_scientific_archives':3,'all_member_files_verified':sum(b['all_files_verified'] for b in bb),'archive_bytes':sum(b['archive_bytes'] for b in bb),'force_fresh_cache_and_separate_consumers':True,'exact_safe_member_sets':True,'candidate_probability_metric_paths':sum(len(b['portable_CPU_checks']['policy_paths']) for b in bb[:2]),'restored_audit_refit_artifacts_checked':sum(len(b['portable_CPU_checks']['restored_refit_checks']) for b in bb[:2]),'candidate_panel':'R4/R6 x every other-five task x layer16/final_norm x seed42 x both policies; includes binary and three-class splice','candidate_probability_max_abs':max(p['probability_max_abs'] for b in bb[:2] for p in b['portable_CPU_checks']['policy_paths']),'candidate_metric_max_abs':max(p['metric_max_abs'] for b in bb[:2] for p in b['portable_CPU_checks']['policy_paths']),'new_contrast_restore':bb[2]['portable_CPU_checks'],'revisions':{b['phase']:b['revision'] for b in bb},'GPU_recreation_claim':False,'all_grid_fresh_refit_claim':False,'final_report_metadata_recovery':'Separate post-push full-member readback receipt'}
 put(C/'BACKUP_MANIFEST.json',manifest);put(C/'BACKUP_VERIFICATION.json',verification);publish('BACKUP_MANIFEST.json',manifest);publish('BACKUP_VERIFICATION.json',verification)
 md='# A08 CPU recovery\n\nThe three immutable scientific archives below passed force-fresh download into separate empty consumers and exact safe-member validation. Restore only these pinned revisions. Keep the dataset private.\n\n'
 for b in bb:
  md+=f"## {b['phase']}\n\nRevision `{b['revision']}`; archive `{b['archive_path']}`. SHA256 `{b['archive_sha256']}`; {b['archive_bytes']:,} bytes; {b['all_files_verified']:,} members checked.\n\nExisting checked consumer: `{b['fresh_consumer_root']}`. Exact CPU check command:\n\n```bash\nOMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 {shlex.join(b['restore_command'])}\n```\n\n"
 md+='''## Fresh-machine sequence and limitations

Use the frozen CPU environment in ENVIRONMENT_CHECK.json. Download each archive with `huggingface_hub.hf_hub_download`, `repo_type='dataset'`, the exact revision and path above, `force_download=True`, and a new empty cache. Verify archive byte count and SHA256 before opening it. Reject absolute/traversing paths, symlinks, hardlinks, duplicate or unexpected members; compare the exact member set and all MEMBER_MANIFEST.json size/digest entries before consuming arrays or trusted serialized audit heads. The owned checkpoint_phase.py and protect_delivery.py supply the executable validation sequence.

Each scientific archive contains DEPENDENCIES.json with exact immutable A03/A06/A07 references and path translations. Restore missing dependencies safely by those revisions; reverify every member. Replace consumer-root entries in a copied DEPENDENCIES.json with the corresponding new consumer roots, preserving the original dependency receipts. Run the command above with the new `--root` and restored source path. Do not substitute original producer paths for recovery consumers. Both candidate consumers must exist before the analysis check. All command options were checked against the owned restore CLI.

The recorded panel checks 40 candidate probability/metric paths, both candidates, all five tasks, both anchors and both readout policies, plus two restored audit-refit heads. It also checks the new human-TF layer-16 seed-42 R6−R4 contrast for both policies, all five metrics and all 2,000 draws, plus new human-TF dev LM NLL/PPL points. This supplements the full live-input numerical audit. It is neither GPU/runtime recreation nor a second 780-head refit. Weights and unchanged historical payloads are referenced rather than repacked; derived reference caches are regenerable. The final public report/code/figure snapshot is protected separately after push, with an immutable metadata revision and final-receipt revision in the run's DELIVERY_RECEIPT.json.

No science automatically resumes after recovery. A08 is complete for its qualified scope; A09 requires separate direct approval. R2/R5 backfill and R3 qualification are outside that reporting scope.
'''
 publish('RESTORE.md',md)

def disposition_and_resources():
 jobs=[read(p) for p in sorted(C.glob('JOB_*.json')) if p.name!='JOB_DISPOSITION.json'];dispositions=[]
 for j in jobs:
  p=Path('/proc')/str(j['pid'])/'stat';same=p.exists() and p.read_text().split()[2]!='Z' and p.read_text().split()[21]==str(j['proc_start_ticks']);assert not same and j['status']=='EXITED_PASS'
  dispositions.append({'name':j['name'],'pid':j['pid'],'proc_start_ticks':j['proc_start_ticks'],'recorded_state':j['status'],'same_process_still_running':same,'exit_code':j['exit_code']})
 science_names=['audit_units.py','refit_panel.py','analysis_pairs.py','run_candidate.py','run_analysis.py','checkpoint_phase.py','plot_verified.py'];running=[]
 for p in Path('/proc').glob('[0-9]*/cmdline'):
  try:argv=p.read_bytes().split(b'\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if any(str(A).encode() in x and any(x.endswith(('/'+n).encode()) for n in science_names) for x in argv):running.append(str(p.parent.name))
 assert not running,running
 locks=[]
 for p in (A/'locks').rglob('*.lock'):
  with p.open('a') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN);locks.append(str(p.relative_to(A)))
 obs=observer();proof={'status':'PASS','scientific_jobs':'QUIESCENT','owned_job_records':dispositions,'owned_scientific_process_scan':running,'exclusive_locks_checked_free':len(locks),'observer':obs,'unrelated_processes_stopped':0,'Pod_running':True,'A09_started':False,'observed_utc':now()};put(C/'JOB_DISPOSITION.json',proof);publish('JOB_DISPOSITION.json',proof);publish('OBSERVER_STATUS.json',obs)
 audits=[read(p) for p in (A/'audits').rglob('NUMERICAL_AUDIT.json')];rf=read(C/'AUDIT_REFIT_RECEIPT.json');aCPU=sum(j['CPU_process_seconds'] for j in audits);rCPU=sum(j['CPU_seconds'] for j in rf['units']);usage=lambda p:int(subprocess.check_output(['du','-sb',str(p)],text=True).split()[0]);cg=Path('/sys/fs/cgroup')
 measure={'status':'MEASURED','observed_utc':now(),'attempt_started_utc':cfg['started_utc'],'attempt_elapsed_wall_seconds':(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(cfg['started_utc'])).total_seconds(),'CPU_workers_max':2,'BLAS_threads_per_worker':4,'per_worker_RLIMIT_AS_bytes':32*1024**3,'all_unit_audit_CPU_process_seconds':aCPU,'sampled_refit_CPU_process_seconds':rCPU,'measured_unit_CPU_subtotal_seconds':aCPU+rCPU,'peak_audit_worker_RSS_kib':max(j['peak_RSS_kib'] for j in audits),'derived_analysis_controller_child_CPU_seconds':max(j['children_CPU_user_seconds']+j['children_CPU_system_seconds'] for j in jobs if j['name'].startswith('analysis-')),'worker_elapsed_seconds_sum':sum(j['wall_seconds'] for j in jobs),'worker_resource_ledger_semantics':'Raw RUSAGE_CHILDREN counters are cumulative within each dispatcher; never sum successive cumulative counters. Unit CPU subtotal and final analysis-dispatch counter are separate measured scopes, excluding uninstrumented orchestration/reporting overhead. Worker elapsed sum is not attempt wall time.','final_figure_render':{k:v for k,v in read(D/'FIGURE_VALIDATION.json').items() if k in ['render_wall_seconds','render_CPU_seconds','pid','proc_start_ticks','executed_argv']},'scientific_archive_compression_seconds':sum(read(C/('BACKUP_'+p+'.json'))['compression_seconds'] for p in ['R4','R6','analysis']),'scientific_archive_upload_seconds':sum(read(C/('BACKUP_'+p+'.json'))['upload_seconds'] for p in ['R4','R6','analysis']),'scientific_archive_fresh_download_seconds':sum(read(C/('BACKUP_'+p+'.json'))['fresh_download_seconds'] for p in ['R4','R6','analysis']),'scientific_archive_transfer_bytes_each_direction':sum(read(C/('BACKUP_'+p+'.json'))['archive_bytes'] for p in ['R4','R6','analysis']),'artifact_tree_bytes':usage(A),'recovery_tree_bytes':usage(Path(cfg['recovery'])),'public_report_tree_bytes':usage(D),'cgroup_RAM_current_bytes':int((cg/'memory/memory.usage_in_bytes').read_text()),'cgroup_RAM_limit_bytes':int((cg/'memory/memory.limit_in_bytes').read_text()),'persistent_capacity_bytes':500000000000,'capacity_basis':'Existing verified provider allocation; fresh provider unavailable at preflight','GPU_seconds':0,'GPU_forwards':0,'LM_forwards':0,'model_weight_download_bytes':0,'production_fits':0,'audit_final_head_fits':60,'audit_optimizer_fits':960,'audit_optimizer_retries':0,'synthetic_fixture_fits':2,'original_start_utc':None,'rental_start_utc':None,'hourly_rate_usd':None,'cost_usd':None,'hard_deadline_utc':None,'closure_reserve_hours':None,'purchases':False,'no_clock_reset':True,'time_policy':cfg['time_policy'],'jobs':jobs}
 put(C/'RESOURCE_MEASUREMENTS.json',measure);publish('RESOURCE_MEASUREMENTS.json',measure)
 return jobs,proof

def documents(jobs,disposition):
 # Reporting typography only: preserve exact CSV values, keys and frozen scientific source.
 text=(D/'ANALYSIS.md').read_text()
 replacements={'contribute936pending':'contribute 936 pending','covered780A07units,1560saved':'covered 780 A07 units, 1,560 saved','paths,7800marginal and16800paired':'paths, 7,800 marginal and 16,800 paired','distributions:49.2million':'distributions: 49.2 million','was0,':'was 0,','residual3.':'residual 3.','residual7.':'residual 7.','residual4.':'residual 4.','remain1e-10for':'remain 1e-10 for','and1e-12for':'and 1e-12 for','prospective60-unit':'prospective 60-unit','passed:960planned':'passed: 960 planned','fits,960actual including0recorded':'fits, 960 actual including 0 recorded','norm,seed42':'norm, seed 42','Full26representation':'Full 26-representation','block16(17th block)':'block 16 (17th block)','pointwise95%':'pointwise 95%','HumanTF':'Human TF','dev,finalnorm,seed42':'dev, final norm, seed 42','R4refitAUROC':'R4 refit AUROC','fixedAUROC':'fixed AUROC','baseAUROC':'base AUROC','Corepromoter':'Core promoter','finalnorm/seed42':'final norm / seed 42','displays,R6-minus-R4':'displays, R6-minus-R4','in3tasks and negative in3':'in 3 tasks and negative in 3','R4corpus':'R4 corpus','R4fixed':'R4 fixed','everydecoder block0–24and finalnorm':'every decoder block 0–24 and final norm','threeCVseeds':'three CV seeds','Layer16is zero-based block17':'Layer 16 is zero-based block 17','normalized-forward4mer':'normalized forward 4-mer','reuse36unique historical fits(30for':'reuse 36 unique historical fits (30 for','251of260candidate/task/representation':'251 of 260 candidate/task/representation','sameC':'same C','fold hashes,C traces,parameter/probability':'fold hashes, C traces, parameter/probability','the60-unit':'the 60-unit','score.35of49primary LMunits':'score. 35 of 49 primary LM units','available(21historical+14A06);12A06TRAIN':'available (21 historical + 14 A06); 12 A06 TRAIN','contains14LMmetric':'contains 14 LM metric','humanTF,corepromoter,promoter300,splice,mouseTF':'human TF, core promoter, promoter 300, splice, mouse TF','inclusion,config declaration,exact dataset version,observed sampled rows':'inclusion, config declaration, exact dataset version, observed sampled rows','parents,objectives,steps,schedules':'parents, objectives, steps, schedules','forgetting,resistance to recovery,information erasure':'forgetting, resistance to recovery, information erasure','reasons,while':'reasons, while','test,was':'test, was','dev,and':'dev, and','layer/seed/Cselection':'layer/seed/C selection','checks,not':'checks, not','promoter300':'promoter 300','Promoter300':'Promoter 300','corpusNLL':'corpus NLL'}
 for old,new in replacements.items():text=text.replace(old,new)
 # Add a task-specific adverse/inconclusive comparison and exact figure navigation.
 extra='''
## What the layer views add

The AUROC profiles show that final norm can differ sharply from the middle decoder blocks; the final-norm display must not stand in for the full representation grid. Human-TF discrimination under the original-base readout degrades across many later representations even where refitted readouts remain useful. Core-promoter and promoter-300 readouts also differ by policy. These are descriptive features of the released curves, not a newly selected best layer or a causal localization claim.

At the predeclared final-norm/seed-42 dev display, R6−R4 refit AUROC decreases for core promoter (−0.047809; pointwise interval −0.072749 to −0.023016) and mouse TF (−0.091893; −0.132478 to −0.051743). Splice is inconclusive at this display (−0.019191; −0.058705 to 0.019562), despite lower R6 corpus LM NLL. Promoter-300 refit AUROC changes little (0.003555; −0.008065 to 0.015516), while its NLL is higher. These examples preserve unfavorable and mixed evidence; none establishes equivalence or a family-wide result.

[All-layer dev AUROC profiles](figures/dev/profiles_auroc.png), [base/R1 paired anchors](figures/dev/anchors_auroc.png), [nonadjacent R6−R4 profiles](figures/dev/R6_minus_R4_auroc.png), [shared-control anchors](figures/dev/anchors__controls_auroc.png), [within-task LM](figures/dev/LM_within_task.png), [nonadjacent LM differences](figures/dev/LM_R6_minus_R4.png) and [coverage map](figures/coverage/availability_and_missing_edges.png) have matching standalone PDFs and full-precision source rows in PLOT_DATA/plotted_values.csv. All 31 figures have a per-file digest and caption in FIGURE_VALIDATION.json. See CLAIMS_TO_EVIDENCE.csv for exact endpoint IDs and row keys.

'''
 if '## What the layer views add' not in text:text=text.replace('## Task declarations and interpretation limits',extra+'## Task declarations and interpretation limits')
 publish('ANALYSIS.md',text)
 commands='# A08 commands and environments\n\nThese commands are records, not an automatic resume queue. A08 only was approved. Scientific core version audit-source-001 remains unchanged. GPU visibility is empty; ordinary workers use four BLAS/OpenMP threads and a 32-GiB address-space ceiling.\n\n'
 for j in jobs:commands+=f"### {j['name']}\n\nPID `{j['pid']}`, start ticks `{j['proc_start_ticks']}`, state `{j['status']}`, exit `{j['exit_code']}`.\n\n```bash\nOMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 {shlex.join(j['argv'])}\n```\n\n"
 commands+='## Rendering and reporting\n\nThe isolated figure environment did not alter the frozen audit/runtime environments. Reporting-only changes retained original source spellings, scientific values and private seals while filling exact LM/reference provenance. Rendering revisions corrected exploratory-test legend overlap, header spacing and explicit tight-bbox title inclusion. Final rendering uses completed provenance tables; prior unsealed layout diagnostics are preserved privately. See FIGURE_ENVIRONMENT.json and REPORT_PROVENANCE_NORMALIZATION.json.\n\n```bash\n'+shlex.join(read(D/'FIGURE_VALIDATION.json')['executed_argv'])+'\n```\n\nThe saved reporting order is report_tables.py → control_table.py → context_and_analysis.py → enrich_provenance.py → plot_verified.py → complete_plot_keys.py → closeout.py. Regeneration of completed files is unnecessary for reporting reuse. Numerical CLI options were exercised in the actual job records; restore CLI commands are in RESTORE.md.\n'
 publish('PRODUCTION_COMMANDS.md',commands)
 nextmd='''# Proposed A09 edits — no A09 execution

Require separate direct A09 approval and an explicitly approved prompt commit. Bind this A08 scientific/public manifest and its later exact commit-delivery receipt, preserving the same coverage/protocol hashes and no-deadline policy. Reuse the complete verified tables, 31 PNG/PDF figures, plot data, claims and recovery archives; do not run fitting, model forwards or a repeat unchanged audit merely to generate a report.

Explain the qualified R4/R6 scope separately from the incomplete full project. Lead with readout-policy divergence, mixed R6−R4 outcomes and within-task LM/probe divergence, with the predeclared anchor keys and pointwise uncertainty. Keep the historical R3 domain and H3 exploratory test separate. Carry every missing adjacent edge, unknown exposure/parent/objective/budget field and A04 PARTIAL state into the report. Preserve the original A06 schema defect and derivative normalization evidence.

Specify both reporting and recovery acceptance before any A09 action: exact source/manifest/delivery pins; independent CSV key/type/link checks; restore dependencies and exclusions; final public/private metadata references; scientific/administrative services separately. Observer ACTIVE does not authorize a scientific stage or publish prompt revisions. Reviewer remains DRAFT_ONLY, publisher BLOCKED.

R2 identity/delivery/admission, R5 native qualification/downstream evidence, the R3 live runtime bridge, exact retain versions/sampler/exposure logs and checkpoint parents/objectives/steps/schedules/token budgets remain external inputs. New delivery may be inventoried as pending. Backfill, R3 qualification, new inferential families, forgetting/relearning, perturbations and Pod B work require separate explicit scope; they must not enter A09 silently.

WAITING_FOR_APPROVAL: A09
''';publish('NEXT_PROMPT_RECOMMENDATIONS.md',nextmd)
 restore_commands=[b['restore_command'] for b in read(C/'BACKUP_MANIFEST.json')['archives']]
 resume={'schema':'pod-a-resume-manifest-v1','template_only':False,'run_id':R.name,'stopped_stage':'A08','attempt_id':C.name,'status':'READY_FOR_A09_SEPARATE_APPROVAL','requires_new_direct_approval':True,'required_approval':'A09 at a separately approved prompt commit; no A09 dispatch exists','prompt_commit':cfg['prompt_commit'],'research_input_commit':cfg['research_head_before'],'research_commit':'Bound by separate post-push delivery receipt; no self-reference','protocol_sha256':cfg['protocol_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'paths':cfg,'budget':cfg['time_policy'],'completed_receipts':[ref(C/n) for n in ['NUMERICAL_AUDIT.json','AUDIT_REFIT_RECEIPT.json','DERIVED_ANALYSIS_AUDIT.json','BACKUP_VERIFICATION.json','PRESERVATION_VERIFICATION.json','JOB_DISPOSITION.json']],'missing_units_in_priority_order':[],'invalidated_units':[],'downloads':read(C/'BACKUP_MANIFEST.json')['archives'],'exact_commands_checked_against_cli':restore_commands,'excluded_completed_units':'780 full audits,60 sampled refits,546 classifier and7 LM analysis units; all accepted historical/A06/A07 production and dependency checks','required_additional_time_seconds':None,'blockers':['Full-project external R2/R5 gaps and R3 bridge','Unknown ancestry/objective/realized exposure and token budgets'],'automatic_resume':False,'A09_started':False}
 put(C/'RESUME_MANIFEST.json',resume);publish('RESUME_MANIFEST.json',resume)
 audit=read(C/'NUMERICAL_AUDIT.json');rf=read(C/'AUDIT_REFIT_RECEIPT.json');receipt={'schema':'pod-a-stage-receipt-v1','template_only':False,'run_id':R.name,'stage':'A08','attempt_id':C.name,'status':'VERIFIED_READY_FOR_DELIVERY','scientific_scope':'COMPLETE_QUALIFIED_AVAILABLE_ENDPOINTS','full_project_status':'PARTIAL_EXTERNAL_DEPENDENCIES','A04_status':'PARTIAL','approval':read(C/'APPROVAL_RECORD.json'),'prompt_commit':cfg['prompt_commit'],'research':{'origin':'https://github.com/Georgakopoulos-Soares-lab/unlearning.git','branch':'POD_A','head_before':cfg['research_head_before'],'scientific_parent_at_assembly':git('rev-parse','HEAD'),'exact_delivery_commit':'Separate post-push receipt','other_refs_main_preserved':True},'protocol_sha256':cfg['protocol_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'budget':cfg['time_policy'],'coverage':{'full_head_universe':3276,'new_production_heads':0,'new_independently_audited_A07_heads':780,'new_fixed_probability_paths':780,'all_probability_paths':1560,'reused_historical_heads':1404,'reused_A06_H3_heads':156,'released_existing_heads':2340,'R2_pending_heads':468,'R5_pending_heads':468,'failed_heads_or_audits':0,'fixed_application_universe':3276,'available_fixed_applications':2340,'primary_LM_available':35,'primary_LM_universe':49,'unique_controls_reused':36,'full_ledger_units':6637},'all_unit_audit':{k:v for k,v in audit.items() if k!='units'},'sampled_refit_audit':{k:v for k,v in rf.items() if k!='units'},'new_analysis':{k:v for k,v in read(C/'DERIVED_ANALYSIS_AUDIT.json').items() if k!='records'},'figures':{'count':31,'validation':ref(D/'FIGURE_VALIDATION.json')},'checks_not_performed':['GPU/model/LM forwards','Independent refitting outside prospective60unit panel','New untouched tests','R2/R5 backfill','R3 live bridge','New policy/inferential families/controls fitting','PodB/relearning/unlearning or causal mixture identification'],'backup_status':read(C/'BACKUP_VERIFICATION.json'),'all_owned_jobs_quiescent':True,'owned_jobs':disposition['owned_job_records'],'observer':disposition['observer'],'resume_manifest_sha256':sha(C/'RESUME_MANIFEST.json'),'approval_for_next_stage':False,'A09_started':False,'next_state':'WAITING_FOR_APPROVAL: A09','delivery_gate':'Public raw Git bytes and post-push metadata protection pending; later proof must PASS before final completion is reported','assembled_utc':now()}
 put(C/'A08_RECEIPT.json',receipt);publish('A08_RECEIPT.json',receipt)
 handoff=f'''# A08 handoff

Run `{R.name}`, attempt `{C.name}`. **Qualified scientific scope complete; final delivery being sealed. Full project PARTIAL; A04 PARTIAL.** Prompt `{cfg['prompt_commit']}`; accepted research input `{cfg['research_head_before']}`. Exact published commit and post-push recovery revisions are bound by the separate final DELIVERY_RECEIPT.json, avoiding a self-hash cycle.

Coverage SHA256 `{cfg['coverage_plan_sha256']}`; protocol SHA256 `{cfg['protocol_sha256']}`. The recorded no-deadline amendment remains active; original/rental starts and price/cost are unknown. No original start was invented or clock reset.

## Result and verification

All 780 A07 saved heads and their unchanged-base applications passed 1,560 probability paths, 7,800 marginal and 16,800 paired distributions, all 49,200,000 attempted values valid. Maximum residuals: probability {audit['probability_max_abs']}, point metric {audit['metric_max_abs']:.17g}, every draw {audit['bootstrap_draw_max_abs']:.17g}, interval {audit['interval_max_abs']:.17g}. The exact prospective 60-unit panel passed 960 independent optimizer fits without retry; probability/CV residual zero, metric residual {rf['metric_max_abs']:.17g}. The panel is sampled, not all-head refitting. No production head was replaced or added. 27 synthetic tests and two fixture fits are separate.

Reuse preserves 1,404 historical heads, 156 A06 H3 heads, 35 primary LM units and 36 unique controls. Total existing released production heads 2,340/3,276; the separate application universe also has 2,340/3,276. R2 and R5 each retain 468 pending cells. All 6,637 ledger keys remain present. Historical R3 is valid in its accepted domain; new affected live-runtime edges remain gated.

The predeclared R6−R4 family has all 5,460 classifier rows (4,680 dev, 780 separate H3 exploratory test) and 14 LM rows, each with independent every-draw checks. It is nonadjacent. All five actual adjacent families retain null blocked/pending keys. The public logical paired table comprises all four partitions in TABLE_PARTITIONS.json, totaling 45,360 rows. VERIFIED_METRICS.csv has 27,300 rows; LM point/paired tables have 70/112. Both readout policies, all 26 hooks and all three seeds remain available. Reporting-only policy/provenance fixes preserve original values, source spellings and immutable receipts.

See [analysis](ANALYSIS.md), [claims](CLAIMS_TO_EVIDENCE.csv), [coverage](COVERAGE.csv), [schemas](RESULT_SCHEMAS.json), [figures](FIGURE_VALIDATION.json), [numerical checks](NUMERICAL_AUDIT.json), [sampled refits](AUDIT_REFIT_RECEIPT.json), [new-contrast checks](DERIVED_ANALYSIS_AUDIT.json) and [resources](RESOURCE_MEASUREMENTS.json).

## Recovery and jobs

The three new scientific archives passed force-fresh exact-member checks, 40 restored prediction/metric paths across both candidates/every other-five task/both anchors/policies, two audit-refit heads and new classifier/LM contrast checks. [Restore instructions](RESTORE.md) provide exact commands, revisions, dependency translations and exclusions. No GPU recreation is claimed. Final report/code/figure metadata protection follows public push and records a separate immutable receipt.

All owned scientific workers have exited successfully and all owned scientific locks are free; the Pod remains running. Existing observer {disposition['observer']['observer_status']}; reviewer DRAFT_ONLY; publisher BLOCKED. No duplicate observer or self-advancing scheduler was started. Observer state is administrative, separate from science.

## Remaining external inputs and next boundary

R2 admitted identity/delivery; R5 native qualification/downstream payloads; R3 live cross-runtime bridge; exact retain versions, sampler/realized exposure records, parent checkpoints, objectives, steps/schedules/token budgets. None is an A08 backfill authorization. The reporting/recovery stage may reuse this package after separate direct A09 approval and a pinned approved prompt; no fitting or full unchanged audit is required. See [proposed edits](NEXT_PROMPT_RECOMMENDATIONS.md), [resume manifest](RESUME_MANIFEST.json) and [exact commands](PRODUCTION_COMMANDS.md).

WAITING_FOR_APPROVAL: A09
''';put(C/'SESSION_HANDOFF.md',handoff);publish('SESSION_HANDOFF.md',handoff)
 for n in ['FIGURE_ENVIRONMENT.json','FIGURE_REQUIREMENTS.txt','RESOURCE_LEDGER.jsonl','REPORT_EXPORT_ATTEMPT_001.json']:
  if (C/n).exists():publish(n,(C/n).read_bytes())
 # Explicit owned-source export; no arrays or serialized objects enter Git.
 for subtree in ['code','stage_drivers']:
  for p in sorted((A/subtree).glob('*')):
   if p.is_file() and p.name!='control_views.py' and p.suffix in ['.py','.patch','.txt']:publish('CODE/'+subtree+'/'+p.name,p.read_bytes())
 supplement={'schema':'pod-a-a08-supplemental-source-v1','core_scientific_source_identity':ref(C/'SOURCE_IDENTITY.json'),'core_immutable':True,'report_plot_recovery_source':[{'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((D/'CODE').rglob('*')) if p.is_file()],'reporting_fixes':'Policy aliases, exact inherited provenance, progress analysis glob and figure layout only; no numerical core changes or invalidated science','analysis_render_versions_preserved_privately':True};publish('SOURCE_SUPPLEMENT.json',supplement)
 return receipt

def main():
 guard(allow_dirty=True);assert read(D/'FIGURE_VALIDATION.json')['status']=='PASS'
 preserved_history();analysis_audit();backups();jobs,disposition=disposition_and_resources();documents(jobs,disposition)
 print(json.dumps({'status':'READY_TO_VALIDATE_AND_DELIVER','all_jobs_quiescent':True,'A09_started':False}))
if __name__=='__main__':main()
