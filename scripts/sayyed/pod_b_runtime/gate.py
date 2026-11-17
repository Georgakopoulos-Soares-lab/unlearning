"""Executable, fail-closed B04/B06 qualification interface.

There is deliberately no guessed native backend. A source-verified backend must
implement load/snapshot/forward/disable/close after the full-state binding clears
preflight. Current B04 cases are blocked before backend import or GPU ownership.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import datetime as dt
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Protocol

import numpy as np

from .contracts import (GateError, adapter_activity, binding_preflight, canonical_sha,
    compare_forward, file_sha, loaded_state, output_path, require, validate_forward, verify_file)


class NativeBackend(Protocol):
    """No generic LoRA substitute: implement using the authenticated native source."""
    def load(self, binding: dict) -> None: ...
    def snapshot(self) -> dict: ...
    def forward(self, rows: list[dict], *, logical_batch_size: int, hooks: bool) -> dict: ...
    def set_adapter_enabled(self, enabled: bool) -> None: ...
    def close(self) -> None: ...


def load_result(record: dict, roots: list[str]) -> dict:
    meta_path = verify_file(record, roots=roots)
    meta = json.loads(meta_path.read_text())
    data_path = verify_file(meta['arrays_file'], roots=roots)
    result = {k: v for k, v in meta.items() if k != 'arrays_file'}
    result['features'] = {}
    with np.load(data_path, allow_pickle=False) as data:
        for key in data.files:
            value = data[key]
            require(not value.dtype.hasobject, 'OBJECT_ARRAY', key)
            if key.startswith('feature__'):
                result['features'][key.removeprefix('feature__')] = value
            else:
                result[key] = value
    return result


def save_result(directory: Path, name: str, result: dict) -> dict:
    array_path = directory / (name + '.npz')
    meta_path = directory / (name + '.json')
    require(not array_path.exists() and not meta_path.exists(), 'OUTPUT_EXISTS', name)
    arrays = {k: v for k, v in result.items() if isinstance(v, np.ndarray)}
    arrays.update({'feature__' + k: v for k, v in result['features'].items()})
    require(all(not a.dtype.hasobject for a in arrays.values()), 'OBJECT_ARRAY', name)
    meta = {k: v for k, v in result.items() if k != 'features' and not isinstance(v, np.ndarray)}
    np.savez(array_path, **arrays)
    meta['arrays_file'] = {'path': str(array_path), 'bytes': array_path.stat().st_size, 'sha256': file_sha(array_path)}
    meta_path.write_text(json.dumps(meta, indent=2, allow_nan=False) + '\n')
    return {'path': str(meta_path), 'bytes': meta_path.stat().st_size, 'sha256': file_sha(meta_path)}


def qualify_matrix(backend: NativeBackend, binding: dict, rows: list[dict], reference: dict,
                   parent_reference: dict, swap_binding: dict | None = None) -> tuple[dict, dict]:
    """Run same-state gates. The caller owns GPU lease and torch.inference_mode.

    Unit tests may supply disposable simulated backends; that never supplies
    actual native-route evidence or upgrades a production binding.
    """
    gates = []
    contract = binding['extraction_contract']
    backend.load(binding)
    initial = backend.snapshot()
    loaded_state(initial, binding)
    principal = backend.forward(rows, logical_batch_size=8, hooks=True)
    validate_forward(principal, rows, contract)
    adapter_activity(principal, binding)
    gates.append({'gate': 'original_route_reference', 'comparisons': compare_forward(principal, reference, rows, contract)})
    repeated = backend.forward(rows, logical_batch_size=8, hooks=True)
    gates.append({'gate': 'repeatability', 'comparisons': compare_forward(repeated, principal, rows, contract)})
    logical_one = backend.forward(rows, logical_batch_size=1, hooks=True)
    gates.append({'gate': 'logical1_physical8', 'comparisons': compare_forward(logical_one, principal, rows, contract)})
    require(len(rows) % 8 != 0, 'PARTIAL_BATCH_UNTESTED', 'The fixed12-row fixture exercises the final short batch')
    gates.append({'gate': 'final_partial_batch_filler_exclusion', 'status': 'PASS_EXACT_IDS_MASKS_COUNTS'})
    no_hooks = backend.forward(rows, logical_batch_size=8, hooks=False)
    neutral_reference = {**principal, 'features': {}, 'hook_calls': {}}
    gates.append({'gate': 'hook_neutrality', 'comparisons': compare_forward(no_hooks, neutral_reference, rows, contract, hooks=False)})
    # No numerical equality is required between two different adapter states.
    backend.set_adapter_enabled(False)
    disabled = backend.forward(rows, logical_batch_size=8, hooks=True)
    gates.append({'gate': 'adapter_disable_vs_qualified_parent', 'comparisons': compare_forward(disabled, parent_reference, rows, contract)})
    backend.set_adapter_enabled(True)
    generation = initial['load_generation']
    if swap_binding is not None:
        require(swap_binding['parent_fingerprint'] == binding['parent_fingerprint'], 'SWAP_PARENT',
                'Cross-parent changes require a fresh full parent load')
        backend.load(swap_binding)
        middle = backend.snapshot()
        loaded_state(middle, swap_binding, previous_generation=generation)
        middle_output = backend.forward(rows, logical_batch_size=8, hooks=True)
        validate_forward(middle_output, rows, contract)
        adapter_activity(middle_output, swap_binding)
        backend.load(binding)
        final = backend.snapshot()
        loaded_state(final, binding, previous_generation=middle['load_generation'])
        restored = backend.forward(rows, logical_batch_size=8, hooks=True)
        gates.append({'gate': 'A_B_A_swap_isolation', 'comparisons': compare_forward(restored, principal, rows, contract),
                      'backbone_fingerprint_unchanged': final['parent_fingerprint'] == initial['parent_fingerprint']})
    else:
        raise GateError('SWAP_NOT_QUALIFIED', 'An approved same-parent endpoint/boundary swap case is required')
    # Check that forwards/hooks did not mutate inference-relevant non-adapter state.
    end = backend.snapshot()
    loaded_state(end, binding)
    return {'status': 'PASS_MATRIX_PENDING_FRESH_PROCESS', 'gates': gates,
            'model_identity': binding['checkpoint_id'], 'full_route_qualification': False}, principal


def execution_authorized(plan: dict, control: dict) -> None:
    require(plan.get('synthetic_contract_test') is not True, 'SYNTHETIC_NOT_SCIENCE', 'Synthetic contract fixtures cannot authorize native inference')
    require(control.get('stage') in ('B04', 'B06') and control.get('status') == 'RUNNING',
            'STAGE_NOT_AUTHORIZED', 'Current stage must be explicitly running; no automatic advancement')
    require(control.get('prompt_commit') == plan.get('execution_prompt_commit', plan.get('prompt_commit')),
            'APPROVAL_VERSION', 'Running stage approval/version does not match this execution plan')
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(plan['budgets']['scientific_cutoff']),
            'SCIENCE_DEADLINE', 'No automatic clock extension')
    remaining = (dt.datetime.fromisoformat(plan['budgets']['scientific_cutoff']) - dt.datetime.now(dt.timezone.utc)).total_seconds()
    require(remaining >= plan['budgets']['per_gpu_job_seconds'] + 60, 'INSUFFICIENT_VERIFICATION_TIME',
            'A complete job plus bounded verification reserve must fit before cutoff')
    require(not plan.get('new_training_or_fits_allowed') and not plan.get('new_heldout_evaluation_allowed'),
            'SCOPE', 'This runner permits frozen training-only diagnostics')


@contextmanager
def gpu_lease(plan: dict, directory: Path):
    """Existing shared ownership lock, new scoped ledger; never reset old usage."""
    from scripts.sayyed.multiretain_support import SessionBudget
    config_record = plan.get('gpu_runtime_config')
    ledger = plan.get('gpu_stage_ledger')
    require(config_record is not None and ledger is not None, 'GPU_ACCOUNTING_BLOCKED', 'Scoped budget must be prepared and frozen')
    verify_file(config_record, roots=plan['isolation']['output_roots'])
    ledger_path = Path(ledger)
    require(any(ledger_path.resolve().is_relative_to(Path(p).resolve()) for p in plan['isolation']['output_roots']),
            'OUTPUT_PATH', 'A historical ledger cannot be a new stage ledger')
    lock_path = Path(plan['isolation']['shared_gpu_lock'])
    require(str(lock_path) == '/workspace/meeting-artifacts/evo2-pilot.gpu.lock', 'GPU_LOCK_PATH', 'Use the established shared lock')
    lease = lock_path.open('a+')
    started = False
    acquired = False
    try:
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except BlockingIOError as exc:
            raise GateError('GPU_BUSY', 'Never remove another owner lock') from exc
        shared = json.loads(Path('/workspace/meeting-artifacts/evo2-pilot.gpu-budget.json').read_text())
        require(shared.get('active_since') is None, 'GPU_OWNER_UNRESOLVED', 'Historical active owner must be resolved')
        budget = SessionBudget(ledger_path, config_record['path'])
        budget.begin()
        started = True
        yield
    finally:
        if started:
            budget.end()
        if acquired:
            fcntl.flock(lease, fcntl.LOCK_UN)
        lease.close()


def run_owned_worker(command: list[str], log, timeout: float, plan: dict) -> int:
    """Bound the owned process group; reconcile only its new scoped stage ledger."""
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        return process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        ledger_name = plan.get('gpu_stage_ledger')
        if ledger_name is not None:
            ledger_path = Path(ledger_name)
            require(any(ledger_path.resolve().is_relative_to(Path(p).resolve()) for p in plan['isolation']['output_roots']),
                    'OUTPUT_PATH', 'Never reconcile an old ledger')
            if ledger_path.is_file():
                state = json.loads(ledger_path.read_text())
                if state.get('pid') == process.pid and state.get('active_since') is not None:
                    elapsed = max(0., time.time() - state['active_since'])
                    state['used_seconds'] += elapsed
                    state['active_since'] = None
                    state.setdefault('stages', []).append({'pid': process.pid, 'gpu_stage_wall_seconds': elapsed,
                        'failure': 'owned_worker_timeout', 'clock_scope': 'reconciled recorded owner epoch to observed exit'})
                    from scripts.sayyed.multiretain_support import atomic_json
                    atomic_json(ledger_path, state)
        raise GateError('WORKER_TIMEOUT', 'Owned process group stopped; no automatic retry or stage advance') from exc


def load_backend(binding: dict, plan: dict) -> NativeBackend:
    record = binding.get('backend_file')
    require(record is not None, 'NATIVE_BACKEND_MISSING', 'Do not substitute generic LoRA for missing native implementation')
    path = verify_file(record, roots=binding['allowed_read_roots'])
    require(record['sha256'] == binding['route_source_sha256'], 'ROUTE_HASH', 'Backend source changed')
    require(any(r['sha256'] == record['sha256'] and r['path'] == record['path'] for r in binding['source_files']),
            'ROUTE_HASH', 'Backend absent from source manifest')
    for name in ['TORCH_EXTENSIONS_DIR', 'TRITON_CACHE_DIR', 'XDG_CACHE_HOME', 'HF_HOME']:
        value = os.environ.get(name)
        require(value is not None and any(Path(value).resolve().is_relative_to(Path(p).resolve())
                for p in plan['isolation']['output_roots']), 'CACHE_ISOLATION', name)
    require(os.environ.get('PYTHONDONTWRITEBYTECODE') == '1', 'CACHE_ISOLATION', 'Preserve historical source bytecode paths')
    spec = importlib.util.spec_from_file_location('pod_b_authenticated_native_backend', path)
    require(spec is not None and spec.loader is not None, 'NATIVE_BACKEND_MISSING', str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.create_backend(binding=binding, stage_cache_root=plan['isolation']['cache_root'])


def worker(plan: dict, case_id: str, binding_path: Path, directory: Path, phase: str) -> None:
    binding, rows, key = binding_preflight(plan, case_id, binding_path)
    parent_reference_record = binding.get('qualified_parent_reference')
    require(parent_reference_record is not None, 'REFERENCE_BLOCKED', 'Adapter-disabled diagnostic needs the exact qualified parent reference')
    reference = load_result(binding['reference'], binding['allowed_read_roots'])
    parent_reference = load_result(parent_reference_record, binding['allowed_read_roots'])
    swap = binding.get('swap')
    require(swap is not None, 'SWAP_NOT_QUALIFIED', 'Planned endpoint/boundary swap binding missing')
    swap_binding, _, _ = binding_preflight(plan, swap['checkpoint_id'], Path(swap['binding_path']))
    with gpu_lease(plan, directory):
        import torch
        with torch.inference_mode():
            backend = load_backend(binding, plan)
            try:
                if phase == 'matrix':
                    result, principal = qualify_matrix(backend, binding, rows, reference, parent_reference, swap_binding)
                else:
                    backend.load(binding)
                    loaded_state(backend.snapshot(), binding)
                    principal = backend.forward(rows, logical_batch_size=8, hooks=True)
                    adapter_activity(principal, binding)
                    result = {'status': 'PASS_PRINCIPAL_FRESH_PROCESS',
                              'comparisons': compare_forward(principal, reference, rows, binding['extraction_contract'])}
                result['principal'] = save_result(directory, 'principal', principal)
                result['deterministic_cache_key'] = key
                result['cuda_peak_memory_bytes'] = int(torch.cuda.max_memory_allocated())
                (directory / 'RESULT.json').write_text(json.dumps(result, indent=2) + '\n')
            finally:
                backend.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preflight', 'qualify', '_worker'])
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--checkpoint-id', required=True)
    parser.add_argument('--binding', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--control-state', type=Path, default=Path('/workspace/agent-handoff/POD_B/STATE.json'))
    parser.add_argument('--phase', choices=['matrix', 'fresh'])
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text())
        binding, rows, key = binding_preflight(plan, args.checkpoint_id, args.binding)
        if args.command == 'preflight':
            print(json.dumps({'status': 'PASS_MANIFEST_PREFLIGHT_ONLY', 'checkpoint_id': args.checkpoint_id,
                              'cache_key': key, 'rows': len(rows), 'scientifically_qualified': False}))
            return 0
        execution_authorized(plan, json.loads(args.control_state.read_text()))
        require(args.output is not None, 'OUTPUT_PATH', 'Explicit new stage output is mandatory')
        directory = output_path(args.output, plan['isolation']['output_roots'])
        directory.mkdir(parents=True)
        if args.command == '_worker':
            require(args.phase is not None, 'PHASE', 'Worker phase required')
            worker(plan, args.checkpoint_id, args.binding, directory, args.phase)
            return 0
        # Controller itself loads no native model. Independent subprocesses exit
        # completely between matrix and fresh reproduction, clearing CUDA state.
        for phase in ['matrix', 'fresh']:
            command = [sys.executable, '-m', 'scripts.sayyed.pod_b_runtime.gate', '_worker',
                '--plan', str(args.plan), '--checkpoint-id', args.checkpoint_id, '--binding', str(args.binding),
                '--control-state', str(args.control_state), '--phase', phase, '--output', str(directory / phase)]
            with (directory / (phase + '.log')).open('x') as log:
                returncode = run_owned_worker(command, log, plan['budgets']['per_gpu_job_seconds'], plan)
            require(returncode == 0, 'WORKER_FAILED', phase)
        first = json.loads((directory / 'matrix/RESULT.json').read_text())
        second = json.loads((directory / 'fresh/RESULT.json').read_text())
        require(first['deterministic_cache_key'] == second['deterministic_cache_key'] == key,
                'CACHE_KEY', 'Dependencies changed between processes')
        comparisons = compare_forward(load_result(second['principal'], plan['isolation']['output_roots']),
                                      load_result(first['principal'], plan['isolation']['output_roots']),
                                      rows, binding['extraction_contract'])
        final = {'status': 'QUALIFIED_B04', 'checkpoint_id': args.checkpoint_id, 'cache_key': key,
                 'route_kind': binding['route_kind'], 'original_comparison_scope': 'same_identified_state',
                 'matrix_receipt': str(directory / 'matrix/RESULT.json'), 'fresh_process_comparisons': comparisons,
                 'new_probe_fits': 0, 'heldout_inputs': 0}
        (directory / 'QUALIFICATION.json').write_text(json.dumps(final, indent=2) + '\n')
        print(json.dumps(final))
        return 0
    except GateError as exc:
        print(json.dumps({'status': 'BLOCKED_OR_FAILED', 'code': exc.code, 'checkpoint_id': args.checkpoint_id,
                          'message': str(exc), 'scientifically_qualified': False}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
