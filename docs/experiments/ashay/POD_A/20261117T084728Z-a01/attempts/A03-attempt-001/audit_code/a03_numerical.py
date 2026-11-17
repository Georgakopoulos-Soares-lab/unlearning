"""Predeclared saved-head/control/LM/bootstrap CPU recovery. Never fit estimators."""
from a03_common import *
import itertools,resource

def controls(sequences):
 words={''.join(k):i for i,k in enumerate(itertools.product('ACGT',repeat=4))};out={'composition':[],'4mer':[]}
 for seq in sequences:
  comp=np.array([seq.count(b) for b in 'ACGT'],dtype=float);kmer=np.zeros(256)
  for i in range(len(seq)-3):
   key=seq[i:i+4]
   if key in words:kmer[words[key]]+=1
  ensure(comp.sum()>0 and kmer.sum()>0,'Empty canonical control population');out['composition'].append(comp/comp.sum());out['4mer'].append(kmer/kmer.sum())
 return {k:np.array(v) for k,v in out.items()}

def math_check():
 from sklearn.metrics import roc_auc_score,average_precision_score,accuracy_score,balanced_accuracy_score,log_loss
 checked=0;residual=0.
 for classes,y,p in [(np.array([0,1]),np.array([0,1,0,1,0,1]),np.array([[.5,.5],[.2,.8],[.2,.8],[.8,.2],[1.,0.],[0.,1.]])),(np.array([0,1,2]),np.array([2,1,0,0,1,2]),np.array([[.2,.2,.6],[.2,.6,.2],[.6,.2,.2],[.4,.4,.2],[.2,.4,.4],[.2,.2,.6]]))]:
  w=np.array([[1,1,1,1,1,1],[2,1,3,2,1,2]],dtype=float);got,valid=metrics(y,p,classes,w)
  for i,wi in enumerate(w):
   pred=classes[(p[:,1]>=.5).astype(int)] if len(classes)==2 else classes[p.argmax(1)]
   truth={'accuracy':accuracy_score(y,pred,sample_weight=wi),'balanced_accuracy':balanced_accuracy_score(y,pred,sample_weight=wi),'classification_cross_entropy':log_loss(y,p,labels=classes,sample_weight=wi)}
   truth['auroc']=roc_auc_score(y,p[:,1],sample_weight=wi) if len(classes)==2 else roc_auc_score(y,p,labels=classes,multi_class='ovr',average='macro',sample_weight=wi)
   truth['average_precision']=average_precision_score(y,p[:,1],sample_weight=wi) if len(classes)==2 else np.mean([average_precision_score(y==k,p[:,j],sample_weight=wi) for j,k in enumerate(classes)])
   for m in truth:residual=max(residual,abs(float(got[m][i])-truth[m]));checked+=1
 ensure(residual<=1e-12,'Independent metric synthetic check failed');return {'status':'PASS','scalar_comparisons':checked,'max_residual':residual,'cases':'Binary/multiclass, tied scores, exact0/1 probabilities, weighted and unweighted; no fitting'}

def main(c):
 c.family='numerical';ensure(jread(c.c/'STRUCTURAL_REUSE_AUDIT.json')['status']=='PASS','Structural gate required');plan=jread(c.c/'NUMERICAL_RECOVERY_PLAN.json');plan_sha=sha(c.c/'NUMERICAL_RECOVERY_PLAN.json');math_result=math_check();c.log('MATH_CHECK_PASS',**math_result)
 arrays={};panel=[];control_records=[];lm=[];pairchecks=[];resampling_checks=[];failures=[];weights_cache={};heads=set();transfers=set();prob_rows=0
 def arr(role,g):
  key=(role,g)
  if key not in arrays:
   with np.load(c.cache/f'{role}_{g}_anchors.npz',allow_pickle=False) as z:arrays[key]={k:z[k] for k in z.files}
  return arrays[key]
 def task_ix(a,t,sp):return np.flatnonzero((a['task']==t)&(a['split']==sp))
 def unit(rootkey,t,l,s):return c.roots[rootkey]/'probes'/group(t)/t/l/f'seed{s}'
 def weights(t,sp):
  key=(t,sp)
  if key in weights_cache:return weights_cache[key]
  a=arr('base',group(t));ix=task_ix(a,t,sp);names=np.array(sorted(set(a['groups'][ix].tolist())));inv=np.array([{v:i for i,v in enumerate(names)}[v] for v in a['groups'][ix]])
  expected_draws=np.random.default_rng(20261103).integers(len(names),size=(2000,len(names)),dtype=np.int32)
  original=None
  for rootkey in ['base_R1','R3','controls']:
   p=(c.roots[rootkey]/'tasks'/t if rootkey=='controls' else c.roots[rootkey]/'probes'/group(t)/t)/f'{sp}_resampling.npz'
   with np.load(c.ref(p)['path'],allow_pickle=False) as z:
    ensure(np.array_equal(z['ids'],a['ids'][ix]) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inv),'Resampling population/order mismatch');d=z['group_draws'];ensure(d.shape==(2000,len(names)) and d.dtype==np.int32 and np.all((d>=0)&(d<len(names))) and np.array_equal(d,expected_draws),'Saved bootstrap RNG/shape/range mismatch')
    for k in ['ids','group_names','row_groups','group_draws']:
     if original is not None:ensure(np.array_equal(original[k],z[k]),'Arms/control resampling pairing mismatch')
    if original is None:original={k:z[k] for k in z.files}
   resampling_checks.append({'task':t,'split':sp,'dependency':rootkey,'reference':c.ref(p),'draws':2000,'groups':len(names),'rows':len(ix),'seed':20261103,'identity_replay':'PASS, saved draws used; replay only validates existing artifact'})
  w=np.stack([np.bincount(d,minlength=len(names)) for d in original['group_draws']]).astype(np.float64)[:,inv];weights_cache[key]=w;return w
 for t in TASKS:
  for sp in splits(t):weights(t,sp)
 c.done('PAIRING_POPULATION_CHECKS',{'status':'PASS','arrays':resampling_checks,'paired_group_population_count':len(weights_cache),'draws_per_population':2000,'new_draw_policy':False})
 # Metadata-selected 108 refits +72 fixed-reference transfers, with H3 split records counted separately.
 for role,rootkey,name,policy in [('base','base_R1','base','base_refit'),('R1','base_R1','h3_only_maxent','h3_only_refit'),('R3','R3','new_checkpoint','new_refit')]:
  for t in TASKS:
   a=arr(role,group(t));train=task_ix(a,t,'train');classes=np.unique(a['labels'][train])
   for l in ANCHORS:
    for s in SEEDS:
     u=unit(rootkey,t,l,s)
     try:
      model=joblib.load(c.ref(u/(name+'.joblib'))['path']);scaler,head=validate_model(model,classes,1920);mean=a[l][train].mean(0,dtype=np.float64);var=a[l][train].var(0,dtype=np.float64);ensure(np.allclose(scaler.mean_,mean,atol=1e-12,rtol=1e-10) and np.allclose(scaler.var_,var,atol=1e-12,rtol=1e-9),'Saved scaler differs from declared training-only population');ensure(scaler.n_samples_seen_==len(train),'Saved scaler sample count differs')
      result=jread(u/'results.json');policies=[(policy,model)]
      if role!='base':policies.append(('h3_only_fixed_base' if role=='R1' else 'new_fixed_base',joblib.load(c.ref(unit('base_R1',t,l,s)/'base.joblib')['path'])))
      for sp in splits(t):
       ix=task_ix(a,t,sp)
       with np.load(u/f'{sp}_predictions.npz',allow_pickle=False) as z:
        for pol,m in policies:
         pred=reconstruct(m,a[l][ix]);pd=maxerr(pred,z['prob_'+pol]);ensure(pd<=1e-10,'Saved-head probability reconstruction exceeds1e-10');got,valid=metrics(a['labels'][ix],pred,classes,np.ones((1,len(ix))));ensure(valid.all(),'Point metrics class support invalid');md=0.
         for metric in NAMES:
          saved=next(x['value'] for x in result['metrics'] if x['split']==sp and x['policy']==pol and x['metric']==metric);md=max(md,abs(float(got[metric][0])-saved))
         ensure(md<=1e-12,'Reconstructed-head scalar metric exceeds1e-12');guessed=classes[(pred[:,1]>=.5).astype(int)] if len(classes)==2 else classes[pred.argmax(1)];support=next(x for x in result['support'] if x['split']==sp and x['policy']==pol);conf=[[int(np.sum((a['labels'][ix]==aa)&(guessed==bb))) for bb in classes] for aa in classes];ensure(conf==support['confusion_counts'] and support['class_support']==[int(np.sum(a['labels'][ix]==k)) for k in classes],'Confusion/class support differs')
         panel.append({'role':role,'task':t,'representation':hook(l),'array_key':l,'seed':s,'split':sp,'policy':pol,'rows':len(ix),'status':'PASS','max_probability_residual':pd,'max_metric_residual':md,'scaler_mean_max_abs_residual':maxerr(scaler.mean_,mean),'scaler_variance_max_abs_residual':maxerr(scaler.var_,var),'head':c.ref((u/(name+'.joblib')) if pol==policy else unit('base_R1',t,l,s)/'base.joblib'),'saved_predictions':c.ref(u/f'{sp}_predictions.npz')});prob_rows+=len(ix)
         if pol==policy:heads.add((role,t,l,s))
         else:transfers.add((role,t,l,s))
     except Exception as e:failures.append({'family':'head_panel','role':role,'task':t,'layer':l,'seed':s,'exception':type(e).__name__,'reason':str(e)})
   c.log('HEAD_PANEL_TASK',role=role,task=t,heads=len(heads),transfers=len(transfers),failed=len(failures));put(c.cache/'NUMERICAL_PANEL_PROGRESS.json',{'panel':panel,'failures':failures,'heads':len(heads),'transfers':len(transfers)})
  # Keep arrays for LM/bootstrap; three roles two groups total <3GB, no all-layer matrices.
 # Controls are one fit per task/seed/definition, never multiplied by checkpoint/layer.
 metric_table=list(csv.DictReader((c.roots['controls']/'metrics.csv').open()))
 for t in TASKS:
  rr=[r for r in c.rows(group(t)) if r['task']==t];seq=[r['sequence'] for r in rr];computed=controls(seq);cp=c.roots['controls']/'tasks'/t
  with np.load(c.ref(cp/'features.npz')['path'],allow_pickle=False) as z:
   for field,vals in [('ids',[r['id'] for r in rr]),('labels',[r['label'] for r in rr]),('groups',[r['exact_rc_group'] for r in rr]),('sequence_sha256',[seqsha(r) for r in rr])]:ensure(z[field].tolist()==vals,'Control feature row association differs')
   for name in computed:ensure(np.array_equal(z[name],computed[name]),'Recomputed control feature definition differs')
  train=np.array([i for i,r in enumerate(rr) if r['split']=='train']);y=np.array([r['label'] for r in rr]);classes=np.unique(y[train])
  for name,x in computed.items():
   for s in SEEDS:
    u=cp/name/f'seed{s}'
    try:
     c.receipt(u/'COMPLETE.json');model=joblib.load(c.ref(u/'model.joblib')['path']);scaler,head=validate_model(model,classes,x.shape[1]);sel=jread(u/'selection.json');selection(sel['candidates'],3 if t=='emp_H3' else 5,head.C,sel['refit']);ensure(sel['selected_C']==head.C and sel['train_rows']==len(train)==scaler.n_samples_seen_,'Control selection support differs');ensure(np.allclose(scaler.mean_,x[train].mean(0),atol=1e-12,rtol=1e-10) and np.allclose(scaler.var_,x[train].var(0),atol=1e-12,rtol=1e-9),'Control scaler training statistics differ');records=[]
     for sp in splits(t):
      ix=np.array([i for i,r in enumerate(rr) if r['split']==sp]);p=reconstruct(model,x[ix])
      with np.load(u/f'{sp}_predictions.npz',allow_pickle=False) as z:
       ensure(np.array_equal(z['ids'],[rr[i]['id'] for i in ix]) and np.array_equal(z['labels'],y[ix]) and np.array_equal(z['classes'],classes) and np.array_equal(z['groups'],[rr[i]['exact_rc_group'] for i in ix]),'Control prediction row/class/group mismatch');pd=maxerr(p,z['probabilities']);ensure(pd<=1e-10,'Control probability reconstruction exceeds1e-10')
      got,valid=metrics(y[ix],p,classes,np.ones((1,len(ix))));md=0.
      for metric in NAMES:
       row=next(r for r in metric_table if r['task']==t and r['split']==sp and int(r['seed'])==s and r['readout']==name and r['metric']==metric);md=max(md,abs(float(got[metric][0])-float(row['value'])))
      ensure(md<=1e-12,'Control metric reconstruction exceeds1e-12');records.append({'split':sp,'rows':len(ix),'max_probability_residual':pd,'max_metric_residual':md,'predictions':c.ref(u/f'{sp}_predictions.npz')})
     control_records.append({'task':t,'control':name,'seed':s,'status':'PASS','feature_definition':'ACGT counts / canonical total' if name=='composition' else 'Normalized overlapping forward-strand ACGT4mers in lexicographic order; no RC aggregation','feature_width':x.shape[1],'feature_definition_recomputed_exactly':True,'feature_reference':c.ref(cp/'features.npz'),'receipt':c.ref(u/'COMPLETE.json'),'head':c.ref(u/'model.joblib'),'records':records})
    except Exception as e:failures.append({'family':'controls','task':t,'control':name,'seed':s,'exception':type(e).__name__,'reason':str(e)})
  c.log('CONTROLS_TASK',task=t,verified=len(control_records),failed=len(failures))
 c.done('CONTROL_REUSE_INDEX',{'status':'PASS' if len(control_records)==36 else 'PARTIAL','expected_units':36,'verified_units':len(control_records),'units':control_records,'fit_multiplication_by_model_or_layer':False,'inherited_draw_audit':c.ref(c.roots['controls']/'VERIFICATION.json')})
 # Exact saved-draw seed42 panel R3 minus R1 (nonadjacent, refit and fixed base), all specified task/splits.
 contrasts=list(csv.DictReader((c.roots['R3']/'reports/native_contrasts.csv').open()))
 for t in TASKS:
  for l in ANCHORS:
   for sp in splits(t):
    old=unit('base_R1',t,l,42);new=unit('R3',t,l,42);w=weights(t,sp)
    with np.load(old/f'{sp}_predictions.npz',allow_pickle=False) as o,np.load(new/f'{sp}_predictions.npz',allow_pickle=False) as n,np.load(old/f'{sp}_bootstrap.npz',allow_pickle=False) as ob,np.load(new/f'{sp}_bootstrap.npz',allow_pickle=False) as nb:
     for field in ['ids','labels','classes','groups','sequence_sha256']:ensure(np.array_equal(o[field],n[field]),'Contrast pairing row/label identity mismatch')
     ensure(np.array_equal(o['prob_base_refit'],n['prob_base_refit']),'Shared base predictions differ');ensure(np.array_equal(ob['valid'],nb['valid']),'Shared invalid bootstrap draws differ')
     for npol,opol in [('new_refit','h3_only_refit'),('new_fixed_base','h3_only_fixed_base')]:
      try:
       nm,nv=metrics(n['labels'],n['prob_'+npol],n['classes'],w);om,ov=metrics(o['labels'],o['prob_'+opol],o['classes'],w);ensure(np.array_equal(nv,ov) and np.array_equal(nv,nb['valid']),'Valid-class draw mask differs');path=c.roots['R3']/'paired_bootstrap'/group(t)/t/l/'seed42'/f'{sp}_{npol}_vs_h3.npz';draws=[]
       with np.load(c.ref(path)['path'],allow_pickle=False) as saved:
        ensure(np.array_equal(saved['valid'],nv),'Published paired valid mask differs')
        for metric in NAMES:
         direct=nm[metric]-om[metric];subtracted=nb[npol+'__'+metric]-ob[opol+'__'+metric];delta=max(maxerr(direct[nv],saved[metric][nv]),maxerr(direct[nv],subtracted[nv]));ci=np.quantile(direct[nv],[.025,.975]);point=float(metrics(n['labels'],n['prob_'+npol],n['classes'],np.ones((1,len(n['ids']))))[0][metric][0]-metrics(o['labels'],o['prob_'+opol],o['classes'],np.ones((1,len(o['ids']))))[0][metric][0]);row=next(r for r in contrasts if r['task']==t and r['layer']==l and int(r['cv_seed'])==42 and r['split']==sp and r['policy']==npol and r['metric']==metric and r['contrast']=='new_minus_h3_only');ci_delta=max(abs(ci[0]-float(row['ci_low'])),abs(ci[1]-float(row['ci_high'])));point_delta=abs(point-float(row['difference']));ensure(max(delta,ci_delta,point_delta)<=1e-12,'Paired draw/interval/point residual exceeds1e-12');draws.append({'metric':metric,'draw_max_residual':delta,'interval_max_residual':ci_delta,'point_residual':point_delta,'difference':point,'ci_low':float(ci[0]),'ci_high':float(ci[1]),'valid':int(nv.sum()),'invalid':int((~nv).sum())})
       pairchecks.append({'task':t,'representation':hook(l),'seed':42,'split':sp,'policy':npol,'status':'PASS','saved_draws':c.ref(path),'metrics':draws})
      except Exception as e:failures.append({'family':'paired_bootstrap','task':t,'layer':l,'split':sp,'policy':npol,'exception':type(e).__name__,'reason':str(e)})
    c.log('BOOTSTRAP_PANEL',task=t,layer=l,split=sp,verified=len(pairchecks),failed=len(failures));put(c.cache/'PAIR_PROGRESS.json',{'checks':pairchecks,'failures':failures})
 # All historical corpus LM aggregates and available native/paired intervals.
 lm_draws=[];lm_contrast_table=list(csv.DictReader((c.roots['R3']/'reports/LM_CONTRASTS.csv').open()))
 for t in TASKS:
  g=group(t);old=c.roots['base_R1']/'probes'/g/t;new=c.roots['R3']/'probes'/g/t;oldres=jread(old/'lm_metrics.json');newres=jread(new/'lm_metrics.json')
  for sp in splits(t):
   w=weights(t,sp);points={};drawvalues={};ix=task_ix(arr('base',g),t,sp)
   for role,name,source in [('base','base',oldres),('R1','h3_only_maxent',oldres),('R3','new_checkpoint',newres)]:
    a=arr(role,g);sums=a['nll_sum'][ix].astype(np.float64);counts=a['n_tokens'][ix].astype(np.float64);ensure(np.array_equal(a['ids'][ix],arr('base',g)['ids'][ix]) and np.all(counts>0),'LM row/count mismatch');nll=float(sums.sum(dtype=np.float64)/counts.sum(dtype=np.float64));ppl=float(np.exp(nll));ensure(np.isfinite(ppl),'LM perplexity overflow');point={'causal_nll':nll,'perplexity':ppl};record=next(r for r in source['metrics'] if r['split']==sp and r['arm']==name);delta=max(abs(point[m]-record[m]) for m in point);ensure(delta<=1e-12 and record['target_count']==int(counts.sum()),'LM aggregate/count residual exceeds1e-12');lm.append({'role':role,'task':t,'split':sp,'status':'PASS','examples':len(ix),'target_count':int(counts.sum()),'loss_sum_float64':float(sums.sum()),**point,'max_aggregate_residual':delta,'per_example_accumulation':'float32 archived; corpus sum/count float64','metrics_reference':c.ref((new if role=='R3' else old)/'lm_metrics.json')});points[role]=point;bnll=(w@sums)/(w@counts);drawvalues[role]={'causal_nll':bnll,'perplexity':np.exp(bnll)}
   for role,source,path in [('R1',oldres,old),('R3',newres,new)]:
    with np.load(path/f'{sp}_lm_bootstrap.npz',allow_pickle=False) as saved:
     for metric in ['causal_nll','perplexity']:
      diff=drawvalues[role][metric]-drawvalues['base'][metric];ci=np.quantile(diff,[.025,.975]);row=next(r for r in source['contrasts'] if r['split']==sp and r['metric']==metric);delta=max(maxerr(diff,saved[metric]),abs(ci[0]-row['ci_low']),abs(ci[1]-row['ci_high']),abs(points[role][metric]-points['base'][metric]-row['difference']));ensure(delta<=1e-12,'LM native paired residual exceeds1e-12');lm_draws.append({'contrast':role+'-base','task':t,'split':sp,'metric':metric,'draws':2000,'max_residual':delta,'status':'PASS'})
   for metric in ['causal_nll','perplexity']:
    diff=drawvalues['R3'][metric]-drawvalues['R1'][metric];ci=np.quantile(diff,[.025,.975]);row=next(r for r in lm_contrast_table if r['task']==t and r['split']==sp and r['metric']==metric and r.get('contrast')=='new_checkpoint_minus_h3_only');delta=max(abs(ci[0]-float(row['ci_low'])),abs(ci[1]-float(row['ci_high'])),abs(points['R3'][metric]-points['R1'][metric]-float(row['difference'])));ensure(delta<=1e-12,'LM R3-R1 paired interval residual exceeds1e-12');lm_draws.append({'contrast':'R3-R1 (nonadjacent)','task':t,'split':sp,'metric':metric,'draws':2000,'max_residual':delta,'status':'PASS'})
   c.log('LM_POPULATION',task=t,split=sp,aggregates=len(lm),intervals=len(lm_draws))
 # Reconcile the predeclared logical denominators; prediction records include H3 dev+test separately.
 ensure(len(heads)<=108 and len(transfers)<=72,'Unexpected panel units')
 summary={'status':'PASS' if not failures and len(heads)==108 and len(transfers)==72 and len(control_records)==36 and len(pairchecks)==28 and len(lm)==21 else 'PARTIAL','predeclared_plan_sha256':plan_sha,'tolerances':{'probabilities':1e-10,'metrics_and_bootstrap':1e-12},'expected_refitted_heads':108,'verified_refitted_heads':len(heads),'expected_fixed_base_target_head_combinations':72,'verified_fixed_base_combinations':len(transfers),'head_prediction_records':len(panel),'head_probability_rows':prob_rows,'control_logical_units':len(control_records),'control_prediction_records':sum(len(r['records']) for r in control_records),'paired_R3_minus_R1_policy_panels':len(pairchecks),'paired_scalar_metric_intervals':sum(len(r['metrics']) for r in pairchecks),'lm_aggregates':lm,'lm_intervals':lm_draws,'fresh_head_panel':panel,'failures':failures,'max_probability_residual':max([r['max_probability_residual'] for r in panel]+[z['max_probability_residual'] for r in control_records for z in r['records']],default=0.),'max_metric_residual':max([r['max_metric_residual'] for r in panel]+[z['max_metric_residual'] for r in control_records for z in r['records']],default=0.),'max_bootstrap_residual':max([r['draw_max_residual'] for x in pairchecks for r in x['metrics']]+[r['max_residual'] for r in lm_draws],default=0.),'synthetic_math_check':math_result,'math_helper_sha256':sha(Path(__file__).with_name('historical_independent_math.py')),'all_byte_and_all_unit_structural_coverage':'Separate RESTORE_VALIDATION/STRUCTURAL_REUSE_AUDIT; numerical reconstruction here is the predeclared panel','outside_panel':'Inherited hash-bound original full numerical audits; no all-head re-fit or GPU replication','new_model_measurements':0,'new_probe_fits':0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
 c.done('PAIRING_AND_UNCERTAINTY_AUDIT',{'status':'PASS' if len(pairchecks)==28 and not any(f['family']=='paired_bootstrap' for f in failures) else 'PARTIAL','resampling_checks':resampling_checks,'paired_panels':pairchecks,'lm_paired_checks':lm_draws,'interpretation':'2000 paired exact/RC-group draws, seed20261103; pointwise exploratory conditional on fitted heads; not homology groups; R3-R1 nonadjacent; CV seeds are not checkpoint replicates','new_R4_R5_R6_contrasts':0,'control_bootstrap_scope':'All original36 controls have inherited full draw audits, fresh probability/point-metric checks; resampling identity freshly validated'})
 c.done('NUMERICAL_RECOVERY_CHECKS',summary);c.log('NUMERICAL_FINISHED',status=summary['status'],heads=len(heads),transfers=len(transfers),controls=len(control_records),paired=len(pairchecks),lm=len(lm),failures=len(failures))

def seqsha(r):return hashlib.sha256(r['sequence'].encode()).hexdigest()
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);a=p.parse_args()
 with threadpool_limits(limits=4):main(Context(a.control))
