"""Separate scalar endpoint traversal and explicit order-statistic interpolation."""
import math
import numpy as np
def reconstruct(target,reference,target_valid,reference_valid,target_point,reference_point):
 assert len(target)==len(reference)==len(target_valid)==len(reference_valid)==2000
 masks=[];v=[]
 for a,b,am,bm in zip(target,reference,target_valid,reference_valid):
  assert bool(am)==math.isfinite(a) and bool(bm)==math.isfinite(b)
  ok=bool(am) and bool(bm);masks.append(ok);v.append(math.fsum((float(a),-float(b))) if ok else math.nan)
 ordered=sorted(x for x,m in zip(v,masks) if m);bounds=[]
 for probability in [.025,.975]:
  if not ordered:bounds.append(None);continue
  h=(len(ordered)-1)*probability;i=math.floor(h);fraction=h-i;j=min(i+1,len(ordered)-1)
  bounds.append(ordered[i]+fraction*(ordered[j]-ordered[i]))
 return math.fsum((float(target_point),-float(reference_point))),np.array(v),np.array(masks),bounds
def check_binding(spec,target,reference):
 assert target['endpoint_id']==spec['d']
 assert reference['endpoint_id']==(spec['q'] if spec['f']=='anchor_policy_gap' else spec['q']+'|'+spec['m'])
 assert target['task']==reference['task']==spec['t'] and target['metric']==reference['metric']==spec['m']
 for field in ['cohort_sha256','draw_sha256','class_order','row_order_sha256','group_order_sha256']:assert target[field]==reference[field],field+' mismatch'
 assert target['candidate']==spec['c'] and target['representation']==spec['r'] and target['seed']==spec['s'] and target['policy']==spec['p']
 if spec['f']=='anchor_policy_gap':assert reference['candidate']==spec['c'] and reference['representation']==spec['r'] and reference['seed']==spec['s'] and reference['policy']=='fixed_original_base'
 elif spec['f']=='base_reference':assert reference['representation']==spec['r'] and reference['seed']==spec['s']
 else:assert reference['seed']==spec['s'] and reference['reference_type']=='DNA_control'
