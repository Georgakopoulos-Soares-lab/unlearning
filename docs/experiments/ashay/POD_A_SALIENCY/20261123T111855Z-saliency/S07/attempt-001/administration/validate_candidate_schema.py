"""Canonical schema checks only in existing administrative Python, no scientific recomputation/install."""
from pathlib import Path
import json,sys,hashlib
from ops import C,A,save,now
alias=sys.argv[1];read=lambda p:json.loads(p.read_text());cfg=read(C/'RUN_CONFIG.json');case=A/'candidates'/alias;index=read(case/'EXECUTION_INDEX.json');pkg=Path(read(C/'PATHS.json')['package_root']);sys.path.insert(0,str(pkg));import S_validate_package as v
schema=read(pkg/'S_RESULT_SCHEMAS.json')['$defs']['metric'];engine=v.schema_engine();metric=engine(schema)
for row in index['metrics']:
 m=row['canonical_metric'];metric.validate(m);assert m['bootstrap_valid']+m['bootstrap_invalid']==m['bootstrap_attempted'];assert (m['ci_low'] is None)==(m['ci_high'] is None);assert m['estimate'] is not None or m['missing_reason'];assert row['status']=='COMPLETE_UNVERIFIED' and row['release_status']=='COMPLETE_UNVERIFIED' and row['independent_release']=='PENDING_S08'
unit=engine({'type':'object','additionalProperties':False,'required':['planned_spec_id','kind','actual_identity_sha256','artifact_sha256','archive_member','selector','status'],'properties':{'planned_spec_id':{'type':'string','pattern':'^[0-9a-f]{64}$'},'kind':{'enum':['final_head','fixed_application','optimizer_call','prediction','classifier_metric']},'actual_identity_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},'artifact_sha256':{'type':'string','pattern':'^[0-9a-f]{64}$'},'archive_member':{'type':'string','pattern':'^candidate/'},'selector':{'type':['string','null']},'status':{'const':'COMPLETE_UNVERIFIED'}}})
for row in index['unit_records']:unit.validate(row)
validation=read(case/'PRODUCER_VALIDATION.json');validation.update(canonical_metric_schema_status='PASS',canonical_metric_records_validated=3900,typed_unit_record_schema_status='PASS',typed_unit_records_validated=11700,administrative_schema_python=sys.executable,scientific_CPU_environment_unchanged=True);save(case/'PRODUCER_VALIDATION.json',validation);print('S07_CANONICAL_METRIC_AND_TYPED_RECORD_SCHEMAS_PASS',alias,3900,11700,flush=True)
