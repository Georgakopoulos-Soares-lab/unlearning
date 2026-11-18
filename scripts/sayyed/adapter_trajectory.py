"""CPU-only serialized adapter product geometry; never constructs a model.

Checkpoint metadata is decoded as inert records with an explicit global allowlist.
Only selected tensor chunks are loaded using torch.load(weights_only=True,CPU).
All geometry uses FP64 low-rank algebra. Actual original model state is unbound.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
from pathlib import Path
import pickle
import re
import resource
import time
import numpy as np

class AnalysisError(ValueError):pass

def require(ok,message):
    if not ok:raise AnalysisError(message)

def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def record(path):
    p=Path(path);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))

def write_json(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')

class InertRecord:
    def __new__(cls,*args,**kwargs):
        x=object.__new__(cls);x._args=args;return x
    def __setstate__(self,state):
        if isinstance(state,dict):self.__dict__.update(state)
        else:self._state=state

_STUBS={}
_ALLOWED_META={'Metadata','TensorStorageMetadata','BytesStorageMetadata','TensorProperties','ChunkStorageMetadata','MetadataIndex','StorageMeta','_MEM_FORMAT_ENCODING'}

def safe_layout(value):
    require(value=='torch.strided','Unsupported storage layout');return value

class DescriptorUnpickler(pickle.Unpickler):
    """No classes/functions supplied by a checkpoint are imported or executed."""
    def find_class(self,module,name):
        key=(module,name)
        if module=='torch.distributed.checkpoint.metadata'and name in _ALLOWED_META or module=='torch.distributed.checkpoint.filesystem'and name=='_StorageInfo' or module=='torch.serialization'and name=='_MEM_FORMAT_ENCODING':
            if key not in _STUBS:_STUBS[key]=type('Inert_'+name,(InertRecord,),{})
            return _STUBS[key]
        if module=='torch'and name in {'bfloat16','float32','float64','int64','int32','bool','uint8','float16'}:return 'torch.'+name
        if module=='torch'and name=='Size':return tuple
        if module=='torch.serialization'and name=='_get_layout':return safe_layout
        raise AnalysisError('UNSAFE_METADATA_GLOBAL: '+module+'.'+name)
    def persistent_load(self,pid):raise AnalysisError('Metadata persistent ID prohibited')

def descriptors(path):
    raw=Path(path).read_bytes();require(len(raw)<=2_000_000,'Metadata too large')
    value=DescriptorUnpickler(io.BytesIO(raw)).load()
    require(hasattr(value,'state_dict_metadata')and hasattr(value,'storage_data'),'Metadata schema')
    return value

def model_chunks(meta,schema):
    wanted={k:v for k,v in meta.state_dict_metadata.items()if k in schema}
    model_keys={k for k,v in meta.state_dict_metadata.items()if type(v).__name__=='Inert_TensorStorageMetadata'and not k.startswith('optimizer')and '_extra_state'not in k}
    require(model_keys==set(schema)==set(wanted),'Missing/unpaired/extra adapter keys')
    storage={}
    for index,info in meta.storage_data.items():
        fqn=getattr(index,'fqn',None)
        if fqn in schema:
            offset=tuple(index.offset);require((fqn,offset)not in storage,'Duplicate chunk descriptor')
            storage[fqn,offset]=info
    out={}
    for key,node in wanted.items():
        shape=tuple(schema[key]['shape']);require(tuple(node.size)==shape,'Metadata shape mismatch')
        used=np.zeros(shape,dtype=bool);chunks=[]
        for chunk in node.chunks:
            offset=tuple(chunk.offsets);sizes=tuple(chunk.sizes)
            require(len(offset)==len(sizes)==len(shape)==2 and all(isinstance(x,int)for x in offset+sizes),'Chunk dimensions')
            require(all(0<=o and n>0 and o+n<=s for o,n,s in zip(offset,sizes,shape)),'Chunk bounds')
            sl=tuple(slice(o,o+n)for o,n in zip(offset,sizes));require(not used[sl].any(),'Overlapping tensor chunks');used[sl]=True
            require((key,offset)in storage,'Missing storage chunk');info=storage.pop((key,offset))
            require(info.relative_path=='__0_0.distcp'and isinstance(info.offset,int)and isinstance(info.length,int)and info.offset>=0 and info.length>0,'Storage descriptor bounds/path')
            chunks.append(dict(offset=offset,shape=sizes,file_offset=info.offset,length=info.length))
        require(used.all(),'Incomplete serialized tensor extent');out[key]=chunks
    require(not storage,'Unused model storage chunks')
    return out

def prepare_inputs(spec_path,run):
    import torch
    torch.set_num_threads(1);torch.set_grad_enabled(False)
    require(not torch.cuda.is_initialized(),'CUDA initialized')
    spec=json.loads(Path(spec_path).read_text());run=Path(run);prior=json.loads(Path('/workspace/meeting-artifacts/relearning-benign-v1/CHECKPOINT_REGISTRY.json').read_text())['checkpoints'];prior={x['series']+'/iter_'+str(x['step']).zfill(7):x for x in prior}
    schema={k:dict(shape=m[side+'_shape'],dtype=m['dtype'])for m in spec['modules']for side,k in [('A',m['A_key']),('B',m['B_key'])]}
    results=[];start=time.monotonic();cpu=time.process_time()
    for cp in spec['checkpoints']:
        require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(json.loads((run/'APPROVAL.json').read_text())['forward_CPU_scheduling_cutoff_utc']),'CPU scheduling cutoff')
        root=Path(cp['adapter_root']);payload=root/'__0_0.distcp';meta=root/'.metadata';cfg=root/'run_config.yaml'
        require(sha(payload)==cp['payload_sha256']and sha(meta)==cp['metadata_sha256']and sha(cfg)==cp['config_sha256'],'Input hash mismatch '+cp['id'])
        layout=model_chunks(descriptors(meta),schema);arrays={};aggregate=hashlib.sha256();tensor_records={};logical_bytes=0
        with payload.open('rb')as f:
            for key in sorted(schema):
                tensor=torch.empty(schema[key]['shape'],dtype=torch.bfloat16,device='cpu')
                for chunk in layout[key]:
                    require(chunk['file_offset']+chunk['length']<=payload.stat().st_size,'Storage outside payload')
                    f.seek(chunk['file_offset']);raw=f.read(chunk['length']);part=torch.load(io.BytesIO(raw),map_location='cpu',weights_only=True)
                    require(type(part)is torch.Tensor and part.device.type=='cpu'and tuple(part.shape)==tuple(chunk['shape'])and part.dtype==torch.bfloat16,'Safe tensor chunk schema')
                    tensor[tuple(slice(o,o+n)for o,n in zip(chunk['offset'],chunk['shape']))]=part
                require(bool(torch.isfinite(tensor).all()),'Nonfinite adapter tensor')
                raw=tensor.contiguous().view(torch.uint8).numpy().tobytes();h=hashlib.sha256(raw).hexdigest();require(h==prior[cp['id']]['tensors'][key]['sha256'],'Tensor content hash mismatch')
                aggregate.update(key.encode()+b'\0'+str(tensor.dtype).encode()+b'\0');aggregate.update(json.dumps(list(tensor.shape)).encode()+b'\0'+raw)
                arrays[key]=tensor.float().numpy();logical_bytes+=len(raw);tensor_records[key]=dict(shape=list(tensor.shape),dtype=str(tensor.dtype),sha256=h,chunks=layout[key])
        require(aggregate.hexdigest()==cp['tensor_content_fingerprint'],'Aggregate tensor fingerprint mismatch')
        out=run/'cache'/(cp['id'].replace('/','__')+'.npz');np.savez(out,**arrays)
        result=dict(checkpoint=cp['id'],payload=dict(path=str(payload),sha256=cp['payload_sha256'],bytes=payload.stat().st_size),metadata=dict(path=str(meta),sha256=cp['metadata_sha256']),config_sha256=cp['config_sha256'],tensor_count=len(arrays),tensor_content_fingerprint=aggregate.hexdigest(),serialized_extent='COMPLETE_ALL_DCP_CHUNKS',logical_BF16_bytes=logical_bytes,tensors=tensor_records,cache=record(out),cache_dtype='float32_lossless_BF16_conversion',status='VERIFIED_CPU_BYTES_TENSORS_ONLY',original_job_state_bound=False)
        results.append(result);write_json(run/'evidence'/(cp['id'].replace('/','__')+'_INPUT.json'),result)
        print(json.dumps(dict(phase='INPUT_VERIFIED',checkpoint=cp['id'],tensors=len(arrays),elapsed_seconds=time.monotonic()-start)),flush=True)
        del arrays
    require(not torch.cuda.is_initialized(),'CUDA initialized')
    report=dict(schema='POD_B.adapter_trajectory.inputs.v1',spec_sha256=sha(spec_path),inputs=results,checkpoint_count=len(results),tensor_count=sum(x['tensor_count']for x in results),hash_scope='Each consumed original payload/metadata/config SHA once plus every recovered logical BF16 tensor raw-byte SHA and historical full fingerprint; no parent bytes read',safe_reader='Inert allowlisted metadata records,never actual checkpoint classes; torch.load(weights_only=True,map_location=cpu) per selected model chunk; optimizer chunks not loaded',wall_seconds=time.monotonic()-start,CPU_process_seconds=time.process_time()-cpu,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,CUDA_initialized=False,new_GPU_seconds=0)
    write_json(run/'INPUT_MANIFEST.json',report);return report

def factors(A,B):
    A=np.asarray(A,dtype=np.float64);B=np.asarray(B,dtype=np.float64)
    require(A.ndim==B.ndim==2 and A.shape[0]==B.shape[1]and min(A.shape+B.shape)>0,'Factor orientation/rank')
    require(np.isfinite(A).all()and np.isfinite(B).all(),'Nonfinite factor');return A,B

def singular_values(A,B):
    A,B=factors(A,B);_,RB=np.linalg.qr(B,mode='reduced');_,RA=np.linalg.qr(A.T,mode='reduced')
    return np.linalg.svd(RB@RA.T,compute_uv=False)

def point(A,B,scale=1.):
    A,B=factors(A,B);require(math.isfinite(scale),'Invalid scale');s=singular_values(A,B);raw=float(np.linalg.norm(s));bound=float(64*np.finfo(float).eps*A.shape[0]*float(np.linalg.norm(A))*float(np.linalg.norm(B)));zero=bool(raw<=bound)
    norm=0. if zero else raw;spec=0. if zero else float(s[0]);energy=np.cumsum(s*s)
    return dict(P_norm=norm,P_raw_norm=raw,P_zero_bound=bound,P_spectral=spec,U_norm=abs(scale)*norm,U_spectral=abs(scale)*spec,P_RMS=norm/math.sqrt(B.shape[0]*A.shape[1]),U_RMS=abs(scale)*norm/math.sqrt(B.shape[0]*A.shape[1]),stable_rank=None if zero else norm*norm/(spec*spec),energy90_rank=0 if zero else int(np.searchsorted(energy,.9*energy[-1])+1),numerical_rank=0 if zero else int(np.sum(s>np.finfo(float).eps*max(A.shape+B.shape)*s[0])),singular_values=s.tolist(),numerical_zero=zero,exact_factor_zero=bool(not np.any(A)or not np.any(B)),scale=scale)

def pair(Ai,Bi,Aj,Bj,si=1.,sj=1.,pi=None,pj=None):
    Ai,Bi=factors(Ai,Bi);Aj,Bj=factors(Aj,Bj);require(Ai.shape[1]==Aj.shape[1]and Bi.shape[0]==Bj.shape[0],'Different operator coordinates')
    pi=point(Ai,Bi,si)if pi is None else pi;pj=point(Aj,Bj,sj)if pj is None else pj
    require(pi['scale']==si and pj['scale']==sj,'Cached point scale mismatch')
    if Ai.shape==Aj.shape and Bi.shape==Bj.shape:
        Ad=np.concatenate([sj*Aj-si*Ai,si*Ai],axis=0);Bd=np.concatenate([Bj,Bj-Bi],axis=1);method='DELTA_FACTOR_QR'
    else:Ad=np.concatenate([sj*Aj,si*Ai],axis=0);Bd=np.concatenate([Bj,-Bi],axis=1);method='CONCAT_FACTOR_QR'
    raw=float(np.linalg.norm(singular_values(Ad,Bd)));bound=64*np.finfo(float).eps*max(Ai.shape[0],Aj.shape[0])*max(1.,abs(si)*np.linalg.norm(Ai)*np.linalg.norm(Bi)+abs(sj)*np.linalg.norm(Aj)*np.linalg.norm(Bj))
    exact_same=si==sj and np.array_equal(Ai,Aj)and np.array_equal(Bi,Bj);distance=0. if exact_same else raw
    ni,nj=pi['U_norm'],pj['U_norm'];inner=float(si*sj*np.trace((Bi.T@Bj)@(Aj@Ai.T)))
    if ni+nj==0:
        require(distance<=bound,'Zero-product distance outside roundoff bound');relative=0.;cos=None;reason='BOTH_NUMERICALLY_ZERO'
    else:
        relative=2*distance/(ni+nj);require(relative<=2+5e-11,'Triangle inequality violation');relative=min(2.,relative)
        if ni==0 or nj==0:cos=None;reason='ONE_NUMERICALLY_ZERO'
        else:
            cos=inner/(ni*nj);require(-1-5e-11<=cos<=1+5e-11,'Cosine outside FP64 tolerance');cos=max(-1.,min(1.,cos));reason=None
    return dict(distance=distance,distance_raw=raw,relative_distance=relative,cosine=cos,cosine_unavailable_reason=reason,inner_product=inner,difference_method=method,roundoff_bound=bound,exact_same_factors=exact_same,numerically_indistinguishable=distance<=1e-12+5e-11*max(ni,nj))

def check_cutoff(run):
    approval=json.loads((Path(run)/'APPROVAL.json').read_text())
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(approval['forward_CPU_scheduling_cutoff_utc']),'CPU scheduling cutoff')

def analyze_module(task):
    run,index=task;run=Path(run);check_cutoff(run);start=time.monotonic();cpu=time.process_time()
    spec_path=run/'ANALYSIS_SPEC.json';spec=json.loads(spec_path.read_text());specsha=sha(spec_path);module=spec['modules'][index];f={};points={};meta={x['id']:x for x in spec['checkpoints']};rows=[];edges=[]
    for cp in spec['checkpoints']:
        with np.load(run/'cache'/(cp['id'].replace('/','__')+'.npz'),allow_pickle=False)as data:
            A=np.asarray(data[module['A_key']],dtype=np.float64);B=np.asarray(data[module['B_key']],dtype=np.float64)
        require(list(A.shape)==module['A_shape']and list(B.shape)==module['B_shape'],'Cache shape drift');f[cp['id']]=(A,B);q=point(A,B,cp['declared_scale']);points[cp['id']]=q
        rows.append(dict(spec_sha256=specsha,checkpoint=cp['id'],series=cp['series'],step=cp['step'],job_id=cp['job_id'],family=cp['family'],module=module['module'],block=module['block'],target_type=module['target_type'],m=B.shape[0],n=A.shape[1],rank_factor=A.shape[0],original_dtype='bfloat16',analysis_dtype='float64',payload_sha256=cp['payload_sha256'],tensor_fingerprint=cp['tensor_content_fingerprint'],scope='SERIALIZED_PRODUCT_AND_DECLARED_PARAMETERIZATION_NOT_AUTHENTICATED_ORIGINAL_UPDATE',**q))
    cache={}
    for e in spec['edges']:
        key=(e['left'],e['right'])
        if key not in cache:
            ci,cj=meta[key[0]],meta[key[1]];Ai,Bi=f[key[0]];Aj,Bj=f[key[1]];si,sj=ci['declared_scale'],cj['declared_scale'];q=pair(Ai,Bi,Aj,Bj,si,sj,pi=points[key[0]],pj=points[key[1]])
            if si==sj and si>0:
                dp=q['distance']/si;ip=q['inner_product']/(si*si);rp=q['relative_distance'];cp=q['cosine']
            else:
                z=pair(Ai,Bi,Aj,Bj);dp=z['distance'];ip=z['inner_product'];rp=z['relative_distance'];cp=z['cosine']
            cache[key]=dict(U_distance=q['distance'],P_distance=dp,U_relative_distance=q['relative_distance'],P_relative_distance=rp,U_cosine=q['cosine'],P_cosine=cp,U_inner=q['inner_product'],P_inner=ip,cosine_unavailable_reason=q['cosine_unavailable_reason'],difference_method=q['difference_method'],roundoff_bound=q['roundoff_bound'],exact_same_factors=q['exact_same_factors'],numerical_product_agreement=q['numerically_indistinguishable'],left_scale=si,right_scale=sj)
        edges.append(dict(spec_sha256=specsha,edge_id=e['edge_id'],kind=e['kind'],left=e['left'],right=e['right'],left_step=meta[e['left']]['step'],right_step=meta[e['right']]['step'],left_series=meta[e['left']]['series'],right_series=meta[e['right']]['series'],left_job=meta[e['left']]['job_id'],right_job=meta[e['right']]['job_id'],cross_job=e['cross_job'],module=module['module'],block=module['block'],target_type=module['target_type'],scope='CONDITIONAL_SAME_NOMINAL_COORDINATES'if e['kind']=='common_step_conditional'else'SERIALIZED_OPERATOR_COMPARISON',**cache[key]))
    result=dict(module=module['module'],module_index=index,status='COMPLETE',point_rows=rows,edge_rows=edges,wall_seconds=time.monotonic()-start,CPU_process_seconds=time.process_time()-cpu,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,worker_pid=os.getpid(),source_path=__file__,source_sha256=sha(__file__),GPU_seconds=0)
    write_json(run/'results'/('module_'+str(index).zfill(3)+'.json'),result);return result

def csv_rows(path,rows):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='')as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(v,separators=(',',':'))if isinstance(v,(list,dict))else v for k,v in row.items()})


def verify_owned_output(run,output):
    import subprocess
    approval=json.loads((Path(run)/'APPROVAL.json').read_text());worktree=Path(approval['worktree']).resolve();output=Path(output).resolve()
    require(output==Path(approval['documentation_root']).resolve()and output.is_relative_to(worktree/'docs/experiments/ashay/POD_B'),'Unapproved research output scope')
    def git(*args):return subprocess.check_output(['git','-C',str(worktree),*args],text=True).strip()
    require(Path(git('rev-parse','--show-toplevel')).resolve()==worktree and git('branch','--show-current')=='POD_B'and git('remote','get-url','origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git','Research ownership mismatch')
    require(Path(git('rev-parse','--git-common-dir')).resolve()==Path(approval['git_common_dir']).resolve(),'Git common directory mismatch')

def run_geometry(run,output,workers=4):
    import concurrent.futures
    import multiprocessing
    run=Path(run);output=Path(output);verify_owned_output(run,output);check_cutoff(run);spec=json.loads((run/'ANALYSIS_SPEC.json').read_text());specsha=sha(run/'ANALYSIS_SPEC.json');start=time.monotonic();cpu=time.process_time()
    require(1<=workers<=spec['runtime']['CPU_workers_ceiling'],'Worker ceiling')
    for row in json.loads((run/'INPUT_MANIFEST.json').read_text())['inputs']:require(sha(row['cache']['path'])==row['cache']['sha256'],'Cache changed')
    tasks=[(str(run),i)for i in range(len(spec['modules']))];results=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn'))as pool:
        for result in pool.map(analyze_module,tasks):
            results.append(result);print(json.dumps(dict(phase='MODULE_COMPLETE',module=result['module'],completed=len(results),expected=len(tasks),wall_seconds=time.monotonic()-start)),flush=True)
            write_json(run/'PROGRESS.json',dict(status='IN_PROGRESS',modules_completed=len(results),modules_expected=len(tasks),spec_sha256=specsha,new_GPU_seconds=0,next_stage_authorized=False))
    pointrows=[p for x in results for p in x['point_rows']];edgerows=[p for x in results for p in x['edge_rows']]
    require(len(pointrows)==spec['checkpoint_module_units']and len(edgerows)==spec['edge_module_output_rows'],'Output row counts')
    def publish_csv(name,rows):
        verify_owned_output(run,output);csv_rows(output/name,rows)
    publish_csv('MODULE_METRICS.csv',pointrows);publish_csv('EDGE_METRICS.csv',edgerows)
    checkpoint=[];blocks=[];types=[]
    for cp in spec['checkpoints']:
        rr=[x for x in pointrows if x['checkpoint']==cp['id']];require(len(rr)==spec['module_count'],'Incomplete fixed module set')
        pn=math.sqrt(math.fsum(x['P_norm']**2 for x in rr));un=math.sqrt(math.fsum(x['U_norm']**2 for x in rr));checkpoint.append(dict(spec_sha256=specsha,checkpoint=cp['id'],series=cp['series'],step=cp['step'],job_id=cp['job_id'],family=cp['family'],module_count=len(rr),P_norm=pn,U_norm=un,numerical_zero_modules=sum(x['numerical_zero']for x in rr),exact_factor_zero_modules=sum(x['exact_factor_zero']for x in rr),scope='FIXED_SERIALIZED_MODULE_CONCATENATION_DECLARED_U_NOT_FULL_MODEL'))
        for field,target in [('block',blocks),('target_type',types)]:
            for name in sorted({x[field]for x in rr}):
                v=[x for x in rr if x[field]==name];squared=math.fsum(x['U_norm']**2 for x in v);target.append(dict(spec_sha256=specsha,checkpoint=cp['id'],series=cp['series'],step=cp['step'],group_field=field,group=name,module_count=len(v),P_norm=math.sqrt(math.fsum(x['P_norm']**2 for x in v)),U_norm=math.sqrt(squared),fraction_U_squared_magnitude=None if un==0 else squared/(un*un)))
    cpmap={x['checkpoint']:x for x in checkpoint};global_edges=[];edgeblocks=[];edgetypes=[]
    for e in spec['edges']:
        rr=[x for x in edgerows if x['edge_id']==e['edge_id']];require(len(rr)==spec['module_count'],'Incomplete edge module set');left,right=cpmap[e['left']],cpmap[e['right']];row=dict(spec_sha256=specsha,**e,left_step=left['step'],right_step=right['step'],left_series=left['series'],right_series=right['series'],left_job=left['job_id'],right_job=right['job_id'],module_count=len(rr))
        for q in ['P','U']:
            distance=math.sqrt(math.fsum(x[q+'_distance']**2 for x in rr));inner=math.fsum(x[q+'_inner']for x in rr);ni,nj=left[q+'_norm'],right[q+'_norm'];row[q+'_distance']=distance;row[q+'_relative_distance']=0. if ni+nj==0 else 2*distance/(ni+nj);row[q+'_inner']=inner;row[q+'_cosine']=None if ni*nj==0 else max(-1.,min(1.,inner/(ni*nj)))
        row['all_same_factors']=all(x['exact_same_factors']for x in rr);row['numerical_product_agreement']=row['U_distance']<=1e-12+5e-11*max(left['U_norm'],right['U_norm']);global_edges.append(row)
        for field,target in [('block',edgeblocks),('target_type',edgetypes)]:
            for name in sorted({x[field]for x in rr}):
                v=[x for x in rr if x[field]==name];u2=math.fsum(x['U_distance']**2 for x in v);target.append(dict(spec_sha256=specsha,edge_id=e['edge_id'],kind=e['kind'],left=e['left'],right=e['right'],cross_job=e['cross_job'],group_field=field,group=name,module_count=len(v),P_distance=math.sqrt(math.fsum(x['P_distance']**2 for x in v)),U_distance=math.sqrt(u2),fraction_U_squared_distance=None if row['U_distance']==0 else u2/(row['U_distance']**2)))
    for name,rows in [('CHECKPOINT_SUMMARY.csv',checkpoint),('BLOCK_SUMMARY.csv',blocks),('TARGET_SUMMARY.csv',types),('GLOBAL_EDGE_METRICS.csv',global_edges),('BLOCK_EDGE_SUMMARY.csv',edgeblocks),('TARGET_EDGE_SUMMARY.csv',edgetypes)]:publish_csv(name,rows)
    result=dict(status='COMPLETE',spec_sha256=specsha,payloads=36,modules=100,checkpoint_module_rows=len(pointrows),edge_module_rows=len(edgerows),global_edges=len(global_edges),unique_checkpoint_pairs=spec['unique_checkpoint_pairs'],CPU_workers=workers,worker_pids=sorted({x['worker_pid']for x in results}),worker_CPU_process_seconds=sum(x['CPU_process_seconds']for x in results),coordinator_CPU_process_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-start,worker_peak_RSS_max_bytes=max(x['peak_RSS_bytes']for x in results),new_GPU_seconds=0,scientifically_qualified_models=0,new_heldout_forwards=0,new_fits=0,source_sha256=sha(__file__))
    write_json(run/'GEOMETRY_RESULT.json',result);write_json(run/'PROGRESS.json',dict(status='COMPUTATION_COMPLETE_PENDING_VALIDATION',spec_sha256=specsha,modules_completed=100,modules_expected=100,new_GPU_seconds=0,next_stage_authorized=False));return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('stage',choices=['prepare','run']);p.add_argument('--run',required=True,type=Path);p.add_argument('--output',type=Path);p.add_argument('--workers',type=int,default=4);a=p.parse_args(argv)
    if a.stage=='prepare':prepare_inputs(a.run/'ANALYSIS_SPEC.json',a.run)
    else:
        require(a.output is not None,'Explicit new output scope required');run_geometry(a.run,a.output,a.workers)

if __name__=='__main__':main()
