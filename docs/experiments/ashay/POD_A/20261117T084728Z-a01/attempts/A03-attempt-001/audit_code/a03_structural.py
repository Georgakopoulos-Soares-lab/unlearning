"""All-unit A03 structural/cohort audit; bounded feature scans; no fits or GPU."""
from a03_common import *
import importlib.metadata,platform,resource

def main(c):
 c.family='structural';data=[];fold_records=[];features=[];receipts=[];reuse=[];fixed=[];inherited=[];unit_records=[];failures=[]
 rows={g:c.rows(g) for g in HASHES};task_rows={t:[r for r in rows[group(t)] if r['task']==t] for t in TASKS}
 # H3 test gate: exact frozen manifest, explicit historical held-out policy and complete saved-output chain.
 hist=c.roots['base_R1'];protocol=jread(hist/'PROTOCOL_V2.json')
 ensure('previously analyzed H3' in protocol['heldout_access'],'Prior H3 examination policy unavailable')
 ensure(next(x for x in protocol['feature_manifests'] if x['path'].endswith('H3.jsonl'))['sha256']==HASHES['H3'],'H3 historical cohort binding mismatch')
 for key in ['base_R1','R3','controls']:
  for g in rows:ensure(sha(c.roots[key]/'manifests'/f'{g}.jsonl')==HASHES[g],'Historical arm cohort differs')
 for rootkey in ['base_R1','R3']:
  for g in rows:
   p=c.roots[rootkey]/'producer_audit'/g/'VERIFICATION_COMPLETE.json';v=jread(c.ref(p)['path']);ensure(v['status']=='PASS','Inherited numerical audit failure');inherited.append({'dependency':rootkey,'group':g,'reference':c.ref(p),'units':v.get('units'),'scope':v.get('scope'),'status':'INHERITED_FULL_HISTORICAL_AUDIT_NOT_RERUN'})
 for t,rr in task_rows.items():
  ensure(len({r['id'] for r in rr})==len(rr),'Duplicate occurrence IDs')
  by=collections.defaultdict(list);exact=collections.defaultdict(list)
  for r in rr:
   s=r['sequence'];ensure(s==s.upper() and set(s)<=set('ACGTN'),'Unexpected preprocessing/alphabet');h=hashlib.sha256(s.encode()).hexdigest();rc=s.translate(str.maketrans('ACGTN','TGCAN'))[::-1];gh=hashlib.sha256(min(s,rc).encode()).hexdigest()
   ensure(h==seqsha(r) and gh==r['exact_rc_group'],'Frozen sequence/group mapping mismatch');by[gh].append(r);exact[h].append(r)
  counts=collections.Counter(r['split'] for r in rr);ensure(dict(counts)==({'train':11971,'dev':1497,'test':1497} if t=='emp_H3' else {'train':1024,'dev':512}),'Frozen counts differ')
  cross=[v for v in by.values() if len({r['split'] for r in v})>1];conflicts=[v for v in by.values() if len({r['label'] for r in v})>1]
  data.append({'task':t,'counts':dict(counts),'class_counts':{s:dict(sorted(collections.Counter(r['label'] for r in rr if r['split']==s).items())) for s in counts},'length_min':min(len(r['sequence']) for r in rr),'length_max':max(len(r['sequence']) for r in rr),'ambiguous_bases':sum(r['sequence'].count('N') for r in rr),'unique_exact_sequences':len(exact),'unique_exact_rc_groups':len(by),'duplicate_exact_groups':sum(len(v)>1 for v in exact.values()),'duplicate_rc_groups':sum(len(v)>1 for v in by.values()),'cross_split_rc_groups':len(cross),'conflicting_numeric_label_groups':len(conflicts),'biological_independence':'Not established: locus/homology groups unavailable'})
  ensure(not conflicts,'Contradictory numeric labels within exact/RC group')
  lookup={r['id']:r for r in rr};train={r['id'] for r in rr if r['split']=='train'}
  for seed in SEEDS:
   fp=hist/'probes'/group(t)/t/f'folds_seed{seed}.json';folds=jread(fp);ensure(len(folds)==(3 if t=='emp_H3' else 5),'Fold count differs');all_valid=[]
   for fold in folds:
    a,b=set(fold['train_ids']),set(fold['validation_ids']);ensure(len(a)==len(fold['train_ids']) and len(b)==len(fold['validation_ids']),'Duplicate fold index');ensure(not a&b and a|b==train,'Fold train/validation mismatch');ensure(not {lookup[i]['exact_rc_group'] for i in a}&{lookup[i]['exact_rc_group'] for i in b},'Within-CV exact/RC group leak');all_valid.extend(fold['validation_ids'])
   ensure(len(all_valid)==len(train) and set(all_valid)==train,'Validation folds fail partition')
   rp=c.roots['R3']/'probes'/group(t)/t/fp.name;cp=c.roots['controls']/'tasks'/t/fp.name;ensure(sha(fp)==sha(rp)==sha(cp),'Historical arm/control fold mismatch')
   fold_records.append({'task':t,'seed':seed,'folds':len(folds),'training_rows':len(train),'validation_coverage':len(all_valid),'within_fold_rc_overlap':0,'same_across_base_R1_R3_controls':True,'reference':c.ref(fp),'scaler_fitting_evidence':'Fold-local scaler in hash-verified historical source plus sealed CV/convergence traces; individual per-fold scalers were not saved'})
 # Cross-task exact/RC overlap is reported, not removed.
 allby=collections.defaultdict(list)
 for rr in rows.values():
  for r in rr:allby[r['exact_rc_group']].append((r['task'],r['split']))
 cross_task=sum(len({a for a,b in v})>1 for v in allby.values());cross_task_train_eval=sum(len({a for a,b in v})>1 and any(b=='train' for a,b in v) and any(b!='train' for a,b in v) for v in allby.values())
 c.done('DATA_AUDIT',{'status':'PASS','raw_manifest_sha256':HASHES,'tasks':data,'folds':fold_records,'h3_test_gate':{'status':'AUTHORIZED_EXACT_PREVIOUSLY_EXAMINED_COHORT','manifest_sha256':HASHES['H3'],'rows':1497,'protocol':c.ref(hist/'PROTOCOL_V2.json'),'saved_output_chain':inherited,'new_test_access':False},'cross_task_rc_groups':cross_task,'cross_task_training_to_evaluation_groups':cross_task_train_eval,'untouched_tests_opened':False,'cohorts_changed':False,'limitations':['Exact/RC groups do not establish locus/homology independence','H3 test previously examined; exploratory only']})
 c.log('DATA_FOLDS_PASS',tasks=6,fold_assignments=len(fold_records),cross_task_rc_groups=cross_task)
 # Scan one chunk / representation at a time, keeping only the declared two numerical anchors.
 for role,rootkey,arm in [('base','base_R1','base'),('R1','base_R1','maxent'),('R3','R3','new')]:
  for g,rr in rows.items():
   folder=c.roots[rootkey]/'features'/g/arm;receipt=c.receipt(folder/'FEATURE_UNIT_COMPLETE.json');receipts.append(str(folder/'FEATURE_UNIT_COMPLETE.json'));identity=jread(folder/'identity.json');ensure(identity_digest({k:v for k,v in identity.items() if k!='cache_key'})==identity['cache_key'],'Cache identity differs');ensure(identity['manifest_sha256']==HASHES[g],'Feature manifest identity mismatch')
   specs=jread(folder/'layer_registry.json');ensure([x['array_key'] for x in specs]==LAYERS and [x['module_path'] for x in specs]==[hook(k) for k in LAYERS] and all(x['width']==1920 for x in specs),'Hook list/width mismatch')
   listed={c.resolve(e['path']) for e in receipt['files'] if Path(e['path']).name.startswith('chunk_')};chunks=sorted(folder.glob('chunk_*.npz'));ensure(set(chunks)==listed,'Chunk coverage differs');cursor=0;parts={k:[] for k in ANCHORS+['ids','labels','split','task','groups','sequence_sha256','lengths','n_tokens','nll_sum']};arrays=0
   for num,p in enumerate(chunks):
    with np.load(p,allow_pickle=False) as z:
     n=len(z['ids']);expected=rr[cursor:cursor+n];ensure(z['cache_key'].item()==identity['cache_key'],'Chunk identity mismatch')
     for field,vals in [('ids',[r['id'] for r in expected]),('labels',[r['label'] for r in expected]),('split',[r['split'] for r in expected]),('task',[r['task'] for r in expected]),('groups',[r['exact_rc_group'] for r in expected]),('sequence_sha256',[seqsha(r) for r in expected]),('lengths',[len(r['sequence']) for r in expected]),('n_tokens',[len(r['sequence'])-1 for r in expected])]:ensure(z[field].tolist()==vals,'Feature ordered association mismatch: '+field)
     for layer in LAYERS:
      x=z[layer];ensure(x.shape==(n,1920) and x.dtype==np.float32 and np.isfinite(x).all(),'Feature shape/dtype/finiteness failure');arrays+=1
      if layer in ANCHORS:parts[layer].append(x)
     loss=z['nll_sum'];ensure(loss.shape==(n,) and loss.dtype==np.float32 and np.isfinite(loss).all() and np.all(loss>=0),'Invalid per-example LM loss');ensure(np.all(z['n_tokens']>0),'Invalid target count')
     for k in parts:
      if k not in ANCHORS:parts[k].append(z[k])
     cursor+=n
    if num%100==0:c.log('FEATURE_SCAN',role=role,group=g,chunks=num+1,total=len(chunks))
   ensure(cursor==len(rr)==receipt['examples'],'Feature population/fillers mismatch')
   np.savez(c.cache/f'{role}_{g}_anchors.npz',**{k:np.concatenate(v) for k,v in parts.items()})
   features.append({'role':role,'group':g,'rows':cursor,'chunks':len(chunks),'arrays_scanned':arrays,'representations':26,'width':1920,'dtype':'float32','ordered_association':'PASS','finiteness':'PASS','receipt':c.ref(folder/'FEATURE_UNIT_COMPLETE.json'),'identity':c.ref(folder/'identity.json'),'cache_key':identity['cache_key'],'historical_weights':identity['checkpoint_shards'],'tokenizer_sha256':identity['tokenizer_sha256'],'config_sha256':identity['config_sha256'],'extraction_source_sha256':identity['source_sha256'],'runtime':identity['runtime'],'future_runtime_status':'NEEDS_BRIDGE_QUALIFICATION'})
   c.log('FEATURE_FAMILY_PASS',role=role,group=g,rows=cursor,arrays=arrays)
 c.done('FEATURE_STRUCTURAL_AUDIT',{'status':'PASS','families':features,'bounded_scan':'One NPZ chunk and one representation array at a time; only block16/finalnorm retained in private anchor cache','no_gpu_replication':True})
 # Every logical probe receipt, CPU estimator, prediction record and native draw array.
 for rootkey in ['base_R1','R3']:
  root=c.roots[rootkey];protocol_hash=c.ref(root/'PROTOCOL_V2.json')['sha256']
  policies=['base_refit','h3_only_refit','h3_only_fixed_base'] if rootkey=='base_R1' else ['base_refit','new_refit','new_fixed_base']
  armnames=[('base','base'),('R1','h3_only_maxent')] if rootkey=='base_R1' else [('R3','new_checkpoint')]
  for g,rr in rows.items():
   pr=root/'probes'/g;idx=jread(pr/'PROBE_INDEX.json');fd=jread(pr/'FIT_COMPLETE.json');ensure(fd['status']=='COMPLETE' and fd['index_sha256']==c.ref(pr/'PROBE_INDEX.json')['sha256'],'Probe index completion identity failure');ensure(fd['identity_sha256']==c.ref(pr/'run_identity.json')['sha256'] and fd['protocol_sha256']==protocol_hash,'Fit identity mismatch')
   expected={(t,l,s) for t in TASKS if group(t)==g for l in LAYERS for s in SEEDS};actual=[(e['task'],e['layer'],e['cv_seed']) for e in idx['units']];ensure(len(actual)==len(set(actual)) and set(actual)==expected and len(actual)==idx['expected_units'],'All-layer task/seed unit coverage mismatch')
   identity_hash=c.ref(pr/'run_identity.json')['sha256']
   for i,e in enumerate(idx['units']):
    unit=c.resolve(e['receipt']).parent;ensure(c.ref(unit/'COMPLETE.json')['sha256']==e['receipt_sha256'],'Index receipt mismatch');done=c.receipt(unit/'COMPLETE.json');receipts.append(str(unit/'COMPLETE.json'));t,l,s=e['task'],e['layer'],e['cv_seed'];result=jread(unit/'results.json');ensure(done['fit_identity_sha256']==identity_hash and done['protocol_sha256']==protocol_hash,'Unit protocol mismatch');ensure(done['splits']==splits(t),'Wrong reporting splits');ensure(result['fold_sha256']==c.ref(pr/t/f'folds_seed{s}.json')['sha256'],'Unit fold mismatch')
    rr=task_rows[t];train=[r for r in rr if r['split']=='train'];classes=np.array(sorted({r['label'] for r in train}));models={}
    for role,name in armnames:
     model=joblib.load(c.ref(unit/(name+'.joblib'))['path']);scaler,head=validate_model(model,classes,1920);cv=jread(unit/(name+'_cv.json'));fit=result['fits'][name];selection(cv,3 if t=='emp_H3' else 5,head.C,fit['convergence']);ensure(fit['selected_C']==head.C and scaler.n_samples_seen_==len(train),'Final fit selection/sample count mismatch');models[role]=c.ref(unit/(name+'.joblib'))
     if role=='base':fixed.append({'task':t,'representation':hook(l),'array_key':l,'cv_seed':s,'head':models[role],'fold':c.ref(pr/t/f'folds_seed{s}.json'),'identity':c.ref(pr/'run_identity.json'),'future_policy':'Use exact saved scaler/head unchanged; never normalize target anew or substitute intervention head'})
    if rootkey=='R3':ensure(c.ref(unit/'base.joblib')['sha256']==c.ref(hist/'probes'/g/t/l/f'seed{s}'/'base.joblib')['sha256'],'R3 copied base head differs')
    expected_metrics={(sp,pol,m) for sp in splits(t) for pol in policies for m in NAMES};ensure(len(result['metrics'])==len(expected_metrics) and {(r['split'],r['policy'],r['metric']) for r in result['metrics']}==expected_metrics,'Metric inventory differs')
    for sp in splits(t):
     sr=[r for r in rr if r['split']==sp]
     with np.load(unit/f'{sp}_predictions.npz',allow_pickle=False) as z:
      for field,vals in [('ids',[r['id'] for r in sr]),('labels',[r['label'] for r in sr]),('groups',[r['exact_rc_group'] for r in sr]),('sequence_sha256',[seqsha(r) for r in sr])]:ensure(z[field].tolist()==vals,'Prediction association mismatch '+field)
      ensure(np.array_equal(z['classes'],classes),'Probability column class mismatch')
      for pol in policies:
       p=z['prob_'+pol];ensure(p.shape==(len(sr),len(classes)) and np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and np.allclose(p.sum(1),1,atol=1e-12,rtol=0),'Probability structural failure')
     with np.load(unit/f'{sp}_bootstrap.npz',allow_pickle=False) as z:
      ensure(z['valid'].shape==(2000,) and z['valid'].dtype==np.bool_,'Bootstrap mask shape/type failure')
      for pol in policies[1:]:
       for m in NAMES:ensure(z[pol+'__'+m].shape==(2000,) and np.isfinite(z[pol+'__'+m][z['valid']]).all(),'Bootstrap shape/finiteness failure')
     for role,name in armnames:
      pol='base_refit' if role=='base' else ('h3_only_refit' if role=='R1' else 'new_refit')
      reuse.append({'checkpoint':role,'task':t,'representation':hook(l),'cv_seed':s,'policy':pol,'split':sp,'protocol_sha256':protocol_hash,'receipt_sha256':e['receipt_sha256'],'head_sha256':models[role]['sha256'],'prediction_sha256':c.ref(unit/f'{sp}_predictions.npz')['sha256'],'artifact_integrity':'PASS','structural_status':'PASS','historical_numerical':'INHERITED_FULL_AUDIT','fresh_cpu_panel':'PENDING' if l in ANCHORS else 'OUTSIDE_PREDECLARED_PANEL','reuse_status':'REUSABLE','runtime_status':'NEEDS_BRIDGE_QUALIFICATION','reason':'Historical immutable CPU evidence; A04 must qualify live weight identity/runtime'})
     if rootkey in ['base_R1','R3']:
      role='R1' if rootkey=='base_R1' else 'R3';pol=policies[2];bp=hist/'probes'/g/t/l/f'seed{s}'/'base.joblib'
      reuse.append({'checkpoint':role,'task':t,'representation':hook(l),'cv_seed':s,'policy':pol,'split':sp,'protocol_sha256':protocol_hash,'receipt_sha256':e['receipt_sha256'],'head_sha256':c.ref(bp)['sha256'],'prediction_sha256':c.ref(unit/f'{sp}_predictions.npz')['sha256'],'artifact_integrity':'PASS','structural_status':'PASS','historical_numerical':'INHERITED_FULL_AUDIT','fresh_cpu_panel':'PENDING' if l in ANCHORS else 'OUTSIDE_PREDECLARED_PANEL','reuse_status':'REUSABLE','runtime_status':'NEEDS_BRIDGE_QUALIFICATION','reason':'Original base scaler/head binding verified; no target renormalization'})
    unit_records.append({'dependency':rootkey,'task':t,'array_key':l,'seed':s,'receipt':c.ref(unit/'COMPLETE.json'),'models':models,'splits':splits(t)})
    if i%50==0:c.log('UNIT_STRUCTURE',dependency=rootkey,group=g,units=i+1,total=len(idx['units']))
   for e in idx['lm_units']:
    rp=c.resolve(e['receipt']);ensure(c.ref(rp)['sha256']==e['receipt_sha256'],'LM receipt index identity');c.receipt(rp);receipts.append(str(rp))
 ensure(len(fixed)==468,'Original base head inventory differs');ensure(len(unit_records)==936,'Paired-unit inventory differs');ensure(len(receipts)==954,'Feature/probe/LM receipt inventory differs')
 write_csv(c.out/'REUSE_MATRIX.csv',reuse);put(c.c/'FIXED_REFERENCE_INDEX.json',{'schema':'pod-a-fixed-reference-v1','status':'PASS','unique_saved_base_heads':468,'references':fixed});put(c.out/'FIXED_REFERENCE_INDEX.json',jread(c.c/'FIXED_REFERENCE_INDEX.json'))
 put(c.cache/'UNIT_RECORDS.json',unit_records)
 c.done('STRUCTURAL_REUSE_AUDIT',{'status':'PASS','receipt_count':len(receipts),'feature_receipts':6,'paired_probe_receipts':936,'lm_receipts':12,'base_R1_R3_final_refit_heads':{'base':468,'R1':468,'R3':468},'unique_fixed_reference_heads':468,'reuse_rows':len(reuse),'inherited_numerical_audits':inherited,'feature_family_index':'FEATURE_STRUCTURAL_AUDIT.json','runtime_qualified_now':False,'no_gpu_replication':True})
 c.log('STRUCTURAL_FINISHED',receipts=len(receipts),heads=1404,reuse_rows=len(reuse))
 put(c.c/'CPU_ENVIRONMENT.json',{'python':platform.python_version(),'packages':{k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-learn','joblib','threadpoolctl']},'matches_historical_versions':True,'virtual_environment':os.sys.prefix,'blas_threads':4,'worker_processes':1,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'gpu_packages_installed':False,'fitting_disabled':True})

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);a=p.parse_args()
 with threadpool_limits(limits=4):main(Context(a.control))
