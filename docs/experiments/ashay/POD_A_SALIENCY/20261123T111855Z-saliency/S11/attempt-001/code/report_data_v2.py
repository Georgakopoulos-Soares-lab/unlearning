"""Deterministic reporting projection of already released records; no estimators or new contrasts."""
from pathlib import Path
import json,csv,hashlib,collections,itertools,sys
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']
REPS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];SEEDS=[42,17,1234];POLICIES=['independent_refit','fixed_original_base'];METRICS=['AUROC','AP','accuracy','balanced_accuracy','cross_entropy']
LABELS=dict(zip(TASKS,['EMP H3','GUE TF 0','GUE promoter core','GUE promoter 300','GUE splice reconstructed','GUE mouse 0']))
PKG='7007ebd05bf59432bf69109e5f69baad31ec0d3a';PROTO='417707c70843eecf0183f367d503800baee3569db10626fa0362186505c89b22';C9='3c39552d43c2e4c8aaf223ca97e3b8f6ee33d11c';C10='735c9de0ed56be285897b68f84db098ff7a32a6f'
def read(p):return json.loads(Path(p).read_text())
def rows(p):
 with Path(p).open() as f:return [json.loads(l) for l in f if l.strip()]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.partial');tmp.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def jl(p,rs):
 p.parent.mkdir(parents=True,exist_ok=True)
 payload=''.join(json.dumps(r,separators=(',',':'),allow_nan=False)+'\n' for r in rs)
 if p.exists():assert p.read_text()==payload,'Completed reporting projection changed unexpectedly';return
 p.write_text(payload)
def build(root,out):
 root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True);s9=root/'inputs/s09';s10=root/'inputs/s10';candidates=read(s10/'S11_HANDOFF.json')['candidate_bindings'];cs={c['alias']:c for c in candidates};assert len(cs)==9
 raw=rows(s9/'LAYER_PROFILES.jsonl');keys=[(r['candidate'],r['task'],r['representation'],r['seed'],r['policy'],r['metric']) for r in raw];expected=set(itertools.product(cs,TASKS,REPS,SEEDS,POLICIES,METRICS));assert len(keys)==len(set(keys))==42120 and set(keys)==expected
 prediction_paths={k[:-1] for k in keys};assert len(prediction_paths)==8424;heads={k[:-1] for k in prediction_paths if k[-1]=='independent_refit'};fixed={k[:-1] for k in prediction_paths if k[-1]=='fixed_original_base'};assert len(heads)==len(fixed)==4212
 for t in TASKS:
  data=[]
  for line,r in enumerate(raw,1):
   if r['task']!=t:continue
   c=cs[r['candidate']];assert r['split']=='dev' and r['class_order']==([0,1,2] if t=='gue_splice_reconstructed' else [0,1]);assert r['sample_count']==(1497 if t=='emp_H3' else 512) and r['group_count']==(511 if t=='gue_splice_reconstructed' else r['sample_count'])
   data.append({**r,'candidate_id':c['candidate_id'],'checkpoint_content_sha256':c['content_sha256'],'checkpoint_step':c['step'],'checkpoint_declared_label':c['label'],'task_display_label':LABELS[t],'scientific_protocol_sha256':PROTO,'source_release_commit':C9,'source_table':'S09/attempt-001/LAYER_PROFILES.jsonl','source_line':line,'units':'nats_per_example' if r['metric']=='cross_entropy' else 'unitless','interval_scope':'95% pointwise exploratory conditional on fitted heads; no multiplicity adjustment'})
  jl(out/'tables'/('CLASSIFICATION_'+t+'.jsonl'),data)
 contrast=[]
 for p in sorted((s9/'contrasts').glob('*/*/CONTRASTS.jsonl')):
  for line,r in enumerate(rows(p),1):
   assert r['status']=='VERIFIED' and r['split']=='dev' and r['bootstrap_attempted']==2000 and r['bootstrap_valid']+r['bootstrap_invalid']==2000
   assert abs((r['target_estimate']-r['reference_estimate'])-r['estimate'])<=1e-12
   contrast.append({**{k:r[k] for k in ['id','c','t','r','s','p','m','f','q','d','split','estimate','ci_low','ci_high','target_estimate','reference_estimate','reference_label','favorable_sign','bootstrap_attempted','bootstrap_valid','bootstrap_invalid','cohort_sha256','draw_sha256','common_mask_sha256','sample_count','group_count','paired_vector_sha256','target_endpoint_sha256','reference_endpoint_sha256','uncertainty','missing_reason','status']},'checkpoint_content_sha256':cs[r['c']]['content_sha256'],'checkpoint_step':cs[r['c']]['step'],'scientific_protocol_sha256':PROTO,'source_release_commit':C9,'source_table':'S09/attempt-001/'+str(p.relative_to(s9)),'source_line':line,'direction':'target_minus_reference'})
 assert len(contrast)==len({r['id'] for r in contrast})==48924;frozen=rows(s9/'FROZEN_ADMITTED_KEYS.jsonl');assert {r['id'] for r in frozen}=={r['id'] for r in contrast};deferred=rows(s9/'FROZEN_DEFERRED_KEYS.jsonl');assert len(deferred)==len({r['id'] for r in deferred})==42228
 for t in TASKS:jl(out/'tables'/('CONTRASTS_'+t+'.jsonl'),[r for r in contrast if r['t']==t])
 lm=rows(s9/'LM_MARGINALS_REUSED.jsonl');assert len(lm)==216 and len({r['canonical_metric']['unit_id'] for r in lm})==108 and all(r['release_status']=='VERIFIED' and r['representation'] is None and r['cv_seed'] is None for r in lm)
 split_units={sp:len({r['canonical_metric']['unit_id'] for r in lm if r['split']==sp}) for sp in ['train','dev']};assert split_units=={'train':54,'dev':54};jl(out/'tables/LM_RELEASED.jsonl',lm)
 auroc={(r['candidate'],r['task'],r['representation'],r['seed'],r['policy']):r for r in raw if r['metric']=='AUROC'};anchor=[];above=[]
 for c,t,s in itertools.product(cs,TASKS,SEEDS):
  a=auroc[c,t,'decoder.layers.16',s,'independent_refit'];b=auroc[c,t,'decoder.final_norm',s,'independent_refit'];row={'candidate':c,'task':t,'seed':s,'block16_endpoint':a['endpoint_id'],'finalnorm_endpoint':b['endpoint_id'],'block16_AUROC':a['estimate'],'finalnorm_AUROC':b['estimate'],'difference_descriptive_only':a['estimate']-b['estimate'],'inferential_interval':None,'no_new_layer_to_layer_inference':True};anchor.append(row)
  if a['estimate']>b['estimate']:above.append(row)
 jl(out/'tables/ANCHOR_LAYER_DESCRIPTIVE.jsonl',anchor)
 gaps=[r for r in contrast if r['f']=='anchor_policy_gap'];assert len(gaps)==324;gapcounts={'positive':sum(r['estimate']>0 for r in gaps),'negative':sum(r['estimate']<0 for r in gaps),'equal':sum(r['estimate']==0 for r in gaps),'CI_includes_zero':sum(r['ci_low']<=0<=r['ci_high'] for r in gaps)}
 bymetric=collections.Counter(r['f'] for r in contrast);assert dict(bymetric)=={'base_reference':42120,'DNA_control':6480,'anchor_policy_gap':324}
 base=[r for r in contrast if r['f']=='base_reference'];summary=[]
 for t,p,m in itertools.product(TASKS,POLICIES,METRICS):
  ss=[r for r in base if (r['t'],r['p'],r['m'])==(t,p,m)];assert len(ss)==702
  summary.append({'task':t,'policy':p,'metric':m,'n':len(ss),'point_above':sum(r['estimate']>0 for r in ss),'point_below':sum(r['estimate']<0 for r in ss),'point_equal':sum(r['estimate']==0 for r in ss),'CI_above_zero':sum(r['ci_low']>0 for r in ss),'CI_below_zero':sum(r['ci_high']<0 for r in ss),'CI_includes_zero':sum(r['ci_low']<=0<=r['ci_high'] for r in ss),'source_ids':[r['id'] for r in ss]})
 jl(out/'tables/BASE_COMPARISON_SUMMARY.jsonl',summary)
 ranges=[]
 for t,p,rep in itertools.product(TASKS,POLICIES,['decoder.layers.16','decoder.final_norm']):
  ss=[r for r in raw if (r['task'],r['policy'],r['representation'],r['metric'])==(t,p,rep,'AUROC')];ranges.append({'task':t,'policy':p,'representation':rep,'n':len(ss),'min':min(r['estimate'] for r in ss),'max':max(r['estimate'] for r in ss),'source_ids':[r['endpoint_id'] for r in ss],'range_is_not_CI':True})
 jl(out/'tables/ANCHOR_RANGES.jsonl',ranges)
 lm_ranges=[]
 for t,m in itertools.product(TASKS,['LM_NLL','LM_PPL']):
  ss=[r for r in lm if r['task']==t and r['split']=='dev' and r['canonical_metric']['metric']==m];assert len(ss)==9;lm_ranges.append({'task':t,'metric':m,'n':9,'min':min(r['canonical_metric']['estimate'] for r in ss),'max':max(r['canonical_metric']['estimate'] for r in ss),'source_ids':[r['source_row_id'] for r in ss]})
 jl(out/'tables/LM_DEV_RANGES.jsonl',lm_ranges)
 pairgroups=collections.defaultdict(dict)
 for r in base:pairgroups[r['c'],r['t'],r['r'],r['s'],r['p']][r['m']]=r
 disagreement=[{'key':list(k),'AUROC_id':v['AUROC']['id'],'CE_id':v['cross_entropy']['id'],'AUROC_delta':v['AUROC']['estimate'],'CE_delta':v['cross_entropy']['estimate']} for k,v in pairgroups.items() if v['AUROC']['estimate']>0 and v['cross_entropy']['estimate']>0];jl(out/'tables/RANKING_LOSS_DISAGREEMENT.jsonl',disagreement)
 fc=read(s10/'COVERAGE.json');assert fc['sources']==9 and fc['source_bytes']==418914867 and fc['complete_events']==4069391 and fc['scalar_observations_all_tags_axes']==4069382 and fc['training_forget_step_observations']==14090 and fc['validation_forget_loss_step_observations']==23 and fc['forget_validation_loss_and_ppl_both_axes_records']==92 and fc['qualified_descriptive_scientific_aggregates']==fc['qualified_checkpoint_matched_comparisons']==fc['layerwise_forget_performance_observations']==0
 frows=list(csv.DictReader((s10/'FORGET_VALIDATION_OBSERVATIONS.csv').open()));duplicate=[r for r in frows if r['tag']=='forget loss validation' and r['source_id']=='16ABtYkg71z8I2gyZvl48RSaRqYJ1mNXu' and r['step']=='1500'];assert [r['value'] for r in duplicate]==['1.3953843116760254','1.3952388763427734'];(out/'tables/FORGET_VALIDATION_OBSERVATIONS.csv').write_bytes((s10/'FORGET_VALIDATION_OBSERVATIONS.csv').read_bytes())
 findings=[]
 def claim(cid,question,observation,value,ids,scope,uncertainty,limit,table):findings.append({'claim_id':cid,'question':question,'observation':observation,'value':value,'source_ids':ids,'scope':scope,'uncertainty':uncertainty,'interpretation_limit':limit,'table':table})
 claim('policy_gap','How do the readouts differ?','Anchor refitted AUROC minus unchanged-base AUROC',{'n':324,**gapcounts,'min':min(r['estimate'] for r in gaps),'max':max(r['estimate'] for r in gaps)},[r['id'] for r in gaps],'9candidate x6task x2anchor x3CVseed; DEV AUROC; point differences refit minus fixed','Existing paired95% pointwise conditional intervals','Dependent records, not intervention replications; no causal attribution','tables/CONTRASTS_*.jsonl')
 claim('anchor_layer','Where are differences visible?','Refitted block16 AUROC exceeds finalnorm descriptively',{'above':len(above),'n':len(anchor)},[r['block16_endpoint'] for r in anchor]+[r['finalnorm_endpoint'] for r in anchor],'9candidate x6task x3CVseed; refitted DEV AUROC','No new inferential layer comparison or layer-difference CI','Block16 is seventeenth decoder block; no optimal-layer claim','tables/ANCHOR_LAYER_DESCRIPTIVE.jsonl')
 claim('ranking_loss','Do measurements agree?','AUROC above base while classifierCE is worse',{'n':len(disagreement),'eligible_prediction_cells':len(pairgroups)},[x for r in disagreement for x in [r['AUROC_id'],r['CE_id']]],'All9candidate/6task/26representation/3seed/2policy DEV cells','Point-direction descriptive conjunction; do not infer joint significance','Ranking and probability loss answer different questions; count is not capability fraction','tables/RANKING_LOSS_DISAGREEMENT.jsonl')
 for t in ['emp_H3','gue_splice_reconstructed']:
  for p in POLICIES:
   r=next(r for r in base if (r['c'],r['t'],r['r'],r['s'],r['p'],r['m'])==('candidate_01',t,'decoder.layers.16',42,p,'AUROC'))
   claim('example_'+t+'_'+p,'What differs from original base?', 'candidate01 block16 seed42 AUROC target minus original base',{'estimate':r['estimate'],'ci_low':r['ci_low'],'ci_high':r['ci_high'],'target':r['target_estimate'],'reference':r['reference_estimate']},[r['id']],'DEV '+t+'; '+p+'; candidate01; decoder.layers.16; seed42','Existing paired95% pointwise conditional interval','Fixed question-based examples H3 primary and splice multiclass; original base is not proven immediate parent','tables/CONTRASTS_'+t+'.jsonl')
 claim('source_forget','What forget evidence exists?', 'Source logs recovered; qualification pending',{'source_files':9,'primary_validation':23,'qualified_scientific_aggregates':0,'matched_comparisons':0,'qualified_layerwise':0},[r['observation_id'] for r in frows if r['tag']=='forget loss validation'],'Exact original tags, source/event IDs; source-only quotations','No uncertainty manufactured','No content/invocation/cohort/metric-semantic binding; duplicates and alternate axes not independent replicates','tables/FORGET_VALIDATION_OBSERVATIONS.csv')
 jl(out/'CLAIM_LEDGER.jsonl',findings)
 facts={'schema_version':'s11-reporting-facts-v1','source_releases':{'S09':C9,'corrected_S10':C10},'canonical_package':PKG,'scientific_protocol_sha256':PROTO,'candidates':candidates,'tasks':[{'id':t,'label':LABELS[t]} for t in TASKS],'representations':REPS,'seeds':SEEDS,'policies':POLICIES,'metric_names':METRICS,'coverage':{'candidates':9,'tasks':6,'representations':26,'CV_seeds':3,'policies':2,'refitted_heads':len(heads),'unchanged_base_applications':len(fixed),'prediction_paths':len(prediction_paths),'classifier_metric_records':len(raw),'LM_units':108,'LM_DEV_primary_units':split_units['dev'],'LM_TRAIN_diagnostic_units':split_units['train'],'LM_metric_records':216,'admitted_S09_contrasts':len(contrast),'deferred_S09_specifications':len(deferred),'contrast_families':dict(bymetric),'deferred_families':dict(collections.Counter(r['f'] for r in deferred))},'policy_gap':findings[0]['value'],'anchor_layer':findings[1]['value'],'ranking_loss':findings[2]['value'],'anchor_ranges':ranges,'LM_DEV_ranges':lm_ranges,'seed_sensitivity_source':read(s9/'SEED_SENSITIVITY.json'),'forget_source_counts':fc,'reinit5_duplicate_original_values':[r['value'] for r in duplicate],'findings':findings,'FORGET_SCIENTIFIC_STATUS':'EXTRACTION_ONLY_PENDING_QUALIFICATION','LAYERWISE_FORGET_STATUS':'PENDING_QUALIFIED_LAYERWISE_PERFORMANCE','ORIGINAL_RETAIN_AND_FORGET_REQUEST':'PARTIAL','new_inference_fits_draws_or_tests':0};save(out/'REPORTING_FACTS.json',facts);save(out/'COVERAGE_FINAL.json',{'status':'EXPECTED_KEYS_RECONCILED','coverage':facts['coverage'],'forget_source':fc,'scientific_scope':'Verified layerwise retain evaluation; unqualified source-log forget evidence; original combined request remains PARTIAL','missing_full_forget_protocol_denominator':None,'no_completion_percentage':True})
 index=[]
 for p in sorted((out/'tables').glob('*')):index.append({'path':str(p.relative_to(out)),'bytes':p.stat().st_size,'sha256':sha(p),'precision':'Full original values; no display rounding','source_releases':[C9,C10]})
 save(out/'TABLE_INDEX.json',{'schema_version':'s11-table-index-v1','tables':index,'full_source_contrasts_and_deferred_keys':'Immutable S09/attempt-001 source files identified in INPUT_MANIFEST.json; no new tests or activation of deferred specifications','no_raw_examples_or_probabilities_in_public_tables':True});return facts
if __name__=='__main__':f=build(sys.argv[1],sys.argv[2]);print(json.dumps({'coverage':f['coverage'],'policy_gap':f['policy_gap'],'anchor':f['anchor_layer'],'ranking_loss':f['ranking_loss']}),flush=True)
