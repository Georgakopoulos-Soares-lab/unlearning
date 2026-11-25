"""Metadata-only aggregate qualification. No source/model/data discovery or execution."""
from decimal import Decimal
from common import digest
FORBIDDEN={'examples','sequences','per_example_predictions','per_example_losses','raw_forget_data'}
REPS={f'decoder.layers.{i}' for i in range(25)}|{'decoder.final_norm'}
RANKING={'AUROC','AP','accuracy','balanced_accuracy'}
def qualify(record,candidates,sources,references):
 r=record;reasons=[];base={'record_id':r.get('record_id'),'estimate':None,'ci_low':None,'ci_high':None,'missing_uncertainty_reason':'NOT_SUPPLIED','eligible_claims':[]}
 def decision(status,reason):return dict(base,disposition=status,reason=reason)
 if FORBIDDEN&set(r) or r.get('source_safety')!='AGGREGATE_ONLY_NO_EXAMPLES':return decision('INCOMPATIBLE','EXCLUDED_MATERIAL_OR_UNCONFIRMED_AGGREGATE_ONLY')
 source=sources.get(r.get('source_id'))
 if source is None or any(r.get(k)!=source.get(k) for k in ['source_sha256','source_revision']):return decision('PENDING_IDENTITY','SOURCE_IDENTITY_CHANGED_OR_UNKNOWN')
 if r.get('superseded_by') or r.get('duplicate_of'):return decision('DUPLICATE_OR_SUPERSEDED','EXPLICIT_SOURCE_RELATION')
 c=candidates.get(r.get('candidate_alias'))
 if c is None or r.get('identity_type')!='logical_model_tensor_content_sha256':return decision('PENDING_IDENTITY','NO_QUALIFIED_LOGICAL_CONTENT_BINDING')
 for field in ['candidate_id','content_sha256','step','config_sha256','tokenizer_sha256']:
  if r.get(field)!=c[field]:return decision('PENDING_IDENTITY','CHECKPOINT_'+field.upper()+'_MISMATCH_OR_MISSING')
 required=['task_definition','split','cohort_id','evaluation_protocol_sha256','implementation_version','readout','measurement_scope','metric','metric_definition','units','direction','sample_denominator','aggregation_rule']
 if any(r.get(k) is None or r.get(k)=='' for k in required):return decision('PENDING_PROTOCOL','EVALUATION_DEFINITION_INCOMPLETE')
 if r['split'] not in ['dev','train','external_declared_evaluation']:return decision('INCOMPATIBLE','UNAPPROVED_SPLIT_SCOPE')
 if r['measurement_scope'] not in ['whole_model','specified_output_head','layerwise_probe','task_aggregate_unmapped']:return decision('PENDING_PROTOCOL','UNKNOWN_MEASUREMENT_SCOPE')
 if r['measurement_scope']=='layerwise_probe' and (r.get('representation') not in REPS or not r.get('hook_definition')):return decision('PENDING_PROTOCOL','LAYERWISE_HOOK_IDENTITY_MISSING')
 if r['measurement_scope']!='layerwise_probe' and r.get('representation') is not None:return decision('INCOMPATIBLE','GLOBAL_SCORE_FALSE_LAYERWISE_LABEL')
 if type(r['sample_denominator']) is not int or r['sample_denominator']<=0:return decision('PENDING_PROTOCOL','INVALID_DENOMINATOR')
 try:estimate=Decimal(str(r['estimate']))
 except (ValueError,TypeError,ArithmeticError):return decision('INCOMPATIBLE','INVALID_ESTIMATE')
 if not estimate.is_finite():return decision('INCOMPATIBLE','NONFINITE_ESTIMATE')
 if r['metric'] in RANKING:
  if r['direction']!='higher_better':return decision('INCOMPATIBLE','METRIC_DIRECTION_MISMATCH')
  if r['units'] not in ['fraction','percent']:return decision('INCOMPATIBLE','METRIC_UNIT_MISMATCH')
  limit=Decimal(100) if r['units']=='percent' else Decimal(1)
  if not 0<=estimate<=limit:return decision('INCOMPATIBLE','ESTIMATE_UNIT_RANGE_MISMATCH')
  normalized=estimate/100 if r['units']=='percent' else estimate
 elif r['metric'] in ['cross_entropy','LM_NLL','LM_PPL']:
  expected='perplexity' if r['metric']=='LM_PPL' else ('nats_per_target' if r['metric']=='LM_NLL' else 'nats_per_example')
  if r['direction']!='lower_better' or r['units']!=expected:return decision('INCOMPATIBLE','LOSS_DIRECTION_OR_UNIT_MISMATCH')
  if estimate<0:return decision('INCOMPATIBLE','NEGATIVE_LOSS_OR_PERPLEXITY')
  normalized=estimate
 else:return decision('PENDING_PROTOCOL','METRIC_DEFINITION_REQUIRES_VERSIONED_RULE')
 base.update(estimate=str(normalized),source_estimate=str(r['estimate']),source_units=r['units'],source_precision=r.get('source_precision'),normalized_units='fraction' if r['metric'] in RANKING else r['units'])
 uncertainty=r.get('uncertainty')
 if uncertainty is not None:
  if uncertainty.get('kind')!='confidence_interval' or not all(uncertainty.get(k) is not None for k in ['level','method','resampling_unit','conditioning','low','high']):base.update(missing_uncertainty_reason='PENDING_UNCERTAINTY_REPORTED_DISPERSION_NOT_QUALIFIED_CI',reported_uncertainty=uncertainty)
  else:
   low=Decimal(str(uncertainty['low']));high=Decimal(str(uncertainty['high']))
   if not low.is_finite() or not high.is_finite() or low>high:return decision('INCOMPATIBLE','INVALID_INTERVAL_BOUNDS')
   if r['units']=='percent':low/=100;high/=100
   base.update(ci_low=str(low),ci_high=str(high),missing_uncertainty_reason=None,reported_uncertainty=uncertainty)
 claims=['ELIGIBLE_CHECKPOINT_DESCRIPTION']
 if r['measurement_scope']=='layerwise_probe':claims.append('ELIGIBLE_LAYERWISE')
 ref=references.get(r.get('reference_id'));reference_reason='PENDING_REFERENCE'
 if ref and all(r.get('reference_'+k)==ref[k] for k in ['content_sha256','evaluation_protocol_sha256','metric_definition','units','direction','cohort_id','readout']):claims.append('ELIGIBLE_REFERENCE_RELATIVE');reference_reason=None
 return dict(base,disposition='ELIGIBLE_CHECKPOINT_DESCRIPTION',reason=None,eligible_claims=claims,reference_reason=reference_reason,parent_relative_eligible=False,external_evaluation_independently_reproduced=False)

def check_projection(record,distinct_measurements):
 assert distinct_measurements==1,'A unique external source measurement must be counted once; reuse is not replication'
 if record['measurement_scope']!='layerwise_probe':assert record.get('representation') is None,'Do not relabel global forget scores by layer'

def complete_partition(source_records,normalized_records):
 expected=[r['record_id'] for r in source_records];actual=[r['record_id'] for r in normalized_records]
 assert len(expected)==len(set(expected)) and len(actual)==len(set(actual)) and set(actual)==set(expected),'Missing/duplicate source record after normalization'
