from pathlib import Path
import json,csv,hashlib,argparse,re,yaml
from jsonschema import Draft202012Validator
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--public-root',type=Path,required=True);ap.add_argument('--control-root',type=Path,required=True);ap.add_argument('--private-root',type=Path,required=True);a=ap.parse_args();p=a.public_root;c=a.control_root
 inv=json.loads((p/'DELIVERY_INVENTORY.json').read_text());schema=json.loads((p/'S01_REMOTE_EVIDENCE.schema.json').read_text());Draft202012Validator.check_schema(schema);validator=Draft202012Validator(schema)
 remote=[json.loads(line) for line in (p/'REMOTE_OBJECTS.jsonl').read_text().splitlines()];ids={x['provider_object_id'] for x in remote};assert len(ids)==len(remote)==148
 for row in remote:
  validator.validate(row)
  assert 'commit' not in row and 'repository' not in row
  for key in ['drive_id','shortcut_target_id','mime_type','reported_size_bytes','provider_revision','provider_version','modified_time','local_sidecar_sha256','local_sidecar_bytes']:
   if row[key] is None:assert row['null_reasons'].get(key)
  for digest in row['checksums']:
   if digest['origin']=='provider_declared':assert digest['verification_status']=='DECLARED_NOT_LOCALLY_VERIFIED'
   else:assert row['retrieval_status']=='SIDECAR_DOWNLOADED' and digest['digest']==row['local_sidecar_sha256']
  assert row['payload_identity_status']=='NOT_VERIFIED_BY_S01'
 cover=json.loads((p/'LISTING_COVERAGE.json').read_text());assert cover['status']=='PARTIAL' and len(cover['folders'])==43 and cover['unprocessed_exposed_continuations']==0
 for folder in cover['folders']:
  assert folder['folder_id'] in ids and folder['status']=='PARTIAL' and folder['terminal_page_evidence'] is None
  assert folder['count_semantics']=='observed_lower_bound' and folder['page_count']==len(folder['page_receipts'])
  for page in folder['page_receipts']:
   raw=a.private_root/page['private_evidence_id'];assert sha(raw)==page['metadata_observation_sha256']
   d=json.loads(raw.read_text())['result']['structuredContent'];assert page['child_count']==len(d['files'])
   assert not page['continuation_field_exposed'] and not page['repeated']
 assert len(inv['candidates'])==9 and inv['expected_grid'] is None
 assert len({x['candidate_id'] for x in inv['candidates']})==9
 assert len({x['family_folder'] for x in inv['candidates']})==8
 for x in inv['candidates']:
  assert x['checkpoint_folder_id'] in ids and x['candidate_id']=='drive-checkpoint:'+x['checkpoint_folder_id']
  assert x['actual_immediate_parent'] is None and x['actual_fraction_selected'] is None and x['intervention_seeds'] is None
  assert x['realized_exposure'] is None and x['temporal_endpoint']=='UNKNOWN' and x['scientific_qualification']=='NOT_PERFORMED'
  assert x['S02_scope_eligibility']=='ELIGIBLE_FOR_METADATA_ADJUDICATION_ONLY'
  for w in x['listed_weight_objects']:assert w['object_id'] in ids and w['payload_sha256'] is None and w['payload_verified'] is False
 side=json.loads((p/'SMALL_SIDECAR_INDEX.json').read_text());resume=json.loads((c/'RESUME_STATE.json').read_text());actual={x['object_id']:x for x in resume['sidecars']}
 assert len(side['files'])==len(actual)==44
 assert len({x['object_id'] for x in side['files']})==44
 assert sum(x['actual_source_bytes'] for x in side['files'])==side['source_payload_bytes']==323809
 assert side['conservative_cumulative_transfer_bytes']==647618<=20971520
 for x in side['files']:
  assert x['object_id'] in ids and x['actual_source_bytes']==x['reported_size_bytes']<=1048576
  assert x['name'] in ['latest_checkpointed_iteration.txt','run_config.yaml','metadata.json','tokenizer_config.json','tokenizer.json']
  original=Path(actual[x['object_id']]['path']);assert original.stat().st_size==x['actual_source_bytes'] and sha(original)==x['source_sha256']
  assert x['provider_revision'] is None and x['provider_revision_missing_reason'] and x['protection']=='LOCAL_HASH_VERIFIED_ONLY'
  # Every local sidecar hash is joined to exactly the same provider object in remote evidence.
  row=next(r for r in remote if r['provider_object_id']==x['object_id']);assert row['local_sidecar_sha256']==x['source_sha256']
 facts=list(csv.DictReader((p/'METADATA_AND_CONFOUNDERS.csv').open()));links=json.loads((p/'SOURCE_LINK_MAP.json').read_text())['links'];assert len(links)==9
 def sanitize(v):
  if isinstance(v,str) and ('/' in v or '\\' in v):return '[private absolute path omitted; basename] '+v.rstrip('/').split('/')[-1]
  if isinstance(v,list):return [sanitize(z) for z in v]
  return v
 parsed={}
 for row in facts:
  source=actual[row['source_object_id']];assert source['sha256']==row['source_sha256']
  if source['object_id'] not in parsed:parsed[source['object_id']]=yaml.safe_load(Path(source['path']).read_text())
  value=parsed[source['object_id']]
  for k in row['source_field'].split('.'):value=value.get(k) if isinstance(value,dict) else None
  assert sanitize(value)==json.loads(row['value'])
  assert row['candidate_id'] in {x['candidate_id'] for x in inv['candidates']}
  if row['source_line']:assert 1<=int(row['source_line'])<=len(Path(source['path']).read_text().splitlines())
 grid=list(csv.DictReader((p/'SWEEP_GRID_OBSERVED.csv').open()));assert len(grid)==9 and {x['candidate_id'] for x in grid}=={x['candidate_id'] for x in inv['candidates']}
 assert sorted(int(x['observed_iteration']) for x in grid)==[1500]*7+[2000,2151]
 assert {x['expected_grid'] for x in grid}=={'NOT_SUPPLIED'}
 assert not resume['queue'] and not resume.get('sidecar_failures') and not resume['owned_processes']
 # No signed URLs, credentials, raw source configs, or base64 sidecar bodies in research outputs.
 for q in p.rglob('*'):
  if not q.is_file():continue
  data=q.read_bytes();assert not re.search(rb'(?:[?&]sig=|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|hf_[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"b64_string"\s*:)',data),q.name
  assert q.name not in ['run_config.yaml','tokenizer.json','latest_train_state.pt','common.pt','train_state.pt','.metadata','__0_0.distcp']
 binding=json.loads((p/'S01_SCHEMA_BINDING.json').read_text());assert binding['remote_evidence_schema_sha256']==sha(p/'S01_REMOTE_EVIDENCE.schema.json')
 review=(p/'FUTURE_GATE_REVIEW.md').read_text();handoff=(p/'S02_HANDOFF.md').read_text()
 for term in ['S03','S04','S05','S07','BACKUP_ROUTE_IDENTIFIED','PRIVATE_WRITE_READBACK_VERIFIED','interruption']:
  assert term.lower() in review.lower() and term.lower() in handoff.lower()
 print(json.dumps({'status':'PASS','remote_records_validated':len(remote),'folders_pages_validated':43,'candidate_joins_validated':9,'exact_sidecars_rehashed':44,'source_declaration_rows_recomputed':len(facts),'observed_grid_rows':len(grid),'sidecar_source_bytes':323809,'conservative_transfer_bytes':647618,'coverage_status':'PARTIAL','S02_eligible_observed_subset':9,'science_units':0,'privacy_check':'PASS_FOR_PUBLIC_OUTPUTS','unknowns_and_provider_digests_preserved':True},indent=2))
if __name__=='__main__':main()
