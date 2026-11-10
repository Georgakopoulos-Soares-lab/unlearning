"""Independently audit sealed all-layer features, saved heads, metrics and resamples."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import joblib
import numpy as np
from threadpoolctl import threadpool_limits
from scripts.sayyed.multiretain_independent import metrics, reconstruct
from scripts.sayyed.multiretain_support import atomic_json


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--group', choices=['H3', 'other_five'], required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--original-root', default='/workspace/meeting-artifacts/multiretain-layers-v1')
    parser.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    if not 1 <= args.threads <= 4:
        raise ValueError('Audit CPU thread budget must be between1 and4')
    root, original, out = Path(args.run), Path(args.original_root), Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    started, cpu = time.monotonic(), time.process_time()
    manifest_path = root / 'manifests' / (args.group+'.jsonl')
    manifest = [json.loads(x) for x in manifest_path.read_text().splitlines()]
    protocol_path = root / 'PROTOCOL_V2.json'
    protocol = json.loads(protocol_path.read_text())
    probe_root = root / 'probes' / args.group
    index_path = probe_root / 'PROBE_INDEX.json'
    index = json.loads(index_path.read_text())
    fit_done = json.loads((probe_root / 'FIT_COMPLETE.json').read_text())
    if fit_done['status'] != 'COMPLETE' or len(index['units']) != index['expected_units']:
        raise ValueError('Fitting group is not complete')
    if fit_done['index_sha256'] != sha(index_path):
        raise ValueError('Final producer index changed')
    if (fit_done['identity_sha256'] != sha(probe_root / 'run_identity.json')
            or fit_done['protocol_sha256'] != sha(protocol_path)):
        raise ValueError('Final fitting identity/protocol mismatch')
    if len({(u['task'], u['layer'], u['cv_seed']) for u in index['units']}) != len(index['units']):
        raise ValueError('Duplicate scientific units')
    expected_keys = {(task,layer,seed) for task in {r['task'] for r in manifest}
                     for layer in [f'decoder_layer_{i}' for i in range(25)]+['final_norm']
                     for seed in protocol['probe']['cv_seeds']}
    if {(u['task'],u['layer'],u['cv_seed']) for u in index['units']} != expected_keys:
        raise ValueError('Missing or unexpected task/layer/seed conditions')

    def resolve(path):
        p = Path(path)
        return root / p.relative_to(original) if p.is_relative_to(original) else p

    def receipt(path):
        value = json.loads(path.read_text())
        if value['status'] not in ['COMPLETE', 'NEW']:
            raise ValueError('Producer unit is not complete: '+str(path))
        for entry in value['files']:
            target = resolve(entry['path'])
            if target.stat().st_size != entry['bytes'] or sha(target) != entry['sha256']:
                raise ValueError('Producer payload changed: '+str(target))
        return value

    def features(arm):
        folder = root / 'features' / args.group / arm
        complete = receipt(folder / 'FEATURE_UNIT_COMPLETE.json')
        identity = json.loads((folder / 'identity.json').read_text())
        key = identity['cache_key']
        raw_identity = {k:v for k,v in identity.items() if k != 'cache_key'}
        if hashlib.sha256(json.dumps(raw_identity, sort_keys=True).encode()).hexdigest() != key:
            raise ValueError('Feature identity is not self-consistent')
        if identity['manifest_sha256'] != sha(manifest_path):
            raise ValueError('Feature manifest hash mismatch')
        chunks = sorted(folder.glob('chunk_*.npz'))
        listed = {resolve(f['path']) for f in complete['files'] if Path(f['path']).name.startswith('chunk_')}
        if set(chunks) != listed:
            raise ValueError('Sealed chunk coverage differs from directory')
        pieces, cursor = [], 0
        for path in chunks:
            with np.load(path, allow_pickle=False) as saved:
                if saved['cache_key'].item() != key:
                    raise ValueError('Chunk cache key mismatch')
                count = len(saved['ids'])
                expected = manifest[cursor:cursor+count]
                for field, values in [('ids',[r['id'] for r in expected]),
                                      ('labels',[r['label'] for r in expected]),
                                      ('split',[r['split'] for r in expected]),
                                      ('task',[r['task'] for r in expected]),
                                      ('groups',[r['exact_rc_group'] for r in expected]),
                                      ('lengths',[len(r['sequence']) for r in expected]),
                                      ('sequence_sha256',[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in expected])]:
                    if saved[field].tolist() != values:
                        raise ValueError('Independent feature association mismatch: '+field)
                if saved['n_tokens'].tolist() != [len(r['sequence'])-1 for r in expected]:
                    raise ValueError('Independent target-count mismatch')
                pieces.append({k:saved[k] for k in saved.files if k != 'cache_key'})
                cursor += count
        if cursor != len(manifest) or complete['examples'] != cursor:
            raise ValueError('Feature population mismatch')
        value = {key:np.concatenate([x[key] for x in pieces]) for key in pieces[0]}
        for layer in [f'decoder_layer_{i}' for i in range(25)]+['final_norm']:
            if value[layer].shape != (cursor,1920) or value[layer].dtype != np.float32 or not np.isfinite(value[layer]).all():
                raise ValueError('Pooled layer shape, precision or finiteness mismatch')
        if value['nll_sum'].shape != (cursor,) or not np.isfinite(value['nll_sum']).all() or np.any(value['nll_sum'] < 0):
            raise ValueError('Invalid saved causal loss sums')
        return value

    base, post = features('base'), features('maxent')
    task_array = np.array([r['task'] for r in manifest])
    checked, metrics_count, contrasts_count, prediction_rows = [], 0, 0, 0
    max_probability_delta, max_metric_delta, max_bootstrap_delta = 0., 0., 0.
    resampling_cache = {}

    def resampling(task, split, indices):
        key = task, split
        if key in resampling_cache:
            return resampling_cache[key]
        path = probe_root / task / (split+'_resampling.npz')
        with np.load(path, allow_pickle=False) as saved:
            expected_names = np.array(sorted(set(base['groups'][indices].tolist())))
            group_map = {name:i for i,name in enumerate(expected_names)}
            inverse = np.array([group_map[name] for name in base['groups'][indices]])
            expected_draws = np.random.default_rng(protocol['bootstrap']['seed']).integers(
                len(expected_names), size=(protocol['bootstrap']['resamples'], len(expected_names)), dtype=np.int32)
            if (not np.array_equal(saved['ids'], base['ids'][indices])
                    or not np.array_equal(saved['group_names'], expected_names)
                    or not np.array_equal(saved['row_groups'], inverse)
                    or not np.array_equal(saved['group_draws'], expected_draws)):
                raise ValueError('Independent bootstrap seed/group/ID mismatch')
        group_weights = np.zeros((len(expected_draws),len(expected_names)), dtype=np.float64)
        np.add.at(group_weights, (np.repeat(np.arange(len(expected_draws)),len(expected_names)),expected_draws.ravel()), 1)
        weights = group_weights[:, inverse]
        resampling_cache[key] = weights
        return weights

    for entry in index['units']:
        unit_receipt_path = resolve(entry['receipt'])
        if sha(unit_receipt_path) != entry['receipt_sha256']:
            raise ValueError('Scientific unit receipt changed')
        done = receipt(unit_receipt_path)
        unit = unit_receipt_path.parent
        task, layer, seed = entry['task'], entry['layer'], entry['cv_seed']
        result = json.loads((unit / 'results.json').read_text())
        if (done['fit_identity_sha256'] != sha(probe_root / 'run_identity.json')
                or done['protocol_sha256'] != sha(protocol_path)):
            raise ValueError('Scientific unit input/protocol mismatch')
        names = ['auroc','accuracy','balanced_accuracy','average_precision','classification_cross_entropy']
        expected_metrics = {(split,policy,name) for split in done['splits']
                            for policy in ['base_refit','h3_only_refit','h3_only_fixed_base'] for name in names}
        actual_metrics = [(x['split'],x['policy'],x['metric']) for x in result['metrics']]
        if set(actual_metrics) != expected_metrics or len(actual_metrics) != len(expected_metrics):
            raise ValueError('Missing or duplicate scalar metric conditions')
        expected_contrasts = {(split,policy,name) for split in done['splits']
                             for policy in ['h3_only_refit','h3_only_fixed_base'] for name in names}
        actual_contrasts = [(x['split'],x['policy'],x['metric']) for x in result['contrasts']]
        if set(actual_contrasts) != expected_contrasts or len(actual_contrasts) != len(expected_contrasts):
            raise ValueError('Missing or duplicate paired contrast conditions')
        train = np.flatnonzero((task_array == task) & (base['split'] == 'train'))
        train_ids = set(base['ids'][train].tolist())
        fold_path = probe_root / task / ('folds_seed'+str(seed)+'.json')
        folds = json.loads(fold_path.read_text())
        if sha(fold_path) != result['fold_sha256'] or len(folds) != (3 if task == 'emp_H3' else 5):
            raise ValueError('Fold identity/count mismatch')
        by_id = {r['id']:r for r in manifest}
        validation_ids = []
        for fold in folds:
            a, b = set(fold['train_ids']), set(fold['validation_ids'])
            if a & b or a | b != train_ids:
                raise ValueError('Fold membership leaks or changes training population')
            if {by_id[x]['exact_rc_group'] for x in a} & {by_id[x]['exact_rc_group'] for x in b}:
                raise ValueError('Training fold group overlap')
            validation_ids.extend(fold['validation_ids'])
        if len(validation_ids) != len(train_ids) or set(validation_ids) != train_ids:
            raise ValueError('Validation folds do not partition training rows')
        models = {}
        for arm, arr in [('base',base),('h3_only_maxent',post)]:
            candidates = json.loads((unit / (arm+'_cv.json')).read_text())
            if [v['C'] for v in candidates] != [.1,1.,10.]:
                raise ValueError('CV grid changed')
            for candidate in candidates:
                if len(candidate['scores']) != len(folds) or abs(np.mean(candidate['scores'])-candidate['mean_auroc']) > 1e-14:
                    raise ValueError('CV candidate accounting mismatch')
                if any(fold[-1]['warnings'] for fold in candidate['convergence']):
                    raise ValueError('Unresolved CV warnings')
            selected = sorted(candidates,key=lambda c:(-c['mean_auroc'],c['C']))[0]['C']
            model = joblib.load(unit / (arm+'.joblib'))
            if not np.array_equal(model[-1].classes_,np.unique(base['labels'][train])):
                raise ValueError('Saved head class ordering mismatch')
            if any(not np.isfinite(v).all() for v in [model[-1].coef_,model[-1].intercept_,model[0].mean_,model[0].var_,model[0].scale_]):
                raise ValueError('Nonfinite saved head/scaler state')
            if model[-1].C != selected or result['fits'][arm]['selected_C'] != selected:
                raise ValueError('Selected C/tie-break mismatch')
            if (model[-1].solver != 'lbfgs' or model[-1].class_weight != 'balanced'
                    or model[-1].tol != 1e-4 or model[-1].penalty != 'l2'):
                raise ValueError('Classifier protocol changed')
            expected_mean = np.mean(arr[layer][train],axis=0,dtype=np.float64)
            if not np.allclose(model[0].mean_,expected_mean,atol=1e-12,rtol=1e-10):
                raise ValueError('Final scaler was not fitted on the declared training rows')
            expected_variance = np.var(arr[layer][train],axis=0,dtype=np.float64)
            if not np.allclose(model[0].var_,expected_variance,atol=1e-12,rtol=1e-9):
                raise ValueError('Final scaler variance differs from declared training rows')
            if result['fits'][arm]['convergence'][-1]['warnings']:
                raise ValueError('Unresolved final-fit warning')
            models[arm] = model
        local_prob_delta, local_metric_delta, local_boot_delta = 0., 0., 0.
        for split in done['splits']:
            ix = np.flatnonzero((task_array == task) & (base['split'] == split))
            weights = resampling(task,split,ix)
            all_weights = np.vstack([np.ones(len(ix)),weights])
            observed, sampled = {}, {}
            with np.load(unit / (split+'_predictions.npz'),allow_pickle=False) as predictions:
                for field, expected in [('ids',base['ids'][ix]),('labels',base['labels'][ix]),
                                        ('groups',base['groups'][ix]),('sequence_sha256',base['sequence_sha256'][ix])]:
                    if not np.array_equal(predictions[field],expected):
                        raise ValueError('Saved prediction association mismatch: '+field)
                classes = predictions['classes']
                if not np.array_equal(classes,np.unique(base['labels'][train])):
                    raise ValueError('Saved probability class order mismatch')
                for policy, arm, features_array in [('base_refit','base',base),
                    ('h3_only_refit','h3_only_maxent',post),('h3_only_fixed_base','base',post)]:
                    p = predictions['prob_'+policy]
                    with threadpool_limits(limits=args.threads):
                        reconstructed = reconstruct(models[arm],features_array[layer][ix])
                        probability_delta = float(np.max(np.abs(reconstructed-p)))
                        if probability_delta > 1e-10:
                            raise ValueError('Saved scaler/head probability reconstruction mismatch')
                        audited, valid = metrics(base['labels'][ix],p,classes,all_weights)
                    local_prob_delta = max(local_prob_delta,probability_delta)
                    observed[policy] = {k:float(v[0]) for k,v in audited.items()}
                    sampled[policy] = {k:v[1:] for k,v in audited.items()}
                    for row in [x for x in result['metrics'] if x['split'] == split and x['policy'] == policy]:
                        delta = abs(observed[policy][row['metric']]-row['value'])
                        if delta > 1e-12:
                            raise ValueError('Independent scalar metric mismatch: '+row['metric'])
                        local_metric_delta = max(local_metric_delta,delta)
                        metrics_count += 1
                    support = next(x for x in result['support'] if x['split'] == split and x['policy'] == policy)
                    guessed = classes[(p[:,1]>=.5).astype(int)] if len(classes) == 2 else classes[p.argmax(axis=1)]
                    confusion = [[int(np.sum((base['labels'][ix] == a) & (guessed == b))) for b in classes] for a in classes]
                    if confusion != support['confusion_counts'] or support['class_support'] != [int(np.sum(base['labels'][ix] == c)) for c in classes]:
                        raise ValueError('Independent class-support/confusion mismatch')
            with np.load(unit / (split+'_bootstrap.npz'),allow_pickle=False) as bootstrap:
                valid = np.all(np.array([weights[:,base['labels'][ix] == c].sum(axis=1) for c in classes]) > 0,axis=0)
                if not np.array_equal(bootstrap['valid'],valid):
                    raise ValueError('Invalid bootstrap draw accounting mismatch')
                for row in [x for x in result['contrasts'] if x['split'] == split]:
                    policy, metric = row['policy'], row['metric']
                    difference = sampled[policy][metric]-sampled['base_refit'][metric]
                    saved = bootstrap[policy+'__'+metric]
                    delta = float(np.max(np.abs(difference[valid]-saved[valid])))
                    lo,hi = np.quantile(difference[valid],[.025,.975])
                    if (delta > 1e-12 or abs(lo-row['ci_low']) > 1e-12 or abs(hi-row['ci_high']) > 1e-12
                            or abs(observed[policy][metric]-observed['base_refit'][metric]-row['difference']) > 1e-12
                            or row['valid'] != int(valid.sum()) or row['invalid'] != int((~valid).sum())):
                        raise ValueError('Independent paired bootstrap/contrast mismatch: '+metric)
                    local_boot_delta = max(local_boot_delta,delta)
                    contrasts_count += 1
            prediction_rows += len(ix)
        max_probability_delta = max(max_probability_delta,local_prob_delta)
        max_metric_delta = max(max_metric_delta,local_metric_delta)
        max_bootstrap_delta = max(max_bootstrap_delta,local_boot_delta)
        checked.append(dict(task=task,layer=layer,cv_seed=seed,producer_receipt_sha256=sha(unit_receipt_path),
                            max_probability_delta=local_prob_delta,max_metric_delta=local_metric_delta,
                            max_bootstrap_delta=local_boot_delta))
        atomic_json(out / 'progress.json',dict(verified_units=len(checked),total_units=index['expected_units'],
                    wall_seconds=time.monotonic()-started,cpu_process_seconds=time.process_time()-cpu))
        print('VERIFIED',task,layer,'seed',seed,len(checked),'/',index['expected_units'],flush=True)
    lm_checked = []
    for entry in index['lm_units']:
        path = resolve(entry['receipt'])
        if sha(path) != entry['receipt_sha256']:
            raise ValueError('LM receipt identity mismatch')
        receipt(path)
        data = json.loads((path.parent / 'lm_metrics.json').read_text())
        expected_by_split = {}
        for split in {v['split'] for v in data['metrics']}:
            ix = np.flatnonzero((task_array == entry['task']) & (base['split'] == split))
            weights = resampling(entry['task'],split,ix)
            point, sampled = {}, {}
            for arm, arr in [('base',base),('h3_only_maxent',post)]:
                summed = arr['nll_sum'][ix].astype(np.float64)
                counts = arr['n_tokens'][ix].astype(np.float64)
                nll = summed.sum()/counts.sum()
                point[arm] = dict(causal_nll=float(nll),perplexity=float(np.exp(nll)))
                boot_nll = (weights@summed)/(weights@counts)
                sampled[arm] = dict(causal_nll=boot_nll,perplexity=np.exp(boot_nll))
                recorded = next(v for v in data['metrics'] if v['split'] == split and v['arm'] == arm)
                if recorded['target_count'] != int(counts.sum()) or any(abs(point[arm][m]-recorded[m]) > 1e-12 for m in point[arm]):
                    raise ValueError('Independent LM support/aggregate mismatch')
            with np.load(path.parent / (split+'_lm_bootstrap.npz'),allow_pickle=False) as saved:
                for metric in ['causal_nll','perplexity']:
                    delta = sampled['h3_only_maxent'][metric]-sampled['base'][metric]
                    row = next(v for v in data['contrasts'] if v['split'] == split and v['metric'] == metric)
                    lo,hi = np.quantile(delta,[.025,.975])
                    if (np.max(np.abs(delta-saved[metric])) > 1e-12
                            or abs(lo-row['ci_low']) > 1e-12 or abs(hi-row['ci_high']) > 1e-12
                            or abs(point['h3_only_maxent'][metric]-point['base'][metric]-row['difference']) > 1e-12):
                        raise ValueError('Independent LM paired bootstrap mismatch')
                    lm_checked.append(dict(task=entry['task'],split=split,metric=metric))
    summary = dict(status='PASS',group=args.group,units=len(checked),scalar_probe_metrics=metrics_count,
                   paired_probe_contrasts=contrasts_count,prediction_rows=prediction_rows,
                   max_probability_delta=max_probability_delta,max_metric_delta=max_metric_delta,
                   max_bootstrap_delta=max_bootstrap_delta,units_checked=checked,lm_contrasts_checked=lm_checked,
                   scalar_lm_metrics=len(lm_checked)*2,
                   source_sha256=sha(__file__),independent_math_sha256=sha(Path(__file__).with_name('multiretain_independent.py')),
                   producer_index_sha256=sha(index_path),wall_seconds=time.monotonic()-started,
                   cpu_process_seconds=time.process_time()-cpu,
                   scope='Independent pairwise/rank-threshold metrics and all resamples; direct saved-head algebra, folds and source joins. No GPU replication or CV refitting.')
    atomic_json(out / 'VERIFICATION_COMPLETE.json',summary)
    print('Independent verification PASS:',args.group,len(checked),'units',metrics_count,'scalar metrics')


if __name__ == '__main__':
    main()
