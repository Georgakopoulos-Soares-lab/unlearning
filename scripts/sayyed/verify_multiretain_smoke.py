"""Compare training-only all-layer smokes against repeats, batches and old anchors."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from scripts.sayyed.fit_maxent_benign import arrays
from scripts.sayyed.multiretain_support import atomic_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    args = parser.parse_args()
    root = Path(args.run)
    plan = json.loads((root / 'SMOKE_PLAN.json').read_text())
    manifest = [json.loads(x) for x in Path(plan['manifest']).read_text().splitlines()]
    if any(x['split'] != 'train' for x in manifest):
        raise ValueError('Smoke must contain training rows only')
    checks = []
    started, cpu = time.monotonic(), time.process_time()

    def compare(name, reference, value, loss=False):
        tolerance = plan['nll_tolerance' if loss else 'pooling_tolerance']
        if reference.shape != value.shape or not np.isfinite(value).all():
            raise ValueError('Invalid shape or nonfinite smoke: ' + name)
        difference = float(np.max(np.abs(reference.astype(float) - value.astype(float))))
        if not np.allclose(reference, value, **tolerance):
            raise ValueError(f'Smoke mismatch {name}: max_abs={difference}')
        checks.append(dict(comparison=name, max_abs_difference=difference, tolerance=tolerance))

    for arm in ['base', 'maxent']:
        baseline, identity = arrays(root / 'smokes' / (arm + '-b8'), manifest)
        layers = [key for key in baseline if key.startswith('decoder_layer_')] + ['final_norm']
        if len(layers) != 26:
            raise ValueError('Missing all-layer coverage')
        for variant in ['b1', 'repeat']:
            value, other = arrays(root / 'smokes' / (arm + '-' + variant), manifest)
            for key in ['checkpoint_shards', 'config_sha256', 'tokenizer_sha256', 'hooks']:
                if identity[key] != other[key]:
                    raise ValueError('Smoke checkpoint/tokenizer/hook identity changed')
            for layer in layers:
                compare(arm + '/' + variant + '/' + layer, baseline[layer], value[layer])
            compare(arm + '/' + variant + '/nll_sum', baseline['nll_sum'], value['nll_sum'], True)
            if not np.array_equal(baseline['n_tokens'], value['n_tokens']):
                raise ValueError('Target count mismatch')
        anchors = {}
        for suffix in ['H3', 'promoter-splice', 'remaining']:
            historical = root / 'recovery-01/maxent-benign-v16' / (arm + '-' + suffix)
            historic_identity = json.loads((historical / 'identity.json').read_text())
            if historic_identity['checkpoint_shards'] != identity['checkpoint_shards']:
                raise ValueError('Historical checkpoint shard identity differs')
            for chunk in sorted(historical.glob('chunk_*.npz')):
                with np.load(chunk, allow_pickle=False) as data:
                    for index, row_id in enumerate(data['ids'].tolist()):
                        if row_id in baseline['ids']:
                            if str(data['split'][index]) != 'train':
                                raise ValueError('Historical anchor is not training data')
                            anchors[row_id] = {key: data[key][index] for key in
                                               ['decoder_layer_16', 'final_norm', 'nll_sum', 'n_tokens']}
        if set(anchors) != set(baseline['ids'].tolist()):
            raise ValueError('Historical anchor coverage incomplete')
        for key in ['decoder_layer_16', 'final_norm', 'nll_sum', 'n_tokens']:
            reference = np.stack([anchors[row_id][key] for row_id in baseline['ids']])
            compare(arm + '/historical/' + key, reference, baseline[key], key == 'nll_sum')
    result = dict(status='PASS', checks=checks, training_examples=len(manifest),
                  actual_blocks=25, representations=26, wall_seconds=time.monotonic()-started,
                  cpu_process_seconds=time.process_time()-cpu,
                  scope='Training-only output checks, not held-out performance or parent-lineage proof')
    atomic_json(root / 'SMOKE_VALIDATION.json', result)
    print('Training-only smoke validation passed:', len(checks), 'comparisons')


if __name__ == '__main__':
    main()
