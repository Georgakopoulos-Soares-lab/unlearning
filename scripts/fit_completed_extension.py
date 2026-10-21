"""Fit each completed extraction once; called after GPU extraction or per-task."""
import argparse,json
from pathlib import Path
import numpy as np
from benign_pilot.extension import evaluate

p=argparse.ArgumentParser();p.add_argument('--task');a=p.parse_args()
run=Path('/workspace/meeting-artifacts/evo2-extension-20261021T0942');config=json.loads((run/'config.json').read_text());rows=[json.loads(l) for l in (run/'subset_manifest.jsonl').read_text().splitlines()]
for task in ([a.task] if a.task else config['tasks']):
    out=run/'expanded_matched'/task
    if (out/'contrasts.json').exists() and (out/'predictions.jsonl').exists():
        print('PRESERVED',task,flush=True);continue
    if not (run/task/'extraction_complete.json').exists():
        print('NOT_READY',task,flush=True);continue
    selected=[r for r in rows if r['task']==task];saved=np.load(run/task/'features.npz',allow_pickle=False)
    if saved['ids'].tolist()!=[r['id'] for r in selected] or saved['labels'].tolist()!=[r['label'] for r in selected] or saved['sequence_sha256'].tolist()!=[r['scored_prefix_sha256'] for r in selected] or saved['split'].tolist()!=[r['split'] for r in selected]:raise ValueError('Feature identities do not align')
    evaluate(selected,{k:saved[k] for k in config['layers']},out)
