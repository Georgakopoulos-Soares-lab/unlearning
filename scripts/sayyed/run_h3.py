"""Independent frozen H3 extraction and CPU MLP; no viral tasks supported."""
import argparse
from collections import Counter
import fcntl
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import signal
import subprocess
import time
import zipfile

import numpy as np
import torch
from sklearn.metrics import roc_auc_score, accuracy_score, balanced_accuracy_score, log_loss

from benign_pilot import budget
from benign_pilot.identity import checkpoint_identity, backend_identity
from benign_pilot.run import infer, load_model

RUN = Path('/workspace/meeting-artifacts/sayyed-base-20261026-v1')
ARCHIVE = Path('/workspace/data/sayyed-20261026/GUE_benchmark.zip')
CHECKPOINT = '/workspace/models/evo2_1b_base/evo2_1b_base.pt'


def sha(p):
    return hashlib.file_digest(Path(p).open('rb'), 'sha256').hexdigest()


def write(p, v):
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(v, indent=2, allow_nan=False) + '\n')
    tmp.replace(p)


def prepare():
    protocol = json.loads((RUN / 'protocol.json').read_text())
    assert protocol['task'] == 'GUE_benchmark/emp_H3'
    assert sha(ARCHIVE) == protocol['archive_sha256']
    destination = RUN / 'manifest.jsonl'
    if destination.exists():
        return [json.loads(line) for line in destination.read_text().splitlines()]
    rows, split_groups = [], {}
    with zipfile.ZipFile(ARCHIVE) as z:
        for split in ['train', 'dev', 'test']:
            member = f'GUE_benchmark/emp_H3/{split}.jsonl'
            groups = set()
            for i, row in enumerate(map(json.loads, z.read(member).splitlines())):
                sequence = ''.join(row['sequence'].upper().split())
                if set(sequence) - set('ACGTN') or int(row['label']) not in [0, 1]:
                    raise ValueError('Unexpected H3 schema')
                reverse = sequence.translate(str.maketrans('ACGTN', 'TGCAN'))[::-1]
                group = hashlib.sha256(min(sequence, reverse).encode()).hexdigest()
                groups.add(group)
                rows.append(dict(id=f'{protocol["archive_sha256"]}:{member}:{i}', task='emp_H3',
                    split=split, label=int(row['label']), sequence=sequence[:1000],
                    sequence_sha256=hashlib.sha256(sequence.encode()).hexdigest(), exact_rc_group=group))
            split_groups[split] = groups
    overlaps = {f'{a}:{b}':len(split_groups[a] & split_groups[b])
                for a,b in [('train','dev'),('train','test'),('dev','test')]}
    qualification = dict(protocol_sha256=sha(RUN/'protocol.json'), test_access='after protocol freeze; no results inspected',
        rows_by_split=dict(Counter(r['split'] for r in rows)), exact_rc_cross_split=overlaps,
        class_counts={s:dict(Counter(r['label'] for r in rows if r['split']==s)) for s in split_groups})
    write(RUN/'split_qualification.json', qualification)
    if any(overlaps.values()):
        raise ValueError('Cross-split sequence duplicates; protocol amendment required before evaluation')
    with destination.open('x') as f:
        for row in rows: f.write(json.dumps(row, sort_keys=True) + '\n')
    return rows


def extract():
    if subprocess.check_output(['git','branch','--show-current'],text=True).strip() != 'experiments-ashay-sayyed-base-v1':
        raise ValueError('Sayyed branch required')
    rows = prepare()
    checkpoint_identity(CHECKPOINT)
    backend = backend_identity()
    identity = dict(protocol_sha256=sha(RUN/'protocol.json'),manifest_sha256=sha(RUN/'manifest.jsonl'),
        checkpoint_sha256=sha(CHECKPOINT), backend=backend,
        revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_hashes={str(p):sha(p) for p in [Path(__file__),*Path('benign_pilot').glob('*.py')]},
        packages={n:importlib.metadata.version(n) for n in ['torch','numpy','evo2','vtx','transformer_engine','flash-attn']},
        device=torch.cuda.get_device_name(0),cuda=torch.version.cuda)
    key = hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    ip = RUN/'extraction_identity.json'
    if ip.exists() and json.loads(ip.read_text()) != identity:raise ValueError('Extraction identity changed; use new run')
    write(ip,identity)
    chunks=RUN/'chunks';chunks.mkdir(exist_ok=True)
    config=dict(model_name='evo2_1b_base',layers=['norm'])
    with open('/workspace/meeting-artifacts/evo2-pilot.gpu.lock','a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=json.loads(budget.BUDGET_PATH.read_text())
        if state.get('active_since'):raise ValueError('Unreconciled active GPU ledger')
        remaining=budget.update('begin'); started=time.perf_counter()
        def stop(*args):raise TimeoutError('GPU budget exhausted or interrupted')
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGALRM,stop)
        signal.alarm(remaining)
        try:
            model=load_model(config,RUN,CHECKPOINT)
            smoke_rows=[r for r in rows if r['split']=='train'][:32]
            torch.cuda.synchronize();smoke_start=time.perf_counter();torch.cuda.reset_peak_memory_stats()
            smoke_scores=[]
            for row in smoke_rows:
                scores,features=infer(model,[row],['norm'])
                if not torch.isfinite(features['norm']).all() or not all(math.isfinite(s['nll_sum']) for s in scores):raise ValueError('Nonfinite smoke')
                smoke_scores.extend(scores)
            torch.cuda.synchronize();elapsed=time.perf_counter()-smoke_start
            estimate=len(rows)*elapsed/len(smoke_rows)
            write(RUN/'smoke.json',dict(training_examples=32,seconds=elapsed,estimated_full_extraction_seconds=estimate,
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),stage_loading_and_smoke_seconds=time.perf_counter()-started,
                remaining_seconds=remaining-(time.perf_counter()-started),finite=True))
            if estimate*1.25+300 > remaining-(time.perf_counter()-started):raise ValueError('Full protocol exceeds remaining budget')
            for start in range(0,len(rows),128):
                selected=rows[start:start+128];path=chunks/f'{start:06d}.npz'
                if path.exists():
                    with np.load(path,allow_pickle=False) as a:
                        if str(a['cache_key'])!=key or list(a['ids'])!=[r['id'] for r in selected]:raise ValueError('Chunk identity mismatch')
                    continue
                pooled=[];losses=[];counts=[]
                for row in selected:
                    score,feature=infer(model,[row],['norm'])
                    pooled.append(feature['norm'].numpy()[0]);losses.append(score[0]['nll_sum']);counts.append(score[0]['n_tokens'])
                values=np.asarray(pooled)
                if not np.isfinite(values).all() or not np.isfinite(losses).all():raise ValueError('Nonfinite extraction')
                tmp=path.with_suffix('.partial')
                with tmp.open('wb') as f:
                    np.savez_compressed(f,cache_key=key,ids=np.array([r['id'] for r in selected]),
                        labels=np.array([r['label'] for r in selected]),split=np.array([r['split'] for r in selected]),
                        sequence_sha256=np.array([r['sequence_sha256'] for r in selected]),features=values,
                        nll_sum=np.array(losses,dtype=np.float64),n_tokens=np.array(counts,dtype=np.int64))
                tmp.replace(path)
                write(RUN/'progress.json',dict(completed=min(start+128,len(rows)),total=len(rows),seconds=time.perf_counter()-started))
                print('EXTRACTED',min(start+128,len(rows)),'/',len(rows),flush=True)
            write(RUN/'extraction_complete.json',dict(cache_key=key,rows=len(rows),seconds=time.perf_counter()-started))
        finally:
            signal.alarm(0);budget.update('finish')


def metrics(y,p):
    return dict(auroc=float(roc_auc_score(y,p)),accuracy=float(accuracy_score(y,p>=.5)),
        balanced_accuracy=float(balanced_accuracy_score(y,p>=.5)),class1_prevalence=float(np.mean(y)),
        majority_baseline=float(max(np.mean(y),1-np.mean(y))),classification_cross_entropy=float(log_loss(y,p)))


def fit():
    rows=prepare();complete=json.loads((RUN/'extraction_complete.json').read_text())
    arrays=[]
    for path in sorted((RUN/'chunks').glob('*.npz')):
        with np.load(path,allow_pickle=False) as a:
            if str(a['cache_key'])!=complete['cache_key']:raise ValueError('Chunk key mismatch')
            arrays.append({k:a[k] for k in ['ids','labels','split','sequence_sha256','features','nll_sum','n_tokens']})
    a={k:np.concatenate([v[k] for v in arrays]) for k in arrays[0]}
    if list(a['ids'])!=[r['id'] for r in rows] or list(a['labels'])!=[r['label'] for r in rows]:raise ValueError('Saved row association mismatch')
    protocol=json.loads((RUN/'protocol.json').read_text());spec=protocol['head']
    torch.set_num_threads(4);torch.manual_seed(42);np.random.seed(42)
    head=torch.nn.Sequential(torch.nn.LayerNorm(1920),torch.nn.Linear(1920,1920),torch.nn.GELU(),torch.nn.Dropout(.1),torch.nn.Linear(1920,2))
    for module in head.modules():
        if isinstance(module,torch.nn.Linear):
            torch.nn.init.normal_(module.weight,mean=0.,std=1/math.sqrt(module.in_features));torch.nn.init.zeros_(module.bias)
    optimizer=torch.optim.AdamW(head.parameters(),lr=.001,betas=(.9,.95),weight_decay=0.)
    x=torch.from_numpy(a['features']).float();y=torch.from_numpy(a['labels']).long()
    train=np.flatnonzero(a['split']=='train');dev=np.flatnonzero(a['split']=='dev')
    generator=torch.Generator().manual_seed(42)
    def predict(indices):
        head.eval()
        with torch.inference_mode():return torch.cat([head(x[indices[i:i+256]]).softmax(-1)[:,1] for i in range(0,len(indices),256)]).numpy()
    candidates=[];best=-math.inf;selected=None;heads=RUN/'heads';heads.mkdir(exist_ok=True)
    for step in range(1,301):
        lr=.001*step/20 if step<=20 else .0001+.5*(.001-.0001)*(1+math.cos(math.pi*(step-20)/280))
        for group in optimizer.param_groups:group['lr']=lr
        batch=train[torch.randint(len(train),(8,),generator=generator).numpy()]
        head.train();optimizer.zero_grad();loss=torch.nn.functional.cross_entropy(head(x[batch]),y[batch]);loss.backward();optimizer.step()
        if step%50==0:
            score=metrics(a['labels'][dev],predict(dev));candidates.append(dict(step=step,lr=lr,dev=score))
            torch.save(head.state_dict(),heads/f'step-{step}.pt')
            if score['auroc']>best:best=score['auroc'];selected=step
    write(RUN/'selection.json',dict(selected_step=selected,candidates=candidates,criterion=spec['selection']))
    head.load_state_dict(torch.load(heads/f'step-{selected}.pt',weights_only=True))
    report=dict(selected_step=selected,splits={})
    with (RUN/'predictions.jsonl').open('w') as out:
        for split in ['train','dev','test']:
            indices=np.flatnonzero(a['split']==split);p=predict(indices);m=metrics(a['labels'][indices],p)
            sums=math.fsum(float(v) for v in a['nll_sum'][indices]);tokens=sum(int(v) for v in a['n_tokens'][indices])
            m.update(examples=len(indices),nll_sum=sums,n_tokens=tokens,causal_nll=sums/tokens,lm_perplexity=math.exp(sums/tokens))
            report['splits'][split]=m
            for i,prob in zip(indices,p):
                out.write(json.dumps(dict(id=str(a['ids'][i]),split=split,label=int(a['labels'][i]),
                    probability_class1=float(prob),nll_sum=float(a['nll_sum'][i]),n_tokens=int(a['n_tokens'][i])))+'\n')
    write(RUN/'metrics.json',report)
    write(RUN/'head_execution_identity.json',dict(protocol_sha256=sha(RUN/'protocol.json'),
        feature_cache_key=complete['cache_key'],source_sha256=sha(__file__),
        execution_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        torch=importlib.metadata.version('torch'),numpy=np.__version__,sklearn=importlib.metadata.version('scikit-learn'),device='CPU',selected_head_sha256=sha(heads/f'step-{selected}.pt')))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','extract','fit']);args=parser.parse_args()
    {'prepare':prepare,'extract':extract,'fit':fit}[args.stage]()
