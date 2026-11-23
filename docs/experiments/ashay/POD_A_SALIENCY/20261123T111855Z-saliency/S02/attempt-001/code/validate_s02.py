from pathlib import Path
import argparse,json,hashlib,csv,copy,math
from jsonschema import Draft202012Validator
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(test,message):
 if not test:raise ValueError(message)
def check_decision(row,parent_known=False,matched_endpoints=False,independent_run_evidence=False):
 dim=row['dimension'];status=row['decision']
 if dim=='parent_relative_descriptive' and not parent_known:require(status=='PENDING_EVIDENCE','unknown parent cannot support parent-relative effect')
 if dim in ['within_method_strength','between_method_matching'] and not matched_endpoints:require(status=='PENDING_EVIDENCE','unknown/unequal endpoints cannot support matched strength/method effect')
 if dim=='independent_replicates' and not independent_run_evidence:require(status=='PENDING_EVIDENCE','snapshots/CV seeds cannot support intervention replication')
 if dim=='standalone_benign_measurement' and not parent_known:require(status in ['CONDITIONALLY_PLANNED','PENDING_EVIDENCE'],'unknown parent must not fabricate admission or globally exclude potentially independent loading')
def check_conflict(record):
 if record['status']=='CONFLICTING':
  require(len(record['claims'])>=2 and len({json.dumps(x['value'],sort_keys=True) for x in record['claims']})>=2,'contradiction claims must remain visible')
  require(record['resolution'] is None and bool(record['needed_discriminator']),'unresolved contradiction cannot silently choose newest claim')
def merge_completed(existing,new):
 result=dict(existing)
 for key,value in new.items():
  require(key not in result or result[key]==value,'completed identity changed on replay');result[key]=value
 return result
def finite(x):
 if isinstance(x,float):require(math.isfinite(x),'nonfinite public value')
 elif isinstance(x,dict):
  for v in x.values():finite(v)
 elif isinstance(x,list):
  for v in x:finite(v)
def validate(public,control,package):
 p=Path(public);c=Path(control);pkg=Path(package);paths=json.loads((c/'PATHS.json').read_text());s01=Path(paths['S01_public']);input_inv=json.loads((s01/'DELIVERY_INVENTORY.json').read_text());ids={x['candidate_id'] for x in input_inv['candidates']};require(len(ids)==9,'source discovery count')
 schema=json.loads((p/'S02_EVIDENCE_DECISIONS.schema.json').read_text());Draft202012Validator.check_schema(schema)
 defs=json.loads((pkg/'S_RESULT_SCHEMAS.json').read_text())['$defs']
 registry=json.loads((p/'CANDIDATE_REGISTRY.json').read_text());require({x['candidate_id'] for x in registry['candidates']}==ids and len(registry['candidates'])==9,'registry exact scope')
 for row in registry['candidates']:
  Draft202012Validator(defs['candidate']).validate(row);require(row['payload_sha256'] is None and row['parent_id'] is None and row['fraction_selected'] is None and row['noise_scale'] is None,'unsupported payload/parent/units')
  require(row['temporal_endpoint']=='UNKNOWN' and row['eligibility']=='PENDING','no science/runtime readiness claim')
  require(row['seed_identities']['independent_intervention_run'] is None and row['seed_identities']['CV_seeds_are_intervention_replicates'] is False,'replication misuse')
 lineage=json.loads((p/'LINEAGE_EVIDENCE.json').read_text());claim_ids={x['claim_id'] for x in lineage['claims']};require(len(claim_ids)==len(lineage['claims'])==126,'claim identities')
 for claim in lineage['claims']:
  Draft202012Validator(schema['$defs']['claim']).validate(claim);require(claim['candidate_id'] in ids,'claim scope')
  if claim['status']=='UNKNOWN':require(claim['value'] is None or claim['field']=='objective_label_tension','unknown cannot acquire invented value')
  for source in claim['evidence_refs']:
   require(source['source_sha256'] and source['field'],'source identity/locator absent')
   if source.get('git_commit'):require(source['git_commit']=='3e3803a4326723b2fe711b4c33e1f3addfe81595','source is exact prior committed evidence, not future S02 commit')
 node_ids={x['node_id'] for x in lineage['nodes']};require(ids<=node_ids,'graph missing discoveries')
 for edge in lineage['edges']:require(edge['source'] in node_ids and edge['target'] in ids and edge['claim_id'] in claim_ids,'graph joins')
 selections=json.loads((p/'CHECKPOINT_SELECTION_FREEZE.json').read_text());require({x['candidate_id'] for x in selections['candidates']}==ids,'selection exact IDs')
 require(not selections['outcomes_inspected'] and not selections['score_based_selection'] and not selections['science_or_S03_execution_authorized'],'selection boundary')
 for row in selections['candidates']:require(row['retain_discovery'] and row['selected_for_conditional_candidate_recovery'] and row['selected_primary_parent_comparison_endpoint'] is None,'conditional recovery versus primary selection')
 endpoints=list(csv.DictReader((p/'ENDPOINT_AND_REPLICATION.csv').open()));require(len(endpoints)==9 and {x['candidate_id'] for x in endpoints}==ids,'endpoint scope')
 require(sorted(int(x['step_label']) for x in endpoints)==[1500]*7+[2000,2151],'both noise5 endpoints retained')
 replica=json.loads((p/'REPLICATION_LEDGER.json').read_text());require(replica['independent_intervention_count'] is None,'replicate count invented')
 for row in replica['candidates']:require(row['proven_independent_intervention_replicates'] is None and row['same_run'] is None and not row['CV_seeds_count_as_replication'],'replication unknowns')
 exposure=json.loads((p/'EXPOSURE_LEDGER.json').read_text());require({x['candidate_id'] for x in exposure['candidates']}==ids,'exposure scope')
 for row in exposure['candidates']:
  for key in ['actual_objective_version','actual_global_step','actual_optimizer_steps','valid_tokens_realized','unique_rows_realized','repeated_presentations_realized','sampler_and_source_versions_realized','calculated_nominal_tokens']:require(row[key] is None,'realized consumption inferred')
 eligibility=json.loads((p/'ELIGIBILITY_MATRIX.json').read_text());require(len(eligibility['rows'])==99 and len({(x['candidate_id'],x['dimension']) for x in eligibility['rows']})==99,'multidimensional scope')
 for row in eligibility['rows']:
  Draft202012Validator(schema['$defs']['eligibility']).validate(row);check_decision(row);require(set(row['evidence_claim_ids'])<=claim_ids,'eligibility evidence missing')
 contrasts=json.loads((p/'CONTRAST_ELIGIBILITY.json').read_text());require(len(contrasts['rows'])==62 and len({x['contrast_id'] for x in contrasts['rows']})==62,'finite contrast design')
 for row in contrasts['rows']:
  Draft202012Validator(schema['$defs']['contrast']).validate(row);require(row['target_candidate_id'] in ids,'contrast target out of scope')
  ref=row['reference_candidate_id'];require(ref is None or ref in ids or ref.startswith('historical-base:'),'contrast reference fabricated')
  if row['reference_role']=='IMMEDIATE_UNPERTURBED_PARENT':require(ref is None and row['decision']=='PENDING_EVIDENCE','parent/base confusion')
  if 'UNMATCHED' in row['reference_role']:require(row['decision']=='PENDING_EVIDENCE','unmatched strength/method effect falsely admitted')
  require(row['produced_estimate'] is None and not row['scientific_execution_authorized'],'results or execution invented')
 recovery=json.loads((p/'S03_RECOVERY_PLAN.json').read_text());require(set(recovery['selected_discovery_ids'])==ids and not recovery['execution_authorized'] and not recovery['active_package_guard_valid_for_S03'],'S03 guard/execution boundary')
 require({x['candidate_id'] for x in recovery['candidate_dependencies']}==ids,'recovery dependency scope')
 for row in recovery['candidate_dependencies']:
  require(row['immediate_parent_dependency'] is None and row['parent_dependency_reason'],'unknown parent dependency')
  for member in row['members']:require(member['provider_revision'] is None and not member['downloaded_in_S02'],'provider revision or transfer invented')
 calc=recovery['conditional_arithmetic'];require(calc['refitted_heads']==4212 and calc['fixed_base_applications']==4212 and calc['H3_each_policy']==702 and calc['remaining_five_each_policy']==3510 and calc['initial_CV_plus_final_solver_calls']==63180 and calc['LM_dev_units']==54,'conditional count arithmetic')
 backup=json.loads((p/'BACKUP_ROUTE_STATUS.json').read_text());require(backup['route_status']=='BACKUP_ROUTE_IDENTIFIED' and not backup['write_readback_verified'] and not backup['upload_performed'],'backup states conflated')
 for row in json.loads((p/'UNRESOLVED_DECISIONS.json').read_text())['rows']:
  require(row['alternative_interpretations'] and row['smallest_required_evidence'] and row['latest_safe_resolution'],'unactionable unknown')
  require(set(row['claim_ids'])<=claim_ids,'unresolved claims absent')
  require(row['claim_ids'] or row.get('source_binding'),'unresolved source unbound')
 source=json.loads((p/'S02_SOURCE_BINDING.json').read_text());require(source['new_source_payload_bytes']==0 and not source['scientific_work_started'],'scope expanded')
 require(source['private_source_files_reused']['count']==44 and source['private_source_files_reused']['bytes']==323809,'small source reuse accounting')
 amendment=json.loads((c/'PROPOSED_AMENDMENT_METADATA.json').read_text());require(amendment['future_publication_commit'] is None and digest(p/'PROPOSED_PACKAGE_AMENDMENT.patch')==amendment['patch_sha256'],'proposal not exact or fake published pin')
 require(digest(pkg/'S_SHA256SUMS')=='9d3a27d7535e81d87c147eb0d373f87aac009ed65caad4f98f7f56f343a69042','active package changed')
 # This metadata-only validator never reads datasets, tensors, archives or raw forget examples.
 for q in p.rglob('*'):
  if not q.is_file():continue
  data=q.read_bytes()
  require(not __import__('re').search(rb'(?:[?&]sig=|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)',data),'secret-bearing public content')
  require(q.name not in ['run_config.yaml','tokenizer.json','common.pt','train_state.pt','.metadata','__0_0.distcp'],'raw private data in Git')
  if q.suffix=='.json':finite(json.loads(data))
 binding=json.loads((p/'S02_SCHEMA_BINDING.json').read_text());require(binding['schema_sha256']==digest(p/'S02_EVIDENCE_DECISIONS.schema.json'),'schema seal')
 return {'status':'PASS','exact_discovery_ids':9,'canonical_candidate_records':9,'typed_claim_records':126,'eligibility_dimensions_per_candidate':11,'eligibility_rows':99,'planned_policy_relation_rows':62,'both_noise5_endpoints_retained':True,'conditional_recovery_not_primary_selection':True,'no_payload_parent_fraction_or_replication_fabrication':True,'new_source_payload_bytes':0,'new_model_payloads_or_scientific_units':0,'S01_whole_delivery_status':'PARTIAL_PRESERVED','S02_status':'LIMITED_SCOPE_COMPLETE','S03_guard_ready':False,'active_package_unchanged':True,'public_privacy_and_null_semantics':'PASS'}
def self_test():
 tests=[]
 def reject(name,fn):
  try:fn()
  except ValueError:tests.append({'case':name,'status':'REJECTED'});return
  raise ValueError('Synthetic negative accepted '+name)
 check_decision({'dimension':'standalone_benign_measurement','decision':'CONDITIONALLY_PLANNED'});tests.append({'case':'unknown_parent_allows_conditional_standalone','status':'PASS'})
 reject('unknown_parent_blocks_parent_relative',lambda:check_decision({'dimension':'parent_relative_descriptive','decision':'SUPPORTED_AT_METADATA_LEVEL'}))
 reject('unmatched_endpoint_cannot_be_strength_effect',lambda:check_decision({'dimension':'within_method_strength','decision':'SUPPORTED_AT_METADATA_LEVEL'}))
 reject('CV_seeds_or_snapshots_cannot_be_independent_interventions',lambda:check_decision({'dimension':'independent_replicates','decision':'SUPPORTED_AT_METADATA_LEVEL'}))
 conflict={'status':'CONFLICTING','claims':[{'value':'declaration A'},{'value':'declaration B'}],'resolution':None,'needed_discriminator':'Exact source implementation/history'};check_conflict(conflict);tests.append({'case':'contradictory_claims_retained_unresolved','status':'PASS'})
 bad=copy.deepcopy(conflict);bad['resolution']='newest wins';reject('contradiction_cannot_silently_choose_source',lambda:check_conflict(bad))
 receipts={'synthetic-unit':'synthetic-seal'};require(merge_completed(receipts,receipts)==receipts,'duplicate replay');tests.append({'case':'completed_receipt_replay_is_idempotent','status':'PASS'})
 reject('changed_seal_cannot_overwrite_completed_unit',lambda:merge_completed(receipts,{'synthetic-unit':'changed-seal'}))
 return tests
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--public-root',type=Path,required=True);ap.add_argument('--control-root',type=Path,required=True);ap.add_argument('--package-root',type=Path,required=True);a=ap.parse_args();result=validate(a.public_root,a.control_root,a.package_root);result['synthetic_decision_checks']=self_test();print(json.dumps(result,indent=2))
if __name__=='__main__':main()
