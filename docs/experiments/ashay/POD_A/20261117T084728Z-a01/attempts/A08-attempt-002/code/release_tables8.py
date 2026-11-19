"""Exact A05-key release overlays and deterministic sanitized aggregate shards."""
from common8 import *
from provenance8 import Registry
from key_contract5 import table_keys
import csv,io,math,collections,gzip

class PublicationRegistry(Registry):
 def __init__(self):super().__init__();self.public_input_commit=git('rev-parse','HEAD');self.verified_physical_files={}
 def file(self,path,kind,selector=None,expected=None):
  p=Path(path);assert p.is_file() and not p.is_symlink();st=p.stat();fingerprint=(str(p),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
  if fingerprint in self.verified_physical_files:
   d=dict(self.verified_physical_files[fingerprint]);assert expected is None or d['sha256']==expected;d.update(hash_kind=kind,array_selector=selector);identity=digest(d);self.artifacts[identity]=d;return 'provenance:'+identity
  if p.is_relative_to(D):
   rel=str(p.relative_to(W));data=p.read_bytes();assert gitb('show',self.public_input_commit+':'+rel)==data;h=bh(data);assert expected is None or h==expected;d={'storage_kind':'GIT_BLOB','repository':'Georgakopoulos-Soares-lab/unlearning','commit':self.public_input_commit,'path':rel,'bytes':len(data),'sha256':h,'hash_kind':kind,'array_selector':selector};identity=digest(d);self.artifacts[identity]=d;pointer='provenance:'+identity
  else:
   pointer=super().file(path,kind,selector,expected);d=self.artifacts[pointer.removeprefix('provenance:')]
  st2=p.stat();assert fingerprint==(str(p),st2.st_dev,st2.st_ino,st2.st_size,st2.st_mtime_ns,st2.st_ctime_ns);self.verified_physical_files[fingerprint]={k:v for k,v in d.items() if k not in ['hash_kind','array_selector']};return pointer

def csvrows(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def main():
 guard();assert read(C/'AUDIT_QUEUE_RESULT.json')['status']==read(C/'ANALYSIS_QUEUE_RESULT.json')['status']=='PASS';reg=PublicationRegistry();original_map=read(D7/'PRIVATE_PROVENANCE_MAP.json')['artifacts'];rows=[];overlay=[];snap=read(C/'A08_EXECUTION_MANIFEST.json');unitmap={u['unit_id']:u for u in snap['audit_units']}
 def link(row,prefix,path,kind,selector=None,expected=None):
  pointer=reg.file(path,kind,selector,expected);d=reg.artifacts[pointer.removeprefix('provenance:')];row[prefix+'_locator']=pointer;row[prefix+'_sha256']=d['sha256'];row[prefix+'_hash_kind']=kind
 def desc(row,prefix,d,selector=None):
  d=dict(d)
  if selector is not None:d['array_selector']=selector
  identity=digest(d);reg.artifacts[identity]=d;row[prefix+'_locator']='provenance:'+identity;row[prefix+'_sha256']=d['sha256'];row[prefix+'_hash_kind']=d['hash_kind']
 for u in snap['audit_units']:
  uid=u['unit_id'];root=A/'audits'/uid;assert read(root/'COMPLETE.json')['status']=='PASS';r={'unit_id':uid,'producer_receipt_sha256':u['producer_receipt']['sha256'],'original_producer_status':'COMPLETE_UNVERIFIED','A08_release_status':'VERIFIED','audit_attempt':C.name,'full_CV_refit_required':u['sampled_refit_required'],'recovery_status':'PASS_12_PATH_TASK_PANEL_AND_ALL_INCLUDED_FILES'};link(r,'A08_audit_receipt',root/'COMPLETE.json','INDEPENDENT_UNIT_AUDIT_RECEIPT');link(r,'A08_recovery_receipt',D/('BACKUP_audit_'+u['task']+'.json'),'FRESH_TASK_RECOVERY_RECEIPT')
  if u['sampled_refit_required']:link(r,'A08_refit_receipt',A/'refits'/uid/'COMPLETE.json','INDEPENDENT_FULL_CV_REFIT_RECEIPT')
  else:r.update(A08_refit_receipt_locator=None,A08_refit_receipt_sha256=None,A08_refit_receipt_hash_kind=None,A08_refit_not_required_reason='NOT_IN_PROSPECTIVELY_FROZEN_PANEL')
  overlay.append(r)
 ovmap={r['unit_id']:r for r in overlay}
 for filename in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv']:
  original=csvrows(D7/filename)
  for old in original:
   r=dict(old);key='final_norm' if old['representation']=='decoder.final_norm' else old['representation'].replace('decoder.layers.','decoder_layer_');uid='R5/'+old['task']+'/'+key+'/seed'+old['CV_seed'];r.update({k:v for k,v in ovmap[uid].items() if k.startswith('A08_')});r.update(A08_independent_release_attempt=C.name,A08_original_row_status=old['status'],A08_producer_values_unchanged=True,A08_original_table_sha256=sha(D7/filename),A08_original_table_commit=cfg['research_head_before']);link(r,'A08_source_identity',C/'SOURCE_IDENTITY.json','INDEPENDENT_AUDIT_SOURCE_MANIFEST');assert all(r[k]==v for k,v in old.items());rows.append(r)
 assert len(rows)==12300
 newcls=[];newlm=[]
 for kind,out in [('classifier',newcls),('LM',newlm)]:
  paths=(A/'contrasts'/kind).glob('*/*/*/*/seed*/COMPLETE.json') if kind=='classifier' else (A/'contrasts/LM').glob('*/*/*/COMPLETE.json')
  for p in sorted(paths):
   assert read(p)['status']=='PASS';record=read(p.parent/'RESULTS.json');family=record['family'];target=record['endpoints']['target'];reference=record['endpoints']['reference']
   for old in record['rows']:
    r=dict(old);link(r,'A08_contrast_receipt',p,'INDEPENDENT_PAIRED_CONTRAST_RECEIPT');link(r,'A08_paired_values',p.parent/'paired_draws.npz','PAIRED_BOOTSTRAP_VECTORS_AND_MASK',r['policy']+'__'+r['metric'] if kind=='classifier' else r['metric']);link(r,'source_identity',C/'CONTRAST_SOURCE_IDENTITY.json','SAVED_OUTPUT_ANALYSIS_SOURCE_MANIFEST');r.update(independent_validation='PASS_TWO_NUMERICAL_ROUTES',recovery_status='PASS_FROZEN_PANEL_AND_ALL_INCLUDED_FILES',biological_independence='NOT_ESTABLISHED')
    if kind=='classifier':
     desc(r,'target_prediction',target['prediction'],target['selectors'][r['policy']]);desc(r,'reference_prediction',reference['prediction'],reference['selectors'][r['policy']]);desc(r,'target_audit_receipt',target['release_receipts'][r['policy']]);desc(r,'reference_audit_receipt',reference['release_receipts'][r['policy']]);desc(r,'target_producer_receipt',target['producer_receipt']);desc(r,'reference_producer_receipt',reference['producer_receipt']);desc(r,'draw',target['draw']);r['reference_original_content_id']=reference['original_content_id'];r['reference_content_overlay_reason']='Original R3 content field empty; verified native tensor identity admitted only within approved saved-output domains' if reference['candidate']=='R3' else None;link(r,'A08_recovery_receipt',D/('BACKUP_adjacent_'+family+'.json'),'FRESH_ADJACENT_RECOVERY_RECEIPT')
     if family=='R4_minus_R3':link(r,'domain_eligibility',D5/'R3_COMPARABILITY.json','DOMAIN_SPECIFIC_COMPATIBILITY_RECEIPT');r['R3_domain_digest']=reference['R3_domain_digest']
    else:
     for name,item in [('target',target),('reference',reference)]:
      link(r,name+'_prediction',item['statistics']['path'],'NORMALIZED_SAVED_CAUSAL_LM_SUFFICIENT_STATISTICS','nll_sum,n_tokens');desc(r,name+'_original_LM_object',item['endpoint']['prediction_descriptor']);desc(r,name+'_producer_receipt',item['endpoint']['producer_descriptor']);link(r,name+'_normalization_receipt',item['receipt']['path'],'TYPED_LM_NORMALIZATION_RECEIPT')
     desc(r,'draw',target['endpoint']['draw']);link(r,'A08_recovery_receipt',D/'BACKUP_LM_all.json','FRESH_LM_RECOVERY_RECEIPT');link(r,'A08_paired_point_audit',A/'contrasts/LM/POINT_VERIFICATION.json','INDEPENDENT_PAIRED_LM_POINT_AUDIT')
    hroot=Path('/workspace/recovery/POD_A')/R.name/'A03-attempt-001/restored/base_R1/multiretain-layers-v1-final-20261110T140836Z';raw=hroot/'manifests'/('H3.jsonl' if r['task']=='emp_H3' else 'other_five.jsonl');link(r,'raw_cohort',raw,'RAW_COHORT_MANIFEST',expected=r['raw_cohort_sha256']);out.append(r)
 assert len(newcls)==16380 and len(newlm)==70
 # Full amendment union is measured from original A06 rows, unmodified A07 values plus overlays and newly verified contrasts.
 a6=[];reused=[]
 for name in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv','LM_RESULTS.csv']:
  rs=csvrows(D6/name);a6.extend(rs);reused.append({'repository':'Georgakopoulos-Soares-lab/unlearning','commit':'ba340d0f4706b1941f62a4d6256bf78ab99030eb','path':str((D6/name).relative_to(W)),'sha256':sha(D6/name),'rows':len(rs),'role':'IMMUTABLE_REUSED_A06_RELEASE'})
 assert len(a6)==4934;expected=table_keys(read(D5/'TABLE_KEY_DESIGN.json'),cfg['coverage_plan_sha256']);allrows=a6+rows+newcls+newlm;ids=[r['logical_id'] for r in allrows];assert len(ids)==len(set(ids))==33684 and set(ids)=={r['logical_id'] for r in expected};assert len({r['logical_id'] for r in newcls+newlm})==16450
 # Audit reference caches and portable scientific input bindings are metadata views, not additional logical results.
 cache_index=[]
 for p in sorted((A/'endpoint-cache/classifier').glob('*/COMPLETE.json')):
  seal=read(p);identity=seal['identity'];ep=identity['endpoint'];diagnostics=read(p.parent/'ENDPOINT.json');r={'candidate':ep['candidate'],'task':ep['task'],'split':ep['split'],'representation':ep['representation'],'CV_seed':ep['seed'],'policy':identity['policy'],'probability_array_sha256':identity['probability_array_sha256'],'point_max_abs':diagnostics['point_max_abs'],'draw_max_abs':diagnostics['draw_max_abs'],'status':'PASS'};link(r,'cache_receipt',p,'INDEPENDENT_ENDPOINT_DISTRIBUTION_RECEIPT');link(r,'cache_values',p.parent/'vectors.npz','INDEPENDENT_ENDPOINT_DISTRIBUTION_NPZ',['valid']+[route+'__'+m for route in ['ind','rank'] for m in METRICS]);cache_index.append(r)
 assert len(cache_index)==4368
 inputs={}
 for u in snap['audit_units']:
  deps=u['scientific_dependencies'];items=[(u['producer_receipt'],'A07_PRODUCER_RECEIPT'),(deps['fold'],'SAVED_GROUPED_CV_FOLDS'),(deps['original_base_head'],'SAVED_ORIGINAL_BASE_PIPELINE'),(deps['draw'],'SAVED_GROUP_BOOTSTRAP_DRAWS'),(deps['historical_predictions'],'CLASSIFIER_PROBABILITY_NPZ_FILE')]+[(e,'EXTRACTION_BUNDLE_RECEIPT') for e in deps['A06_bundles'].values()]+[(e,'DERIVED_FEATURE_CACHE_RECEIPT') for e in u['producer_identity']['feature_caches'].values()]
  for e,kind in items:
   key=(e['path'],e['sha256'],kind)
   if key in inputs:continue
   r={'object_kind':kind,'original_source_path':e['path'],'derivation_note':'Exact float32 concatenation; cache member hashes and immutable A06 chunk dependencies are in the protected cache receipt. No matrix re-extraction.' if kind=='DERIVED_FEATURE_CACHE_RECEIPT' else None};link(r,'input',e['path'],kind,expected=e['sha256']);inputs[key]=r
 input_rows=list(inputs.values())
 for task in TASKS[1:]:table('metadata/reference_cache_'+task+'.csv',[r for r in cache_index if r['task']==task])
 table('metadata/reference_cache_emp_H3.csv',[r for r in cache_index if r['task']=='emp_H3']);table('SCIENTIFIC_INPUT_BINDINGS.csv',input_rows)
 publish('REFERENCE_CACHE_IDENTITY_INDEX.json',{'status':'PASS','endpoint_policy_distributions':4368,'both_independent_and_rank_routes':True,'tables':['metadata/reference_cache_'+task+'.csv' for task in TASKS],'no_new_measurement_or_logical_result_count':True});publish('CHECKPOINT_IDENTITY_OVERLAYS.json',{'effective_content_ids':read(C/'A08_INPUTS.json')['endpoint_content_ids'],'original_R3_empty_content_fields_preserved':True,'qualification_overlay':{'repository':'Georgakopoulos-Soares-lab/unlearning','commit':cfg['research_head_before'],'path':str((D5/'QUALIFICATION_OVERLAY.json').relative_to(W)),'sha256':sha(D5/'QUALIFICATION_OVERLAY.json')},'no_new_checkpoint_admission':True})
 # Validate types and every published artifact locator/hash/object-kind join before writing shards.
 new_validation=reg.validate();combined=original_map|reg.artifacts;joins=0
 for identity,d in combined.items():
  assert digest(d)==identity
  if d.get('storage_kind','IMMUTABLE_ARCHIVE_MEMBER')!='GIT_BLOB':
   e=reg.member_indices[d['archive_sha256']][d['member']];assert e['sha256']==d['sha256'] and e['bytes']==d['bytes']
 for r in rows+newcls+newlm+cache_index+input_rows+overlay:
  for name,value in r.items():
   if name.endswith('_locator') and value:
    prefix=name[:-8];d=combined[value.removeprefix('provenance:')];assert d['sha256']==r[prefix+'_sha256'] and d['hash_kind']==r[prefix+'_hash_kind'];joins+=1
  if 'estimate' not in r:continue
  for metric in ['estimate','ci_low','ci_high']:assert r[metric] not in [None,''] and math.isfinite(float(r[metric]))
  assert int(r['bootstrap_attempted'])==int(r['bootstrap_valid'])+int(r['bootstrap_invalid']);assert int(r['sample_count'])==(1497 if r['task']=='emp_H3' else 512)
 partitions=[];key_sources={};scopes=[('audited_A07',rows),('new_adjacent_classifier',newcls),('new_LM',newlm)]
 for scope,group in scopes:
  fields=sorted(set().union(*(set(r) for r in group)));buckets=collections.defaultdict(list)
  for r in group:buckets[(r['family'],r['task'],r['split'])].append(r)
  for (family,task,split),rs in sorted(buckets.items()):
   ordered=sorted(rs,key=lambda r:r['logical_id'])
   for part,start in enumerate(range(0,len(ordered),500)):
    chunk=ordered[start:start+500];s=io.StringIO(newline='');writer=csv.DictWriter(s,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(chunk);data=s.getvalue().encode();assert len(data)<10*1024**2;name=f'tables/{scope}/{family}/{task}/{split}.part{part:03d}.csv';publish(name,data);partinfo={'scope':scope,'family':family,'task':task,'split':split,'path':name,'rows':len(chunk),'bytes':len(data),'sha256':bh(data),'fields':fields,'logical_id_sha256':digest([r['logical_id'] for r in chunk])};partitions.append(partinfo)
    for ordinal,r in enumerate(chunk,2):key_sources[r['logical_id']]={'logical_id':r['logical_id'],'owner_stage':r['owner_stage'],'partition':name,'CSV_line':ordinal}
 for r in a6:key_sources[r['logical_id']]={'logical_id':r['logical_id'],'owner_stage':'A06','partition':'git:ba340d0f4706b1941f62a4d6256bf78ab99030eb/'+('LM_RESULTS.csv' if r['table_kind']=='LM_marginal' else 'RESULTS_LONG.csv' if r['table_kind']=='classifier_marginal' else 'PAIRED_CONTRASTS.csv'),'CSV_line':None}
 table('RELEASE_OVERLAY.csv',[{k:r.get(k) for k in sorted(set().union(*(set(e) for e in overlay)))} for r in overlay]);table('AMENDMENT_KEY_SOURCES.csv',sorted(key_sources.values(),key=lambda r:r['logical_id']))
 manifest={'schema':'pod-a-A08-partitions-v2','status':'PASS','shards':partitions,'new_uncompressed_shard_limit_bytes':10*1024**2,'deterministic_grouping':'Scope/family/task/reporting split, logical_id order, maximum500 rows per shard','audited_A07_rows':12300,'new_classifier_rows':16380,'new_LM_rows':70,'immutable_reused_A06':reused,'exact_amendment_union':33684,'missing_extra_duplicate_keys':0,'original_A07_values_and_status_preserved':True,'A07_release_status_field':'A08_release_status; original status remains COMPLETE_UNVERIFIED','all_new_contrast_status':'VERIFIED','canonical_key_generator_sha256':sha(A/'code/key_contract5.py')};publish('TABLE_PARTITIONS.json',manifest);put(C/'TABLE_PARTITIONS.json',manifest)
 registry_parts=[]
 for prefix in '0123456789abcdef':
  subset={k:v for k,v in sorted(combined.items()) if k.startswith(prefix)};name='provenance/registry-'+prefix+'.json';publish(name,{'artifacts':subset});assert (D/name).stat().st_size<10*1024**2;registry_parts.append({'path':name,'entries':len(subset),'sha256':sha(D/name)})
 publish('PRIVATE_PROVENANCE_MAP.json',{'schema':'pod-a-A08-typed-provenance-v2','status':'PASS','partitioned':True,'shards':registry_parts,'entries':len(combined),'legacy_A07_descriptors_preserved':True,'hash_object_kind_and_selector_are_distinct':True,'public_input_commit_for_new_backup_receipts':reg.public_input_commit});publish('PORTABLE_PROVENANCE_VALIDATION.json',{'status':'PASS','typed_descriptors':len(combined),'row_locator_hash_type_joins':joins,'all_archive_descriptors_resolve_to_verified_member_indices':True,'GIT_descriptors_checked_against_exact_committed_bytes':True,'source_A07_map_sha256':sha(D7/'PRIVATE_PROVENANCE_MAP.json')})
 # Protect compact member indexes sufficient to regenerate registry joins from the later metadata consumer.
 put(C/'DESCRIPTOR_MEMBER_INDICES.json',reg.immutable_map())
 validation={'status':'PASS','exact_amendment_keys':33684,'reused_A06_keys':4934,'audited_A07_keys':12300,'new_adjacent_classifier_keys':16380,'new_paired_LM_keys':70,'missing_keys':0,'extra_keys':0,'duplicate_keys':0,'shards':len(partitions),'max_shard_bytes':max(p['bytes'] for p in partitions),'original_A07_cells_unchanged':True,'typed_descriptors':len(combined),'typed_row_joins':joins,'producer_seals_untouched':True,'all_numeric_cells_finite':True};publish('PUBLICATION_VALIDATION.json',validation);put(C/'PUBLICATION_VALIDATION.json',validation);publish('INVALIDATED_OUTPUTS.json',{'status':'NONE','invalidated_logical_ids':[],'scientific_discrepancies':[],'supervisor_metadata_issue':'Preserved in SUPERVISOR_REPAIR.json; no scientific output invalidation or recomputation'})
 publish('RESULT_SCHEMAS.json',{'schema':'pod-a-A08-R5-release-v2','inherited_A07_schema_sha256':sha(D7/'RESULT_SCHEMAS.json'),'per_shard_field_lists':'TABLE_PARTITIONS.json','logical_key_definition':'Unchanged A05 code/keys5.py, copied as key_contract5.py','original_A07_status':'Preserved COMPLETE_UNVERIFIED','A08_release_status':'VERIFIED only after all-unit audit, required prospective refit and task fresh recovery','new_contrast_status':'VERIFIED with independent two-route and fresh-panel evidence','all_numeric_data':'Full precision; display rounding only','LM_axes':'N/A representation/CV_seed, no layer/seed multiplication','classifier_target_count':'Null; not LM token counts','missing_number_encoding':'Empty CSV cell with explicit unavailability/interpretation field; never fabricated zeros','interval_scope':'Pointwise exploratory unadjusted, conditional on fitted heads','typed_locators':'provenance:<descriptor digest>, registry identifies file kind, exact immutable storage and selector','historical_R3_identity':'Original empty field preserved; admitted native tensor identity is an explicit effective overlay'})
 print(json.dumps(validation))
if __name__=='__main__':main()
