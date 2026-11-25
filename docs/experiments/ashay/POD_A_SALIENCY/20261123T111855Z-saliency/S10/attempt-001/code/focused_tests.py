"""All fixture observations are synthetic metadata, never collaborator measurements."""
from common import *
from eligibility import qualify,complete_partition,check_projection
from independent import audit_record
import copy
candidates={r['alias']:r for r in read(A/'inputs/CANDIDATE_BINDINGS.json')};c=candidates['candidate_04'];synthetic_source={'source_sha256':'a'*64,'source_revision':'fixture-v1'};sources={'synthetic-only':synthetic_source};reference={'content_sha256':'b'*64,'evaluation_protocol_sha256':'c'*64,'metric_definition':'synthetic ranking probability','units':'fraction','direction':'higher_better','cohort_id':'SYNTHETIC_COHORT','readout':'synthetic-head'};refs={'SYNTHETIC_REFERENCE':reference}
record={k:c[k] for k in ['candidate_id','step','content_sha256','config_sha256','tokenizer_sha256']};record.update(record_id='synthetic-fixture-001',source_id='synthetic-only',source_safety='AGGREGATE_ONLY_NO_EXAMPLES',**synthetic_source,candidate_alias=c['alias'],identity_type='logical_model_tensor_content_sha256',task_definition='SYNTHETIC_NONBIOLOGICAL_TASK',split='external_declared_evaluation',cohort_id='SYNTHETIC_COHORT',evaluation_protocol_sha256='c'*64,implementation_version='fixture-1',readout='synthetic-head',measurement_scope='whole_model',representation=None,metric='AUROC',metric_definition='synthetic ranking probability',units='fraction',direction='higher_better',sample_denominator=10,aggregation_rule='synthetic macro rule',estimate='0.700',source_precision='3 supplied decimals',uncertainty=None,reference_id='SYNTHETIC_REFERENCE');record.update({'reference_'+k:v for k,v in reference.items()});passed=[]
def case(name,changes,status,extra=None):
 r=copy.deepcopy(record);r.update(changes);actual=qualify(r,candidates,sources,refs);assert actual['disposition']==status,(name,actual);audit_record(r,candidates,sources,refs,actual)
 if extra:extra(r,actual)
 passed.append(name);return actual
case('Exact synthetic identity allows point description with unknown parent',{},'ELIGIBLE_CHECKPOINT_DESCRIPTION')
case('Correct alias wrong logical content rejected',{'content_sha256':'0'*64},'PENDING_IDENTITY')
case('Noise5 step2000 cannot substitute step2151',{'step':2151},'PENDING_IDENTITY')
case('Noise5 same label different candidate content rejected',{'content_sha256':candidates['candidate_05']['content_sha256']},'PENDING_IDENTITY')
case('Wrong tokenizer binding rejected',{'tokenizer_sha256':'0'*64},'PENDING_IDENTITY')
case('Wrong config binding rejected',{'config_sha256':'0'*64},'PENDING_IDENTITY')
case('Shard hash cannot masquerade as logical content',{'identity_type':'native_shard_sha256'},'PENDING_IDENTITY')
case('Missing interval remains null, not zero',{},'ELIGIBLE_CHECKPOINT_DESCRIPTION',lambda r,o:(_ for _ in ()).throw(AssertionError()) if o['ci_low'] is not None or o['ci_high'] is not None else None)
o=case('Explicit percent conversion preserves exact supplied decimal',{'units':'percent','estimate':'73.40'},'ELIGIBLE_CHECKPOINT_DESCRIPTION');assert o['estimate']=='0.734'
case('Percent value mislabeled fraction rejected',{'estimate':'73.40'},'INCOMPATIBLE')
case('Ranking direction cannot be inverted',{'direction':'lower_better'},'INCOMPATIBLE')
case('Duplicate record not counted as new measurement',{'duplicate_of':'synthetic-prior'},'DUPLICATE_OR_SUPERSEDED')
case('Explicit supersession preserved',{'superseded_by':'synthetic-next'},'DUPLICATE_OR_SUPERSEDED')
o=case('Wrong reference is not reference-relative eligible',{'reference_content_sha256':'0'*64},'ELIGIBLE_CHECKPOINT_DESCRIPTION');assert 'ELIGIBLE_REFERENCE_RELATIVE' not in o['eligible_claims']
o=case('Incompatible reference protocol excluded from shared comparison',{'reference_evaluation_protocol_sha256':'d'*64},'ELIGIBLE_CHECKPOINT_DESCRIPTION');assert 'ELIGIBLE_REFERENCE_RELATIVE' not in o['eligible_claims']
case('Stale source revision cannot reuse result',{'source_revision':'fixture-v2'},'PENDING_IDENTITY')
case('Stale source bytes cannot reuse result',{'source_sha256':'d'*64},'PENDING_IDENTITY')
case('Missing protocol remains pending',{'evaluation_protocol_sha256':None},'PENDING_PROTOCOL')
case('Global measurement cannot gain layerwise label',{'representation':'decoder.layers.16'},'INCOMPATIBLE')
case('Genuine layerwise scope requires hook definition',{'measurement_scope':'layerwise_probe','representation':'decoder.layers.16'},'PENDING_PROTOCOL')
o=case('Declared valid seventeenth-block hook admitted as layerwise',{'measurement_scope':'layerwise_probe','representation':'decoder.layers.16','hook_definition':'SYNTHETIC zero-based decoder block output'},'ELIGIBLE_CHECKPOINT_DESCRIPTION');assert 'ELIGIBLE_LAYERWISE' in o['eligible_claims']
case('New held-out data access not admitted',{'split':'untouched_test'},'INCOMPATIBLE')
case('Raw/per-example material excluded before values',{'source_safety':'NOT_CONFIRMED'},'INCOMPATIBLE')
case('Invalid denominator not admitted',{'sample_denominator':0},'PENDING_PROTOCOL')
case('Standard deviation is not a confidence interval',{'uncertainty':{'kind':'standard_deviation','value':'0.03'}},'ELIGIBLE_CHECKPOINT_DESCRIPTION')
o=case('Reported CI decimal conversion independently checked',{'uncertainty':{'kind':'confidence_interval','level':'0.95','method':'SYNTHETIC_METHOD','resampling_unit':'SYNTHETIC_UNIT','conditioning':'SYNTHETIC_FIXED','low':'0.6','high':'0.8'}},'ELIGIBLE_CHECKPOINT_DESCRIPTION');assert o['ci_low']=='0.6' and o['ci_high']=='0.8'
for name,action in [('Global result expanded into26falsemeasurements',lambda:check_projection(record,26)),('Normalization lost a source row',lambda:complete_partition([record],[])),('Duplicate source row after normalization',lambda:complete_partition([record],[record,record]))]:
 try:action()
 except AssertionError:passed.append(name)
 else:raise AssertionError(name+' mutation survived')
save(C/'FOCUSED_TESTS.json',{'status':'PASS','fixture_type':'SYNTHETIC_ONLY_NO_EXTERNAL_MEASUREMENTS','checks':passed,'count':len(passed),'producer_sha256':sha(A/'code/eligibility.py'),'independent_checker_sha256':sha(A/'code/independent.py'),'original_external_evaluation_reproduced':False,'completed_utc':now()});print('S10_FOCUSED_METADATA_TESTS_PASS',len(passed),flush=True)
