"""Distinct T01 evidence check: provider responses and primary docs, not builder labels."""
from pathlib import Path
import json,csv,hashlib,datetime,subprocess,os,re,zipfile,pickletools
P=Path(__file__).parent;V=P.parents[1]
C=Path('/workspace/pod-a-saliency/control/20261123T111855Z-saliency/T_SERIES/v2/T01/attempt-001')
R=Path('/workspace/pod-a-saliency/research-POD_A_SALIENCY')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(l) for l in p.read_text().splitlines() if l]
def provider(name):
    d=read(C/'responses'/name)['result']
    if d.get('status')=='fulfilled':d=d['value']
    assert not d.get('isError')
    return d['structuredContent']
cat=rows(P/'DRIVE_CATALOG.jsonl');byid={x['object_id']:x for x in cat};bycat={x['catalog_id']:x for x in cat}
cov=read(P/'FOLDER_COVERAGE.json');add=read(P/'T01_ADDITION.json');doc=read(P/'DOCUMENTARY_EVIDENCE.json')
checks=[]
def check(name,ok,detail):
    assert ok,name+': '+detail
    checks.append({'name':name,'status':'PASS','detail':detail})
check('01_unique_provider_objects',len(cat)==len(byid)==len(bycat)==148,'Stable IDs deduplicate objects; names and payload checksums do not merge distinct objects')
discovered={cov['root_id']};folder_edges=[];seen_tokens=[];pagecount=0
for id,f in cov['folders'].items():
    assert f['terminal_observed'] and f['status']=='ENUMERATION_COMPLETE_FOR_ACCESSIBLE_SCOPE'
    token=None;tokens=set()
    for pg in f['pages']:
        d=provider(pg['response']);assert isinstance(d['files'],list)
        assert pg['input_page_token']==token
        assert pg['child_ids']==[x['id'] for x in d['files']]
        assert pg['next_page_token']==d.get('next_page_token')
        for n in d['files']:
            assert n['id'] in byid
            row=byid[n['id']]
            assert row['original_name']==n['title'] and row['mime_type']==n['mime_type']
            assert row['provider_reported_size_bytes']==(int(n['size']) if n.get('size') is not None else None)
            discovered.add(n['id']);folder_edges.append((id,n['id']))
        token=d.get('next_page_token');pagecount+=1
        if token:assert token not in tokens;tokens.add(token)
    assert token is None,'More pages remain, even if previous page empty'
check('02_exhausted_provider_pages',discovered==set(byid) and pagecount==43 and len(cov['folders'])==43,
      '43raw provider pages checked directly, terminal token state and exact parent/child association for every discovered object')
check('03_folder_and_shortcut_coverage',{x['object_id'] for x in cat if x['artifact_type']=='FOLDER'}==set(cov['folders']) and
      len(folder_edges)==147 and len(set(folder_edges))==147 and not cov['shortcut_records'] and not cov['errors'],
      'All folders covered; no shortcuts/cycles/aliases observed; provider parent IDs kept separate from listing edges')
for id,f in cov['folders'].items():
    for parent,child in folder_edges:
        if child==id:
            current=parent;ancestors={id}
            while current!=cov['root_id']:
                assert current not in ancestors;ancestors.add(current)
                ps=[p for p,ch in folder_edges if ch==current];assert len(ps)==1;current=ps[0]
for id in cov['rechecks']['folder_ids']:
    d=provider('recheck-page-'+id+'-001.json');assert not d.get('next_page_token')
    assert {x['id'] for x in d['files']}=={ch for p,ch in folder_edges if p==id}
    for n in d['files']:
        row=byid[n['id']]
        for field,original in [('title','original_name'),('mime_type','mime_type'),('modified_time','provider_modified_time')]:assert n.get(field)==row.get(original)
mi=provider('root-metadata-initial.json');mf=provider('root-metadata-final.json')
assert all(mi.get(k)==mf.get(k) for k in ['id','title','mime_type','parent_ids','created_time','modified_time'])
check('04_temporal_scope',len(cov['rechecks']['folder_ids'])==10 and not cov['observation_window']['is_atomic_snapshot'],
      'Root and nine material-reference/opaque endpoint folders rechecked; time-bounded observed inventory, no atomic snapshot claim')
types={'FOLDER','SHORTCUT','DATA_PAYLOAD','DATA_MANIFEST_OR_INDEX','CONFIG','CHECKPOINT_OR_MODEL_SHARD','TRAINING_STATE','EVENT_LOG','AGGREGATE_RESULTS','REPORT_OR_DOCUMENTATION','CODE','ARCHIVE_OR_CONTAINER','OTHER','UNKNOWN'}
roles={'FORGET','RETAIN','MIXED','OTHER_OR_CONTROL','UNKNOWN','NOT_APPLICABLE'}
relationships={'ACTUAL_PAYLOAD','MANIFEST_OR_INDEX','REFERENCE_ONLY','DERIVED_OUTPUT','CONTAINER','NOT_APPLICABLE'}
levels={'NAME_ONLY','METADATA_SUPPORTED','DOCUMENTED_ROLE','IDENTITY_BOUND_TO_MANIFEST','CONFLICTED','UNRESOLVED'}
check('05_independent_labels',all(x['artifact_type'] in types and x['documented_dataset_role'] in roles and
      x['relationship_to_data'] in relationships and x['evidence_level'] in levels for x in cat),
      'Artifact type, documented dataset role, relationship and evidence level are separate fields')
for id,e in doc.items():
    p=C/'documents'/id;assert sha(p)==e['local_sha256']==byid[id]['local_payload_sha256']
    assert p.stat().st_size==e['bytes']==byid[id]['provider_reported_size_bytes']
check('06_exact_small_sources',len(doc)==87 and sum(e['bytes'] for e in doc.values())==2099503,
      '87downloaded small-source files match exact local hashes and provider listing sizes; checksums explicitly local, not provider revisions')
refs=list(csv.DictReader((P/'DATASET_REFERENCE_MAP.csv').open()))
cfg=[x for x in cat if x['artifact_subtype']=='TRAINING_RUN_CONFIG']
high=[]
for row in cfg:
    id=row['object_id'];text=(C/'documents'/id).read_text()
    # Independent literal-key/indent review of exact source, not the YAML builder output.
    block=text.split('\ndataset:\n',1)[1].split('\nddp:\n',1)[0]
    assert 'forget_dataset_dir:' in block and 'forget_dataset_config_path:' in block
    assert 'retain_dataset_dirs:' in block and 'retain_dataset_config_paths:' in block
    relevant=[x for x in refs if x['source_id']==id];assert len(relevant)==4
    for ref in relevant:
        assert ref['original_value'] in block and ref['source_sha256']==sha(C/'documents'/id)
        assert ref['raw_payload_bytes_accessed']=='false' and ref['current_Pod_path_exists']=='false'
        assert not os.path.lexists(ref['original_value'])
    assert row['artifact_type']=='CONFIG' and row['documented_dataset_role']=='MIXED' and row['relationship_to_data']=='REFERENCE_ONLY'
    high.append({'object_id':id,'source_sha256':sha(C/'documents'/id),'primary_location':'Exact literal dataset block',
        'decision':'DOCUMENTED_FORGET_AND_RETAIN_REFERENCES_ONLY','reviewer':'AGENT_DISTINCT_PRIMARY_SOURCE_ROUTE'})
check('07_every_config_role_reviewed',len(cfg)==9 and len(refs)==36 and len({x['original_value'] for x in refs})==4,
      'Each of nine config dataset blocks inspected directly; four actual path targets and36source references, never converted into delivered payloads')
zipcount=indexcount=0
for id,e in doc.items():
    p=C/'documents'/id
    if e['kind'] in ['TRAIN_STATE_ZIP','COMMON_CHECKPOINT_ZIP']:
        with zipfile.ZipFile(p) as z:
            assert [{'name':m.filename,'uncompressed_bytes':m.file_size,'compressed_bytes':m.compress_size} for m in z.infolist()]==e['members']
            raw=z.read(next(n for n in z.namelist() if n.endswith('data.pkl')))
            names=[a for op,a,pos in pickletools.genops(raw) if op.name in ['SHORT_BINUNICODE','BINUNICODE','UNICODE','GLOBAL']]
            assert names==e['pickle_declared_strings']
            assert ('step' in names and 'consumed_train_samples' in names) if e['kind']=='TRAIN_STATE_ZIP' else ('checkpoint_version' in names and 'opt_param_scheduler' in names)
        zipcount+=1
    if e['kind']=='CHECKPOINT_STORAGE_INDEX':
        names=[a for op,a,pos in pickletools.genops(p.read_bytes()) if op.name in ['SHORT_BINUNICODE','BINUNICODE','UNICODE','GLOBAL']]
        assert 'torch.distributed.checkpoint.metadata' in names and 'TensorStorageMetadata' in names
        assert sorted({n for n in names if n.endswith('.distcp')})==['__0_0.distcp']
        target=e['manifest_bound_storage_object_ids'][0];assert target in byid and byid[target]['original_name']=='__0_0.distcp'
        assert byid[target]['local_payload_sha256'] is None and byid[target]['content_inspection_state']=='OPAQUE_LARGE_CONTAINER'
        high.append({'object_id':id,'source_sha256':sha(p),'target_object_id':target,
            'decision':'CHECKPOINT_STORAGE_INDEX_BINDS_NAME_AND_LISTED_ID_ONLY_NOT_DATASET_MANIFEST_OR_CURRENT_SHARD_BYTES','reviewer':'AGENT_DISTINCT_PRIMARY_SOURCE_ROUTE'})
        indexcount+=1
check('08_structural_containers',zipcount==26 and indexcount==9,
      'All26small ZIP member lists/opcode schemas and9checkpoint indexes checked without object deserialization; every opaque shard explicitly retained as coverage gap')
for x in cat:
    if x['original_name']=='tokenizer.json':
        d=read(C/'documents'/x['object_id']);assert d['model']['type']=='WordLevel' and len(d['model']['vocab'])==512
        assert x['artifact_subtype']=='TOKENIZER_MODEL_ASSET' and x['relationship_to_data']!='ACTUAL_PAYLOAD'
check('09_no_false_dataset_presence',all(x['artifact_type']!='DATA_PAYLOAD' for x in cat) and
      len(cov['content_review']['large_model_containers_uninspected'])==9 and
      add['dataset_presence_by_scope'][0]['actual_all_content_payload_count'] is None,
      'No model/tokenizer/log/config promoted into actual data; identified-payload count0distinct from unknown all-content count')
for id,ref in add['observation_evidence'].items():
    assert sha(C/'responses'/id)==ref['sha256']
for row in cat:
    review=row['review'];assert review['rationale'] and review['exact_location'] and review['unresolved_conflicts_or_limits'] and review['future_use_consequence']
    assert review['reviewer_type']=='AGENT_EVIDENCE_REVIEW_NOT_HUMAN_APPROVAL'
    for ref in review['evidence_source_ids']:
        assert (ref.startswith('OBS:') and ref[4:] in add['observation_evidence']) or (ref.startswith('DOC:') and ref[4:] in doc) or ref in add['source_records']
check('10_review_and_evidence_references',True,'Every item has an explicit evidence-located agent decision; no human approval asserted; observation/source hashes resolve')
flat=list(csv.DictReader((P/'DRIVE_CATALOG.csv').open()))
assert len(flat)==len(cat)
for row in flat:
    canonical=bycat[row['catalog_id']]
    for k,value in row.items():
        expect=canonical.get(k)
        if isinstance(expect,(list,dict,bool)):assert json.loads(value)==expect
        elif expect is None:assert value==''
        else:assert value==str(expect)
check('11_catalog_csv_matches',True,'Every exported CSV cell agrees with its canonical JSONL value')
matrix=list(csv.DictReader((P/'FUTURE_USE_MATRIX.csv').open()))
eligible={'ELIGIBLE_FOR_METADATA_OR_PROVENANCE_REVIEW','ELIGIBLE_UNDER_EXISTING_VERIFIED_RELEASE','CANDIDATE_FOR_LATER_QUALIFICATION','BLOCKED_IDENTITY_OR_ACCESS','BLOCKED_ROLE_OR_SEMANTICS','UNREVIEWED_CONTENT','OUT_OF_SCOPE'}
assert set(bycat)<={x['catalog_id'] for x in matrix}
for x in matrix:
    assert x['catalog_id'] in bycat or x['catalog_id'] in add['source_records']
    assert x['eligibility_state'] in eligible
    assert all(x[k] for k in ['specific_use','supporting_evidence','required_immutable_identity_or_version','remaining_checks_or_dependencies','permitted_conclusion','cannot_establish'])
    assert x['raw_dataset_use']=='NOT_ASSESSED_BY_THIS_AUDIT'
    if x['eligibility_state']=='ELIGIBLE_UNDER_EXISTING_VERIFIED_RELEASE':assert x['catalog_id']=='INHERITED_RETAIN_RELEASE' or bycat[x['catalog_id']]['artifact_type']=='EVENT_LOG'
check('12_future_use_scope',len(matrix)==167,'All catalog objects and distinct inherited retain release have explicit purpose-specific eligibility; no generic READY or advance-stage admission')
old=[json.loads(l) for l in (R/add['source_records']['INHERITED_S01']['path']).read_text().splitlines()]
endpoints=read(P/'ENDPOINT_CORRESPONDENCE.json');t00=read(V/'CONTINUATION_REGISTER.json')
assert {x['provider_object_id'] for x in old}==set(byid)
assert len(endpoints)==9 and [e['alias'] for e in endpoints]==[e['alias'] for e in t00['known_endpoint_roster']]
assert {x['delivered_step'] for x in endpoints if x['alias'] in ['candidate_04','candidate_05']}=={2000,2151}
for x in endpoints:assert sha(C/'documents'/x['current_config_id'])==x['current_config_sha256']
check('13_historical_reconciliation',True,'Same148S01IDs;9endpoint aliases/config identities retained; distinct noise5 endpoints not collapsed despite identical config bytes')
before=read(C/'BEFORE_STATE.json')
for n,h in before['existing_continuation_files'].items():assert sha(V/n)==h
assert sha(V/'CONTINUATION_REGISTER.json')==add['T00_register_sha256']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=R).decode().strip()==before['HEAD']
assert subprocess.check_output(['git','rev-parse','POD_A'],cwd=R).decode().strip()==before['original_POD_A']
assert subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R)==b''
assert subprocess.check_output(['git','diff','--cached','--name-only'],cwd=R)==b''
new=set(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=R).decode().splitlines())
allowed={str((V/n).relative_to(R)) for n in before['existing_continuation_files']}
assert all(x in allowed or x.startswith(str(P.relative_to(R))+'/') for x in new)
check('14_preserved_sources_and_owned_paths',True,'Sealed T00 bytes, tracked historical research, originalPOD_A/HEAD/index unchanged; only new owned T01 files')
assert all(x=='NOT_STARTED' for x in add['future_stage_execution'].values()) and add['new_scientific_admissions']==0
assert not add['publication']['committed'] and not add['publication']['pushed'] and not add['publication']['collaborator_sent']
state=add['separate_states'];assert state['ORIGINAL_RETAIN_AND_FORGET_REQUEST']=='PARTIAL' and state['DATASET_SCIENTIFIC_SUITABILITY']=='NOT_ESTABLISHED_BY_THIS_AUDIT'
assert state['DATASET_BYTE_ACCESS_STATUS']=='NOT_TESTED_NO_DATASET_PAYLOAD_IDENTIFIED'
check('15_no_scope_promotion',True,'No T02–T16, scientific admission/evaluation, raw-data byte access, publication or collaborator message; original request remains PARTIAL')
# Separate high-consequence verdict, backed by direct docs/container metadata above.
high.append({'scope':'SUPPLIED_TREE','decision':'No actual forget/retain payload identified in reviewed accessible metadata/documentation; no universal absence claim',
  'checks':['Every105file classified individually','Nine explicit source dataset blocks are references only','26state containers and9indexes inertly inspected','Nine large containers retained as uninspected coverage gaps'],
  'not_inferred':['Dataset nonexistent globally','Byte access established by metadata','Payload scientifically suitable','Entire producer filesystem absent'],
  'reviewer':'AGENT_DISTINCT_PRIMARY_SOURCE_ROUTE'})
result={'schema_version':'t01-independent-verification-v1','status':'PASS','checks':checks,'high_consequence_review':high,
 'route':'Direct raw provider responses, exact config text blocks and inert structural source checks; no import of build_audit.py',
 'catalog_rows':148,'future_use_rows':167,'documentation_and_structure_files':87,'source_bytes_checked':2099503,
 'register_sha256':sha(P/'T01_ADDITION.json'),'catalog_sha256':sha(P/'DRIVE_CATALOG.jsonl'),
 'scientific_results_validated_or_admitted':0,'source_Drive_writes':0,'external_messages_sent':0,
 'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
out=P/'VERIFICATION.json';tmp=out.with_suffix('.pending');tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(out)
print('T01_INDEPENDENT_VERIFICATION_PASS',len(checks),'checks',len(high),'direct high-consequence decisions')
