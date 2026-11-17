"""Real frozen BioNeMo Hyena + source-pinned native Evo2LoRA backend.

Candidate engineering provenance is explicit; successful tensor loading and
numerics never establish the unknown historical job parent/source identity.
Imports of CUDA/native code occur only inside a budget-owned worker.
"""
from __future__ import annotations
import dataclasses
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from .budget import worker_guard
from .contracts import require, canonical_sha, file_sha, LAYERS


def tensor_record(key, tensor):
    import torch
    value = tensor.detach().cpu().contiguous()
    return dict(key=key, shape=list(value.shape), dtype=str(value.dtype),
                sha256=hashlib.sha256(value.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest(),
                finite=bool(torch.isfinite(value).all()))


def fingerprint(records):
    return canonical_sha(sorted(records, key=lambda r: r['key']))


class NativeBackend:
    def __init__(self, directory: Path):
        self.directory = directory; self.model = None; self.peft = None
        self.generation = 0; self.handles = []; self.adapter_sha = None
        self.initial_parent = None; self.binding = None
        self.model_forward_invocations=0;self.completed_model_batches=0;self.candidate_binding=None

    def load(self, binding: dict) -> None:
        worker_guard()
        self.candidate_binding=binding
        import torch
        import torch.distributed as dist
        import yaml
        from tokenizers import Tokenizer
        from megatron.core import parallel_state, tensor_parallel
        from megatron.core.transformer.enums import AttnBackend
        from bionemo.evo2.models.evo2_provider import Hyena1bModelProvider
        from bionemo.evo2.models.evo2_lora import Evo2LoRA
        from scripts.sayyed.check_benign_checkpoint_pair import load
        torch.set_grad_enabled(False); torch.set_num_threads(4)
        adapter_root = Path(binding['adapter_root']); parent_root = Path(binding['parent_root'])
        for record in binding['input_files']:
            p = Path(record['path'])
            require(p.stat().st_size == record['bytes'] and file_sha(p) == record['sha256'], 'INPUT_HASH', str(p))
        config = yaml.safe_load((adapter_root/'run_config.yaml').read_text())
        require(config['model'].get('num_moe_experts') is None, 'NATIVE_CONFIG', 'No MoE backport')
        peft_cfg = dict(config['peft']); peft_cfg.pop('_target_')
        saved_names = set(peft_cfg.pop('params_to_save'))
        require(len(saved_names) == 200, 'TENSOR_SCHEMA', 'Checkpoint params_to_save must account for all adapters')
        accepted = {f.name for f in dataclasses.fields(Evo2LoRA) if f.init}
        require(not (set(peft_cfg)-accepted), 'NATIVE_CONFIG', 'Unsupported fields: '+str(set(peft_cfg)-accepted))
        require(peft_cfg['dim'] == 16 and peft_cfg['alpha'] == 32 and peft_cfg['dropout'] == .1
                and peft_cfg['dropout_position'] == 'pre' and peft_cfg['skip_freeze_modules'] == [],
                'NATIVE_CONFIG', 'Changed native LoRA semantics')
        require(not peft_cfg['canonical_mapping'] and not peft_cfg['normalize_moe_lora']
                and peft_cfg['share_expert_adapters'], 'NATIVE_CONFIG', 'Non-default MoE/canonical configuration unsupported')
        adapter = load(adapter_root)
        require(set(adapter) == saved_names, 'TENSOR_KEYS', 'No inference tensor may be omitted')
        schema = {k:dict(shape=list(v.shape),dtype=str(v.dtype)) for k,v in adapter.items()}
        require(hashlib.sha256(json.dumps(schema,sort_keys=True).encode()).hexdigest() == binding['adapter_schema_sha256'],
                'TENSOR_SCHEMA', 'All 200 names/shapes/dtypes must match')
        expected_adapter = [tensor_record(k,v) for k,v in adapter.items()]
        if self.model is None:
            self.delivered_model_config = config["model"]
            # CPU deserialization occurs inside the conservatively charged stage.
            parent = load(parent_root)
            require('embedding.word_embeddings.weight' in parent, 'OUTPUT_HEAD', 'Embedding tensor missing')
            actual_vocab, hidden = parent['embedding.word_embeddings.weight'].shape
            require(hidden == 1920 and actual_vocab in (256,512), 'OUTPUT_HEAD', 'Unsupported native shape')
            if 'output_layer.weight' in parent:
                require(tuple(parent['output_layer.weight'].shape) == (actual_vocab,hidden), 'OUTPUT_HEAD', 'Head shape disagrees')
            allowed = {f.name for f in dataclasses.fields(Hyena1bModelProvider) if f.init}
            cfg = config['model']
            kwargs = {k:v for k,v in cfg.items() if k in allowed and (isinstance(v,(str,int,float,bool)) or v is None)}
            # The delivered parent tensor defines its native vocabulary. This is
            # explicit metadata resolution, never head padding/slicing/resizing.
            kwargs.update(vocab_size=int(actual_vocab), attention_backend=AttnBackend.unfused,
                params_dtype=torch.bfloat16, pipeline_dtype=torch.bfloat16, bf16=True,
                use_cpu_initialization=True, perform_initialization=False,
                recompute_granularity=None,recompute_method=None,recompute_num_layers=None,seq_length=1000)
            worker_guard(); torch.cuda.set_device(0); torch.cuda.reset_peak_memory_stats()
            dist.init_process_group('nccl', init_method='file://'+str((self.directory/'dist_init').resolve()),rank=0,world_size=1)
            parallel_state.initialize_model_parallel(tensor_model_parallel_size=1,pipeline_model_parallel_size=1)
            tensor_parallel.model_parallel_cuda_manual_seed(42)
            self.resolved_inference_config=dict(provider='bionemo.evo2.models.evo2_provider.Hyena1bModelProvider',
                kwargs={k:v if isinstance(v,(str,int,float,bool)) or v is None else str(v) for k,v in kwargs.items()})
            (self.directory/'resolved_inference_config.json').write_text(json.dumps(self.resolved_inference_config,sort_keys=True,separators=(',',':')))
            provider = Hyena1bModelProvider(**kwargs); provider.finalize()
            self.model = provider.provide().to('cuda'); self.model.eval(); self.model.requires_grad_(False)
            complete_state = self.model.state_dict()
            import pickle
            runtime_extras = {k:v for k,v in complete_state.items() if k.endswith('._extra_state')}
            (self.directory/'runtime_extra_state_types.json').write_text(json.dumps({k:dict(type=type(v).__name__,bytes_hex=v.detach().cpu().numpy().tobytes().hex() if torch.is_tensor(v) and v.numel()<32 else None) for k,v in runtime_extras.items()},indent=2))
            for k,v in runtime_extras.items():
                require(v is None or (torch.is_tensor(v) and v.detach().cpu().numpy().tobytes() in (pickle.dumps(None), pickle.dumps({}))),
                        'NONEMPTY_TE_EXTRA_STATE', k)
            for m in self.model.modules():
                require(not getattr(m,'fp8',False) and not getattr(m,'primary_weights_in_fp8',False),
                        'FP8_UNSUPPORTED','BF16/FP32 route only')
            actual = {k:v for k,v in complete_state.items() if torch.is_tensor(v) and k not in runtime_extras}
            require(set(actual)==set(parent), 'PARENT_TENSOR_KEYS', str(dict(missing=sorted(set(actual)-set(parent)),unexpected=sorted(set(parent)-set(actual)))))
            promotions = {}
            for k,v in parent.items():
                require(v.shape == actual[k].shape, 'PARENT_SHAPE', k)
                if v.dtype != actual[k].dtype:
                    require(v.dtype == torch.bfloat16 and actual[k].dtype == torch.float32, 'PARENT_DTYPE', k)
                    promotions[k] = [str(v.dtype),str(actual[k].dtype)]
            missing, unexpected = self.model.load_state_dict(parent,strict=False)
            require(not [k for k in missing+unexpected if '_extra_state' not in k], 'PARENT_LOAD', str((missing,unexpected)))
            for k,v in self.model.state_dict().items():
                if torch.is_tensor(v) and k in parent: require(torch.equal(v.detach().cpu(),parent[k].to(v.dtype)), 'PARENT_CONTENT', k)
            self.contract = dict(layers=list(LAYERS),feature_width=1920,physical_batch_size=8,sequence_length=1000,
                vocab_size=int(actual_vocab),tokenization='historical_char_no_special',nucleotide_ids=dict(A=65,C=67,G=71,T=84,N=78),pad_id=1,atol=1e-4,rtol=1e-5)
            self.tokenizer = Tokenizer.from_file(binding['tokenizer_path'])
            self.peft = Evo2LoRA(**peft_cfg)
            (self.directory/'loading.json').write_text(json.dumps(dict(parent_root=str(parent_root),parent_declared_vocab=yaml.safe_load((parent_root/'run_config.yaml').read_text())['model']['vocab_size'],native_embedding_shape=[actual_vocab,hidden],delivered_adapter_vocab=cfg.get('vocab_size'),vocab_resolution='Exact native parent tensor shape; no reshape, slice, extra rows, or head replacement',dtype_promotions=promotions,missing=missing,unexpected=unexpected,peft=peft_cfg,runtime_TE_extra_state=[tensor_record(k,v) if torch.is_tensor(v) else dict(key=k,kind='literal_None') for k,v in runtime_extras.items()],runtime_TE_extra_state_policy='Literal None is accepted for native Core output_layer; every emitted TE extra-state tensor must byte-match locally generated pickle.dumps(None) or pickle.dumps({}); no FP8, nonempty state fails; all retained in actual snapshots',resolved_provider={k:str(v) for k,v in vars(provider).items()},delivered_model_fields_not_forwarded={k:str(v) for k,v in cfg.items() if k not in kwargs},explicit_runtime_overrides={k:str(kwargs[k]) for k in ['vocab_size','params_dtype','attention_backend','recompute_granularity','seq_length']}),indent=2))
            del parent, actual
            self.initial_parent = self.parent_snapshot()
            if binding['mode']=='SCIENTIFIC_QUALIFICATION':
                require(self.initial_parent['parent_fingerprint']==binding['parent_fingerprint']
                        and self.initial_parent['output_head_fingerprint']==binding['output_head_fingerprint'],
                        'BOUND_STATE','Actual parent/head must match before any parent smoke')
            if hasattr(self, "training_rows"):
                self.parent_baseline = self.forward(self.training_rows,logical_batch_size=8,hooks=True)
                from .gate import save_result
                save_result(self.directory,"parent_baseline_before_adapter",self.parent_baseline)
            self.peft(self.model,training=False)
            # Provider uses CPU initialization; native adapters follow that flag.
            # Move newly attached modules to CUDA without any dtype conversion.
            self.model.to(device="cuda")
            self.model.requires_grad_(False); self.model.eval()
        else:
            require(config['model'] == self.delivered_model_config, 'SWAP_CONFIG', 'Native model inference configuration changed across swap')
            require(self.binding['parent_root'] == binding['parent_root'], 'PARENT_SWAP', 'No backbone change during A-B-A')
            require(self.binding['peft_semantics_sha256'] == binding['peft_semantics_sha256'], 'SWAP_SEMANTICS', 'Different native config')
        actual = {k:v for k,v in self.model.state_dict().items() if '.adapter.' in k and torch.is_tensor(v)}
        require(set(actual)==set(adapter), 'ADAPTER_LOAD_KEYS', str(dict(missing=list(set(adapter)-set(actual)),unexpected=list(set(actual)-set(adapter)))))
        # Canonical keys come from the native AdapterWrapper.state_dict method.
        # Copy each explicitly identified native parameter; never fuzzy-prefix match.
        with torch.no_grad():
            for k,v in adapter.items():
                require(actual[k].shape==v.shape and actual[k].dtype==v.dtype, 'ADAPTER_LOAD_SHAPE_DTYPE', k)
                actual[k].copy_(v)
        self.adapter_sha = file_sha(adapter_root/'__0_0.distcp'); self.binding = binding; self.generation += 1
        self.expected_adapter = expected_adapter; self.set_adapter_enabled(True)
        snap = self.snapshot()
        require(snap['parent_fingerprint'] == self.initial_parent['parent_fingerprint'], 'PARENT_MUTATION', 'Wrapping/swap changed native backbone or buffers')
        require(snap['adapter_tensors'] == sorted(expected_adapter,key=lambda r:r['key']), 'ADAPTER_CONTENT', 'Native loaded tensors disagree')
        self.clear_transients()
        (self.directory/f'load_{self.generation:02d}.json').write_text(json.dumps(snap,indent=2))

    def parent_snapshot(self):
        import torch
        require(self.model is not None, 'NATIVE_MODEL', 'Model not constructed')
        # Actual model tensors plus all nonpersistent buffers, not manifest echoes.
        records = [tensor_record(k,v) for k,v in self.model.state_dict().items() if torch.is_tensor(v) and '.adapter.' not in k]
        # state_dict omits nonpersistent buffers; include them under explicit keys.
        for name,module in self.model.named_modules():
            if '.adapter' in name: continue
            for n in module._non_persistent_buffers_set:
                value = module._buffers[n]
                if value is not None:
                    canonical = ((name+'.') if name else '')+n
                    canonical = canonical.replace('.to_wrap.','.')
                    records.append(tensor_record('nonpersistent:'+canonical,value))
        records.sort(key=lambda r:r['key'])
        head = [r for r in records if r['key'].startswith(('embedding.','output_layer.','decoder.final_norm.'))]
        return dict(parent_fingerprint=fingerprint(records),parent_tensors=records,output_head_fingerprint=fingerprint(head))

    def snapshot(self):
        worker_guard()
        import torch
        from megatron.bridge.peft.adapter_wrapper import AdapterWrapper
        result = self.parent_snapshot()
        result.update(adapter_sha256=self.adapter_sha,adapter_tensors=sorted([tensor_record(k,v) for k,v in self.model.state_dict().items() if torch.is_tensor(v) and '.adapter.' in k],key=lambda r:r['key']),load_generation=self.generation,model_training=self.model.training,grad_enabled=torch.is_grad_enabled(),parameters_requiring_grad=sum(p.requires_grad for p in self.model.parameters()),adapter_enabled=all(m._adapter_enabled for m in self.model.modules() if isinstance(m,AdapterWrapper)),dropout_training=any(m.training for m in self.model.modules() if isinstance(m,torch.nn.Dropout)),hook_registrations=sum(len(m._forward_hooks)+len(m._forward_pre_hooks) for m in self.model.modules()),optimizer_restored=False,training_recompute_active=bool(self.model.config.recompute_granularity),transient_state_cleared=True)
        return result

    def clear_transients(self):
        # Each full forward has no inference context or recurrent state passed.
        require(not self.handles, 'STALE_HOOKS', 'Hooks must be removed after each call')
        for m in self.model.modules():
            for field in ('inference_context','inference_params'):
                require(getattr(m,field,None) is None, 'RECURRENT_STATE', field)

    def set_adapter_enabled(self, enabled):
        if enabled: self.peft.enable_adapter_layers(self.model)
        else: self.peft.disable_adapter_layers(self.model)

    def forward(self, rows, *, logical_batch_size=8, hooks=True, filler_token=1):
        worker_guard(); self.clear_transients()
        import torch
        from scripts.sayyed.fixed_benign_batch import pack
        from scripts.sayyed.multiretain_support import layer_specs,pooled_activation
        from megatron.bridge.peft.adapter_wrapper import AdapterWrapper
        require(logical_batch_size in (1,8), 'LOGICAL_BATCH', str(logical_batch_size))
        require(all(r['split']=='train' for r in rows), 'NON_TRAINING_INPUT', 'Training only')
        for row in rows:
            require(self.tokenizer.encode(row['sequence']).ids == [ord(c) for c in row['sequence']], 'TOKENIZER', row['id'])
        outputs={k:[] for k in ['tokens','positions','target_mask','nll_sum','n_tokens','logits']}
        features={k:[] for k in LAYERS} if hooks else {}; calls={k:0 for k in LAYERS} if hooks else {}
        branches={name:0 for name,m in self.model.named_modules() if isinstance(m,AdapterWrapper)}
        widths=self.contract['feature_width']; specs=layer_specs(self.model)
        require([key for key,_,_ in specs] == list(LAYERS), 'COORDINATES', 'Native model must expose all26')
        try:
            for name,m in self.model.named_modules():
                if isinstance(m,AdapterWrapper):
                    def branch(module,args,out,name=name): branches[name]+=1
                    self.handles.append(m.adapter.register_forward_hook(branch))
            for start in range(0,len(rows),logical_batch_size):
                worker_guard(); rr=rows[start:start+logical_batch_size]; captured={}
                tokens,lengths,positions=pack([r['sequence'] for r in rr],device='cuda',physical_size=8)
                if filler_token != 1: tokens[len(rr):]=filler_token
                batch_handles=[]
                if hooks:
                    for key,_,module in specs:
                        def capture(module,args,out,key=key):
                            require(key not in captured,'DUPLICATE_HOOK',key)
                            captured[key]=pooled_activation(out,lengths,widths);calls[key]+=1
                        handle=module.register_forward_hook(capture);batch_handles.append(handle);self.handles.append(handle)
                try:
                    with torch.inference_mode():
                        self.model_forward_invocations+=1
                        logits=self.model(input_ids=tokens,position_ids=positions,attention_mask=None)
                        require(tuple(logits.shape)==(8,1000,self.contract['vocab_size']),'LOGIT_SHAPE',str(logits.shape))
                        loss=torch.nn.functional.cross_entropy(logits[:,:-1].float().reshape(-1,logits.shape[-1]),tokens[:,1:].reshape(-1),reduction='none').reshape(8,-1)
                        mask=positions[:,1:]<lengths[:,None]
                        values=dict(tokens=tokens,positions=positions,target_mask=mask,nll_sum=(loss*mask).sum(1),n_tokens=mask.sum(1),logits=logits.float())
                        for k,v in values.items():outputs[k].append(v[:len(rr)].cpu().numpy())
                        for k,v in captured.items():features[k].append(v[:len(rr)].cpu().numpy())
                    torch.cuda.synchronize()
                    self.completed_model_batches+=1
                finally:
                    for handle in batch_handles:handle.remove();self.handles.remove(handle)
        finally:
            for handle in self.handles:handle.remove()
            self.handles=[]
        return dict(mode=self.candidate_binding['mode'],scientifically_qualified=False,downstream_eligible=False,
            candidate_checkpoint_id=self.candidate_binding['checkpoint_id'],candidate_adapter_sha256=self.candidate_binding['adapter_sha256'],
            candidate_route_id=self.candidate_binding['route_id'],ids=[r['id'] for r in rows],sequence_sha256=[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows],physical_batch_size=8,logical_batch_size=logical_batch_size,filler_ids=[],hook_calls=calls,features={k:np.concatenate(v) for k,v in features.items()},adapter_branch_calls=branches,**{k:np.concatenate(v) for k,v in outputs.items()})

    def close(self):
        import torch
        import torch.distributed as dist
        from megatron.core import parallel_state
        for h in self.handles:h.remove()
        self.handles=[]; self.model=None
        if parallel_state.model_parallel_is_initialized():parallel_state.destroy_model_parallel()
        if dist.is_initialized():dist.destroy_process_group()
        torch.cuda.empty_cache()
