"""Independent CPU Gram audit of saved adapter-geometry outputs.

Uses no production geometry functions, model imports, Torch or outcome data.
"""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import resource
import time
import numpy as np

def audit_module(task):
    run,module,points,edges,checkpoints=task;run=Path(run);start=time.process_time();cp={x['id']:x for x in checkpoints};factors={};norm2={};max_fraction=0.;zero=[];negative_roundoff=0
    for row in points:
        key=row['checkpoint']
        with np.load(run/'cache'/(key.replace('/','__')+'.npz'),allow_pickle=False)as z:A=np.array(z[module['A_key']],dtype=np.float64);B=np.array(z[module['B_key']],dtype=np.float64)
        factors[key]=(A,B);gramB=B.T@B;gramA=A@A.T;n2=float(np.trace(gramB@gramA));assert n2>=0;norm2[key]=n2
        measured=float(row['P_norm'])**2;bound=64*np.finfo(float).eps*16*max(abs(n2),1e-30);error=abs(measured-n2);assert error<=bound+1e-24,(key,module['module'],error,bound);max_fraction=max(max_fraction,error/max(bound,1e-300))
        np.testing.assert_allclose(float(row['U_norm']),cp[key]['declared_scale']*float(row['P_norm']),rtol=5e-11,atol=1e-12)
        np.testing.assert_allclose(float(row['P_RMS'])*math.sqrt(B.shape[0]*A.shape[1]),float(row['P_norm']),rtol=5e-11,atol=1e-12)
        singular=np.array(json.loads(row['singular_values']));np.testing.assert_allclose(np.linalg.norm(singular),float(row['P_raw_norm']),rtol=5e-11,atol=1e-12)
        if row['numerical_zero']=='False':
            np.testing.assert_allclose(float(row['stable_rank']),float(row['P_norm'])**2/float(row['P_spectral'])**2,rtol=5e-11,atol=1e-12);assert int(row['energy90_rank'])==int(np.searchsorted(np.cumsum(singular**2),.9*np.sum(singular**2))+1)
        zero.append(dict(checkpoint=key,module=module['module'],A_all_zero=not bool(np.any(A)),B_all_zero=not bool(np.any(B)),product_numerically_zero=row['numerical_zero']=='True'))
    seen={};edge_gram={}
    for row in edges:
        key=row['left'],row['right']
        if key not in seen:
            Ai,Bi=factors[key[0]];Aj,Bj=factors[key[1]];inner=float(np.einsum('ab,ba->',(Bi.T@Bj),(Aj@Ai.T)));si,sj=cp[key[0]]['declared_scale'],cp[key[1]]['declared_scale'];d2=si*si*norm2[key[0]]+sj*sj*norm2[key[1]]-2*si*sj*inner;scale=si*si*norm2[key[0]]+sj*sj*norm2[key[1]]+2*abs(si*sj*inner);bound=64*np.finfo(float).eps*16*max(scale,1e-30)
            assert d2>=-bound,('negative outside roundoff bound',key,module['module'])
            if d2<0:negative_roundoff+=1
            error=abs(float(row['U_distance'])**2-d2);assert error<=bound+1e-24,('distance',key,module['module'],error,bound);max_fraction=max(max_fraction,error/max(bound,1e-300));np.testing.assert_allclose(float(row['U_inner']),si*sj*inner,rtol=5e-11,atol=1e-12)
            seen[key]=tuple(row[k]for k in ['U_distance','P_distance','U_cosine','P_cosine','U_inner','P_inner']);edge_gram[key]=dict(U_distance_squared=d2,U_inner=si*sj*inner,P_distance_squared=d2/(si*si)if si==sj else None,P_inner=inner)
        else:assert seen[key]==tuple(row[k]for k in ['U_distance','P_distance','U_cosine','P_cosine','U_inner','P_inner'])
    return dict(module=module['module'],point_count=len(points),unique_pairs=len(seen),edge_rows=len(edges),max_roundoff_bound_fraction=max_fraction,negative_Gram_distance_within_bound=negative_roundoff,zero_rows=zero,point_gram_norm2=norm2,edge_gram=[dict(left=k[0],right=k[1],**v)for k,v in edge_gram.items()],CPU_process_seconds=time.process_time()-start,peak_RSS_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,worker_pid=os.getpid())

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args();run=args.run;out=args.output;start=time.monotonic();cpu=time.process_time();spec=json.loads((run/'ANALYSIS_SPEC.json').read_text());specsha=hashlib.sha256((run/'ANALYSIS_SPEC.json').read_bytes()).hexdigest()
    def rows(name):
        with(out/name).open()as f:return list(csv.DictReader(f))
    points=rows('MODULE_METRICS.csv');edges=rows('EDGE_METRICS.csv');cp_rows=rows('CHECKPOINT_SUMMARY.csv');global_rows=rows('GLOBAL_EDGE_METRICS.csv');assert len(points)==3600 and len(edges)==8600 and len(cp_rows)==36 and len(global_rows)==86
    assert len({(x['checkpoint'],x['module'])for x in points})==3600 and len({(x['edge_id'],x['module'])for x in edges})==8600
    assert all(x['spec_sha256']==specsha for x in points+edges+cp_rows+global_rows)
    tasks=[(str(run),m,[x for x in points if x['module']==m['module']],[x for x in edges if x['module']==m['module']],spec['checkpoints'])for m in spec['modules']]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn'))as pool:results=list(pool.map(audit_module,tasks))
    for row in cp_rows:
        n2=math.fsum(x['point_gram_norm2'][row['checkpoint']]for x in results);np.testing.assert_allclose(float(row['P_norm'])**2,n2,rtol=5e-11,atol=1e-12);assert row['module_count']=='100'
    for row in global_rows:
        vals=[next(y for y in x['edge_gram']if y['left']==row['left']and y['right']==row['right'])for x in results];d2=math.fsum(x['U_distance_squared']for x in vals);inner=math.fsum(x['U_inner']for x in vals);np.testing.assert_allclose(float(row['U_distance'])**2,d2,rtol=5e-11,atol=1e-12);np.testing.assert_allclose(float(row['U_inner']),inner,rtol=5e-11,atol=1e-12)
        left=next(x for x in cp_rows if x['checkpoint']==row['left']);right=next(x for x in cp_rows if x['checkpoint']==row['right']);ni,nj=float(left['U_norm']),float(right['U_norm']);np.testing.assert_allclose(float(row['U_cosine']),inner/(ni*nj),rtol=5e-11,atol=1e-12);np.testing.assert_allclose(float(row['U_relative_distance']),2*float(row['U_distance'])/(ni+nj),rtol=5e-11,atol=1e-12)
    for name,key,fraction in [('BLOCK_SUMMARY.csv','checkpoint','fraction_U_squared_magnitude'),('TARGET_SUMMARY.csv','checkpoint','fraction_U_squared_magnitude'),('BLOCK_EDGE_SUMMARY.csv','edge_id','fraction_U_squared_distance'),('TARGET_EDGE_SUMMARY.csv','edge_id','fraction_U_squared_distance')]:
        table=rows(name)
        for id in {x[key]for x in table}:np.testing.assert_allclose(math.fsum(float(x[fraction])for x in table if x[key]==id),1.,rtol=5e-11,atol=1e-12)
    zero=[z for x in results for z in x['zero_rows']];zpath=run/'evidence/ZERO_TENSOR_AUDIT.csv'
    with zpath.open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=list(zero[0]),lineterminator='\n');w.writeheader();w.writerows(zero)
    report=dict(status='PASS',spec_sha256=specsha,independent_method='FP64 Gram/trace identities,without importing production point/pair/aggregation functions; dense selected real/synthetic references separately validated',point_checks=sum(x['point_count']for x in results),unique_pair_checks=sum(x['unique_pairs']for x in results),edge_rows_verified=sum(x['edge_rows']for x in results),global_point_checks=36,global_edge_checks=86,negative_Gram_roundoff_cases=sum(x['negative_Gram_distance_within_bound']for x in results),max_fraction_of_predeclared_roundoff_bound=max(x['max_roundoff_bound_fraction']for x in results),zero_A_tensors=sum(x['A_all_zero']for x in zero),zero_B_tensors=sum(x['B_all_zero']for x in zero),numerically_zero_products=sum(x['product_numerically_zero']for x in zero),worker_CPU_process_seconds=sum(x['CPU_process_seconds']for x in results),coordinator_CPU_process_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-start,worker_peak_RSS_max_bytes=max(x['peak_RSS_bytes']for x in results),worker_pids=sorted({x['worker_pid']for x in results}),new_GPU_seconds=0,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (run/'evidence/INDEPENDENT_GRAM_AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
