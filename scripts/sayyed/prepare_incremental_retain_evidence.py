from pathlib import Path
import json,hashlib,csv,collections,datetime,subprocess,shutil,time
from scripts.sayyed.incremental_retain_plan import TASKS,STAGES,meeting_role,declared_membership,adjacent_status
r=Path('/workspace/meeting-artifacts/incremental-retain-eval-v1');w=Path('/workspace/wt-incremental-retain-eval');d=w/'docs/experiments/ashay/incremental-retain-eval-v1';n=Path('/workspace/meeting-artifacts/multiretain-comparison-v1');o=Path('/workspace/meeting-artifacts/multiretain-layers-v1');c=Path('/workspace/meeting-artifacts/benign-followup-v1');start=time.monotonic();cpu=time.process_time()
def load(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,indent=2)+'\n')
def rows(p):return list(csv.DictReader(p.open()))
def writecsv(name,data):
 p=r/'tables'/name;p.parent.mkdir(exist_ok=True)
 with p.open('w',newline='') as f:writer=csv.DictWriter(f,fieldnames=list(data[0]),lineterminator='\n');writer.writeheader();writer.writerows(data)
 return p
assert load(r/'REUSE_VERIFICATION.json')['status']=='PASS'
now=datetime.datetime.now(datetime.timezone.utc).isoformat();available={'base','R1','R3'};declared={'R1':STAGES['R1'],'R3':STAGES['R3']}
source_commit='c79ab07e763a9754c68fdaf7d0730d8458f508dc';oldregistry=load(w/'docs/experiments/ashay/multiretain-layers-v1/CHECKPOINT_REGISTRY_QUALIFIED.json');newregistry=load(n/'CHECKPOINT_REGISTRY.json');priorprotocol=load(n/'COMPARISON_PROTOCOL.json')
# Record live metadata boundaries. Supersede the capped initial base listing.
listings={}
for p in sorted((r/'drive').glob('*.json')):
 j=load(p)
 if 'folder_id' in j and not p.name.endswith('-full.json'):listings[j['folder_id']]=j
for p in (r/'drive').glob('*-full.json'):
 j=load(p);listings[j['folder_id']]=j
inventory=dict(status='LIVE_METADATA_REFRESH_COMPLETE_WITH_EXPLICIT_BOUNDARIES',retrieved_utc=now,folder_count=len(listings),entry_count=sum(len(x['listing']['files']) for x in listings.values()),listings=listings,excluded_descents=['Historical official benchmark/classifier output folders: no unrelated evaluation contents read','LoRA checkpoint iterations: outside scope; metadata names only, no training/execution','Historical GradDiff candidates: prior qualification retained; not identified as requested perturbations'],global_perturbation_name_search=load(r/'drive/perturbation-folder-search.json'),limitations='Only visible supplied locations and scoped accessible-folder name search. Absence here does not establish global absence. Original base listing capped at100 was replaced by full134-entry listing;128shards. Provider checksums unavailable. Remote weights not redownloaded or freshly hashed.')
save(r/'LIVE_INVENTORY.json',inventory)
armids={'base':'base','R1':'h3_only_maxent','R3':'supplied_three_source_config_iter2151'};registry=[]
for stage in ['base',*STAGES]:
 delivered=stage in available
 entry=dict(stage_alias=stage,original_identifier=armids.get(stage),status='complete' if delivered else 'awaiting-delivery',result_origin='REUSED_COMPLETED' if delivered else 'NO_MEASUREMENTS',expected_retain_sources=list(STAGES.get(stage,())),declared_retain_sources=list(declared[stage]) if stage in declared else ([] if stage=='base' else None),realized_sampling_exposure='unknown',stage_alias_qualification='separate reference' if stage=='base' else 'provisional config-based alias; no exposure or sequential-finetuning proof',new_units=0,reused_units=468 if delivered else 0,pending_units=0 if delivered else 468,descriptive_eligibility='previously qualified complete' if delivered else 'blocked: no candidate identity/shards',causal_eligibility='not established',missing_input=None if delivered else 'Deliver exact stage checkpoint folder/shards, intended iteration and architecture/tokenizer/config; clarify parent/objective/data/exposure metadata')
 if stage in ['base','R1']:
  old=oldregistry['arms']['base' if stage=='base' else 'h3_only_maxent'];entry['artifact_identity']=old
  if stage=='R1':entry['iteration']=2000
  else:entry['iteration']=1
 elif stage=='R3':entry['artifact_identity']=newregistry;entry['iteration']=2151
 if delivered:
  arm='new' if stage=='R3' else 'base' if stage=='base' else 'maxent';root=n if stage=='R3' else o
  entry['feature_identities']={g:load(root/'features'/g/arm/'identity.json') for g in ['H3','other_five']};entry['remote_weight_rehash_performed']=False
 registry.append(entry)
for k in [1,2]:registry.append(dict(stage_alias=f'offered_perturbation_{k}',original_identifier=None,status='awaiting-delivery',result_origin='NO_MEASUREMENTS',intervention_type=None,immediate_parent=None,retain_stage=None,selected_fraction=None,intervention_seed=None,pre_post_training=None,checkpoint_ids=None,new_units=0,descriptive_eligibility='blocked: no supplied identifiable candidate',causal_eligibility='not established',missing_input='Supply checkpoint link/iteration/shards and actual intervention type, parent hash/stage, selected fraction, seed/settings and any pre/post training. Meeting Gaussian/reinitialization/5percent discussion is context only.'))
save(r/'CHECKPOINT_REGISTRY.json',dict(updated_utc=now,statuses=['evaluated','available-unqualified','eligible','running','complete','failed','awaiting-delivery'],entries=registry,declared_membership_scope='Normalized provisional task-family aliases; exact retain dataset identity/source versions and exposure unverified',unrequested_candidates=load(Path('/workspace/wt-benign-followup/docs/experiments/ashay/graddiff-qualification-v1/CHECKPOINT_REGISTRY_V9.json'))['candidates'],unrequested_candidate_note='Historical H3-only GradDiff original/v2 are outside this incremental/perturbation extension and are not substitutes. No candidate selected by performance.',discovered_perturbation_candidates=[]))
# Validate immutable per-arm compatibility without equating distinct tokenizer artifacts.
keys=['runtime','hooks','schema','feature_dtype','feature_width','physical_batch_size','filler_policy','pool','padding','dtype','attention_backend','source_sha256','support_sha256','fixed_batch_source_sha256']
for g in ['H3','other_five']:
 ids=[next(x for x in registry if x['stage_alias']==stage)['feature_identities'][g] for stage in ['base','R1','R3']]
 for key in keys:assert all(x[key]==ids[0][key] for x in ids)
 for stage,identity in zip(['base','R1','R3'],ids):
  assert sha(w/'scripts/sayyed/extract_multiretain_fixed.py')==identity['source_sha256']
  assert identity['manifest_sha256']==sha(n/'manifests'/(g+'.jsonl'))
protocol=dict(schema='incremental-retain-extension-v1',frozen_utc=now,status='FROZEN_BEFORE_ANY_NEW_MODEL_SCORING',study='Exploratory reuse of previously examined cohorts; not untouched confirmatory evaluation',implementation_source=source_commit,later_fixes='No later relevant production changes found after fetching research refs; computational source unchanged',authoritative_sequence={k:list(v) for k,v in STAGES.items()},aliases={'R1':'provisional h3_only_maxent','R3':'provisional supplied_three_source_config_iter2151'},parent_design='Unknown common-base versus preceding-stage fine-tuning; incremental means agreed retain-set ordering only',tasks=list(TASKS),cohorts={g:dict(path=str(n/'manifests'/(g+'.jsonl')),sha256=sha(n/'manifests'/(g+'.jsonl')),counts={'train':11971,'dev':1497,'test':1497} if g=='H3' else {'per_task_train':1024,'per_task_dev':512}) for g in ['H3','other_five']},representations=priorprotocol['hooks'],anchors=['decoder.layers.16','decoder.final_norm'],physical_batch_size=8,precision='Existing native BF16/FP32 preserved; TEunfused; physical8/fillers excluded; original numerical tolerances and strict loader exceptions',compatibility_fields=keys,per_arm_tokenizers='Preserve exact identity; base256 and intervention512 differ but prior ordinal-DNA behavior was qualified. Never require equal tokenizer-file hashes across legitimate models.',probe=priorprotocol['probe'],exact_optimizer='balanced L2 logistic LBFGS, tol1e-4,2000 then10000 convergence retry, optimizer42; unchanged fitter computational source943b04f5413d99142f9fb22d176c1b8f9a054bb8',metrics=priorprotocol['bootstrap_metrics'],metric_definitions=priorprotocol['metric_definitions'],bootstrap=priorprotocol['bootstrap'],bootstrap_invalid=priorprotocol['bootstrap_invalid'],lm='Actual LM output head, next-token mask, float32 per-sequence sums/counts and float64 target-weighted aggregate; PPL exp(corpus NLL), no per-layer PPL',contrasts=['stage minus base','stage minus R1','stage minus immediate preceding stage if available','perturbation minus actual identified parent if available'],nonadjacent='R3 minus R1 is observational nonadjacent: planned additions include both humanTF and core-promoter, not a single-task adjacent effect',execution_order='R2,R4,R5,R6 if available, skipping missing stages without imputing contrasts; each candidate strict load plus bounded training-only smoke, then complete H3 extraction/fits/audit before other5; then qualified perturbations against actual parent',controls='Reuse verified36 composition/normalized-forward4mer controls at block16/finalnorm; do not refit',allowed='Frozen benign inference and small CPU classifiers only',forbidden=load(r/'inputs/prompt_receipt.json')['path']+' ownership exclusions: no backbone/intervention/noise/LoRA/relearning training, hazardous benchmark contents/evaluation, distillation, test opening, collaborator messages, force push, main merge, shutdown',gpu_accounting='Uncapped within supplied-checkpoint benign scope; shared GPU_EXECUTION.lock plus historical ledger locks; separate new session identities, preserve historical ledger',selection='Metadata-grounded intended candidate only, not heldout score/timestamp/largest iteration alone',preservation_margins={},prior_protocol_sha256=sha(n/'COMPARISON_PROTOCOL.json'),registry_sha256=sha(r/'CHECKPOINT_REGISTRY.json'),live_inventory_sha256=sha(r/'LIVE_INVENTORY.json'),new_measurements=0)
save(r/'COMPARISON_PROTOCOL.json',protocol)
save(r/'PROTOCOL_FROZEN.json',dict(status='FROZEN',utc=now,protocol_sha256=sha(r/'COMPARISON_PROTOCOL.json'),no_new_heldout_scoring=True))
# Exact records are copied and annotated; metrics/intervals are never recomputed here.
m=rows(n/'reports/native_metrics.csv');contrasts=rows(n/'reports/native_contrasts.csv');oldcontrasts=rows(n/'reports/h3_only_minus_base_reference.csv');mapping={'base_refit':('base','refit'),'h3_only_refit':('R1','refit'),'h3_only_fixed_base':('R1','fixed_base'),'new_refit':('R3','refit'),'new_fixed_base':('R3','fixed_base')};annotated=[]
for index,x in enumerate(m,2):
 stage,policy=mapping[x['policy']];annotated.append(dict(**x,stage_alias=stage,original_identifier=armids[stage],readout=policy,meeting_role=meeting_role(stage,x['task']),checkpoint_declaration=declared_membership(stage,x['task'],declared),exposure='unknown',origin='REUSED_COMPLETED',source_file='multiretain-comparison-v1/reports/native_metrics.csv',source_row=index))
writecsv('REUSED_METRICS.csv',annotated)
lookup={(x['stage_alias'],x['task'],x['split'],x['layer'],x['cv_seed'],x['readout'],x['metric']):x for x in annotated};assert len(lookup)==len(annotated)
anchor=[]
for stage in ['base',*STAGES]:
 for task in TASKS:
  split='test' if task=='emp_H3' else 'dev'
  for layer in ['decoder_layer_16','final_norm']:
   for seed in [42,17,1234]:
    for policy in ['refit','fixed_base']:
     for metric in protocol['metrics']:
      x=lookup.get((stage,task,split,layer,str(seed),'refit' if stage=='base' else policy,metric));anchor.append(dict(stage=stage,task=task,split=split,layer=layer,cv_seed=seed,policy=policy,metric=metric,value=x['value'] if x else '',status='REUSED_COMPLETED' if x else 'AWAITING_DELIVERY',original_identifier=armids.get(stage,''),meeting_role=meeting_role(stage,task),checkpoint_declaration=declared_membership(stage,task,declared),exposure='unknown',source_row=x['source_row'] if x else '',base_policy_alias='same original base_refit predictions' if stage=='base' and policy=='fixed_base' else ''))
writecsv('STAGE_ANCHORS.csv',anchor);writecsv('STAGE_ANCHORS_AUROC.csv',[x for x in anchor if x['metric']=='auroc'])
cs=[]
for source,data in [('native_contrasts.csv',contrasts),('h3_only_minus_base_reference.csv',oldcontrasts)]:
 for index,x in enumerate(data,2):
  if source=='native_contrasts.csv':stage='R3';ref='R1' if x['contrast']=='new_minus_h3_only' else 'base'
  else:stage='R1';ref='base'
  cs.append(dict(stage=stage,reference_stage=ref,contrast_relation='nonadjacent' if (stage,ref)==('R3','R1') else 'base-reference',origin='REUSED_COMPLETED',source_file='multiretain-comparison-v1/reports/'+source,source_row=index,**x))
writecsv('REUSED_CONTRASTS.csv',cs)
adjacent=[adjacent_status(f'R{i-1}',f'R{i}',available) for i in range(2,7)]
writecsv('ADJACENT_STAGE_STATUS.csv',[dict(previous=x['previous'],current=x['current'],status=x['status'],missing=','.join(x['missing']),difference='',ci_low='',ci_high='',reason='Missing endpoint delivery; no interpolation or R3-minus-R1 substitution') for x in adjacent])
for name in ['LM_METRICS.csv','LM_CONTRASTS.csv','control_contrasts.csv']:
 shutil.copy2(n/'reports'/name,r/'tables'/name)
shutil.copy2(c/'contrasts.csv',r/'tables/BASE_R1_CONTROL_CONTRASTS.csv')
# Direct copies remain available for exact computational reanalysis; source hashes bind them.
for name in ['native_metrics.csv','native_contrasts.csv','h3_only_minus_base_reference.csv'] :shutil.copy2(n/'reports'/name,r/'tables'/name)
(r/'figures').mkdir(exist_ok=True)
for p in (w/'docs/experiments/ashay/multiretain-comparison-v1/figures').glob('*.png'):shutil.copy2(p,r/'figures'/p.name)
coverage=dict(status='PREPARATION_COMPLETE_NO_NEW_MODELS',new_verified_measurement_units=0,reused_completed_units={'base':468,'R1':468,'R3':468},incremental_pending={s:468 for s in ['R2','R4','R5','R6']},pending_incremental_units=1872,offered_perturbation_candidates_located=0,perturbation_expectations=2,adjacent_comparisons=adjacent,owned_gpu_jobs=0,gpu_stage_seconds=0,backbone_training=False,mathematical_audit_scope='Existing all-unit audits and paired checks reused after current payload hash checks; this extension independently verifies table annotations/source mapping only.')
save(r/'COVERAGE.json',coverage);save(r/'RUN_STATE.json',coverage)
backup=load(w/'docs/experiments/ashay/multiretain-comparison-v1/BACKUP_VERIFICATION.json');deps=backup['required_dependencies'];deps=dict(deps);deps['R3_archive']={k:backup[k] for k in ['remote_repository','remote_repository_type','remote_revision','remote_archive_path','remote_sidecar_path','sha256','bytes','payload_files_verified']};deps['R3_archive']['payload_root']=Path(backup['fresh_payload_root']).name;deps['restore_order']=['base_h3_archive','controls_archive','R3_archive','new_incremental_preparation_supplement'];deps['scope']='Full prior scientific recovery requires these archives. New v13 supplement contains no duplicate feature/probe caches or model weights.';save(r/'RESTORE_DEPENDENCIES.json',deps)
for name in ['CHECKPOINT_REGISTRY.json','COMPARISON_PROTOCOL.json','PROTOCOL_FROZEN.json','COVERAGE.json','RESTORE_DEPENDENCIES.json','LIVE_SMALL_FILE_HASHES.json'] :shutil.copy2(r/name,d/name)
for folder in ['tables','figures']:shutil.copytree(r/folder,d/folder,dirs_exist_ok=True)
save(r/'PREPARATION_EXECUTION.json',dict(status='PASS',wall_seconds=time.monotonic()-start,cpu_process_seconds=time.process_time()-cpu,new_gpu_seconds=0,new_fits=0,new_predictions=0,origin='Only deterministic annotation/copy of completed evidence. No new scientific measurements.'))
print('Preparation complete:',coverage,flush=True)
