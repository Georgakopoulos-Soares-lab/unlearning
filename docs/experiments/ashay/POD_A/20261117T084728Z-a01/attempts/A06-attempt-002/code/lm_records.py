"""R5 actual causal LM marginal statistics only. All LM pairs belong to A08."""
import argparse,math,datetime,time
from h3_common import *
from scope6 import authorize
def canonical_input(kind,source_sha256,cohort_sha256,ordered_ids_sha256):
 require(kind in ['RAW_COHORT_MANIFEST','EXTRACTION_BUNDLE_RECEIPT'],'Unknown LM provenance kind');require(all(isinstance(v,str) and len(v)==64 for v in [source_sha256,cohort_sha256,ordered_ids_sha256]),'Incomplete typed LM identity')
 if kind=='RAW_COHORT_MANIFEST':require(source_sha256==cohort_sha256,'Historical raw manifest mismatch')
 return {'raw_cohort_sha256':cohort_sha256,'ordered_ids_sha256':ordered_ids_sha256}
def draw_weights(task,split,ids,groups):
 group='H3' if task=='emp_H3' else 'other_five';p=checked_old(H/'probes'/group/task/(split+'_resampling.npz'))
 with np.load(p,allow_pickle=False) as z:
  names,inverse=np.unique(groups,return_inverse=True);require(np.array_equal(z['ids'],ids) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse),'LM saved draw order/group identity mismatch');require(int(z['seed'])==20261103,'Wrong LM saved draw seed');draw=z['group_draws'];require(draw.shape==(2000,len(names)),'Wrong LM saved draw population');weights=np.stack([np.bincount(d,minlength=len(names)) for d in draw])[:,inverse]
 return weights,p
def independently_aggregate(losses,counts,weights=None):
 losses=np.asarray(losses,dtype=np.float64);counts=np.asarray(counts,dtype=np.float64);nll=math.fsum(losses.tolist())/math.fsum(counts.tolist())
 if weights is None:return nll,None
 return nll,np.array([math.fsum((losses*w).tolist())/math.fsum((counts*w).tolist()) for w in weights])
def exponent(values):
 values=np.asarray(values,dtype=np.float64);out=np.full(values.shape,np.nan);ok=values<=math.log(np.finfo(np.float64).max);out[ok]=np.exp(values[ok]);return out,ok
def main(alias,group):
 authorize(alias);require(group in ['H3','other_five'],'Unknown LM task group');start=time.monotonic();selected=[u for u in INPUTS['extraction_units'] if u['candidate']==alias and (u['task']=='emp_H3')==(group=='H3')];units=[]
 for unit in selected:
  root=A/'features'/alias/unit['task']/unit['split'];done=read(root/'COMPLETE.json');require(done['status']=='PASS','Unsealed LM source bundle');out=A/'lm'/alias/unit['task']/unit['split']
  if (out/'COMPLETE.json').exists():
   seal=read(out/'COMPLETE.json');require(seal['input_bundle_sha256']==sha(root/'COMPLETE.json') and seal['source_sha256']==sha(__file__),'Stale LM result seal');verify_refs(out,seal);report=read(out/'RESULTS.json')
  else:
   require(not out.exists(),'Partial LM output preserved; quarantine before a controlled retry');parts={k:[] for k in ['ids','labels','groups','sequence_sha256','lengths','nll_sum','n_tokens']}
   for e in done['chunks']:
    chunk=A/e['path'];receipt=read(chunk/'COMPLETE.json');require(sha(chunk/'COMPLETE.json')==e['receipt_sha256'],'Changed LM chunk seal');p=chunk/'features_and_lm.npz';require(sha(p)==receipt['files'][0]['sha256'],'Changed LM chunk payload')
    with np.load(p,allow_pickle=False) as z:
     for k in parts:parts[k].append(z[k])
   arr={k:np.concatenate(v) for k,v in parts.items()};require(len(arr['ids'])==unit['rows'] and digest(arr['ids'].tolist())==unit['ordered_ids_sha256'],'Wrong LM ordered rows');require(arr['nll_sum'].dtype==np.float32 and np.array_equal(arr['n_tokens'],arr['lengths']-1),'LM float32 sums/causal target count mismatch');loss=arr['nll_sum'].astype(np.float64);count=arr['n_tokens'].astype(np.float64);require(np.isfinite(loss).all() and (count>0).all(),'Invalid LM sufficient statistics');point=float(loss.sum(dtype=np.float64)/count.sum(dtype=np.float64));indpoint,_=independently_aggregate(loss,count);require(abs(point-indpoint)<=1e-12,'Independent LM corpus NLL discrepancy');pointp,pointok=exponent(np.array([point]));ppl=float(pointp[0]) if pointok[0] else None;primary=unit['split']!='train';results=[];distributions={};maxnll=abs(point-indpoint);maxppl=0.;draw_ref=None
   if primary:
    weights,dp=draw_weights(unit['task'],unit['split'],arr['ids'],arr['groups']);nll=(weights@loss)/(weights@count);_,ind=independently_aggregate(loss,count,weights);maxnll=max(maxnll,float(np.max(np.abs(nll-ind))));require(maxnll<=1e-12,'Independent every-draw LM NLL discrepancy');pv,pok=exponent(nll);iv,iok=exponent(ind);require(np.array_equal(pok,iok),'LM overflow validity mismatch');maxppl=float(np.max(np.abs(pv[pok]-iv[pok]))) if pok.any() else 0.;require(maxppl<=1e-12,'Independent every-draw PPL discrepancy');distributions={'causal_nll':nll,'perplexity':pv,'perplexity_valid':pok};draw_ref={'path':str(dp),'bytes':dp.stat().st_size,'sha256':sha(dp)}
    for metric,value,dist,indist,valid in [('causal_nll',point,nll,ind,np.ones(2000,dtype=bool)),('perplexity',ppl,pv,iv,pok)]:
     ci=np.quantile(dist[valid],[.025,.975]) if valid.any() else [None,None];ici=np.quantile(indist[valid],[.025,.975]) if valid.any() else [None,None]
     if valid.any():require(np.max(np.abs(np.asarray(ci)-np.asarray(ici)))<=1e-12,'Independent LM interval discrepancy')
     results.append({'checkpoint_alias':alias,'checkpoint_content_id':INPUTS['checkpoint_identities'][alias]['model_tensor_content_sha256'],'task':unit['task'],'split':'test_exploratory' if unit['split']=='test' else unit['split'],'representation':'N/A','CV_seed':'N/A','policy':'actual_causal_head','metric':metric,'estimate':value,'ci_low':None if ci[0] is None else float(ci[0]),'ci_high':None if ci[1] is None else float(ci[1]),'missing_reason':None if value is not None else 'PPL overflow; finite corpus NLL retained','ci_missing_reason':None if valid.any() else 'All transformed draws overflow','sample_count':len(loss),'group_count':len(np.unique(arr['groups'])),'target_count':int(count.sum()),'bootstrap_attempted':2000,'bootstrap_valid':int(valid.sum()),'bootstrap_invalid':int((~valid).sum()),'status':'VERIFIED','protocol_sha256':CFG['protocol_sha256'],'coverage_plan_sha256':CFG['coverage_plan_sha256'],'draw_sha256':sha(dp),'prediction_hash_kind':'LM_SUFFICIENT_STATISTICS_FILE','input_hash_kind':'EXTRACTION_BUNDLE_RECEIPT','input_sha256':sha(root/'COMPLETE.json')})
   out.mkdir(parents=True);np.savez_compressed(out/'sufficient_statistics.npz',**arr)
   if primary:np.savez_compressed(out/'bootstrap.npz',**distributions)
   report={'status':'VERIFIED','candidate':alias,'task':unit['task'],'split':unit['split'],'primary_reporting_unit':primary,'rows':len(loss),'targets':int(count.sum()),'total_loss_sum_float64':float(loss.sum(dtype=np.float64)),'NLL':point,'PPL':ppl,'PPL_missing_reason':None if ppl is not None else 'Overflow; finite NLL retained','independent_max_abs_NLL':maxnll,'independent_max_abs_PPL_draws':maxppl,'metrics':results,'paired_contrasts':[],'paired_LM_computation_authorized':False,'input_bundle_sha256':sha(root/'COMPLETE.json'),'canonical_input_identity':canonical_input('EXTRACTION_BUNDLE_RECEIPT',sha(root/'COMPLETE.json'),unit['parent_manifest']['sha256'],unit['ordered_ids_sha256']),'source_sha256':sha(__file__),'draw_reference':draw_ref,'precision':'float32 per-example sums; float64 corpus aggregation; independent math.fsum','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(out/'RESULTS.json',report);put(out/'COMPLETE.json',{'status':'VERIFIED','input_bundle_sha256':sha(root/'COMPLETE.json'),'source_sha256':sha(__file__),'files':file_refs(out)})
  units.append({'candidate':alias,'task':unit['task'],'split':unit['split'],'primary_reporting_unit':report['primary_reporting_unit'],'status':'VERIFIED','receipt':str((out/'COMPLETE.json').relative_to(A)),'receipt_sha256':sha(out/'COMPLETE.json'),'rows':report['rows'],'targets':report['targets']});print(json.dumps({'event':'LM_VERIFIED','task':unit['task'],'split':unit['split'],'rows':report['rows'],'primary':report['primary_reporting_unit']}),flush=True)
 index=read(C/'LM_INDEX.json') if (C/'LM_INDEX.json').exists() else {'units':[]};index['units']=[u for u in index['units'] if (u['task']=='emp_H3')!=(group=='H3')]+units;index['paired_LM_rows']=0;index['last_group_wall_seconds']=time.monotonic()-start;put(C/'LM_INDEX.json',index)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',choices=['R5'],required=True);p.add_argument('--group',choices=['H3','other_five'],required=True);args=p.parse_args();main(args.candidate,args.group)
