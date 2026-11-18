"""Strict model-only native DCP loading; optimizer/TE metadata exclusions are typed and explicit."""
from pathlib import Path
import math,json,pickle,hashlib

def restricted_metadata_load(stream):
 import torch
 from torch.distributed.checkpoint import metadata as md
 from torch.distributed.checkpoint.filesystem import _StorageInfo
 allowed={("torch.distributed.checkpoint.metadata",n):getattr(md,n) for n in ["Metadata","TensorStorageMetadata","TensorProperties","_MEM_FORMAT_ENCODING","ChunkStorageMetadata","MetadataIndex","StorageMeta","BytesStorageMetadata"]}
 allowed.update({("torch.distributed.checkpoint.filesystem","_StorageInfo"):_StorageInfo,("torch.serialization","_get_layout"):torch.serialization._get_layout,("torch","Size"):torch.Size})
 allowed.update({("torch",n):getattr(torch,n) for n in ["bfloat16","float32","float16","float64","int64","int32","bool"]})
 class Restricted(pickle.Unpickler):
  def find_class(self,module,name):
   require((module,name) in allowed,"Unsupported checkpoint metadata class: "+module+"."+name)
   return allowed[(module,name)]
 return Restricted(stream).load()

def model_content_digest(state):
 h=hashlib.sha256()
 for key,tensor in sorted(state.items()):
  h.update(json.dumps([key,str(tensor.dtype),list(tensor.shape)],separators=(",",":")).encode()+b"\0")
  h.update(tensor.detach().cpu().contiguous().reshape(-1).view(__import__("torch").uint8).numpy().tobytes())
 return h.hexdigest()
from qualification_contract import require,te_metadata_owner

def validate_extra_state_blob(blob):
 import io,pickle,torch
 require(0<len(blob)<=1024**2,'Serialized metadata size is unsupported')
 value=torch.load(io.BytesIO(blob),map_location='cpu',weights_only=True)
 require(isinstance(value,list) and len(value)==1,'Unsupported nativeTP1 extra-state wrapper')
 value=value[0]
 if value is None:return {'wrapper':'singleton TP1 ShardedObject list','payload':'non-tensor None','learned_tensor_values':0}
 require(isinstance(value,torch.Tensor) and value.dtype==torch.uint8 and value.ndim==1,'Serialized TE metadata is not byte encoding of empty non-tensor state')
 raw=value.numpy().tobytes();require(raw in [b'',pickle.dumps(None),pickle.dumps({})],'Nonempty serialized TE state cannot be omitted')
 return {'wrapper':'singleton TP1 ShardedObject list','payload':'empty uint8 metadata container' if not raw else 'serialized None' if raw==pickle.dumps(None) else 'serialized emptydict','learned_tensor_values':0,'serialized_bytes_sha256':hashlib.sha256(raw).hexdigest()}

def read_extra_state_blob(checkpoint,meta,key,expected_files):
 refs=[storage for index,storage in meta.storage_data.items() if index.fqn==key];require(len(refs)==1,'Expected one native byte-object storage entry')
 storage=refs[0];require(storage.relative_path in expected_files and storage.offset>=0 and 0<storage.length<=1024**2 and storage.offset+storage.length<=expected_files[storage.relative_path],'Metadata storage reference outside selected shard')
 with (Path(checkpoint)/storage.relative_path).open('rb') as f:f.seek(storage.offset);blob=f.read(storage.length)
 require(len(blob)==storage.length,'Truncated metadata byte object');return dict(validate_extra_state_blob(blob),storage_sha256=hashlib.sha256(blob).hexdigest(),storage_bytes=len(blob))

def inventory_and_load(checkpoint,expected_files,model):
 import torch
 import torch.distributed.checkpoint as dcp
 from torch.distributed.checkpoint import FileSystemReader
 from torch.distributed.checkpoint.metadata import TensorStorageMetadata,BytesStorageMetadata
 class SafeReader(FileSystemReader):
  def read_metadata(self):
   from torch.distributed.checkpoint.metadata import StorageMeta
   with self.fs.create_stream(self.fs.concat_path(self.path,".metadata"),"rb") as stream: metadata=restricted_metadata_load(stream)
   if getattr(metadata,"storage_meta",None) is None:metadata.storage_meta=StorageMeta()
   metadata.storage_meta.load_id=self.load_id
   return metadata
 reader=SafeReader(checkpoint);meta=reader.read_metadata();wanted={};excluded=[];tensor_inventory=[];modules=dict(model.named_modules())
 for key,value in meta.state_dict_metadata.items():
  if isinstance(value,TensorStorageMetadata):
   sizes=list(value.size);chunks=value.chunks
   for ch in chunks:require(len(ch.offsets)==len(ch.sizes)==len(sizes) and all(0<=o and n>=0 and o+n<=s for o,n,s in zip(ch.offsets,ch.sizes,sizes)),'Invalid checkpoint tensor chunk bounds')
   require(sum(math.prod(ch.sizes) for ch in chunks)==math.prod(sizes),'Checkpoint chunk coverage differs')
   for i,ch in enumerate(chunks):
    for other in chunks[i+1:]:require(any(a+na<=b or b+nb<=a for a,na,b,nb in zip(ch.offsets,ch.sizes,other.offsets,other.sizes)),'Overlapping checkpoint tensor chunks')
   optimizer=key=='optimizer' or key.startswith('optimizer.');tensor_inventory.append({'key':key,'shape':sizes,'dtype':str(value.properties.dtype),'elements':math.prod(sizes),'chunk_count':len(chunks),'usage':'OPTIMIZER_EXCLUDED' if optimizer else 'MODEL_REQUIRED'})
   if optimizer:excluded.append({'key':key,'type':type(value).__name__,'reason':'Optimizer-only namespace; no conversion or training-state reconstruction'})
   else:require('_extra_state' not in key,'Tensor extra_state cannot be silently omitted');wanted[key]=value
  elif isinstance(value,BytesStorageMetadata):
   reason='Non-model serialized training/provenance metadata; not deserialized into model'
   if '._extra_state' in key:
    owner=key.split('._extra_state',1)[0];require(owner in modules,'Unknown owner for serialized TE extra state');m=modules[owner];compat=False
    if type(m).__module__=='megatron.core.tensor_parallel.layers' and type(m).__name__=='ColumnParallelLinear':
     from megatron.core.tensor_parallel.layers import ColumnParallelLinear
     compat=type(m) is ColumnParallelLinear and m.get_extra_state() is None
    require(te_metadata_owner(m) or compat,'Unknown class for serialized TE extra state');proof=read_extra_state_blob(checkpoint,meta,key,expected_files);reason='Verified singleton native metadata wrapper contains only non-tensor None/emptydict; confirmed TE owner or exact MCore TEcompatibilityNone';excluded.append({'key':key,'type':type(value).__name__,'reason':reason,'empty_non_tensor_payload_proof':proof,'MCore_TE_compatibility_owner':compat});continue
   excluded.append({'key':key,'type':type(value).__name__,'reason':reason})
  else:raise ValueError('Unsupported checkpoint metadata entry type')
 for index,storage in meta.storage_data.items():
  rel=storage.relative_path;require(rel in expected_files,'Native checkpoint references an unselected/missing shard');require(storage.offset>=0 and storage.length>0 and storage.offset+storage.length<=expected_files[rel],'Native storage offset/length out of selected shard bounds')
 state={k:torch.empty(value.size,dtype=value.properties.dtype,device='cpu') for k,value in wanted.items()};dcp.load(state_dict=state,storage_reader=reader,no_dist=True)
 return state,{'format':'PyTorch FileSystemReader model-only DCP','conversion':'NOT_NEEDED','metadata_deserialization':'Exact allowlist of pinned Torch metadata classes; arbitrary globals rejected','model_tensor_content_sha256':model_content_digest(state),'tensor_inventory':tensor_inventory,'excluded_entries':excluded,'native_storage_entries_checked':len(meta.storage_data),'all_model_tensor_chunks_covered':True,'optimizer_values_deserialized':False,'common_train_state_sidecars':'Retrieved/hashed for provenance; not used by model-only native reader; not deserialized'}
