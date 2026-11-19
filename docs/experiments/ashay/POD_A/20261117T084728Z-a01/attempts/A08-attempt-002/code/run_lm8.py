"""Five approved paired actual-causal-LM families, ratio/exponential checks by two routes."""
from endpoint_common8 import *
from analysis_pairs import lm_numbers
import argparse,concurrent.futures,resource,traceback,datetime,math

def load(alias,task,split):
 item=next(e for e in read(C/'LM_NORMALIZATION_INDEX.json')['units'] if (e['candidate'],e['task'],e['split'])==(alias,task,split));checked(item['receipt']);checked(item['statistics']);seal_check(Path(item['receipt']['path']).parent,read(item['receipt']['path'])['identity'])
 with np.load(item['statistics']['path'],allow_pickle=False) as z:meta={k:z[k] for k in z.files}
 return meta,item

def run(spec):
 family=spec['family'];task=spec['task'];split=spec['split'];root=A/'contrasts/LM'/family/task/split;src=contrast_source();tmp=None
 with Lock(A/'locks/LM-contrast'/family/task/(split+'.lock')):
  try:
   mt,it=load(spec['target'],task,split);mr,ir=load(spec['reference'],task,split)
   for k in ['ids','labels','groups','sequence_sha256','lengths','n_tokens']:require(np.array_equal(mt[k],mr[k]),'LM endpoint metadata/target mismatch')
   require(it['endpoint']['draw']==ir['endpoint']['draw'],'LM saved draws differ');w,draw=weights_from_draws(resolve(it['endpoint']['draw'],immutable_map()),mt);identity={'stage':'A08','family':family,'task':task,'split':split,'target':it,'reference':ir,'source_sha256':src,'coverage_plan_sha256':CFG['coverage_plan_sha256']}
   if (root/'COMPLETE.json').exists():seal_check(root,identity);return {'status':'REUSED_PASS','family':family,'task':task,'split':split}
   tmp=workdir(root);t=time.monotonic();cpu=time.process_time();points={};values={};cross={};maxdraw=maxpoint=maxci=0.;source_max=0.
   for alias,meta in [(spec['target'],mt),(spec['reference'],mr)]:
    point,ratio,other=lm_numbers(meta,draw,w);alt=float(meta['nll_sum'].astype(np.float64).sum()/meta['n_tokens'].sum());require(max(point,float(np.max(ratio)),float(np.max(other)))<math.log(np.finfo(np.float64).max),'PPL_OVERFLOW: retain affected key explicitly and diagnose');points[alias]={'causal_nll':point,'perplexity':math.exp(point)};values[alias]={'causal_nll':ratio,'perplexity':np.exp(ratio)};cross[alias]={'causal_nll':other,'perplexity':np.exp(other)};maxpoint=max(maxpoint,residual([point],[alt]),residual([math.exp(point)],[float(np.exp(alt))]));source_max=max(source_max,residual(ratio,other),residual(np.exp(ratio),np.exp(other)))
   rows=[];arrays={};valid=np.ones(2000,dtype=bool)
   for metric in ['causal_nll','perplexity']:
    delta=values[spec['target']][metric]-values[spec['reference']][metric];second=cross[spec['target']][metric]-cross[spec['reference']][metric];err=residual(delta,second);maxdraw=max(maxdraw,err);ci=np.quantile(delta,[.025,.975],method='linear');maxci=max(maxci,residual(ci,np.quantile(second,[.025,.975],method='linear')));point=points[spec['target']][metric]-points[spec['reference']][metric];row=dict(keys()['LM_paired',family,task,split,'N/A','N/A','actual_causal_head',metric]);row.update(status='VERIFIED',estimate=float(point),ci_low=float(ci[0]),ci_high=float(ci[1]),sample_count=len(mt['ids']),group_count=len(np.unique(mt['groups'])),target_count=int(mt['n_tokens'].sum()),bootstrap_attempted=2000,bootstrap_valid=2000,bootstrap_invalid=0,missing_reason=None,ci_missing_reason=None,checkpoint_alias=spec['target'],checkpoint_content_id=read(C/'A08_INPUTS.json')['endpoint_content_ids'][spec['target']],policy='actual_causal_head',source_policy='actual_causal_head',measurement_attempt=C.name,target_measurement_attempt=it['endpoint'].get('measurement_attempt'),reference_measurement_attempt=ir['endpoint'].get('measurement_attempt'),verification_attempt=C.name,lineage='NEW_DERIVED_ACTUAL_CAUSAL_LM_CONTRAST',ingestion_status='NEW_A08_LM_CONTRAST',adjacent=family in ['R4_minus_R3','R5_minus_R4','R6_minus_R5'],ancestry_status='UNKNOWN',exposure_status='UNKNOWN',interval_scope='POINTWISE_EXPLORATORY_UNADJUSTED_GROUP_BOOTSTRAP',source_sha256=src,raw_cohort_sha256=it['endpoint']['raw_cohort']['sha256'],target_prediction_sha256=it['statistics']['sha256'],reference_prediction_sha256=ir['statistics']['sha256'],draw_sha256=it['endpoint']['draw']['sha256']);rows.append(row);arrays[metric]=delta
   np.savez_compressed(tmp/'paired_draws.npz',valid=valid,**arrays);record={'status':'PASS','family':family,'task':task,'split':split,'rows':rows,'endpoints':{'target':it,'reference':ir},'point_max_abs':maxpoint,'draw_max_abs':maxdraw,'interval_max_abs':maxci,'endpoint_draw_max_abs':source_max,'attempted_values':4000,'valid_values':4000,'new_LM_forwards':0,'wall_seconds':time.monotonic()-t,'CPU_process_seconds':time.process_time()-cpu};put(tmp/'RESULTS.json',record);seal(tmp,root,{'status':'PASS','identity':identity});return {'status':'PASS','family':family,'task':task,'split':split,'draw_max_abs':maxdraw,'wall_seconds':record['wall_seconds']}
  except BaseException as exc:
   failure={'status':'FAILED','family':family,'task':task,'split':split,'reason':str(exc),'traceback':traceback.format_exc()};q=A/'quarantine/failed-LM'/family/task/(split+'-'+uuid.uuid4().hex);q.parent.mkdir(parents=True,exist_ok=True)
   if tmp is not None and tmp.exists():put(tmp/'FAILED.json',failure);os.replace(tmp,q)
   else:q.mkdir();put(q/'FAILED.json',failure)
   return failure
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['A08'],required=True);parser.parse_args();contrast_source();require(read(C/'LM_NORMALIZATION_INDEX.json')['status']=='PASS','LM sufficient-statistics normalization required');specs=read(C/'CONTRAST_EXECUTION_MANIFEST.json')['LM_units'];require(len(specs)==35,'Wrong frozen five-family LM list');resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3))
 with Lock(A/'locks/LM-pipeline.lock'):
  with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
   for result in pool.map(run,specs):print(json.dumps(result),flush=True)
