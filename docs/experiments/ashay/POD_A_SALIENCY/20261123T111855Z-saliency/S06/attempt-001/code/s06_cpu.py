"""S06 saved-statistics LM producer. No model, classifier, or contrast execution."""
from s06_contract import *
import argparse,time,resource
import numpy as np
from qualification_contract import corpus_likelihood

def aggregate(sums,counts,weights=None):
 nll,ppl,reason=corpus_likelihood(sums,counts);vectors={}
 if weights is not None:
  vectors['LM_NLL']=(weights@sums.astype(np.float64))/(weights@counts.astype(np.float64))
  with np.errstate(over='ignore',invalid='ignore'):vectors['LM_PPL']=np.exp(vectors['LM_NLL'])
 return {'LM_NLL':nll,'LM_PPL':ppl},vectors,reason

def interval_record(values,attempted):
 valid=np.isfinite(values);ci=np.quantile(values[valid],[.025,.975],method='linear') if valid.any() else None
 return valid,ci,('AVAILABLE' if ci is not None else ('UNAVAILABLE_ZERO_VALID_DRAWS' if attempted else 'NOT_REQUIRED_TRAIN_DIAGNOSTIC'))

def main(c,alias):
 cfg,v,source=readiness(c,alias,'LM_producer');lookup=planned(c);case=Path(cfg['artifacts_root'])/'candidates'/alias;start=time.monotonic();records=[]
 with exclusive(case/'LM_WRITER.lock'):
  for task in TASKS:
   for split in SPLITS:
    ids,sums,counts,seals,idx=bundle(case,cfg,alias,task,split);rows=metadata(cfg,task,split);pid=spec_id(lookup,'LM',c=alias,t=task,split=split,r=None,s=None,p='LM');ident={'phase':'S06','planned_spec_id':pid,'candidate_id':v['candidate_id'],'candidate_content_sha256':v['model_tensor_content_sha256'],'alias':alias,'task':task,'split':split,'representation':None,'cv_seed':None,'null_axis_reason':'Actual causal output head; no pooled representation or probe partition','policy':'LM','source_identity_sha256':source,'runtime_lock_sha256':cfg['cpu_runtime_lock_sha256'],'extraction_runtime_lock_sha256':cfg['runtime_lock_sha256'],'feature_seals_sha256':seals,'ordered_cohort_sha256':cfg['cohorts'][task][split]['ordered_metadata_sha256'],'protocol_semantic_sha256':cfg['protocol_semantic_sha256']};actual=digest(ident);root=case/'LM'/task/split
    if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['statistics.npz','draws.npz','METRICS.json']);records.append(load(root/'METRICS.json'));continue
    need(not root.exists(),'Preserve incomplete LM unit; explicit attempt mapping required');root.mkdir(parents=True);weights,drawsha=draw_weights(cfg,task) if split=='dev' else (None,None);points,vectors,overflow=aggregate(sums,counts,weights);metricrows=[];attempted=2000 if split=='dev' else 0
    for name,value in points.items():
     d=vectors.get(name,np.array([],dtype=np.float64));valid,ci,disposition=interval_record(d,attempted);reason=overflow if value is None else ('No finite bootstrap draws; valid point preserved' if attempted and not valid.any() else None);metric={'unit_id':actual,'reference_unit_id':None,'metric':name,'direction':'lower_better','estimate':value,'ci_low':None if ci is None else float(ci[0]),'ci_high':None if ci is None else float(ci[1]),'missing_reason':reason,'sample_count':len(ids),'group_count':cfg['cohorts'][task][split]['groups'],'valid_targets':int(counts.sum()),'bootstrap_attempted':attempted,'bootstrap_valid':int(valid.sum()),'bootstrap_invalid':attempted-int(valid.sum()),'draw_sha256':drawsha,'common_mask_sha256':None,'uncertainty':'pointwise_exploratory_conditional' if attempted else 'none','source_sha256':source};metricrows.append({'planned_spec_id':spec_id(lookup,'LM_metric',c=alias,t=task,split=split,r=None,s=None,p='LM',m=name),'source_row_id':digest({'actual_LM_unit_id':actual,'metric':name}),'canonical_metric':metric,'interval_disposition':disposition,'valid_mask_sha256':hashlib.sha256(valid.tobytes()).hexdigest()});vectors[name]=d;vectors[name+'_valid']=valid
    np.savez(root/'statistics.npz',ids=np.array(ids),labels=np.array([r['label'] for r in rows]),groups=np.array([r['group'] for r in rows]),classes=np.array(cfg['cohorts'][task][split]['class_order']),nll_sum=sums,n_tokens=counts)
    np.savez(root/'draws.npz',**vectors);rec={'schema_version':'s06-LM-unit-v1','status':'COMPLETE_UNVERIFIED','identity':ident,'actual_LM_unit_id':actual,'metrics':metricrows,'TRAIN_diagnostic_no_draw_generation':split=='train','per_example_sum_dtype':'float32','corpus_aggregation_dtype':'float64','interval_label':'95% pointwise exploratory conditional; not multiplicity adjusted; no biological/intervention independence claim' if attempted else None};put(root/'METRICS.json',rec);write_seal(root,ident,['statistics.npz','draws.npz','METRICS.json'],{'LM_units':1,'LM_metric_records':2,'rows':len(ids),'valid_targets':int(counts.sum())});records.append(rec);print('S06_LM_UNIT_SEALED',alias,task,split,flush=True)
 rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;need(rss<=8*1024**3,'LM CPU worker 8GiB ceiling');put(case/'LM_RESOURCE.json',{'status':'PASS','units':len(records),'wall_seconds':time.monotonic()-start,'peak_RSS_bytes':rss,'fits':0,'head_applications':0,'GPU_forwards':0});return records
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);p.add_argument('--alias',required=True);x=p.parse_args();main(Path(x.control),x.alias)
