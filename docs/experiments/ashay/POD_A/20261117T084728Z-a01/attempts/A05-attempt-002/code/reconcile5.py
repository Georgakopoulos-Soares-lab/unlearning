"""Saved identity metadata reconciliation; never accesses prediction/loss values."""
from common5 import *
from metadata_contract5 import metadata_only,pair_identity,validate_original_file,unique_keys
import time
def main():
 start=time.monotonic();guard();protocol=read(D50/'PROTOCOL_FROZEN.json');inputs=read(C/'INPUT_MANIFEST.json');inputs['inputs']=[e for e in inputs['inputs'] if e.get('status')!='NOT_CANONICAL_FILENAME_RESOLVE_EQUIVALENT'];cache={};refs={}
 def ref(p,expected=None,owner='historical metadata dependency'):
  p=Path(p);key=str(p)
  if key not in refs:
   assert p.is_file();refs[key]={'path':key,'bytes':p.stat().st_size,'sha256':sha(p),'owner':owner,'verification_method':'FRESH_BYTE_SHA256_IDENTITY_ONLY'}
  e=refs[key]
  if expected:assert e['sha256']==expected,(key,'digest mismatch')
  return e
 def meta(p):
  if str(p) not in cache:cache[str(p)]=metadata_only(p)
  return cache[str(p)]
 for name in ['AUDIT_SCOPE_MATRIX.csv','AUDIT_REFIT_RECEIPT.json','NUMERICAL_AUDIT.json','BOOTSTRAP_AUDIT.json','VERIFICATION_OVERLAY.json','A08_EXECUTION_MANIFEST.json']:
  e=ref(D8/name,owner='A08-attempt-001');e.update(repository='Georgakopoulos-Soares-lab/unlearning',commit=cfg['research_head_before'],repository_path=str((D8/name).relative_to(W)));assert bh(gitb('show',cfg['research_head_before']+':'+e['repository_path']))==e['sha256'];inputs['inputs'].append(e)
 fixed=read(D3/'FIXED_REFERENCE_INDEX.json');baseheads={(e['task'],e['representation'],e['cv_seed']):e for e in fixed['references']};assert len(baseheads)==468
 for e in fixed['references']:ref(e['head']['path'],e['head']['sha256']);ref(e['identity']['path'],e['identity']['sha256'])
 folds={(e['task'],e['seed']):e['reference'] for e in protocol['folds']}
 for e in folds.values():ref(e['path'],e['sha256'])
 draws={}
 for e in read(D3/'PAIRING_POPULATION_CHECKS.json')['arrays']:
  assert e['draws']==2000 and e['seed']==20261103;ref(e['reference']['path'],e['reference']['sha256']);key=(e['task'],e['split'])
  if key in draws:assert draws[key]['sha256']==e['reference']['sha256']
  else:draws[key]=e['reference']
 assert len(draws)==7
 # Parse only lineage/identity columns. No estimates, intervals or scientific values retained.
 cols=['checkpoint_alias','checkpoint_content_id','original_endpoint_id','task','split','representation','CV_seed','policy','source_policy','protocol_sha256','coverage_plan_sha256','source_sha256','measurement_source_sha256','prediction_sha256','draw_sha256','producer_receipt','producer_receipt_sha256','audit_receipt','audit_receipt_sha256','prediction_hash_kind','prediction_locator','sample_count','group_count','status']
 unique={};table_index=read(D9/'TABLE_INDEX.json');t=next(e for e in table_index['tables'] if e['logical_table']=='VERIFIED_METRICS');ref(D8/'VERIFIED_METRICS.csv',t['sha256'],'A08 release preserved by A09')
 with (D8/'VERIFIED_METRICS.csv').open() as f:
  for row in csv.DictReader(f):
   e={k:row[k] for k in cols};key=(e['checkpoint_alias'],e['task'],e['split'],e['representation'],int(e['CV_seed']),e['policy'])
   if key in unique:assert unique[key]==e
   else:unique[key]=e
 assert len(unique)==5460
 catalog=[];units={};producer_cache={}
 def producer(path,expected):
  path=Path(path);ref(path,expected)
  if str(path) not in producer_cache:producer_cache[str(path)]=read(path)
  return producer_cache[str(path)]
 for key,e in sorted(unique.items()):
  alias,task,split,hook,seed,policy=key;physical=original_split(split);p=Path(e['producer_receipt']);j=producer(p,e['producer_receipt_sha256']);root=p.parent
  # A06 H3 release seal points at its immutable producer through a separate file.
  pj=j
  if alias in ['R4','R6'] and task=='emp_H3':
   pp=root/'PRODUCER_COMPLETE.json';pj=producer(pp,j.get('producer_sha256'));ref(root/'AUDIT.json',j.get('audit_sha256'))
  records={Path(x['path']).name:x for x in pj['files']};pr=records[physical+'_predictions.npz'];path=root/Path(pr['path']).name;ref(path,pr['sha256']);assert pr['sha256']==e['prediction_sha256'];m=meta(path);assert m['rows']==int(e['sample_count']);assert m['fields']['groups']['unique_groups']==int(e['group_count']);assert m['fields']['classes']['values']==([0,1,2] if task=='gue_splice_reconstructed' else [0,1]);assert e['draw_sha256']==draws[(task,physical)]['sha256']
  if alias in ['base','R1','R3']:
   headname={'base':'base.joblib','R1':'h3_only_maxent.joblib','R3':'new_checkpoint.joblib'}[alias];head=records[headname];ref(root/headname,head['sha256']);ff=records['folds_seed'+str(seed)+'.json'];assert ff['sha256']==folds[(task,seed)]['sha256'];assert records['base.joblib']['sha256']==baseheads[(task,hook,seed)]['head']['sha256'];original_protocol=pj['protocol_sha256'];fitid=root.parents[2]/'run_identity.json';fit=read(fitid);ref(fitid,pj['fit_identity_sha256']);assert fit['manifest_sha256']==protocol['cohorts']['H3' if task=='emp_H3' else 'other_five'];assert fit['seeds']==SEEDS
  else:
   head=records['head.joblib'];ref(root/'head.joblib',head['sha256']);b=pj['original_base_head'];assert b['sha256']==baseheads[(task,hook,seed)]['head']['sha256'];fold_sha=pj.get('fold_sha256') or pj['fold']['sha256'];assert fold_sha==folds[(task,seed)]['sha256'];original_protocol=pj.get('protocol_sha256') or pj['identity']['protocol_sha256']
  selector={'base':{'independent_refit':'prob_base_refit','fixed_original_base':'prob_base_refit'},'R1':{'independent_refit':'prob_h3_only_refit','fixed_original_base':'prob_h3_only_fixed_base'},'R3':{'independent_refit':'prob_new_refit','fixed_original_base':'prob_new_fixed_base'}}.get(alias,{p:p for p in POLICIES})[policy]
  # Resolve inherited schema spellings by archive member NAME only; never read those members.
  available=m['available_member_names_only']
  if selector+'.npy' not in available and alias=='R1':
   possible={'independent_refit':['prob_post_refit','prob_h3_refit'],'fixed_original_base':['prob_post_fixed_base','prob_h3_fixed_base']}[policy];selector=next((v for v in possible if v+'.npy' in available),selector)
  assert selector+'.npy' in available,(alias,selector,available)
  record={**e,'CV_seed':seed,'prediction_file':ref(path),'probability_member_selector':selector,'identity_metadata':m,'head':ref(root/Path(head['path']).name),'original_base_head':baseheads[(task,hook,seed)]['head'],'saved_fold':folds[(task,seed)],'draw':draws[(task,physical)],'original_producer_protocol_sha256':original_protocol,'released_ingestion_protocol_sha256':e['protocol_sha256'],'producer_status_preserved':j['status'],'A05_new_numerical_audit':False}
  units[key]=record;catalog.append(record)
 # Exact identities across all five old endpoints, every hook, seed and policy.
 pair_checks=[]
 for task in TASKS:
  for split in reporting_splits(task):
   for hook in HOOKS:
    for seed in SEEDS:
     for policy in POLICIES:
      baseline=units[('base',task,split,hook,seed,policy)]
      for alias in ['R1','R3','R4','R6']:pair_identity(units[(alias,task,split,hook,seed,policy)]['identity_metadata'],baseline['identity_metadata'])
      pair_checks.append({'task':task,'split':split,'representation':hook,'seed':seed,'policy':policy,'status':'ELIGIBLE_FOR_SAVED_OUTPUT_COMPARISON','R3_reference_prediction_sha256':units[('R3',task,split,hook,seed,policy)]['prediction_sha256'],'R4_target_prediction_sha256':units[('R4',task,split,hook,seed,policy)]['prediction_sha256'],'ordered_metadata_digest':digest(baseline['identity_metadata']['fields']),'draw_sha256':baseline['draw_sha256'],'fold_sha256':baseline['saved_fold']['sha256'],'classes':baseline['identity_metadata']['fields']['classes']['values'],'causal_comparability':'NOT_ESTABLISHED','heldout_cross_runtime_numerical_equality':'NOT_CLAIMED'})
 identities=read(D4/'CHECKPOINT_IDENTITIES.json');r3=next(e for e in identities['targets'] if e['alias']=='R3');r3root=Path(next(e['producer_receipt'] for e in catalog if e['checkpoint_alias']=='R3')).parents[5];features=[]
 for group in ['H3','other_five']:
  p=r3root/'features'/group/'new'/'identity.json';j=read(p);ref(p);assert j['checkpoint_shards'][0]['sha256']==r3['native_sha256'] and j['config_sha256']==r3['config_sha256'] and j['tokenizer_sha256']==r3['tokenizer_sha256'];assert j['hooks']==HOOKS and j['physical_batch_size']==8 and j['feature_dtype']=='float32' and j['feature_width']==1920 and j['attention_backend']=='TE unfused';assert j['manifest_sha256']==protocol['cohorts'][group];features.append({'group':group,'identity':ref(p),'feature_seal':ref(p.parent/'FEATURE_UNIT_COMPLETE.json'),'runtime_and_hook_semantics':j,'status':'REUSABLE_WITH_A03_A04_EVIDENCE'})
 smoke=read(D4/'SMOKE_RESULTS.json');bridge=[{k:e[k] for k in ['alias','kind','variant','array','qualification_identity','reference_sha256','status']} for e in smoke['checks'] if e['alias']=='R3' and e['kind']=='same_checkpoint_historical'];assert len(bridge)==81 and all(e['status']=='PASS' for e in bridge)
 # Current feature descriptors supply exact ordered TRAIN/cohort manifests for prospective R5.
 extraction=[]
 for e in read(D6/'EXTRACTION_INDEX.json')['units']:
  if e['candidate']!='R4':continue
  p=A6/e['receipt'];j=read(p);ref(p,e['receipt_sha256']);u=j['identity']['unit'];ref(u['manifest']['path'],u['manifest']['sha256']);extraction.append({'task':e['task'],'split':e['split'],'rows':e['rows_verified'],'chunks':e['chunks'],'physical_forwards':e['physical_forwards_expected'],'identity':j['identity'],'R4_feature_receipt':ref(p),'input_manifest':u['manifest']})
 assert len(extraction)==13
 # R3 LM uses a sealed feature-bundle selector, R4/R6 use sufficient-statistic files.
 lm=[]
 with (D8/'LM_METRICS_VERIFIED.csv').open() as f:
  for row in csv.DictReader(f):
   if row['checkpoint_alias'] not in ['R3','R4','R6']:continue
   if row['metric']!='causal_nll':continue
   fields=['checkpoint_alias','task','split','input_sha256','prediction_sha256','prediction_hash_kind','prediction_locator','draw_sha256','producer_receipt','producer_receipt_sha256','protocol_sha256','coverage_plan_sha256','source_sha256'];q={k:row[k] for k in fields};p=Path(q['producer_receipt']);ref(p,q['producer_receipt_sha256']);q['canonical_cohort_sha256']=protocol['cohorts']['H3' if row['task']=='emp_H3' else 'other_five'];q['raw_input_sha_semantics']='raw_cohort_manifest' if row['checkpoint_alias']=='R3' else 'feature_bundle_receipt';q['draw_reference']=draws[(row['task'],original_split(row['split']))];assert q['draw_sha256']==q['draw_reference']['sha256']
   if row['checkpoint_alias']=='R3':
    group='H3' if row['task']=='emp_H3' else 'other_five';feature=r3root/'features'/group/'new'/'FEATURE_UNIT_COMPLETE.json';ref(feature,q['prediction_sha256']);q['ordered_LM_identity_proof']='A03 FEATURE_STRUCTURAL_AUDIT + PAIRING_AND_UNCERTAINTY_AUDIT; sealed feature bundle, typed task/split/arm selector'
   else:
    pred=p.parent/'sufficient_statistics.npz';ref(pred,q['prediction_sha256']);m=meta(pred);baseline=units[('R3',row['task'],row['split'],HOOKS[0],42,POLICIES[0])];pair_identity(m,baseline['identity_metadata'],require_classes=False);q['ordered_LM_identity_proof']='Fresh sufficient-statistics identity metadata equals historical classifier/feature cohort; no loss values accessed'
   q['status']='ELIGIBLE_FOR_SAVED_OUTPUT_COMPARISON';q['whole_heldout_runtime_numerical_equality_claimed']=False;lm.append(q)
 assert len(lm)==21, len(lm)
 put(C/'REUSE_CATALOG.json',{'schema':'pod-a-a05-identity-catalog-v2','status':'PASS','units':catalog,'unique_probability_files_metadata_inspected':len(cache),'array_whitelist':['ids','labels','groups','sequence_sha256','classes','lengths'],'scientific_probability_feature_loss_values_read':False});put(C/'R3_COMPARABILITY.json',{'status':'ELIGIBLE_FOR_SAVED_OUTPUT_COMPARISON','domains':pair_checks,'historical_feature_families':features,'TRAIN_bridge':bridge,'LM_domains':lm,'R3_historical_model_identity':r3,'historical_release_R3_content_id_empty_preserved':True,'new_identity_overlay_only':True,'historical_release_scientific_reaudit_performed':False,'global_heldout_equality_proven':False,'causal_lineage_or_exposure_proven':False});put(C/'EXTRACTION_INPUTS.json',extraction)
 inputs['inputs']+=list(refs.values());inputs.update(status='PASS',identity_catalog_sha256=sha(C/'REUSE_CATALOG.json'),R3_comparability_sha256=sha(C/'R3_COMPARABILITY.json'));put(C/'INPUT_MANIFEST.json',inputs);put(C/'METADATA_RECONCILIATION_RECEIPT.json',{'status':'PASS','current_identity_refs':len(refs),'released_policy_split_unit_identities':len(catalog),'unique_NPZ_identity_metadata_reads':len(cache),'R3_R4_exact_classifier_joins':len(pair_checks),'R3_LM_eligible_task_splits':7,'R3_bridge_rows_reused':len(bridge),'new_measurements_fits_or_effects':0,'no_prediction_feature_loss_arrays_read':True,'no_heldout_forward':True,'wall_seconds':time.monotonic()-start});no_science_imports();print(json.dumps(read(C/'METADATA_RECONCILIATION_RECEIPT.json')))
if __name__=='__main__':main()
