"""CPU recovery from consumer roots only. No producer configuration or refitting."""
from pathlib import Path
import argparse,json,hashlib,sys
import numpy as np
import joblib
from independent_math import reconstruct,metrics

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def checked(root,e):
 p=root/e['path'];assert p.resolve().is_relative_to(root.resolve()) and not p.is_symlink() and p.stat().st_size==e['bytes'] and sha(p)==e['sha256'];return p

def main(root,depmap,task):
 # Consumer paths and immutable descriptors are explicit. No historical producer absolute locator is followed.
 assert '/consumer' in str(root) and '/consumer' in str(depmap['A06_feature_consumer'])
 fr=Path(depmap['A06_feature_consumer']);assert sha(fr/'MEMBER_MANIFEST.json')==depmap['member_manifest_sha256'];index={e['path']:e for e in read(fr/'MEMBER_MANIFEST.json')['files']}
 rel=f'artifacts/features/R5/{task}/dev/COMPLETE.json';bp=checked(fr,index[rel]);bundle=read(bp);xx={k:[] for k in ['decoder_layer_16','final_norm']};meta={k:[] for k in ['ids','labels','groups','sequence_sha256']}
 for e in bundle['chunks']:
  rel='artifacts/'+e['path'];cp=fr/rel;assert sha(cp/'COMPLETE.json')==e['receipt_sha256'];checked(fr,index[rel+'/COMPLETE.json']);j=read(cp/'COMPLETE.json')
  for ent in j['files']:checked(fr,index[rel+'/'+ent['path']]);assert sha(cp/ent['path'])==ent['sha256']
  with np.load(cp/'features_and_lm.npz',allow_pickle=False) as z:
   for k in xx:assert z[k].dtype==np.float32;xx[k].append(z[k])
   for k in meta:meta[k].append(z[k])
 xx={k:np.concatenate(v) for k,v in xx.items()};meta={k:np.concatenate(v) for k,v in meta.items()};classes=np.array([0,1,2] if task=='gue_splice_reconstructed' else [0,1]);assert len(meta['ids'])==512
 deps=read(root/'DEPENDENCIES.json');checks=[];worst={};maxima={k:0. for k in ['probability','point_metric','marginal_draw','paired_draw','CI']};vectors=0;values=0
 def compare(kind,a,b,unit):
  a=np.asarray(a);b=np.asarray(b);assert a.shape==b.shape and np.array_equal(np.isnan(a),np.isnan(b));finite=np.isfinite(a)&np.isfinite(b);delta=float(np.max(np.abs(a[finite]-b[finite]))) if finite.any() else 0.;tol=1e-10 if kind=='probability' else 1e-12;assert delta<=tol,(kind,unit,delta)
  if delta>=maxima[kind]:maxima[kind]=delta;worst[kind]=unit
 def interval(x,valid):return np.quantile(x[valid],[.025,.975]) if valid.any() else np.array([np.nan,np.nan])
 draw=checked(root,deps['saved_draws'])
 with np.load(draw,allow_pickle=False) as z:
  names,inverse=np.unique(meta['groups'],return_inverse=True);assert np.array_equal(z['ids'],meta['ids']) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse) and int(z['seed'])==20261103;weights=np.stack([np.bincount(d,minlength=len(names)) for d in z['group_draws']])[:,inverse];assert weights.shape==(2000,512)
 refcache={}
 for key in xx:
  assert xx[key].dtype==np.float32 and xx[key].shape==(512,1920)
  for seed in [42,17,1234]:
   uid=f'R5/{task}/{key}/seed{seed}';unit=root/'artifacts/probes'/uid;receipt=read(unit/'COMPLETE.json');assert receipt['status']=='COMPLETE_UNVERIFIED' and receipt['producer_validation']=='PASS'
   for e in receipt['files']:checked(unit,e)
   head=joblib.load(unit/'head.joblib');base=joblib.load(checked(root,deps['base_heads'][key+'/seed'+str(seed)]));result=read(unit/'RESULTS.json');references={r['reference']:r for r in deps['reference_predictions'][key+'/seed'+str(seed)]}
   with np.load(unit/'dev_predictions.npz',allow_pickle=False) as z,np.load(unit/'dev_bootstrap.npz',allow_pickle=False) as boot:
    for k in meta:assert np.array_equal(z[k],meta[k])
    assert np.array_equal(z['classes'],classes)
    for policy,model in [('independent_refit',head),('fixed_original_base',base)]:
     name=uid+'/'+policy;assert np.array_equal(model[-1].classes_,classes);p=reconstruct(model,xx[key]);compare('probability',p,z[policy],name);dist,valid=metrics(meta['labels'],p,classes,weights);point,pvalid=metrics(meta['labels'],p,classes,np.ones((1,512)));assert pvalid.all() and np.array_equal(valid,boot['valid'])
     for row in result['metrics']:
      if row['policy']!=policy:continue
      m=row['metric'];compare('point_metric',point[m],[row['estimate']],name+'/'+m);compare('marginal_draw',dist[m],boot[policy+'__'+m],name+'/'+m);compare('CI',interval(dist[m],valid),[row['ci_low'],row['ci_high']],name+'/'+m)
     for refname in ['base','R1','control_composition','control_kmer4']:
      desc=references[refname];path=checked(root,desc);selector=desc['selectors'][policy];cachekey=(str(path),selector)
      if cachekey not in refcache:
       with np.load(path,allow_pickle=False) as rz:
        for k in ['ids','labels','groups']:assert np.array_equal(rz[k],meta[k])
        assert np.array_equal(rz['classes'],classes);rp=rz[selector];rd,rv=metrics(meta['labels'],rp,classes,weights);rpoint,rpv=metrics(meta['labels'],rp,classes,np.ones((1,512)));assert rpv.all();refcache[cachekey]=(rd,rv,rpoint)
      rd,rv,rpoint=refcache[cachekey];assert np.array_equal(valid,rv);rows=[r for r in result['paired_contrasts'] if r['policy']==policy and r['reference']==refname];assert len(rows)==5
      for row in rows:
       m=row['metric'];delta=dist[m]-rd[m];compare('paired_draw',delta,boot[policy+'__minus_'+refname+'__'+m],name+'/'+refname+'/'+m);compare('point_metric',point[m]-rpoint[m],[row['estimate']],name+'/'+refname+'/'+m);compare('CI',interval(delta,valid),[row['ci_low'],row['ci_high']],name+'/'+refname+'/'+m);vectors+=1;values+=len(delta)
     checks.append(dict(unit_id=uid,policy=policy,rows=512,groups=len(np.unique(meta['groups'])),classes=classes.tolist(),status='PASS'))
 assert len(checks)==12 and vectors==240 and values==480000
 return dict(status='PASS',checks=checks,paired_vectors=vectors,paired_values=values,max_abs_residuals=maxima,worst_units=worst,refits=0,producer_paths_used=False,new_A07_consumer=str(root),reused_A06_consumer=str(fr),inherited_dependency_new_download=False,independent_release='PENDING_A08',GPU_runtime_recreated=False)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--dependency-map',type=Path,required=True);p.add_argument('--task',required=True);v=p.parse_args();print(json.dumps(main(v.root,read(v.dependency_map),v.task),allow_nan=False))
