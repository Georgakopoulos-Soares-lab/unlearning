"""Explicit engineering, original first-reference and equivalent-route policies.

Historical identity must be independently bound even when a checkpoint inherits
an already qualified implementation route. Engineering bytes are never promoted.
"""
from pathlib import Path
import json
from .contracts import require, verify_file, fixture_rows, canonical_sha, file_sha
from .budget import ENGINEERING, SCIENTIFIC

APPROVED_PROMPT_SHA = 'ce0aa8cc20c76c2caf779d8102d23101173ecf436e9d8c286b5a22d89026c611'
ROUTE_KEYS = ('parent_fingerprint','tokenizer_sha256','output_head_fingerprint',
              'route_id','environment_lock_sha256','resolved_inference_config_sha256',
              'peft_semantics_sha256','extraction_contract')


def reference_policy(mode: str, binding: dict, case: dict) -> str:
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
    require(all(ref.get(k)==binding.get(k) for k in ('parent_fingerprint','adapter_sha256','config_sha256','tokenizer_sha256')),
            'REFERENCE_STATE','Original fixture must describe the same full model')
    verify_file(ref,roots=binding['allowed_read_roots'])
    return 'COMPARE_INDEPENDENT_ORIGINAL'


def preflight(plan: dict, checkpoint_id: str):
    require(plan['stage']=='B04' and plan['approved_prompt_sha256']==APPROVED_PROMPT_SHA,'STAGE_APPROVAL','Exact revised B04 approval required')
    require(plan.get('next_stage_authorized') is False,'STAGE_APPROVAL','No stage queue')
    case = next((x for x in plan['cases'] if x['checkpoint_id']==checkpoint_id),None)
    require(case is not None,'UNPLANNED_CHECKPOINT',checkpoint_id)
    path=verify_file(case['binding_file'],roots=[plan['artifact_root']]);binding=json.loads(path.read_text())
    require(binding['checkpoint_id']==checkpoint_id,'CASE_HASH','Wrong case')
    if plan['mode']==SCIENTIFIC:
        require(case.get('approved_binding_sha256')==file_sha(path),'BINDING_HASH','Unreviewed scientific binding')
    policy=reference_policy(plan['mode'],binding,case)
    for group in ['input_files','source_files']:
        require(bool(binding.get(group)),'INCOMPLETE_MANIFEST',group)
        for record in binding[group]:verify_file(record,roots=binding['allowed_read_roots'])
    require(binding['adapter_sha256']==next(r['sha256'] for r in binding['input_files'] if r['path']==binding['adapter_root']+'/__0_0.distcp'),
            'CASE_HASH','Adapter payload not pinned')
    rows=fixture_rows(Path(plan['inputs']['fixture_path']),expected_sha=plan['inputs']['fixture_sha256'],expected_ordered_ids_sha=plan['inputs']['ordered_ids_sha256'])
    require(binding['route_id']==plan['route_id'],'ROUTE_HASH','Candidate changed')
    require(binding['environment_lock_sha256']==plan['environment_lock_sha256'],'RUNTIME_HASH','Runtime changed')
    return binding, rows, policy, canonical_sha(dict(binding_sha256=file_sha(path),fixture=plan['inputs'],mode=plan['mode']))
