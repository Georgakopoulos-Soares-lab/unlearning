"""Publish lossless, role-labelled consumer views of sealed producer probe units."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from scripts.sayyed.fit_multiretain_layers import verify_receipt, sha, save_npz
from scripts.sayyed.multiretain_support import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',required=True)
    parser.add_argument('--group',choices=['H3','other_five'],required=True)
    parser.add_argument('--shared',required=True)
    args = parser.parse_args()
    root, shared = Path(args.run), Path(args.shared)
    out = root / 'consumer_views' / args.group
    out.mkdir(parents=True,exist_ok=True)
    source_manifest_path = root / 'manifests' / (args.group+'.jsonl')
    source_manifest = [json.loads(x) for x in source_manifest_path.read_text().splitlines()]
    scientific_protocol = root / 'PROTOCOL_V2.json'
    protocol = json.loads(scientific_protocol.read_text())
    identity = dict(schema='multiretain-consumer-view-v1',source_sha256=sha(__file__),
                    scientific_protocol_sha256=sha(scientific_protocol),
                    source_manifest_sha256=sha(source_manifest_path),adaptation='Lossless serialization/identity views only; no fitting or inference')
    ip = out / 'view_identity.json'
    if ip.exists() and json.loads(ip.read_text()) != identity:
        raise ValueError('Consumer-view implementation changed; use a new view identity')
    if not ip.exists():
        atomic_json(ip,identity)
    task_manifests = {}
    for task in sorted({r['task'] for r in source_manifest}):
        path = out / (task+'_manifest.jsonl')
        if not path.exists():
            rows = []
            for row in source_manifest:
                if row['task'] == task:
                    row = dict(row)
                    row['sequence_sha256'] = hashlib.sha256(row['sequence'].encode()).hexdigest()
                    rows.append(row)
            temporary = path.with_name('.'+path.name+'.tmp')
            temporary.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows))
            temporary.replace(path)
        task_manifests[task] = path
    source_index = root / 'probes' / args.group / 'PROBE_INDEX.json'
    index = json.loads(source_index.read_text())
    views = []
    for entry in index['units']:
        source_receipt = Path(entry['receipt'])
        if sha(source_receipt) != entry['receipt_sha256']:
            raise ValueError('Source unit identity changed')
        receipt = verify_receipt(source_receipt)
        source = source_receipt.parent
        results = json.loads((source / 'results.json').read_text())
        task, layer, seed = entry['task'],entry['layer'],entry['cv_seed']
        module = 'decoder.final_norm' if layer == 'final_norm' else 'decoder.layers.'+layer.rsplit('_',1)[-1]
        for split in receipt['splits']:
            folder = out / task / layer / ('seed'+str(seed)) / split
            folder.mkdir(parents=True,exist_ok=True)
            complete = folder / 'COMPLETE.json'
            if complete.exists():
                existing = verify_receipt(complete)
                if existing['source_receipt_sha256'] != sha(source_receipt):
                    raise ValueError('Consumer view belongs to changed producer unit')
                views.append(dict(task=task,split=split,layer=module,cv_seed=seed,receipt=str(complete),receipt_sha256=sha(complete)))
                continue
            manifest_path = task_manifests[task]
            view_protocol = folder / 'protocol.json'
            atomic_json(view_protocol,dict(manifest_sha256=sha(manifest_path),
                        scientific_protocol_sha256=sha(scientific_protocol),
                        bootstrap_seed=protocol['bootstrap']['seed'],bootstrap_resamples=protocol['bootstrap']['resamples'],
                        feature_dtype='float32',coefficient_dtype='float64',reconstruction_tolerance=1e-10,
                        adaptation='NPZ float64 probabilities to JSONL without arithmetic; canonical module names; AUROC-only bootstrap view for reviewer checker',
                        independent_head_verification='Producer pairwise auditor uses actual sklearn in-place dtype arithmetic; reviewer precast-mean/scale issue disclosed separately'))
            with np.load(source / (split+'_predictions.npz'),allow_pickle=False) as saved:
                predictions = [dict(task=task,split=split,id=str(saved['ids'][i]),label=int(saved['labels'][i]),
                                    group=str(saved['groups'][i]),sequence_sha256=str(saved['sequence_sha256'][i]),
                                    classes=saved['classes'].tolist(),probabilities={name:saved['prob_'+name][i].tolist()
                                    for name in ['base_refit','h3_only_refit','h3_only_fixed_base']})
                               for i in range(len(saved['ids']))]
            predictions_path = folder / 'predictions.jsonl'
            temporary = predictions_path.with_name('.predictions.jsonl.tmp')
            temporary.write_text(''.join(json.dumps(r)+'\n' for r in predictions))
            temporary.replace(predictions_path)
            metric_rows = [dict(model=r['policy'],task=task,split=split,layer=module,metric=r['metric'],value=r['value'])
                           for r in results['metrics'] if r['split'] == split]
            metrics_path = folder / 'metrics.csv'
            temporary = metrics_path.with_name('.metrics.csv.tmp')
            with temporary.open('w',newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=list(metric_rows[0]),lineterminator='\n')
                writer.writeheader();writer.writerows(metric_rows)
            temporary.replace(metrics_path)
            contrast_rows = [dict(task=task,split=split,layer=module,probe=r['policy'],metric='auroc',
                                  difference=r['difference'],ci_low=r['ci_low'],ci_high=r['ci_high'],rejected=r['invalid'])
                             for r in results['contrasts'] if r['split'] == split and r['metric'] == 'auroc']
            contrast_path = folder / 'contrasts.csv'
            temporary = contrast_path.with_name('.contrasts.csv.tmp')
            with temporary.open('w',newline='') as stream:
                writer = csv.DictWriter(stream,fieldnames=list(contrast_rows[0]),lineterminator='\n')
                writer.writeheader();writer.writerows(contrast_rows)
            temporary.replace(contrast_path)
            with np.load(source.parent.parent / (split+'_resampling.npz'),allow_pickle=False) as resampling:
                values = {key:resampling[key] for key in ['ids','group_names','row_groups','group_draws']}
            with np.load(source / (split+'_bootstrap.npz'),allow_pickle=False) as bootstrap:
                valid = bootstrap['valid']
                for policy in ['h3_only_refit','h3_only_fixed_base']:
                    values[policy] = bootstrap[policy+'__auroc'][valid]
            bootstrap_path = folder / 'bootstrap.npz'
            save_npz(bootstrap_path,**values)
            selection_paths = {}
            for arm in ['base','h3_only_maxent']:
                candidates = json.loads((source / (arm+'_cv.json')).read_text())
                selection_paths[arm] = folder / (arm+'_selection.json')
                atomic_json(selection_paths[arm],dict(selected_C=results['fits'][arm]['selected_C'],
                    candidates=[dict(**candidate,training_scope='train_only') for candidate in candidates],
                    source_cv_sha256=sha(source / (arm+'_cv.json'))))
            roles = dict(protocol=view_protocol,manifest=manifest_path,predictions=predictions_path,
                         metrics=metrics_path,contrasts=contrast_path,bootstrap=bootstrap_path,
                         folds=source.parent.parent / ('folds_seed'+str(seed)+'.json'),
                         selection=selection_paths['base'],post_selection=selection_paths['h3_only_maxent'],
                         producer_receipt=source_receipt,producer_results=source / 'results.json',
                         scientific_protocol=scientific_protocol,source_manifest=source_manifest_path,
                         base_model=source / 'base.joblib',post_model=source / 'h3_only_maxent.joblib')
            result = dict(schema='multiretain-unit-v1',status='COMPLETE',
                          unit=dict(task=task,split=split,checkpoint='base_and_h3_only_maxent',layer=module,
                                    seed=seed,probe_policy='independent_refit_and_fixed_base'),
                          baseline_probe='base_refit',source_receipt=str(source_receipt),
                          source_receipt_sha256=sha(source_receipt),new_measurement=False,
                          view_of_new_measurements=True,view_identity_sha256=sha(ip),
                          feature_dtype='float32',coefficient_dtype='float64',reconstruction_tolerance=1e-10,
                          linear_reconstruction_note='Audited separately with correct in-place float32 transforms; not opting into reviewer precast-mean/scale reconstruction',
                          reviewer_metric_limit='Reviewer checks AUROC/accuracy/balanced accuracy/CE and binary AP; full macro AP and every metric bootstrap checked by producer pairwise auditor',
                          files=[dict(role=role,path=str(path.resolve()),bytes=path.stat().st_size,sha256=sha(path)) for role,path in roles.items()])
            atomic_json(complete,result)
            views.append(dict(task=task,split=split,layer=module,cv_seed=seed,receipt=str(complete),receipt_sha256=sha(complete)))
    result = dict(schema='multiretain-consumer-index-v1',group=args.group,units=views,
                  source_index_sha256=sha(source_index),expected_units=index['expected_units']*(2 if args.group == 'H3' else 1),
                  status='COMPLETE' if len(index['units']) == index['expected_units'] else 'PARTIAL',
                  scope='Only finalized producer units adapted; no active files consumed')
    atomic_json(out / 'CONSUMER_INDEX.json',result)
    atomic_json(shared / ('CONSUMER_INDEX_'+args.group+'.json'),result)
    print('Published',len(views),'sealed consumer views for',args.group)


if __name__ == '__main__':
    main()
