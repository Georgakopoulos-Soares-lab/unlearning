"""Source-first T02 verification, runnable solely from declared metadata inputs."""
import argparse,json,csv,hashlib,collections,sys,pickletools
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--package',required=True);ap.add_argument('--inputs',required=True);ap.add_argument('--observations',required=True);ap.add_argument('--deny-original-tree',action='store_true')
args=ap.parse_args();P=Path(args.package).resolve();I=Path(args.inputs).resolve();O=Path(args.observations).resolve()
sys.dont_write_bytecode=True
if args.deny_original_tree:
    allowed=P.parent
    def guard(event,values):
        if event=='open' and values and isinstance(values[0],(str,bytes)):
            path=Path(values[0]).resolve()
            if str(path).startswith('/workspace/pod-a-saliency/') and not path.is_relative_to(allowed):
                raise PermissionError('Producer-tree fallback prohibited in fresh metadata consumer')
    sys.addaudithook(guard)
sys.path.insert(0,str(P))
from acceptance_rules import verdict,classify_documentary_case,CRITERIA,USES
from safe_index_fields import storage_records
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
e=read(P/'T02_EVIDENCE.json');freeze=read(P/'REQUIREMENTS_FROZEN.json');ss={s['id']:s for s in e['source_register']}
def src(id):return read(I/ss[id]['snapshot_file'])
checks=[]
def check(id,condition,detail):
    assert condition,id+': '+detail
    checks.append({'id':id,'status':'PASS','detail':detail})
for s in ss.values():
    assert '/' not in s['snapshot_file'] and sha(I/s['snapshot_file'])==s['sha256']
    assert (I/s['snapshot_file']).stat().st_size==s['bytes']
check('V01_SOURCE_IDENTITIES',len(ss)==40,'40exact small declared inputs read; no original_path or native payload path opened')
assert e['requirements_amendment']['freeze_sha256']==sha(P/'REQUIREMENTS_FROZEN.json')
assert [c['id'] for c in freeze['mandatory_criteria']]==list(CRITERIA)
assert [u['id'] for u in freeze['required_downstream_uses']]==list(USES)
check('V02_FROZEN_SCOPE',not freeze['scope_reduction_amendments'] and len(e['mandatory_criteria'])==13,
      'All13mandatory gates and7required uses retained; test applicability not silently waived')
cat=[json.loads(l) for l in (I/'T01_CATALOG').read_text().splitlines()];byid={x['object_id']:x for x in cat}
configs=[x for x in cat if x['artifact_subtype']=='TRAINING_RUN_CONFIG'];refs=e['reference_resolutions']
oldrefs=list(csv.DictReader((I/'T01_REFERENCE_MAP').open()))
assert len(refs)==len(oldrefs)==36 and {x['reference_id'] for x in refs}=={x['reference_id'] for x in oldrefs}
for cfg in configs:
    id='CFG_'+cfg['object_id'];text=(I/id).read_text();block=text.split('\ndataset:\n',1)[1].split('\nddp:\n',1)[0]
    r=[x for x in refs if x['source_id']==id];assert len(r)==4 and ss[id]['sha256']==cfg['local_payload_sha256']
    for x in r:
        key=x['configuration_key'].removeprefix('dataset.').split('[')[0]
        assert key in block
        assert x['original_value'] in block
        assert x['source_snapshot_sha256']==ss[id]['sha256']
        assert x['target_provider_object_id'] is None and x['target_version_identity'] is None
        assert x['resolution_status']=='UNRESOLVED_INTENDED_TARGET'
        assert x['actual_run_or_invocation_binding']=='NOT_ESTABLISHED_BY_T02'
check('V03_REFERENCE_RECONCILIATION',len(configs)==9 and len({x['original_value'] for x in refs})==4,
      'Source-first literal config blocks confirm36references/four targets; no source path substituted for an object')
paths=read(O/'TARGET_PATH_CHECKS.json')
assert len(paths)==4 and all(x['observation']['errno']==2 and not x['content_opened'] for x in paths)
assert {x['target'] for x in paths}=={x['original_value'] for x in refs}
check('V04_LOCATION_LIMITS',all(x['producer_host_target_status']=='UNRESOLVED_HOST_AND_VERSION' for x in refs),
      'Recorded ENOENThere is not a producer-host absence assertion or a live access proof during replay')
assert len(e['dataset_declarations'])==2
for d in e['dataset_declarations']:
    assert d['actual_dataset_id'] is None and d['expected_member_count'] is None and d['observed_intended_member_count'] is None
    assert not d['complete_dataset_bundle_accepted'] and len(d['configured_role_evidence'])==9
    assert all(l['status']=='UNKNOWN' for l in d['provenance_links'])
    assert {x['name'] for x in d['splits']}=={'train','validation','test'}
    assert all(x['manifest_identity'] is None for x in d['splits'])
    assert next(x for x in d['splits'] if x['name']=='test')['applicability']=='UNRESOLVED_REQUIRES_SCOPE_DOCUMENTATION'
membership=e['membership_reconciliation'];assert len(membership)==16
assert all(x['expected_count'] is None and x['observed_object_identity'] is None and not x['required_availability_satisfied'] for x in membership)
check('V05_MEMBERSHIP_ROLES_PROVENANCE',True,'Declaration groups are not proven dataset versions;16requirement rows are not a dataset-file denominator; required provenance/split gaps remain T02 blockers')
payloads=src('S03_PAYLOADS')['payloads'];admissions=src('S03_LOCAL_ADMISSION')['records'];stats={**src('S03_STATS_1'),**src('S03_STATS_3')}
opaque={x['object_id'] for x in cat if x['content_inspection_state']=='OPAQUE_LARGE_CONTAINER'}
assert {x['object_id'] for x in e['container_dispositions']}==opaque and len(opaque)==9
container_summary=[]
for x in e['container_dispositions']:
    record=next(a for a in admissions if a['alias']==x['alias']);payload=next(a for a in payloads if a['alias']==x['alias'])
    shard=next(a for a in record['files'] if a['file_id']==x['object_id'])
    assert x['native_shard_sha256']==shard['sha256']==stats[x['local_native_path']]['sha256']==payload['native_shard_sha256']
    assert x['stat_binding']==stats[x['local_native_path']]['stat']
    assert x['native_payload_revision']==payload['payload_revision']
    iid=x['source_index_id'];raw=(I/iid).read_bytes();assert sha(I/iid)==x['source_index_sha256']
    assert any(m['SHA256']==x['source_index_sha256'] and m['relative_payload_member']=='.metadata' for m in payload['members'])
    # Shared inert field decoder; range, identity and role assertions checked here independently.
    strings=[a for op,a,pos in pickletools.genops(raw) if op.name in ['SHORT_BINUNICODE','BINUNICODE']]
    assert 'state_dict_metadata' in strings and 'storage_data' in strings and 'TensorStorageMetadata' in strings
    records=storage_records(raw);assert len(records)==x['index_declared_segments']==1126
    cursor=0
    for r in sorted(records,key=lambda z:z['offset']):
        assert r['offset']==cursor and r['length']>0 and r['relative_path']=='__0_0.distcp'
        assert r['fqn'].startswith(('decoder.','embedding.','output_layer.','optimizer.','rng_state/'))
        cursor+=r['length']
    assert cursor==x['declared_segments_contiguous_cover_bytes']==15516878934==byid[x['object_id']]['provider_reported_size_bytes']
    assert hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest()==x['segment_declaration_sha256']
    assert not x['current_Drive_payload_bytes_reverified'] and x['new_shard_payload_reads']==x['new_model_loads']==0
    assert x['disposition']=='MODEL_ONLY_ESTABLISHED'
    container_summary.append({'alias':x['alias'],'object_id':x['object_id'],'source_index_sha256':x['source_index_sha256'],
       'segments':len(records),'complete_declared_byte_range':cursor,'role':'model/optimizer/RNG checkpoint artifacts at bound versions'})
check('V06_ALL_CONTAINER_DISPOSITIONS',True,'All9T01IDs joined to exact S03 native manifest/index/stat identities; complete declared byte coverage, no model bodies or object deserialization')
uses={x['id']:x for x in e['required_downstream_uses']};assert set(uses)==set(USES)
expectedeligible={'U01','U03','U05','U06'}
for id,u in uses.items():
    f=next(x for x in freeze['required_downstream_uses'] if x['id']==id)
    assert all(u[k]==f[k] for k in ['stage','purpose','minimum_evidence','classification'])
    assert u['eligibility']==('ELIGIBLE' if id in expectedeligible else 'BLOCKED')
    assert set(u['input_source_ids'])<=ss.keys() and u['prohibited_inferences']
    if id in expectedeligible:assert not u['unmet_conditions']
    else:assert u['unmet_conditions']==u['minimum_evidence']
check('V07_PURPOSE_SPECIFIC_USES',True,'Four documentary use types eligible; three mandatory identity/provenance/membership uses blocked; no vacuous or universal readiness')
criteria={x['id']:x['status'] for x in e['mandatory_criteria']}
expected={'C01':'PASS','C02':'UNKNOWN','C03':'UNKNOWN','C04':'UNKNOWN','C05':'PASS','C06':'UNKNOWN','C07':'UNKNOWN','C08':'UNKNOWN','C09':'FAIL','C10':'PASS','C11':'PASS','C12':'PASS','C13':'PASS'}
assert criteria==expected
for x in e['mandatory_criteria']:assert x['classification']=='MANDATORY' and x['supporting_evidence'] and set(x['source_ids'])<=ss.keys()
assert e['unresolved_consequential_conflicts']==0 and all(c['resolution'] for c in e['conflicts'])
assert verdict(criteria,{id:u['eligibility'] for id,u in uses.items()})==e['T02_status']=='T02_BLOCKED_EXTERNAL'
check('V08_STRICT_VERDICT',True,'SixPASS/oneFAIL/sixUNKNOWN; unknown cannot pass; explicit T02 amendment never retroactively invalidates T00/T01')
for name,key in [('DATASET_REFERENCE_MAP.csv','reference_resolutions'),('MEMBERSHIP_RECONCILIATION.csv','membership_reconciliation'),('DOWNSTREAM_USE_MATRIX.csv','required_downstream_uses')]:
    table=list(csv.DictReader((P/name).open()));canonical=e[key];assert len(table)==len(canonical)
    for observed,want in zip(table,canonical):
        assert set(observed)==set(want)
        for k,value in observed.items():
            if isinstance(want[k],(dict,list,bool)):assert json.loads(value)==want[k]
            elif want[k] is None:assert value==''
            else:assert value==str(want[k])
check('V09_TABLES_AND_LINKS',all(set(d['source_ids'])<=ss.keys() for d in e['dataset_declarations']),
      'All three CSVs agree cell-for-cell with canonical model; source foreign keys and null reasons resolve')
cases=read(P/'CHALLENGE_CASES.json');results=[]
assert cases['expected_outcomes_decided_before_execution'] and len(cases['cases'])==20
for c in cases['cases']:
    observed=classify_documentary_case(c);assert observed==c['expected'],c['id']
    results.append({'id':c['id'],'expected':c['expected'],'observed':observed,'status':'PASS','synthetic':True})
gates=[]
def gate(id,cc,uu,expected,**kwargs):
    observed=verdict(cc,uu,**kwargs);assert observed==expected
    gates.append({'id':id,'expected':expected,'observed':observed,'status':'PASS','synthetic':True})
good={k:'PASS' for k in CRITERIA};ready={k:'ELIGIBLE' for k in USES}
gate('G01_ALL_REQUIRED_POSITIVE',good,ready,'T02_REQUIREMENTS_MET')
gate('G02_DROPPED_USES',good,{},'T02_BLOCKED_INTERNAL')
gate('G03_ALL_BLOCKED_NOT_READY',{**good,'C09':'FAIL'},{k:'BLOCKED' for k in USES},'T02_BLOCKED_EXTERNAL')
gate('G04_MANDATORY_EXEMPTION',{**good,'C03':'NOT_APPLICABLE'},ready,'T02_BLOCKED_INTERNAL')
gate('G05_INTERNAL_PRECEDENCE',criteria,{id:u['eligibility'] for id,u in uses.items()},'T02_BLOCKED_INTERNAL',internal_defects=['synthetic integrity defect'])
check('V10_ADVERSARIAL_AND_POSITIVE_CONTROLS',True,'20predeclared cases including10Appendix/6added/4positive plus5end-to-end verdict controls passed')
assert not e['scientific_state']['T03_executed'] and e['scientific_state']['new_scientific_admissions']==0
assert not e['scientific_state']['raw_data_evaluation_authorized'] and e['scientific_state']['original_request']=='PARTIAL'
assert e['publication']=={'state':'LOCAL_ONLY','commits':0,'pushes':0,'uploads':0,'messages_sent':0}
check('V11_BOUNDARIES',True,'No future-stage execution, scientific promotion, publication, raw access authority or original-scope closure')
print(json.dumps({'status':'PASS','route':'Separate source-first checker; direct source config text, receipt/index/stat joins, predicates and CSVs. Shared inert field decoder/pickletools explicitly acknowledged.',
  'checks':checks,'synthetic_challenges':results,'gate_controls':gates,'container_source_reviews':container_summary,
  'T02_assessment_verdict':'T02_BLOCKED_EXTERNAL','declared_sources_checked':len(ss),
  'decoded_source_bytes_checked':sum(s['bytes'] for s in ss.values()),'producer_tree_fallback':False,
  'native_shard_or_raw_data_reads':0,'metadata_package_path':str(P),'inputs_path':str(I),'evidence_sha256':sha(P/'T02_EVIDENCE.json')},indent=2))
