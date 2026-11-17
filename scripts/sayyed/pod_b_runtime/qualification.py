"""Resumed B04 native qualification; explicit modes and aggregate budget.

Call `run --plan ... --case ... --output ...` from the pinned isolated interpreter.
Engineering arrays never enter a scientifically qualified cache namespace.
"""
from __future__ import annotations
import argparse
import copy
import json
import os
from pathlib import Path
import sys
import time
import traceback
import numpy as np
from .contracts import (require, validate_forward, numeric_comparison, independent_lm_reduction,
                        adapter_activity, validate_algebra_evidence, file_sha)
from .budget import run_budgeted, worker_guard, ENGINEERING, SCIENTIFIC
from .modes import preflight, ROUTE_KEYS
from .gate import save_result,load_result


def compare(actual,reference,rows,contract, *, hooks=True):
    validate_forward(actual,rows,contract,hooks=hooks)
    validate_forward(reference,rows,contract,hooks=hooks)
    checks=[dict(name='exact_'+k,pass_=bool(np.array_equal(actual[k],reference[k]))) for k in ['tokens','positions','target_mask','n_tokens']]
    for x in checks:x['pass']=x.pop('pass_')
    if hooks:checks += [numeric_comparison(actual['features'][k],reference['features'][k],k) for k in contract['layers']]
    checks += [numeric_comparison(actual[k],reference[k],k) for k in ['logits','nll_sum']]
    return dict(pass_=all(x['pass'] for x in checks),checks=checks)


def without_hooks(result):
    return dict(result,features={},hook_calls={})


def native_algebra(model):
    """Controlled dyadic CPU-oracle trace through actual native GPU adapter/wrapper.

    The base fixture intentionally returns normalized input distinct from x and
    a separate bias. Native all100 branch execution is checked independently.
    """
    import torch
    from megatron.bridge.peft.utils import ParallelLinearAdapter
    from megatron.bridge.peft.lora_layers import LoRALinear
    cfg=copy.copy(model.config);cfg.params_dtype=torch.float64;cfg.use_cpu_initialization=False
    cfg.perform_initialization=True;cfg.sequence_parallel=False;cfg.bf16=False;cfg.fp16=False
    adapter=ParallelLinearAdapter(4,3,16,'B04.tiny_native',activation='identity',norm_type=None,
        model_parallel_config=cfg,alpha=32,dropout=.1,dropout_position='pre',input_is_parallel=False,
        disable_sequence_parallel_comm=True)
    a=torch.arange(64,dtype=torch.float64,device='cuda').reshape(16,4)%5/8
    b=torch.arange(48,dtype=torch.float64,device='cuda').reshape(3,16)%7/16
    adapter.linear_in.weight.copy_(a);adapter.linear_out.weight.copy_(b)
    x=torch.tensor([[[.5,-.5,1.,2.]]],device='cuda',dtype=torch.float64)
    norm=x/2+.25;base=torch.tensor([[[2.,4.,8.]]],device='cuda',dtype=torch.float64)
    bias=torch.tensor([.25,-.5,1.],device='cuda',dtype=torch.float64)
    class ControlledBase(torch.nn.Module):
        def forward(self,x):return base,bias,norm
    wrapper=LoRALinear(ControlledBase(),adapter);wrapper.eval();wrapper.requires_grad_(False)
    out,returned_bias=wrapper(x);branch=adapter(norm)
    evidence=dict(normalized_input=norm.cpu().numpy().reshape(1,4).tolist(),linear_in=a.cpu().numpy().tolist(),
        linear_out=b.cpu().numpy().tolist(),alpha=32,rank=16,base_without_bias=base.cpu().numpy().reshape(1,3).tolist(),bias=bias.cpu().numpy().tolist(),branch_output=branch.cpu().numpy().reshape(1,3).tolist(),combined_with_bias=(out+returned_bias).cpu().numpy().reshape(1,3).tolist(),eval_mode=not wrapper.training,dropout_applied=False)
    validate_algebra_evidence(evidence)
    wrapper.disable_adapter_layers();disabled,disabled_bias=wrapper(x)
    require(torch.equal(disabled,base) and torch.equal(disabled_bias,bias),'ADAPTER_ALGEBRA','Native disable/bias semantics')
    return dict(status='PASS_TINY_NATIVE_GPU_ALGEBRA',scope='Actual native ParallelLinearAdapter and LoRALinear; controlled base, not whole-model equivalence',evidence=evidence)


def worker(plan,case,directory,phase):
    binding,rows,policy,key=preflight(plan,case)
    worker_guard()
    from .native import NativeBackend
    import torch
    torch.set_grad_enabled(False)
    backend=NativeBackend(directory);backend.training_rows=rows
    result=dict(mode=plan['mode'],scientifically_qualified=False,downstream_eligible=False,
        checkpoint_id=case,reference_policy=policy,cache_key=key,phase=phase,gates={})
    def persist():
        (directory/'RESULT.json').write_text(json.dumps(result,indent=2))
    def save(name,value):return save_result(directory,name,value)
    try:
        with torch.inference_mode():
            backend.load(binding)
            result['contract']=backend.contract
            result['loaded_state']=dict(status='PASS_EXACT_PARENT_ADAPTER_AND_BUFFERS',snapshot=str(directory/'load_01.json'))
            principal=backend.forward(rows,logical_batch_size=8,hooks=True)
            validate_forward(principal,rows,backend.contract)
            adapter_activity(principal,dict(adapter_tensor_specs={r['key']:r for r in backend.expected_adapter}))
            result['principal']=save('principal',principal)
            result['gates']['schema_all26_full_vocabulary_train12_filler_exclusion']=dict(pass_=True)
            result['gates']['all100_native_adapter_branch_execution']=dict(pass_=True,calls=principal['adapter_branch_calls'])
            _,lm=independent_lm_reduction(principal)
            result['gates']['independent_float64_lm_diagnostic']=dict(pass_=lm['pass'],checks=[lm],canonical_dtype_unchanged='float32')
            result['actual_snapshot']=backend.snapshot();persist()
            if phase=='matrix':
                result['native_algebra']=native_algebra(backend.model)
                result['gates']['native_normalized_input_scale_bias_eval_dropout_disable']=dict(pass_=True)
                for name,kwargs in [('repeat',dict(logical_batch_size=8,hooks=True)),('logical1',dict(logical_batch_size=1,hooks=True)),('filler_perturbation',dict(logical_batch_size=8,hooks=True,filler_token=65)),('hookless',dict(logical_batch_size=8,hooks=False))]:
                    other=backend.forward(rows,**kwargs);record=save(name,other)
                    expected=without_hooks(principal) if name=='hookless' else principal
                    result['gates'][name]=dict(compare(other,expected,rows,backend.contract,hooks=name!='hookless'),output=record);persist()
                backend.set_adapter_enabled(False)
                disabled=backend.forward(rows,logical_batch_size=8,hooks=True)
                result['disabled']=save('disabled',disabled)
                result['parent_baseline']=save('plain_parent_baseline',backend.parent_baseline)
                result['gates']['adapter_disabled_vs_plain_same_candidate_parent']=compare(disabled,backend.parent_baseline,rows,backend.contract)
                result['enabled_disabled_effect']=dict(max_logits_change=float(np.max(np.abs(principal['logits']-disabled['logits']))),interpretation='Engineering activity diagnostic only; no performance or information-removal claim')
                backend.set_adapter_enabled(True);persist()
                swap_binding,_,_,_=preflight(plan,binding['swap_checkpoint_id'])
                backend.load(swap_binding)
                swap_result=backend.forward(rows,logical_batch_size=8,hooks=True)
                validate_forward(swap_result,rows,backend.contract)
                result['swap']=save('swap_B',swap_result)
                backend.load(binding)
                aba=backend.forward(rows,logical_batch_size=8,hooks=True)
                result['gates']['A_B_A_same_parent_full_adapter_overwrite']=dict(compare(aba,principal,rows,backend.contract),output=save('swap_A_return',aba))
                after=backend.snapshot()
                require(after['parent_fingerprint']==result['actual_snapshot']['parent_fingerprint'],'PARENT_MUTATION','A-B-A changed backbone/buffers')
                result['gates']['strict_state_after_swap']=dict(pass_=True,snapshot=after)
                if policy=='COMPARE_INDEPENDENT_ORIGINAL':
                    original=load_result(binding['reference'],binding['allowed_read_roots'])
                    result['gates']['independent_original_agreement']=compare(principal,original,rows,backend.contract)
                else:
                    result['original_agreement']=dict(status='NOT_AVAILABLE' if plan['mode']==ENGINEERING else policy,
                        pass_=None,reason='No external agreement claim from self comparison or a different checkpoint')
            result['peak_cuda_memory_bytes']=int(torch.cuda.max_memory_allocated())
            result['all_observed_gates_passed']=all(v['pass_'] for v in result['gates'].values())
            result['status']='ENGINEERING_DIAGNOSTIC_PASS' if result['all_observed_gates_passed'] else 'NATIVE_NUMERICAL_FAILURE'
            if plan['mode']==SCIENTIFIC:result['status']='SCIENTIFIC_GATES_PENDING_FRESH_PROCESS'
            persist()
    except BaseException as exc:
        result['status']='NATIVE_EXECUTION_FAILED';result['error']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());persist();raise
    finally:backend.close()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('command',choices=['run','_worker','preflight']);ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--case',required=True);ap.add_argument('--output',type=Path);ap.add_argument('--phase',choices=['matrix','fresh'],default='matrix');args=ap.parse_args()
    plan=json.loads(args.plan.read_text());binding,rows,policy,key=preflight(plan,args.case)
    if args.command=='preflight':print(json.dumps(dict(status='PASS_MANIFEST_PREFLIGHT_ONLY',policy=policy,scientifically_qualified=False)));return
    directory=args.output.resolve();root=Path(plan['artifact_root']).resolve()
    require(directory.is_relative_to(root/('engineering' if plan['mode']==ENGINEERING else 'scientific')),'MODE_SEPARATION','Disjoint output namespaces required')
    require(not directory.exists(),'OUTPUT_EXISTS',str(directory));directory.mkdir(parents=True)
    if args.command=='_worker':worker(plan,args.case,directory,args.phase);return
    command=[sys.executable,'-m','scripts.sayyed.pod_b_runtime.qualification','_worker','--plan',str(args.plan),'--case',args.case,'--output',str(directory/'worker'),'--phase',args.phase]
    receipt=run_budgeted(command,ledger=root/'GPU_LEDGER.json',mode=plan['mode'],log=directory/'worker.log',label=args.case+':'+args.phase,env=dict(os.environ))
    receipt.update(mode=plan['mode'],scientifically_qualified=False,downstream_eligible=False)
    (directory/'CONTROLLER.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
    if receipt['returncode']!=0:raise SystemExit(2)

if __name__=='__main__':main()
