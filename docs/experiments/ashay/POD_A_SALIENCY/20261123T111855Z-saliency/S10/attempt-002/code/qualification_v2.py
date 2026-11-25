"""Aggregate metadata validator v2. Invalid uncertainty does not destroy a valid point."""
from decimal import Decimal,InvalidOperation
import math
SEMANTICS=('task_definition','cohort_id','split','evaluation_protocol_sha256','readout','metric_definition','units','direction','aggregation_rule')
def number(x):
 if isinstance(x,bool) or x is None:return None
 try:v=Decimal(str(x))
 except (InvalidOperation,ValueError,TypeError):return None
 return v if v.is_finite() else None
def meaningful(x):return isinstance(x,str) and bool(x.strip()) and x.strip().lower() not in ('unknown','none','null','n/a','unspecified')
def interval(u):
 out={'status':'MISSING','low':None,'high':None,'level':None,'reason':'NOT_SUPPLIED'}
 if u is None:return out
 out.update(status='INVALID_UNCERTAINTY',reason='MALFORMED_INTERVAL')
 if not isinstance(u,dict):return out
 if u.get('kind')!='confidence_interval':out['reason']='NOT_A_CONFIDENCE_INTERVAL';return out
 level=number(u.get('level'));lo=number(u.get('low'));hi=number(u.get('high'))
 if level is None or not 0<level<1:out['reason']='CONFIDENCE_LEVEL_OUTSIDE_OPEN_UNIT_INTERVAL';return out
 if not all(meaningful(u.get(k)) for k in ('method','resampling_unit','conditioning')):out['reason']='UNCERTAINTY_PROVENANCE_MISSING';return out
 if lo is None or hi is None or lo>hi:out['reason']='INVALID_INTERVAL_BOUNDS';return out
 return {'status':'QUALIFIED_REPORTED_CI','low':str(lo),'high':str(hi),'level':str(level),'reason':None,'independently_reproduced':False}
def assess(r,reference=None):
 point=number(r.get('estimate'));ci=interval(r.get('uncertainty'))
 result={'record_id':r.get('record_id',r.get('observation_id')),'point_status':'VALID_POINT' if point is not None else 'INVALID_RECORD','estimate':None if point is None else str(point),'uncertainty':ci,'scientific_status':'SOURCE_VERIFIED_UNQUALIFIED','checkpoint_status':'UNBOUND','reference_comparison':False,'reference_reason':'REFERENCE_NOT_SUPPLIED','allowed_use':'SOURCE_LABEL_DESCRIPTION_ONLY','missing_fields':[]}
 if point is None:result.update(scientific_status='INVALID_RECORD',allowed_use='PRESERVED_INVALID_RECORD');return result
 if not r.get('exact_checkpoint_content_sha256'):
  result['scientific_status']='AMBIGUOUS_CHECKPOINT_BINDING' if r.get('candidate_associations') else 'SOURCE_VERIFIED_UNQUALIFIED'
 else:result['checkpoint_status']='EXACT_CONTENT_BOUND'
 required=SEMANTICS+('implementation_version','sample_denominator')
 missing=[k for k in required if (not meaningful(r.get(k)) if k!='sample_denominator' else type(r.get(k)) is not int or r[k]<=0)]
 result['missing_fields']=missing
 if missing:return result
 if r.get('protocol_compatible') is False:result['scientific_status']='INCOMPATIBLE_PROTOCOL';return result
 result['scientific_status']='QUALIFIED_DESCRIPTIVE_AGGREGATE';result['allowed_use']='DECLARED_PROTOCOL_POINT_DESCRIPTION'
 if reference is not None:
  mismatch=[k for k in SEMANTICS if r.get(k)!=reference.get(k)]
  advertised=any(r.get('reference_'+k)!=reference.get(k) for k in ('content_sha256',)+SEMANTICS)
  if mismatch or advertised or not reference.get('content_sha256'):result['reference_reason']='ACTUAL_TARGET_REFERENCE_SEMANTICS_OR_IDENTITY_MISMATCH';result['reference_mismatches']=mismatch;return result
  if result['checkpoint_status']!='EXACT_CONTENT_BOUND':result['reference_reason']='EXACT_TARGET_IDENTITY_MISSING';return result
  result.update(scientific_status='QUALIFIED_MATCHED_COMPARISON',reference_comparison=True,reference_reason=None,allowed_use='MATCHED_DECLARED_POINT_COMPARISON_NO_INVENTED_JOINT_UNCERTAINTY')
 return result

def ingest_scalar(row,source):
 # Real path shared by extraction assessment and adversarial ingestion tests. Source hash is not a model hash.
 r={'record_id':row['observation_id'],'estimate':row['value'],'exact_checkpoint_content_sha256':None,'candidate_associations':source['candidate_alias_associations_only'],'uncertainty':None,'task_definition':None,'cohort_id':None,'split':None,'evaluation_protocol_sha256':None,'readout':None,'metric_definition':None,'units':None,'direction':None,'aggregation_rule':None,'implementation_version':None,'sample_denominator':None,'source_id':source['id'],'source_sha256':source['sha256']}
 if row['source_sha256']!=source['sha256']:return {'record_id':r['record_id'],'scientific_status':'INVALID_RECORD','point_status':'INVALID_SOURCE_BINDING','allowed_use':'PRESERVED_INVALID_RECORD','checkpoint_status':'UNBOUND','reference_comparison':False,'uncertainty':interval(None),'missing_fields':['SOURCE_BYTES_MISMATCH']}
 return assess(r)
