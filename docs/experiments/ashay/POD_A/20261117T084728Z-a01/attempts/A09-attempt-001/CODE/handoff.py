"""Practical A09 recovery, missing-input and provenance documents; no science dispatch."""
from common import *
import importlib.metadata,platform,shlex
def main():
 graph=read(C/'RECOVERY_DEPENDENCY_GRAPH.json');assert graph['status']=='PASS';products=[]
 for p in sorted(D.glob('*')):
  if p.is_file() and p.suffix in ['.md','.csv','.json']:products.append({'product':p.name,'sha256_at_report_assembly':sha(p),'source_research_commit':cfg['research_head_before'],'scientific_source_graph_roots':['A08/final_delivery_receipt'],'source_nodes':[n['id'] for n in graph['nodes']],'row_level_provenance':'CLAIMS_TO_EVIDENCE.csv;TABLE_INDEX.json;ENDPOINT_ALIAS_MAP.csv','code_and_approval':'SOURCE_IDENTITY.json;APPROVAL_RECORD.json;A09_EXECUTION_MANIFEST.json'})
 figures=read(D8/'FIGURE_VALIDATION.json')
 for f in figures['figures']:products.append({'product':'figure:'+f['name'],'files':f['files'],'source_graph_roots':['A08/final_metadata'],'scientific_sources':f['source_tables'],'plot_source':figures['source_code_sha256'],'plot_data':figures['plotted_values_csv_sha256']})
 graph['products']=products;graph['original_measurement_ancestors']={'HISTORICAL_NOVEMBER10':['historical/base_R1','historical/R3','historical/controls'],'A06_H3_LM':['A06/R4_H3','A06/R6_H3','A06/R4_other_five','A06/R6_other_five'],'A07_other_five':[n['id'] for n in graph['nodes'] if n['id'].startswith('A07/')],'A08_new_verification_and_contrasts':['A08/R4','A08/R6','A08/analysis']};publish('RECOVERY_DEPENDENCY_GRAPH.json',graph)
 coverage=[]
 for n in graph['nodes']:
  coverage.append({'dependency_id':n['id'],'kind':n['kind'],'revision':n['revision'],'remote_path':n['remote_path'],'bytes':n['bytes'],'sha256':n['sha256'],'current_remote_identity':n['current_remote']['status'],'remote_check_utc':n['current_remote']['checked_utc'],'current_local_hash_check':n['current_local']['status'],'files_hashed':n['current_local']['files_checked'],'bytes_hashed':n['current_local']['bytes_hashed'],'prior_fresh_restore_proof':n['prior_fresh_restore_proof']['path'],'prior_proof_sha256':n['prior_fresh_restore_proof']['sha256'],'new_A09_transfer':n['current_local']['new_transfer'],'new_A09_computation':'Only prescribed panel, recorded separately in FRESH_RESTORE_CHECK.json','scope':n['required_for'],'dependencies':json.dumps(n['dependencies'])})
 table('RECOVERY_COVERAGE.csv',coverage)
 env={'schema':'pod-a-a09-environment-v1','status':'PASS','python':platform.python_version(),'packages':{k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-learn','joblib','threadpoolctl']},'cpu_executable':sys.executable,'GPU_visibility':'Disabled for workers','ordinary_workers_max':2,'BLAS_threads_per_worker':4,'RLIMIT_AS_bytes':32*1024**3,'no_installs_or_upgrades':True,'inherited_A08_environment':ref(D8/'ENVIRONMENT_CHECK.json'),'plot_environment_reused':ref(D8/'FIGURE_ENVIRONMENT.json')};assert env['python']=='3.12.3' and env['packages']=={'numpy':'2.5.4','scipy':'1.18.1','scikit-learn':'1.7.2','joblib':'1.5.2','threadpoolctl':'3.8.0'};put(C/'ENVIRONMENT_CHECK.json',env);publish('ENVIRONMENT_CHECK.json',env)
 ids=read(D.parent/'A05-attempt-001/CHECKPOINT_READINESS.json');a4=C.parent/'A04-attempt-002';reacquire={'schema':'pod-a-a09-reacquisition-v1','saved_analysis_recovery_requires_weights':False,'FULL_GPU_RECREATION_VERIFIED':False,'model_weights_and_runtime_binaries_included':False,'checkpoint_original_and_content_identities':ids,'native_manifest_archive_node':'A04-attempt-002','native_manifest_revision':next(n['revision'] for n in graph['nodes'] if n['id']=='A04-attempt-002'),'native_manifest_members':[],'recipe':'Recover exact manifest/sidecar source IDs and bytes through the pinned A04 metadata archive. Reacquire each authorized original native shard/config/tokenizer by recorded provider file ID, expected byte size and SHA256; reject mismatches; rebuild the exact source/environment recipe. Any live qualification/bridge or model acquisition requires fresh scoped approval. Saved analysis uses existing qualified features/heads and does not need these downloads.','access_status':'A09 verified the immutable private metadata archives/sidecars; original native model-provider transport was NOT freshly tested, and no missing-model download occurred','R2':'Delivery/unique admitted identity unresolved; no filename or log substitutes for payload','R3_R5':'Historical qualification/transport gaps persist; sidecars alone are not complete native payloads','runtime_binary_equivalence':'A rebuilt binary is not automatically a qualified live-model bridge'}
 for name in ['CHECKPOINT_HASHES.final.json','ASSET_TRANSFER_MANIFEST.json','ENVIRONMENT_LOCK.json','SOURCE_IDENTITY.json','RUNTIME_REBUILD.md','runtime-freeze.txt']:
  p=a4/name
  if p.exists():reacquire['native_manifest_members'].append({'member':'control/'+name,**ref(p),'included_via':'A04-attempt-002 immutable metadata archive','native_access_tested_in_A09':False})
 publish('REACQUISITION_MAP.json',reacquire);publish('CHECKPOINT_READINESS.reused.json',ids)
 refs=[]
 for st,names in [('A02-attempt-001',['CHECKPOINT_REGISTRY.json','LINEAGE_EXPOSURE.csv','PROVENANCE_EVIDENCE.jsonl']),('A04-attempt-003',['A04_RECEIPT.json','PAYLOAD_RECOVERY_INDEX.json','R2_DISCOVERY.json','BLOCKERS.json'])]:
  for n in names:
   p=C.parent/st/n
   if p.exists():refs.append({'stage':st,'source':ref(p),'provider_access_retested_in_A09':False})
 publish('AUTHORITATIVE_INPUT_REFERENCES.json',{'checkpoint_readiness':ref(D.parent/'A05-attempt-001/CHECKPOINT_READINESS.json'),'configuration_and_exposure_plan':ref(D8/'INCLUSION_EXPOSURE_PLAN.csv'),'observed_current_remote_metadata':ref(C/'RECOVERY_DEPENDENCY_GRAPH.json'),'original_registry_and_access_refs':refs,'unknowns_remain_unknown':True})
 missing=rows(D/'COVERAGE.csv');missing=[r for r in missing if r['status'] not in ['VERIFIED','REUSED_VALIDATED']];assert len(missing)==1886;table('MISSING_UNIT_KEYS.csv',missing)
 draft='''# Missing inputs — unsent request draft

This is a draft only; no collaborator message has been sent. These are outstanding full-project dependencies, not failures of the qualified A09 reporting scope. Original provider access was not freshly retested in A09. Current immutable private metadata/sidecar availability was checked at the timestamps in RECOVERY_COVERAGE.csv. Historical access/qualification observations retain the dates and exact hashes in AUTHORITATIVE_INPUT_REFERENCES.json and the A04 receipts.

## R2: transport plus identity/admission

Please supply the intended two-source H3/human-TF checkpoint through an accessible original provider location or explicitly authorized immutable private mirror, with original file/folder IDs, all native model shards and SHA256/size manifest, configuration/tokenizer identity, intended iteration and mapping evidence. Resolve the unique identity rather than relying on newest timestamps, folder names, config names, tensor similarity or a training log. Parent identity is required if the payload is an adapter. Existing R2 discovery/access notes are historical evidence; no new identity has been admitted here. The exact blocked unit IDs are in MISSING_UNIT_KEYS.csv, including 468 head cells and their separate applications.

## R5: admitted complete payload and qualification dependencies

Please provide the intended splice-addition checkpoint or a separately authorized immutable private mirror, exact original/native shard/config/tokenizer IDs, sizes and content hashes, model format/parent if required, and source config/version evidence. A folder, log or sidecar cannot substitute for complete weights. The frozen registry retains the intended original endpoint. Native qualification and downstream extraction/probes remain incomplete; 468 head cells and separate applications remain pending. This request does not authorize their download or qualification now.

## R3: live cross-runtime bridge

Historical R3 outputs and comparisons remain valid in the accepted historical domain. New affected R4−R3 edges require the actual admitted R3 native payload, exact config/tokenizer/format/parent dependencies and a qualified unchanged runtime/anchor bridge. A04's recovered sidecars are metadata, not complete model recovery. Do not derive the missing effect by subtracting incompatible baseline-relative differences. See REACQUISITION_MAP.json for exact historical IDs/manifests and excluded runtime dependencies.

## Scientific-identifiability and biological metadata

Please provide exact training parents/checkpoint chain, objective, actual steps, learning-rate schedule and matched-budget basis; retain dataset versions/source IDs; sampled training manifests and realized source/token exposure; overlap evidence relevant to before-declaration interpretation; numerical label definitions and human/mouse TF source/identity metadata. Unknowns remain unknown. These records may improve interpretation but cannot replace missing checkpoint payloads or create a controlled intervention retrospectively.

## Approval and ownership

After actual delivery, request a newly scoped A02 identity/inventory review and affected A04 qualification, then an explicitly approved A05 coverage amendment and bounded A06/A07/A08 backfill as needed. Every necessary stage needs fresh direct approval under the controller or an explicitly revised scoped controller; no full restart or automatic queue is proposed. Existing completed cells are excluded. Pod B owns relearning on a separate server. Saliency/perturbation requires its own published scope and approval.
''';publish('MISSING_INPUTS_DRAFT.md',draft)
 resume={'schema':'pod-a-resume-manifest-v1','template_only':False,'run_id':R.name,'stopped_stage':'A09','attempt_id':C.name,'status':'TERMINAL_REPORT_RECOVERY_IN_PROGRESS','requires_new_direct_approval':True,'required_approval':'Only if further work is requested: new explicitly scoped identity/qualification/backfill or perturbation approval; no A10 exists','prompt_commit':cfg['prompt_commit'],'scientific_commit':cfg['scientific_commit'],'A08_metadata_commit':cfg['research_head_before'],'report_delivery_commit':None,'metadata_commit':None,'commit_null_reason':'Future delivery hashes are bound in post-push/private receipts rather than self-referenced','protocol_sha256':cfg['protocol_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'paths':cfg,'budget':cfg['time_policy'],'completed_receipts':[ref(D8/n) for n in ['A08_RECEIPT.json','NUMERICAL_AUDIT.json','AUDIT_REFIT_RECEIPT.json','DERIVED_ANALYSIS_AUDIT.json']],'missing_unit_ids_in_priority_order':[r['unit_id'] for r in missing],'missing_unit_index':ref(D/'MISSING_UNIT_KEYS.csv'),'invalidated_units':[],'downloads':graph['nodes'],'exact_commands_checked_against_CLI':[[cfg['cpu_venv']+'/bin/python',str(A/'code/consumer.py'),'--help'],[cfg['tools_venv']+'/bin/python',str(A/'code/restore.py'),'--help']],'recovery_command_after_archive_is_available':[cfg['tools_venv']+'/bin/python',str(A/'code/restore.py'),'--backup',str(D/'BACKUP_MANIFEST.json'),'--destination',str(REC/'manual-consumer-001'),'--use-recorded-dependencies'],'fresh_server_command_same_tool_adds':['--restore-dependencies'],'excluded_completed_units':'All existing2340heads and2340applications,35LMunits,36controls; A08all780audits/60refits/derived families; all reports/figures after terminal completion','required_additional_time_seconds':None,'blockers':['R2delivery/unique admission','R5native qualification/downstream evidence','R3live bridge for affected new contrasts','Unknown training ancestry/objective/exposure/source-label metadata'],'automatic_resume':False,'new_fits_or_forwards_authorized':False};put(C/'RESUME_MANIFEST.json',resume);publish('RESUME_MANIFEST.json',resume)
 restore=f'''# A09 saved-analysis restore

This tool restores the declared report/consumer payload and verifies its archive and every member before loading trusted serialized heads. It does not run a scientific production CLI, fit, model forward, new draw or checkpoint qualification. Model weights and installed GPU/runtime binaries are excluded; see [reacquisition map](REACQUISITION_MAP.json). Full GPU recreation remains unverified.

## Current-Pod recovery with existing verified restored dependencies

The concrete owned command, after BACKUP_MANIFEST.json is sealed, is:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' {cfg['tools_venv']}/bin/python {A}/code/restore.py --backup {D}/BACKUP_MANIFEST.json --destination {REC}/manual-consumer-001 --use-recorded-dependencies
```

The destination must not exist. The tool forces a fresh download into its new cache, rejects unsafe/duplicate/extra members and checks each declared SHA256/size. It uses the pinned dataset revision in BACKUP_MANIFEST.json, not a moving branch. Every dependency is pinned in [the graph](RECOVERY_DEPENDENCY_GRAPH.json) and reverified before the frozen CPU consumer panel. The currently restored roots are prior fresh consumers, not original producer paths.

## Fresh-server sequence

Clone research POD_A at the exact report-delivery/metadata commit identified by the final delivery receipt. Recover this A09 prompt/approval/source snapshot. Create Python 3.12.3 with NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.7.2, joblib 1.5.2 and threadpoolctl 3.8.0; use the exact inherited environment recipe and wheel/source identities referenced by ENVIRONMENT_CHECK.json and the A04 metadata archive. Use existing authorized private-dataset authentication without copying account files into payloads. Install the recorded transfer-tool environment separately; do not upgrade the numerical environment opportunistically.

Run the same owned restore CLI with `--restore-dependencies` in place of `--use-recorded-dependencies`. Use a new absolute destination appropriate to that server. The tool downloads only the exact declared archives/objects, verifies their immutable sizes/hashes, restores all members safely and creates a copied dependency-root translation context. It never edits historical producer receipts. No shared /workspace with Pod B is assumed. This can require the complete declared historical saved-analysis dependency graph; do not download model weights. If valid local restored dependencies already exist, use `--context` with the copied root translation and preserve original receipts.

After a restore, the exact CPU consumer invocation has this form; the restore tool prints the concrete command with real new paths:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 {cfg['cpu_venv']}/bin/python <restored-payload>/code/consumer.py --root <restored-payload> --context <translated-context.json>
```

The angle-bracket notation is documentation of translated paths, not a runnable production command. The restore CLI above constructs those actual arguments and accepts `--cpu-python` for the exact rebuilt numerical interpreter. Its help/syntax is checked without launching science.

## Finite computational scope

Before outcomes, A09 froze R4/R6 × human TF/three-class splice × both policies at final norm/seed42/dev: eight saved prediction/metric paths. It additionally checks one saved A08 audit-refit head per candidate; human-TF/layer16/seed42 R6−R4 for both policies/five metrics/all 2,000 original draws; and the human-TF dev LM NLL/PPL contrast. The consumer checks every report-table/figure source hash and row identity needed for those claims. Probability tolerance is 1e−10; metrics, draws and intervals 1e−12. A08's prior 40-path proof is reused and attributed separately. Saved-feature analysis recovery does not establish full model/GPU recreation or complete missing science.

There is no automatic restart. After verified terminal A09 delivery, the owned administrative loop stops while the Pod remains running. Any further identity/qualification/backfill or perturbation work requires a new explicit scope and direct approval.
''';publish('RESTORE.md',restore)
 handoff=f'''# Pod A A09 handoff

**Qualified available-checkpoint analysis is complete; full R1–R6 science and A04 remain PARTIAL.** A09 is finishing its finite report/recovery delivery. This is plain UTF-8 Markdown with real newlines, validated by typed writer regression tests.

Run `{R.name}`, attempt `{C.name}`. Approved prompt `{cfg['prompt_commit']}`. Scientific input `{cfg['scientific_commit']}`; A08 final metadata `{cfg['research_head_before']}`. Coverage `{cfg['coverage_plan_sha256']}` and protocol `{cfg['protocol_sha256']}` remain frozen. Actual final report/metadata commits and private revisions are named in separate post-push/final receipts to avoid self-hash cycles.

## Read first

[One-page summary](ONE_PAGE_SUMMARY.md), [full results](RESULTS.md), [methods/limits](METHODS_AND_LIMITS.md), [figure gallery](FIGURE_GALLERY.md), [exact claim keys](CLAIMS_TO_EVIDENCE.csv), [table index](TABLE_INDEX.json) and [data dictionary](DATA_DICTIONARY.md).

The full logical paired table has 45,360 rows across all four partitions; 27,300 marginal classifier rows and 70/112 LM point/paired rows remain available. The 31 figure pairs and 30,886 plot uses are unchanged A08 evidence. All six tasks, 26 representations, three CV seeds and both frozen readouts remain visible. H3 exploratory test and the historical R3 domain remain separate. R6−R4 is nonadjacent and no causal/forgetting/optimal-mixture claim is established.

## Verification and repair

Reused 2,340 of 3,276 heads and a separate 2,340 of 3,276 unchanged-base applications, 35/49 primary LM units and 36 unique controls. A09 creates zero scientific measurements, fits, forwards or new bootstrap draws. A08's all-780-unit audit and prescribed 60-unit fresh-refit panel remain authoritative and are not rerun. [Audit releases](AUDIT_RELEASE_STATUS.csv) label the old status matrix as a plan. [Repair log](REPORT_REPAIR_LOG.json) binds the decoded historical handoff and 480 typed H3 control endpoint joins, preserving original IDs, every numeric/origin string and producer seals.

## Recovery and exact commands

[Dependency graph](RECOVERY_DEPENDENCY_GRAPH.json), [recovery coverage](RECOVERY_COVERAGE.csv), [private backup](BACKUP_MANIFEST.json), [fresh check](FRESH_RESTORE_CHECK.json) and [restore instructions](RESTORE.md) distinguish prior fresh proof/current remote availability/local all-byte verification from the new A09 selected CPU panel. Model weights and installed runtime binaries are excluded by [exact reacquisition references](REACQUISITION_MAP.json). No full GPU recreation is claimed. Dataset visibility remains private.

## Remaining science and future approval

R2 and R5 each lack 468 head cells and their corresponding applications. All 1,886 pending ledger units, five blocked/pending adjacent contrast families and 14 missing primary LM units remain explicit. R3's historical results are valid; affected new live-runtime comparisons require the bridge. Training parent/objective/dataset-version/sampler/exposure/token-budget and biological label gaps constrain interpretation. [Unsent missing-input draft](MISSING_INPUTS_DRAFT.md), [exact missing keys](MISSING_UNIT_KEYS.csv), [authoritative refs](AUTHORITATIVE_INPUT_REFERENCES.json) and [resume manifest](RESUME_MANIFEST.json) state what is needed.

No A10 exists. Further identity/qualification/backfill requires fresh scoped approval for each needed stage or a revised scoped controller. Completed work is excluded. Saliency/perturbation is DEFERRED_SEPARATE_APPROVAL; Pod B relearning is EXTERNAL_OWNER_POD_B on a separate server. Neither starts now.

## Resource and process policy

The no-deadline amendment remains active. Original/rental starts, rate and cost are unknown, never zero or a reset clock. At most two CPU workers × four threads, 32-GiB per-worker address-space ceiling; no GPU work or purchases. [Resource closeout](RESOURCE_CLOSEOUT.json) and the final private delivery receipt record actual job/transfer/lock disposition. After verified terminal delivery the owned observer stops; unrelated infrastructure and the Pod remain running.

Terminal status is certified only by A09_RECEIPT.json and separate remote/private proofs, not by this prose alone.
''';write_md(C/'SESSION_HANDOFF.md',handoff);publish('SESSION_HANDOFF.md',handoff)
 print(json.dumps({'status':'LOCAL_REPORT_HANDOFF_READY','dependencies':len(graph['nodes']),'explicit_missing_unit_ids':len(missing),'new_science':0}))
if __name__=='__main__':main()
