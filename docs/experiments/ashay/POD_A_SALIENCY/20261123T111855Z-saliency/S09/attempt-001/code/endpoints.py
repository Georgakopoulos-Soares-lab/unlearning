"""Source-bound compact endpoints; no inference, fitting, new draws, sequences or test access."""
from s09_common import *
import numpy as np, shutil, functools,sys, fcntl,time
from reference_rank_metrics import bootstrap_metrics
from reference_pairwise_metrics import metrics as independent_metrics

@functools.lru_cache(maxsize=6)
def metadata(t):
 root=stage('S04/attempt-001/metadata-inputs');rr=read(root/(t+'-dev-metadata.json'));binding=read(public('S04/attempt-001/COHORT_REFERENCE_BINDINGS.json'));co=binding['cohorts'][t]['dev'];assert digest(rr)==co['ordered_metadata_sha256'];dp=root/'draws'/(t+'-dev.npz');db=next(x for x in binding['draws'] if x['task']==t);assert sha(dp)==db['file_sha256']
 y=np.array([r['label'] for r in rr]);groups=[r['group'] for r in rr];names,inverse=np.unique(groups,return_inverse=True)
 with np.load(dp,allow_pickle=False) as z:
  assert z['ids'].tolist()==[r['id'] for r in rr] and z['group_names'].tolist()==names.tolist() and np.array_equal(z['row_groups'],inverse);draw=z['group_draws'];assert draw.shape==(2000,len(names)) and hashlib.sha256(draw.tobytes()).hexdigest()==db['draw_array_C_order_bytes_sha256']
 # Separate implementations of original group multiplicity and class-support validity.
 counts=np.array([np.bincount(row,minlength=len(names)) for row in draw]);weights=counts[:,inverse].astype(float);classes=np.array(co['class_order']);valid=np.all(np.stack([weights[:,y==k].sum(1)>0 for k in classes]),axis=0)
 group_support=np.zeros((len(names),len(classes)),dtype=np.int32)
 for i,label in enumerate(y):group_support[inverse[i],np.where(classes==label)[0][0]]+=1
 independently_valid=(group_support[draw].sum(1)>0).all(1);assert np.array_equal(valid,independently_valid)
 out=A/'endpoints/inputs';out.mkdir(parents=True,exist_ok=True)
 for p in [root/(t+'-dev-metadata.json'),dp]:
  dest=out/p.name
  if not dest.exists():shutil.copy2(p,dest)
 b={'task':t,'split':'dev','class_order':co['class_order'],'cohort_sha256':co['ordered_metadata_sha256'],'draw_sha256':db['file_sha256'],'row_order_sha256':digest([r['id'] for r in rr]),'group_order_sha256':digest(groups),'sample_count':len(rr),'group_count':len(names),'valid_mask_sha256':hashlib.sha256(valid.tobytes()).hexdigest()}
 return rr,y,classes,np.concatenate([np.ones((1,len(y))),weights]),valid,b

def write_shard(root,entries,points,vectors,masks,receipt):
 root.mkdir(parents=True,exist_ok=True);points=np.array(points,dtype=float);vectors=np.array(vectors,dtype=float);masks=np.array(masks,dtype=bool)
 assert len(entries)==len({r['endpoint_id'] for r in entries})==len(points) and vectors.shape==masks.shape==(len(points),2000)
 tmp=root/'statistics.partial.npz';np.savez_compressed(tmp,points=points,draws=vectors,valid=masks);os.replace(tmp,root/'statistics.npz');jsonl(root/'INDEX.jsonl',entries);save(root/'COMPLETE.json',dict(status='VERIFIED',entries=len(entries),files={n:sha(root/n) for n in ['statistics.npz','INDEX.jsonl']},**receipt))

def references(t):
 root=A/'endpoints/references'/t
 if (root/'COMPLETE.json').exists():print('REUSE_REFERENCE_ENDPOINTS',t,flush=True);return
 rr,y,classes,w,valid,b=metadata(t);allrefs=read(C/'REFERENCE_RECOVERY_RECEIPT.json')['members'];entries=[];points=[];vectors=[];masks=[];worst={'max_abs_residual':0.0};started=time.monotonic()
 for num,entry in enumerate(v for v in allrefs if v['frozen_binding']['task']==t):
  ref=entry['frozen_binding'];rid=entry['reference_id'];p=A/entry['relative_path'];assert sha(p)==ref['sha256']
  with np.load(p,allow_pickle=False) as z:
   for k,field in [('ids','id'),('labels','label'),('groups','group')]:assert z[k].tolist()==[r[field] for r in rr],(rid,k)
   assert z['classes'].tolist()==classes.tolist();prob=z[ref['probability_selector']]
  assert prob.shape==(len(rr),len(classes)) and np.isfinite(prob).all() and np.all((prob>=0)&(prob<=1)) and np.allclose(prob.sum(1),1,atol=1e-12,rtol=0)
  produced,pm=bootstrap_metrics(y,prob,classes,w);checked,vm=independent_metrics(y,prob,classes,w);assert pm[0] and vm[0] and np.array_equal(pm,vm) and np.array_equal(pm[1:],valid)
  for m in METRICS:
   a=produced[MAP[m]];q=checked[MAP[m]];assert np.array_equal(np.isfinite(a),pm) and np.array_equal(np.isfinite(q),vm);diff=np.abs(a[pm]-q[vm]);mx=float(diff.max());assert mx<=1e-12,(rid,m,mx)
   if mx>worst['max_abs_residual']:worst={'max_abs_residual':mx,'reference_id':rid,'metric':m,'coordinate':int(np.flatnonzero(pm)[int(np.argmax(diff))])}
   values=a[1:];ci=np.quantile(values[valid],[.025,.975],method='linear').tolist() if valid.any() else [None,None]
   entries.append(dict(b,endpoint_id=rid+'|'+m,metric=m,reference_id=rid,reference_type='DNA_control' if 'control' in ref else 'base_reference',reference_label=ref.get('control','original_base'),representation=ref.get('representation'),seed=ref['cv_seed'],candidate=None,policy='original_qualified_reference',source_sha256=ref['sha256'],head_sha256=ref['head_sha256'],estimate=float(a[0]),ci_low=ci[0],ci_high=ci[1],bootstrap_vector_sha256=hashlib.sha256(values.tobytes()).hexdigest(),frozen_reference_binding_sha256=digest(ref)))
   points.append(a[0]);vectors.append(values);masks.append(valid)
  if num%6==0:print('REFERENCE_QUALIFIED',t,num+1,'worst',worst['max_abs_residual'],flush=True)
 write_shard(root,entries,points,vectors,masks,{'role':'Exact restored DEV probabilities, rank producer vs pairwise independently computed metrics; all2001weights,5metrics','worst':worst,'new_fits':0,'wall_seconds':time.monotonic()-started});print('REFERENCE_ENDPOINTS_VERIFIED',t,len(entries),flush=True)

def targets(candidate,t):
 root=A/'endpoints'/candidate/t
 if (root/'COMPLETE.json').exists():print('REUSE_TARGET_ENDPOINTS',candidate,t,flush=True);return
 rr,y,classes,w,valid,b=metadata(t)
 old=public('S05/attempt-001/candidates')/candidate/'H3_MARGINALS.jsonl' if t=='emp_H3' else public('S07/attempt-001/candidates')/candidate/t/'MARGINALS.jsonl';marg=rows(old);assert len(marg)==780
 release=None if t=='emp_H3' else {x['planned_spec_id']:x for x in rows(public('S08/attempt-001/candidates')/candidate/t/'RELEASE_OVERLAY.jsonl')}
 entries=[];points=[];vectors=[];masks=[];sourcefiles={};cache={}
 for row in marg:
  metric=row['canonical_metric'];r=row['representation'];seed=row['cv_seed'];policy=row['policy'];eid=row['planned_spec_id']
  assert metric['draw_sha256']==b['draw_sha256'] and metric['sample_count']==len(rr) and metric['group_count']==b['group_count']
  if release is None:assert row['release_status']=='VERIFIED'
  else:assert release[eid]['release_status']=='VERIFIED' and release[eid]['canonical_unit']['status']=='VERIFIED'
  pr=stage('S05/attempt-001/candidates')/candidate/'probabilities'/key(r)/('seed'+str(seed))/policy if t=='emp_H3' else stage('S07/attempt-001/candidates')/candidate/'tasks'/t/'probabilities'/key(r)/('seed'+str(seed))/policy
  ck=(r,seed,policy)
  if ck not in cache:
   complete=read(pr/'COMPLETE.json');files=complete['files'];drawbinding=next(x for x in files if x['path']=='draws.npz');dp=pr/'draws.npz';assert dp.stat().st_size==drawbinding['bytes'] and sha(dp)==drawbinding['sha256'];sourcefiles[str(dp)]={'sha256':drawbinding['sha256'],'complete_sha256':sha(pr/'COMPLETE.json')}
   with np.load(dp,allow_pickle=False) as z:cache[ck]={n:z[n] for n in z.files}
  z=cache[ck];v=z[row['distribution_selector']];mask=z[row.get('validity_selector','valid')];assert v.dtype==np.float64 and v.shape==mask.shape==(2000,) and mask.dtype==bool;assert np.array_equal(mask,valid) and np.array_equal(np.isfinite(v),valid);assert hashlib.sha256(v.tobytes()).hexdigest()==row['bootstrap_vector_sha256'] and hashlib.sha256(mask.tobytes()).hexdigest()==row['valid_mask_sha256']
  # Qualified marginal intervals are sanity-checked; reference pairing is independent of marginal interval endpoints.
  ci=np.quantile(v[mask],[.025,.975],method='linear');assert np.allclose(ci,[metric['ci_low'],metric['ci_high']],atol=1e-12,rtol=0)
  entries.append(dict(b,endpoint_id=eid,metric=metric['metric'],candidate=candidate,representation=r,seed=seed,policy=policy,reference_type=None,estimate=metric['estimate'],ci_low=metric['ci_low'],ci_high=metric['ci_high'],bootstrap_vector_sha256=row['bootstrap_vector_sha256'],source_row_sha256=digest(row),source_table_sha256=sha(old) if not entries else entries[0]['source_table_sha256'],source_sha256=metric['source_sha256'],prediction_planned_spec_id=row['prediction_planned_spec_id'],release_overlay_sha256=sha(public('S08/attempt-001/candidates')/candidate/t/'RELEASE_OVERLAY.jsonl') if release is not None and not entries else (entries[0]['release_overlay_sha256'] if entries else None)))
  points.append(metric['estimate']);vectors.append(v);masks.append(mask)
 write_shard(root,entries,points,vectors,masks,{'role':'Reused verifiedS05 orS07+S08overlay; original source vectors rehashed, maskindependentlyderivedfromoriginalgroupdrawmetadata','source_tables':{str(old):sha(old)},'source_files':sourcefiles,'new_fits':0});print('TARGET_ENDPOINTS_ADMITTED',candidate,t,len(entries),flush=True)

if __name__=='__main__':
 with (C/'ENDPOINT_WRITER.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if sys.argv[1]=='references':
   for t in TASKS:references(t)
  elif sys.argv[1]=='targets':
   for candidate in ['candidate_'+str(i).zfill(2) for i in range(1,10)]:
    for t in TASKS:targets(candidate,t)
  else:raise ValueError('Unknown bounded unit mode')
