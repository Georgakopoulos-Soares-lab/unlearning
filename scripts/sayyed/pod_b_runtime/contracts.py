"""Strict B04 identity, tensor and training-output contracts.

This module implements no model or substitute LoRA. An authoritative binding and
an independently authenticated reference must be reviewed/pinned before a native
backend can be invoked. Metadata validation cannot establish that provenance.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

import numpy as np

LAYERS = tuple([f'decoder_layer_{i}' for i in range(25)] + ['final_norm'])
ATOL = 1e-4
RTOL = 1e-5
SCHEMA_SHA256 = '38a84e1cd2b75b58e7a6d61fb2114238d17812f7301a5e00e2f5e1091b831e78'


class GateError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f'{code}: {message}')


def require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise GateError(code, message)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_file(record: dict, *, roots: list[str] | None = None) -> Path:
    path = Path(record['path'])
    require(path.is_absolute(), 'INPUT_PATH', 'Input paths must be explicit and absolute')
    require(path.is_file() and not path.is_symlink(), 'MISSING_INPUT', str(path))
    if roots is not None:
        require(any(path.resolve().is_relative_to(Path(r).resolve()) for r in roots), 'INPUT_PATH', str(path))
    require(isinstance(record.get('sha256'), str) and re.fullmatch('[0-9a-f]{64}', record['sha256']) is not None,
            'HASH_FORMAT', 'A provider ID/ETag is not a SHA256')
    require(path.stat().st_size == record['bytes'], 'INPUT_BYTES', str(path))
    require(file_sha(path) == record['sha256'], 'INPUT_HASH', str(path))
    return path


def output_path(path: str | Path, allowed_roots: list[str]) -> Path:
    require(Path(path).is_absolute(), 'OUTPUT_PATH', 'Relative output paths are not authorized')
    target = Path(path).resolve()
    require(target.is_absolute() and bool(allowed_roots), 'OUTPUT_PATH', 'Explicit stage output root required')
    require(any(target.is_relative_to(Path(r).resolve()) for r in allowed_roots), 'OUTPUT_PATH', str(target))
    require(not target.exists(), 'OUTPUT_EXISTS', str(target))
    return target


def fixture_rows(path: Path, *, expected_sha: str, expected_ordered_ids_sha: str,
                 expected_rows: int = 12) -> list[dict]:
    require(file_sha(path) == expected_sha, 'FIXTURE_HASH', str(path))
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    require(len(rows) == expected_rows, 'FIXTURE_ROWS', str(len(rows)))
    ids = [r['id'] for r in rows]
    require(len(set(ids)) == len(ids), 'DUPLICATE_IDS', 'Fixture contains duplicate example IDs')
    require(all(r.get('split') == 'train' for r in rows), 'NON_TRAINING_INPUT', 'Only approved training rows may run')
    require(canonical_sha(ids) == expected_ordered_ids_sha, 'FIXTURE_ORDER', 'Unexpected ordered input IDs')
    require(all(isinstance(r.get('sequence'), str) and r['sequence'] and set(r['sequence']) <= set('ACGTN')
                for r in rows), 'SEQUENCE_CONTRACT', 'Do not normalize or replace frozen sequence bytes')
    return rows


def validate_tensor_records(expected: dict, records: list[dict], expected_storage: list[str],
                            actual_storage: list[str]) -> None:
    require(len(actual_storage) == len(set(actual_storage)) and sorted(actual_storage) == sorted(expected_storage),
            'SHARD_SET', 'Incomplete or duplicate storage shards')
    names = [r['key'] for r in records]
    require(len(names) == len(set(names)), 'DUPLICATE_MAPPING', 'A required tensor was mapped more than once')
    require(set(names) == set(expected), 'TENSOR_KEYS', 'Missing or unexpected inference tensor')
    for record in records:
        spec = expected[record['key']]
        require(record['shape'] == spec['shape'], 'TENSOR_SHAPE', record['key'])
        require(record['dtype'] == spec['dtype'], 'TENSOR_DTYPE', record['key'])
        require(record['sha256'] == spec['sha256'], 'TENSOR_CONTENT', record['key'])
        require(record.get('finite') is True, 'NONFINITE_TENSOR', record['key'])


def binding_preflight(plan: dict, checkpoint_id: str, binding_path: Path) -> tuple[dict, list[dict], str]:
    cases = [c for c in plan['representatives'] if c['id'] == checkpoint_id]
    require(len(cases) == 1, 'UNPLANNED_CHECKPOINT', checkpoint_id)
    case = cases[0]
    # This is intentionally checked before loading a backend or importing torch.
    require(case.get('identity_established') is True and bool(case.get('approved_binding_sha256')),
            'IDENTITY_BLOCKED', 'No reviewed full inference-state/job binding; CPU adapter PASS cannot substitute')
    require(binding_path.is_file(), 'MISSING_BINDING', str(binding_path))
    require(file_sha(binding_path) == case['approved_binding_sha256'], 'BINDING_HASH', str(binding_path))
    binding = json.loads(binding_path.read_text())
    require(binding.get('checkpoint_id') == checkpoint_id and binding.get('family') == case['family']
            and str(binding.get('job_id')) == str(case['job_id']), 'JOB_BINDING', checkpoint_id)
    proof = binding.get('reviewed_provenance', {})
    require(proof.get('full_inference_state_complete') is True and proof.get('job_association_established') is True
            and proof.get('hidden_backbone_merge_or_extra_state_excluded') is True
            and bool(proof.get('authoritative_evidence_ids')), 'IDENTITY_BLOCKED', 'Full-state evidence incomplete')
    require(binding.get('route_kind') in ('R0_ORIGINAL', 'R2_EQUIVALENT'), 'ROUTE_KIND', 'Unsupported route')
    require(bool(binding.get('source_files')) and bool(binding.get('parent_files'))
            and bool(binding.get('adapter_files')), 'INCOMPLETE_MANIFEST', 'Full source/parent/adapter manifests required')
    require(binding.get('adapter_sha256') == case['adapter_sha256']
            and binding.get('config_sha256') == case['config_sha256'], 'CASE_HASH', 'Changed adapter/config')
    for name in ('parent_fingerprint', 'tokenizer_sha256', 'output_head_fingerprint', 'route_source_sha256',
                 'resolved_inference_config_sha256', 'environment_lock_sha256'):
        require(re.fullmatch('[0-9a-f]{64}', str(binding.get(name, ''))) is not None, 'MISSING_IDENTITY', name)
    require(binding['route_source_sha256'] == case.get('backend_source_sha256'), 'ROUTE_HASH', 'Stale route identity')
    for group in ('source_files', 'parent_files', 'adapter_files', 'evidence_files'):
        require(bool(binding.get(group)), 'INCOMPLETE_MANIFEST', group)
        paths = [r['path'] for r in binding[group]]
        require(len(paths) == len(set(paths)), 'DUPLICATE_FILE', group)
        for record in binding[group]:
            verify_file(record, roots=binding['allowed_read_roots'])
    identity_files = binding.get('identity_files', {})
    for role, field in [('delivered_config', 'config_sha256'), ('resolved_inference_config', 'resolved_inference_config_sha256'),
                        ('tokenizer', 'tokenizer_sha256'), ('environment_lock', 'environment_lock_sha256')]:
        require(role in identity_files, 'INCOMPLETE_MANIFEST', role)
        verify_file(identity_files[role], roots=binding['allowed_read_roots'])
        require(identity_files[role]['sha256'] == binding[field], 'IDENTITY_FILE_HASH', role)
    require(bool(binding.get('parent_tensor_specs')), 'INCOMPLETE_MANIFEST', 'Native inference tensors AND buffers must be enumerated')
    backend_file = binding.get('backend_file')
    require(backend_file is not None and backend_file['sha256'] == binding['route_source_sha256']
            and backend_file in binding['source_files'], 'NATIVE_BACKEND_MISSING', 'Pin the actual native implementation before allocation')
    head_record = identity_files.get('output_head_manifest')
    require(head_record is not None, 'INCOMPLETE_MANIFEST', 'output_head_manifest')
    head_path = verify_file(head_record, roots=binding['allowed_read_roots'])
    require(json.loads(head_path.read_text()).get('fingerprint') == binding['output_head_fingerprint'],
            'OUTPUT_HEAD', 'Output/embedding/norm identity not bound')
    require(len(binding.get('adapter_tensor_specs', {})) == 200, 'TENSOR_SCHEMA', 'All200 native adapter keys required')
    modules = {key.split('.adapter.')[0] for key in binding['adapter_tensor_specs']}
    require(len(modules) == 100 and all('.adapter.' in key for key in binding['adapter_tensor_specs']),
            'TENSOR_SCHEMA', 'All100 native modules required')
    observed_schema = {k: {'shape': v['shape'], 'dtype': v['dtype']}
                       for k, v in binding['adapter_tensor_specs'].items()}
    schema_hash = hashlib.sha256(json.dumps(observed_schema, sort_keys=True).encode()).hexdigest()
    require(schema_hash == SCHEMA_SHA256, 'TENSOR_SCHEMA', 'Native names/shapes/dtypes differ from the pinned200-key schema')
    contract = binding.get('extraction_contract', {})
    require(contract.get('layers') == list(LAYERS) and contract.get('feature_width') == 1920
            and contract.get('physical_batch_size') == 8 and contract.get('sequence_length') == 1000
            and contract.get('vocab_size') == 512, 'EXTRACTION_CONTRACT', 'Unqualified coordinate/batch/head change')
    require(contract.get('tokenization') == 'historical_char_no_special', 'TOKENIZATION_UNSUPPORTED',
            'A different original transformation requires an explicitly reviewed contract amendment')
    require(contract.get('nucleotide_ids') == dict(A=65, C=67, G=71, T=84, N=78)
            and contract.get('pad_id') == 1, 'TOKENIZATION_UNSUPPORTED',
            'Do not remap the pinned tokenizer/head to make an inference load pass')
    require(contract.get('atol') == ATOL and contract.get('rtol') == RTOL, 'TOLERANCE_CHANGE', 'Smoke gate is frozen')
    reference = binding.get('reference', {})
    require(reference.get('provenance_kind') == 'AUTHORITATIVE_ORIGINAL_ROUTE'
            and reference.get('same_full_state') is True and bool(reference.get('original_source_evidence_ids')),
            'REFERENCE_BLOCKED', 'A candidate/parent-only fixture cannot authenticate adapter equivalence')
    if binding['route_kind'] == 'R2_EQUIVALENT':
        require(reference.get('independent_of_candidate') is True, 'REFERENCE_BLOCKED', 'Self-generated reference')
    require(reference.get('sha256') == case.get('original_reference_sha256'), 'REFERENCE_HASH', 'Reference not frozen in plan')
    state_components = {k: binding[k] for k in ('parent_fingerprint', 'adapter_sha256', 'config_sha256',
                                               'tokenizer_sha256', 'output_head_fingerprint')}
    require(reference.get('full_state_fingerprint') == canonical_sha(state_components)
            and reference.get('fixture_sha256') == plan['inputs']['fixture_sha256']
            and reference.get('ordered_ids_sha256') == plan['inputs']['ordered_ids_sha256'],
            'REFERENCE_STATE', 'Fixture must bind the same complete state and exact training membership')
    verify_file(reference, roots=binding['allowed_read_roots'])
    rows = fixture_rows(Path(plan['inputs']['fixture_path']), expected_sha=plan['inputs']['fixture_sha256'],
                        expected_ordered_ids_sha=plan['inputs']['ordered_ids_sha256'], expected_rows=plan['inputs']['rows'])
    components = {key: binding[key] for key in ('parent_fingerprint', 'adapter_sha256', 'config_sha256',
        'tokenizer_sha256', 'output_head_fingerprint', 'route_source_sha256', 'resolved_inference_config_sha256',
        'environment_lock_sha256', 'extraction_contract')}
    components['fixture_sha256'] = plan['inputs']['fixture_sha256']
    components['reference_sha256'] = reference['sha256']
    for group in ['parent_files', 'adapter_files', 'source_files']:
        components[group] = [{'path': r['path'], 'sha256': r['sha256'], 'bytes': r['bytes']}
                             for r in sorted(binding[group], key=lambda r: r['path'])]
    return binding, rows, canonical_sha(components)


def numeric_comparison(actual: np.ndarray, reference: np.ndarray, name: str,
                       *, atol: float = ATOL, rtol: float = RTOL) -> dict:
    actual = np.asarray(actual)
    reference = np.asarray(reference)
    require(actual.shape == reference.shape, 'OUTPUT_SHAPE', name)
    require(np.isfinite(actual).all() and np.isfinite(reference).all(), 'NONFINITE_OUTPUT', name)
    delta = np.abs(actual.astype(np.float64) - reference.astype(np.float64))
    allowed = atol + rtol * np.abs(reference.astype(np.float64))
    bad = delta > allowed
    index = list(np.unravel_index(np.argmax(delta), delta.shape)) if delta.size else []
    return {'name': name, 'pass': not bool(np.any(bad)), 'atol': atol, 'rtol': rtol,
            'max_absolute_error': float(np.max(delta, initial=0)),
            'relative_error_definition': 'abs(delta)/max(abs(reference),atol)',
            'max_relative_error': float(np.max(delta / np.maximum(np.abs(reference), atol), initial=0)),
            'failing_elements': int(np.sum(bad)), 'max_error_index': [int(x) for x in index]}


def validate_forward(output: dict, rows: list[dict], contract: dict, *, hooks: bool = True) -> None:
    n, length, width, vocab = len(rows), contract['sequence_length'], contract['feature_width'], contract['vocab_size']
    require(output.get('ids') == [r['id'] for r in rows], 'OUTPUT_IDS', 'Filler/stale/reordered IDs')
    require(output.get('sequence_sha256') == [hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows],
            'OUTPUT_SEQUENCE', 'Changed input bytes')
    require(output.get('physical_batch_size') == 8 and output.get('filler_ids', []) == [], 'FILLER_OUTPUT', 'Filler/physical shape')
    logical = output.get('logical_batch_size')
    require(logical in (1, 8), 'LOGICAL_BATCH', str(logical))
    batches = (n + logical - 1) // logical
    require(output.get('hook_calls') == {k: batches for k in contract['layers']} if hooks
            else output.get('hook_calls') == {}, 'HOOK_COUNT', 'Stale, duplicate or missing hooks')
    features = output.get('features', {})
    require(set(features) == (set(contract['layers']) if hooks else set()), 'COORDINATES', 'All intended coordinates required')
    for key, value in features.items():
        require(isinstance(value, np.ndarray) and value.shape == (n, width) and value.dtype == np.float32,
                'FEATURE_SCHEMA', key)
        require(np.isfinite(value).all(), 'NONFINITE_OUTPUT', key)
    for key, shape, dtype in [('tokens', (n, length), np.int64), ('positions', (n, length), np.int64),
        ('target_mask', (n, length - 1), np.bool_), ('n_tokens', (n,), np.int64), ('nll_sum', (n,), np.float32),
        ('logits', (n, length, vocab), np.float32)]:
        value = output.get(key)
        require(isinstance(value, np.ndarray) and value.shape == shape and value.dtype == dtype, 'OUTPUT_SCHEMA', key)
        require(np.isfinite(value).all(), 'NONFINITE_OUTPUT', key)
    require(np.array_equal(output['n_tokens'], output['target_mask'].sum(axis=1)), 'TARGET_COUNT', 'Mask/count mismatch')
    require(np.all((output['tokens'] >= 0) & (output['tokens'] < vocab)), 'TOKEN_RANGE', 'Full vocabulary required')
    if contract['tokenization'] == 'historical_char_no_special':
        positions = np.tile(np.arange(length, dtype=np.int64), (n, 1))
        require(np.array_equal(output['positions'], positions), 'POSITION_IDS', 'Changed position contract')
        mapping, pad = contract['nucleotide_ids'], contract['pad_id']
        for i, row in enumerate(rows):
            sequence = row['sequence']
            require(len(sequence) <= length, 'INPUT_LENGTH', row['id'])
            expected = np.full(length, pad, dtype=np.int64)
            expected[:len(sequence)] = [mapping[c] for c in sequence]
            require(np.array_equal(output['tokens'][i], expected), 'TOKENIZATION', row['id'])
            require(np.array_equal(output['target_mask'][i], np.arange(1, length) < len(sequence)), 'TARGET_MASK', row['id'])
            require(int(output['n_tokens'][i]) == len(sequence) - 1, 'TARGET_COUNT', row['id'])


def independent_lm_reduction(output: dict) -> tuple[np.ndarray, dict]:
    """Float64 diagnostic from full-vocabulary logits; canonical float32 sums stay unchanged."""
    logits = output['logits'][:, :-1].astype(np.float64)
    targets = output['tokens'][:, 1:]
    maximum = np.max(logits, axis=-1)
    logsumexp = maximum + np.log(np.sum(np.exp(logits - maximum[..., None]), axis=-1))
    chosen = np.take_along_axis(logits, targets[..., None], axis=-1)[..., 0]
    sums64 = np.sum((logsumexp - chosen) * output['target_mask'], axis=1, dtype=np.float64)
    record = numeric_comparison(output['nll_sum'], sums64, 'LM_independent_float64_diagnostic')
    record['canonical_sum_dtype_unchanged'] = 'float32'
    return sums64, record


def compare_forward(actual: dict, reference: dict, rows: list[dict], contract: dict, *, hooks: bool = True) -> list[dict]:
    validate_forward(actual, rows, contract, hooks=hooks)
    validate_forward(reference, rows, contract, hooks=hooks)
    require(actual['ids'] == reference['ids'], 'OUTPUT_IDS', 'Reference order mismatch')
    for key in ['tokens', 'positions', 'target_mask', 'n_tokens']:
        require(np.array_equal(actual[key], reference[key]), 'EXACT_OUTPUT_MISMATCH', key)
    records = [numeric_comparison(actual['features'][k], reference['features'][k], k) for k in contract['layers']] if hooks else []
    records.extend(numeric_comparison(actual[k], reference[k], k) for k in ['logits', 'nll_sum'])
    _, diagnostic = independent_lm_reduction(actual)
    records.append(diagnostic)
    require(all(r['pass'] for r in records), 'NUMERICAL_MISMATCH', json.dumps([r for r in records if not r['pass']]))
    return records


def loaded_state(snapshot: dict, binding: dict, *, previous_generation: int | None = None) -> None:
    require(snapshot.get('parent_fingerprint') == binding['parent_fingerprint'], 'WRONG_PARENT', 'Backbone/buffer state changed')
    require(snapshot.get('output_head_fingerprint') == binding['output_head_fingerprint'], 'OUTPUT_HEAD', 'Wrong head/tied state')
    require(snapshot.get('adapter_sha256') == binding['adapter_sha256'], 'STALE_ADAPTER', 'Adapter identity mismatch')
    validate_tensor_records(binding['parent_tensor_specs'], snapshot.get('parent_tensors', []),
                            binding['parent_storage_files'], snapshot.get('parent_storage_files', []))
    validate_tensor_records(binding['adapter_tensor_specs'], snapshot.get('adapter_tensors', []),
                            binding['adapter_storage_files'], snapshot.get('adapter_storage_files', []))
    require(snapshot.get('model_training') is False and snapshot.get('grad_enabled') is False
            and snapshot.get('optimizer_restored') is False and snapshot.get('training_recompute_active') is False,
            'TRAINING_MODE', 'Frozen inference only; optimizer/trainer resume forbidden')
    require(snapshot.get('adapter_enabled') is True and snapshot.get('dropout_training') is False,
            'ADAPTER_DISABLED', 'Cannot fall back to a parent or retain training dropout')
    require(snapshot.get('transient_state_cleared') is True and snapshot.get('hook_registrations') == 0,
            'STALE_STATE', 'Leftover hooks or inference/recurrent state')
    require(type(snapshot.get('load_generation')) is int, 'STALE_STATE', 'Load generation missing')
    if previous_generation is not None:
        require(snapshot['load_generation'] > previous_generation, 'STALE_STATE', 'No new complete adapter overwrite')


def adapter_activity(output: dict, binding: dict) -> None:
    modules = {key.split('.adapter.')[0] for key in binding['adapter_tensor_specs']}
    calls = output.get('adapter_branch_calls', {})
    require(set(calls) == modules and all(type(v) is int and v > 0 for v in calls.values()),
            'ADAPTER_NOT_EXECUTED', 'Missing native wrapper branch execution; parameter presence is insufficient')


def validate_algebra_evidence(evidence: dict) -> None:
    """Check an observed tiny native-branch trace against independent matrix arithmetic.

    This validator is exercised with synthetic unit data, not used to label a
    guessed native route equivalent. It never constructs a substitute adapter.
    """
    x = np.asarray(evidence['normalized_input'], dtype=np.float64)
    a, b = np.asarray(evidence['linear_in'], dtype=np.float64), np.asarray(evidence['linear_out'], dtype=np.float64)
    expected_branch = (x @ a.T) @ b.T * (evidence['alpha'] / evidence['rank'])
    expected = np.asarray(evidence['base_without_bias']) + np.asarray(evidence['bias']) + expected_branch
    require(evidence.get('eval_mode') is True and evidence.get('dropout_applied') is False,
            'ADAPTER_ALGEBRA', 'Eval dropout must be disabled')
    require(numeric_comparison(evidence['branch_output'], expected_branch, 'native_branch_algebra', atol=1e-12, rtol=1e-12)['pass'],
            'ADAPTER_ALGEBRA', 'Scale or normalized-input mismatch')
    require(numeric_comparison(evidence['combined_with_bias'], expected, 'native_branch_bias', atol=1e-12, rtol=1e-12)['pass'],
            'ADAPTER_ALGEBRA', 'Bias duplication or incorrect branch addition')
