"""Standalone CPU consumer using only freshly restored R5 payload/dependency members."""
from pathlib import Path
import argparse,hashlib,json,math,time,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np,joblib
from threadpoolctl import threadpool_limits
from independent_math import reconstruct,metrics
METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy'];LAYERS=[f'decoder_layer_{i}' for i in range(25)]+['final_norm']
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def error(a,b,tol=1e-12):
 a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape and np.array_equal(np.isnan(a),np.isnan(b));mask=np.isfinite(a)&np.isfinite(b);assert not np.isinf(a).any() and not np.isinf(b).any();d=float(np.max(np.abs(a[mask]-b[mask]))) if mask.any() else 0.;assert d<=tol,d;return d
def bootstrap_weights(path,ids,groups):
 with np.load(path,allow_pickle=False) as z:
  names,inverse=np.unique(groups,return_inverse=True);assert np.array_equal(z['ids'],ids) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse) and int(z['seed'])==20261103;draw=z['group_draws'];assert draw.shape==(2000,len(names));return np.stack([np.bincount(d,minlength=len(names)) for d in draw])[:,inverse]
def main(root,group):
 start=time.monotonic();root=Path(root);art=root/'artifacts';selected=read(root/'RESTORE_MAP.json');slice_manifest=read(root/'FEATURE_SLICE_REFERENCES.json');metadata={};feature_views={};lm=[];feature_matrices=0
 if group=='H3':
  old_indices={}
  for node in selected['historical_archives']:
   p=root/node['protected_checksum_index'];assert sha(p)==node['original_checksum_index_sha256'];old_indices[node['id']]={e['path']:e for e in read(p)['files']}
  for e in read(root/'PINNED_HISTORICAL_DEPENDENCIES.json')['files']:
   original=old_indices[e['historical_dependency']][e['historical_member']];assert original['sha256']==e['sha256'] and original['bytes']==e['bytes'];assert sha(root/e['member'])==e['sha256'] and (root/e['member']).stat().st_size==e['bytes']
 for done in sorted((art/'features/R5').glob('*/*/COMPLETE.json')):
  task=done.parent.parent.name;split=done.parent.name;assert (task=='emp_H3')==(group=='H3');bundle=read(done);u=bundle['identity']['unit'];manifest=root/'manifests'/(task+'__'+split+'.jsonl');assert sha(manifest)==u['manifest']['sha256'];rows=[json.loads(s) for s in manifest.read_text().splitlines()];parts={k:[] for k in ['ids','labels','groups','sequence_sha256','lengths','nll_sum','n_tokens']};features={k:[] for k in LAYERS} if group=='H3' else None;cursor=0
  for e in bundle['chunks']:
   chunk=art/e['path'];receipt=read(chunk/'COMPLETE.json');assert sha(chunk/'COMPLETE.json')==e['receipt_sha256'];p=chunk/'features_and_lm.npz';assert sha(p)==receipt['files'][0]['sha256'];rr=rows[cursor:cursor+e['rows']]
   with np.load(p,allow_pickle=False) as z:
    assert z['ids'].tolist()==[r['id'] for r in rr] and z['labels'].tolist()==[r['label'] for r in rr] and z['groups'].tolist()==[r['exact_rc_group'] for r in rr] and z['sequence_sha256'].tolist()==[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rr];assert np.array_equal(z['lengths'],[len(r['sequence']) for r in rr]) and np.array_equal(z['n_tokens'],z['lengths']-1) and z['nll_sum'].dtype==np.float32
    for k in parts:parts[k].append(z[k])
    for k in LAYERS:
     f=z[k];assert f.shape==(len(rr),1920) and f.dtype==np.float32 and np.isfinite(f).all()
     ref=slice_manifest[str(Path(e['path'])/k)];take=f[ref['rows']][:,ref['columns']];assert hashlib.sha256(take.tobytes()).hexdigest()==ref['sha256']
     if features is not None:features[k].append(f)
   cursor+=len(rr)
  assert cursor==bundle['rows']==len(rows);m={k:np.concatenate(v) for k,v in parts.items()};assert digest(m['ids'].tolist())==u['ordered_ids_sha256'];metadata[(task,split)]=m
  if features is not None:feature_views[(task,split)]={k:np.concatenate(v) for k,v in features.items()}
  feature_matrices+=26;loss=m['nll_sum'].astype(np.float64);counts=m['n_tokens'].astype(np.float64);nll=math.fsum(loss.tolist())/math.fsum(counts.tolist());saved=read(art/'lm/R5'/task/split/'RESULTS.json');assert abs(nll-saved['NLL'])<=1e-12 and saved['paired_contrasts']==[]
  with np.load(art/'lm/R5'/task/split/'sufficient_statistics.npz',allow_pickle=False) as z:
   for k in m:assert np.array_equal(z[k],m[k])
  lm.append({'task':task,'split':split,'rows':len(m['ids']),'targets':int(counts.sum()),'NLL_abs_residual':abs(nll-saved['NLL'])})
 panel=[];paired_arrays=0;maxprob=0.;maxmetric=0.;maxdraw=0.;maxci=0.;ref_cache={};audit_artifacts=0
 if group=='H3':
  for key in ['decoder_layer_16','final_norm']:
   for seed in [42,17,1234]:
    unit=art/'h3/R5'/key/('seed'+str(seed));producer=read(unit/'PRODUCER_COMPLETE.json');head=joblib.load(unit/'head.joblib');basefile=root/'dependencies/base-heads'/key/('seed'+str(seed))/'base.joblib';assert sha(basefile)==producer['original_base_head']['sha256'];base=joblib.load(basefile);auditroot=art/'audit-refits/R5'/key/('seed'+str(seed));audit=read(auditroot/'COMPLETE.json');assert audit['status']=='PASS' and audit['audit_kind']=='INDEPENDENT_FULL_CV_AND_FINAL_REFIT';trace=read(auditroot/'FULL_CV_REFIT.json');assert max(trace['candidates'],key=lambda e:(e['mean_auroc'],-e['C']))['C']==trace['selected_C']==read(unit/'FINAL_FIT.json')['C'];audithead=joblib.load(auditroot/'independent_scaler_head.joblib');audit_artifacts+=1
    for split in ['dev','test']:
     m=metadata[('emp_H3',split)];x=feature_views[('emp_H3',split)][key];weights=bootstrap_weights(root/'dependencies/draws'/(split+'_resampling.npz'),m['ids'],m['groups']);result=read(unit/'RESULTS.json')
     with np.load(root/'dependencies/reference-predictions'/key/('seed'+str(seed))/(split+'_predictions.npz'),allow_pickle=False) as z:
      assert np.array_equal(z['ids'],m['ids']) and np.array_equal(z['labels'],m['labels']);old={k:z[k] for k in ['prob_base_refit','prob_h3_only_refit','prob_h3_only_fixed_base']}
     with np.load(unit/(split+'_predictions.npz'),allow_pickle=False) as pred,np.load(unit/(split+'_bootstrap.npz'),allow_pickle=False) as boot:
      assert np.array_equal(pred['ids'],m['ids']) and np.array_equal(pred['classes'],[0,1]);error(reconstruct(audithead,x),pred['independent_refit'],1e-10)
      for policy,model in [('independent_refit',head),('fixed_original_base',base)]:
       p=reconstruct(model,x);maxprob=max(maxprob,error(p,pred[policy],1e-10));point,_=metrics(m['labels'],p,np.array([0,1]),np.ones((1,len(p))));dist,valid=metrics(m['labels'],p,np.array([0,1]),weights);assert np.array_equal(valid,boot['valid'])
       for metric in METRICS:
        row=next(e for e in result['metrics'] if e['split']==('test_exploratory' if split=='test' else split) and e['policy']==policy and e['metric']==metric);maxmetric=max(maxmetric,error([point[metric][0]],[row['estimate']]));maxdraw=max(maxdraw,error(dist[metric],boot[policy+'__'+metric]));maxci=max(maxci,error(np.quantile(dist[metric][valid],[.025,.975]),[row['ci_low'],row['ci_high']]))
       refs={'base':old['prob_base_refit'],'R1':old['prob_h3_only_refit' if policy=='independent_refit' else 'prob_h3_only_fixed_base']}
       for control in ['composition','kmer4']:
        with np.load(root/'dependencies/control-predictions'/control/('seed'+str(seed))/(split+'_predictions.npz'),allow_pickle=False) as z:assert np.array_equal(z['ids'],m['ids']);refs['control_'+control]=z['probabilities']
       for name,rp in refs.items():
        ck=(hashlib.sha256(rp.tobytes()).hexdigest(),split)
        if ck not in ref_cache:ref_cache[ck]=(metrics(m['labels'],rp,np.array([0,1]),weights),metrics(m['labels'],rp,np.array([0,1]),np.ones((1,len(rp))))[0])
        (rd,rv),rpoint=ref_cache[ck];common=valid&rv
        for metric in METRICS:
         delta=dist[metric]-rd[metric];maxdraw=max(maxdraw,error(delta,boot[policy+'__minus_'+name+'__'+metric]));paired_arrays+=1;row=next(e for e in result['paired_contrasts'] if e['split']==split and e['policy']==policy and e['reference']==name and e['metric']==metric);maxmetric=max(maxmetric,error([point[metric][0]-rpoint[metric][0]],[row['difference']]));maxci=max(maxci,error(np.quantile(delta[common],[.025,.975]),[row['ci_low'],row['ci_high']]));assert row['valid']==int(common.sum())
       panel.append({'representation':key,'seed':seed,'split':split,'policy':policy,'status':'PASS'})
  assert len(panel)==24 and audit_artifacts==6 and paired_arrays==480
 assert len(lm)==(3 if group=='H3' else 10);assert feature_matrices==(78 if group=='H3' else 260);assert 'torch' not in sys.modules;report={'status':'PASS','group':group,'restored_policy_prediction_metric_paths':len(panel),'restored_prediction_panel':panel,'restored_paired_full_draw_arrays':paired_arrays,'restored_full_CV_audit_artifacts':audit_artifacts,'all_restored_representation_matrices_shape_dtype_finite':feature_matrices,'metadata_selected_feature_slices':'All26 hooks every chunk; first/middle/last rows and channels0/16/1919','restored_LM_units':lm,'probability_max_abs':maxprob,'metric_max_abs':maxmetric,'draw_max_abs':maxdraw,'interval_max_abs':maxci,'external_producer_paths_used':False,'GPU_or_model_loads':0,'new_refits':0,'full_GPU_runtime_recreation_claimed':False,'wall_seconds':time.monotonic()-start};(root/'FRESH_COMPUTATIONAL_RESTORE.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--group',choices=['H3','other_five'],required=True);args=p.parse_args()
 with threadpool_limits(limits=4):main(args.root,args.group)
