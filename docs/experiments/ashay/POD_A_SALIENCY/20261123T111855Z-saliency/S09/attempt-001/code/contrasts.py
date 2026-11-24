"""Finite frozen paired comparisons. Production and scalar verification are separate modules."""
from s09_common import *
from paired_producer import paired,favorable
from paired_verifier import reconstruct,check_binding
import numpy as np,sys,fcntl,resource

def load_endpoints(root):
 receipt=read(root/'COMPLETE.json');assert receipt['status']=='VERIFIED'
 for n,h in receipt['files'].items():assert sha(root/n)==h
 ix=rows(root/'INDEX.jsonl')
 with np.load(root/'statistics.npz',allow_pickle=False) as z:p=z['points'];v=z['draws'];m=z['valid']
 assert len(ix)==len(p)==len({x['endpoint_id'] for x in ix}) and v.shape==m.shape==(len(ix),2000)
 return {r['endpoint_id']:(r,p[i],v[i],m[i]) for i,r in enumerate(ix)}

def run_unit(candidate,t):
 assert read(C/'READINESS.json')['status']=='PASS'
 source=read(C/'SOURCE_IDENTITY.json')
 for n,h in source['numerical_files'].items():assert sha(A/'code'/n)==h,'Changed scientific source'
 root=A/'contrasts'/candidate/t
 if (root/'COMPLETE.json').exists():
  receipt=read(root/'COMPLETE.json')
  for n,h in receipt['files'].items():assert sha(root/n)==h
  print('REUSE_VERIFIED_CONTRAST_UNIT',candidate,t,flush=True);return
 end=load_endpoints(A/'endpoints'/candidate/t);end.update(load_endpoints(A/'endpoints/references'/t));specs=[r for r in rows(C/'FROZEN_ADMITTED_KEYS.jsonl') if r['c']==candidate and r['t']==t];assert len(specs)==906 and len({r['id'] for r in specs})==906
 output=[];ledger=[];values=[];masks=[];worst={'max_abs_residual':0.0};attempted=valid_total=0
 for s in specs:
  target=end[s['d']];reference=end[s['q'] if s['f']=='anchor_policy_gap' else s['q']+'|'+s['m']];a,tp,tv,tm=target;b,rp,rv,rm=reference;check_binding(s,a,b)
  p,v,m,ci=paired(tv,rv,tm,rm,tp,rp);q,w,n,cj=reconstruct(tv,rv,tm,rm,tp,rp);assert np.array_equal(m,n) and np.array_equal(np.isfinite(v),m) and np.array_equal(np.isfinite(w),n)
  diffs=np.abs(v[m]-w[n]);mx=float(max(abs(p-q),diffs.max(initial=0),max(abs(x-y) for x,y in zip(ci,cj)) if m.any() else 0));assert mx<=1e-12,(s['id'],mx)
  if mx>worst['max_abs_residual']:worst={'max_abs_residual':mx,'specification_id':s['id'],'draw_coordinate':int(np.flatnonzero(m)[diffs.argmax()]) if m.any() else None}
  count=int(m.sum());attempted+=2000;valid_total+=count
  row=dict(s,estimate=p,ci_low=ci[0],ci_high=ci[1],target_estimate=float(tp),reference_estimate=float(rp),reference_label=b.get('reference_label','fixed_original_base'),favorable_sign=favorable(s['m'],s['f']),bootstrap_attempted=2000,bootstrap_valid=count,bootstrap_invalid=2000-count,common_mask_sha256=hashlib.sha256(m.tobytes()).hexdigest(),draw_sha256=a['draw_sha256'],cohort_sha256=a['cohort_sha256'],sample_count=a['sample_count'],group_count=a['group_count'],target_endpoint_sha256=digest(a),reference_endpoint_sha256=digest(b),paired_vector_sha256=hashlib.sha256(v.tobytes()).hexdigest(),uncertainty='pointwise_exploratory_conditional',missing_reason=None if count else 'ZERO_COMMON_VALID_DRAWS',status='VERIFIED' if count else 'BLOCKED_INFERENTIAL_RELEASE',source_identity_sha256=source['numerical_identity_sha256'])
  # Canonical metric keeps raw metric direction. Policy-gap ordering is explicitly neutral in companion field.
  row['canonical_metric']={'unit_id':s['id'],'reference_unit_id':s['q'],'metric':s['m'],'direction':'lower_better' if s['m']=='cross_entropy' else 'higher_better','estimate':p,'ci_low':ci[0],'ci_high':ci[1],'missing_reason':row['missing_reason'],'sample_count':a['sample_count'],'group_count':a['group_count'],'valid_targets':None,'bootstrap_attempted':2000,'bootstrap_valid':count,'bootstrap_invalid':2000-count,'draw_sha256':a['draw_sha256'],'common_mask_sha256':row['common_mask_sha256'],'uncertainty':'pointwise_exploratory_conditional','source_sha256':source['numerical_identity_sha256']}
  output.append(row);values.append(v);masks.append(m);ledger.append({'id':s['id'],'status':'PASS','point_abs_residual':abs(p-q),'max_draw_abs_residual':float(diffs.max(initial=0)),'max_CI_abs_residual':float(max(abs(x-y) for x,y in zip(ci,cj))) if count else None,'mask_exact':True,'coordinates_attempted':2000,'coordinates_valid':count,'target_endpoint_sha256':digest(a),'reference_endpoint_sha256':digest(b)})
 root.mkdir(parents=True,exist_ok=True);tmp=root/'paired.partial.npz';np.savez_compressed(tmp,draws=np.array(values),valid=np.array(masks));os.replace(tmp,root/'paired.npz');jsonl(root/'CONTRASTS.jsonl',output);jsonl(root/'VERIFICATION.jsonl',ledger)
 files={n:sha(root/n) for n in ['paired.npz','CONTRASTS.jsonl','VERIFICATION.jsonl']};save(root/'COMPLETE.json',{'status':'VERIFIED','specifications':906,'attempted_draw_differences':attempted,'valid_draw_differences':valid_total,'worst':worst,'source_identity_sha256':source['numerical_identity_sha256'],'files':files,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'completed_utc':now()});pub=P/'contrasts'/candidate/t;pub.mkdir(parents=True,exist_ok=True)
 import shutil
 for n in ['CONTRASTS.jsonl','VERIFICATION.jsonl','COMPLETE.json']:shutil.copy2(root/n,pub/n)
 completed=list((A/'contrasts').glob('*/*/COMPLETE.json'));progress('PAIRED_CONTRAST_PRODUCTION',completed_scientific_contrasts=len(completed)*906,remaining_admitted_count=48924-len(completed)*906,last_verified_unit=candidate+'|'+t,next_permitted_action='Continue exact remaining finite S09 units; then reports/figures/private exhaustive regeneration; no S10')
 assert resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<8*1024**3
 print('VERIFIED_CONTRAST_UNIT',candidate,t,906,'draws',attempted,'residual',mx,flush=True)

if __name__=='__main__':
 with (C/'CPU_STAGE.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  for candidate in ['candidate_'+str(i).zfill(2) for i in range(1,10)]:
   for t in TASKS:run_unit(candidate,t)
