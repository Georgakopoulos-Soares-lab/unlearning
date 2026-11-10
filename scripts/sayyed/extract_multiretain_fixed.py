"""Separately versioned all-layer BioNeMo extraction; mandatory session ledger."""
import argparse,dataclasses,fcntl,hashlib,json,os,time,subprocess,importlib.metadata,signal
from pathlib import Path
import numpy as np
import torch
import torch.distributed as dist
import yaml
from tokenizers import Tokenizer
from benign_pilot.budget import BUDGET_PATH
from scripts.sayyed.fixed_benign_batch import pack
from scripts.sayyed.multiretain_support import SessionBudget,layer_specs,pooled_activation
from scripts.sayyed.check_benign_checkpoint_pair import load

def write(path,obj):
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(obj,indent=2));tmp.replace(path)
def sha(p):
    return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def terminate_own_stage(*_):
    raise SystemExit('Terminated own stage; ledger finalized')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);ap.add_argument('--config',required=True);ap.add_argument('--tokenizer',required=True);ap.add_argument('--manifest',required=True);ap.add_argument('--output',required=True);ap.add_argument('--model-name',required=True);ap.add_argument('--smoke',action='store_true');ap.add_argument('--smoke-rows',type=int,default=32);ap.add_argument('--batch-size',type=int,default=8);ap.add_argument('--session-ledger',required=True);ap.add_argument('--session-config',required=True);args=ap.parse_args()
    signal.signal(signal.SIGTERM,terminate_own_stage)
    torch.set_num_threads(4);out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    manifest=Path(args.manifest);rows=list(map(json.loads,manifest.read_text().splitlines()))
    if not 1<=args.batch_size<=8 or args.smoke_rows<1:raise ValueError('Positive batch and smoke sizes required')
    if args.smoke:rows=[r for r in rows if r['split']=='train'][:args.smoke_rows]
    if any(r['split'] not in ['train','dev','test'] for r in rows):raise ValueError('Unexpected split')
    if not rows or len({r['id'] for r in rows})!=len(rows):raise ValueError('Empty or duplicate-ID manifest')
    if any(not 2<=len(r['sequence'])<=1000 or set(r['sequence'])-set('ACGTN') for r in rows):raise ValueError('Unqualified sequence alphabet or length')
    tokenizer=Tokenizer.from_file(args.tokenizer)
    for r in rows:
        ids=tokenizer.encode(r['sequence']).ids
        if ids!=[ord(c) for c in r['sequence']]:raise ValueError('Tokenizer nucleotide identity mismatch')
    shards=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(Path(args.checkpoint).glob('*.distcp'))]
    runtime={n:importlib.metadata.version(n) for n in ['torch','transformer-engine','transformer-engine-torch','bionemo-evo2','megatron-bridge','megatron-core','tokenizers','causal-conv1d']}
    runtime['source_commits']={p:subprocess.check_output(['git','-C',p,'rev-parse','HEAD'],text=True).strip() for p in ['/workspace/bionemo-cu12','/workspace/megatron-bridge','/workspace/megatron-bridge/3rdparty/Megatron-LM']}
    identity=dict(runtime=runtime,checkpoint_shards=shards,model=args.model_name,checkpoint=args.checkpoint,checkpoint_metadata_sha256=sha(Path(args.checkpoint)/'.metadata'),config_sha256=sha(args.config),tokenizer_sha256=sha(args.tokenizer),manifest_sha256=sha(manifest),hooks=[f'decoder.layers.{i}' for i in range(yaml.safe_load(Path(args.config).read_text())['model']['num_layers'])]+['decoder.final_norm'],schema='multiretain-all-layers-fixed8-v2',physical_batch_size=8,filler_policy='pad1 rows of valid length1; all filler outputs excluded',layer_numbering='exact zero-indexed module16; meeting layer16 equivalence unresolved',pool='mean nucleotide positions; padding excluded',padding='right to1000, pad1',dtype='checkpoint BF16/FP32 preserved',attention_backend='TE unfused',batch_size=args.batch_size,smoke=args.smoke,smoke_rows=args.smoke_rows,source_sha256=sha(__file__),support_sha256=sha(Path(__file__).with_name('multiretain_support.py')),fixed_batch_source_sha256=sha(Path(__file__).with_name('fixed_benign_batch.py')),effective_config_sha256=sha(args.session_config))
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
    lock=BUDGET_PATH.with_name('evo2-pilot.gpu.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    legacy_lock=BUDGET_PATH.with_suffix('.lock').open('a');fcntl.flock(legacy_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    historical=json.loads(BUDGET_PATH.read_text())
    budget=SessionBudget(args.session_ledger,args.session_config)
    if historical.get('active_since'):raise RuntimeError('Existing active ledger; reconcile before execution')
    remaining=budget.read()
    if remaining<60:raise RuntimeError('Insufficient GPU budget')
    budget.begin();started=time.monotonic()
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
            def capture(module,inputs,output):captured[name]=pooled_activation(output,lengths,model.config.hidden_size)
            return capture
        specs=layer_specs(model)
        if [name for _,name,_ in specs]!=identity['hooks']:raise ValueError('Actual architecture differs from configured hooks')
        handles=[module.register_forward_hook(hook(key)) for key,_,module in specs]
        chunk_count=0;processed=0;forward_seconds=0;batch_seconds=[]
        for start in range(0,len(rows),args.batch_size):
            if time.monotonic()-started>remaining-15:raise TimeoutError('Stage time cap; completed chunks preserved')
            rr=rows[start:start+args.batch_size];target=out/f'chunk_{start:06d}.npz'
            if target.exists():
                with np.load(target,allow_pickle=False) as a:
                    if a['cache_key'].item()!=key or a['ids'].tolist()!=[r['id'] for r in rr]:raise ValueError('Saved chunk identity mismatch')
                processed+=len(rr);continue
            tokens,lengths,positions=pack([r['sequence'] for r in rr],device='cuda',physical_size=8)
            torch.cuda.synchronize();t=time.monotonic()
            captured.clear()
            with torch.inference_mode():
                logits=model(input_ids=tokens,position_ids=positions,attention_mask=None)
                if logits.shape!=(8,1000,512):raise ValueError(f'Logit shape {logits.shape}')
                features={}
                if set(captured)!={key for key,_,_ in specs}:raise ValueError('Missing layer activation')
                for name,h in captured.items():
                    if h.shape!=(8,model.config.hidden_size):raise ValueError(f'Pooled hook shape {name} {h.shape}')
                    features[name]=h[:len(rr)]
                    if not torch.isfinite(features[name]).all():raise ValueError('Nonfinite features')
                loss=torch.nn.functional.cross_entropy(logits[:,:-1].float().reshape(-1,512),tokens[:,1:].reshape(-1),reduction='none').reshape(8,-1);mask=positions[:,1:]<lengths[:,None];sums=(loss*mask).sum(1)
                if not torch.isfinite(sums).all():raise ValueError('Nonfinite NLL')
            torch.cuda.synchronize();batch_seconds.append(time.monotonic()-t);forward_seconds+=batch_seconds[-1]
            temporary=target.with_name('.'+target.name+'.tmp.npz')
            np.savez(temporary,ids=np.array([r['id'] for r in rr]),labels=np.array([r['label'] for r in rr]),split=np.array([r['split'] for r in rr]),sequence_sha256=np.array([hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rr]),cache_key=np.array(key),nll_sum=sums[:len(rr)].cpu().numpy(),n_tokens=(lengths[:len(rr)]-1).cpu().numpy(),**{k:v.cpu().numpy() for k,v in features.items()})
            temporary.replace(target)
            processed+=len(rr);chunk_count+=1
            write(out/'progress.json',dict(processed=processed,total=len(rows),pid=os.getpid(),elapsed=time.monotonic()-started,forward_seconds=forward_seconds,peak_memory=torch.cuda.max_memory_allocated(),cache_key=key))
        write(out/'complete.json',dict(examples=processed,batch_seconds=batch_seconds,forward_seconds=forward_seconds,wall_seconds=time.monotonic()-started,peak_memory=torch.cuda.max_memory_allocated(),cache_key=key))
        finalized=[out/'identity.json',out/'loading.json',out/'complete.json',*sorted(out.glob('chunk_*.npz'))]
        write(out/'COMPLETE.json',dict(schema='multiretain-unit-v1',status='NEW',unit='training_smoke' if args.smoke else 'extraction',cache_key=key,examples=processed,files=[dict(path=str(p.resolve()),sha256=sha(p),bytes=p.stat().st_size) for p in finalized],qualification='Extraction finished; scientific smoke/anchor and consumer verification remain separate gates'))
    finally:
        budget.end()
        if dist.is_initialized():dist.destroy_process_group()
        fcntl.flock(legacy_lock,fcntl.LOCK_UN)
        fcntl.flock(lock,fcntl.LOCK_UN)
if __name__=='__main__':main()
