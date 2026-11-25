"""Independent checker: Fraction arithmetic and explicit gate reconstruction; no producer imports."""
from fractions import Fraction
def rational(x):
 if x is None or isinstance(x,bool):return None
 try:return Fraction(str(x))
 except (ValueError,TypeError,ZeroDivisionError,OverflowError):return None
def check_interval(u,actual):
 valid=False
 if isinstance(u,dict):
  level=rational(u.get('level'));low=rational(u.get('low'));high=rational(u.get('high'))
  labels=all(isinstance(u.get(k),str) and u[k].strip() and u[k].strip().lower() not in ['unknown','none','null','n/a','unspecified'] for k in ['conditioning','method','resampling_unit'])
  valid=u.get('kind')=='confidence_interval' and level is not None and 0<level<1 and low is not None and high is not None and low<=high and labels
 assert (actual['status']=='QUALIFIED_REPORTED_CI')==valid
 if valid:assert rational(actual['low'])==low and rational(actual['high'])==high and rational(actual['level'])==level
 else:assert actual['low'] is None and actual['high'] is None
def check_assessment(r,reference,actual):
 check_interval(r.get('uncertainty'),actual['uncertainty']);point=rational(r.get('estimate'))
 assert (actual['point_status']=='VALID_POINT')==(point is not None)
 if point is None:assert actual['scientific_status']=='INVALID_RECORD' and not actual['reference_comparison'];return
 assert rational(actual['estimate'])==point
 targetfields=['task_definition','split','cohort_id','evaluation_protocol_sha256','metric_definition','units','direction','readout','aggregation_rule']
 mandatory=targetfields+['implementation_version'];complete=all(isinstance(r.get(k),str) and r[k].strip() and r[k].strip().lower() not in ['unknown','none','null','n/a','unspecified'] for k in mandatory) and type(r.get('sample_denominator')) is int and r['sample_denominator']>0
 expected=bool(complete and r.get('protocol_compatible') is not False and reference and reference.get('content_sha256') and r.get('exact_checkpoint_content_sha256') and all(r.get(k)==reference.get(k) and r.get('reference_'+k)==reference.get(k) for k in targetfields) and r.get('reference_content_sha256')==reference.get('content_sha256'))
 assert actual['reference_comparison']==expected
 if not complete:assert actual['scientific_status'] in ['SOURCE_VERIFIED_UNQUALIFIED','AMBIGUOUS_CHECKPOINT_BINDING']
 elif r.get('protocol_compatible') is False:assert actual['scientific_status']=='INCOMPATIBLE_PROTOCOL'
 elif expected:assert actual['scientific_status']=='QUALIFIED_MATCHED_COMPARISON'
 else:assert actual['scientific_status']=='QUALIFIED_DESCRIPTIVE_AGGREGATE'
def check_ingested(row,source,actual):
 assert row['source_id']==source['id']
 if row['source_sha256']!=source['sha256']:assert actual['point_status']=='INVALID_SOURCE_BINDING' and actual['scientific_status']=='INVALID_RECORD';return
 point=rational(row['value']);assert (actual['point_status']=='VALID_POINT')==(point is not None)
 assert actual['checkpoint_status']=='UNBOUND' and not actual['reference_comparison']
 assert actual['scientific_status']==('AMBIGUOUS_CHECKPOINT_BINDING' if source['candidate_alias_associations_only'] else 'SOURCE_VERIFIED_UNQUALIFIED') if point is not None else actual['scientific_status']=='INVALID_RECORD'
 assert actual['uncertainty']['status']=='MISSING' and actual['allowed_use'] in ['SOURCE_LABEL_DESCRIPTION_ONLY','PRESERVED_INVALID_RECORD']
