"""Frozen BioNeMo benign H3 extraction with separate checkpoint cache identities."""
import argparse,dataclasses,fcntl,hashlib,json,os,time,subprocess,importlib.metadata
from pathlib import Path
import numpy as np
import torch
import torch.distributed as dist
import yaml
from tokenizers import Tokenizer
from benign_pilot.budget import update,BUDGET_PATH
from scripts.sayyed.check_benign_checkpoint_pair import load

def write(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2));tmp.replace(path)
def sha(p):
    return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);ap.add_argument('--config',required=True);ap.add_argument('--tokenizer',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--output',required=True);ap.add_argument('--model-name',required=True);ap.add_argument('--smoke',action='store_true');ap.add_argument('--smoke-rows',type=int,default=32);ap.add_argument('--batch-size',type=int,default=8);args=ap.parse_args()
    torch.set_num_threads(4);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    manifest=Path(args.manifest);rows=list(map(json.loads,manifest.read_text().splitlines()))
    if args.smoke:rows=[r for r in rows if r['split']=='train'][:args.smoke_rows]
    if any(r['split'] not in ['train','dev','test'] for r in rows):raise ValueError('Unexpected split')
    tokenizer=Tokenizer.from_file(args.tokenizer)
    for r in rows:
        ids=tokenizer.encode(r['sequence']).ids
        if ids!=[ord(c) for c in r['sequence']]:raise ValueError('Tokenizer nucleotide identity mismatch')
    shards=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(Path(args.checkpoint).glob('*.distcp'))]
    runtime={n:importlib.metadata.version(n) for n in ['torch','transformer-engine','transformer-engine-torch','bionemo-evo2','megatron-bridge','megatron-core','tokenizers','causal-conv1d']}
    runtime['source_commits']={p:subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip() for p in ['/workspace/bionemo-cu12','/workspace/megatron-bridge','/workspace/megatron-bridge/3rdparty/Megatron-LM']}
    identity=dict(runtime=runtime,checkpoint_shards=shards,model=args.model_name,checkpoint=args.checkpoint,checkpoint_metadata_sha256=sha(Path(args.checkpoint)/'.metadata'),config_sha256=sha(args.config),tokenizer_sha256=sha(args.tokenizer),manifest_sha256=sha(manifest),hooks=['decoder.final_norm','decoder.layers.16'],layer_numbering='exact zero-indexed module16; meeting layer16 equivalence unresolved',pool='mean nucleotide positions; padding excluded',padding='right to1000, pad1',dtype='checkpoint BF16/FP32 preserved',attention_backend='TE unfused',batch_size=args.batch_size,smoke=args.smoke,smoke_rows=args.smoke_rows,source_sha256=sha(__file__))
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();identity['cache_key']=key
    ip=out/'identity.json'
    if ip.exists() and json.loads(ip.read_text())!=identity:raise ValueError('Cache identity mismatch')
    write(ip,identity)
    from bionemo.evo2.models.evo2_provider import Hyena1bModelProvider
    from megatron.core import parallel_state,tensor_parallel
    from megatron.core.transformer.enums import AttnBackend
    cfg=yaml.safe_load(Path(args.config).read_text())['model'];allowed={f.name for f in dataclasses.fields(Hyena1bModelProvider) if f.init};kwargs={k:v for k,v in cfg.items() if k in allowed and (isinstance(v,(str,int,float,bool)) or v is None)}
    kwargs.update(attention_backend=AttnBackend.unfused,vocab_size=512,params_dtype=torch.bfloat16,pipeline_dtype=torch.bfloat16,bf16=True,use_cpu_initialization=True,perform_initialization=False,recompute_granularity=None,recompute_method=None,recompute_num_layers=None,seq_length=1000)
    # Checkpoint CPU loading is outside GPU timing; all backbone tensors must load.
    state=load(args.checkpoint)
    lock=BUDGET_PATH.with_suffix('.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    budget=json.loads(BUDGET_PATH.read_text())
    if budget.get('active_since'):raise RuntimeError('Existing active ledger; reconcile before execution')
    remaining=budget['limit_seconds']-budget['used_seconds']
    if remaining<60:raise RuntimeError('Insufficient GPU budget')
    update('begin');started=time.monotonic()
    try:
        torch.cuda.set_device(0);torch.cuda.reset_peak_memory_stats()
        init_file=out/'distributed_init'
        dist.init_process_group('nccl',init_method='file://'+str(init_file.resolve()),rank=0,world_size=1)
        parallel_state.initialize_model_parallel(tensor_model_parallel_size=1,pipeline_model_parallel_size=1)
        tensor_parallel.model_parallel_cuda_manual_seed(42)
        provider=Hyena1bModelProvider(**kwargs);provider.finalize()
        model=provider.provide();model=model.to(device='cuda')
        dtype_mismatches={k:[str(v.dtype),str(model.state_dict()[k].dtype)] for k,v in state.items() if k in model.state_dict() and v.dtype!=model.state_dict()[k].dtype}
        bad_dtypes={k:v for k,v in dtype_mismatches.items() if v!=['torch.bfloat16','torch.float32']}
        if bad_dtypes:raise ValueError(f'Lossy checkpoint/model dtype mismatch: {bad_dtypes}')
        missing,unexpected=model.load_state_dict(state,strict=False)
        bad_missing=[x for x in missing if '_extra_state' not in x];bad_unexpected=[x for x in unexpected if '_extra_state' not in x]
        write(out/'loading.json',dict(dtype_promotions=dtype_mismatches,promotion_policy='BF16 to FP32 only, exact value-preserving promotion for filter computation',missing=missing,unexpected=unexpected,allowed='only TE extra-state differences; BF16 evaluation',model_parameters=sum(p.numel() for p in model.parameters())))
        if bad_missing or bad_unexpected:raise RuntimeError(f'Backbone load mismatch {bad_missing} {bad_unexpected}')
        model.eval();model.requires_grad_(False);del state
        captured={}
        def hook(name):
            def capture(module,inputs,output):captured[name]=output[0] if isinstance(output,tuple) else output
            return capture
        handles=[model.decoder.final_norm.register_forward_hook(hook('final_norm')),model.decoder.layers[16].register_forward_hook(hook('decoder_layer_16'))]
        chunk_count=0;processed=0;forward_seconds=0;batch_seconds=[]
        for start in range(0,len(rows),args.batch_size):
            if time.monotonic()-started>min(remaining-15,1800):raise TimeoutError('Stage time cap; completed chunks preserved')
            rr=rows[start:start+args.batch_size];target=out/f'chunk_{start:06d}.npz'
            if target.exists():
                with np.load(target,allow_pickle=False) as a:
                    if a['cache_key'].item()!=key or a['ids'].tolist()!=[r['id'] for r in rr]:raise ValueError('Saved chunk identity mismatch')
                processed+=len(rr);continue
            lengths=torch.tensor([len(r['sequence']) for r in rr],device='cuda');tokens=torch.ones((len(rr),1000),dtype=torch.long,device='cuda')
            for i,r in enumerate(rr):tokens[i,:len(r['sequence'])]=torch.tensor(tokenizer.encode(r['sequence']).ids,device='cuda')
            positions=torch.arange(1000,device='cuda')[None].expand(len(rr),-1);valid=positions<lengths[:,None]
            torch.cuda.synchronize();t=time.monotonic()
            with torch.inference_mode():
                logits=model(input_ids=tokens,position_ids=positions,attention_mask=None)
                if logits.shape!=(len(rr),1000,512):raise ValueError(f'Logit shape {logits.shape}')
                features={}
                for name,h in captured.items():
                    if h.shape!=(1000,len(rr),1920):raise ValueError(f'Hook shape {name} {h.shape}')
                    features[name]=(h.transpose(0,1).float()*valid[:,:,None]).sum(1)/lengths[:,None]
                    if not torch.isfinite(features[name]).all():raise ValueError('Nonfinite features')
                loss=torch.nn.functional.cross_entropy(logits[:,:-1].float().reshape(-1,512),tokens[:,1:].reshape(-1),reduction='none').reshape(len(rr),-1);mask=positions[:,1:]<lengths[:,None];sums=(loss*mask).sum(1)
                if not torch.isfinite(sums).all():raise ValueError('Nonfinite NLL')
            torch.cuda.synchronize();batch_seconds.append(time.monotonic()-t);forward_seconds+=batch_seconds[-1]
            np.savez(target,ids=np.array([r['id'] for r in rr]),labels=np.array([r['label'] for r in rr]),split=np.array([r['split'] for r in rr]),sequence_sha256=np.array([hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rr]),cache_key=np.array(key),nll_sum=sums.cpu().numpy(),n_tokens=(lengths-1).cpu().numpy(),**{k:v.cpu().numpy() for k,v in features.items()})
            processed+=len(rr);chunk_count+=1
            write(out/'progress.json',dict(processed=processed,total=len(rows),pid=os.getpid(),elapsed=time.monotonic()-started,forward_seconds=forward_seconds,peak_memory=torch.cuda.max_memory_allocated(),cache_key=key))
        write(out/'complete.json',dict(examples=processed,batch_seconds=batch_seconds,forward_seconds=forward_seconds,wall_seconds=time.monotonic()-started,peak_memory=torch.cuda.max_memory_allocated(),cache_key=key))
    finally:
        update('end')
        if dist.is_initialized():dist.destroy_process_group()
        fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
