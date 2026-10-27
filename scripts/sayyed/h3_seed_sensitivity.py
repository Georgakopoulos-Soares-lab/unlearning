"""Two predeclared CPU MLP seeds on cached benign H3 features; no seed sweep."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time

import numpy as np
import torch
from threadpoolctl import threadpool_limits

from .h3_followup import load, metric, sha, write


def freeze(run):
    if (run/'seed_amendment.json').exists():raise ValueError('Amendment already frozen')
    value=dict(frozen_utc=datetime.now(timezone.utc).isoformat(),seeds=[17,1234],original_seed=42,
        policy='Report every seed; no best-seed selection and no replacement of original primary result',
        architecture_and_schedule='Exactly the original LayerNorm1920/Linear1920/GELU/Dropout.1/Linear2; AdamW betas.9/.95 eps1e-8 no weight decay;300 steps batch8 uniform replacement;20-step warmup to.001 then cosine to.0001; CPU float32 four threads',
        rng='Set torch.manual_seed(seed), numpy seed, and separate torch.Generator seed to each declared seed',
        selection='Dev AUROC at50/100/150/200/250/300; exact ties earliest; threshold.5',
        protocol_sha256=sha(run/'protocol.json'),source_sha256=sha(__file__),
        qualification='Optional post-hoc exploratory sensitivity; three seeds do not estimate all training uncertainty')
    write(run/'seed_amendment.json',value);write(run/'seed_amendment_hash.json',dict(sha256=sha(run/'seed_amendment.json')))


def execute(run):
    amendment=json.loads((run/'seed_amendment.json').read_text())
    if amendment['source_sha256']!=sha(__file__):raise ValueError('Seed code changed after amendment')
    if amendment['seeds']!=[17,1234]:raise ValueError('Bounded seeds only')
    cfg,original,rows,a=load(run);torch.set_num_threads(4)
    x=torch.from_numpy(a['features']).float();y=torch.from_numpy(a['labels']).long()
    train=np.flatnonzero(a['split']=='train');dev=np.flatnonzero(a['split']=='dev');test=np.flatnonzero(a['split']=='test')
    output=run/'seed_sensitivity';output.mkdir(exist_ok=True);results={}
    all_start=time.perf_counter();cpu_start=time.process_time()
    for seed in amendment['seeds']:
        torch.manual_seed(seed);np.random.seed(seed);generator=torch.Generator().manual_seed(seed)
        head=torch.nn.Sequential(torch.nn.LayerNorm(1920),torch.nn.Linear(1920,1920),torch.nn.GELU(),torch.nn.Dropout(.1),torch.nn.Linear(1920,2))
        for module in head.modules():
            if isinstance(module,torch.nn.Linear):
                torch.nn.init.normal_(module.weight,mean=0.,std=1/math.sqrt(module.in_features));torch.nn.init.zeros_(module.bias)
        optimizer=torch.optim.AdamW(head.parameters(),lr=.001,betas=(.9,.95),weight_decay=0.)
        def predict(ix):
            head.eval()
            with torch.inference_mode():return torch.cat([head(x[ix[i:i+256]]).softmax(-1)[:,1] for i in range(0,len(ix),256)]).numpy()
        trajectory=[];best=-math.inf;selected=None;state=None;draws=[]
        started=time.perf_counter()
        for step in range(1,301):
            lr=.001*step/20 if step<=20 else .0001+.5*(.001-.0001)*(1+math.cos(math.pi*(step-20)/280))
            for group in optimizer.param_groups:group['lr']=lr
            local=torch.randint(len(train),(8,),generator=generator).numpy();draws.append(local)
            batch=train[local];head.train();optimizer.zero_grad()
            loss=torch.nn.functional.cross_entropy(head(x[batch]),y[batch]);loss.backward();optimizer.step()
            if step%50==0:
                score=metric(a['labels'][dev],predict(dev));trajectory.append(dict(step=step,lr=lr,dev=score))
                if score['auroc']>best:
                    best=score['auroc'];selected=step;state={k:v.detach().clone() for k,v in head.state_dict().items()}
        selection=dict(seed=seed,selected_step=selected,trajectory=trajectory,
            unique_rows_seen_at_selected=len(np.unique(np.stack(draws)[:selected])))
        # Persist the dev-only selection before producing this seed's test predictions.
        write(output/f'seed-{seed}-selection.json',selection)
        torch.save(state,output/f'seed-{seed}-selected.pt');head.load_state_dict(state)
        metrics={}
        with (output/f'seed-{seed}-predictions.jsonl').open('w') as out:
            for split,ix in [('dev',dev),('test',test)]:
                probabilities=predict(ix);metrics[split]=metric(a['labels'][ix],probabilities)
                for i,p in zip(ix,probabilities):out.write(json.dumps(dict(id=str(a['ids'][i]),split=split,label=int(a['labels'][i]),probability_class1=float(p)))+'\n')
        results[str(seed)]=dict(**selection,metrics=metrics,wall_seconds=time.perf_counter()-started,
            selected_head_sha256=sha(output/f'seed-{seed}-selected.pt'))
        write(run/'seed_results.partial.json',results);print('SEED_COMPLETE',seed,selected,metrics['test']['auroc'],flush=True)
    write(run/'seed_results.json',results);write(run/'seed_timing.json',dict(wall_seconds=time.perf_counter()-all_start,cpu_seconds=time.process_time()-cpu_start))


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['freeze','execute']);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    with threadpool_limits(limits=4):{'freeze':freeze,'execute':execute}[a.stage](a.run)


if __name__=='__main__':main()
