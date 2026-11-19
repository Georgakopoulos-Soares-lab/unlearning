"""Portable scientific identity and source-join contracts; outcomes never enter identity."""
import hashlib,json

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def context(row,kind,ids,protocol):
 target=row['checkpoint_alias'];reference=row.get('reference','');assert target in ids
 return {'kind':kind,'target':target,'target_effective_content_id':ids[target],'reference':reference,'reference_effective_content_id':ids.get(reference,row.get('reference_content_id') or row.get('reference_endpoint_id') or reference),'task':row['task'],'split':row['split'],'representation':row.get('representation','N/A') if kind.startswith('classifier') else 'N/A','CV_seed':str(row.get('CV_seed','N/A')) if kind.startswith('classifier') else 'N/A','policy':row['policy'],'source_policy':row.get('source_policy') or row['policy'],'reference_policy':row.get('reference_policy') or (row['policy'] if reference else ''),'metric':row['metric'],'effective_protocol_sha256':protocol}
def accept_source(row,original,kind,ids,protocol):
 assert row['A09_source_row_sha256']==digest(original),'Original source row changed';key=digest(context(original,kind,ids,protocol));assert key==row['A09_scientific_key_sha256'],'Scientific key changed';assert row['A09_row_id']==(original.get('logical_id') or 'legacy-v1:'+key),'Row identity changed'
 for field in ['estimate','ci_low','ci_high','status','task','split','representation','CV_seed','policy','source_policy','reference','metric']:
  if field in original:assert row.get(field,'')==original[field],'Original cell changed: '+field
 return key

def unique_add(mapping,key,value):
 assert key not in mapping,'Duplicate scientific or row key';mapping[key]=value
