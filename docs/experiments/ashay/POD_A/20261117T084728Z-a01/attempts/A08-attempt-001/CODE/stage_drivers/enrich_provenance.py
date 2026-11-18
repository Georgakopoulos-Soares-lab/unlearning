"""Reporting-only provenance completion; preserve every numerical field and frozen receipt."""
from report_tables import *
from functools import lru_cache

@lru_cache(maxsize=None)
def lm_evidence(alias,task,split):
 archive_split='test' if split=='test_exploratory' else split
 dp=old(H/('probes/H3' if task=='emp_H3' else 'probes/other_five')/task/(archive_split+'_resampling.npz'))
 if alias in ['R4','R6']:
  unit=A6/'lm'/alias/task/archive_split;receipt=unit/'COMPLETE.json';seal=read(receipt)
  for e in seal['files']:
   p=unit/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
  stats=unit/'sufficient_statistics.npz';result=read(unit/'RESULTS.json')
  return {'prediction_sha256':sha(stats),'prediction_hash_kind':'LM_SUFFICIENT_STATISTICS_FILE','prediction_locator':str(stats),'draw_sha256':sha(dp),'producer_receipt':str(receipt),'producer_receipt_sha256':sha(receipt),'input_sha256':result['input_bundle_sha256'],'target_count':result['targets'],'measurement_source_sha256':result['source_sha256']}
 root=R3 if alias=='R3' else H;group='H3' if task=='emp_H3' else 'other_five';arm={'base':'base','R1':'maxent','R3':'new'}[alias];bundle=old(root/'features'/group/arm/'FEATURE_UNIT_COMPLETE.json');unit=root/('probes/H3' if task=='emp_H3' else 'probes/other_five')/task;receipt=old(unit/'LM_COMPLETE.json')
 armname={'base':'base','R1':'h3_only_maxent','R3':'new_checkpoint'}[alias]
 original=next(r for r in csvrows(old(root/'reports/LM_METRICS.csv')) if r['task']==task and normsplit(r['split'])==split and r['arm']==armname)
 return {'prediction_sha256':sha(bundle),'prediction_hash_kind':'LM_SEALED_FEATURE_BUNDLE_WITH_SUM_COUNT_SELECTOR','prediction_locator':str(bundle)+'#task='+task+'&split='+archive_split+'&arm='+arm,'draw_sha256':sha(dp),'producer_receipt':str(receipt),'producer_receipt_sha256':sha(receipt),'input_sha256':COHORTS[group],'target_count':int(original['target_count']),'measurement_source_sha256':None}

def main():
 names=['VERIFIED_METRICS.csv','PAIRED_CONTRASTS.csv','PAIRED_CONTRASTS.H3_reused.csv','PAIRED_CONTRASTS.historical.csv','PAIRED_CONTRASTS.R6_minus_R4.csv','LM_METRICS_VERIFIED.csv','LM_CONTRASTS_VERIFIED.csv'];proof=[]
 added=['prediction_hash_kind','prediction_locator','reference_prediction_hash_kind','reference_prediction_locator','source_prediction_sha256','source_reference_prediction_sha256','measurement_source_sha256']
 protected=['estimate','ci_low','ci_high','bootstrap_attempted','bootstrap_valid','bootstrap_invalid','measurement_attempt','lineage','ingestion_status','status']
 for name in names:
  rr=csvrows(D/name);before=digest([{k:r[k] for k in protected} for r in rr]);fields=list(rr[0])+[k for k in added if k not in rr[0]]
  for r in rr:
   r.update({k:None for k in added});r['source_prediction_sha256']=r['prediction_sha256'];r['source_reference_prediction_sha256']=r['reference_prediction_sha256']
   if r['policy']=='actual_causal_head':
    r.update(lm_evidence(r['checkpoint_alias'],r['task'],r['split']))
    if r['reference']:
     refdata=lm_evidence(r['reference'],r['task'],r['split']);r['reference_prediction_sha256']=refdata['prediction_sha256'];r['reference_prediction_hash_kind']=refdata['prediction_hash_kind'];r['reference_prediction_locator']=refdata['prediction_locator'];assert int(r['target_count'])==int(refdata['target_count'])
   else:
    r['prediction_hash_kind']='CLASSIFIER_PROBABILITY_NPZ_FILE';r['prediction_locator']='Producer receipt member; policy/class/split selected by full row key'
    if r['reference']:
     r['reference_prediction_hash_kind']='CLASSIFIER_PROBABILITY_NPZ_FILE';r['reference_prediction_locator']='Reference producer receipt member; reference policy selected by full row key'
     if r['measurement_attempt']=='HISTORICAL_NOVEMBER10':
      x={'task':r['task'],'layer':r['representation'],'seed':r['CV_seed'],'split':r['split']};e=historical_evidence(H,x);r['reference_prediction_sha256']=e['prediction_sha256']
   assert r['prediction_sha256'] and r['draw_sha256'] and r['producer_receipt_sha256'] and r['audit_receipt_sha256']
   if r['reference']:assert r['reference_prediction_sha256']
  assert before==digest([{k:r[k] for k in protected} for r in rr])
  guard(allow_dirty=True)
  with (D/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rr)
  proof.append({'file':name,'rows':len(rr),'protected_numerical_and_origin_fields_sha256':before,'all_values_unchanged':True,'sha256':sha(D/name)})
 tablemap=read(D/'TABLE_PARTITIONS.json')
 for p in tablemap['logical_PAIRED_CONTRASTS']['partitions']:p['sha256']=sha(D/p['file'])
 for name,n in [('PENDING_ADJACENT_CONTRASTS.csv',27300),('PENDING_ADJACENT_LM.csv',70),('POLICY_POINT_DIFFERENCES.csv',5460),('TASK_ENTRY_ANALYSIS.csv',240),('PREDECLARED_ANCHORS.csv',240),('CONTROL_METRICS_REUSED.csv',210)]:tablemap[name.removesuffix('.csv')]={'file':name,'rows':n,'sha256':sha(D/name)}
 publish('TABLE_PARTITIONS.json',tablemap);schema=read(D/'RESULT_SCHEMAS.json');schema['columns']+=added;schema['prediction_hash_semantics']={'CLASSIFIER_PROBABILITY_NPZ_FILE':'Exact immutable NPZ file; full key selects the policy and class columns','LM_SUFFICIENT_STATISTICS_FILE':'Exact saved float32 sequence-loss sums and shifted-target counts, not classifier probabilities','LM_SEALED_FEATURE_BUNDLE_WITH_SUM_COUNT_SELECTOR':'Exact immutable FEATURE_UNIT_COMPLETE.json digest binds feature/LM chunk member hashes; locator preserves task/split/arm selector. No LM probabilities invented.'};schema['source_prediction_sha256']='Retains prior A08 export hash, including original LM receipt pointers, before provenance-only normalization; original private analysis seals unchanged';schema['measurement_source_sha256']='Original LM producer source digest where recorded; historical value unknown, inherited source graph bound by A03 accepted audit receipts';schema['additional_table_schemas']={'PENDING_ADJACENT_CONTRASTS':'family/task/split/representation/CV_seed/policy/metric/protocol unique; null estimate/CI with reason; all 27300 frozen blocked keys','PENDING_ADJACENT_LM':'family/task/split/metric/protocol unique; null representation and seed; 70 missing keys','POLICY_POINT_DIFFERENCES':'candidate/task/split/representation/CV_seed/metric unique; descriptive refit-minus-fixed point only; null intervals with reason','TASK_ENTRY_ANALYSIS':'candidate/task/dev/representation/seed42/policy/metric unique; 240 predeclared displays joined to unchanged source configuration evidence','CONTROL_METRICS_REUSED':'36 shared unique fits x5metrics x1dev, plus six H3 exploratory-test fits x5metrics=210 metric rows; canonical columns plus typed source refs in CONTROL_REUSE_MAP.json'};publish('RESULT_SCHEMAS.json',schema)
 proof={'status':'PASS','schema':'pod-a-a08-report-provenance-normalization-v1','scientific_source_changed':False,'original_analysis_seals_changed':False,'numerical_values_changed':False,'tables':proof,'note':'Completed exact reference-prediction identities, LM sum/count and draw identities, and historical LM token counts through immutable accepted evidence. This is a reporting-only correction.'};put(C/'REPORT_PROVENANCE_NORMALIZATION.json',proof);publish('REPORT_PROVENANCE_NORMALIZATION.json',proof);print(json.dumps({'status':'PASS','tables':len(names),'all_numerical_and_origin_fields_unchanged':True}))
if __name__=='__main__':main()
