"""Independent S05 reconstruction: pinned pairwise metrics and direct scaler/linear/logistic probabilities."""
from pathlib import Path
import os,sys,json,argparse,time,resource
from s05_contract import *

def verify_probability(case,cfg,alias,rep,seed,policy,inputs,restored,feature_cache):
 import numpy as np,joblib
 from inherited_independent import metrics as independent_metrics,reconstruct
 key=KEYS[HOOKS.index(rep)];root=Path(case)/'probabilities'/key/('seed'+str(seed))/policy;seal=verify_seal(root,required=['predictions.npz','draws.npz','METRICS.json'],restored=restored);record=load(root/'METRICS.json');ident=record['identity'];need(ident['candidate_alias']==alias and ident['representation']==rep and ident['cv_seed']==seed and ident['policy']==policy and ident['source_identity_sha256']==cfg['_source'],'Probability source/scope mismatch')
 if ('dev',key) not in feature_cache:feature_cache[('dev',key)]=load_layer(case,cfg,'dev',key,inputs_root=inputs,restored=restored)
 x,y,ids,_,_,fseal=feature_cache[('dev',key)];need(ident['DEV_feature_seals_sha256']==fseal,'Wrong probability feature source');head=Path(case)/'production'/key/('seed'+str(seed))/'head.joblib' if policy=='independent_refit' else Path(inputs)/'fixed-reference-heads'/(key+'-seed'+str(seed)+'.joblib');need(sha(head)==ident['head_sha256'],'Head identity mismatch')
 if policy=='fixed_original_base':need(sha(head)==next(r['sha256'] for r in cfg['fixed_heads'] if r['representation']==rep and r['cv_seed']==seed),'Original-base replaced')
 pipe=joblib.load(head);need(pipe[-1].classes_.tolist()==[0,1],'Wrong probability class columns');independent=reconstruct(pipe,x)
 with np.load(root/'predictions.npz',allow_pickle=False) as z:need(z['ids'].tolist()==ids and np.array_equal(z['labels'],y) and z['classes'].tolist()==[0,1] and z['groups'].tolist()==[r['group'] for r in metadata(cfg,'dev',inputs)],'Prediction metadata/class/order mismatch');probcheck=strict_residual(independent,z['probabilities'],1e-10,'saved_probability')
 weights,drawy,draw_sha=draw_weights(cfg,inputs);need(np.array_equal(y,drawy) and ident['dev_draw_sha256']==draw_sha,'Draw identity mismatch');classes=np.array([0,1]);points,pvalid=independent_metrics(y,independent,classes,np.ones((1,len(y)),dtype=np.float64));samples,valid=independent_metrics(y,independent,classes,weights);need(bool(pvalid[0]),'Undefined H3pointmetric');checks=[probcheck];name_map={'AUROC':'auroc','AP':'average_precision','accuracy':'accuracy','balanced_accuracy':'balanced_accuracy','cross_entropy':'classification_cross_entropy'}
 with np.load(root/'draws.npz',allow_pickle=False) as z:
  need(np.array_equal(z['valid'],valid),'Marginal validity masks differ');need(record['inference_eligible']==bool(valid.any()),'False inferential release eligibility')
  for row in record['metrics']:
   canonical=row['canonical_metric'];name=canonical['metric'];d=samples[name_map[name]];saved=z[name];need(np.isnan(saved[~valid]).all() and np.isnan(d[~valid]).all(),'Unexplained invaliddrawvalues');need(canonical['sample_count']==1497 and canonical['group_count']==cfg['cohorts']['dev']['groups'] and canonical['bootstrap_attempted']==2000 and canonical['bootstrap_valid']==int(valid.sum()) and canonical['bootstrap_invalid']==int((~valid).sum()),'Metric denominator/mask counts differ');checks.append(strict_residual(np.array([points[name_map[name]][0]]),np.array([canonical['estimate']]),1e-12,name+'_point'))
   if valid.any():
    checks.append(strict_residual(d[valid],saved[valid],1e-12,name+'_all_valid_draws'));interval=np.percentile(d[valid],[2.5,97.5],method='linear');checks.append(strict_residual(interval,np.array([canonical['ci_low'],canonical['ci_high']]),1e-12,name+'_interval'))
   else:need(canonical['ci_low'] is None and canonical['ci_high'] is None and canonical['missing_reason'],'Zero-validdraws need nullinterval/reason, no inferentialPASS')
 return {'status':'PASS' if valid.any() else 'PARTIAL_NO_VALID_INTERVAL','alias':alias,'representation':rep,'cv_seed':seed,'policy':policy,'planned_prediction_spec_id':ident['planned_spec_id'],'producer_receipt_sha256':sha(root/'COMPLETE.json'),'source_row_ids':[r['source_row_id'] for r in record['metrics']],'checks':checks,'point_metrics':5,'bootstrap_vectors':5,'attempted_draws':2000,'valid_draws':int(valid.sum()),'probability_columns':2,'rows':1497,'independent_implementation':'Exact inherited pairwise wins and threshold indicators; direct float32-preserving scaler/linear/logistic reconstruction, no producer metric/predict call'}

def verify_LM(case,cfg,alias,split,inputs,restored,feature_cache):
 import numpy as np
 root=Path(case)/'LM'/split;verify_seal(root,required=['statistics.npz','draws.npz','METRICS.json'],restored=restored);r=load(root/'METRICS.json');need(r['identity']['split']==split and r['identity']['source_identity_sha256']==cfg['_source'],'LMsource/scope mismatch');expected=metadata(cfg,split,inputs)
 if (split,'final_norm') not in feature_cache:feature_cache[(split,'final_norm')]=load_layer(case,cfg,split,'final_norm',inputs_root=inputs,restored=restored)
 _,y,ids,feat_sums,feat_counts,hashes=feature_cache[(split,'final_norm')]
 with np.load(root/'statistics.npz',allow_pickle=False) as z:
  need(z['ids'].tolist()==ids and np.array_equal(z['nll_sum'],feat_sums) and np.array_equal(z['n_tokens'],feat_counts),'LMstats row/sourceassociation mismatch');sums=z['nll_sum'].astype(np.float64);counts=z['n_tokens'].astype(np.float64);need(np.isfinite(sums).all() and np.isfinite(counts).all() and np.all(counts>0),'Invalid actual loss/target denominator');nll=np.sum(sums,dtype=np.float64)/np.sum(counts,dtype=np.float64)
 with np.errstate(over='ignore',invalid='ignore'):ppl=np.exp(nll)
 checks=[];points={'LM_NLL':nll,'LM_PPL':ppl};vectors={}
 if split=='dev':
  weights,yy,drawsha=draw_weights(cfg,inputs);need(np.array_equal(yy,y),'LMdraw labelcohort mismatch');sampled_num=np.sum(weights*sums[None,:],axis=1,dtype=np.float64);sampled_den=np.sum(weights*counts[None,:],axis=1,dtype=np.float64);vectors['LM_NLL']=sampled_num/sampled_den
  with np.errstate(over='ignore',invalid='ignore'):vectors['LM_PPL']=np.exp(vectors['LM_NLL'])
 with np.load(root/'draws.npz',allow_pickle=False) as z:
  for row in r['metrics']:
   cr=row['canonical_metric'];name=cr['metric'];need(cr['sample_count']==len(expected) and cr['valid_targets']==int(counts.sum()),'LMdenominator changed');val=points[name]
   if np.isfinite(val):checks.append(strict_residual(np.array([val]),np.array([cr['estimate']]),1e-12,name+'_corpus_point'))
   else:need(name=='LM_PPL' and cr['estimate'] is None and cr['missing_reason'],'LMoverflow notexplicit')
   if split=='dev':
    d=vectors[name];mask=np.isfinite(d);need(np.array_equal(z[name+'_valid'],mask),'LMvalidity masks differ');need(cr['bootstrap_attempted']==2000 and cr['bootstrap_valid']==int(mask.sum()),'LMdraw denominator changed');checks.append(strict_residual(d[mask],z[name][mask],1e-12,name+'_bootstrap'))
    if mask.any():checks.append(strict_residual(np.percentile(d[mask],[2.5,97.5],method='linear'),np.array([cr['ci_low'],cr['ci_high']]),1e-12,name+'_interval'))
    else:need(cr['ci_low'] is None and cr['ci_high'] is None,'InvalidLMinterval')
   else:need(cr['bootstrap_attempted']==0 and cr['ci_low'] is None and cr['ci_high'] is None and cr['uncertainty']=='none','TRAINdiagnostic has unauthorized bootstrap')
 return {'status':'PASS','alias':alias,'split':split,'planned_spec_id':r['identity']['planned_spec_id'],'producer_receipt_sha256':sha(root/'COMPLETE.json'),'source_row_ids':[v['source_row_id'] for v in r['metrics']],'checks':checks,'rows':len(ids),'valid_targets':int(counts.sum()),'new_GPU_or_fit_work':False,'scope':'Independent aggregate andDEVbootstrap ratio from actual per-example source-bound FP32loss sums andtargetcounts; no newlogit/GPUreplay'}

def verify_audit(case,cfg,alias,unit,inputs,restored,cache):
 import numpy as np,joblib
 from inherited_independent import reconstruct
 rep=unit['r'];seed=unit['s'];key=KEYS[HOOKS.index(rep)];audit=Path(case)/'audits'/key/('seed'+str(seed));prod=Path(case)/'production'/key/('seed'+str(seed));verify_seal(audit,required=['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json'],restored=restored);verify_seal(prod,required=['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json'],restored=restored);need(load(audit/'COMPLETE.json')['identity']['source_identity_sha256']==cfg['_auditor_source'],'Audit source identity mismatch');a=load(audit/'SUMMARY.json');p=load(prod/'SUMMARY.json');need(a['selected_C']==p['selected_C'],'Audit Cselection mismatch');checks=[]
 for i in range(3):checks.append(strict_residual(np.array(a['CV'][i]['fold_AUROC']),np.array(p['CV'][i]['fold_AUROC']),1e-12,'fullCV_AUROC'))
 if ('dev',key) not in cache:cache[('dev',key)]=load_layer(case,cfg,'dev',key,inputs_root=inputs,restored=restored)
 x=cache[('dev',key)][0];actual=reconstruct(joblib.load(audit/'head.joblib'),x)
 with np.load(Path(case)/'probabilities'/key/('seed'+str(seed))/'independent_refit/predictions.npz',allow_pickle=False) as z:checks.append(strict_residual(actual,z['probabilities'],1e-10,'audit_vs_production_probability'))
 return {'status':'PASS','planned_audit_spec_id':unit['id'],'alias':alias,'representation':rep,'cv_seed':seed,'selected_C':a['selected_C'],'audit_receipt_sha256':sha(audit/'COMPLETE.json'),'production_receipt_sha256':sha(prod/'COMPLETE.json'),'audit_parameter_content_sha256':a['parameter_content_sha256'],'production_parameter_content_sha256':p['parameter_content_sha256'],'parameter_content_exactly_equal':a['parameter_content_sha256']==p['parameter_content_sha256'],'checks':checks,'audit_replaced_production':False}

def run(c,alias,consumer=None,recovery=False):
 c=Path(c)
 if consumer is None:
  cfg,v,source=readiness(c,alias,role='verifier');case=Path(cfg['artifacts_root'])/'candidates'/alias;inputs=Path(cfg['inputs_root']);out=case/'verification';out.mkdir(exist_ok=True);cfg['_source']=cfg['_producer_source'];frozen=Path(cfg['frozen_root']);restored=False
 else:
  consumer=Path(consumer).resolve();cfg=load(consumer/'control/RUN_CONFIG.json');scope(cfg,alias);bundle=load(consumer/'control/SOURCE_IDENTITY.json');source=bundle['roles']['verifier']['source_identity_sha256'];cfg['_source']=bundle['roles']['producer']['source_identity_sha256'];cfg['_GPU_source']=bundle['roles']['GPU']['source_identity_sha256'];cfg['_auditor_source']=bundle['roles']['auditor']['source_identity_sha256'];cfg['_GPU_runtime_lock']=cfg['runtime_lock_sha256'];cfg['runtime_lock_sha256']=cfg['cpu_runtime_lock_sha256'];case=consumer/'candidate';inputs=consumer/'inputs';out=consumer/'fresh-verification';need(not out.exists(),'Never overwrite prior freshverification');out.mkdir();frozen=consumer/'frozen';restored=True
  for p in [case,inputs,frozen]:need(p.resolve().is_relative_to(consumer),'Producerinputfallback prohibited')
  for v in load(consumer/'control/SOURCE_IDENTITY.json')['files']:need(sha(consumer/'code'/v['path'])==v['sha256'],'Restored source changed')
 panel=[v for v in load(frozen/'H3_AUDIT_SUBSET.json')['units'] if v['c']==alias];need(len(panel)==(3 if alias in ['candidate_01','candidate_04','candidate_07'] else 2),'Frozen audit subset drift');keys=[(v['r'],v['s']) for v in panel] if recovery else [(r,s) for r in HOOKS for s in SEEDS];cache={};probability=[];audits=[];start=time.monotonic()
 from threadpoolctl import threadpool_limits
 with threadpool_limits(limits=4):
  for rep,seed in keys:
   for policy in POLICIES:
    row=verify_probability(case,cfg,alias,rep,seed,policy,inputs,restored,cache);need(row['status']=='PASS','Affected marginalinference noteligible');probability.append(row);put(out/'PROGRESS.json',{'alias':alias,'probability_paths_verified':len(probability),'expected_probability_paths':len(keys)*2,'owned_process':process_identity(),'updated_utc':now()});print('S05_INDEPENDENT_PATH_VERIFIED',alias,rep,seed,policy,flush=True)
  LM=[verify_LM(case,cfg,alias,split,inputs,restored,cache) for split in ['train','dev']]
  if not recovery:audits=[verify_audit(case,cfg,alias,v,inputs,restored,cache) for v in panel]
 rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;need(rss<=8*1024**3,'IndependentCPUworker8GiBRSS ceiling exceeded');allchecks=[x for row in probability+LM+audits for x in row['checks']];report={'schema_version':'s05-independent-reconstruction-v1','status':'PASS','alias':alias,'source_identity_sha256':source,'recovery_panel_only':recovery,'probability_paths_verified':len(probability),'classifier_metrics_verified':len(probability)*5,'LM_units_verified':2,'frozen_audit_refits_verified':len(audits),'probability_records':probability,'LM_records':LM,'audit_records':audits,'max_probability_abs_residual':max([x['max_abs_residual'] for x in allchecks if x['atol']==1e-10],default=0),'max_metric_draw_interval_abs_residual':max([x['max_abs_residual'] for x in allchecks if x['atol']==1e-12],default=0),'probability_atol':1e-10,'metric_draw_interval_atol':1e-12,'rtol':0,'CPU_wall_seconds':time.monotonic()-start,'peak_RSS_bytes':rss,'producer_input_fallback':False if consumer else None,'verification_scope':'Frozen auditkey recovery panel underbothpolicies andTRAIN/devLM, no refits/GPU' if recovery else 'Every156newprobabilitypaths/780marginalmetrics/allvaliddraws/masks/CIs, bothLM units andexactfullCVauditrefits','S09_contrasts_executed':False};put(out/'VERIFICATION.json',report);print('S05_INDEPENDENT_VERIFICATION_PASS',alias,len(probability),len(audits),report['max_probability_abs_residual'],report['max_metric_draw_interval_abs_residual'],flush=True);return report
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);p.add_argument('--alias',required=True);p.add_argument('--consumer');p.add_argument('--recovery',action='store_true');x=p.parse_args();run(x.control,x.alias,x.consumer,x.recovery)
