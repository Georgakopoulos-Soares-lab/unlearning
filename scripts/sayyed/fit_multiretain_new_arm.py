"""All-layer grouped training-CV logistic probes with sealed producer units."""
import argparse
import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import shutil
import joblib
from joblib import Parallel, delayed, parallel_config
import resource
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold
from threadpoolctl import threadpool_limits
from scripts.sayyed.fit_maxent_benign import arrays
from scripts.sayyed.fit_maxent_extension import auc
from scripts.sayyed.h3_followup import train_model
from scripts.sayyed.multiretain_metrics import (METRICS, bootstrap_metrics, group_resampling,
                                               point_metrics)
from scripts.sayyed.multiretain_support import atomic_json


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save_npz(path, **values):
    temporary = path.with_name('.'+path.name+'.tmp.npz')
    np.savez_compressed(temporary, **values)
    temporary.replace(path)


def sealed_files(path, files, **metadata):
    result = dict(schema='multiretain-probe-unit-v1', status='COMPLETE', **metadata,
                  files=[dict(path=str(p.resolve()), bytes=p.stat().st_size, sha256=sha(p))
                         for p in files])
    atomic_json(path, result)
    return result


def verify_receipt(path):
    receipt = json.loads(path.read_text())
    if receipt['status'] not in ['COMPLETE', 'NEW']:
        raise ValueError('Incomplete producer receipt')
    for entry in receipt['files']:
        p = Path(entry['path'])
        if p.stat().st_size != entry['bytes'] or sha(p) != entry['sha256']:
            raise ValueError('Sealed file changed: '+str(p))
    return receipt


def reuse_base_head(original, unit):
    original = Path(original)
    unit = Path(unit)
    verify_receipt(original / 'COMPLETE.json')
    record = json.loads((original / 'results.json').read_text())
    paths = []
    for filename in ['base.joblib','base_cv.json']:
        shutil.copy2(original / filename, unit / filename)
        paths.append(unit / filename)
    return joblib.load(unit / 'base.joblib'), dict(record['fits']['base'], reused=True,
             source_receipt_sha256=sha(original / 'COMPLETE.json')), paths


def cv_fold(features, labels, train_indices, validation_indices, regularization, classes):
    """One independent fold, bounded to one BLAS thread in each worker."""
    started_cpu = time.process_time()
    with threadpool_limits(limits=1):
        model, attempts = train_model(features[train_indices], labels[train_indices], regularization)
        if attempts[-1]['warnings']:
            raise ValueError('Unresolved classifier warning')
        score = auc(labels[validation_indices], model.predict_proba(features[validation_indices]), classes)
    return score, attempts, time.process_time()-started_cpu


def main():
    started, cpu_started = time.monotonic(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ['base', 'post', 'manifest', 'protocol', 'output', 'shared', 'reference-probes']:
        parser.add_argument('--'+flag, required=True)
    args = parser.parse_args()
    out, shared = Path(args.output), Path(args.shared)
    out.mkdir(parents=True, exist_ok=True)
    protocol = json.loads(Path(args.protocol).read_text())
    protocol_hash = sha(args.protocol)
    rows = [json.loads(x) for x in Path(args.manifest).read_text().splitlines()]
    manifest_hash = sha(args.manifest)
    tasks = np.array([r['task'] for r in rows])
    task_order = [t for t in ['emp_H3', 'gue_prom_300_all', 'gue_splice_reconstructed',
                              'gue_prom_core_all', 'gue_tf_0', 'gue_mouse_0'] if t in tasks]
    if set(tasks) != set(task_order):
        raise ValueError('Task outside the six-task benign matrix')
    seeds = protocol['probe']['cv_seeds']
    if seeds != [42, 17, 1234] or protocol['probe']['C'] != [.1, 1, 10]:
        raise ValueError('Unexpected CV policy')
    for path in [Path(args.base), Path(args.post)]:
        verify_receipt(path / 'FEATURE_UNIT_COMPLETE.json')
    base, base_identity = arrays(args.base, rows)
    post, post_identity = arrays(args.post, rows)
    for value, identity in [(base, base_identity), (post, post_identity)]:
        if identity['manifest_sha256'] != manifest_hash or identity['physical_batch_size'] != 8:
            raise ValueError('Feature manifest or fixed physical batch mismatch')
        if value['groups'].tolist() != [r['exact_rc_group'] for r in rows]:
            raise ValueError('Feature group association mismatch')
        if value['task'].tolist() != tasks.tolist():
            raise ValueError('Feature task association mismatch')
        if value['lengths'].tolist() != [len(r['sequence']) for r in rows]:
            raise ValueError('Feature length association mismatch')
        if not np.array_equal(value['n_tokens'], value['lengths']-1):
            raise ValueError('LM target count mismatch')
    if base_identity['cache_key'] == post_identity['cache_key']:
        raise ValueError('Checkpoint cache collision')
    registry = json.loads((Path(args.base) / 'layer_registry.json').read_text())
    if registry != json.loads((Path(args.post) / 'layer_registry.json').read_text()):
        raise ValueError('Checkpoint layer registries disagree')
    layers = [r['array_key'] for r in registry]
    if layers != [f'decoder_layer_{i}' for i in range(25)] + ['final_norm']:
        raise ValueError('All-layer coverage mismatch')
    for layer in layers:
        for arr in [base, post]:
            if arr[layer].shape != (len(rows), 1920) or arr[layer].dtype != np.float32 or not np.isfinite(arr[layer]).all():
                raise ValueError('Invalid pooled features: '+layer)
    y, splits, groups = base['labels'], base['split'], base['groups']
    identity = dict(schema='multiretain-fit-v1', manifest_sha256=manifest_hash,
                    protocol_sha256=protocol_hash, base_cache_key=base_identity['cache_key'],
                    post_cache_key=post_identity['cache_key'], tasks=task_order, layers=layers,
                    seeds=seeds, source_sha256=sha(__file__),
                    metrics_source_sha256=sha(Path(__file__).with_name('multiretain_metrics.py')),
                    training_source_sha256=sha(Path(__file__).with_name('h3_followup.py')),
                    cv_parallelism=dict(workers=4,blas_threads_per_worker=1,final_refit_blas_threads=1),
                    packages={name: importlib.metadata.version(name) for name in
                              ['numpy', 'scipy', 'scikit-learn', 'joblib', 'threadpoolctl']})
    identity_path = out / 'run_identity.json'
    if identity_path.exists() and json.loads(identity_path.read_text()) != identity:
        raise ValueError('Fitting identity changed; use a new run/cache identity')
    atomic_json(identity_path, identity)
    atomic_json(out / ('invocation_'+str(time.time_ns())+'.json'),
                dict(actual_git_head=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                     started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     identity_sha256=sha(identity_path), argv=vars(args)))
    index_path = out / 'PROBE_INDEX.json'
    index = json.loads(index_path.read_text()) if index_path.exists() else dict(
        schema='multiretain-probe-index-v1', group=out.name, expected_units=len(task_order)*len(layers)*len(seeds), units=[])

    def publish(unit_path, receipt):
        entry = dict(task=receipt['task'], layer=receipt['layer'], cv_seed=receipt['cv_seed'],
                     status='COMPLETE', receipt=str(unit_path), receipt_sha256=sha(unit_path))
        index['units'] = [u for u in index['units'] if u['receipt'] != str(unit_path)] + [entry]
        index['completed_units'] = len(index['units'])
        index['wall_seconds_this_invocation'] = time.monotonic()-started
        index['cpu_process_seconds_this_invocation'] = time.process_time()-cpu_started
        atomic_json(index_path, index)
        atomic_json(shared / ('PROBE_INDEX_'+out.name+'.json'), index)
        producer_path = shared / 'PRODUCER_INDEX.json'
        producer = json.loads(producer_path.read_text()) if producer_path.exists() else dict(schema='multiretain-producer-index-v1', probe_groups={})
        producer['feature_index'] = str(shared / 'FEATURE_INDEX.json')
        producer['probe_groups'][out.name] = str(index_path)
        atomic_json(producer_path, producer)

    with parallel_config(backend='loky', n_jobs=4, inner_max_num_threads=1):
        parallel = Parallel(n_jobs=4, max_nbytes='1M', mmap_mode='r')
    with parallel:
        if parallel._backend.inner_max_num_threads != 1:
            raise RuntimeError('CV worker thread budget was not applied')
        worker_cpu_seconds = 0.
        for task in task_order:
            task_out = out / task
            task_out.mkdir(exist_ok=True)
            train = np.flatnonzero((tasks == task) & (splits == 'train'))
            heldout_splits = ['dev', 'test'] if task == 'emp_H3' else ['dev']
            expected_train = 11971 if task == 'emp_H3' else 1024
            if len(train) != expected_train:
                raise ValueError('Training population mismatch')
            classes = np.unique(y[train])
            heldout = {}
            for split in heldout_splits:
                ix = np.flatnonzero((tasks == task) & (splits == split))
                if len(ix) != (1497 if task == 'emp_H3' else 512) or set(groups[train]) & set(groups[ix]):
                    raise ValueError('Held-out population or group overlap mismatch')
                names, inverse, draws, weights = group_resampling(groups[ix], seed=protocol['bootstrap']['seed'],
                                                                repetitions=protocol['bootstrap']['resamples'])
                sample_path = task_out / (split+'_resampling.npz')
                if not sample_path.exists():
                    save_npz(sample_path, ids=base['ids'][ix], group_names=names, row_groups=inverse,
                             group_draws=draws, seed=np.array(protocol['bootstrap']['seed']))
                else:
                    with np.load(sample_path, allow_pickle=False) as saved:
                        if (not np.array_equal(saved['group_draws'], draws)
                                or not np.array_equal(saved['ids'], base['ids'][ix])
                                or not np.array_equal(saved['group_names'], names)
                                or not np.array_equal(saved['row_groups'], inverse)):
                            raise ValueError('Resampling identity mismatch')
                heldout[split] = (ix, weights, sample_path)
            # LM is one backbone readout, independent of layer/probe/CV seed.
            lm_path = task_out / 'LM_COMPLETE.json'
            if not lm_path.exists():
                lm_metrics, lm_contrasts, lm_files = [], [], []
                for split, (ix, weights, sample_path) in heldout.items():
                    values, sampled = {}, {}
                    for arm, arr in [('base', base), ('new_checkpoint', post)]:
                        sums = arr['nll_sum'][ix].astype(np.float64)
                        counts = arr['n_tokens'][ix].astype(np.float64)
                        if np.any(counts <= 0) or not np.isfinite(sums).all():
                            raise ValueError('Invalid causal loss sufficient statistics')
                        nll = float(sums.sum()/counts.sum())
                        values[arm] = dict(causal_nll=nll, perplexity=float(np.exp(nll)))
                        sampled_nll = (weights @ sums)/(weights @ counts)
                        sampled[arm] = dict(causal_nll=sampled_nll, perplexity=np.exp(sampled_nll))
                        lm_metrics.append(dict(task=task, split=split, arm=arm, n=len(ix),
                                               target_count=int(counts.sum()), **values[arm]))
                    distributions = {}
                    for metric in ['causal_nll', 'perplexity']:
                        delta = sampled['new_checkpoint'][metric]-sampled['base'][metric]
                        distributions[metric] = delta
                        lo, hi = np.quantile(delta, [.025, .975])
                        lm_contrasts.append(dict(task=task, split=split, metric=metric,
                                                 contrast='new_checkpoint_minus_base',
                                                 difference=values['new_checkpoint'][metric]-values['base'][metric],
                                                 ci_low=float(lo), ci_high=float(hi), valid=len(delta), invalid=0,
                                                 interpretation='paired conditional sequence/exact-RC-group bootstrap; no homology guarantee'))
                    target = task_out / (split+'_lm_bootstrap.npz')
                    save_npz(target, **distributions)
                    lm_files.extend([target, sample_path])
                target = task_out / 'lm_metrics.json'
                atomic_json(target, dict(metrics=lm_metrics, contrasts=lm_contrasts,
                                         definition='natural-log next-token loss sum / valid-target count; PPL=exp(corpus NLL)',
                                         layer='backbone only', precision='saved float32 sequence sums, float64 aggregation',
                                         population='exploratory reused splits; no additional truncation'))
                lm_files.append(target)
                sealed_files(lm_path, lm_files, task=task, protocol_sha256=protocol_hash, unit='causal_lm')
            else:
                verify_receipt(lm_path)
            index.setdefault('lm_units', [])
            index['lm_units'] = [u for u in index['lm_units'] if u['task'] != task] + [
                dict(task=task, status='COMPLETE', receipt=str(lm_path), receipt_sha256=sha(lm_path))]
            atomic_json(index_path, index)
            atomic_json(shared / ('PROBE_INDEX_'+out.name+'.json'), index)
            for seed in seeds:
                folds = list(StratifiedGroupKFold(n_splits=3 if task == 'emp_H3' else 5,
                                                 shuffle=True, random_state=seed).split(train, y[train], groups[train]))
                fold_path = task_out / ('folds_seed'+str(seed)+'.json')
                fold_records = [dict(train_ids=base['ids'][train[a]].tolist(),
                                     validation_ids=base['ids'][train[b]].tolist()) for a, b in folds]
                if json.loads((Path(args.reference_probes) / task / ('folds_seed'+str(seed)+'.json')).read_text()) != fold_records:
                    raise ValueError('Reference fold identity mismatch')
                if fold_path.exists() and json.loads(fold_path.read_text()) != fold_records:
                    raise ValueError('Training fold identity changed')
                if not fold_path.exists():
                    atomic_json(fold_path, fold_records)
                for layer in layers:
                    unit = task_out / layer / ('seed'+str(seed))
                    unit.mkdir(parents=True, exist_ok=True)
                    complete = unit / 'COMPLETE.json'
                    if complete.exists():
                        receipt = verify_receipt(complete)
                        if receipt['fit_identity_sha256'] != sha(identity_path):
                            raise ValueError('Completed fit belongs to different inputs/source')
                        publish(complete, receipt)
                        continue
                    begin, cpu_begin = time.monotonic(), time.process_time()
                    worker_cpu_begin = worker_cpu_seconds
                    files, models, fits = [fold_path], {}, {}
                    print('START', task, layer, 'CV seed', seed, flush=True)
                    for arm, arr in [('base', base), ('new_checkpoint', post)]:
                        if arm == 'base':
                            original = Path(args.reference_probes) / task / layer / ('seed'+str(seed))
                            models['base'], fits['base'], reused_paths = reuse_base_head(original, unit)
                            files.extend(reused_paths)
                            continue
                        candidates = []
                        with threadpool_limits(limits=1):
                            for regularization in [.1, 1., 10.]:
                                fold_results = parallel(delayed(cv_fold)(arr[layer], y, train[a], train[b], regularization, classes)
                                                        for a, b in folds)
                                scores = [value[0] for value in fold_results]
                                convergence = [value[1] for value in fold_results]
                                fold_cpu_seconds = sum(value[2] for value in fold_results)
                                worker_cpu_seconds += fold_cpu_seconds
                                candidates.append(dict(C=regularization, scores=scores,
                                                       mean_auroc=float(np.mean(scores)), convergence=convergence,
                                                       worker_cpu_process_seconds=fold_cpu_seconds))
                                atomic_json(unit / (arm+'_cv.json'), candidates)
                            selected = max(candidates, key=lambda x:(x['mean_auroc'], -x['C']))['C']
                            model, attempts = train_model(arr[layer][train], y[train], selected)
                            if attempts[-1]['warnings'] or not np.array_equal(model.classes_, classes):
                                raise ValueError('Final classifier warning or class ordering mismatch')
                        model_path = unit / (arm+'.joblib')
                        temporary = model_path.with_name('.'+model_path.name+'.tmp')
                        joblib.dump(model, temporary)
                        temporary.replace(model_path)
                        models[arm] = model
                        fits[arm] = dict(selected_C=selected, convergence=attempts,
                                         coefficient_dtype=str(model[-1].coef_.dtype),
                                         coefficient_shape=list(model[-1].coef_.shape),
                                         all_training_examples=len(train))
                        files.extend([model_path, unit / (arm+'_cv.json')])
                    metrics, contrasts, support = [], [], []
                    for split, (ix, weights, sample_path) in heldout.items():
                        with threadpool_limits(limits=1):
                            probabilities = dict(base_refit=models['base'].predict_proba(base[layer][ix]),
                                                 new_refit=models['new_checkpoint'].predict_proba(post[layer][ix]),
                                                 new_fixed_base=models['base'].predict_proba(post[layer][ix]))
                            with np.load(Path(args.reference_probes) / task / layer / ('seed'+str(seed)) / (split+'_predictions.npz'),allow_pickle=False) as prior:
                                if not np.array_equal(prior['ids'],base['ids'][ix]) or not np.array_equal(prior['classes'],classes):
                                    raise ValueError('Reused baseline prediction join mismatch')
                                if not np.allclose(probabilities['base_refit'],prior['prob_base_refit'],atol=1e-10,rtol=0):
                                    raise ValueError('Baseline head/cache compatibility mismatch')
                                probabilities['base_refit'] = prior['prob_base_refit'].copy()
                            observed, samples, valid_masks = {}, {}, {}
                            for policy, p in probabilities.items():
                                observed[policy], counts = point_metrics(y[ix], p, classes)
                                samples[policy], valid_masks[policy] = bootstrap_metrics(y[ix], p, classes, weights)
                                support.append(dict(task=task, layer=layer, cv_seed=seed, split=split, policy=policy, **counts))
                                metrics.extend(dict(task=task, layer=layer, cv_seed=seed, split=split,
                                                    policy=policy, metric=k, value=v, n=len(ix))
                                               for k, v in observed[policy].items())
                        distribution = {}
                        valid = valid_masks['base_refit']
                        for policy in ['new_refit', 'new_fixed_base']:
                            if not np.array_equal(valid, valid_masks[policy]):
                                raise ValueError('Paired bootstrap validity differs across models')
                            if not valid.any():
                                raise ValueError('No valid paired bootstrap draws')
                            for metric in METRICS:
                                delta = samples[policy][metric]-samples['base_refit'][metric]
                                distribution[policy+'__'+metric] = delta
                                lo, hi = np.quantile(delta[valid], [.025, .975])
                                contrasts.append(dict(task=task, layer=layer, cv_seed=seed, split=split,
                                                      policy=policy, metric=metric,
                                                      contrast='new_minus_base',
                                                      difference=observed[policy][metric]-observed['base_refit'][metric],
                                                      ci_low=float(lo), ci_high=float(hi), valid=int(valid.sum()),
                                                      invalid=int((~valid).sum()), invalid_reason='missing class in resample',
                                                      scope='pointwise unadjusted conditional on fitted heads; exact/RC groups only'))
                        predictions_path = unit / (split+'_predictions.npz')
                        save_npz(predictions_path, ids=base['ids'][ix], labels=y[ix], groups=groups[ix],
                                 sequence_sha256=base['sequence_sha256'][ix], classes=classes,
                                 **{'prob_'+key:value for key,value in probabilities.items()})
                        bootstrap_path = unit / (split+'_bootstrap.npz')
                        save_npz(bootstrap_path, valid=valid, **distribution)
                        files.extend([predictions_path, bootstrap_path, sample_path])
                    metadata_path = unit / 'results.json'
                    atomic_json(metadata_path, dict(metrics=metrics, contrasts=contrasts, support=support,
                                                    fits=fits, fold_sha256=sha(fold_path),
                                                    cv_seed_changes='StratifiedGroupKFold training partitions only; deterministic LBFGS optimizer seed42',
                                                    policy='fold-local StandardScaler; balanced L2; C=.1/1/10; smaller-C ties; all-training refit',
                                                    wall_seconds=time.monotonic()-begin,
                                                    cpu_process_seconds=time.process_time()-cpu_begin,
                                                    cv_worker_cpu_process_seconds=worker_cpu_seconds-worker_cpu_begin,
                                                    total_scientific_cpu_process_seconds=time.process_time()-cpu_begin+worker_cpu_seconds-worker_cpu_begin))
                    files.extend([metadata_path, identity_path])
                    receipt = sealed_files(complete, files, task=task, layer=layer, cv_seed=seed,
                                           policies=['base_refit', 'new_refit', 'new_fixed_base'],
                                           splits=heldout_splits, fit_identity_sha256=sha(identity_path),
                                           protocol_sha256=protocol_hash, unit='paired_logistic_probes')
                    publish(complete, receipt)
                    print('DONE', task, layer, 'CV seed', seed, 'seconds', round(time.monotonic()-begin, 3), flush=True)
    from joblib.externals.loky import get_reusable_executor
    get_reusable_executor().shutdown(wait=True)
    if len(index['units']) != index['expected_units']:
        raise ValueError('Incomplete task/layer/seed coverage')
    atomic_json(out / 'FIT_COMPLETE.json', dict(status='COMPLETE', units=len(index['units']),
                protocol_sha256=protocol_hash, identity_sha256=sha(identity_path), index_sha256=sha(index_path),
                wall_seconds_this_invocation=time.monotonic()-started,
                cpu_process_seconds_this_invocation=time.process_time()-cpu_started,
                cv_worker_cpu_process_seconds=worker_cpu_seconds,
                child_cpu_seconds_including_worker_setup=resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime+resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime,
                scope='Only new-arm CPU logistic fits; all base heads/CV/predictions reused; four independent one-thread CV workers, one-thread final refit; no backbone training'))


if __name__ == '__main__':
    main()
