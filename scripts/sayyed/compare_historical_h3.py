"""Describe numerical agreement on reused historical H3 rows; no GPU work."""
import json
from pathlib import Path
import numpy as np

RUN=Path('/workspace/meeting-artifacts/sayyed-base-20261026-v1')
OLD=Path('/workspace/recovery/sayyed-20261026-extracted/evo2-extension-20261021T0942-supplement/evo2-extension-20261021T0942')


def main():
    if not (RUN/'extraction_complete.json').exists():raise ValueError('Extraction incomplete')
    historical=[json.loads(x) for x in (OLD/'subset_manifest.jsonl').read_text().splitlines()]
    historical={r['id']:r for r in historical if r['task']=='gue_emp_h3'}
    losses={r['id']:r for r in map(json.loads,(OLD/'gue_emp_h3/per_example_metrics.jsonl').read_text().splitlines())}
    with np.load(OLD/'gue_emp_h3/features.npz',allow_pickle=False) as old:
        features=old['norm'];ids=old['ids']
        reference={historical[str(oid)]['full_sequence_sha256']:(features[i],losses[str(oid)]) for i,oid in enumerate(ids)}
    max_feature=0.;max_nll=0.;count=0;exact_features=0;exact_losses=0
    for path in sorted((RUN/'chunks').glob('*.npz')):
        with np.load(path,allow_pickle=False) as a:
            for i,digest in enumerate(a['sequence_sha256']):
                if str(digest) not in reference:continue
                features,loss=reference[str(digest)]
                max_feature=max(max_feature,float(np.max(np.abs(features-a['features'][i]))))
                max_nll=max(max_nll,abs(float(a['nll_sum'][i])/int(a['n_tokens'][i])-loss['nll_sum']/loss['n_tokens']))
                exact_features+=int(np.array_equal(features,a['features'][i]))
                exact_losses+=int(float(a['nll_sum'][i])==loss['nll_sum'] and int(a['n_tokens'][i])==loss['n_tokens'])
                count+=1
    assert count==1536
    result=dict(matched_rows=count,exact_feature_rows=exact_features,exact_loss_rows=exact_losses,
        max_abs_feature_difference=max_feature,max_abs_per_row_mean_nll_difference=max_nll,
        limitation='Descriptive reused-row numerical comparison across recovered historical and new inference; not independent benchmark replication')
    (RUN/'historical_numerical_comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
