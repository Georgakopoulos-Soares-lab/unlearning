"""Portable A09 consumer: 24 prediction paths,60 saved classifier vectors,6 LM vectors; zero fitting."""
from pathlib import Path
import json,hashlib,argparse,os,sys,math,time,csv
import numpy as np
import joblib
from independent_math import reconstruct,metrics
from portable_math8 import resolve,probabilities,pair,weights_from_draws,historical_lm
from analysis_pairs import lm_numbers
from canonical9 import accept_source,unique_add
import key_contract5

def read(p):return json.loads(Path(p).read_text())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(root):
 start=time.monotonic();cpu=time.process_time();identity=read(root/'control/IDENTITY_CONTEXT.json');binding=read(root/'control/RECOVERY_INPUT_BINDINGS.json');mapping=binding['immutable_saved_outputs'];pub=root/'public';index=read(pub/'TABLE_INDEX.json');scientific={};keyids=set();source_index={e['source_id']:e for e in read(pub/'SOURCE_TABLE_INDEX.json')['sources']};source_files=read(root/'IMMUTABLE_SOURCE_FILES.json')['files'];original_cache={};source_joins=0
 for p in index['partitions']:
  path=pub/p['path'];assert sha(path)==p['sha256'];rs=list(csv.DictReader(path.open()));assert len(rs)==p['rows']
  for r in rs:
   assert r['A09_row_id'] not in scientific and r['A09_scientific_key_sha256'] not in keyids;scientific[r['A09_row_id']]=r;keyids.add(r['A09_scientific_key_sha256']);sid=r['A09_source_id']
   if sid not in original_cache:
    e=source_files[sid];f=root/e['member'];assert sha(f)==source_index[sid]['sha256']==e['sha256'];original_cache[sid]=list(csv.DictReader(f.open()))
   old=original_cache[sid][int(r['A09_source_CSV_line'])-2];accept_source(r,old,old.get('table_kind') or source_index[sid]['kind'],identity['endpoint_content_ids'],identity['protocol_sha256'])
   for k in ['estimate','ci_low','ci_high','status','task','split','representation','CV_seed','policy','source_policy','reference','metric']:
    if k in old:assert r.get(k,'')==old[k],(k,r['A09_row_id'])
   source_joins+=1
 assert len(scientific)==len(keyids)==106526
 amendment={r['logical_id'] for r in scientific.values() if r['A09_integration_scope'] in ['R5_A06','R5_A08']};expected={r['logical_id'] for r in key_contract5.table_keys(read(root/'immutable-design/TABLE_KEY_DESIGN.json'),identity['coverage_plan_sha256'])};assert amendment==expected and len(amendment)==33684
 marginal={(r['checkpoint_alias'],r['task'],r['split'],r['representation'],r['CV_seed'],r['policy'],r['metric']):r for r in scientific.values() if r['A09_table_kind']=='classifier_marginal'}
 maxima={'probability':0.,'point':0.,'draw':0.,'CI':0.};counts={k:0 for k in maxima};worst={};checks=[]
 def compare(kind,a,b,unit,valid=None):
  a=np.asarray(a,dtype=np.float64);b=np.asarray(b,dtype=np.float64);assert a.shape==b.shape and np.array_equal(np.isnan(a),np.isnan(b));mask=np.isfinite(a) if valid is None else valid;assert np.isfinite(a[mask]).all() and np.isfinite(b[mask]).all();error=float(np.max(np.abs(a[mask]-b[mask]))) if mask.any() else 0.;assert error<=(1e-10 if kind=='probability' else 1e-12),(kind,unit,error);counts[kind]+=int(mask.sum())
  if error>=maxima[kind]:maxima[kind]=error;worst[kind]=unit
 for u in binding['prediction_units']:
  feature_parts=[];metadata={k:[] for k in ['ids','labels','groups','sequence_sha256']}
  for d in u['chunks']:
   with np.load(resolve(d,mapping),allow_pickle=False) as z:
    assert z[u['array_key']].dtype==np.float32;feature_parts.append(z[u['array_key']])
    for k in metadata:metadata[k].append(z[k])
  x=np.concatenate(feature_parts);meta={k:np.concatenate(v) for k,v in metadata.items()};assert x.shape==(1497 if u['task']=='emp_H3' else 512,1920)
  for policy,head in u['heads'].items():
   saved,m,classes=probabilities(u['endpoint'],policy,mapping);pair(meta,m,classes,classes);model=joblib.load(resolve(head,mapping));assert np.array_equal(model[-1].classes_,classes);p=reconstruct(model,x);name=u['task']+'/'+u['representation']+'/'+policy;compare('probability',p,saved,name);point,valid=metrics(meta['labels'],p,classes,np.ones((1,len(p))));assert valid.all()
   for metric in point:
    r=marginal['R5',u['task'],'dev',u['representation'],'42',policy,metric];compare('point',[point[metric][0]],[float(r['estimate'])],name+'/'+metric)
   checks.append({'kind':'prediction','task':u['task'],'representation':u['representation'],'policy':policy,'status':'PASS'})
 for u in binding['classifier_units']:
  j=read(resolve(u['result'],mapping));target=j['endpoints']['target'];reference=j['endpoints']['reference'];savedpath=resolve(u['paired_draws'],mapping)
  with np.load(savedpath,allow_pickle=False) as saved:
   for policy in ['independent_refit','fixed_original_base']:
    pt,meta,cl=probabilities(target,policy,mapping);pr,mr,cr=probabilities(reference,policy,mapping);pair(meta,mr,cl,cr);assert target['draw']==reference['draw'];w,draw=weights_from_draws(resolve(target['draw'],mapping),meta);a,va=metrics(meta['labels'],pt,cl,w);b,vb=metrics(meta['labels'],pr,cl,w);assert np.array_equal(va,vb) and np.array_equal(va,saved['valid']);pa,pv=metrics(meta['labels'],pt,cl,np.ones((1,len(pt))));pb,qv=metrics(meta['labels'],pr,cl,np.ones((1,len(pt))));assert pv.all() and qv.all()
    for row in [r for r in j['rows'] if r['policy']==policy]:
     r=scientific[row['logical_id']];metric=r['metric'];delta=a[metric]-b[metric];name=row['logical_id'];compare('draw',delta,saved[policy+'__'+metric],name,va);compare('point',[pa[metric][0]-pb[metric][0]],[float(r['estimate'])],name);compare('CI',np.quantile(delta[va],[.025,.975],method='linear'),[float(r['ci_low']),float(r['ci_high'])],name);checks.append({'kind':'classifier_vector','logical_id':name,'valid':int(va.sum()),'attempted':2000,'status':'PASS'})
 raw_routes=[]
 for u in binding['LM_units']:
  j=read(resolve(u['result'],mapping));m={}
  for side,desc in u['statistics'].items():
   with np.load(resolve(desc,mapping),allow_pickle=False) as z:m[side]={k:z[k] for k in z.files}
   item=j['endpoints'][side];assert m[side]['nll_sum'].dtype==np.float32 and m[side]['n_tokens'].dtype==np.int64;assert np.array_equal(m[side]['n_tokens'],m[side]['lengths']-1)
   if item['endpoint']['prediction_descriptor']['hash_kind']=='LM_SEALED_FEATURE_BUNDLE_WITH_SUM_COUNT_SELECTOR':
    raw,_=historical_lm(item['endpoint']['prediction_descriptor'],item['endpoint']['raw_cohort'],u['task'],'dev',mapping)
    for key in raw:assert np.array_equal(raw[key],m[side][key])
    raw_routes.append(item['candidate']+'/'+u['task']+'/dev')
  a,b=m['target'],m['reference']
  for key in ['ids','labels','groups','sequence_sha256','lengths','n_tokens']:assert np.array_equal(a[key],b[key])
  td=j['endpoints']['target']['endpoint']['draw'];assert td==j['endpoints']['reference']['endpoint']['draw'];w,draw=weights_from_draws(resolve(td,mapping),a);pa,da,_=lm_numbers(a,draw,w);pb,db,_=lm_numbers(b,draw,w);pts={'causal_nll':pa-pb,'perplexity':math.exp(pa)-math.exp(pb)};deltas={'causal_nll':da-db,'perplexity':np.exp(da)-np.exp(db)}
  with np.load(resolve(u['paired_draws'],mapping),allow_pickle=False) as saved:
   assert saved['valid'].all()
   for row in j['rows']:
    r=scientific[row['logical_id']];metric=r['metric'];name=row['logical_id'];compare('point',[pts[metric]],[float(r['estimate'])],name);compare('draw',deltas[metric],saved[metric],name);compare('CI',np.quantile(deltas[metric],[.025,.975],method='linear'),[float(r['ci_low']),float(r['ci_high'])],name);checks.append({'kind':'LM_vector','logical_id':name,'attempted':2000,'valid':2000,'status':'PASS'})
 # Regenerate report-facing source joins and every plotted/displayed numeric cell.
 displays=list(csv.DictReader((pub/'REPORT_DISPLAY_DATA.csv').open()));plot=read(pub/'plot_data/main_figures.json');joined=0
 for r in displays+[r for group in ['task_entry','profiles','LM'] for r in plot[group]]:
  source=scientific[r['A09_row_id']]
  for key in ['estimate','ci_low','ci_high']:
   if r.get(key) not in ['',None]:assert float(r[key])==float(source[key])
  for key in ['task','split','representation','CV_seed','policy','metric','reference','checkpoint_alias']:
   if key in r and r[key]!='':assert str(r[key])==str(source.get(key,''))
  joined+=1
 for gap in plot['policy_gaps']:
  a=scientific[gap['refitted_row_id']];b=scientific[gap['fixed_row_id']];assert float(gap['estimate'])==float(a['estimate'])-float(b['estimate'])
 cov=list(csv.DictReader((pub/'COVERAGE.csv').open()));inc={(r['candidate'],r['task']):r for r in csv.DictReader((pub/'INCLUSION_EXPOSURE_PLAN.csv').open())}
 for r in plot['coverage']:
  n=sum(v['candidate']==r['checkpoint_alias'] and v['task']==r['task'] and v['kind']=='final_head' and v['independently_released']=='True' for v in cov);assert n==r['released_heads'] and int(n==78)==r['value']
 for r in plot['declarations']:
  v=inc.get((r['checkpoint_alias'],r['task']));expected_value=2 if v is None or r['checkpoint_alias']=='R2' else {'true':1,'false':0}.get(v['observed_selected_config_declares_family'].lower(),2);assert expected_value==r['value'] and r['realized_exposure']=='UNKNOWN'
 assert sum(e['kind']=='prediction' for e in checks)==24 and sum(e['kind']=='classifier_vector' for e in checks)==60 and sum(e['kind']=='LM_vector' for e in checks)==6
 return {'status':'PASS','prediction_paths':24,'classifier_vectors':60,'LM_vectors':6,'paired_attempted_values':132000,'comparison_counts':counts,'max_abs_residuals':maxima,'worst_private_units':worst,'canonical_report_keys_regenerated':len(scientific),'source_row_hash_and_value_joins':source_joins,'R5_amendment_keys_regenerated':33684,'coverage_declaration_cells_regenerated':84,'display_plot_source_joins':joined,'descriptive_policy_gap_checks':len(plot['policy_gaps']),'historical_typed_LM_routes':raw_routes,'checks':checks,'new_fits_model_forwards_or_draws':0,'producer_paths_used':False,'GPU_recreation_verified':False,'wall_seconds':time.monotonic()-start,'CPU_seconds':time.process_time()-cpu}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True);a=parser.parse_args();events=[]
 def deny(event,args):
  if event in ['open','os.listdir','os.scandir'] and args and isinstance(args[0],(str,bytes,os.PathLike)):
   p=os.path.abspath(os.fsdecode(args[0]))
   if any(p==b or p.startswith(b+'/') for b in ['/workspace/meeting-artifacts','/workspace/agent-handoff','/workspace/wt-pod-a']):events.append(event);raise PermissionError('A09 producer-tree access denied')
 sys.addaudithook(deny)
 try:open('/workspace/meeting-artifacts/A09-producer-denial-sentinel','rb')
 except PermissionError:pass
 else:raise AssertionError('Producer denial sentinel not rejected')
 out=main(a.root);assert len(events)==1;out['producer_path_denial_active']=True;out['sentinel_rejection_proven']=True;print(json.dumps(out,allow_nan=False))
