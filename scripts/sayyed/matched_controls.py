"""Matched exploratory CPU controls; immutable prior outputs are read only."""
import csv,hashlib,json,shutil,time,subprocess
from pathlib import Path
import numpy as np
import joblib
from threadpoolctl import threadpool_limits
from benign_pilot.extension import controls
from scripts.sayyed.h3_followup import train_model
from scripts.sayyed.multiretain_metrics import point_metrics,bootstrap_metrics
from scripts.sayyed.multiretain_independent import metrics as independent,reconstruct
R=Path('/workspace/meeting-artifacts/benign-followup-v1');OLD=Path('/workspace/meeting-artifacts/multiretain-layers-v1')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,allow_nan=False))
def run():
 start=time.monotonic();cpu=time.process_time();records=[];contrasts=[];units=[];sources={};maxdelta=0.
 for group in ['H3','other_five']:
  source=OLD/'manifests'/(group+'.jsonl');dest=R/'manifests'/source.name;dest.parent.mkdir(exist_ok=True);shutil.copy2(source,dest);rows=[json.loads(x) for x in dest.read_text().splitlines()]
  for task in sorted({r['task'] for r in rows}):
   rr=[r for r in rows if r['task']==task];ids=np.array([r['id'] for r in rr]);y=np.array([r['label'] for r in rr]);groups=np.array([r['exact_rc_group'] for r in rr]);tr=np.array([i for i,r in enumerate(rr) if r['split']=='train']);classes=np.unique(y[tr]);lookup={x:i for i,x in enumerate(ids)};features=controls([r['sequence'] for r in rr]);td=R/'tasks'/task;td.mkdir(parents=True,exist_ok=True)
   np.savez_compressed(td/'features.npz',ids=ids,labels=y,groups=groups,sequence_sha256=np.array([hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rr]),**features)
   for seed in [42,17,1234]:
    foldsource=OLD/'probes'/group/task/f'folds_seed{seed}.json';shutil.copy2(foldsource,td/foldsource.name);folds=json.loads(foldsource.read_text());foldix=[(np.array([lookup[x] for x in f['train_ids']]),np.array([lookup[x] for x in f['validation_ids']])) for f in folds]
    for a,b in foldix:
     assert set(a)|set(b)==set(tr) and not set(a)&set(b) and not set(groups[a])&set(groups[b])
    for name,x in features.items():
     unit=td/name/f'seed{seed}';unit.mkdir(parents=True,exist_ok=True)
     if (unit/'COMPLETE.json').exists():raise ValueError('Fresh execution only; do not overwrite units')
     if (unit/'selection.json').exists():
      model=joblib.load(unit/'model.joblib');assert np.array_equal(model.classes_,classes)
     else:
      candidates=[]
      for c in [.1,1.,10.]:
       scores=[];attempts=[]
       for a,b in foldix:
        m,logs=train_model(x[a],y[a],c);scores.append(point_metrics(y[b],m.predict_proba(x[b]),classes)[0]['auroc']);attempts.append(logs)
       candidates.append(dict(C=c,scores=scores,mean_auroc=float(np.mean(scores)),convergence=attempts))
      c=max(candidates,key=lambda z:(z['mean_auroc'],-z['C']))['C'];model,logs=train_model(x[tr],y[tr],c);assert np.array_equal(model.classes_,classes);joblib.dump(model,unit/'model.joblib');write(unit/'selection.json',dict(candidates=candidates,selected_C=c,refit=logs,train_rows=len(tr)))
     for split in (['dev','test'] if group=='H3' else ['dev']):
      ix=np.array([i for i,r in enumerate(rr) if r['split']==split]);sample=OLD/'probes'/group/task/f'{split}_resampling.npz';copied=td/sample.name
      if not copied.exists():shutil.copy2(sample,copied)
      with np.load(copied,allow_pickle=False) as z:
       assert np.array_equal(z['ids'],ids[ix]);assert np.array_equal(z['group_names'][z['row_groups']],groups[ix]);weights=np.stack([np.bincount(a,minlength=len(z['group_names'])) for a in z['group_draws']])[:,z['row_groups']]
      p=model.predict_proba(x[ix]);assert np.max(np.abs(reconstruct(joblib.load(unit/'model.joblib'),x[ix])-p))<1e-10
      np.savez_compressed(unit/f'{split}_predictions.npz',ids=ids[ix],labels=y[ix],groups=groups[ix],classes=classes,probabilities=p)
      point,support=point_metrics(y[ix],p,classes);sampled,valid=bootstrap_metrics(y[ix],p,classes,weights);ip,iv=independent(y[ix],p,classes,np.ones((1,len(ix))));ib,ibv=independent(y[ix],p,classes,weights);assert np.array_equal(valid,ibv)
      for metric,value in point.items():
       delta=max(float(abs(ip[metric][0]-value)),float(np.max(np.abs(ib[metric][valid]-sampled[metric][valid]))));maxdelta=max(maxdelta,delta);assert delta<1e-12
       records.append(dict(task=task,split=split,seed=seed,readout=name,layer='sequence_control',policy='refit',metric=metric,value=value))
      write(unit/f'{split}_support.json',support);np.savez_compressed(unit/f'{split}_bootstrap.npz',valid=valid,**sampled)
      for layer in ['decoder_layer_16','final_norm']:
       orig=OLD/'probes'/group/task/layer/f'seed{seed}';key=f'{task}/{layer}/seed{seed}/{split}';anchor=R/'anchors'/key;anchor.mkdir(parents=True,exist_ok=True)
       if key not in sources:
        receipt=json.loads((orig/'COMPLETE.json').read_text())
        for filename in [f'{split}_predictions.npz',f'{split}_bootstrap.npz','results.json']:
         src=orig/filename;entry=next(a for a in receipt['files'] if a['path']==str(src));assert sha(src)==entry['sha256'];shutil.copy2(src,anchor/filename)
        sources[key]=dict(original=str(orig),receipt_sha256=sha(orig/'COMPLETE.json'),files={p.name:sha(p) for p in anchor.iterdir()})
       with np.load(anchor/f'{split}_predictions.npz',allow_pickle=False) as z:
        assert np.array_equal(z['ids'],ids[ix]) and np.array_equal(z['labels'],y[ix]) and np.array_equal(z['classes'],classes) and np.array_equal(z['groups'],groups[ix]);pred={pol:z['prob_'+pol] for pol in ['base_refit','h3_only_refit','h3_only_fixed_base']}
       baseboot,basevalid=independent(y[ix],pred['base_refit'],classes,weights)
       with np.load(anchor/f'{split}_bootstrap.npz',allow_pickle=False) as z:
        for pol,probs in pred.items():
         modelpoint,_=point_metrics(y[ix],probs,classes);im,_=independent(y[ix],probs,classes,np.ones((1,len(ix))));imboot,vm=independent(y[ix],probs,classes,weights);assert np.array_equal(valid,vm)
         for metric in point:
          dist=imboot[metric]
          if pol!='base_refit':assert np.max(np.abs(z[pol+'__'+metric][valid]-(dist[valid]-baseboot[metric][valid])))<1e-12
          diff=dist[valid]-sampled[metric][valid];ci=np.quantile(diff,[.025,.975]);ic=np.quantile(imboot[metric][valid]-ib[metric][valid],[.025,.975]);assert np.max(np.abs(ci-ic))<1e-12;assert abs(im[metric][0]-modelpoint[metric])<1e-12
          contrasts.append(dict(task=task,split=split,seed=seed,layer=layer,policy=pol,control=name,metric=metric,difference=modelpoint[metric]-point[metric],ci_low=float(ci[0]),ci_high=float(ci[1]),valid=int(valid.sum()),invalid=int((~valid).sum())))
          if name=='composition':records.append(dict(task=task,split=split,seed=seed,readout=pol,layer=layer,policy=pol,metric=metric,value=modelpoint[metric]))
     write(unit/'COMPLETE.json',dict(status='COMPLETE',task=task,seed=seed,control=name,files={p.name:sha(p) for p in unit.iterdir() if p.is_file()}));units.append(str(unit));print('COMPLETE',task,seed,name,flush=True)
 for filename,values in [('metrics.csv',records),('contrasts.csv',contrasts)]:
  with (R/filename).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(values[0]),lineterminator='\n');w.writeheader();w.writerows(values)
 write(R/'SOURCE_ANCHORS.json',sources);write(R/'VERIFICATION.json',dict(status='PASS',scope='Separate pairwise/threshold metrics and all2000 draws, paired intervals, saved-head algebra and exact folds/row/class/group joins; no GPU regeneration',max_control_metric_or_draw_delta=maxdelta,units=len(units)))
 write(R/'EXECUTION.json',dict(status='COMPLETE',source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),source_sha256=sha(__file__),final_fits=len(units),wall_seconds=time.monotonic()-start,cpu_process_seconds=time.process_time()-cpu,threads=2,GPU_seconds=0))
if __name__=='__main__':
 with threadpool_limits(limits=2):run()
