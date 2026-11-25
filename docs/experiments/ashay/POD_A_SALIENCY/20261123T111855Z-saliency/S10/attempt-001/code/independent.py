"""Independent metadata and exact-decimal reconciliation; never calls producer eligibility."""
from fractions import Fraction
import re
def audit_record(r,candidates,sources,reference_bindings,actual):
 # This checker independently derives the admitted descriptive and layerwise conditions.
 forbidden=any(k in r for k in ('examples','sequences','per_example_predictions','per_example_losses','raw_forget_data'))
 if forbidden or r.get('source_safety')!='AGGREGATE_ONLY_NO_EXAMPLES':assert actual['disposition']=='INCOMPATIBLE';return
 s=sources.get(r.get('source_id'))
 if s is None or (r.get('source_revision'),r.get('source_sha256'))!=(s.get('source_revision'),s.get('source_sha256')):assert actual['disposition']=='PENDING_IDENTITY';return
 if r.get('duplicate_of') or r.get('superseded_by'):assert actual['disposition']=='DUPLICATE_OR_SUPERSEDED';return
 c=candidates.get(r.get('candidate_alias'))
 identity_valid=c is not None and r.get('identity_type')=='logical_model_tensor_content_sha256' and all(r.get(f)==c[f] for f in ('candidate_id','step','content_sha256','config_sha256','tokenizer_sha256'))
 if not identity_valid:assert actual['disposition']=='PENDING_IDENTITY';return
 mandatory=('task_definition','split','cohort_id','evaluation_protocol_sha256','implementation_version','readout','measurement_scope','metric','metric_definition','units','direction','sample_denominator','aggregation_rule')
 if not all(r.get(k) is not None and r.get(k)!='' for k in mandatory):assert actual['disposition']=='PENDING_PROTOCOL';return
 if r['split'] not in ('dev','train','external_declared_evaluation'):assert actual['disposition']=='INCOMPATIBLE';return
 if r['measurement_scope'] not in ('whole_model','specified_output_head','layerwise_probe','task_aggregate_unmapped'):assert actual['disposition']=='PENDING_PROTOCOL';return
 if type(r['sample_denominator']) is not int or r['sample_denominator']<=0:assert actual['disposition']=='PENDING_PROTOCOL';return
 layer=r.get('measurement_scope')=='layerwise_probe';rep=r.get('representation');known=rep=='decoder.final_norm' or bool(isinstance(rep,str) and re.fullmatch(r'decoder\.layers\.(?:[0-9]|1[0-9]|2[0-4])',rep))
 if layer and not(known and r.get('hook_definition')):assert actual['disposition']=='PENDING_PROTOCOL';return
 if not layer and rep is not None:assert actual['disposition']=='INCOMPATIBLE';return
 ranking=r['metric'] in ('AUROC','AP','accuracy','balanced_accuracy')
 if ranking:
  if r['direction']!='higher_better' or r['units'] not in ('fraction','percent'):assert actual['disposition']=='INCOMPATIBLE';return
  try:number=Fraction(str(r['estimate']))
  except (ValueError,TypeError,ZeroDivisionError):assert actual['disposition']=='INCOMPATIBLE';return
  ceiling=100 if r['units']=='percent' else 1
  if number<0 or number>ceiling:assert actual['disposition']=='INCOMPATIBLE';return
  expected=number/(100 if r['units']=='percent' else 1)
 else:
  if r['metric'] not in ('cross_entropy','LM_NLL','LM_PPL'):assert actual['disposition']=='PENDING_PROTOCOL';return
  expected=Fraction(str(r['estimate']))
  wanted=('perplexity' if r['metric']=='LM_PPL' else 'nats_per_target' if r['metric']=='LM_NLL' else 'nats_per_example')
  if r['direction']!='lower_better' or r['units']!=wanted:assert actual['disposition']=='INCOMPATIBLE';return
  if expected<0:assert actual['disposition']=='INCOMPATIBLE';return
 uncertainty=r.get('uncertainty')
 qualified_CI=uncertainty is not None and uncertainty.get('kind')=='confidence_interval' and all(uncertainty.get(k) is not None for k in ('level','method','resampling_unit','conditioning','low','high'))
 if qualified_CI and Fraction(str(uncertainty['low']))>Fraction(str(uncertainty['high'])):assert actual['disposition']=='INCOMPATIBLE';return
 assert actual['disposition']=='ELIGIBLE_CHECKPOINT_DESCRIPTION' and Fraction(actual['estimate'])==expected
 assert ('ELIGIBLE_LAYERWISE' in actual['eligible_claims'])==layer
 if not qualified_CI:assert actual['ci_low'] is None and actual['ci_high'] is None and actual['missing_uncertainty_reason']
 else:
  scale=100 if r['units']=='percent' else 1;assert Fraction(actual['ci_low'])==Fraction(str(uncertainty['low']))/scale and Fraction(actual['ci_high'])==Fraction(str(uncertainty['high']))/scale
 ref=reference_bindings.get(r.get('reference_id'));eligible_ref=ref is not None and all(r.get('reference_'+f)==ref[f] for f in ('readout','cohort_id','direction','units','metric_definition','evaluation_protocol_sha256','content_sha256'));assert ('ELIGIBLE_REFERENCE_RELATIVE' in actual['eligible_claims'])==eligible_ref
 assert actual['parent_relative_eligible'] is False and actual['external_evaluation_independently_reproduced'] is False

def reconcile_no_data(inputs,outputs):
 assert inputs['discovery']['external_aggregate_sources']==[] and inputs['discovery']['external_source_records']==[]
 expected={r['candidate_id']:r for r in inputs['candidates']};assert len(expected)==9
 data=outputs['COLLABORATOR_FORGET_INPUTS.json'];joins=outputs['EXACT_JOIN_ELIGIBILITY.json'];views=outputs['RETAIN_FORGET_VIEWS.json'];pending=outputs['PENDING_FORGET_INPUTS.json']
 assert data['sources']==[] and data['normalized_records']==[] and data['partition']=={'accepted':0,'pending':0,'incompatible':0,'duplicate_or_superseded':0,'total_source_records':0}
 assert joins['record_join_decisions']==[] and views['views']==[] and views['unique_external_measurements']==0 and views['figures']==[]
 observed=[r['candidate_id'] for r in joins['candidate_coverage']];assert len(observed)==len(set(observed))==9 and set(observed)==set(expected)
 for row in joins['candidate_coverage']:
  c=expected[row['candidate_id']];assert row['content_sha256']==c['content_sha256'] and row['step']==c['step'] and row['external_source_record_ids']==[] and row['forget_estimate'] is None and row['forget_ci'] is None and row['layerwise_forget_measurements']==0 and row['reason']=='NO_AGGREGATE_SUPPLIED_IN_BOUNDED_SCOPE'
 assert {r['candidate_id'] for r in pending['candidates']}==set(expected) and pending['scientific_integration']=='PENDING' and pending['S11_retain_only_permitted'] is True
 assert inputs['baseline']['all_admitted_keys']==48924 and inputs['baseline']['all_deferred_keys']==42228
 return {'status':'PASS','candidate_assessments':9,'source_records':0,'eligible_joins':0,'record_pending_joins':0,'candidate_missing_source_slots':9,'rejected_joins':0,'integrated_views':0,'layerwise_forget_measurements':0,'original_external_evaluation_reproduced':False,'independence':'Separately written membership/null/identity/coverage checks, not producer eligibility calls; shared frozen inputs and Python primitives'}
