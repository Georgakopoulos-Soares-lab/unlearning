"""Lossless reporting tables from fully audited, immutable probe units."""
import argparse
import csv
import json
from pathlib import Path


def write(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True, type=Path)
    args = parser.parse_args()
    root = args.run
    metrics, differences = [], []
    native_metrics, native_differences = [], []
    for group, expected in [('H3', 78), ('other_five', 390)]:
        audit = json.loads((root/'producer_audit'/group/'VERIFICATION_COMPLETE.json').read_text())
        if audit['status'] != 'PASS':
            raise ValueError('Full group audit required')
        units = sorted((root/'probes'/group).glob('*/*/seed*/results.json'))
        if len(units) != expected:
            raise ValueError('Incomplete matrix')
        for path in units:
            if not (path.parent/'COMPLETE.json').exists():
                raise ValueError('Unsealed unit')
            data = json.loads(path.read_text())
            for kind, target in [('metrics', metrics), ('contrasts', differences)]:
                for row in data[kind]:
                    (native_metrics if kind == 'metrics' else native_differences).append(row)
                    policy = row['policy']
                    base = policy == 'base_refit'
                    layer = row['layer'].replace('decoder_layer_', 'decoder.layers.')
                    if layer in {'decoder_final_norm', 'final_norm'}:
                        layer = 'decoder.final_norm'
                    out = dict(task=row['task'], split=row['split'],
                               checkpoint='base' if base else 'h3_only_maxent',
                               checkpoint_role='base' if base else 'h3_only',
                               layer=layer, seed=row['cv_seed'],
                               probe_policy='fixed_base_scaler_and_head' if policy.endswith('fixed_base') else 'independent_refit',
                               metric=row['metric'])
                    if kind == 'metrics':
                        out['value'] = row['value']
                    else:
                        out.update({key: row[key] for key in ['difference', 'ci_low', 'ci_high']})
                    out.update(status='completed', missing_reason='')
                    target.append(out)
                    if base:
                        target.append(dict(out, probe_policy='fixed_base_scaler_and_head'))
    # Explicit absent arm, with blank values rather than invented zero scores.
    absent = [dict(row, checkpoint='multi_retain', checkpoint_role='multi_retain',
                   value='', status='blocked', missing_reason='Checkpoint not identified')
              for row in metrics if row['checkpoint'] == 'base']
    metrics.extend(absent)
    output = root/'reports'
    output.mkdir(exist_ok=True)
    write(output/'metrics.csv', metrics)
    write(output/'differences.csv', differences)
    write(output/'native_metrics.csv', native_metrics)
    write(output/'native_contrasts.csv', native_differences)
    (output/'AGGREGATION.json').write_text(json.dumps(dict(
        status='COMPLETE', native_metric_rows=len(native_metrics),
        native_contrast_rows=len(native_differences),
        reporting_metric_rows=len(metrics), reporting_difference_rows=len(differences),
        base_fixed_policy='Alias of identical base refit predictions; no additional fit',
        missing_arms='Multi-retain deferred/not identified; no noise checkpoint supplied',
        inference='All exploratory; pointwise conditional intervals, no multiplicity adjustment',
    ), indent=2))


if __name__ == '__main__':
    main()
