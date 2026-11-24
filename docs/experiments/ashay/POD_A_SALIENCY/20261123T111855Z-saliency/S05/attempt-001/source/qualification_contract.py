"""Owned A04 rejection/array contracts. Imports have no GPU, network, fit or ledger effects."""
from pathlib import Path
import hashlib,io,json,math,re
import numpy as np
SMOKE_SHA='42d64d32b77e946bc962c32d2b801e485d41a095221af49a492079ff0f76fd30'
ALIASES=['base', 'candidate_01', 'candidate_02', 'candidate_03', 'candidate_04', 'candidate_05', 'candidate_06', 'candidate_07', 'candidate_08', 'candidate_09'];VARIANTS=['logical1','logical8','repeat8'];LAYERS=[f'decoder_layer_{i}' for i in range(25)]+['final_norm'];HOOKS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm']

def require(v,msg):
 if not v:raise ValueError(msg)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def validate_rows(rows):
 require(len(rows)==12,'Exactly12 frozen training rows required');require(len({r['id'] for r in rows})==12,'Duplicate/misaligned occurrence IDs')
 for r in rows:
  require(r['split']=='train','Held-out row rejected before model inference');s=r['sequence'];require(isinstance(s,str) and 2<=len(s)<=1000 and not set(s)-set('ACGTN'),'Unsupported frozen preprocessing/alphabet/length');require(isinstance(r['label'],int) and not isinstance(r['label'],bool),'Numeric label schema differs');h=hashlib.sha256(s.encode()).hexdigest();record=r.get('sequence_sha256',r.get('scored_prefix_sha256'));require(h==record,'Sequence digest differs');rc=s.translate(str.maketrans('ACGTN','TGCAN'))[::-1];require(hashlib.sha256(min(s,rc).encode()).hexdigest()==r['exact_rc_group'],'Exact/RC identity differs')
 return rows

def validate_manifest(path,expected_sha=SMOKE_SHA,expected_ids=None):
 require(sha(path)==expected_sha,'Frozen manifest byte hash differs');rows=validate_rows([json.loads(l) for l in Path(path).read_text().splitlines()]);require(expected_ids is None or [r['id'] for r in rows]==expected_ids,'Frozen occurrence order differs');return rows

def owned_path(path,root):
 p=Path(path).resolve();r=Path(root).resolve();require(p.is_relative_to(r) and p!=r,'Protected/unowned output path rejected');return p

def validate_alias(alias,candidate_id,selected):
 require(alias in ALIASES and selected.get(alias)==candidate_id,'Unknown or substituted checkpoint identity')

def check_hook_registry(names,width):require(names==HOOKS and width==1920,'Unexpected hook list/order/width')

def pack(sequences,device='cpu'):
 import torch
 require(1<=len(sequences)<=8,'Invalid logical batch; physical8 required')
 for s in sequences:require(2<=len(s)<=1000 and not set(s)-set('ACGTN'),'Unsupported packer input')
 tokens=torch.full((8,1000),1,dtype=torch.long,device=device);lengths=torch.ones(8,dtype=torch.long,device=device)
 for i,s in enumerate(sequences):tokens[i,:len(s)]=torch.tensor([ord(c) for c in s],dtype=torch.long,device=device);lengths[i]=len(s)
 positions=torch.arange(1000,device=device).expand(8,-1);return tokens,lengths,positions

def validate_batch(tokens,lengths,positions,sequences):
 import torch
 require(tuple(tokens.shape)==tuple(positions.shape)==(8,1000) and tuple(lengths.shape)==(8,),'Batch physical shape differs')
 require(torch.equal(positions,torch.arange(1000,device=positions.device).expand(8,-1)),'Position order differs')
 for i,sequence in enumerate(sequences):
  expected=torch.tensor([ord(ch) for ch in sequence],dtype=torch.long,device=tokens.device)
  require(int(lengths[i])==len(sequence) and torch.equal(tokens[i,:len(sequence)],expected) and bool((tokens[i,len(sequence):]==1).all()),'Actual packed token/row order/length/padding differs')
 require(bool((tokens[len(sequences):]==1).all()) and bool((lengths[len(sequences):]==1).all()),'Filler row tokens/lengths differ')

def pool(output,lengths,width=1920):
 import torch
 h=output[0] if isinstance(output,tuple) else output
 require(h.ndim==3 and tuple(h.shape)==(1000,8,width),'Hook tensor must be seq1000,batch8,width1920');require(bool(((lengths>=1)&(lengths<=1000)).all()),'Invalid nucleotide lengths');require(bool(torch.isfinite(h).all()),'Nonfinite activation');mask=torch.arange(h.shape[0],device=h.device)[:,None]<lengths[None,:];return (h.float()*mask[:,:,None]).sum(0)/lengths[:,None]

def production_loss(logits,tokens,lengths,positions):
 import torch
 require(tuple(logits.shape)==(8,1000,512),'Actual output-head logits shape differs');require(tuple(tokens.shape)==tuple(positions.shape)==(8,1000),'Token/position shape differs');require(bool(torch.isfinite(logits).all()),'Nonfinite output-head logits');loss=torch.nn.functional.cross_entropy(logits[:,:-1].float().reshape(-1,512),tokens[:,1:].reshape(-1),reduction='none').reshape(8,-1);mask=positions[:,1:]<lengths[:,None];counts=mask.sum(1);require(bool(torch.equal(counts,lengths-1)),'Causal shift/mask target count differs');sums=(loss*mask).sum(1);require(sums.dtype==torch.float32 and bool(torch.isfinite(sums).all()),'Invalid LM loss sum');return sums,counts,loss,mask

def check_real_population(ids,expected_ids,features,nll,counts,lengths):
 require(list(ids)==list(expected_ids),'Row order/filler leakage detected');n=len(ids);require(set(features)==set(LAYERS),'Missing/unexpected representation array')
 for k,x in features.items():require(x.shape==(n,1920) and x.dtype==np.float32 and np.isfinite(x).all(),'Feature shape/dtype/finiteness differs: '+k)
 require(nll.shape==(n,) and nll.dtype==np.float32 and np.isfinite(nll).all(),'LM sums shape/dtype/finiteness differs');require(counts.shape==(n,) and np.issubdtype(counts.dtype,np.integer) and np.array_equal(counts,np.asarray(lengths)-1),'LM target counts/filler leakage differs')

def componentwise(observed,reference,atol=1e-4,rtol=1e-5):
 a=np.asarray(observed);b=np.asarray(reference);require(a.shape==b.shape and a.size>0,'Comparison shape/empty denominator differs');require(np.isfinite(a).all() and np.isfinite(b).all(),'Nonfinite comparison');delta=np.abs(a.astype(np.float64)-b.astype(np.float64));bound=atol+rtol*np.abs(b.astype(np.float64));bad=delta>bound;worst=np.unravel_index(int(np.argmax(delta)),delta.shape);rel=np.divide(delta,np.abs(b),out=np.where(delta==0,0.,np.inf),where=b!=0);finite_rel=rel[np.isfinite(rel)];return {'status':'PASS' if not bad.any() else 'FAIL','denominator':int(a.size),'violations':int(bad.sum()),'max_abs_residual':float(delta.max()),'max_scaled_residual':float(np.max(delta/bound)),'max_relative_residual_finite':float(finite_rel.max()) if finite_rel.size else None,'relative_undefined_nonzero_at_reference_zero':int(np.isinf(rel).sum()),'worst_index':[int(i) for i in worst],'worst_observed':float(a[worst]),'worst_reference':float(b[worst]),'worst_allowed_abs_error':float(bound[worst]),'atol':atol,'rtol':rtol,'comparison_direction':'observed versus reference; atol+rtol*abs(reference)'}

def independent_cross_entropy(logits,targets):
 x=np.asarray(logits,dtype=np.float64);y=np.asarray(targets,dtype=np.int64);require(x.ndim==2 and x.shape[1]==512 and y.shape==(len(x),) and np.isfinite(x).all() and np.all((y>=0)&(y<512)),'Invalid actual-logit LM witness');m=x.max(1);return m+np.log(np.exp(x-m[:,None]).sum(1))-x[np.arange(len(y)),y]

def te_metadata_owner(module):return any(cls.__module__.startswith('transformer_engine.pytorch') for cls in type(module).__mro__)

def validate_state(model,state):
 import torch
 expected=model.state_dict();modules=dict(model.named_modules());missing=set(expected)-set(state);unexpected=set(state)-set(expected);allowed=[]
 for key in missing:
  owner,sep,leaf=key.rpartition('.');v=expected[key];m=modules.get(owner);compat=False
  if m is not None and type(m).__module__=='megatron.core.tensor_parallel.layers' and type(m).__name__=='ColumnParallelLinear' and v is None:
   from megatron.core.tensor_parallel.layers import ColumnParallelLinear
   compat=type(m) is ColumnParallelLinear and m.get_extra_state() is None
  require(sep and leaf=='_extra_state' and m is not None and (te_metadata_owner(m) or compat),'Unexplained missing model key: '+key)
  registered=set(dict(model.named_parameters()))|set(dict(model.named_buffers()));require(key not in registered,'Registered tensor cannot be ignored as TE metadata')
  if isinstance(v,torch.Tensor):
   import pickle
   m=modules[owner];require(v.dtype==torch.uint8 and v.ndim==1 and v.detach().cpu().numpy().tobytes() in [pickle.dumps(None),pickle.dumps({})],'Tensor extra state is not exact serialization of non-tensor None/emptydict')
   require(not any(bool(getattr(m,n,False)) for n in ['fp8','fp8_calibration','primary_weights_in_fp8']) and not getattr(m,'fp8_meta',{}).get('fp8_checkpoint',False),'Nonempty FP8 state cannot be omitted')
   metas=getattr(m,'_fp8_metas',None);require(metas is None or isinstance(metas,dict) and all(v is None for v in metas.values()),'Nonempty operation FP8 state cannot be omitted')
  allowed.append({'key':key,'value_type':type(v).__name__,'owner_type':type(modules[owner]).__module__+'.'+type(modules[owner]).__name__,'reason':'Confirmed TE non-tensor metadata; current TE serializes literal None/emptydict into uint8 byte container; no registered parameter/buffer omitted','serialized_payload':('None' if v.numel()==4 else 'emptydict') if isinstance(v,torch.Tensor) else 'non-tensor metadata','MCore_output_TE_compatibility_None':compat,'TE_attention_missing_metadata_removed_by_pinned_posthook':any(cls.__module__=='transformer_engine.pytorch.attention.dot_product_attention.dot_product_attention' and cls.__name__=='DotProductAttention' for cls in type(m).__mro__)})
 require(not unexpected,'Unexpected model tensor/state keys: '+str(sorted(unexpected)));promotions=[];inventory=[]
 for key,value in state.items():
  require(isinstance(value,torch.Tensor) and isinstance(expected[key],torch.Tensor),'Non-tensor supplied as model tensor');target=expected[key];require(value.shape==target.shape,'Model tensor shape mismatch: '+key);require(bool(torch.isfinite(value).all()),'Nonfinite model tensor: '+key)
  if value.dtype!=target.dtype:require(value.dtype==torch.bfloat16 and target.dtype==torch.float32,'Forbidden model dtype change: '+key);promotions.append({'key':key,'from':str(value.dtype),'to':str(target.dtype),'policy':'BF16 to FP32 value-preserving only'})
  inventory.append({'key':key,'shape':list(value.shape),'checkpoint_dtype':str(value.dtype),'model_dtype':str(target.dtype),'elements':value.numel()})
 return {'model_tensor_count':len(state),'model_tensor_elements':sum(v.numel() for v in state.values()),'allowed_missing_non_tensor_metadata':allowed,'unexpected':[],'dtype_promotions':promotions,'tensors':inventory}

def check_loaded_values(model,state):
 import torch
 observed=model.state_dict();checked=0
 for key,value in state.items():
  target=observed[key].detach().cpu();want=value if target.dtype==value.dtype else value.to(target.dtype);require(torch.equal(target,want),'Loaded tensor values differ: '+key);checked+=1
 return checked


def validate_actual_loading(missing,unexpected,report):
 expected={r['key'] for r in report['allowed_missing_non_tensor_metadata'] if not r.get('MCore_output_TE_compatibility_None',False) and not r.get('TE_attention_missing_metadata_removed_by_pinned_posthook',False)}
 require(set(missing)==expected and not unexpected,'Actual load-state exceptions differ from exact prevalidated metadata and pinned MCore default-None hook')
 return {'actual_missing_non_tensor_metadata':list(missing),'actual_unexpected':list(unexpected),'MCore_compatibility_None_added_by_pinned_load_hook':[r['key'] for r in report['allowed_missing_non_tensor_metadata'] if r.get('MCore_output_TE_compatibility_None',False)],'TE_attention_empty_metadata_suppressed_by_pinned_post_hook':[r['key'] for r in report['allowed_missing_non_tensor_metadata'] if r.get('TE_attention_missing_metadata_removed_by_pinned_posthook',False)]}


def corpus_likelihood(loss_sums,valid_counts):
 """Preserve inherited float32 row sums/float64 corpus ratio, including overflow."""
 sums=np.asarray(loss_sums);counts=np.asarray(valid_counts)
 require(sums.ndim==counts.ndim==1 and sums.shape==counts.shape and sums.size>0,'LM aggregate population differs')
 require(np.isfinite(sums).all() and np.isfinite(counts).all() and np.all(counts>=0),'Nonfinite/negative LM aggregate input')
 denominator=counts.astype(np.float64).sum();require(denominator>0,'No valid LM target denominator')
 nll=float(sums.astype(np.float64).sum()/denominator);require(np.isfinite(nll),'Nonfinite LM corpus NLL')
 with np.errstate(over='ignore',invalid='ignore'):ppl=float(np.exp(nll))
 reason=None
 if not np.isfinite(ppl):ppl=None;reason='exp(corpus NLL) exceeds finite float64 range; finite NLL preserved'
 return nll,ppl,reason


def validate_tied_weight_contract(model,state):
 """Check native tied/untied head structure, beyond equality of saved values."""
 import torch
 flag=getattr(model,'share_embeddings_and_output_weights',None)
 require(type(flag) is bool,'Unspecified input/output weight sharing policy')
 embedding=model.embedding.word_embeddings.weight;head=getattr(model.output_layer,'weight',None)
 require(isinstance(embedding,torch.Tensor),'Native input embedding weight absent')
 if flag:
  shared=model.shared_embedding_or_output_weight();require(shared is embedding,'Tied forward head does not use actual input embedding')
  require(head is None or head.untyped_storage().data_ptr()==embedding.untyped_storage().data_ptr(),'Declared tied output head has independent storage')
 else:
  require(isinstance(head,torch.Tensor),'Untied output head weight absent')
  require(head.untyped_storage().data_ptr()!=embedding.untyped_storage().data_ptr(),'Declared untied head unexpectedly shares embedding storage')
 require('embedding.word_embeddings.weight' in state,'Checkpoint embedding identity absent')
 require(flag or 'output_layer.weight' in state,'Checkpoint untied output-head identity absent')
 aliases={}
 for name,p in model.named_parameters(remove_duplicate=False):
  if p.numel():aliases.setdefault(p.untyped_storage().data_ptr(),[]).append(name)
 return {'status':'PASS','share_embeddings_and_output_weights':flag,'forward_head_uses_embedding':flag,'output_layer_omits_duplicate_parameter':head is None,'checkpoint_embedding_present':True,'checkpoint_separate_head_present':'output_layer.weight' in state,'aliased_parameter_name_groups':[n for n in aliases.values() if len(n)>1],'embedding_shape':list(embedding.shape),'registered_tensor_values_checked_separately':True}
