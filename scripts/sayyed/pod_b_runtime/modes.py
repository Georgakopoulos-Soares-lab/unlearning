"""Explicit engineering, original first-reference and equivalent-route policies.

Historical identity must be independently bound even when a checkpoint inherits
an already qualified implementation route. Engineering bytes are never promoted.
"""
from pathlib import Path
import json
from .contracts import require, verify_file, fixture_rows, canonical_sha, file_sha
from .budget import ENGINEERING, SCIENTIFIC

ROUTE_KEYS = ('parent_fingerprint','tokenizer_sha256','output_head_fingerprint',
              'route_id','environment_lock_sha256','resolved_inference_config_sha256',
              'peft_semantics_sha256','extraction_contract')


def reference_policy(mode: str, binding: dict, case: dict, *, inputs=None, rows=None) -> str:
    require(mode in (ENGINEERING,SCIENTIFIC),'MODE',mode)
    if mode == ENGINEERING:
        require(binding.get('scientifically_qualified') is False and binding.get('downstream_eligible') is False,
                'MODE_SEPARATION','Engineering outputs must remain ineligible')
        return 'NOT_AVAILABLE_ENGINEERING'
    proof = binding.get('reviewed_provenance',{})
    require(case.get('identity_established') is True and case.get('approved_binding_sha256'),
            'IDENTITY_BLOCKED','Scientific full-state/job association must be separately reviewed')
    require(all(proof.get(k) is True for k in ('full_inference_state_complete','job_association_established',
        'hidden_backbone_merge_or_extra_state_excluded')) and proof.get('authoritative_evidence_ids'),
        'IDENTITY_BLOCKED','Unknown historical backbone cannot inherit identity from another checkpoint')
    inherited = binding.get('qualified_route_receipt')
    if inherited:
        receipt = json.loads(verify_file(inherited,roots=binding['allowed_read_roots']).read_text())
        require(receipt.get('scientifically_qualified') is True and receipt.get('mode') == SCIENTIFIC,
                'ROUTE_INHERITANCE','Engineering receipts cannot become scientific routes')
        require(all(receipt.get(k)==binding.get(k) and k in binding for k in ROUTE_KEYS),
                'ROUTE_INHERITANCE','Parent, source/runtime/config/tokenizer/head/LoRA coordinates must match')
        require(receipt.get('all_route_gates_passed') is True,'ROUTE_INHERITANCE','Incomplete route receipt')
        return 'INHERITED_QUALIFIED_ROUTE'
    if binding.get('route_kind') == 'R0_ORIGINAL':
        require(proof.get('original_source_runtime_authenticated') is True,'ORIGINAL_ROUTE_BLOCKED','R0 requires actual original source/runtime')
        # No adapter reference prerequisite: this run creates the first original fixture.
        return 'CREATE_FIRST_ORIGINAL_REFERENCE'
    require(binding.get('route_kind') == 'R2_EQUIVALENT','ROUTE_KIND','Unsupported scientific route')
    ref = binding.get('reference') or {}
    require(ref.get('provenance_kind')=='AUTHORITATIVE_ORIGINAL_ROUTE' and ref.get('independent_of_candidate') is True
            and ref.get('same_full_state') is True and ref.get('original_source_evidence_ids'),
            'REFERENCE_BLOCKED','R2 requires an independent original-route fixture')
    require(ref.get('sha256') == case.get('original_reference_sha256'),'REFERENCE_HASH','Unpinned reference')
    validate_reference(binding,case,inputs,rows)
    return 'COMPARE_INDEPENDENT_ORIGINAL'


def preflight(plan: dict, checkpoint_id: str):
    require(plan.get('stage')=='B04' and bool(plan.get('approved_prompt_sha256')),'STAGE_APPROVAL','Pinned B04 approval required; execution separately requires live control')
    require(plan.get('next_stage_authorized') is False,'STAGE_APPROVAL','No stage queue')
    case = next((x for x in plan['cases'] if x['checkpoint_id']==checkpoint_id),None)
    require(case is not None,'UNPLANNED_CHECKPOINT',checkpoint_id)
    path=verify_file(case['binding_file'],roots=[plan['artifact_root']]);binding=json.loads(path.read_text())
    require(binding['checkpoint_id']==checkpoint_id,'CASE_HASH','Wrong case')
    require(binding.get('mode')==plan['mode'],'MODE_SEPARATION','Binding and plan mode differ')
    if plan['mode']==SCIENTIFIC:
        require(case.get('approved_binding_sha256')==file_sha(path),'BINDING_HASH','Unreviewed scientific binding')
    for group in ['input_files','source_files']:
        require(bool(binding.get(group)),'INCOMPLETE_MANIFEST',group)
        for record in binding[group]:verify_file(record,roots=binding['allowed_read_roots'])
    require(binding['adapter_sha256']==next(r['sha256'] for r in binding['input_files'] if r['path']==binding['adapter_root']+'/__0_0.distcp'),
            'CASE_HASH','Adapter payload not pinned')
    rows=fixture_rows(Path(plan['inputs']['fixture_path']),expected_sha=plan['inputs']['fixture_sha256'],expected_ordered_ids_sha=plan['inputs']['ordered_ids_sha256'])
    if plan['mode']==SCIENTIFIC:
        validate_scientific_binding(binding,plan['inputs'],rows)
    policy=reference_policy(plan['mode'],binding,case,inputs=plan['inputs'],rows=rows)
    require(binding['route_id']==plan['route_id'],'ROUTE_HASH','Candidate changed')
    require(binding['environment_lock_sha256']==plan['environment_lock_sha256'],'RUNTIME_HASH','Runtime changed')
    return binding, rows, policy, canonical_sha(dict(binding_sha256=file_sha(path),fixture=plan['inputs'],mode=plan['mode']))


# Full state includes both delivered and resolved effective model configuration.
STATE_KEYS = ('parent_fingerprint','adapter_sha256','config_sha256',
              'resolved_inference_config_sha256','tokenizer_sha256','output_head_fingerprint')


def state_fingerprint(binding):
    import re
    require(all(re.fullmatch('[0-9a-f]{64}',str(binding.get(k,''))) for k in STATE_KEYS),
            'MISSING_IDENTITY','Complete parent/adapter/config/tokenizer/head identity required')
    return canonical_sha({k:binding[k] for k in STATE_KEYS})


def fixture_identity(inputs,rows):
    import hashlib
    require(inputs is not None and rows is not None,'REFERENCE_CONTEXT','Exact approved fixture context required')
    return dict(fixture_sha256=inputs['fixture_sha256'],ordered_ids_sha256=inputs['ordered_ids_sha256'],
                sequence_sha256=[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows])


def validate_evidence(binding,required_ids):
    records=binding.get('evidence_records',[])
    by_id={r['evidence_id']:r for r in records}
    require(len(by_id)==len(records) and bool(required_ids) and set(required_ids)<=set(by_id),
            'AUTHORITATIVE_EVIDENCE','Missing or duplicate real evidence records')
    for evidence_id in required_ids:
        record=by_id[evidence_id]
        proof=json.loads(verify_file(record['file'],roots=binding['allowed_read_roots']).read_text())
        require(proof.get('authoritative') is True and not proof.get('is_response_template')
                and bool(proof.get('issuer')) and bool(proof.get('statement_utc'))
                and str(binding['job_id']) in [str(j) for j in proof.get('job_ids',[])]
                and binding['full_state_fingerprint'] in proof.get('bound_full_state_fingerprints',[]),
                'AUTHORITATIVE_EVIDENCE','Current observations/templates do not attest a historical job')


def validate_scientific_binding(binding,inputs,rows):
    expected=state_fingerprint(binding)
    require(binding.get('full_state_fingerprint')==expected,'BOUND_STATE','Contradictory complete-state fingerprint')
    for key,value in fixture_identity(inputs,rows).items():
        require(binding.get(key)==value,'REFERENCE_FIXTURE',key)
    contract=binding.get('extraction_contract')
    from .contracts import LAYERS,ATOL,RTOL
    require(isinstance(contract,dict) and contract.get('layers')==list(LAYERS)
            and contract.get('feature_width')==1920 and contract.get('physical_batch_size')==8
            and contract.get('sequence_length')==1000 and contract.get('vocab_size') in (256,512)
            and contract.get('atol')==ATOL and contract.get('rtol')==RTOL,
            'EXTRACTION_CONTRACT','Frozen coordinates, batching, native vocabulary and tolerances')
    require(contract.get('tokenization')=='historical_char_no_special' and contract.get('pad_id')==1
            and contract.get('nucleotide_ids')==dict(A=65,C=67,G=71,T=84,N=78),
            'TOKENIZATION_UNSUPPORTED','Frozen native tokenizer contract required')
    require(bool(binding.get('parent_tensor_specs')) and len(binding.get('adapter_tensor_specs',{}))==200,
            'BOUND_STATE','Expected actual tensor/buffer records are required')
    from .contracts import SCHEMA_SHA256
    import hashlib
    schema={k:{'shape':v['shape'],'dtype':v['dtype']} for k,v in binding['adapter_tensor_specs'].items()}
    require(hashlib.sha256(json.dumps(schema,sort_keys=True).encode()).hexdigest()==SCHEMA_SHA256,
            'TENSOR_SCHEMA','Native200-key schema changed')
    resolved=binding.get('resolved_inference_config')
    require(isinstance(resolved,dict) and canonical_sha(resolved)==binding['resolved_inference_config_sha256'],
            'EFFECTIVE_CONFIG','Resolved effective configuration must be explicit')
    ids=binding.get('reviewed_provenance',{}).get('authoritative_evidence_ids',[])
    validate_evidence(binding,ids)


def validate_reference(binding,case,inputs,rows):
    from .gate import load_result
    from .contracts import validate_forward
    ref=binding['reference']
    expected={k:binding[k] for k in STATE_KEYS}
    expected.update(full_state_fingerprint=state_fingerprint(binding),
                    extraction_contract=binding['extraction_contract'],**fixture_identity(inputs,rows))
    for key,value in expected.items():
        require(ref.get(key)==value,'REFERENCE_STATE',key)
    path=verify_file(ref,roots=binding['allowed_read_roots']);meta=json.loads(path.read_text())
    for key,value in expected.items():require(meta.get(key)==value,'REFERENCE_METADATA',key)
    require(meta.get('provenance_kind')=='AUTHORITATIVE_ORIGINAL_ROUTE'
            and meta.get('independent_of_candidate') is True and meta.get('candidate_generated') is False
            and meta.get('mode')!='ENGINEERING_DIAGNOSTIC',
            'REFERENCE_BLOCKED','Candidate-generated metadata is not original-route evidence')
    require(meta.get('original_source_evidence_ids')==ref.get('original_source_evidence_ids'),
            'REFERENCE_METADATA','Evidence IDs contradict reference record')
    validate_evidence(binding,ref['original_source_evidence_ids'])
    if 'arrays_file' in ref:require(ref['arrays_file']==meta.get('arrays_file'),'REFERENCE_METADATA','Contradictory array identity')
    verify_file(meta['arrays_file'],roots=binding['allowed_read_roots'])
    output=load_result(ref,binding['allowed_read_roots'])
    validate_forward(output,rows,binding['extraction_contract'])
    require(output['sequence_sha256']==expected['sequence_sha256'],'REFERENCE_FIXTURE','Changed sequence digests')
    return output
