"""Actual causal-head LM sufficient-statistic aggregation and independent paired checks."""
import argparse,math,datetime
from h3_common import *
def old_statistics(alias,group):
 out=A/'reference-LM'/alias/(group+'.npz');out.parent.mkdir(parents=True,exist_ok=True)
 if out.exists():
  with np.load(out,allow_pickle=False) as z:return {k:z[k] for k in z.files}
 folder=H/'features'/group/('base' if alias=='base' else 'maxent');fields=['ids','task','split','labels','groups','sequence_sha256','nll_sum','n_tokens'];parts={k:[] for k in fields}
 for p in sorted(folder.glob('chunk_*.npz')):
  checked_old(p)
  with np.load(p,allow_pickle=False) as z:
   for k in fields:parts[k].append(z[k])
 result={k:np.concatenate(v) for k,v in parts.items()};np.savez_compressed(out,**result);return result
def draw_weights(task,split,ids,groups):
 group='H3' if task=='emp_H3' else 'other_five';p=checked_old(H/'probes'/group/task/(split+'_resampling.npz'))
 with np.load(p,allow_pickle=False) as z:
  names,inverse=np.unique(groups,return_inverse=True);require(np.array_equal(z['ids'],ids) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse),'LM paired draw row/group mismatch');draw=z['group_draws'];require(draw.shape==(2000,len(names)),'Wrong LM bootstrap draws');weights=np.stack([np.bincount(d,minlength=len(names)) for d in draw])[:,inverse]
 return weights,p
def independently_aggregate(losses,counts,weights=None):
 losses=np.asarray(losses,dtype=np.float64);counts=np.asarray(counts,dtype=np.float64);nll=math.fsum(losses.tolist())/math.fsum(counts.tolist())
 if weights is None:return nll,None
 values=np.array([math.fsum((losses*w).tolist())/math.fsum((counts*w).tolist()) for w in weights]);return nll,values
def main(alias,group):
 selected=[u for u in INPUTS['extraction_units'] if u['candidate']==alias and (u['task']=='emp_H3')==(group=='H3')];old={r:old_statistics(r,group) for r in ['base','R1']};units=[]
 for unit in selected:
  root=A/'features'/alias/unit['task']/unit['split'];done=read(root/'COMPLETE.json');require(done['status']=='PASS','LM extraction incomplete');parts={k:[] for k in ['ids','labels','groups','sequence_sha256','lengths','nll_sum','n_tokens']}
  for e in done['chunks']:
   chunk=A/e['path'];receipt=read(chunk/'COMPLETE.json');require(sha(chunk/'COMPLETE.json')==e['receipt_sha256'],'LM input receipt changed')
   p=chunk/'features_and_lm.npz';require(sha(p)==receipt['files'][0]['sha256'],'LM input payload changed')
   with np.load(p,allow_pickle=False) as z:
    for k in parts:parts[k].append(z[k])
  arr={k:np.concatenate(v) for k,v in parts.items()};require(len(arr['ids'])==unit['rows'] and digest(arr['ids'].tolist())==unit['ordered_ids_sha256'],'LM row identity mismatch');require(arr['nll_sum'].dtype==np.float32 and np.array_equal(arr['n_tokens'],arr['lengths']-1),'LM dtype/shift/count mismatch');loss=arr['nll_sum'].astype(np.float64);count=arr['n_tokens'].astype(np.float64);require(np.isfinite(loss).all() and np.all(count>0),'Invalid LM sufficient statistics');point=float(loss.sum(dtype=np.float64)/count.sum(dtype=np.float64));ipoint,_=independently_aggregate(loss,count);require(abs(point-ipoint)<=1e-12,'LM independent corpus NLL discrepancy');ppl=float(np.exp(point));primary=unit['split']!='train';results=[];contrasts=[];distributions={};maxres=abs(point-ipoint)
  if primary:
   weights,dp=draw_weights(unit['task'],unit['split'],arr['ids'],arr['groups']);nll=(weights@loss)/(weights@count);_,ind=independently_aggregate(loss,count,weights);maxres=max(maxres,float(np.max(np.abs(nll-ind))));require(maxres<=1e-12,'LM independent every-draw NLL discrepancy');dist={'causal_nll':nll,'perplexity':np.exp(nll)};distributions.update(dist)
   for metric,pvalue in [('causal_nll',point),('perplexity',ppl)]:
    values=dist[metric];indvalues=ind if metric=='causal_nll' else np.exp(ind);require(np.max(np.abs(values-indvalues))<=1e-12,'LM transformed bootstrap discrepancy');ci=np.quantile(values,[.025,.975]);ici=np.quantile(indvalues,[.025,.975]);require(np.max(np.abs(ci-ici))<=1e-12,'LM interval discrepancy');results.append({'checkpoint_alias':alias,'checkpoint_content_id':INPUTS['checkpoint_identities'][alias]['model_tensor_content_sha256'],'lineage':'NEW','task':unit['task'],'split':'test_exploratory' if unit['split']=='test' else unit['split'],'representation':'N/A','CV_seed':'N/A','policy':'actual_causal_head','metric':metric,'estimate':pvalue,'sample_count':len(loss),'group_count':len(np.unique(arr['groups'])),'target_count':int(count.sum()),'ci_low':float(ci[0]),'ci_high':float(ci[1]),'bootstrap_attempted':2000,'bootstrap_valid':2000,'bootstrap_invalid':0,'status':'VERIFIED','missing_reason':None,'protocol_sha256':CFG['protocol_sha256'],'input_sha256':sha(root/'COMPLETE.json'),'prediction_sha256':None,'receipt':str(Path('lm')/alias/unit['task']/unit['split']/'COMPLETE.json')})
   for refname,ref in old.items():
    mask=(ref['task']==unit['task'])&(ref['split']==unit['split']);rr={k:ref[k][mask] for k in ref if k not in ['task','split']}
    for k in ['ids','labels','groups','sequence_sha256','n_tokens']:require(np.array_equal(rr[k],arr[k]),'LM historical exact pairing differs '+k)
    rl=rr['nll_sum'].astype(np.float64);rc=rr['n_tokens'].astype(np.float64);refnll=float(rl.sum()/rc.sum());refdist=(weights@rl)/(weights@rc);ir,ib=independently_aggregate(rl,rc,weights);require(abs(ir-refnll)<=1e-12 and np.max(np.abs(ib-refdist))<=1e-12,'LM independent reference aggregation discrepancy')
    for metric,delta,indelta,pdelta in [('causal_nll',nll-refdist,ind-ib,point-refnll),('perplexity',np.exp(nll)-np.exp(refdist),np.exp(ind)-np.exp(ib),ppl-float(np.exp(refnll)))]:
     require(np.max(np.abs(delta-indelta))<=1e-12,'LM paired every-draw discrepancy');ci=np.quantile(delta,[.025,.975]);ici=np.quantile(indelta,[.025,.975]);require(np.max(np.abs(ci-ici))<=1e-12,'LM paired interval discrepancy');distributions[refname+'__'+metric]=delta;contrasts.append({'candidate':alias,'reference':refname,'task':unit['task'],'split':unit['split'],'metric':metric,'difference':pdelta,'ci_low':float(ci[0]),'ci_high':float(ci[1]),'attempted':2000,'valid':2000,'invalid':0,'direction':'target-reference','orientation':'lower','status':'VERIFIED','protocol_sha256':CFG['protocol_sha256'],'draw_sha256':sha(dp)})
  out=A/'lm'/alias/unit['task']/unit['split'];out.mkdir(parents=True,exist_ok=True);require(not (out/'COMPLETE.json').exists(),'LM unit already sealed; use verified index rather than overwrite');np.savez_compressed(out/'sufficient_statistics.npz',**arr)
  if primary:np.savez_compressed(out/'bootstrap.npz',**distributions)
  report={'status':'VERIFIED','candidate':alias,'task':unit['task'],'split':unit['split'],'primary_reporting_unit':primary,'rows':len(loss),'targets':int(count.sum()),'NLL':point,'PPL':ppl,'independent_max_abs_NLL':maxres,'metrics':results,'paired_contrasts':contrasts,'input_bundle_sha256':sha(root/'COMPLETE.json'),'source_sha256':sha(__file__),'precision':'float32 per-example sums; float64 corpus aggregation; independent math.fsum','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};put(out/'RESULTS.json',report);put(out/'COMPLETE.json',{'status':'VERIFIED','input_bundle_sha256':sha(root/'COMPLETE.json'),'files':file_refs(out)});units.append({'candidate':alias,'task':unit['task'],'split':unit['split'],'primary_reporting_unit':primary,'status':'VERIFIED','receipt':str((out/'COMPLETE.json').relative_to(A)),'receipt_sha256':sha(out/'COMPLETE.json'),'rows':len(loss),'targets':int(count.sum())});print(json.dumps({'event':'LM_VERIFIED','candidate':alias,'task':unit['task'],'split':unit['split'],'rows':len(loss),'reporting':primary}),flush=True)
 index=read(C/'LM_INDEX.json') if (C/'LM_INDEX.json').exists() else {'units':[]};index['units']=[u for u in index['units'] if not (u['candidate']==alias and (u['task']=='emp_H3')==(group=='H3'))]+units;put(C/'LM_INDEX.json',index)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',choices=['R4','R6'],required=True);p.add_argument('--group',choices=['H3','other_five'],required=True);a=p.parse_args();main(a.candidate,a.group)
