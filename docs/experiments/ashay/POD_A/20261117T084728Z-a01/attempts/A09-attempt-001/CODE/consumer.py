"""Portable finite A09 saved-analysis recovery panel. No fits, forwards or RNG."""
from pathlib import Path
import argparse,csv,hashlib,json,math,resource,time,sys,importlib.metadata
import numpy as np
import joblib
from independent_math import reconstruct,metrics
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def residual(a,b,valid=None):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape
 if valid is not None:a=a[valid];b=b[valid]
 assert np.isfinite(a).all() and np.isfinite(b).all();return float(np.max(np.abs(a-b))) if a.size else 0.
def ci(v,valid=None):
 v=np.sort(v if valid is None else v[valid]);assert len(v)>0;out=[]
 for q in [.025,.975]:
  rank=(len(v)-1)*q;lo=math.floor(rank);hi=math.ceil(rank);out.append(float(v[lo]+(rank-lo)*(v[hi]-v[lo])))
 return out
def main(root,context_path=None):
 t=time.monotonic();cpu=time.process_time();resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));versions={k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-learn','joblib','threadpoolctl']};assert sys.version_info[:3]==(3,12,3) and versions=={'numpy':'2.5.4','scipy':'1.18.1','scikit-learn':'1.7.2','joblib':'1.5.2','threadpoolctl':'3.8.0'}
 root=root.resolve();manifest=read(root/'MEMBER_MANIFEST.json');assert len(manifest['files'])==len({e['path'] for e in manifest['files']});payload_bytes=0
 for e in manifest['files']:
  p=root/e['path'];assert p.resolve().is_relative_to(root) and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];payload_bytes+=e['bytes']
 context=read(context_path or root/'DEPENDENCY_CONTEXT.json');roots={k:Path(v).resolve() for k,v in context['roots'].items()};indexes={}
 for node,relative in context['indexes'].items():
  p=root/relative;assert sha(p)==context['index_sha256'][node];entries=read(p)['files'];assert len(entries)==len({e['path'] for e in entries});indexes[node]={e['path']:e for e in entries}
 used=set()
 def trusted(node,relative):
  assert '/meeting-artifacts/' not in str(roots[node]),'Original producer root forbidden';p=roots[node]/relative;assert p.resolve().is_relative_to(roots[node]) and p.is_file() and not p.is_symlink();e=indexes[node][relative];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];used.add((node,relative));return p
 def load(node,relative):
  with np.load(trusted(node,relative),allow_pickle=False) as z:return {k:z[k] for k in z.files}
 def features(alias,task,key):
  node='A06/'+alias+'_other_five';bundle=read(trusted(node,'artifacts/features/'+alias+'/'+task+'/dev/COMPLETE.json'));pieces=[];meta={k:[] for k in ['ids','labels','groups','sequence_sha256']}
  for chunk in bundle['chunks']:
   prefix='artifacts/'+chunk['path'];p=trusted(node,prefix+'/COMPLETE.json');assert sha(p)==chunk['receipt_sha256'];data=load(node,prefix+'/features_and_lm.npz');pieces.append(data[key])
   for k in meta:meta[k].append(data[k])
  x=np.concatenate(pieces);m={k:np.concatenate(v) for k,v in meta.items()};assert x.dtype==np.float32 and x.shape==(512,1920) and np.isfinite(x).all();return x,m
 def audit(alias,task,key):
  node='A08/'+alias;prefix='artifacts/audits/'+alias+'/'+task+'/'+key+'/seed42';record=read(trusted(node,prefix+'/NUMERICAL_AUDIT.json'));pred=load(node,prefix+'/independent_predictions.npz');return record,pred,prefix
 def same_metadata(a,b):
  for k in ['ids','labels','groups','sequence_sha256']:assert np.array_equal(a[k],b[k]),'Ordered pairing mismatch: '+k
 def draw_population(meta):
  draw=load('historical/base_R1','probes/other_five/gue_tf_0/dev_resampling.npz');names,inverse=np.unique(meta['groups'],return_inverse=True);assert np.array_equal(draw['ids'],meta['ids']) and np.array_equal(draw['group_names'],names) and np.array_equal(draw['row_groups'],inverse) and int(draw['seed'])==20261103;d=draw['group_draws'];assert d.dtype==np.int32 and d.shape==(2000,len(names));assert d.min()>=0 and d.max()<len(names);counts=np.zeros((2000,len(names)),dtype=np.int64)
  for i,g in enumerate(d):counts[i]=np.bincount(g,minlength=len(names))
  assert np.all(counts.sum(1)==len(names));return d,counts[:,inverse],counts,inverse
 results=[];refits=[];feature_cache={};classes_for=lambda task:np.array([0,1,2] if task=='gue_splice_reconstructed' else [0,1])
 for alias in ['R4','R6']:
  for task in ['gue_tf_0','gue_splice_reconstructed']:
   key='final_norm';x,meta=features(alias,task,key);feature_cache[alias,task]=(x,meta);record,z,prefix=audit(alias,task,key);same_metadata(meta,z);classes=classes_for(task);assert np.array_equal(z['classes'],classes)
   node='A07/'+alias+'_'+task;prod='artifacts/probes/'+alias+'/'+task+'/'+key+'/seed42';head=joblib.load(trusted(node,prod+'/head.joblib'));base=joblib.load(trusted(node,'dependencies/base-heads/'+key+'/base.joblib'))
   for policy,model in [('independent_refit',head),('fixed_original_base',base)]:
    p=reconstruct(model,x);err=residual(p,z[policy]);assert err<=1e-10 and np.allclose(p.sum(1),1,atol=1e-12,rtol=0);values,valid=metrics(meta['labels'],p,classes,np.ones((1,len(p)),dtype=np.int64));assert valid.all();dm=max(abs(float(v[0])-record['independent_point_values'][policy][m]) for m,v in values.items());assert dm<=1e-12;results.append({'candidate':alias,'task':task,'split':'dev','representation':'decoder.final_norm','seed':42,'policy':policy,'rows':len(p),'groups':len(np.unique(meta['groups'])),'class_count':len(classes),'probability_max_abs':err,'metric_max_abs':dm,'status':'PASS'})
  task='gue_tf_0';x,meta=feature_cache[alias,task];node='A08/'+alias;prefix='artifacts/refits/'+alias+'/'+task+'/final_norm/seed42';model=joblib.load(trusted(node,prefix+'/audit_head.joblib'));z=load(node,prefix+'/audit_dev_probabilities.npz');p=reconstruct(model,x);err=residual(p,z['probabilities']);assert err<=1e-10;refits.append({'candidate':alias,'restored_artifact':prefix+'/audit_head.joblib','probability_max_abs':err,'fitting_performed':False,'status':'PASS'})
 # Recompute the one prescribed classifier contrast using exact saved group draws.
 records={};pred={};endpoint_dists={};point={};valids={};maxpoint=maxdraw=maxinterval=0.;meta=None
 for alias in ['R4','R6']:
  r,z,prefix=audit(alias,'gue_tf_0','decoder_layer_16');records[alias]=r;pred[alias]=z
  if meta is None:meta=z;draw,weights,groupcounts,inverse=draw_population(meta)
  else:same_metadata(meta,z)
  saved=load('A08/'+alias,prefix+'/bootstrap_independent.npz')
  for policy in ['independent_refit','fixed_original_base']:
   vals,mask=metrics(z['labels'],z[policy],np.array([0,1]),weights);pt,good=metrics(z['labels'],z[policy],np.array([0,1]),np.ones((1,len(z['ids'])),dtype=np.int64));assert good.all();endpoint_dists[alias,policy]=vals;point[alias,policy]={m:float(v[0]) for m,v in pt.items()};valids[alias,policy]=mask
   for m,v in vals.items():err=residual(v,saved[policy+'__'+m],mask);maxdraw=max(maxdraw,err);assert err<=1e-12
 node='A08/analysis';prefix='artifacts/analysis/R6_minus_R4/gue_tf_0/dev/decoder_layer_16/seed42';new=read(trusted(node,prefix+'/ANALYSIS.json'));saved=load(node,prefix+'/paired_draws.npz');checked=0
 for r in new['rows']:
  policy,m=r['policy'],r['metric'];mask=valids['R6',policy];assert np.array_equal(mask,valids['R4',policy]) and np.array_equal(mask,saved['valid']);delta=endpoint_dists['R6',policy][m]-endpoint_dists['R4',policy][m];err=residual(delta,saved[policy+'__'+m],mask);pe=abs(point['R6',policy][m]-point['R4',policy][m]-r['estimate']);ie=residual(ci(delta,mask),[r['ci_low'],r['ci_high']]);maxdraw=max(maxdraw,err);maxpoint=max(maxpoint,pe);maxinterval=max(maxinterval,ie);assert max(err,pe,ie)<=1e-12;checked+=2000
 assert checked==20000
 # Actual causal loss/count ratios, both aggregation routes, same saved draws.
 lm={};maxlm=0.;lmvalues={};lmvalid=np.ones(2000,dtype=bool)
 for alias in ['R4','R6']:
  z=load('A06/'+alias+'_other_five','artifacts/lm/'+alias+'/gue_tf_0/dev/sufficient_statistics.npz');same_metadata(meta,z);assert z['nll_sum'].dtype==np.float32 and z['n_tokens'].dtype==np.int64 and np.array_equal(z['n_tokens'],z['lengths']-1) and np.all(z['n_tokens']>0)
  nll=math.fsum(float(v) for v in z['nll_sum'])/sum(int(v) for v in z['n_tokens']);gloss=[math.fsum(float(v) for v in z['nll_sum'][inverse==g]) for g in range(len(groupcounts[0]))];gtokens=[sum(int(v) for v in z['n_tokens'][inverse==g]) for g in range(len(groupcounts[0]))];ratio=np.array([math.fsum(gloss[int(g)] for g in d)/sum(gtokens[int(g)] for g in d) for d in draw]);other=(weights@z['nll_sum'].astype(np.float64))/(weights@z['n_tokens']);maxlm=max(maxlm,residual(ratio,other),residual(np.exp(ratio),np.exp(other)));assert maxlm<=1e-12;lm[alias]={'causal_nll':nll,'perplexity':math.exp(nll)};lmvalues[alias]={'causal_nll':ratio,'perplexity':np.exp(ratio)}
 prefix='artifacts/analysis/LM_R6_minus_R4/gue_tf_0/dev';lmrecord=read(trusted(node,prefix+'/ANALYSIS.json'));lmsaved=load(node,prefix+'/paired_draws.npz');assert np.array_equal(lmsaved['valid'],lmvalid);lmpoint=lmdraw=lmci=0.
 for r in lmrecord['rows']:
  m=r['metric'];delta=lmvalues['R6'][m]-lmvalues['R4'][m];lmpoint=max(lmpoint,abs(lm['R6'][m]-lm['R4'][m]-r['estimate']));lmdraw=max(lmdraw,residual(delta,lmsaved[m]));lmci=max(lmci,residual(ci(delta),[r['ci_low'],r['ci_high']]));assert max(lmpoint,lmdraw,lmci)<=1e-12
 # Every inherited public table/figure is read through the restored metadata root.
 metadata='A08/final_metadata';index=read(root/'public/TABLE_INDEX.json');tableproof=[]
 for item in index['tables']:
  location=item['file'];p=trusted(metadata,'public-final/'+location.removeprefix('../A08-attempt-001/')) if location.startswith('../A08-attempt-001/') else root/'public'/location;assert sha(p)==item['sha256'];rr=list(csv.DictReader(p.open()));assert len(rr)==item['rows'];tableproof.append({'file':location,'rows':len(rr),'sha256':sha(p)})
 fig=read(trusted(metadata,'public-final/FIGURE_VALIDATION.json'));figcount=0
 for f in fig['figures']:
  for e in f['files']:p=trusted(metadata,'public-final/'+e['path']);assert sha(p)==e['sha256'];figcount+=1
 assert figcount==62;pp=trusted(metadata,'public-final/PLOT_DATA/plotted_values.csv');assert sha(pp)==fig['plotted_values_csv_sha256']
 result={'schema':'pod-a-a09-fresh-consumer-panel-v1','status':'PASS','root':str(root),'payload_member_files_checked':len(manifest['files']),'payload_bytes_checked':payload_bytes,'deterministic_panel_source':'Frozen A09_EXECUTION_MANIFEST before recovery outcomes','saved_prediction_metric_paths':results,'path_count':len(results),'restored_A08_refit_artifacts':refits,'new_refitting':0,'new_model_or_LM_forwards':0,'new_bootstrap_draws':0,'probability_max_abs':max(r['probability_max_abs'] for r in results+refits),'metric_max_abs':max(r['metric_max_abs'] for r in results),'classifier_contrast':{'unit':'gue_tf_0/dev/layer16/seed42/bothpolicies/5metrics/2000saved_draws','attempted_delta_values':checked,'point_max_abs':maxpoint,'every_draw_max_abs':maxdraw,'interval_max_abs':maxinterval},'LM_contrast':{'unit':'gue_tf_0/dev/NLL_and_perplexity','attempted_delta_values':4000,'point_max_abs':lmpoint,'every_draw_max_abs':lmdraw,'interval_max_abs':lmci,'aggregation_crosscheck_max_abs':maxlm},'restored_public_tables_checked':tableproof,'restored_figure_files_checked':figcount,'restored_plot_data_records':30886,'required_dependency_files_rechecked_before_use':len(used),'original_producer_paths_used':False,'prior_A08_40path_panel_reused_not_reexecuted':True,'GPU_recreation_claim':False,'CPU_environment':versions,'wall_seconds':time.monotonic()-t,'CPU_seconds':time.process_time()-cpu,'pid':__import__('os').getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21]};print(json.dumps(result))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--context',type=Path);v=p.parse_args();main(v.root,v.context)
