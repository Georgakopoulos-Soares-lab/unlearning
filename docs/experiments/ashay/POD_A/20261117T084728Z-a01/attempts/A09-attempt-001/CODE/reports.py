"""Evidence-linked A09 report generation from immutable released aggregates only."""
from common import *
import collections,itertools,re
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];LABELS=dict(zip(TASKS,['H3','Human TF','Core promoter','Promoter 300','Splice (three classes)','Mouse TF']));POLS=['independent_refit','fixed_original_base'];HOOKS=['decoder.layers.16','decoder.final_norm'];KEY=['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256']
def main():
 manifest=read(D8/'TABLE_PARTITIONS.json');files=['VERIFIED_METRICS.csv','CONTROL_METRICS_REUSED.csv','LM_METRICS_VERIFIED.csv','LM_CONTRASTS_VERIFIED.csv','PAIRED_CONTRASTS.csv','PAIRED_CONTRASTS.H3_reused.csv','PAIRED_CONTRASTS.historical.csv','PAIRED_CONTRASTS.R6_minus_R4.csv'];data={n:rows(D8/n) for n in files};hashes={n:sha(D8/n) for n in files};points=data['VERIFIED_METRICS.csv'];pairs=[r for n in files if n.startswith('PAIRED_') for r in data[n]];point={(r['checkpoint_alias'],r['task'],r['split'],r['representation'],r['CV_seed'],r['policy'],r['metric']):r for r in points};paired={(r['checkpoint_alias'],r['reference'],r['task'],r['split'],r['representation'],r['CV_seed'],r['policy'],r['metric']):r for r in pairs};lm={(r['checkpoint_alias'],r['task'],r['split'],r['metric']):r for r in data['LM_METRICS_VERIFIED.csv']};lmp={(r['checkpoint_alias'],r['reference'],r['task'],r['split'],r['metric']):r for r in data['LM_CONTRASTS_VERIFIED.csv']};origins={id(r):n for n,rr in data.items() for r in rr};claims={}
 def cite(r,context):
  assert r['status'] in ['VERIFIED','REUSED_VALIDATED'];n=origins[id(r)];key={k:r.get(k,'') for k in KEY};cid='A09-C-'+digest({'source':hashes[n],'key':key})[:16]
  if cid not in claims:claims[cid]={'claim_id':cid,'claim_type':'RELEASED_ROW','used_in':context,'checkpoint_alias':r['checkpoint_alias'],'reference':r['reference'],'original_endpoint_id':r['original_endpoint_id'],'checkpoint_content_id':r['checkpoint_content_id'],'reference_endpoint_id':r['reference_endpoint_id'],'reference_content_id':r['reference_content_id'],'task':r['task'],'split':r['split'],'representation':r['representation'],'CV_seed':r['CV_seed'],'policy':r['policy'],'reference_policy':r['reference_policy'],'metric':r['metric'],'estimate':r['estimate'],'ci_low':r['ci_low'],'ci_high':r['ci_high'],'row_key':json.dumps(key,sort_keys=True),'source_table':'../A08-attempt-001/'+n,'source_table_sha256':hashes[n],'source_research_commit':cfg['research_head_before'],'release_status':r['status'],'measurement_attempt':r['measurement_attempt'],'ingestion_status':'REUSED_IN_A09_REPORT','prediction_sha256':r['prediction_sha256'],'reference_prediction_sha256':r['reference_prediction_sha256'],'draw_sha256':r['draw_sha256'],'producer_receipt_sha256':r['producer_receipt_sha256'],'audit_receipt_sha256':r['audit_receipt_sha256'],'uncertainty_scope':'Pointwise unadjusted exact/RC-group paired bootstrap conditional on fitted heads; inherited marginal CIs null with reason','interpretation_limit':'Observational checkpoint/readout association; no causal mixture, unseen-training-data, equivalence or forgetting inference'}
  elif context not in claims[cid]['used_in']:claims[cid]['used_in']+='; '+context
  value=f"{float(r['estimate']):.6f}"
  if r['ci_low'] and r['ci_high']:value+=f" [{float(r['ci_low']):.6f}, {float(r['ci_high']):.6f}]"
  return value
 def p(alias,task,policy,hook='decoder.final_norm',metric='auroc'):return point[alias,task,'dev',hook,'42',policy,metric]
 def e(alias,reference,task,policy,hook='decoder.final_norm',metric='auroc'):return paired[alias,reference,task,'dev',hook,'42',policy,metric]
 def c(r):return cite(r,'RESULTS.md; ONE_PAGE_SUMMARY.md; TEAM_UPDATE_DRAFT.md; report anchors')
 # Readable scope counts come from the immutable coverage ledger, not filename arithmetic.
 coverage=rows(D8/'COVERAGE.csv');assert len(coverage)==6637
 for kind in ['final_head','fixed_base_application']:
  rr=[r for r in coverage if r['unit_kind']==kind];assert len(rr)==3276 and sum(r['status'] in ['VERIFIED','REUSED_VALIDATED'] for r in rr)==2340
 scope={'schema':'pod-a-a09-count-evidence-v1','coverage_source':ref(D8/'COVERAGE.csv'),'heads_available':2340,'heads_planned':3276,'fixed_applications_available':2340,'fixed_applications_planned':3276,'pending_heads':936,'R2_pending_heads':468,'R5_pending_heads':468,'primary_LM_available':35,'primary_LM_planned':49,'controls':36,'marginal_classifier_rows':len(points),'logical_paired_classifier_rows':len(pairs),'LM_marginal_rows':len(data['LM_METRICS_VERIFIED.csv']),'LM_paired_rows':len(data['LM_CONTRASTS_VERIFIED.csv']),'new_A09_measurements':0,'A08_audits':ref(D8/'NUMERICAL_AUDIT.json'),'A08_refits':ref(D8/'AUDIT_REFIT_RECEIPT.json'),'A08_figure_validation':ref(D8/'FIGURE_VALIDATION.json'),'no_new_fits_forwards_or_draws':True};publish('COUNT_EVIDENCE.json',scope)
 tableindex=[]
 for n in files:
  if n=='PAIRED_CONTRASTS.H3_reused.csv':loc='PAIRED_CONTRASTS.H3_canonical.v1.csv';path=D/loc;explain='A09 metadata-only canonical control reference IDs; all 6720 original rows/numbers/order/lineage preserved; original IDs retained'
  else:loc='../A08-attempt-001/'+n;path=D8/n;explain='Immutable byte-identical A08 evidence, reused by relative repository link and pinned input commit'
  tableindex.append({'logical_table':'PAIRED_CONTRASTS' if n.startswith('PAIRED_') else n.removesuffix('.csv'),'file':loc,'rows':len(data[n]),'sha256':sha(path),'source_file':'../A08-attempt-001/'+n,'source_sha256':hashes[n],'source_commit':cfg['research_head_before'],'release_status':'VERIFIED_OR_REUSED_VALIDATED','measurement_origin':'See each row measurement_attempt; A09 adds no measurements','explanation':explain})
 for n in ['COVERAGE.csv','PENDING_ADJACENT_CONTRASTS.csv','PENDING_ADJACENT_LM.csv','INCLUSION_EXPOSURE_PLAN.csv','COMPARABILITY_MATRIX.csv','POLICY_POINT_DIFFERENCES.csv','SEED_SENSITIVITY.csv','SEED_DIAGNOSTICS.csv','PREDECLARED_ANCHORS.csv','TASK_ENTRY_ANALYSIS.csv']:
  path=D/n if (D/n).exists() else D8/n;tableindex.append({'logical_table':n.removesuffix('.csv'),'file':str(path.relative_to(D)) if path.is_relative_to(D) else '../A08-attempt-001/'+n,'rows':len(rows(path)),'sha256':sha(path),'source_file':'../A08-attempt-001/'+n,'source_sha256':sha(D8/n),'source_commit':cfg['research_head_before'],'release_status':'EXPLICIT_PENDING_KEYS_WITH_NULLS' if n.startswith('PENDING') else 'REUSED_VALIDATED_METADATA','measurement_origin':'Immutable A08/inherited evidence','explanation':'Full denominator retained; descriptive policy gaps have no CI'})
 publish('TABLE_INDEX.json',{'schema':'pod-a-a09-table-index-v1','status':'PASS','input_research_commit':cfg['research_head_before'],'tables':tableindex,'logical_paired_rows':45360,'logical_partition_count':4,'A07_only_main_paired_csv_rows':16800,'H3_partition_rows':6720,'historical_partition_rows':16380,'new_nonadjacent_partition_rows':5460,'combined_export_created':False,'null_encoding':'CSV empty -> null, unknown never zero','schemas':'../A08-attempt-001/RESULT_SCHEMAS.json','typed_alias_map':'ENDPOINT_ALIAS_MAP.csv','full_scope_missingness_not_reduced':True})
 report='''# Pod A results: verified available checkpoints, incomplete incremental sequence

**Qualified available-endpoint analysis is complete. The full R1–R6 sequence and A04 remain partial.** A09 adds usable reports and fresh saved-analysis recovery; it adds no model forwards, fitting, draws or new scientific estimates. Relative to the November 10 historical base/R1/R3 evidence, the package now contains independently verified R4/R6 measurements across all six tasks, 26 representations and three CV seeds. That new science was produced in A06/A07 and released in A08, not measured again here.

The study currently has 2,340 of 3,276 final heads and a separate 2,340 of 3,276 unchanged-base applications. R2 and R5 each lack 468 head cells. Primary causal LM coverage is 35 of 49 units; 36 shared control fits are reused. Every cell remains in the 6,637-unit ledger. [Count evidence](COUNT_EVIDENCE.json), [coverage](COVERAGE.csv), [table index](TABLE_INDEX.json) and [goals](GOALS_STATUS.csv) retain the denominators.

## Main findings

'''
 tf=p('R4','gue_tf_0','independent_refit');tff=p('R4','gue_tf_0','fixed_original_base');tfbase=p('base','gue_tf_0','independent_refit');core=e('R4','base','gue_prom_core_all','independent_refit');corefixed=e('R4','base','gue_prom_core_all','fixed_original_base');mouse=e('R6','R4','gue_mouse_0','independent_refit');splice16=e('R6','R4','gue_splice_reconstructed','independent_refit','decoder.layers.16');splicefn=e('R6','R4','gue_splice_reconstructed','independent_refit');core16=e('R6','R4','gue_prom_core_all','independent_refit','decoder.layers.16');lmsplice=lmp['R6','R4','gue_splice_reconstructed','dev','causal_nll'];lmtf=lm['R4','gue_tf_0','dev','causal_nll'];lmbase=lm['base','gue_tf_0','dev','causal_nll']
 findings=[f"**Readout policy changes the conclusion.** Human-TF official-dev final-norm/seed-42 AUROC is {c(tf)} for the R4 refit, {c(tff)} using the unchanged base readout, and {c(tfbase)} for base. The refitted and fixed heads answer different questions. Their discrepancy is compatible with a changed feature/readout relationship; it does not prove information erasure or forgetting.",f"**A refit gain need not survive the original base head.** At the same final-norm/seed-42 display, core-promoter R4−base AUROC is {c(core)} under refitting and {c(corefixed)} under fixed transfer. The latter interval crosses zero; this is inconclusive rather than evidence of equivalence. These predeclared displays are not selected best layers.",f"**R6 is not uniformly better than R4, and location matters.** The mouse-TF final-norm/seed-42 refit AUROC change is {c(mouse)}. Splice is {c(splice16)} at block 16 but {c(splicefn)} at final norm; core promoter is {c(core16)} at block 16. All effects are the predeclared **nonadjacent** R6−R4 comparison. Its two planned additions and unmatched training changes cannot be separated causally.",f"**Likelihood and probe behavior can disagree.** R4 human-TF corpus NLL is {c(lmtf)} against base {c(lmbase)}, despite weak fixed-base classification above. R6−R4 splice NLL is {c(lmsplice)}, while the final-norm refit AUROC interval is inconclusive. NLL and discriminative readouts measure different properties; no cross-task capability average is constructed."]
 for i,f in enumerate(findings,1):report+=str(i)+'. '+f+'\n\n'
 report+='''All brackets below are **pointwise, unadjusted 95% exact/RC-group bootstrap intervals conditional on the fitted heads**, not familywise claims across correlated tasks/layers/seeds. An interval crossing zero does not establish equivalence or preservation. Three CV seeds are not checkpoint-training replications. Every displayed value is machine-joined to an immutable released row in [claims](CLAIMS_TO_EVIDENCE.csv).

## Both predeclared anchors and both readouts

The following official-dev tables use seed 42 for readability. Block 16 is the zero-based **17th decoder block**; final norm is a separate hook. All 26 representations, all three seeds and all five metrics remain in the complete source tables and [figure gallery](FIGURE_GALLERY.md). Historical marginal intervals absent from the inherited reports remain null; no new marginal interval was manufactured.

'''
 anchor_export=[]
 for hook,policy in itertools.product(HOOKS,POLS):
  report+='### '+('Block 16' if hook.endswith('.16') else 'Final norm')+' — '+('refitted readout' if policy=='independent_refit' else 'unchanged base readout')+'\n\n| Task | Base AUROC | R1 AUROC | R4 AUROC | R6 AUROC | R6−R4 AUROC |\n|---|---:|---:|---:|---:|---:|\n'
  for task in TASKS:
   vals=[p(alias,task,policy,hook) for alias in ['base','R1','R4','R6']]+[e('R6','R4',task,policy,hook)];report+='| '+LABELS[task]+' | '+' | '.join(c(r) for r in vals)+' |\n';anchor_export+=vals
  report+='\n'
 report+='''## Changes relative to base, R1 and simple DNA controls

The paired differences below retain matched cohorts, shared group draws and reference-policy semantics. Controls are shared input baselines: composition uses four canonical A/C/G/T fractions, and normalized forward 4-mers use 256 features without reverse-complement collapsing. There are 36 total historical fits, not a new fit per checkpoint or layer. Formal control comparisons are restricted to these anchors and frozen seeds; horizontal control lines in all-layer plots do not add an all-layer inferential family.

'''
 for hook,policy in itertools.product(HOOKS,POLS):
  report+='### '+('Block 16' if hook.endswith('.16') else 'Final norm')+' — '+('refitted' if policy=='independent_refit' else 'fixed base')+' paired AUROC changes\n\n| Task / candidate | −base | −R1 | −composition | −forward 4-mer |\n|---|---:|---:|---:|---:|\n'
  for task,alias in itertools.product(TASKS,['R4','R6']):
   vals=[e(alias,reference,task,policy,hook) for reference in ['base','R1','control_composition','control_kmer4']];report+='| '+LABELS[task]+' / '+alias+' | '+' | '.join(c(r) for r in vals)+' |\n';anchor_export+=vals
  report+='\n'
 report+='''## Where changes appear and what the seeds mean

All-layer profiles show the full block-0–24 and final-norm axes, rather than choosing a favorable hook after looking at scores. The distinct splice results at block 16 and final norm above illustrate why a final-norm-only headline is insufficient. Human-TF fixed transfer also varies substantially across representations while its refitted readout remains useful. The profiles expose these differences for every task and both policies; the paired anchor tables supply uncertainty at the prospectively chosen displays.

A08 verified that 251 of 260 candidate/task/representation groups have identical final parameter content across all three CV seeds; nine have two parameter sets. Different frozen folds can select the same regularization C and yield an identical deterministic full-TRAIN fit. This is explained by fold/selection/parameter identities and the prescribed sampled refit panel. It does **not** establish broad seed robustness or independent checkpoint-training replication. [Seed evidence](../A08-attempt-001/SEED_SAMENESS_AUDIT.json) and [full seed sensitivity](../A08-attempt-001/SEED_SENSITIVITY.csv) retain the scope.

## Task entry and already-declared tasks

The supplied cumulative design is H3 → human TF → core promoter → promoter 300 → splice → mouse TF. [Configuration evidence](INCLUSION_EXPOSURE_PLAN.csv) distinguishes planned membership, first evidenced declaration, exact dataset/version, sampled rows, realized exposure and parent/objective/token-budget comparability. Unknown exposure is not zero exposure.

The following R4 refit changes relative to R1 occur before splice/mouse appear in R4's supplied retain declaration. They are descriptive checkpoint associations, not isolated inclusion transitions or proof of unseen-training-data generalization:

| Task | Block-16 R4−R1 AUROC | Final-norm R4−R1 AUROC |
|---|---:|---:|
'''
 for task in ['gue_splice_reconstructed','gue_mouse_0']:report+='| '+LABELS[task]+' | '+c(e('R4','R1',task,'independent_refit','decoder.layers.16'))+' | '+c(e('R4','R1',task,'independent_refit'))+' |\n'
 report+='''
For already-declared H3, human TF, core promoter and promoter 300, the complete anchor tables show changes under both policies. Apparent preservation under a refitted head does not guarantee unchanged-base transfer or establish a noninferiority margin. Unknown parents, objectives, training steps, schedules and realized source/token exposure prevent a controlled causal retain-diversity interpretation. One supplied cumulative ordering cannot identify an optimal mixture.

All five actual adjacent edges—R2−R1, R3−R2, R4−R3, R5−R4 and R6−R5—remain pending or bridge-gated. Their 27,300 classifier keys and 70 LM keys retain null estimates and reasons. R6−R4 is not substituted for either missing adjacent edge.

## Actual causal LM evidence within each task

NLL is total actual next-token loss divided by total valid shifted targets, using saved float32 per-sequence loss sums and float64 corpus aggregation; perplexity is exp(corpus NLL). It is not classifier cross-entropy, an average of sequence perplexities, or a per-layer/seed score. The 12 A06 TRAIN diagnostics remain separate from the 35 available primary units. No task ranking by raw loss or pooled task capability score is justified.

| Task | Base NLL | R1 NLL | R4 NLL | R6 NLL | R6−R4 NLL | R6−R4 perplexity |
|---|---:|---:|---:|---:|---:|---:|
'''
 for task in TASKS:
  vals=[lm[a,task,'dev','causal_nll'] for a in ['base','R1','R4','R6']]+[lmp['R6','R4',task,'dev','causal_nll'],lmp['R6','R4',task,'dev','perplexity']];report+='| '+LABELS[task]+' | '+' | '.join(c(r) for r in vals)+' |\n'
 report+='''
## Historical R3: accepted domain only

R3 and its base/R1 comparisons remain useful in their verified historical runtime domain. The table below stays separate from current R4/R6 effects; no R4−R3 effect is constructed by subtracting baseline-relative differences. Missing R3 native payload/bridge dependencies remain explicit.

| Task / hook / readout | R3 AUROC | R3−base | R3−R1 (nonadjacent) |
|---|---:|---:|---:|
'''
 for task,hook,policy in itertools.product(TASKS,HOOKS,POLS):
  vals=[p('R3',task,policy,hook),e('R3','base',task,policy,hook),e('R3','R1',task,policy,hook)];report+='| '+LABELS[task]+' / '+('block 16' if hook.endswith('.16') else 'final norm')+' / '+('refit' if policy=='independent_refit' else 'fixed')+' | '+' | '.join(c(r) for r in vals)+' |\n'
 report+='''
## Exploratory test, limits and reproducibility

H3's previously examined test records are explicitly `test_exploratory` and appear in separate tables/figures. They are not an untouched test, were not pooled with dev, and did not select C, a layer or a seed. Other tasks use the established official dev only. Numeric label consistency does not resolve missing biological TF/label metadata. Exact/RC groups prevent the frozen duplicate leakage definition; they do not prove locus/homology independence.

These benign measurements alone establish neither successful unlearning/forgetting nor information erasure or resistance to relearning. Pod B owns relearning on another server. Saliency/perturbation remains deferred to a separate scope and approval. No missing checkpoint was interpolated or downloaded in A09.

A08 independently checked every eligible saved-output probability, point metric, draw mask/value, paired delta and interval at the frozen tolerances. Its 60-unit independent refit panel is sampled; it is not a second fit of all 780 heads. A09's [audit release table](AUDIT_RELEASE_STATUS.csv) reconciles the frozen plan with those completed receipts without rewriting producer seals. [Report repairs](REPORT_REPAIR_LOG.json) retain the original handoff, plan and control IDs. [Data dictionary](DATA_DICTIONARY.md), [figure gallery](FIGURE_GALLERY.md), [recovery graph](RECOVERY_DEPENDENCY_GRAPH.json), [restore commands](RESTORE.md) and [handoff](SESSION_HANDOFF.md) bind exact sources and scope. Saved-analysis recovery is distinct from full GPU/model recreation.
'''
 publish('RESULTS.md',report)
 one='# Pod A: one-page summary\n\n**The available-endpoint analysis is complete; the full incremental sequence remains incomplete.** A09 reports and recovers previously verified science without adding fits, forwards or intervals.\n\n'+ '\n\n'.join(findings)+'\n\nThe readable displays use official dev, seed 42 and predeclared block 16/final norm. All layers, three seeds, both policies and five metrics are retained in the [full results](RESULTS.md), [tables](TABLE_INDEX.json) and [31-figure gallery](FIGURE_GALLERY.md). Intervals are conditional, pointwise and unadjusted; zero-crossing is not equivalence and CV seeds are not intervention replicas.\n\nCoverage is 2,340/3,276 heads and separately 2,340/3,276 fixed applications, 35/49 primary LM units and 36 shared controls. R2/R5 each lack 468 heads; R3 cross-runtime contrasts need the live bridge. All five adjacent edges remain missing; R6−R4 is nonadjacent. Training ancestry, objective and realized exposure gaps prevent a causal mixture or optimality claim. A04 remains PARTIAL. H3 exploratory test remains separate.\n\n[Claims and exact row keys](CLAIMS_TO_EVIDENCE.csv), [missing inputs](MISSING_INPUTS_DRAFT.md) and [saved-analysis recovery](BACKUP_VERIFICATION.json) make the evidence and remaining dependencies reviewable.\n';publish('ONE_PAGE_SUMMARY.md',one)
 methods='''# Methods and interpretation limits

## Frozen inputs and readouts

The six tasks are H3, human TF, core promoter, promoter 300, reconstructed three-class splice and mouse TF. H3 has 11,971 TRAIN, 1,497 dev and 1,497 previously examined exploratory-test rows. Each other task has 1,024 TRAIN and 512 official-dev rows. Splice dev has 511 exact/RC groups; the other four have 512; H3 dev/test have 1,497. Counts supplement, rather than replace, ordered ID/label/class/group/sequence-digest checks. The exact cohort hashes are in the frozen protocol and A09 input receipts.

Representations are decoder blocks 0–24 and the separate final norm, width 1920. The file-key mapping is bijective. The source extraction used qualified physical batches of eight, excluded filler rows, masked nucleotide mean pooling, right padding, BF16/FP32 arithmetic and the approved backend. A09 performs no extraction or requalification.

Refitted readouts use TRAIN-only fold-local StandardScaler and balanced L2 LBFGS logistic regression, C in 0.1/1/10, mean fold AUROC, exact ties to smaller C, tol 1e−4, max_iter 2000 with recorded 10000 retry, optimizer random_state 42. Frozen group folds use CV seeds 42/17/1234, threefold H3 and fivefold other tasks. Final scaling uses all authorized TRAIN. Saved float32 transform arithmetic, including intermediate rounding, matters for exact prediction reconstruction.

Fixed transfer applies the original pretrained-base scaler/head unchanged. Target-specific scaling, calibration, retuning or substituting an R1/R3 head would change the policy and was not done. The point-only refit-minus-fixed table does not authorize a policy-gap CI. Composition and normalized forward 4-mer controls reuse 36 historical fits; repeated curves/contrasts do not create more fits.

Binary positive class is numerical 1 with threshold 0.5. Splice uses sorted classes 0/1/2, argmax, macro one-vs-rest AUROC and mean per-class AP. AUROC, AP, accuracy, balanced accuracy and classifier cross-entropy are retained. Biological label/TF meanings unresolved in source metadata remain unresolved here.

## Conditional uncertainty and independent computation

The exact saved 2,000 group draws use seed 20261103, frozen group order and shared endpoint masks. Both splice rows in the duplicate exact/RC group share a multiplicity. Target−reference is calculated within each draw before the frozen quantiles. Missing-class masks and undefined values are explicit; no zeros, intersections or extra resampling replace invalid data. Pointwise intervals are unadjusted and conditional on fitted heads. They are not simultaneous across the correlated grid, nor equivalent to uncertainty over independently trained intervention checkpoints.

A08 checked all 780 A07 units and both saved policies: 1,560 paths, 7,800 marginal distributions and 16,800 paired distributions, accounting for 49.2 million attempted values. It independently reconstructed scaler/coefficient probabilities, float64 pairwise/threshold metrics and group draw values. Its prospectively selected 60-unit panel comprised 960 independent optimizer fits with no retries; A09 reuses that proof and does not refit. All original producer seals remain COMPLETE_UNVERIFIED where originally written; A08 overlays provide the independent release state.

Probability agreement tolerance remains 1e−10; metric/draw/interval tolerance remains 1e−12. These are numerical agreement gates, not uncertainty bands. The exact audit maxima, tests, lineage and scopes are in the immutable A08 audit files. A09 runs focused reporting/identity/writer tests, table/figure joins and a deterministic saved-output recovery panel; it does not rerun the full numerical audit.

## Causal LM and compatibility domains

Causal NLL is total actual shifted next-token loss divided by total valid targets; PPL is its exponential. Saved sequence sums are float32 and corpus/group aggregation is float64. It is neither classifier loss nor an average of sequence perplexities. There is no LM representation/CV-seed axis. Task losses are interpreted within task; there is no averaged perplexity capability score. Primary units and 12 TRAIN diagnostics stay separate.

Historical base/R1/R3 results retain their accepted source/runtime domain. Qualified R4/R6 comparisons use exact compatible references and frozen cohorts. A missing R3 live bridge blocks new affected R3 cross-runtime contrasts; subtracting two base-relative effects does not repair that dependency. R6−R4 and historical R3−R1 are nonadjacent. The five actual adjacent edges remain null/pending rather than interpolated.

## Interpretation and exclusions

Planned membership, configuration declaration, dataset version, sampler rows and realized exposure are separate. Unknown parents/objectives/steps/schedules/source or token exposure prevent causal retain-diversity attribution. One cumulative order cannot establish an optimal mixture. A higher score before config declaration is not proof of unseen-data generalization. An interval crossing zero does not demonstrate equivalence/noninferiority or a specified preservation margin. Identical final functions across CV seeds do not establish broad robustness. Exact/RC groups do not establish locus/homology independence.

Previously examined H3 test is exploratory, separate from dev and unused for selection. No new untouched test was accessed. Benign capability evidence does not establish forgetting, information erasure, biological understanding or resistance to relearning. Pod B relearning has an external owner; perturbation/saliency requires separate approval. Model weights and installed GPU/runtime binaries are excluded from saved-analysis recovery with explicit [reacquisition identities and limitations](REACQUISITION_MAP.json). No full GPU recreation is claimed.
''';publish('METHODS_AND_LIMITS.md',methods)
 gallery='# Verified figure gallery\n\nAll 31 PNG/PDF pairs are reused byte-identically from the pinned A08 commit. Full-precision values and all panel uses are in [plot data](../A08-attempt-001/PLOT_DATA/plotted_values.csv); [figure validation](../A08-attempt-001/FIGURE_VALIDATION.json) records data/source/file hashes and captions. No rerendering, smoothing, new interval family or best-layer selection was performed. Bold curves display seed 42; thin curves retain seeds 17/1234. Seed spread is not a CI; shaded intervals are conditional pointwise bootstrap intervals. Final norm is a separate hook.\n\n'
 figures=read(D8/'FIGURE_VALIDATION.json');groups=collections.defaultdict(list)
 for f in figures['figures']:groups[f['name'].split('/')[0]].append(f)
 for group,ff in groups.items():
  gallery+='## '+group.replace('_',' ').title()+'\n\n'
  if group=='dev':gallery+='Official dev only. R6−R4 is explicitly nonadjacent; all-layer controls are point displays while paired control inference stays at the predeclared anchors.\n\n'
  elif group=='historical_domain':gallery+='Historical R3/base/R1 domain only; no line bridges it into current R4/R6 effects.\n\n'
  elif group=='exploratory_test':gallery+='Previously examined H3 exploratory test, never pooled with dev or presented as untouched confirmation.\n\n'
  else:gallery+='Missing endpoints and adjacent edges stay visible; no filled-in trajectory.\n\n'
  gallery+='| Figure | PNG | PDF | Scope / caption |\n|---|---|---|---|\n'
  for f in ff:
   png=next(e for e in f['files'] if e['path'].endswith('.png'));pdf=next(e for e in f['files'] if e['path'].endswith('.pdf'));gallery+='| '+f['name']+' | [View](../A08-attempt-001/'+png['path']+') | [Download](../A08-attempt-001/'+pdf['path']+') | '+f['caption'].replace('|','/')+' |\n'
  gallery+='\n'
 for name in ['dev/profiles_auroc','dev/R6_minus_R4_auroc','dev/anchors__controls_auroc','dev/LM_R6_minus_R4','coverage/availability_and_missing_edges']:
  gallery+='### '+name.replace('_',' ')+'\n\n!['+name+'](../A08-attempt-001/figures/'+name+'.png)\n\n'
 publish('FIGURE_GALLERY.md',gallery)
 draft='# Team update — unsent draft\n\nQualified Pod A available-endpoint analysis and verification are complete; the full incremental checkpoint sequence remains incomplete. Since the November 10 historical comparison, R4/R6 now have the complete qualified six-task/all-layer/three-seed readout grid, independently released in A08. A09 adds presentation and saved-analysis recovery rather than new measurements.\n\n'+ '\n\n'.join(findings)+'\n\nThe [results](RESULTS.md), [one-page summary](ONE_PAGE_SUMMARY.md) and [gallery](FIGURE_GALLERY.md) retain both readout policies, adverse/inconclusive outcomes, historical R3 and the separate exploratory H3 test. R2 and R5 remain unavailable for the full sequence; R3 needs its live bridge for affected new cross-runtime contrasts. Parent/objective/source/exposure evidence is still needed before causal retain-mixture or unseen-training-data claims.\n\nNo message has been sent. Missing-input requests are recorded in [a separate unsent draft](MISSING_INPUTS_DRAFT.md). Pod B owns relearning on its separate server. Saliency/perturbation requires a separately published and approved scope.\n';publish('TEAM_UPDATE_DRAFT.md',draft)
 # Full precision machine-readable displays supplement the rounded Markdown.
 uniq={digest({k:r.get(k,'') for k in KEY}):r for r in anchor_export};table('REPORT_ANCHORS_FULL_PRECISION.csv',list(uniq.values()))
 table('CLAIMS_TO_EVIDENCE.csv',list(claims.values()))
 scopeclaims={'count_source':'COUNT_EVIDENCE.json','count_source_sha256':sha(D/'COUNT_EVIDENCE.json'),'seed_sameness_source':ref(D8/'SEED_SAMENESS_AUDIT.json'),'non_estimate_quantities':'Coverage, dataset/representation/seed/fold counts, audit/resource/figure counts are defined by the frozen protocol/count receipts; no inferential estimates are implied','released_row_claims':len(claims),'all_displays_generated_by_join':True};publish('CLAIM_SCOPE_INDEX.json',scopeclaims)
 goals=[{'goal':'R1–R6 full incremental sequence','denominator':'3276heads and3276fixed applications','status':'PARTIAL_EXTERNAL_DEPENDENCIES','available':'2340heads;2340applications','gap':'R2/R5 each468heads and468applications; R3livebridge for affected new contrasts','evidence':'COVERAGE.csv;COMPARABILITY_MATRIX.csv'},{'goal':'Qualified R4/R6 six-task/all-layer/three-seed/both-policy analysis','denominator':'26hooks x3seeds x6tasks per candidate, plus separate authorized H3exploratory test rows','status':'COMPLETE_QUALIFIED_SCOPE','available':'A06H3 and A07other-five production; A08all780audit +60sampled refits','gap':'No full-project or all-head fresh-refit claim','evidence':'AUDIT_RELEASE_STATUS.csv;TABLE_INDEX.json'},{'goal':'Task entry/retention interpretation','denominator':'Six tasks across supplied cumulative declarations','status':'DESCRIPTIVE_ONLY_CAUSAL_IDENTIFIABILITY_INCOMPLETE','available':'Supplied config hashes, declared sources, both readouts and exact paired effects','gap':'Dataset versions/sampled rows/realized exposure/parents/objectives/token budgets unknown','evidence':'INCLUSION_EXPOSURE_PLAN.csv;RESULTS.md'},{'goal':'Simple DNA controls','denominator':'36unique fitted controls','status':'REUSED_VALIDATED','available':'210point rows; anchor paired effects;480typedH3alias rows repaired','gap':'No new all-layer control inference','evidence':'ENDPOINT_ALIAS_MAP.csv;TABLE_INDEX.json'},{'goal':'Actual causal LM','denominator':'49primary model/task/split units','status':'35_AVAILABLE_14_PENDING','available':'70marginal and112paired metric rows;12TRAINdiagnostics separate','gap':'R2/R5missing; no layer/seed multiplication','evidence':'TABLE_INDEX.json;RESULTS.md'},{'goal':'Independent numerical verification','denominator':'780A07units,1560paths,60prospective audit refits','status':'REUSED_VALIDATED_A08','available':'All-unit numerical PASS,960audit optimizerfits,zero new productionheads','gap':'Not all780independently refitted or GPUrecreated','evidence':'AUDIT_RELEASE_STATUS.csv;../A08-attempt-001/NUMERICAL_AUDIT.json'},{'goal':'Saved-analysis recovery','denominator':'Full newpayload members plus frozen8paths/2refitheads/classifierdraws/LMpanel','status':'PENDING_FRESH_A09_PROOF','available':'Pinned inherited graph; currentremote/local verification','gap':'Current A09newpayload upload/fresh restore must pass','evidence':'RECOVERY_DEPENDENCY_GRAPH.json;BACKUP_VERIFICATION.json'},{'goal':'Full GPU/model recreation','denominator':'Exact checkpoint payloads/runtime plus qualified livebridges','status':'NOT_VERIFIED','available':'Pinned source/env/asset manifests and historical qualification evidence','gap':'Weights/runtime excluded; missing native R3/R5/R2dependencies retained','evidence':'REACQUISITION_MAP.json'},{'goal':'Saliency/perturbation','denominator':'Separately scoped future evaluation','status':'DEFERRED_SEPARATE_APPROVAL','available':'No execution','gap':'Published finite scope and fresh approval required','evidence':'METHODS_AND_LIMITS.md'},{'goal':'Benign relearning trajectories','denominator':'PodB-owned work on separate server','status':'EXTERNAL_OWNER_POD_B','available':'Not a PodA deliverable','gap':'No shared /workspace or reassignment inferred','evidence':'METHODS_AND_LIMITS.md'},{'goal':'Forgetting/unlearning/optimal retain mixture','denominator':'Evidence beyond current benign observational readouts','status':'NOT_ESTABLISHED','available':'Qualified benign measurements and explicit limitations','gap':'No erasure/recovery-resistance/causal-optimum evidence','evidence':'RESULTS.md;METHODS_AND_LIMITS.md'}];table('GOALS_STATUS.csv',goals)
 dictionary='''# Data dictionary and table navigation

## Complete logical evidence

TABLE_INDEX.json pins every physical table by source commit, row count and digest. The logical classifier paired table is the union of four partitions: main A07 16,800 rows; H3 6,720; historical 16,380; new nonadjacent R6−R4 5,460, totaling 45,360 unique scientific keys. A09 uses a lossless H3 canonical-ID derivative; the other three are immutable A08 references. No combined export is needed and no partition is omitted. VERIFIED_METRICS has 27,300 rows; controls 210; primary LM points/paired tables 70/112. All 6,637 coverage keys and explicit 27,300 classifier/70 LM missing-edge keys are retained.

## Keys, types and missingness

Classifier key: original endpoint ID, task, split, canonical representation, CV seed, policy, metric and protocol hash. A paired row adds original reference ID and reference policy. Endpoint aliases never replace content/prediction identity. Controls have no representation axis; task/split/seed/control kind plus exact serialized-head and prediction-file digests disambiguate the alias. LM representation and CV seed are null; its primary unit is checkpoint/task/split, not metric or layer. H3 `test_exploratory` maps to original exposed `test`; dev/test are separate.

CSV empty means JSON null. Estimates/intervals retain full source precision. Row/group/token and resample counts are integers or explicitly unknown. Missing/blocked estimates remain null with a reason; unknown is not zero. Historical marginal CIs absent from source reports remain null with ci_missing_reason; paired CIs remain valid. Higher AUROC/AP/accuracy/balanced accuracy is favorable; lower classifier cross-entropy, causal NLL and perplexity is favorable. Delta direction is target−reference.

## Measurement origin and release

measurement_attempt/lineage describe the original measurement. ingestion_status and A09_ingestion_status describe later reuse; neither establishes checkpoint ancestry. A08 release overlays preserve original producer COMPLETE_UNVERIFIED seals. AUDIT_SCOPE_MATRIX is an immutable pre-execution plan; AUDIT_RELEASE_STATUS is the exact 780-unit current join. Only 60 units required fresh audit refits. All-member archive hashing and sampled restored computation are separate columns.

## Typed hash objects

Classifier prediction_sha256 binds an immutable NPZ file, with the full row key selecting policy/class columns. Current LM hashes bind saved float32 loss/count sufficient-statistics files. Historical LM hashes can bind FEATURE_UNIT_COMPLETE.json, which seals the feature/LM chunks; prediction_locator includes task/split/arm selectors. These are different object types, not interchangeable probability arrays. source_prediction_sha256 retains earlier export pointers where provenance normalization occurred. Original producer/audit/source/draw hashes and locators are preserved.

Control `control-head-sha256:` IDs bind serialized head-file bytes, not tensor/parameter-content identity. `control:composition` and `control:kmer4` are family aliases; they require the full identity tuple. ENDPOINT_ALIAS_MAP records all 480 affected H3 contrast keys, exact head/prediction digests and source identities. PAIRED_CONTRASTS.H3_canonical.v1 retains original_reference_endpoint_id/type, every original numeric/origin field, row order and source hash. Name-only or conflicting joins fail closed.

## Descriptive policies and plot uses

POLICY_POINT_DIFFERENCES contains refit-minus-fixed point summaries with null intervals; no extra inferential family was introduced. Plot-data record IDs identify rendering uses, not new fits: a shared control can occur in both readout panels. Seed spread is not a CI. Layer16 is the 17th block; final norm is a separate hook. R3 remains historical-domain-only and R6−R4 is nonadjacent. Consult RESULTS.md and METHODS_AND_LIMITS.md before interpreting comparisons.

REPORT_ANCHORS_FULL_PRECISION.csv supplements rounded Markdown displays. CLAIMS_TO_EVIDENCE.csv records exact original keys, hashes, status, source commit, measurement origin, uncertainty and limits for every reported scientific row. COUNT_EVIDENCE.json and CLAIM_SCOPE_INDEX.json separately bind coverage/protocol/audit/seed-count statements. No presentation-derived value is a new scientific measurement.
''';publish('DATA_DICTIONARY.md',dictionary)
 print(json.dumps({'status':'PASS','released_row_claims':len(claims),'full_precision_anchor_rows':len(uniq),'table_index_entries':len(tableindex),'figures_reused':len(figures['figures']),'new_scientific_estimates':0}))
if __name__=='__main__':main()
