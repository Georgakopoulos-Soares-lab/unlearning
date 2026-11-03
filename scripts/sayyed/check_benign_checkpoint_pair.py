"""CPU-only integrity check for the supplied benign evaluation model pair."""
import argparse,json,hashlib,time
from pathlib import Path
import torch
import torch.distributed.checkpoint as dcp
from torch.distributed.checkpoint import FileSystemReader
from torch.distributed.checkpoint.metadata import TensorStorageMetadata

def load(path, keys=None):
    reader=FileSystemReader(path);meta=reader.read_metadata()
    wanted={k:v for k,v in meta.state_dict_metadata.items() if isinstance(v,TensorStorageMetadata) and not k.startswith('optimizer') and '_extra_state' not in k}
    if keys is not None:
        missing=set(keys)-set(wanted)
        if missing:raise ValueError(f'Missing model tensors: {sorted(missing)}')
        wanted={k:wanted[k] for k in keys}
    state={k:torch.empty(v.size,dtype=v.properties.dtype,device='cpu') for k,v in wanted.items()}
    dcp.load(state_dict=state,storage_reader=reader,no_dist=True)
    for k,v in state.items():
        if not torch.isfinite(v).all():raise ValueError('Nonfinite model tensor '+k)
    return state

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True);ap.add_argument('--post',required=True);ap.add_argument('--output',required=True);args=ap.parse_args()
    torch.set_num_threads(4);started=time.monotonic();base=load(args.base);post=load(args.post,base)
    differences={}
    for k,b in base.items():
        v=post[k]
        if b.shape!=v.shape:raise ValueError('Shape mismatch '+k)
        differences[k]=dict(shape=list(b.shape),dtype=str(b.dtype),equal=torch.equal(b,v),max_abs_difference=float((b.float()-v.float()).abs().max()))
    report=dict(base=args.base,post=args.post,model_tensor_count=len(base),parameters=sum(x.numel() for x in base.values()),all_finite=True,changed_tensors=sum(not v['equal'] for v in differences.values()),tensors=differences,wall_seconds=time.monotonic()-started,gpu_seconds=0,scope='Backbone tensor integrity; not successful forward loading or parent lineage proof')
    Path(args.output).write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='tensors'},flush=True)
if __name__=='__main__':main()
