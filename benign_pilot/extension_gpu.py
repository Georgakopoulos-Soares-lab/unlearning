"""Serialized, budgeted frozen extraction with immutable per-task identity arrays."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

import numpy as np
import torch

from . import budget
from .data import digest, eligibility_for_run
from .extension import write
from .identity import checkpoint_identity, backend_identity
from .metrics import aggregate
from .run import infer, load_model

RUN=Path('/workspace/meeting-artifacts/evo2-extension-20261021T0942')
CHECKPOINT='/workspace/models/evo2_1b_base/evo2_1b_base.pt'
OLD=Path('/workspace/meeting-artifacts/evo2-20261020T1437')


def main():
    branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
    if branch!='experiments-ashay-benign-v2':raise ValueError('Extension branch required')
    config=json.loads((RUN/'config.json').read_text())
    rows=[json.loads(l) for l in (RUN/'subset_manifest.jsonl').read_text().splitlines()]
    eligible=eligibility_for_run(config,RUN,rows);write(RUN/'eligibility.json',eligible)
    source={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*Path('benign_pilot').glob('*.py'),Path('configs/benign_extension.json'),Path('configs/evo2_backend_identity.json')]}
    identity=dict(checkpoint_sha256=checkpoint_identity(CHECKPOINT),backend=backend_identity(),source_hashes=source,
        execution_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),manifest_sha256=hashlib.sha256((RUN/'subset_manifest.jsonl').read_bytes()).hexdigest(),config=config,
        final_representation='norm output: final RMSNorm after blocks.24 and before tied unembedding; mean all nucleotide positions, excluding right-padding; distinct from blocks.24 output and vocabulary logits',
        tokenizer='ASCII CharLevelTokenizer(512), no BOS/EOS, pad1/eos0 excluded targets',batch_size=1)
    previous=RUN/'extraction_identity.json'
    if previous.exists() and json.loads(previous.read_text())!=identity:raise ValueError('Extraction identity mismatch')
    write(previous,identity);key=digest(json.dumps(identity,sort_keys=True))
    with open('/workspace/meeting-artifacts/evo2-pilot.gpu.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads(budget.BUDGET_PATH.read_text())
        if state.get('active_since'):raise RuntimeError('Ledger indicates another active/interrupted stage; reconcile before begin')
        remaining=budget.update('begin')
        def stop(*args):raise TimeoutError('GPU stage interrupted/budget exhausted; saved completed tasks preserved')
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGALRM,stop);signal.alarm(remaining)
        try:
            model=load_model(config,RUN,CHECKPOINT)
            oldrows=[json.loads(l) for l in (OLD/'subset_manifest.jsonl').read_text().splitlines()]
            anchors=[]
            # One original train and dev row per historical task; exact saved identity/order.
            for task in dict.fromkeys(r['task'] for r in oldrows):
                selected=[r for r in oldrows if r['task']==task];saved=np.load(OLD/task/'features.npz',allow_pickle=False)
                losses={r['id']:r for r in map(json.loads,(OLD/task/'per_example_metrics.jsonl').read_text().splitlines())}
                for split in ['train','validation']:
                    i=next(i for i,r in enumerate(selected) if r['split']==split);row=selected[i]
                    scores,features=infer(model,[row],config['layers']);ref=losses[row['id']]
                    nll_delta=abs(scores[0]['nll_sum']/scores[0]['n_tokens']-ref['nll_sum']/ref['n_tokens'])
                    feature_checks={}
                    for layer in ['blocks.7','blocks.15']:
                        actual=features[layer].numpy()[0];expected=saved[layer][i]
                        feature_checks[layer]=dict(max_abs=float(np.max(np.abs(actual-expected))),passed=bool(np.allclose(actual,expected,atol=1e-4,rtol=1e-3)))
                    anchors.append(dict(id=row['id'],split=split,nll_abs_delta=nll_delta,features=feature_checks,passed=nll_delta<=1e-5 and all(v['passed'] for v in feature_checks.values())))
            write(RUN/'anchor.json',dict(tolerances=dict(nll_absolute=1e-5,feature_atol=1e-4,feature_rtol=1e-3),anchors=anchors,all_passed=all(r['passed'] for r in anchors)))
            if not all(r['passed'] for r in anchors):raise RuntimeError('Historical anchor discrepancies; expanded extraction blocked pending explanation')
            smoke_rows=[r for r in rows if eligible[r['task']]['eligible']][:32]
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
            for row in smoke_rows:infer(model,[row],config['layers'])
            torch.cuda.synchronize();elapsed=time.perf_counter()-started
            n=sum(eligible[r['task']]['eligible'] for r in rows)
            estimate=n/len(smoke_rows)*elapsed
            write(RUN/'expanded_smoke.json',dict(examples=len(smoke_rows),seconds=elapsed,estimated_extraction_seconds=estimate,peak_allocated_bytes=torch.cuda.max_memory_allocated(),target_examples=n))
            if estimate+600>remaining-(time.perf_counter()-stage_start):raise RuntimeError('Expanded target does not fit remaining GPU budget; choose smaller common target before dev inspection')
            for task in config['tasks']:
                if not eligible[task]['eligible']:print('BLOCKED',task,flush=True);continue
                out=RUN/task;out.mkdir(exist_ok=True)
                if (out/'extraction_complete.json').exists():
                    if json.loads((out/'extraction_complete.json').read_text())['cache_key']!=key:raise ValueError('Cache identity mismatch')
                    continue
                selected=[r for r in rows if r['task']==task];features={k:[] for k in config['layers']};scores=[];started=time.perf_counter()
                with (out/'per_example_metrics.partial.jsonl').open('w') as log:
                    for i,row in enumerate(selected):
                        score,feature=infer(model,[row],config['layers']);scores.extend(score)
                        for k in features:features[k].append(feature[k].numpy())
                        log.write(json.dumps(score[0])+'\n');log.flush()
                        if i%128==0:print(task,i+1,'/',len(selected),flush=True)
                np.savez_compressed(out/'features.npz',ids=np.array([r['id'] for r in selected]),labels=np.array([r['label'] for r in selected]),split=np.array([r['split'] for r in selected]),sequence_sha256=np.array([r['scored_prefix_sha256'] for r in selected]),extraction_identity=json.dumps(identity,sort_keys=True),cache_key=key,**{k:np.concatenate(v) for k,v in features.items()})
                (out/'per_example_metrics.partial.jsonl').rename(out/'per_example_metrics.jsonl')
                write(out/'extraction_complete.json',dict(status='NEW_GPU_COMPLETE',cache_key=key,seconds=time.perf_counter()-started,nll={s:aggregate([r for r in scores if r['split']==s]) for s in ['train','validation']},examples=len(selected)))
                print('COMPLETE',task,flush=True)
        finally:
            signal.alarm(0);budget.update('finish')

stage_start=time.perf_counter()
if __name__=='__main__':main()
