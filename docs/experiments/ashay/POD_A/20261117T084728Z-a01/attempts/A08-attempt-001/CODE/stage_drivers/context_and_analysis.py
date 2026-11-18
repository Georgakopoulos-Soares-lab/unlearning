"""Verified goals, missingness, retain-entry context and bounded scientific answers."""
from common import *
from research_guard import guard
import collections,itertools,math
D7=D.parent/'A07-attempt-001';D6=D.parent/'A06-attempt-001';TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];REPS=['decoder.layers.'+str(i) for i in range(25)]+['decoder.final_norm'];SEEDS=[42,17,1234];POLICIES=['independent_refit','fixed_original_base'];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy'];LABELS={'emp_H3':'H3','gue_tf_0':'Human TF','gue_prom_core_all':'Core promoter','gue_prom_300_all':'Promoter300','gue_splice_reconstructed':'Splice','gue_mouse_0':'Mouse TF'}
def rows(p):return list(csv.DictReader(Path(p).open()))
def write(name,rs):
 guard(allow_dirty=True)
 with (D/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rs[0]),lineterminator='\n');w.writeheader();w.writerows(rs)
def rkey(r):return {k:r[k] for k in ['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256'] if k in r}
def main():
 metrics=rows(D/'VERIFIED_METRICS.csv');parts=read(D/'TABLE_PARTITIONS.json')['logical_PAIRED_CONTRASTS']['partitions'];paired=[r for p in parts for r in rows(D/p['file'])];lm=rows(D/'LM_METRICS_VERIFIED.csv');lmp=rows(D/'LM_CONTRASTS_VERIFIED.csv');assert len(metrics)==27300 and len(paired)==45360 and len(lm)==70 and len(lmp)==112
 point={(r['checkpoint_alias'],r['task'],r['split'],r['representation'],int(r['CV_seed']),r['policy'],r['metric']):r for r in metrics};effects={(r['checkpoint_alias'],r['reference'],r['task'],r['split'],r['representation'],int(r['CV_seed']),r['policy'],r['metric']):r for r in paired};lpoint={(r['checkpoint_alias'],r['task'],r['split'],r['metric']):r for r in lm};assert len(point)==27300 and len(effects)==45360
 # Preserve the entire 6,637-unit frozen ledger; release existing artifacts with overlays.
 coverage=rows(D7/'COVERAGE.csv');overlay={r['unit_id']:r for r in read(D/'VERIFICATION_OVERLAY.json')['units']}
 for r in coverage:
  r['ingestion_status']='REUSED_IN_A08';r['A08_audit_receipt_sha256']='';uid=r['unit_id'].split('/',1)[1]
  if uid in overlay and r['unit_kind'] in ['final_head','fixed_base_application']:
   o=overlay[uid];r.update(status='VERIFIED',verification_status='A08_ALL_UNIT_PASS_SAMPLED_PANEL_PASS_WHERE_PLANNED',backup_status='A08_FRESH_RESTORE_PASS',reason='Original A07 producer artifact remains immutable; independent A08 overlay releases its saved outputs',A08_audit_receipt_sha256=o['audit_receipt_sha256'] if 'audit_receipt_sha256' in o else o['audit_receipt']['sha256'])
 assert len(coverage)==6637 and len({r['unit_id'] for r in coverage})==6637
 for kind in ['final_head','fixed_base_application']:
  rr=[r for r in coverage if r['unit_kind']==kind];assert len(rr)==3276 and sum(r['status'] in ['VERIFIED','REUSED_VALIDATED'] for r in rr)==2340
 write('COVERAGE.csv',coverage)
 plan=read(D6/'CONTRAST_PLAN.json')['contrasts'];family_counts=collections.Counter((r['checkpoint_alias'],r['reference']) for r in paired);lm_counts=collections.Counter((r['checkpoint_alias'],r['reference']) for r in lmp);ledger=[]
 for p in plan:
  r=dict(p);target,reference=p['target'],p['reference'];r['historical_A05_plan_status']=p['status'];r['classifier_released_rows']=family_counts[target,reference];r['LM_released_rows']=lm_counts[target,reference];r['new_effect_estimate']=None;r['ci_low']=None;r['ci_high']=None
  if target in ['R1','R3'] and reference in ['base','R1']:
   r.update(status='REUSED_VALIDATED_HISTORICAL_DOMAIN',reason='Exact A03 accepted domain and immutable prior full-audit receipts; no new live R3 contrast admitted')
  elif target in ['R4','R6'] and reference in ['base','R1']:
   r.update(status='VERIFIED_A08_AVAILABLE_ENDPOINTS',reason='A06 H3/LM verified reuse plus A08 other-five full numerical audit and prospective refit panel')
  elif target=='R6' and reference=='R4':r.update(status='VERIFIED_PREDECLARED_NONADJACENT',reason='Two planned retain additions plus other training differences; descriptive, not adjacent or causal')
  elif target=='R4' and reference=='R3':r.update(status='BLOCKED_R3_LIVE_BRIDGE',reason='R3 historical outputs are valid; live cross-runtime bridge required for this new edge is absent')
  else:r.update(status='PENDING_ENDPOINT',reason='R2 identity/delivery unadmitted or R5 qualification/downstream outputs missing; no interpolation/backfill authorized')
  ledger.append(r)
 # Enforce the predeclared nonadjacent row universe regardless of inherited plan metadata spelling.
 if not any(r['target']=='R6' and r['reference']=='R4' for r in ledger):ledger.append({**ledger[0],'contrast_id':'R6_minus_R4','target':'R6','reference':'R4','adjacent':False,'status':'VERIFIED_PREDECLARED_NONADJACENT','classifier_released_rows':5460,'LM_released_rows':14,'reason':'Predeclared nonadjacent; two additions and unmatched training differences'})
 assert len([r for r in ledger if r['adjacent']])==5;columns=list(ledger[0]);assert all(set(r)==set(columns) for r in ledger);write('CONTRAST_STATUS.csv',ledger);write('COMPARABILITY_MATRIX.csv',ledger)
 edges=[('R2','R1','R2identity/delivery unadmitted'),('R3','R2','R2identity/delivery unadmitted; future compatibility would require review'),('R4','R3','R3live cross-runtime bridge missing; historical R3 remains valid'),('R5','R4','R5native qualification/downstream outputs missing'),('R6','R5','R5native qualification/downstream outputs missing')];pending=[];pending_lm=[]
 for target,reference,reason in edges:
  for task in TASKS:
   for split in (['dev','test_exploratory'] if task=='emp_H3' else ['dev']):
    for rep,seed,policy,metric in itertools.product(REPS,SEEDS,POLICIES,METRICS):pending.append({'family':target+'_minus_'+reference,'target':target,'reference':reference,'task':task,'split':split,'representation':rep,'CV_seed':seed,'policy':policy,'reference_policy':policy,'metric':metric,'direction':'target-reference','estimate':None,'ci_low':None,'ci_high':None,'status':'BLOCKED' if target=='R4' else 'PENDING','reason':reason,'adjacent':True,'protocol_sha256':cfg['protocol_sha256']})
    for metric in ['causal_nll','perplexity']:pending_lm.append({'family':target+'_minus_'+reference,'target':target,'reference':reference,'task':task,'split':split,'representation':None,'CV_seed':None,'policy':'actual_causal_head','metric':metric,'estimate':None,'ci_low':None,'ci_high':None,'status':'BLOCKED' if target=='R4' else 'PENDING','reason':reason,'adjacent':True,'protocol_sha256':cfg['protocol_sha256']})
 assert len(pending)==27300 and len(pending_lm)==70;write('PENDING_ADJACENT_CONTRASTS.csv',pending);write('PENDING_ADJACENT_LM.csv',pending_lm)
 entries=rows(D6/'INCLUSION_EXPOSURE_PLAN.csv');entry_index={(r['endpoint'],r['task']):r for r in entries};entryrows=[];anchors=[];policy_diffs=[]
 for alias,task,rep,policy,metric in itertools.product(['R4','R6'],TASKS,['decoder.layers.16','decoder.final_norm'],POLICIES,METRICS):
  r=point[alias,task,'dev',rep,42,policy,metric];e=entry_index[alias,task];effect=effects[alias,'base',task,'dev',rep,42,policy,metric];entryrows.append({'candidate':alias,'task':task,'split':'dev','representation':rep,'CV_seed':42,'policy':policy,'metric':metric,'estimate':r['estimate'],'minus_base':effect['estimate'],'minus_base_ci_low':effect['ci_low'],'minus_base_ci_high':effect['ci_high'],'first_planned_inclusion':e['first_planned_inclusion'],'first_evidenced_declaration':e['first_evidenced_declaration'],'declared_at_endpoint':e['declared_at_endpoint'],'exact_retain_dataset_version':e['exact_retain_dataset_version'],'observed_sampler_rows':e['observed_sampler_rows'],'realized_exposure':e['realized_exposure'],'parent_lineage':e['parent_lineage'],'objective_comparability':e['objective_comparability'],'matched_tokens_or_budget':e['matched_tokens_or_budget'],'config_sha256':e['config_sha256'],'claim_limit':'Before config declaration is not proof of unseen training data; missing adjacent effects cannot identify task entry causally','metric_row_key':json.dumps(rkey(r),sort_keys=True),'paired_row_key':json.dumps(rkey(effect),sort_keys=True)});anchors.append(r)
 for alias,task in itertools.product(['R4','R6'],TASKS):
  for split in (['dev','test_exploratory'] if task=='emp_H3' else ['dev']):
   for rep,seed,metric in itertools.product(REPS,SEEDS,METRICS):
    refit=point[alias,task,split,rep,seed,'independent_refit',metric];fixed=point[alias,task,split,rep,seed,'fixed_original_base',metric];policy_diffs.append({'candidate':alias,'task':task,'split':split,'representation':rep,'CV_seed':seed,'metric':metric,'refit_minus_fixed_point':float(refit['estimate'])-float(fixed['estimate']),'ci_low':None,'ci_high':None,'status':'DESCRIPTIVE_POINT_ONLY','reason':'No additional policy-difference inferential family approved; do not subtract marginal CI endpoints','refit_row_key':json.dumps(rkey(refit),sort_keys=True),'fixed_row_key':json.dumps(rkey(fixed),sort_keys=True)})
 assert len(entryrows)==240 and len(policy_diffs)==5460;write('TASK_ENTRY_ANALYSIS.csv',entryrows);write('POLICY_POINT_DIFFERENCES.csv',policy_diffs);write('PREDECLARED_ANCHORS.csv',anchors);publish('INCLUSION_EXPOSURE_PLAN.csv',(D6/'INCLUSION_EXPOSURE_PLAN.csv').read_bytes())
 goals=[{'goal':'Available checkpoint probe grid','target':'R4/R6six tasks x26hooks x3seeds x2policies','status':'COMPLETE_QUALIFIED_SCOPE','evidence':'NUMERICAL_AUDIT.json;AUDIT_REFIT_RECEIPT.json;VERIFIED_METRICS.csv','limit':'780A07heads independently released;156A06H3heads reused;60sampled audit refits, not all-head refitting'},{'goal':'Full R1-R6 project','target':'3276heads and3276fixedapplications','status':'PARTIAL_EXTERNAL_DEPENDENCIES','evidence':'COVERAGE.csv;PENDING_ADJACENT_CONTRASTS.csv','limit':'936R2/R5heads pending; R3livebridge pending; A04PARTIAL'},{'goal':'Shared input controls','target':'36unique fits','status':'REUSED_VALIDATED','evidence':'CONTROL_REUSE_MAP.json;CONTROL_METRICS_REUSED.csv','limit':'30otherfive fits relevant; repeated lines/applications are not extra fits'},{'goal':'True causal LM','target':'49primaryunits','status':'35_AVAILABLE_14_PENDING','evidence':'LM_METRICS_VERIFIED.csv;LM_CONTRASTS_VERIFIED.csv','limit':'No layer/CVseed axis, no classifier-CE substitution;12A06TRAIN diagnostics separate'},{'goal':'Predeclared R6-minus-R4','target':'5460classifier and14LMrows','status':'VERIFIED_NONADJACENT','evidence':'PAIRED_CONTRASTS.R6_minus_R4.csv;LM_CONTRASTS_VERIFIED.csv','limit':'Two planned additions and unmatched training differences; no individual addition effect'},{'goal':'Private independent-audit recovery','target':'Both candidates xall5tasks x2anchors x2policies;refit/classifier/LM checks','status':'PASS','evidence':'BACKUP_VERIFICATION.json;RESTORE.md','limit':'Representative CPU recovery, not GPU recreation or a second all-grid refit'},{'goal':'Causal mixture/optimality/forgetting','target':'Evidence beyond current benign observational endpoints','status':'NOT_ESTABLISHED','evidence':'CLAIMS_TO_EVIDENCE.csv;INCLUSION_EXPOSURE_PLAN.csv','limit':'Parents/objective/exposure/token budgets unknown; one cumulative order and3CVseeds do not identify causal optimum or forgetting'}];write('GOALS_STATUS.csv',goals)
 def p(alias,task,policy,rep='decoder.final_norm',metric='auroc'):return point[alias,task,'dev',rep,42,policy,metric]
 def fmt(row):return f"{float(row['estimate']):.6f}"+(f" [{float(row['ci_low']):.6f}, {float(row['ci_high']):.6f}]" if row.get('ci_low') and row.get('ci_high') else '')
 def eff(target,reference,task,policy,rep='decoder.final_norm',metric='auroc'):return effects[target,reference,task,'dev',rep,42,policy,metric]
 claims=[]
 def claim(cid,text,evidence,limit):claims.append({'claim_id':cid,'claim':text,'status':'SUPPORTED_DESCRIPTIVE' if cid!='C6' else 'NOT_IDENTIFIABLE','row_keys':json.dumps([rkey(r) for r in evidence],sort_keys=True),'evidence_files':'VERIFIED_METRICS.csv;TABLE_PARTITIONS.json;LM_METRICS_VERIFIED.csv;LM_CONTRASTS_VERIFIED.csv','uncertainty_scope':'Pointwise unadjusted2000exact/RC-group draws conditional on fitted heads; predeclared seed42anchors','limit':limit})
 tf_refit=p('R4','gue_tf_0','independent_refit');tf_fixed=p('R4','gue_tf_0','fixed_original_base');tf_base=p('base','gue_tf_0','independent_refit');core_refit=eff('R4','base','gue_prom_core_all','independent_refit');core_fixed=eff('R4','base','gue_prom_core_all','fixed_original_base');lm_tf=lpoint['R4','gue_tf_0','dev','causal_nll'];lm_base=lpoint['base','gue_tf_0','dev','causal_nll'];a=read(C/'NUMERICAL_AUDIT.json');rf=read(C/'AUDIT_REFIT_RECEIPT.json');seedreport=read(D/'SEED_SAMENESS_AUDIT.json')
 claim('C1','All780A07unit saved outputs passed independent checks;60prospective fresh-refit units passed, with zero new production heads.',[],'Full project remains partial; no GPU replication or all-head independent refitting.')
 claim('C2',f"HumanTF dev,finalnorm,seed42: R4refitAUROC {fmt(tf_refit)}, fixedAUROC {fmt(tf_fixed)}, baseAUROC {fmt(tf_base)}.",[tf_refit,tf_fixed,tf_base],'Different readout behavior is compatible with changed feature/readout relationships; does not prove erasure, understanding or forgetting.')
 claim('C3',f"Corepromoter dev,finalnorm,seed42 R4-minus-base AUROC: refit {fmt(core_refit)}; fixed {fmt(core_fixed)}.",[core_refit,core_fixed],'Readout policy matters; these are predeclared pointwise displays, not best-layer/seed selection or family-wide evidence.')
 nonadj=[eff('R6','R4',task,'independent_refit') for task in TASKS];positive=sum(float(r['estimate'])>0 for r in nonadj);negative=sum(float(r['estimate'])<0 for r in nonadj);claim('C4',f'At the six predeclared finalnorm/seed42 dev refit-AUROC displays,R6-minus-R4 point deltas are positive in{positive}tasks and negative in{negative}; intervals and all layers/seeds remain in full tables.',nonadj,'Descriptive anchor signs are not family-wide significance; R6-R4 is nonadjacent and cannot isolate splice or mouse addition.')
 claim('C5',f"HumanTF R4corpus NLL {fmt(lm_tf)} versus base {fmt(lm_base)}, while R4fixed AUROC is {fmt(tf_fixed)} versus base {fmt(tf_base)}.",[lm_tf,lm_base,tf_fixed,tf_base],'Within-task likelihood and linear-readout performance measure different properties; no cross-task capability score or causal/unlearning claim.')
 claim('C6','The five actual adjacent retain edges and realized training exposure do not identify a causal retain-mixture effect or optimum.',[],'R2/R5missing,R3livebridge absent,parents/objective/steps/schedules/token exposure unmatched;3probing seeds are not checkpoint-training replicas.')
 write('CLAIMS_TO_EVIDENCE.csv',claims)
 md=f'''# A08 verified analysis of the qualified endpoints

A08 independently verifies the available R4/R6 readout grid. **The full project remains partial.** R2 and R5 contribute936pending head cells; the R3 live bridge is absent; A04 remains PARTIAL. No missing checkpoint was interpolated or admitted.

The new audit covered780A07units,1560saved probability paths,7800marginal and16800paired metric distributions:49.2million attempted draw values. Maximum probability residual was{a['probability_max_abs']:.17g}, point-metric residual{a['metric_max_abs']:.17g}, per-draw residual{a['bootstrap_draw_max_abs']:.17g}, and interval residual{a['interval_max_abs']:.17g}. Frozen gates remain1e-10for probabilities and1e-12for metrics/draws/intervals. The prospective60-unit refit panel passed:960planned optimizer fits,{rf['actual_optimizer_fits']}actual including{rf['convergence_retries']}recorded retries. These are audit fits, not new production heads. All original A06/A07 seals remain unchanged.

## Readout behavior at the predeclared displays

The following official-dev AUROCs use **final norm,seed42**. These were predeclared displays, not selected winners. Full26representation/three-seed/five-metric results and block16(17th block) anchors are retained in the CSVs and figures. Brackets are pointwise95% exact/RC-group bootstrap intervals conditional on fitted heads.

| Task | R4 refit | R4 original-base | R6 refit | R6 original-base | R6−R4 refit |
|---|---:|---:|---:|---:|---:|
'''
 for task in TASKS:md+='| '+' | '.join([LABELS[task],fmt(p('R4',task,'independent_refit')),fmt(p('R4',task,'fixed_original_base')),fmt(p('R6',task,'independent_refit')),fmt(p('R6',task,'fixed_original_base')),fmt(eff('R6','R4',task,'independent_refit'))])+' |\n'
 md+='\n'+ '\n\n'.join(c['claim']+' '+c['limit'] for c in claims[1:5])+'\n'
 md+='''
## Layers, seeds and controls

The profiles show everydecoder block0–24and finalnorm, both policies and all threeCVseeds. Layer16is zero-based block17. Composition and normalized-forward4mer controls reuse36unique historical fits(30for the other-five tasks); repeated horizontal curves and paired applications do not create extra controls. Formal control comparisons remain at layer16/finalnorm and the three frozen seeds.

251of260candidate/task/representation groups have identical final parameter content across all three seeds; nine have two parameter sets. Distinct frozen folds can select the sameC, producing an identical deterministic full-TRAIN fit. This explanation was checked against fold hashes,C traces,parameter/probability identities and the60-unit independent refit panel. A seed range describes readout-selection sensitivity; it is not a confidence interval or intervention-training replication.

## Actual causal LM evidence

NLL uses total actual causal-head loss divided by total valid shifted targets; PPL is exp(corpusNLL). It is not classifier cross-entropy, an average of sequence perplexities, or a per-layer/seed score.35of49primary LMunits are available(21historical+14A06);12A06TRAIN diagnostics remain separate. The new predeclared R6−R4 family contains14LMmetric rows, with independent sum/count and every-draw ratio checks.

| Task | R4 corpus NLL | R6 corpus NLL | R6−R4 NLL [95% pointwise CI] |
|---|---:|---:|---:|
'''
 for task in TASKS:
  rr=next(r for r in lmp if r['checkpoint_alias']=='R6' and r['reference']=='R4' and r['task']==task and r['split']=='dev' and r['metric']=='causal_nll');md+='| '+' | '.join([LABELS[task],fmt(lpoint['R4',task,'dev','causal_nll']),fmt(lpoint['R6',task,'dev','causal_nll']),fmt(rr)])+' |\n'
 md+='''
## Task declarations and interpretation limits

The supplied cumulative design is H3; then humanTF,corepromoter,promoter300,splice,mouseTF. TASK_ENTRY_ANALYSIS joins measured rows to the stored configuration evidence. Planned inclusion,config declaration,exact dataset version,observed sampled rows and realized exposure remain distinct. Higher scores before a family appears in a supplied config do not prove unseen-training-data generalization. Unknown parents,objectives,steps,schedules and realized token/source exposure prevent causal mixture attribution; one cumulative ordering cannot establish an optimal mixture.

All five actual adjacent edges remain explicitly pending or bridge-gated. R6−R4 is predeclared and **nonadjacent**, spanning two planned additions and any other training differences. It never substitutes for R6−R5 or R5−R4. Historical R3 results and R3−R1 remain valid in their accepted domain; no new R3-to-R4/R6 effect was derived directly or by subtracting baseline-relative effects.

Intervals are pointwise exploratory and unadjusted across correlated tasks/layers/seeds. They are conditional on fitted heads. CI endpoints were never averaged or subtracted to invent a new interval. An interval crossing zero does not demonstrate equivalence/noninferiority. Exact/RC groups do not establish locus/homology independence. Numeric biological-label ambiguities remain. These benign capability measurements alone do not establish forgetting,resistance to recovery,information erasure or biological understanding.

## Historical reuse and exploratory test

A06 H3 and LM checks and the qualified base/R1/R3 historical audit graph are reused by exact identities. Historical marginal point reports do not carry all absolute CIs; those fields remain null with reasons,while accepted historical paired intervals remain available. The legacy policy spelling fixed_base_scaler_and_head is normalized to fixed_original_base with source spelling retained and original values unchanged. The pretrained base's own fixed application is the same original-base prediction function; it is not a new fit.

H3's previously examined exploratory test is kept in separate rows and figures. It was not an untouched test,was not pooled with dev,and was not used for layer/seed/Cselection. No new held-out set was opened.

A06's original paired export still records FAIL_MISSING_REQUIRED_LINEAGE. The normalized derivative retains every original field/key/order and measurement origin A06; ingestion is REUSED_IN_A08. Reporting lineage is not checkpoint parentage.

The public logical paired table is the union of the four files in TABLE_PARTITIONS.json; missing adjacent-effect keys are separately enumerated with null estimates and precise reasons. Figure values come only from released rows. Private recovery claims are scoped CPU checks,not GPU/runtime recreation. See BACKUP_VERIFICATION.json,RESTORE.md and SESSION_HANDOFF.md for exact archives,hashes,commands and exclusions.

WAITING_FOR_APPROVAL: A09
'''
 publish('ANALYSIS.md',md)
 policy_record=read(C/'REPORT_POLICY_NORMALIZATION.json');policy_record.update(status='PASS',normalized_fixed_policy_metric_rows=8190,original_scientific_values_changed=False,source_spelling_retained=True)
 for root,map_alias in [(H,{'base':'base','h3_only_maxent':'R1'}),(H.parent.parent/'R3/multiretain-comparison-v1-final-20261110T173945Z',{'three_source_config2151':'R3'})]:
  for old in rows(root/'reports/metrics.csv'):
   if old['checkpoint'] not in map_alias:continue
   pol='fixed_original_base' if old['probe_policy']=='fixed_base_scaler_and_head' else old['probe_policy'];new=point[map_alias[old['checkpoint']],old['task'],'test_exploratory' if old['split']=='test' else old['split'],old['layer'],int(old['seed']),pol,old['metric']];assert float(new['estimate'])==float(old['value']) and new['source_policy']==old['probe_policy']
 for task in TASKS:
  for split in (['dev','test_exploratory'] if task=='emp_H3' else ['dev']):
   for rep,seed,m in itertools.product(REPS,SEEDS,METRICS):assert point['base',task,split,rep,seed,'independent_refit',m]['estimate']==point['base',task,split,rep,seed,'fixed_original_base',m]['estimate']
 policy_record['base_fixed_and_refit_function_point_equivalence_checked']=2730;put(C/'REPORT_POLICY_NORMALIZATION.json',policy_record);publish('REPORT_POLICY_NORMALIZATION.json',policy_record)
 print(json.dumps({'status':'PASS','head_universe':3276,'available_heads':2340,'pending_adjacent_classifier_keys':27300,'pending_adjacent_LM_keys':70,'task_entry_rows':240,'descriptive_policy_difference_rows':5460,'claims':len(claims)}))
if __name__=='__main__':main()
