"""Saved-head reconstruction of inherited fixed selectors. No fitting, backbone execution or new draws."""
from pathlib import Path
import sys,os,json,hashlib,time,resource
import numpy as np,joblib
from threadpoolctl import threadpool_limits
from panel_metrics import reconstruct,metrics
from report_data_v2 import read,sha,save
root=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=True);mode=sys.argv[3] if len(sys.argv)>3 else 'fresh';units=read(root/'panel/PREPARED_UNITS.json');P=root/'panel';bindings={b['path']:b for b in read(P/'FEATURE_BINDINGS.json')};cache={};replay_values={};results=[];started=time.monotonic();worst={};coordinate_counts={};unitdir=out/'units';unitdir.mkdir(exist_ok=True)
if mode in ['qualify','qualify_pairs']:
 selected=[units[0],next(u for u in units if u['candidate']=='candidate_01' and u['task']=='gue_splice_reconstructed' and u['policy']=='fixed_original_base')]
 if mode=='qualify_pairs':
  wanted={(u['candidate'],u['task'],u['representation'],u['seed']) for u in selected};units=[u for u in units if (u['candidate'],u['task'],u['representation'],u['seed']) in wanted]
 else:units=selected
if mode=='fresh':
 runtime=Path(sys.executable).parent.parent.resolve()
 def audit(event,args):
  if event=='open' and isinstance(args[0],(str,bytes,os.PathLike)):
   p=Path(os.fsdecode(args[0])).resolve()
   if str(p).startswith('/workspace/pod-a-saliency') and not any(p==q or q in p.parents for q in [root,out,runtime]):raise PermissionError('Unrecorded producer-tree fallback denied')
 sys.addaudithook(audit)
MAP={'AUROC':'auroc','AP':'average_precision','accuracy':'accuracy','balanced_accuracy':'balanced_accuracy','cross_entropy':'classification_cross_entropy'}
def compare(a,b,tol,component,u,metric=None):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape and a.size and np.isfinite(a).all() and np.isfinite(b).all();diff=np.abs(a-b);ix=int(np.argmax(diff));mx=float(diff.flat[ix]);key='probability' if tol==1e-10 else 'metric_draw_CI';record={'abs_residual':mx,'candidate':u['candidate'],'task':u['task'],'representation':u['representation'],'seed':u['seed'],'policy':u['policy'],'unit':u['unit'],'metric':metric,'component':component,'index':list(map(int,np.unravel_index(ix,diff.shape))),'actual':float(a.flat[ix]),'reference':float(b.flat[ix])}
 if key not in worst or mx>worst[key]['abs_residual']:worst[key]=record
 coordinate_counts[key]=coordinate_counts.get(key,0)+int(a.size);assert mx<=tol,(record,'TOLERANCE_EXCEEDED');return record
with threadpool_limits(limits=1):
 for number,u in enumerate(units,1):
  receipt=unitdir/(u['unit']+'.json')
  if receipt.exists():raise RuntimeError('Use explicit source-bound resume reconciliation; do not overwrite or silently rerun completed units')
  xfile=P/u['features'];binding=bindings[u['features']];assert sha(xfile)==binding['sha256'] and sha(P/u['head'])==u['head_sha256'];meta=read(P/u['row_metadata']);expected=u['expected_released_metrics'];checks=[]
  with np.load(xfile,allow_pickle=False) as z:
   x=z['features'];y=z['labels'];classes=z['classes'];assert x.dtype==np.float32 and x.shape==(len(meta),1920) and hashlib.sha256(x.tobytes()).hexdigest()==binding['matrix_value_sha256'];assert y.tolist()==[r['label'] for r in meta] and z['ids'].tolist()==[r['id'] for r in meta] and z['groups'].tolist()==[r['group'] for r in meta]
  model=joblib.load(P/u['head']);assert model[-1].classes_.tolist()==classes.tolist()
  with np.load(P/u['paths']['predictions.npz'],allow_pickle=False) as z:
   assert z['ids'].tolist()==[r['id'] for r in meta] and np.array_equal(z['labels'],y) and z['groups'].tolist()==[r['group'] for r in meta] and np.array_equal(z['classes'],classes);p=z['probabilities'];checks.append(compare(reconstruct(model,x),p,1e-10,'saved_head_probability',u))
  if u['task'] not in cache:
   group_names,inverse=np.unique([r['group'] for r in meta],return_inverse=True)
   with np.load(P/u['original_draws'],allow_pickle=False) as z:
    draws=z['group_draws'];assert draws.shape==(2000,len(group_names)) and z['ids'].tolist()==[r['id'] for r in meta] and z['group_names'].tolist()==group_names.tolist() and np.array_equal(z['row_groups'],inverse)
   count=np.zeros((len(draws),len(group_names)),dtype=np.int64);np.add.at(count,(np.arange(len(draws))[:,None],draws),1);assert np.array_equal(count.sum(1),np.full(2000,len(group_names)));cache[u['task']]=count[:,inverse].astype(np.float64)
  weights=cache[u['task']];point,pointvalid=metrics(y,p,classes,np.ones((1,len(y))));vectors,valid=metrics(y,p,classes,weights);assert pointvalid[0]
  replay_values[u['unit']]=(float(point['auroc'][0]),vectors['auroc'],valid&np.isfinite(vectors['auroc']),u)
  m=read(P/u['paths']['METRICS.json']);assert m['identity']['planned_spec_id']==expected[0]['prediction_planned_spec_id'] and m['identity']['head_sha256']==u['head_sha256']
  with np.load(P/u['paths']['draws.npz'],allow_pickle=False) as z:
   for er in expected:
    name=er['metric'];cr=next(r['canonical_metric'] for r in m['metrics'] if r['canonical_metric']['metric']==name);v=vectors[MAP[name]];mask=valid&np.isfinite(v);oldmask=z[name+'_valid'] if name+'_valid' in z else z['valid'];assert np.array_equal(mask,oldmask) and np.isnan(v[~mask]).all() and np.isnan(z[name][~mask]).all();assert cr['sample_count']==len(meta) and cr['group_count']==len(set(r['group'] for r in meta)) and cr['bootstrap_valid']==int(mask.sum()) and cr['bootstrap_invalid']==int((~mask).sum())
    checks.append(compare(point[MAP[name]],[er['estimate']],1e-12,'point_vs_released_endpoint',u,name));assert abs(cr['estimate']-er['estimate'])<=1e-12
    if mask.any():checks.extend([compare(v[mask],z[name][mask],1e-12,'original_draw_vector',u,name),compare(np.percentile(v[mask],[2.5,97.5],method='linear'),[er['ci_low'],er['ci_high']],1e-12,'original_conditional_interval',u,name)])
    else:assert er['ci_low'] is None and er['ci_high'] is None
  result={'status':'PASS','unit':u['unit'],'selector':{k:u[k] for k in ['candidate','task','representation','seed','policy']},'original_prediction_id':m['identity']['planned_spec_id'],'samples':len(meta),'groups':len(set(r['group'] for r in meta)),'marginal_vectors':5,'attempted_draw_values':10000,'checks':checks};save(receipt,result);results.append(result)
  if number%10==0:print('RESTORED_PANEL',number,'of',len(units),u['candidate'],u['task'],round(time.monotonic()-started,1),flush=True)
paired_done=[]
if (P/'PAIRED_PANEL.json').exists():
 with np.load(P/'PAIRED_PANEL.npz',allow_pickle=False) as z:
  for entry in read(P/'PAIRED_PANEL.json'):
   if entry['target_panel_unit'] not in replay_values or entry['reference_panel_unit'] not in replay_values:continue
   pointA,vA,mA,u=replay_values[entry['target_panel_unit']];pointB,vB,mB,_=replay_values[entry['reference_panel_unit']];mask=mA&mB;vector=np.full(vA.shape,np.nan);vector[mask]=vA[mask]-vB[mask];row=entry['source_row'];index=entry['index'];assert np.array_equal(mask,z['valid'][index]);checks=[compare([pointA-pointB],[row['estimate']],1e-12,'paired_point',u,'AUROC'),compare(vector[mask],z['draws'][index][mask],1e-12,'paired_original_draws',u,'AUROC'),compare(np.percentile(vector[mask],[2.5,97.5],method='linear'),[row['ci_low'],row['ci_high']],1e-12,'paired_conditional_interval',u,'AUROC')];paired_done.append({'contrast_id':row['id'],'status':'PASS','checks':checks})
 save(out/'PAIRED_RECONSTRUCTION.json',paired_done)
 if mode=='fresh':assert len(paired_done)==108
report={'status':'PASS','mode':mode,'existing_paired_contrasts_reconstructed':len(paired_done),'paired_attempted_original_draw_values':len(paired_done)*2000,'saved_prediction_paths_reconstructed':len(results),'marginal_metric_vectors':len(results)*5,'attempted_draw_values':len(results)*10000,'probability_atol':1e-10,'metric_draw_interval_atol':1e-12,'rtol':0,'worst_residuals_with_locations':worst,'coordinates_compared':coordinate_counts,'CPU_threads':1,'new_fits':0,'backbone_inference':0,'new_draws':0,'producer_fallback':False if mode=='fresh' else 'qualification_on_declared_staged_inputs','GPU_replay':False,'clean_runtime_recreation':False,'runtime':'Existing qualified S03 CPU runtime, source-pinned environment reused','elapsed_seconds':time.monotonic()-started,'CPU_seconds':time.process_time(),'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'selectors':[r['selector'] for r in results]};assert report['peak_RSS_bytes']<=8*1024**3;save(out/'NUMERICAL_PANEL_RESULT.json',report);print('S11_SAVED_ANALYSIS_PANEL_PASS',len(results),json.dumps(worst),flush=True)
