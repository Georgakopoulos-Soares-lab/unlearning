"""Independent S06 saved-artifact CPU verifier and real S07 typed-matrix consumer. No fitting."""
from s06_contract import *
import numpy as np
import math,argparse,time,resource

def independent(sums,counts,groups=None,draws=None):
 # Python exact summation of the saved FP32 row sums, integer denominators; no producer helper.
 nll=math.fsum(float(v) for v in sums)/sum(int(v) for v in counts)
 with np.errstate(over='ignore',invalid='ignore'):ppl=float(np.exp(nll))
 vectors={}
 if draws is not None:
  names=sorted(set(groups));lookup={g:i for i,g in enumerate(names)};gn=np.zeros(len(names),dtype=np.float64);gd=np.zeros(len(names),dtype=np.int64)
  for g in names:
   ix=[i for i,x in enumerate(groups) if x==g];gn[lookup[g]]=math.fsum(float(sums[i]) for i in ix);gd[lookup[g]]=sum(int(counts[i]) for i in ix)
  # Gather sampled groups then reduce, independently of producer's row multiplicity matrix product.
  num=np.sum(gn[draws],axis=1,dtype=np.float64);den=np.sum(gd[draws],axis=1,dtype=np.int64);need(np.all(den>0),'Zero bootstrap target denominator');vectors['LM_NLL']=num/den
  with np.errstate(over='ignore',invalid='ignore'):vectors['LM_PPL']=np.exp(vectors['LM_NLL'])
 return {'LM_NLL':nll,'LM_PPL':ppl},vectors

def verify_lm(case,cfg,alias,t,sp,inputs,restored,feature):
 ids,fs,fc,seals,index=feature;root=Path(case)/'LM'/t/sp;verify_seal(root,required=['statistics.npz','draws.npz','METRICS.json'],restored=restored);r=load(root/'METRICS.json');ident=r['identity'];v=scope(cfg,alias,t,sp);need(ident['source_identity_sha256']==cfg['_LM_source'] and ident['task']==t and ident['split']==sp and ident['candidate_id']==v['candidate_id'] and ident['candidate_content_sha256']==v['model_tensor_content_sha256'] and ident['feature_seals_sha256']==seals and ident['runtime_lock_sha256']==cfg['cpu_runtime_lock_sha256'],'LM source/model/runtime/scope mismatch');need(digest(ident)==r['actual_LM_unit_id'],'LM actual ID changed');expected=metadata(cfg,t,sp,inputs);draws=None
 if sp=='dev':
  # Contract checks original exact bytes, mapping and seed; verifier independently consumes raw group draw indices.
  _,drawsha=draw_weights(cfg,t,inputs)
  with np.load(Path(inputs)/cfg['draws'][t]['relative_path'],allow_pickle=False) as d:draws=d['group_draws']
 with np.load(root/'statistics.npz',allow_pickle=False) as z:
  need(set(z.files)=={'ids','labels','groups','classes','nll_sum','n_tokens'},'LM statistics member set differs');need(z['ids'].tolist()==ids and z['labels'].tolist()==[x['label'] for x in expected] and z['groups'].tolist()==[x['group'] for x in expected] and z['classes'].tolist()==cfg['cohorts'][t][sp]['class_order'],'LM row/class/group order mismatch');need(np.array_equal(z['nll_sum'],fs) and np.array_equal(z['n_tokens'],fc),'LM arrays not exact feature sufficient statistics');points,vectors=independent(z['nll_sum'],z['n_tokens'],z['groups'].tolist(),draws)
 checks=[];need(len(r['metrics'])==2,'LM metric record count differs');expectedmetricids={spec_id(cfg['_planned'],'LM_metric',c=alias,t=t,split=sp,r=None,s=None,p='LM',m=m) for m in ['LM_NLL','LM_PPL']};need({x['planned_spec_id'] for x in r['metrics']}==expectedmetricids,'LM metric frozen keys differ');need(ident['planned_spec_id']==spec_id(cfg['_planned'],'LM',c=alias,t=t,split=sp,r=None,s=None,p='LM'),'LM frozen unit ID differs')
 with np.load(root/'draws.npz',allow_pickle=False) as z:
  need(set(z.files)=={'LM_NLL','LM_PPL','LM_NLL_valid','LM_PPL_valid'},'LM draw member set differs')
  for row in r['metrics']:
   m=row['canonical_metric'];name=m['metric'];val=points[name];need(m['sample_count']==len(ids) and m['group_count']==cfg['cohorts'][t][sp]['groups'] and m['valid_targets']==int(fc.sum()) and m['source_sha256']==cfg['_LM_source'] and m['unit_id']==r['actual_LM_unit_id'],'LM metric identity/denominator mismatch')
   if np.isfinite(val):checks.append(strict_residual([val],[m['estimate']],1e-12,name+'_point'))
   else:need(name=='LM_PPL' and m['estimate'] is None and m['missing_reason'],'PPL overflow not explicitly represented')
   d=vectors.get(name,np.array([],dtype=np.float64));mask=np.isfinite(d);saved=z[name];need(saved.dtype==np.float64 and saved.shape==d.shape and z[name+'_valid'].dtype==np.bool_ and np.array_equal(z[name+'_valid'],mask),'Quantity-specific draw mask mismatch');need(hashlib.sha256(mask.tobytes()).hexdigest()==row['valid_mask_sha256'],'Draw mask byte identity changed');need(np.array_equal(np.isposinf(saved),np.isposinf(d)) and np.array_equal(np.isnan(saved),np.isnan(d)),'Invalid/overflow draw values differ');attempted=2000 if sp=='dev' else 0;need(m['bootstrap_attempted']==attempted and m['bootstrap_valid']==int(mask.sum()) and m['bootstrap_invalid']==attempted-int(mask.sum()) and m['draw_sha256']==(drawsha if attempted else None),'Bootstrap denominator/source changed')
   if mask.any():
    checks.append(strict_residual(d[mask],saved[mask],1e-12,name+'_all_draws'));ci=np.percentile(d[mask],[2.5,97.5],method='linear');checks.append(strict_residual(ci,[m['ci_low'],m['ci_high']],1e-12,name+'_CI'));need(row['interval_disposition']=='AVAILABLE','Valid interval mislabeled')
   else:need(m['ci_low'] is None and m['ci_high'] is None and row['interval_disposition']==('UNAVAILABLE_ZERO_VALID_DRAWS' if attempted else 'NOT_REQUIRED_TRAIN_DIAGNOSTIC'),'Zero-draw interval not explicitly unavailable')
 return {'task':t,'split':sp,'planned_spec_id':ident['planned_spec_id'],'metrics':r['metrics'],'checks':checks,'statistics_seal_sha256':sha(root/'COMPLETE.json')}

def main(c,alias,consumer=None):
 start=time.monotonic();restored=consumer is not None
 if restored:
  base=Path(consumer);c=base/'control';cfg=load(c/'RUN_CONFIG.json');v=scope(cfg,alias);source=load(c/'SOURCE_IDENTITY.json');need(sha(c/'RUN_CONFIG.json')==source['configuration_sha256'],'Restored configuration identity changed');need(Path(__file__).resolve()==(base/'code/s06_verify.py').resolve(),'Restored source required');need(str(Path(sys.executable).absolute())==cfg['cpu_runtime_python'],'Wrong restored CPU interpreter')
  for f in source['files']:need(sha(base/'code'/f['path'])==f['sha256'],'Restored source differs')
  for role,key in [('GPU','_GPU_source'),('LM_producer','_LM_source'),('verifier','_verifier_source')]:cfg[key]=source['roles'][role]['source_identity_sha256']
  need(sha(c/'ENVIRONMENT_LOCK.json')==cfg['runtime_lock_sha256'] and sha(c/'CPU_ENVIRONMENT_LOCK.json')==cfg['cpu_runtime_lock_sha256'],'Restored runtime locks differ');case=base/'candidate';inputs=base/'inputs';out=base/'fresh-verification'
 else:
  cfg,v,_=readiness(c,alias,'verifier');case=Path(cfg['artifacts_root'])/'candidates'/alias;inputs=Path(cfg['inputs_root']);out=case/'verification'
 cfg['_planned']=planned(c);out.mkdir(exist_ok=True);lm=[];extractions=[];matrixcount=0
 with exclusive(out/'WRITER.lock'):
  for t in TASKS:
   for sp in SPLITS:
    result=bundle(case,cfg,alias,t,sp,inputs,restored,full=True);ids,_,_,_,idx=result;need(idx['planned_spec_id']==spec_id(cfg['_planned'],'extraction',c=alias,t=t,split=sp),'Extraction frozen ID mismatch')
    for rep in HOOKS:
     matrix=read_matrix(case,cfg,alias,t,sp,rep,inputs,restored);need(matrix.shape==(len(ids),1920),'Real S07 typed reader mismatch');del matrix;matrixcount+=1
    lm.append(verify_lm(case,cfg,alias,t,sp,inputs,restored,result));extractions.append({'task':t,'split':sp,'planned_spec_id':idx['planned_spec_id'],'rows':len(ids),'logical_matrices':26,'bundle_seal_sha256':sha(case/'features'/t/sp/'COMPLETE.json'),'chunks':idx['chunks']});print('S06_INDEPENDENT_BUNDLE_PASS',alias,t,sp,flush=True)
  bindings=s07_bindings(case,cfg,alias,inputs,restored);put(out/'S07_BINDINGS.json',{'schema_version':'s06-s07-consumer-bindings-v1','alias':alias,'candidate_id':v['candidate_id'],'candidate_content_sha256':v['model_tensor_content_sha256'],'records':bindings,'fitting_or_head_application_performed':False});checks=[x for row in lm for x in row['checks']];scopeids={x['planned_spec_id'] for x in extractions+lm}|{m['planned_spec_id'] for x in lm for m in x['metrics']};expected={x['id'] for x in cfg['_planned'] if x['c']==alias};need(scopeids==expected and len(scopeids)==40,'Exact candidate 40-key set differs');rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;need(rss<=8*1024**3,'Verifier8GiB ceiling exceeded');report={'schema_version':'s06-independent-verification-v1','status':'PASS','alias':alias,'candidate_id':v['candidate_id'],'candidate_content_sha256':v['model_tensor_content_sha256'],'source_identity_sha256':cfg['_verifier_source'],'producer_source_identity_sha256':cfg['_LM_source'],'extraction_source_identity_sha256':cfg['_GPU_source'],'extraction_bundles_verified':10,'logical_rows':sum(x['rows'] for x in extractions),'representation_matrices_verified':matrixcount,'LM_units_verified':len(lm),'primary_dev_uncertainty_units_verified':5,'LM_metric_records_verified':20,'exact_spec_ids':sorted(scopeids),'S07_refit_identities_resolved':len(bindings),'S07_fixed_application_identities_resolved':len(bindings),'S07_bindings_sha256':sha(out/'S07_BINDINGS.json'),'extractions':extractions,'LM_records':lm,'checks':checks,'max_abs_residual':max(x['max_abs_residual'] for x in checks),'atol':1e-12,'rtol':0,'CPU_wall_seconds':time.monotonic()-start,'peak_RSS_bytes':rss,'producer_input_fallback':False if restored else None,'recovery_scope':'All10bundles/all260typedmatrices/all10LMpoints/all5devdraws+masks+CIs/all390+390futureidentities; no fitting/head application/GPU/cleanruntime recreation','GPU_forwards':0,'fits':0,'head_applications':0};put(out/'VERIFICATION.json',report);print('S06_INDEPENDENT_VERIFICATION_PASS',alias,matrixcount,report['max_abs_residual'],flush=True);return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control');p.add_argument('--alias',required=True);p.add_argument('--consumer');x=p.parse_args();main(x.control,x.alias,x.consumer)
