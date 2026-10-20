"""Bounded original Evo2-1B inference pilot with independently runnable stages."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import random
import signal
import subprocess
import sys
import time
import traceback

import numpy as np
import torch

from .data import digest, prepare
from .metrics import aggregate, causal_nll, masked_pool
from .probes import fit_probes


def atomic(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False))
    temporary.replace(path)


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def guard(config):
    if git('branch', '--show-current') != 'experiments-ashay':
        raise RuntimeError('Only experiments-ashay may run this pilot')
    origin = git('remote', 'get-url', 'origin').removesuffix('.git')
    if origin not in ['https://github.com/Georgakopoulos-Soares-lab/unlearning', 'git@github.com:Georgakopoulos-Soares-lab/unlearning']:
        raise RuntimeError('Unexpected origin identity')
    if config['model_name'] != 'evo2_1b_base' or config['model_repo'] != 'arcinstitute/evo2_1b_base':
        raise ValueError('Original Evo2-1B only')
    if config['max_length'] != 512 or config['batch_size'] != 1:
        raise ValueError('Pilot uses the fixed maximum-512-prefix protocol at batch size 1')


def status(run, stage, **kwargs):
    value = dict(utc=datetime.now(timezone.utc).isoformat(), run_id=run.name, stage=stage,
                 task=None, samples_completed=0, failures=[], pid=os.getpid(), pgid=os.getpgrp(),
                 log_path=str(run / (stage + '.log')), next_action='inspect stage outputs', **{})
    value.update(kwargs)
    if stage in ['failed', 'interrupted'] and (run/'status.json').exists():
        previous = json.loads((run/'status.json').read_text())
        value.update({k: previous[k] for k in ['task','samples_completed','log_path']})
    if stage.endswith('_complete'):
        value['samples_completed'] = sum(sum(v['n_examples'] for v in json.loads(p.read_text())['nll'].values()) for p in run.glob('gue_*/complete.json'))
    atomic(run/'status.json', value)
    completed = sorted(p.parent.name for p in run.glob('gue_*/complete.json'))
    (run/'PROGRESS.md').write_text(f"Stage: {stage}\nUTC: {value['utc']}\nCompleted tasks: {completed}\nTask: {value['task']}\nSamples: {value['samples_completed']}\nFailures: {value['failures']}\n")
    (run/'RESUME.md').write_text(
        'Worktree: /workspace/wt-eval-pilot (experiments-ashay only).\n'
        'Python: /workspace/venvs/evo2-pilot/bin/python\n'
        f"Run: {run}\nPID: {os.getpid()} PGID: {os.getpgrp()} (verify process identity; do not trust PID alone).\n"
        f"Stage: {stage}; completed tasks: {completed}.\n"
        'Inspect status.json, stage logs, run_manifest.json, smoke_provenance.json and task completion keys before resuming.\n'
        f'Command: cd /workspace/wt-eval-pilot && bash scripts/run_benign_pilot.sh <stage> {run}\n'
        'User removed absolute clock deadlines; preserve the cumulative GPU-job budget ledger.\n'
        'Environment troubleshooting budget is cumulative: inspect environment_setup.md before any further installation.\n'
        'Downloads are already cached under /workspace/models and /workspace/data; do not redownload.\n'
        'Missing external audit/handoff files are a documented limitation. OFF-POD BACKUP PENDING.\n')


def sha_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def provenance(config, run, checkpoint):
    import evo2
    import vortex
    paths = list(Path('benign_pilot').glob('*.py')) + [Path('configs/benign_pilot.json'), Path('scripts/run_benign_pilot.sh')]
    config_text = json.dumps(config, sort_keys=True)
    value = dict(config=config, config_sha256=digest(config_text),
                 manifest_sha256=sha_file(run/'subset_manifest.jsonl'), source_commit=git('rev-parse', 'HEAD'),
                 source_hashes={str(p): sha_file(p) for p in paths}, checkpoint_sha256=sha_file(checkpoint),
                 packages={name: importlib.metadata.version(name) for name in ['torch','numpy','scikit-learn','evo2','vtx','transformer_engine','flash-attn']},
                 backend_files={str(p): sha_file(p) for root in [Path(evo2.__file__).parent, Path(vortex.__file__).parent] for p in root.rglob('*.py')},
                 python=sys.version, cuda=torch.version.cuda, cudnn=torch.backends.cudnn.version(),
                 device=torch.cuda.get_device_name(), compute_capability=torch.cuda.get_device_capability(),
                 seeds=dict(python=42, numpy=42, torch=42),
                 deterministic=dict(algorithms=torch.are_deterministic_algorithms_enabled(), cudnn_benchmark=torch.backends.cudnn.benchmark,
                                    cudnn_deterministic=torch.backends.cudnn.deterministic),
                 precision=config['precision'], pooling='mean of nucleotide positions, no BOS, padding excluded')
    atomic(run/'run_manifest.json', value)
    return value


def verify_checkpoint_tensors(expected, state, tied_embeddings):
    missing = [k for k, v in expected.items() if isinstance(v, torch.Tensor) and k not in state]
    extra = [k for k, v in state.items() if isinstance(v, torch.Tensor) and k not in expected]
    mismatch = [k for k in expected.keys() & state.keys() if isinstance(expected[k], torch.Tensor) and isinstance(state[k], torch.Tensor) and expected[k].shape != state[k].shape]
    aliases = {}
    if 'unembed.weight' in extra and tied_embeddings:
        source = state.get('embedding_layer.weight')
        if source is None or not torch.equal(source, state['unembed.weight']):
            raise ValueError('Extra output embedding is not an exact tied-weight alias')
        aliases['unembed.weight'] = 'embedding_layer.weight (bitwise equal checkpoint tensors)'
        extra.remove('unembed.weight')
    if missing or extra or mismatch:
        raise ValueError(f'Checkpoint tensor mismatch: missing={missing}, extra={extra}, shapes={mismatch}')
    return dict(tensor_missing=missing, tensor_extra=extra, shape_mismatch=mismatch, verified_aliases=aliases)


def load_model(config, run, checkpoint):
    from evo2 import Evo2
    import pkgutil
    import yaml
    recipe = yaml.safe_load(pkgutil.get_data('evo2', 'configs/evo2-1b-8k.yml'))
    if recipe['num_layers'] != 25 or recipe['hidden_size'] != 1920 or not recipe['use_fp8_input_projections']:
        raise ValueError('Unexpected original 1B architecture/precision')
    model = Evo2(config['model_name'], local_path=checkpoint)
    model.model.eval().requires_grad_(False)
    expected = model.model.state_dict()
    state = torch.load(checkpoint, map_location='cpu', mmap=True, weights_only=True)
    audit = verify_checkpoint_tensors(expected,state,recipe['tie_embeddings'])
    if model.tokenizer.tokenize('ACGTN') != list(b'ACGTN'):
        raise ValueError('Unexpected character tokenizer')
    for name in config['layers']:
        model.model.get_submodule(name)
    atomic(run/'model_contract.json', dict(config=recipe, config_sha256=digest(json.dumps(recipe, sort_keys=True)),
           parameter_count=sum(p.numel() for p in model.model.parameters()),
           parameter_shapes={k:list(p.shape) for k,p in model.model.named_parameters()},
           layers=config['layers'], indexing='zero-based block outputs: 8th and 16th of 25',
           **audit,
           extra_non_tensor_metadata=[k for k in state if k not in expected and not isinstance(state[k],torch.Tensor)],
           tokenizer='Vortex CharLevelTokenizer(512); ASCII bytes; pad=1/eos=0; no BOS/EOS added',
           dtype_counts=dict(__import__('collections').Counter(str(p.dtype) for p in model.model.parameters()))))
    del state
    return model


def infer(model, rows, layers):
    encoded = [model.tokenizer.tokenize(row['sequence']) for row in rows]
    # TE FP8 GEMMs require aligned dimensions; right padding never becomes a target.
    length = (max(map(len, encoded)) + 15) // 16 * 16
    tokens = torch.full((len(rows), length), model.tokenizer.pad_id, dtype=torch.long, device='cuda')
    mask = torch.zeros_like(tokens, dtype=torch.bool)
    for i, ids in enumerate(encoded):
        tokens[i,:len(ids)] = torch.tensor(ids, device='cuda')
        mask[i,:len(ids)] = True
    pooled, handles = {}, []
    def hook(name):
        def capture(module, inputs, output):
            hidden = output[0] if isinstance(output, tuple) else output
            pooled[name] = masked_pool(hidden, mask)
        return capture
    for name in layers:
        handles.append(model.model.get_submodule(name).register_forward_hook(hook(name)))
    try:
        with torch.inference_mode():
            output = model.model(tokens)
            while isinstance(output, (list, tuple)):
                output = output[0]
            sums, counts = causal_nll(output, tokens, mask, special_ids=(0, 1))
    finally:
        for handle in handles:
            handle.remove()
    if set(pooled) != set(layers):
        raise RuntimeError('Missing representation hooks')
    return [dict(id=row['id'], task=row['task'], split=row['split'], nll_sum=s, n_tokens=n) for row,s,n in zip(rows,sums,counts)], pooled


def smoke(config, run, model, rows):
    started = time.perf_counter()
    tiny = [dict(row, sequence=row['sequence'][:length]) for row,length in zip(rows[:4], [127, 256, 511, 300])]
    all_results = {}
    for size in [1, 2, 4, 1]:
        metrics = []
        for start in range(0, len(tiny), size):
            scores, _ = infer(model, tiny[start:start+size], config['layers'])
            metrics.extend(scores)
        key = str(size) if str(size) not in all_results else '1_repeat'
        all_results[key] = dict(per_example=metrics, **aggregate(metrics))
    baseline = all_results['1']
    for key, result in all_results.items():
        result['corpus_nll_difference_from_bs1'] = result['corpus_nll'] - baseline['corpus_nll']
        result['max_per_example_mean_nll_difference'] = max(abs(a['nll_sum']/a['n_tokens']-b['nll_sum']/b['n_tokens']) for a,b in zip(result['per_example'],baseline['per_example']))
    result = dict(batches=all_results, synthetic=False, inputs='First four fixed training manifest records, smoke-only prefix lengths 127/256/511/300',
                  interpretation='Measured numerical differences; no upstream numerical tolerance was established',
                  pilot_batch_size=1)
    atomic(run/'model_smoke_results.json', result)
    if all_results['1_repeat']['max_per_example_mean_nll_difference'] != 0:
        raise RuntimeError('Repeated batch-size-one smoke changed: numerical stability requires investigation')
    warmup_seconds = time.perf_counter() - started
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    timed_scores = []
    for row in rows[:32]:
        scores, _ = infer(model,[row],config['layers'])
        timed_scores.extend(scores)
    torch.cuda.synchronize()
    elapsed = time.perf_counter()-started
    result['throughput'] = dict(warmup_and_numerical_smoke_seconds=warmup_seconds, timed_examples=len(timed_scores),
        timed_seconds=elapsed, examples_per_second=len(timed_scores)/elapsed,
        scored_tokens_per_second=sum(r['n_tokens'] for r in timed_scores)/elapsed,
        peak_allocated_bytes=torch.cuda.max_memory_allocated(),batch_size=1,max_context=512,
        estimated_three_task_inference_seconds=len(rows)/len(timed_scores)*elapsed)
    atomic(run/'model_smoke_results.json',result)
    return result


def pilot(config, run, model, rows, context):
    for task in config['tasks']:
        selected = [row for row in rows if row['task'] == task]
        task_dir = run/task
        task_dir.mkdir(exist_ok=True)
        key = digest(json.dumps(dict(manifest=context['manifest_sha256'], config=context['config_sha256'],
                                   checkpoint=context['checkpoint_sha256'], source=context['source_hashes'], packages=context['packages'], backend=context['backend_files']), sort_keys=True))
        cache = task_dir/'features.npz'
        complete = task_dir/'complete.json'
        if complete.exists():
            if json.loads(complete.read_text())['cache_key'] != key:
                raise ValueError('Completion provenance mismatch')
            print(f'Reusing completed {task}', flush=True)
            continue
        scores, features = [], {name:[] for name in config['layers']}
        if cache.exists():
            saved = np.load(cache, allow_pickle=False)
            if saved['cache_key'].item() != key:
                raise ValueError('Feature provenance mismatch')
            scores = [json.loads(line) for line in (task_dir/'per_example_metrics.jsonl').read_text().splitlines()]
            for name in features:
                features[name] = [torch.from_numpy(saved[name])]
        else:
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats()
            started = time.perf_counter()
            with (task_dir/'per_example_metrics.partial.jsonl').open('w') as f:
                for i, row in enumerate(selected):
                    batch_scores, batch_features = infer(model, [row], config['layers'])
                    scores.extend(batch_scores)
                    for name in features:
                        features[name].append(batch_features[name])
                    f.write(json.dumps(batch_scores[0])+'\n')
                    f.flush()
                    if (i+1)%16 == 0 or i == 0:
                        status(run, 'pilot', task=task, samples_completed=i+1)
                        print(f'{task}: {i+1}/{len(selected)} samples; {time.perf_counter()-started:.1f}s', flush=True)
            torch.cuda.synchronize()
            elapsed = time.perf_counter()-started
            (task_dir/'per_example_metrics.partial.jsonl').rename(task_dir/'per_example_metrics.jsonl')
            np.savez_compressed(cache, cache_key=key, **{name:torch.cat(values).numpy() for name,values in features.items()})
            timing = dict(task=task, seconds=elapsed, examples_per_second=len(scores)/elapsed,
                          scored_tokens_per_second=sum(s['n_tokens'] for s in scores)/elapsed,
                          peak_allocated_bytes=torch.cuda.max_memory_allocated(), batch_size=1, max_context=512)
            atomic(task_dir/'throughput.json', timing)
        labels, splits = np.array([r['label'] for r in selected]), np.array([r['split'] for r in selected])
        probe_rows = []
        for name, values in features.items():
            candidates, best, scaler, classifier = fit_probes(torch.cat(values).numpy(), labels, splits)
            np.savez(task_dir/(name+'.probe.npz'), coef=classifier.coef_, intercept=classifier.intercept_, classes=classifier.classes_, mean=scaler.mean_, scale=scaler.scale_)
            for i, candidate in enumerate(candidates):
                probe_rows.append(dict(task=task, layer=name, **candidate, selected=i==best,
                                       train_count=int((splits=='train').sum()), validation_count=int((splits=='validation').sum())))
        atomic(task_dir/'probe_results.json', probe_rows)
        result = dict(task=task, cache_key=key, nll={s:aggregate([r for r in scores if r['split']==s]) for s in ['train','validation']},
                      probes=probe_rows, validation_selected=True)
        atomic(complete, result)
        report(config,run)
        print(json.dumps(result), flush=True)
        status(run, 'pilot', task=task, samples_completed=len(scores), next_action='next core task or report')


def report(config, run):
    results = [json.loads(p.read_text()) for p in run.glob('gue_*/complete.json')]
    lines = ['# Frozen original Evo2-1B GUE pilot', '', 'Validation-selected engineering evidence; no forgetting or retention claims.', '',
             '| Task | Layer | Selected C | Validation AUROC | Validation corpus NLL |', '|---|---|---:|---:|---:|']
    csv_rows, metrics, timings = [], [], []
    for result in results:
        for row in result['probes']:
            csv_rows.append(row)
            if row['selected']:
                lines.append(f"| {result['task']} | {row['layer']} | {row['C']} | {row['validation_auroc']:.6f} | {result['nll']['validation']['corpus_nll']:.6f} |")
        task_dir = run/result['task']
        metrics.extend((task_dir/'per_example_metrics.jsonl').read_text().splitlines())
        timings.append(json.loads((task_dir/'throughput.json').read_text()))
    for name, content in [('baseline_probe_results.csv',csv_rows), ('throughput_memory.csv',timings)]:
        if content:
            with (run/name).open('w') as f:
                writer=csv.DictWriter(f, fieldnames=list(content[0]), lineterminator='\n')
                writer.writeheader()
                writer.writerows(content)
    (run/'per_example_metrics.jsonl').write_text('\n'.join(metrics)+ ('\n' if metrics else ''))
    lines += ['', '## Execution status', f'Completed tasks: {len(results)}/{len(config["tasks"])}.',
              'Missing task measurements: NOT RUN or interrupted; inspect status.json and stage logs.',
              'Protocol: stratified seed 42, up to 256 train / 128 official dev; max 512 nucleotide prefix, no BOS; first nucleotide has no causal target.',
              'Two zero-based block outputs (7,15), mean over nucleotide positions; scaler and balanced logistic probes fit on train only; C selected on dev AUROC, ties favor lower C.',
              'Exact/RC overlap checks cover selected records only, not homology or forget/retain overlap. See data_provenance.json.',
              'No test contents were opened or scored. No backbone weights were trained.',
              'OFF-POD BACKUP PENDING. Verify the recovery download before stopping the Pod; experiment timeouts do not stop rental billing.', '']
    (run/'SUMMARY.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['preflight','prepare','smoke','pilot','report'])
    parser.add_argument('--config', default='configs/benign_pilot.json')
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--archive', default='/workspace/data/gue/GUE.zip')
    parser.add_argument('--checkpoint', default='/workspace/models/evo2_1b_base/evo2_1b_base.pt')
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    guard(config)
    run = Path(args.run_dir)
    run.mkdir(parents=True, exist_ok=True)
    saved_config=run/'config.json'
    if saved_config.exists() and json.loads(saved_config.read_text()) != config:
        previous = json.loads(saved_config.read_text())
        operational = {'experiment_cutoff_utc','gpu_budget_seconds'}
        if {k:v for k,v in previous.items() if k not in operational} != {k:v for k,v in config.items() if k not in operational}:
            raise ValueError('Saved scientific configuration mismatch; use a new run directory')
        atomic(run/'config_before_deadline_update.json',previous)
        atomic(run/'runtime_policy_change.json',dict(reason='User explicitly removed clock deadlines; cumulative budgets unchanged',previous=previous,current=config))
    atomic(saved_config, config)
    status(run,args.stage)
    def interrupted(signum, frame):
        raise InterruptedError(f'Signal {signum}; partial files preserved')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        random.seed(42); np.random.seed(42); torch.manual_seed(42)
        torch.backends.cudnn.benchmark = False
        if args.stage == 'preflight':
            with (run/'evaluator_test_results.txt').open('w') as log:
                subprocess.run([sys.executable,'-m','pytest','tests/test_benign_pilot.py','-q'],stdout=log,stderr=subprocess.STDOUT,check=True)
        elif args.stage == 'prepare':
            if config.get('data_archive_sha256') and sha_file(args.archive) != config['data_archive_sha256']:
                raise ValueError('Official GUE archive hash mismatch')
            atomic(run/'data_preparation.json', prepare(config,args.archive,run))
        elif args.stage == 'report':
            report(config,run)
        else:
            rows = [json.loads(line) for line in (run/'subset_manifest.jsonl').read_text().splitlines()]
            context = provenance(config, run, args.checkpoint)
            started=time.perf_counter()
            model=load_model(config,run,args.checkpoint)
            atomic(run/'model_load_timing.json',dict(seconds=time.perf_counter()-started))
            if args.stage == 'smoke':
                smoke(config,run,model,rows)
                atomic(run/'smoke_provenance.json', context)
            else:
                smoke_path=run/'model_smoke_results.json'
                if not smoke_path.exists():
                    raise RuntimeError('Complete smoke stage first')
                previous = json.loads((run/'smoke_provenance.json').read_text())
                for key in ['manifest_sha256','config_sha256','checkpoint_sha256','source_hashes','packages','backend_files']:
                    if previous[key] != context[key]:
                        raise ValueError(f'Smoke provenance mismatch: {key}')
                pilot(config,run,model,rows,context)
                report(config,run)
        status(run,args.stage+'_complete')
    except BaseException as exc:
        status(run,'failed' if not isinstance(exc,(InterruptedError,TimeoutError)) else 'interrupted', failures=[repr(exc)], next_action='inspect log and retained partial outputs')
        (run/'BLOCKERS.md').write_text(f'{args.stage}: {type(exc).__name__}: {exc}\n')
        traceback.print_exc()
        raise


if __name__ == '__main__':
    main()
