"""Pinned-defect reproduction plus independent v2 adversarial qualification; synthetic only."""
from common import *
import importlib.util,copy
from qualification_v2 import assess,ingest_scalar
from independent_v2 import check_assessment,check_ingested
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
oldroot=A.with_name('attempt-001')/'code';old=load_module('pinned_old_eligibility',oldroot/'eligibility.py');oi=load_module('pinned_old_independent',oldroot/'independent.py')
c=read(A/'inputs/CANDIDATE_BINDINGS.json')[3];candidates={c['alias']:c};sources={'fixture':{'source_sha256':'a'*64,'source_revision':'fixture-v1'}}
ref={'content_sha256':'b'*64,'task_definition':'SYNTHETIC_TASK','split':'dev','cohort_id':'SYNTHETIC_COHORT','evaluation_protocol_sha256':'c'*64,'readout':'synthetic-head','metric_definition':'synthetic AUROC','units':'fraction','direction':'higher_better','aggregation_rule':'synthetic rule'};refs={'REF':ref}
r={k:c[k] for k in ['candidate_id','step','content_sha256','config_sha256','tokenizer_sha256']};r.update(record_id='SYNTHETIC_ONLY',source_id='fixture',source_safety='AGGREGATE_ONLY_NO_EXAMPLES',**sources['fixture'],candidate_alias=c['alias'],identity_type='logical_model_tensor_content_sha256',exact_checkpoint_content_sha256=c['content_sha256'],task_definition='SYNTHETIC_TASK',split='dev',cohort_id='SYNTHETIC_COHORT',evaluation_protocol_sha256='c'*64,implementation_version='fixture1',readout='synthetic-head',measurement_scope='whole_model',representation=None,metric='AUROC',metric_definition='synthetic AUROC',units='fraction',direction='higher_better',sample_denominator=10,aggregation_rule='synthetic rule',estimate='0.7',uncertainty=None,reference_id='REF');r.update({'reference_'+k:v for k,v in ref.items()})
ci={'kind':'confidence_interval','level':'0.95','method':'SYNTHETIC percentile','resampling_unit':'SYNTHETIC group','conditioning':'SYNTHETIC fixed head','low':'0.6','high':'0.8'}
cases=[]
for value in ['-1','0','1','2','NaN','nonnumeric']:
 u={**ci,'level':value};cases.append(('confidence_level_'+value,{'uncertainty':u},'CI_INVALID'))
for field in ['method','resampling_unit','conditioning']:
 for val in ['', '   ',None,'unknown']:cases.append(('provenance_'+field+'_'+repr(val),{'uncertainty':{**ci,field:val}},'CI_INVALID'))
for v in [[],[1],42,'bad',{'kind':'confidence_interval'}, {**ci,'low':'nonnumeric'},{**ci,'low':'NaN'},{**ci,'high':'Infinity'},{**ci,'low':'0.9','high':'0.8'}]:cases.append(('malformed_'+repr(v),{'uncertainty':v},'CI_INVALID'))
for field,value in [('task_definition','DIFFERENT_TASK'),('cohort_id','DIFFERENT_COHORT'),('split','train'),('evaluation_protocol_sha256','d'*64),('readout','DIFFERENT_HEAD'),('metric_definition','DIFFERENT_METRIC'),('units','percent'),('direction','lower_better'),('aggregation_rule','DIFFERENT_RULE')]:cases.append(('target_reference_'+field,{field:value},'NO_REFERENCE'))
cases += [('valid_CI',{'uncertainty':ci},'CI_VALID'),('valid_point_without_CI',{},'POINT_ONLY'),('invalid_point',{'estimate':'not numeric'},'INVALID_POINT'),('nonfinite_point',{'estimate':'NaN'},'INVALID_POINT'),('incompatible_protocol',{'protocol_compatible':False},'INCOMPATIBLE'),('unknown_exact_content',{'exact_checkpoint_content_sha256':None},'NO_REFERENCE')]
observed=[]
for name,changes,wanted in cases:
 record=copy.deepcopy(r);record.update(changes)
 try:
  prior=old.qualify(record,candidates,sources,refs);oldresult={'disposition':prior['disposition'],'ci_accepted':prior.get('ci_low') is not None,'reference_accepted':'ELIGIBLE_REFERENCE_RELATIVE' in prior.get('eligible_claims',[])}
  try:oi.audit_record(record,candidates,sources,refs,prior);oldresult['old_independent']='ACCEPTS'
  except Exception as x:oldresult['old_independent']='RAISES_'+type(x).__name__
 except Exception as x:oldresult={'raises':type(x).__name__}
 current=assess(record,ref);check_assessment(record,ref,current)
 if wanted=='CI_INVALID':assert current['point_status']=='VALID_POINT' and current['uncertainty']['status']!='QUALIFIED_REPORTED_CI'
 elif wanted=='NO_REFERENCE':assert not current['reference_comparison']
 elif wanted=='CI_VALID':assert current['uncertainty']['status']=='QUALIFIED_REPORTED_CI'
 elif wanted=='POINT_ONLY':assert current['point_status']=='VALID_POINT' and current['uncertainty']['status']=='MISSING'
 elif wanted=='INVALID_POINT':assert current['scientific_status']=='INVALID_RECORD'
 elif wanted=='INCOMPATIBLE':assert current['scientific_status']=='INCOMPATIBLE_PROTOCOL'
 observed.append({'name':name,'old_pinned_behavior':oldresult,'new_behavior':current,'independent_check':'PASS'})
source={'id':'SYNTHETIC_SOURCE','sha256':'a'*64,'candidate_alias_associations_only':['candidate_09']};row={'observation_id':'synthetic:1','source_id':source['id'],'source_sha256':source['sha256'],'value':'1.3953843116760254','tag':'forget loss validation','step':'1500','duplicate_step':'True'}
for label,changes in [('missing_model_duplicate_step',{}),('other_duplicate_value',{'value':'1.3952388763427734','observation_id':'synthetic:2'}),('missing_value',{'value':None}),('explicit_null_value',{'value':'null'}),('wrong_source_sha',{'source_sha256':'f'*64})]:
 rr={**row,**changes};out=ingest_scalar(rr,source);check_ingested(rr,source,out);observed.append({'name':'real_ingestion_'+label,'new_behavior':out,'independent_check':'PASS'})
 # A forged acceptance result must be rejected by independent checker.
 mutant=copy.deepcopy(out);mutant['scientific_status']='QUALIFIED_MATCHED_COMPARISON';mutant['reference_comparison']=True
 try:check_ingested(rr,source,mutant)
 except AssertionError:pass
 else:raise AssertionError('Independent checker accepted forged qualification')
receipt={'status':'PASS','tests':len(observed),'synthetic_only':True,'old_producer_sha256':sha(oldroot/'eligibility.py'),'old_independent_sha256':sha(oldroot/'independent.py'),'old_source_commit':PRIOR,'new_producer_sha256':sha(A/'code/qualification_v2.py'),'new_independent_sha256':sha(A/'code/independent_v2.py'),'cases':observed};save(C/'VALIDATOR_TESTS.json',receipt);print('V2_VALIDATOR_TESTS_PASS',len(observed),flush=True)
