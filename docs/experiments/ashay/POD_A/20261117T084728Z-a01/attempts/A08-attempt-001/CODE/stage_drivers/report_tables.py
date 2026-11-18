"""Full-precision verified reporting joins and explicit historical reuse; no fits."""
from common import *
from research_guard import guard
import collections,math
from functools import lru_cache
_sha_uncached=sha
@lru_cache(maxsize=None)
def sha(p):return _sha_uncached(Path(p))
A7=A.parent/'A07-attempt-001';A6=A.parent/'A06-attempt-001';D7=D.parent/'A07-attempt-001';D6=D.parent/'A06-attempt-001';C6=C.parent/'A06-attempt-001';C7=C.parent/'A07-attempt-001';R3=H.parent.parent/'R3/multiretain-comparison-v1-final-20261110T173945Z';CONTROL=H.parent.parent/'controls/benign-followup-v1'
FIELDS=['checkpoint_alias','checkpoint_content_id','original_endpoint_id','reference','reference_content_id','reference_endpoint_id','task','split','representation','CV_seed','policy','source_policy','reference_policy','metric','direction','metric_orientation','estimate','ci_low','ci_high','sample_count','group_count','target_count','bootstrap_attempted','bootstrap_valid','bootstrap_invalid','status','missing_reason','ci_missing_reason','lineage','measurement_attempt','ingestion_status','ancestry_status','exposure_status','family','adjacent','protocol_sha256','coverage_plan_sha256','source_sha256','input_sha256','prediction_sha256','reference_prediction_sha256','draw_sha256','producer_receipt','producer_receipt_sha256','audit_receipt','audit_receipt_sha256','sampled_refit_receipt_sha256','verification_scope','contrast_id']
IDENTITIES={r['alias']:r for r in read(D.parent/'A05-attempt-001/CHECKPOINT_READINESS.json')['rows']}
OLD={}
AUDIT_SOURCE_HASH=sha(C/'SOURCE_IDENTITY.json');COHORTS=read(D.parent/'A05-attempt-001/PROTOCOL_FROZEN.json')['cohorts']
for dep,root in [('base_R1',H),('controls',CONTROL),('R3',R3)]:
 for e in read(C03/('PAYLOAD_CHECKSUMS_'+dep+'.json'))['files']:OLD[str(root/e['path'])]=e
def old(p):
 p=Path(p);e=OLD[str(p)];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];return p
def historical_evidence(root,x):
 task=x['task'];key=key_for(x.get('layer',x.get('representation')));seed=str(x.get('seed',x.get('cv_seed')));split='test' if normsplit(x['split'])=='test_exploratory' else x['split'];unit=root/('probes/H3' if task=='emp_H3' else 'probes/other_five')/task/key/('seed'+seed);pred=unit/(split+'_predictions.npz');receipt=unit/'COMPLETE.json';draw=H/('probes/H3' if task=='emp_H3' else 'probes/other_five')/task/(split+'_resampling.npz');return {'producer_receipt':str(receipt),'producer_receipt_sha256':OLD[str(receipt)]['sha256'],'prediction_sha256':OLD[str(pred)]['sha256'],'draw_sha256':OLD[str(draw)]['sha256'],'input_sha256':COHORTS['H3' if task=='emp_H3' else 'other_five']}
def csvrows(p):return list(csv.DictReader(Path(p).open()))
def normsplit(s):return 'test_exploratory' if s in ['test','test_exploratory'] else s
def key_for(rep):return 'final_norm' if rep=='decoder.final_norm' else rep.replace('decoder.layers.','decoder_layer_')
def canon(rep):return 'decoder.final_norm' if rep=='final_norm' else rep.replace('decoder_layer_','decoder.layers.')
def canonical_policy(policy):return {'fixed_base_scaler_and_head':'fixed_original_base'}.get(policy,policy)
def rowbase(alias,task,split,representation,seed,policy,metric):
 ident=IDENTITIES[alias];r={k:None for k in FIELDS};r.update(checkpoint_alias=alias,checkpoint_content_id=ident['model_tensor_content_sha256'],original_endpoint_id=ident['endpoint_id'],task=task,split=normsplit(split),representation=representation,CV_seed=None if seed is None else int(seed),policy=canonical_policy(policy),source_policy=policy,metric=metric,direction='metric_value',metric_orientation='lower' if metric in ['classification_cross_entropy','causal_nll','perplexity'] else 'higher',sample_count=1497 if task=='emp_H3' else 512,group_count=1497 if task=='emp_H3' else 511 if task=='gue_splice_reconstructed' else 512,status='VERIFIED',lineage='NEW',ingestion_status='REUSED_IN_A08',ancestry_status='UNKNOWN',exposure_status='UNKNOWN',protocol_sha256=cfg['protocol_sha256'],coverage_plan_sha256=cfg['coverage_plan_sha256'],source_sha256=AUDIT_SOURCE_HASH);return r
def parse_numeric(row):
 for k in ['estimate','ci_low','ci_high']:row[k]=None if row[k] in ['',None] else float(row[k])
 for k in ['CV_seed','sample_count','group_count','target_count','bootstrap_attempted','bootstrap_valid','bootstrap_invalid']:row[k]=None if row[k] in ['',None,'N/A'] else int(row[k])
 return row
def write(name,rows):
 guard(allow_dirty=True)
 with (D/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(rows)
def check_unique(rows,paired=False):
 keys=[tuple(r[k] for k in (['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256'] if paired else ['original_endpoint_id','task','split','representation','CV_seed','policy','metric','protocol_sha256'])) for r in rows];assert len(keys)==len(set(keys))
def historical_point_rows():
 out=[];auditref=ref(C03/'STRUCTURAL_REUSE_AUDIT.json')
 for root,mapping in [(H,{'base':'base','h3_only_maxent':'R1'}),(R3,{'three_source_config2151':'R3'})]:
  path=old(root/'reports/metrics.csv');path_hash=sha(path)
  for x in csvrows(path):
   if x['checkpoint'] not in mapping:continue
   assert x['status']=='completed' and x['value']!='';alias=mapping[x['checkpoint']];r=rowbase(alias,x['task'],x['split'],x['layer'],x['seed'],x['probe_policy'],x['metric']);r.update(estimate=float(x['value']),status='REUSED_VALIDATED',lineage='REUSED',measurement_attempt='HISTORICAL_NOVEMBER10',input_sha256=path_hash,producer_receipt=str(path),producer_receipt_sha256=path_hash,audit_receipt=auditref['path'],audit_receipt_sha256=auditref['sha256'],verification_scope='Prior full historical producer-independent audits accepted through A03; no A08 refitting or re-extraction',ci_missing_reason='Inherited marginal report provides point estimates only; compatible paired intervals are retained');r.update(historical_evidence(root,x));out.append(r)
 assert len(out)==16380;return out
def historical_pair_rows():
 out=[];auditref=ref(C03/'STRUCTURAL_REUSE_AUDIT.json');mapping={'h3_only_minus_base':('R1','base'),'new_minus_base':('R3','base'),'new_minus_h3_only':('R3','R1')}
 for root in [H,R3]:
  path=old(root/'reports/native_contrasts.csv');path_hash=sha(path)
  for x in csvrows(path):
   if x['contrast'] not in mapping:continue
   alias,reference=mapping[x['contrast']];policy='fixed_original_base' if 'fixed' in x['policy'] else 'independent_refit';r=rowbase(alias,x['task'],x['split'],canon(x['layer']),x['cv_seed'],policy,x['metric']);r.update(reference=reference,reference_content_id=IDENTITIES[reference]['model_tensor_content_sha256'],reference_endpoint_id=IDENTITIES[reference]['endpoint_id'],reference_policy=policy,direction='target-reference',estimate=float(x['difference']),ci_low=float(x['ci_low']),ci_high=float(x['ci_high']),bootstrap_attempted=int(x['valid'])+int(x['invalid']),bootstrap_valid=int(x['valid']),bootstrap_invalid=int(x['invalid']),status='REUSED_VALIDATED',lineage='REUSED',measurement_attempt='HISTORICAL_NOVEMBER10',family=alias+'_minus_'+reference,adjacent=False,input_sha256=path_hash,producer_receipt=str(path),producer_receipt_sha256=path_hash,audit_receipt=auditref['path'],audit_receipt_sha256=auditref['sha256'],verification_scope='Prior independently verified historical domain only; no new cross-runtime R3 effects',contrast_id=digest({'target':alias,'reference':reference,'task':x['task'],'split':r['split'],'representation':r['representation'],'seed':r['CV_seed'],'policy':policy,'protocol':cfg['protocol_sha256']}));r.update(historical_evidence(root,x));out.append(r)
 assert len(out)==16380;return out
def current_rows(source,stage,paired=False):
 out=[];root=A7 if stage=='A07' else A6
 for x in csvrows(source):
  if paired and x['policy']=='actual_causal_head':continue
  r=rowbase(x['checkpoint_alias'],x['task'],x['split'],x['representation'],x['CV_seed'],x['policy'],x['metric']);r.update({k:x[k] for k in FIELDS if k in x});r['original_endpoint_id']=IDENTITIES[x['checkpoint_alias']]['endpoint_id'];r['measurement_attempt']='A07-attempt-001' if stage=='A07' else 'A06-attempt-001';r['ingestion_status']='REUSED_IN_A08';r['lineage']='NEW';r['status']='VERIFIED';r['source_sha256']=AUDIT_SOURCE_HASH;r['coverage_plan_sha256']=cfg['coverage_plan_sha256'];r['ancestry_status']='UNKNOWN';r['exposure_status']='UNKNOWN';r['producer_receipt']=str(root/x['receipt']);r['producer_receipt_sha256']=sha(root/x['receipt']);uid=f"{x['checkpoint_alias']}/{x['task']}/{key_for(x['representation'])}/seed{x['CV_seed']}"
  if stage=='A07':
   ar=A/'audits'/uid/'COMPLETE.json';assert read(ar)['status']=='PASS';r['audit_receipt']=str(ar.relative_to(A));r['audit_receipt_sha256']=sha(ar);refit=A/'refits'/uid/'COMPLETE.json';r['sampled_refit_receipt_sha256']=sha(refit) if refit.exists() else None;r['verification_scope']='A08 all saved probabilities,points,everydraw,intervals; numerical fresh CV refits only for declared60-unit panel'
  else:
   ar=root/'h3'/x['checkpoint_alias']/key_for(x['representation'])/('seed'+x['CV_seed'])/'AUDIT.json';r['audit_receipt']=str(ar);r['audit_receipt_sha256']=sha(ar);r['verification_scope']='A06 verified H3 audit reused unchanged; new R6−R4 contrasts independently checked in A08';split='test' if x['split']=='test_exploratory' else x['split'];r['draw_sha256']=sha(old(H/'probes/H3/emp_H3'/(split+'_resampling.npz')))
  if paired:
   reference=x['reference'];r['reference_prediction_sha256']=x.get('reference_prediction_sha256') or x.get('reference_source_sha256') or None;r['reference_policy']='control' if reference.startswith('control_') else x['policy'];r['reference_endpoint_id']=x['reference_endpoint_id'];r['reference_content_id']=IDENTITIES[reference]['model_tensor_content_sha256'] if reference in IDENTITIES else None;r['family']=x['checkpoint_alias']+'_minus_'+reference;r['direction']='target-reference';r['adjacent']=False
  out.append(parse_numeric(r))
 return out
def new_analysis_rows():
 rows=[]
 for p in sorted((A/'analysis/R6_minus_R4').glob('*/*/*/seed*/COMPLETE.json')):
  seal=read(p);record=read(p.parent/'ANALYSIS.json');assert seal['status']==record['status']=='PASS'
  for x in record['rows']:
   r=rowbase('R6',x['task'],x['split'],x['representation'],x['CV_seed'],x['policy'],x['metric']);r.update({k:v for k,v in x.items() if k in FIELDS});r['original_endpoint_id']=x['target_endpoint_id'];r['prediction_sha256']=x['target_prediction_sha256'];r['producer_receipt']=str((A6/'h3' if x['task']=='emp_H3' else A7/'probes')/'R6'/x['task']/key_for(x['representation'])/('seed'+str(x['CV_seed']))/'COMPLETE.json') if x['task']!='emp_H3' else str(A6/'h3/R6'/key_for(x['representation'])/('seed'+str(x['CV_seed']))/'COMPLETE.json');r['audit_receipt_sha256']=sha(p);r['verification_scope']='New predeclared nonadjacent paired effects checked with independent pairwise and rank routes for every draw';rows.append(parse_numeric(r))
 assert len(rows)==5460;return rows
def lm_tables():
 points=[];pairs=[];historical_map={'base':'base','h3_only_maxent':'R1','new_checkpoint':'R3','supplied_three_source_config_iter2151':'R3'};auditref=ref(C03/'NUMERICAL_RECOVERY_CHECKS.json')
 for root,allowed in [(H,{'base','R1'}),(R3,{'R3'})]:
  path=old(root/'reports/LM_METRICS.csv')
  for x in csvrows(path):
   alias=historical_map.get(x['arm']);
   if alias not in allowed or normsplit(x['split']) not in ['dev','test_exploratory']:continue
   for m in ['causal_nll','perplexity']:
    r=rowbase(alias,x['task'],x['split'],None,None,'actual_causal_head',m);r.update(estimate=float(x[m]),sample_count=int(x['n']),target_count=int(x['target_count']),status='REUSED_VALIDATED',lineage='REUSED',measurement_attempt='HISTORICAL_NOVEMBER10',ci_missing_reason='Inherited LM marginal table provides point only; paired LM intervals remain available',input_sha256=sha(path),producer_receipt=str(path),producer_receipt_sha256=sha(path),audit_receipt=auditref['path'],audit_receipt_sha256=auditref['sha256'],verification_scope='Prior actual causal-head summed-loss/target aggregation and uncertainty audit, accepted by A03');points.append(r)
  path=old(root/'reports/LM_CONTRASTS.csv')
  for x in csvrows(path):
   target,reference=({'h3_only_maxent_minus_base':('R1','base'),'new_checkpoint_minus_base':('R3','base'),'new_checkpoint_minus_h3_only':('R3','R1')}.get(x['contrast'],(None,None)))
   if target not in allowed:continue
   r=rowbase(target,x['task'],x['split'],None,None,'actual_causal_head',x['metric']);r.update(reference=reference,reference_content_id=IDENTITIES[reference]['model_tensor_content_sha256'],reference_endpoint_id=IDENTITIES[reference]['endpoint_id'],reference_policy='actual_causal_head',direction='target-reference',estimate=float(x['difference']),ci_low=float(x['ci_low']),ci_high=float(x['ci_high']),bootstrap_attempted=int(x['valid'])+int(x['invalid']),bootstrap_valid=int(x['valid']),bootstrap_invalid=int(x['invalid']),status='REUSED_VALIDATED',lineage='REUSED',measurement_attempt='HISTORICAL_NOVEMBER10',family=target+'_minus_'+reference,adjacent=False,input_sha256=sha(path),producer_receipt=str(path),producer_receipt_sha256=sha(path),audit_receipt=auditref['path'],audit_receipt_sha256=auditref['sha256'],verification_scope='Prior verified historical-domain LM paired uncertainty',contrast_id=digest({'family':target+'_minus_'+reference,'task':x['task'],'split':normsplit(x['split']),'metric':x['metric'],'policy':'actual_causal_head'}));pairs.append(r)
 for x in csvrows(D6/'LM_RESULTS.csv'):
  r=rowbase(x['checkpoint_alias'],x['task'],x['split'],None,None,'actual_causal_head',x['metric']);r.update({k:x[k] for k in FIELDS if k in x});r.update(representation=None,CV_seed=None,measurement_attempt='A06-attempt-001',ingestion_status='REUSED_IN_A08',status='VERIFIED',original_endpoint_id=IDENTITIES[x['checkpoint_alias']]['endpoint_id'],producer_receipt=str(A6/x['receipt']),producer_receipt_sha256=sha(A6/x['receipt']),audit_receipt=str(A6/x['receipt']),audit_receipt_sha256=sha(A6/x['receipt']),verification_scope='A06 independent actual-logit corpus/group-draw checks reused, no A08 LM forwards');points.append(parse_numeric(r))
 for x in csvrows(D7/'A06_PAIRED_CONTRASTS.normalized.v1.csv'):
  if x['policy']!='actual_causal_head':continue
  r=rowbase(x['checkpoint_alias'],x['task'],x['split'],None,None,'actual_causal_head',x['metric']);r.update({k:x[k] for k in FIELDS if k in x});r.update(representation=None,CV_seed=None,reference_policy='actual_causal_head',measurement_attempt='A06-attempt-001',ingestion_status='REUSED_IN_A08',status='VERIFIED',original_endpoint_id=IDENTITIES[x['checkpoint_alias']]['endpoint_id'],reference_content_id=IDENTITIES[x['reference']]['model_tensor_content_sha256'],producer_receipt=str(A6/x['receipt']),producer_receipt_sha256=sha(A6/x['receipt']),audit_receipt=str(A6/x['receipt']),audit_receipt_sha256=sha(A6/x['receipt']),family=x['checkpoint_alias']+'_minus_'+x['reference'],adjacent=False,verification_scope='A06 independently verified causal LM paired uncertainty reused');pairs.append(parse_numeric(r))
 for p in (A/'analysis/LM_R6_minus_R4').glob('*/*/COMPLETE.json'):
  for x in read(p.parent/'ANALYSIS.json')['rows']:
   r=rowbase('R6',x['task'],x['split'],None,None,'actual_causal_head',x['metric']);r.update({k:v for k,v in x.items() if k in FIELDS});r.update(original_endpoint_id=x['target_endpoint_id'],prediction_sha256=x['target_prediction_sha256'],audit_receipt_sha256=sha(p),verification_scope='New nonadjacent LM paired corpus/group ratio differences; independent fsum and matrix routes');pairs.append(parse_numeric(r))
 assert len(points)==70 and len(pairs)==112,(len(points),len(pairs));return points,pairs
def main():
 assert read(C/'NUMERICAL_AUDIT.json')['status']=='PASS' and read(C/'AUDIT_REFIT_RECEIPT.json')['status']=='PASS';assert read(C/'BACKUP_analysis.json')['status']=='PASS'
 historical=historical_point_rows();a7=current_rows(D7/'RESULTS_LONG.csv','A07');h3=current_rows(D6/'RESULTS_LONG.csv','A06');metrics=historical+a7+h3;assert len(metrics)==27300;check_unique(metrics);write('VERIFIED_METRICS.csv',metrics)
 partitions={'PAIRED_CONTRASTS.csv':current_rows(D7/'PAIRED_CONTRASTS.csv','A07',True),'PAIRED_CONTRASTS.H3_reused.csv':current_rows(D7/'A06_PAIRED_CONTRASTS.normalized.v1.csv','A06',True),'PAIRED_CONTRASTS.historical.csv':historical_pair_rows(),'PAIRED_CONTRASTS.R6_minus_R4.csv':new_analysis_rows()};allpairs=[r for rows in partitions.values() for r in rows];assert len(allpairs)==45360;check_unique(allpairs,True)
 for name,rows in partitions.items():write(name,rows)
 lm,lp=lm_tables();check_unique(lm);check_unique(lp,True);write('LM_METRICS_VERIFIED.csv',lm);write('LM_CONTRASTS_VERIFIED.csv',lp)
 tablemap={'schema':'pod-a-a08-table-partitions-v1','logical_PAIRED_CONTRASTS':{'rows':len(allpairs),'partitions':[{'file':n,'rows':len(rows),'sha256':sha(D/n)} for n,rows in partitions.items()],'interpretation':'Union all listed partitions; main CSV is A07 other-five comparisons, not a reduced full denominator'},'VERIFIED_METRICS':{'file':'VERIFIED_METRICS.csv','rows':27300},'LM_METRICS_VERIFIED':{'rows':70,'primary_units':35,'full_primary_universe':49},'LM_CONTRASTS_VERIFIED':{'rows':112,'new_R6_minus_R4_rows':14},'semantic_mapping':{'per-unit numerical receipts':'AUDIT_UNIT_RECORDS.jsonl and NUMERICAL_AUDIT.json immutable receipt locators','partitioned PAIRED_CONTRASTS.csv':'All four physical files jointly form the logical table; no score-based subset'}};publish('TABLE_PARTITIONS.json',tablemap)
 schemas={'schema':'pod-a-a08-result-schemas-v1','columns':FIELDS,'metric_primary_key':['original_endpoint_id','task','split','representation','CV_seed','policy','metric','protocol_sha256'],'paired_primary_key':['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256'],'policy_alias_mapping':{'fixed_base_scaler_and_head':'fixed_original_base'},'source_policy':'Preserves inherited producer spelling; canonical policy resolves the verified same original-base scaler/head operation','status_values':['VERIFIED','REUSED_VALIDATED','PENDING','BLOCKED','FAILED','UNDEFINED'],'numeric_null_encoding':'CSV empty -> JSON null; unknown never zero','numeric_fields':['estimate','ci_low','ci_high'],'integer_or_null':['CV_seed','sample_count','group_count','target_count','bootstrap_attempted','bootstrap_valid','bootstrap_invalid'],'LM_axes':'representation and CV_seed are null; primary LM unit count35/49, no layer/seed multiplication','checkpoint_content_id_null_reason':'R3native tensor content identity unavailable; original folder ID and verified historical feature/probe domain preserved, livebridge not admitted','historical_marginal_CI':'Not in inherited point reports; intervals/drawcounts null with ci_missing_reason; accepted paired historical intervals retained','measurement_lineage':'NEW/REUSED refers to original measurement attempt, separate from A08 ingestion and checkpoint ancestry','interval_scope':'Pointwise unadjusted paired exact/RC-group bootstrap, conditional on fitted heads','table_partitions':'TABLE_PARTITIONS.json'};publish('RESULT_SCHEMAS.json',schemas)
 print(json.dumps({'status':'PASS','metric_rows':27300,'paired_rows':45360,'LM_metric_rows':70,'LM_contrast_rows':112,'new_R6_R4_classifier_rows':5460}))
if __name__=='__main__':main()
