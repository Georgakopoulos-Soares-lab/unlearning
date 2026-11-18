"""Same qualified architecture/loading/forward primitives; A06 orchestration only."""
from pathlib import Path
import dataclasses,json,time
from qualification_contract import *
from native_loader import inventory_and_load
def load_model(checkpoint,assets,out,expected_content):
 import torch,torch.distributed as dist,yaml
 from tokenizers import Tokenizer
 from megatron.core import parallel_state,tensor_parallel
 from megatron.core.transformer.enums import AttnBackend
 from bionemo.evo2.models.evo2_provider import Hyena1bModelProvider
 from production_contract import put
 torch.set_num_threads(4);config=yaml.safe_load((checkpoint/'run_config.yaml').read_text());require(isinstance(config,dict) and isinstance(config.get('model'),dict),'Unsupported model config schema');supplied=config['model'];require(supplied['num_layers']==25 and supplied['hidden_size']==1920,'Unexpected selected architecture');tokenizer=Tokenizer.from_file(str(checkpoint/'tokenizer.json'))
 for s in ['A','C','G','T','N','ACGTN']:require(tokenizer.encode(s).ids==[ord(ch) for ch in s],'Tokenizer ordinal DNA/no-BOS/EOS identity differs')
 allowed={f.name for f in dataclasses.fields(Hyena1bModelProvider) if f.init};kwargs={k:v for k,v in supplied.items() if k in allowed and (isinstance(v,(str,int,float,bool)) or v is None)};overrides={'attention_backend':AttnBackend.unfused,'vocab_size':512,'params_dtype':torch.bfloat16,'pipeline_dtype':torch.bfloat16,'bf16':True,'use_cpu_initialization':True,'perform_initialization':False,'recompute_granularity':None,'recompute_method':None,'recompute_num_layers':None,'seq_length':1000};kwargs.update(overrides)
 torch.cuda.set_device(0);torch.cuda.reset_peak_memory_stats();init_file=out/'distributed_init';dist.init_process_group('nccl',init_method='file://'+str(init_file.resolve()),rank=0,world_size=1);parallel_state.initialize_model_parallel(tensor_model_parallel_size=1,pipeline_model_parallel_size=1);tensor_parallel.model_parallel_cuda_manual_seed(42);t=time.monotonic();provider=Hyena1bModelProvider(**kwargs);provider.finalize();model=provider.provide();timing={'architecture_instantiation_seconds':time.monotonic()-t}
 t=time.monotonic();state,native=inventory_and_load(checkpoint,{x['name']:x['bytes'] for x in assets if x['name'].endswith('.distcp')},model);timing['CPU_native_model_only_load_seconds']=time.monotonic()-t;require(native['model_tensor_content_sha256']==expected_content,'Native model content differs from approved checkpoint');model=model.to(device='cuda');report=validate_state(model,state);missing,unexpected=model.load_state_dict(state,strict=False);report.update(validate_actual_loading(missing,unexpected,report));report.update(status='PASS',native=native,all_loaded_tensor_values_exactly_checked=check_loaded_values(model,state));put(out/'LOADING.json',report);del state;model.eval();model.requires_grad_(False);require(not model.training and not any(p.requires_grad for p in model.parameters()),'Model training/gradient enabled')
 specs=[(f'decoder_layer_{i}',f'decoder.layers.{i}',m) for i,m in enumerate(model.decoder.layers)]+[('final_norm','decoder.final_norm',model.decoder.final_norm)];check_hook_registry([n for k,n,m in specs],model.config.hidden_size);return model,tokenizer,specs,timing
def forward(model,specs,rows,tokenizer,witness=False):
 import torch,numpy as np
 for r in rows:require(tokenizer.encode(r['sequence']).ids==[ord(ch) for ch in r['sequence']],'Actual sequence tokenization differs')
 tokens,lengths,positions=pack([r['sequence'] for r in rows],device='cuda');validate_batch(tokens,lengths,positions,[r['sequence'] for r in rows]);captured={};fires={}
 def make_hook(key):
  def capture(module,inputs,output):fires[key]=fires.get(key,0)+1;require(fires[key]==1,'Hook fired more than once');captured[key]=pool(output,lengths,1920)
  return capture
 handles=[m.register_forward_hook(make_hook(k)) for k,n,m in specs]
 try:
  torch.cuda.synchronize();start=time.monotonic()
  with torch.inference_mode():
   logits=model(input_ids=tokens,position_ids=positions,attention_mask=None);require(set(captured)==set(LAYERS) and all(fires.get(k)==1 for k in LAYERS),'Missing/repeated hook capture');sums,counts,loss,mask=production_loss(logits,tokens,lengths,positions);features={k:captured[k][:len(rows)].cpu().numpy() for k in LAYERS};nll=sums[:len(rows)].cpu().numpy();ntokens=counts[:len(rows)].cpu().numpy();wit=[]
   if witness:
    for local,r in enumerate(rows):
     take=np.arange(len(r['sequence'])-1);ix=torch.as_tensor(take,device='cuda');wit.append({'logits':logits[local,ix].float().cpu().numpy(),'targets':tokens[local,ix+1].cpu().numpy(),'losses':loss[local,ix].cpu().numpy(),'row_id':r['id']})
  torch.cuda.synchronize();elapsed=time.monotonic()-start
 finally:
  for h in handles:h.remove()
 return features,nll,ntokens,wit,elapsed
