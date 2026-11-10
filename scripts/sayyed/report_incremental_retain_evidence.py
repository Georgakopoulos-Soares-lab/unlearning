from pathlib import Path
import json,csv,hashlib,shutil,datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scripts.sayyed.incremental_retain_plan import TASKS,STAGES
r=Path('/workspace/meeting-artifacts/incremental-retain-eval-v1');w=Path('/workspace/wt-incremental-retain-eval');d=w/'docs/experiments/ashay/incremental-retain-eval-v1';n=Path('/workspace/meeting-artifacts/multiretain-comparison-v1');now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def save(p,j):p.write_text(json.dumps(j,indent=2)+'\n')
def rows(p):return list(csv.DictReader(p.open()))
def one(data,**kw):
 found=[x for x in data if all(x[k]==str(v) for k,v in kw.items())];assert len(found)==1,(kw,len(found));return found[0]
a=rows(r/'tables/STAGE_ANCHORS_AUROC.csv');c=rows(r/'tables/REUSED_CONTRASTS.csv');lm=rows(r/'tables/LM_METRICS.csv');lc=rows(r/'tables/LM_CONTRASTS.csv')
def point(stage,task,layer='decoder_layer_16',policy='refit'):
 return one(a,stage=stage,task=task,layer=layer,cv_seed=42,policy=policy,split='test' if task=='emp_H3' else 'dev')['value']
def contrast(task,stage='R3',reference='R1',layer='decoder_layer_16',policy='new_refit'):
 return one(c,stage=stage,reference_stage=reference,task=task,split='test' if task=='emp_H3' else 'dev',layer=layer,cv_seed=42,policy=policy,metric='auroc')
def ci(x):return f"{float(x['difference']):+.6f} [{float(x['ci_low']):+.6f}, {float(x['ci_high']):+.6f}]"
def table(layer='decoder_layer_16',policy='refit'):
 text='| Task/split | Base | R1 | R3 | R3 − R1 [95% CI] | R3 − base [95% CI] | R3 config declaration |\n|---|---:|---:|---:|---:|---:|---|\n'
 for t in TASKS:
  pp='new_refit' if policy=='refit' else 'new_fixed_base';vals=[f'{float(point(s,t,layer,policy)):.6f}' for s in ['base','R1','R3']];text+='| '+t+'/'+('test' if t=='emp_H3' else 'dev')+' | '+' | '.join(vals)+' | '+ci(contrast(t,layer=layer,policy=pp))+' | '+ci(contrast(t,reference='base',layer=layer,policy=pp))+' | '+('included' if t in STAGES['R3'] else 'not listed; exposure unknown')+' |\n'
 return text
# New visualization of historical data and explicit missingness, no stage interpolation.
stages=['base',*STAGES];data=np.full((7,6),np.nan)
for i,s in enumerate(stages):
 for j,t in enumerate(TASKS):
  v=point(s,t)
  if v:data[i,j]=float(v)
cmap=plt.colormaps['viridis'].copy();cmap.set_bad('#eeeeee');fig,ax=plt.subplots(figsize=(13,7));im=ax.imshow(np.ma.masked_invalid(data),vmin=0,vmax=1,cmap=cmap,aspect='auto')
labels=['H3 / reused test','human TF / reused dev','core promoter / reused dev','promoter / reused dev','splice macroOVR / reused dev','mouse TF / reused dev'];ax.set_xticks(range(6),labels,rotation=15,ha='right');ax.set_yticks(range(7),['base (reference)','R1 (provisional)','R2 (awaiting delivery)','R3 (provisional)','R4 (awaiting delivery)','R5 (awaiting delivery)','R6 (awaiting delivery)'])
for i,s in enumerate(stages):
 for j,t in enumerate(TASKS):
  if np.isfinite(data[i,j]):ax.text(j,i,f'{data[i,j]:.4f}'+('\nconfig retain' if s!='base' and t in STAGES[s] else ''),ha='center',va='center',fontsize=9,color='black')
  else:ax.text(j,i,'NO CHECKPOINT',ha='center',va='center',fontsize=8,color='#555555')
ax.set_title('Reused block16 / seed42 refitted AUROC; missing stages remain blank');fig.colorbar(im,ax=ax,label='AUROC (existing measurements)');fig.text(.5,-.02,'R1/R3 aliases reflect config declarations, not verified exposure. No adjacent-stage effect is estimable. No interpolation, overall score or new measurements.',ha='center',fontsize=9)
fig.tight_layout()
for ext in ['png','pdf','svg']:fig.savefig(r/'figures'/('stage_coverage.'+ext),dpi=180,bbox_inches='tight')
plt.close(fig)
# Make exact smoke/runtime gates explicit before any future candidate scoring.
p=load(r/'COMPARISON_PROTOCOL.json');p['bounded_training_smoke']=load(n/'SMOKE_PLAN.json');p['bounded_training_smoke']['arms']=['each new qualified candidate'];p['bounded_training_smoke']['reference_smoke_plan_sha256']=sha(n/'SMOKE_PLAN.json');p['numeric_audit_tolerances']={'saved_probability_max_abs':1e-10,'metric_and_bootstrap_max_abs':1e-12};p['metadata_clarified_utc']=now;p['metadata_clarification']='Explicit unchanged smoke/audit references; no new heldout inference has occurred.';save(r/'COMPARISON_PROTOCOL.json',p);save(r/'PROTOCOL_FROZEN.json',dict(status='FROZEN_BEFORE_NEW_MODEL_SCORING',utc=now,protocol_sha256=sha(r/'COMPARISON_PROTOCOL.json'),new_heldout_scoring=False));shutil.copy2(r/'COMPARISON_PROTOCOL.json',d/'COMPARISON_PROTOCOL.json');shutil.copy2(r/'PROTOCOL_FROZEN.json',d/'PROTOCOL_FROZEN.json')
text='''# Incremental retain evaluation: qualified continuation and delivery status

**No new model measurements were possible in this continuation.** The live supplied locations still contain the completed H3-only and three-source-config checkpoints; no identifiable R2/R4/R5/R6 or offered perturbation delivery was found. The registry/protocol/reporting handoff is complete; the expanded model matrix remains pending delivery. No models were generated and no completed arm was rerun. GPU use and new fits are both **zero**.

## Evidence reused and stage identities

The validated implementation is pinned to c79ab07e763a9754c68fdaf7d0730d8458f508dc. Existing base, H3-only and three-source results were verified again against990sealed receipts/15678files, including exact cohorts, heads/predictions/bootstrap/LM records and36controls. The original independent numerical audits are reused, not counted as new measurements or GPU replication. Source SHA/frozen runtime/hook/pooling/batching identities match.

R1 is the provisional alias for original `h3_only_maxent`, iteration2000, config declares H3. R3 provisionally aliases `supplied_three_source_config_iter2151`, config declares H3/humanTF0/core-promoter. Its shard SHA256 is a401c810f6479c090de26550b785e22a50280d15f4ef920f1f237b4a41df3ac0. Original identifiers and all per-arm tokenizer/checkpoint identities remain in CHECKPOINT_REGISTRY.json. These aliases establish neither realized exposure nor sequential fine-tuning. The R3 pointer still reads2151 and freshly retrieved R1/R3 configs match recorded SHA256 values. No large remote weights were downloaded or freshly hashed; live IDs/sizes/timestamps alone are not weight-identity proof.

| Stage | Agreed cumulative retain set | Delivery/result status | Completed task/layer/seed units reused |
|---|---|---|---:|
| base | Separate pretrained reference | complete |468|
| R1 | H3 | provisional alias, complete |468|
| R2 | R1 + human TF | awaiting checkpoint |0|
| R3 | R2 + core promoter | provisional config alias, complete |468|
| R4 | R3 + promoter | awaiting checkpoint |0|
| R5 | R4 + splice | awaiting checkpoint |0|
| R6 | R5 + mouse TF | awaiting checkpoint |0|

This is the November10 cumulative sequence, not the older promoter/splice-first proposal. Expected remaining incremental units:1872 (four missing checkpoints×468), not a completed measurement count. Sayyed’s two-day delivery expectation is context, not proof of arrival. No combination search or stage×perturbation grid is authorized or constructed.

## Stage-by-task anchors and declared membership

All values below are **reused**. Block16 is zero-based decoder.layers.16, the17th block; seed42 is the historical display anchor, not a favorable selected seed. R2/R4/R5/R6 values are absent in the machine tables rather than interpolated. R3−R1 is explicitly **nonadjacent**: both humanTF and core-promoter are planned additions across that gap. It cannot identify either task’s individual effect. H3 uses reused test; the other tasks use reused official dev. AUROC positive is numerical class1; splice is sorted-class macroOVR. Conditional95% intervals use2000paired exact/RC-group draws, pointwise and unadjusted.

'''+table()+'''
![Stage availability and historical block16 scores](figures/stage_coverage.png)

The gray rows have no delivered checkpoint or score. “Config retain” means a source appears in the checkpoint configuration, not known row exposure. Every task/stage has separate planned role, actual config declaration and unknown-exposure columns in [STAGE_ANCHORS.csv](tables/STAGE_ANCHORS.csv). For missing artifacts, actual declarations remain unresolved even though the meeting plan is known. Fixed-base entries for base alias the same saved base predictions, with no duplicate fit.

## Adjacent-stage comparisons

| Required contrast | Missing endpoint(s) | Result |
|---|---|---|
| R2−R1 | R2 | pending |
| R3−R2 | R2 | pending |
| R4−R3 | R4 | pending |
| R5−R4 | R4,R5 | pending |
| R6−R5 | R5,R6 | pending |

No adjacent-stage difference is currently estimable. The exact historical R1−base, R3−base and nonadjacent R3−R1 differences remain in [REUSED_CONTRASTS.csv](tables/REUSED_CONTRASTS.csv), with source file/row and original contrast/policy names. No interval endpoints are averaged.

## Scientific questions answerable now

- **Newly included tasks:** relative to R1, R3 config adds both humanTF and core promoter. At block16, core-promoter refit AUROC increases +0.033236 [+0.005188,+0.062930]; humanTF +0.026812 [−0.006171,+0.060078] is uncertain. Neither is an adjacent single-task effect.
- **Previously retained H3:** block16 R3−R1 is −0.001778 [−0.007604,+0.003956]; final norm +0.019844 [+0.008910,+0.031323]. This does not prove preservation/equivalence without an agreed margin.
- **Tasks not in R3’s declaration:** splice improves +0.050243 [+0.018868,+0.082140] and mouseTF +0.044168 [+0.015725,+0.073613] at block16 versus R1. Splice still has a negative point gap to base (−0.015513 [−0.048207,+0.020142]); mouseTF’s point reaches base (+0.001313 [−0.027421,+0.029687]), without establishing equivalence. Promoter +0.002792 [−0.008700,+0.014209] versus R1 remains uncertain. Not in the declared mixture does not mean unseen.
- **Layer distribution:** existing R3−R1 seed42 refit signs are positive at24/26core-promoter,25/26humanTF,19/26splice,23/26mouseTF,17/26promoter and14/26H3-test representations. These correlated descriptive counts are not family-wide significance claims. Splice final-norm R3−R1 is −0.009713 [−0.052729,+0.035328], preserving an unfavorable/inconclusive outcome rather than selecting a peak layer.

![Reused all-layer dev refitted profiles](figures/dev_refit.png)

Three original model identifiers, six reused dev cohorts, all26representations. Lines=mean across CVseeds17/42/1234; bars=observed seed minimum/maximum, faint points=seeds. These are seed variation, not confidence intervals or intervention-training replications. R1/R3 aliases are provisional. H3 test remains separate below.

![Reused H3 test profiles](figures/h3_test_refit.png)

Reused H3 test only, no pooling with other-task dev. All seed-specific values and all five metrics remain in [REUSED_METRICS.csv](tables/REUSED_METRICS.csv).

## Fixed-base transfer and final normalization

A fixed-base probe applies the original base scaler/head unchanged. Better refitting does not imply transferable coordinates or recovered biological understanding. Block16 fixed-base values and conditional contrasts:

'''+table(policy='fixed_base')+'''
The new/refitted versus transferred discrepancy remains substantial on several tasks, including promoter, splice and humanTF. Readout degradation does not prove information removal. Final-normalization refits are also retained rather than replaced by a selected best layer:

'''+table(layer='final_norm')+'''
![Reused fixed-base dev profiles](figures/dev_fixed_base.png)

Same all-layer/three-seed summary; bars remain seed ranges, not confidence intervals. No new classifiers or control heads were fitted.

## Controls and within-task LM loss

Matched composition and normalized-forward4mer controls are reused once per task/seed at block16 and final norm. [control_contrasts.csv](tables/control_contrasts.csv) contains the R3 comparisons; [BASE_R1_CONTROL_CONTRASTS.csv](tables/BASE_R1_CONTROL_CONTRASTS.csv) preserves prior base/R1 comparisons. R3 block16 refits exceed the4mer control at all six seed42 task anchors under the original pointwise conditional intervals. These are comparisons with those particular controls, not proof of biological understanding or capacity-matched model superiority.

LM loss is one actual output-head statistic: total next-token loss divided by valid targets, then PPL=exp(NLL). It is not classifier cross-entropy or per-hidden-layer perplexity. Exact three-arm within-task values/intervals are reused in [LM_METRICS.csv](tables/LM_METRICS.csv) and [LM_CONTRASTS.csv](tables/LM_CONTRASTS.csv). On H3/test, base/R1/R3 causal NLL are1.310650139/1.455799276/1.221998229; R3−R1 is−0.233801 [−0.252156,−0.215530]. Thus LM loss improves while H3 block16 refit AUROC has a small negative, uncertain change. All five other tasks have favorable R3−R1 block16 AUROC and NLL point directions; this is a within-task observation, not an overall-capability score. Final-norm classification can differ while LM loss remains one output-head readout.

## Perturbation versus parent

No identifiable supplied perturbation checkpoint was found in the refreshed roots/relevant model folders or scoped accessible-folder name search. The two offers are placeholder registry entries awaiting delivery, not assigned Gaussian/reinitialization labels. Meeting discussion of5percent is not a verified selected fraction. No immediate parent, stage, intervention seed/settings or pre/post training is established. Therefore no perturbation-versus-parent measurements or causal claims exist. Historical GradDiff originals/v2 and LoRA checkpoint directories are explicitly excluded as substitutes. Unrelated hazardous benchmark contents were not read or executed.

## Qualification limits and next owners

R1/R3 parent/conversion hashes, executed objective/loader revision, actual sampling proportions, unique/repeated rows, per-source retain tokens and authorized-cohort exposure remain incomplete. Training steps and LR schedules differ (delivered R12000 versus R32151; planned decay schedules differ). A path containing base and a MaxEnt log tag do not resolve exact lineage/objective. Missing manifests mean exposure unknown, not clean. Exact/RC groups do not establish homology or biological independence. CVseeds are not independent intervention replications. No preservation margins or multiplicity correction were invented. Benign measurements alone do not establish successful unlearning.

**Sayyed next:** supply R2/R4/R5/R6 checkpoint folders with intended iteration, complete shard inventory and config/tokenizer; supply both offered perturbations with actual intervention type, parent hash/stage, fraction, seed/settings and any pre/post training. Also provide parent/conversion hashes, executed objective/loader revision, source/retain manifests and per-source sampling/token/exposure accounting. Do not ask Ashay to create these interventions.

**Ashay next:** qualify each identified delivery, freeze its identity and pass strict native loading plus unchanged training-only physical8 gates. Evaluate available incremental stages in agreed order (missing earlier stage need not block a later descriptive arm), completing H3/audit before other five; then qualified perturbations against actual available parent. Reuse verified caches/controls, fit only new heads, independently verify new outputs and recover them privately. No indefinite polling is running.

## Verification, delivery and recovery

[COMPARISON_PROTOCOL.json](COMPARISON_PROTOCOL.json), [CHECKPOINT_REGISTRY.json](CHECKPOINT_REGISTRY.json) and [COVERAGE.json](COVERAGE.json) preserve all states and identities. New checks are deterministic stage/membership/adjacency tests and source-table/annotation/figure consistency; they are not new scientific measurements. Full prior numerical audits remain the basis for reused scores. New GPU-stage use0seconds, new fits0, new predictions0. Resource receipts distinguish this continuation from historical375.8GPU-stage seconds for R3.

New outputs form a small dependent supplement. Restore prior base/R1, controls and R3 archives at their pinned private revisions before the new preparation bundle; [RESTORE_DEPENDENCIES.json](RESTORE_DEPENDENCIES.json) records hashes and order. Model weights and installed runtime are excluded. Final backup/restore and branch receipts postdate packaging and will be preserved in Git. No collaborator messages, main merge, force push, intervention training or Pod shutdown occurred.
'''
(d/'RESULTS.md').write_text(text)
(d/'COMPARABILITY_AND_EXPOSURE.md').write_text('The stage sequence is a meeting-defined cumulative retain-set design, not evidence of sequential fine-tuning. R1/R3 are provisional aliases preserving original identities. R3-minus-R1 adds two declared tasks across missingR2, so it is nonadjacent. Parent identity, objective/loader execution, source versions, realized mixture, per-source unique/repeated rows/tokens and cohort exposure remain unknown. Different delivered steps2000/2151 and planned LR schedules contradict equal-budget attribution. No source-genome/homology groups or biological numeric-class mapping were newly inferred. Missing configs/manifests/stages remain unknown; no interpolation or exposed-row pruning. Prior qualification: e95380d22b982a8fa5d71e4aaf7f8553010b6408; completed descriptive study c79ab07e763a9754c68fdaf7d0730d8458f508dc. No finalized data-identities-v1 or retain-preparation-v1 output found in inspected worktrees or fetched matching branch names; parallel work is not consumed as final evidence.\n')
(d/'TEAM_UPDATE_DRAFT.md').write_text('UNSENT DRAFT — no message sent.\n\nCompleted the v13 delivery audit and continuation protocol on experiments-ashay-incremental-retain-eval-v1. Reused verified base/R1/R3 results; zero new model measurements. R2/R4/R5/R6 and both offered perturbations were not identified in supplied locations. All adjacent-stage comparisons remain pending; R3−R1 is nonadjacent. At historical block16/seed42 refit, splice +0.050243 [+0.018868,+0.082140] and mouseTF +0.044168 [+0.015725,+0.073613] versus R1; H3−0.001778 [−0.007604,+0.003956]. These are descriptive reused evidence, not diversity/forgetting proof.\n\nReport: https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/experiments-ashay-incremental-retain-eval-v1/docs/experiments/ashay/incremental-retain-eval-v1/RESULTS.md\nRegistry: https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/experiments-ashay-incremental-retain-eval-v1/docs/experiments/ashay/incremental-retain-eval-v1/CHECKPOINT_REGISTRY.json\n\nSayyed: please supply exact R2/R4/R5/R6 folders/iterations/shards/configs/tokenizers and perturbation checkpoints with actual type, parent hash/stage, fraction, seed and pre/post training; add executed objective/loader revision and retain-source/exposure accounting. Ashay will qualify and evaluate available deliveries in agreed order with the unchanged pipeline. No intervention generation or combination sweeps.\n')
(d/'RESUME.md').write_text('Resume only after a supplied candidate becomes identifiable; do not poll indefinitely. Record exact Drive IDs, intended iteration, all shard/config/tokenizer hashes and stage membership without selecting by score. Keep realized exposure/parent/objective facts separate. Use a new candidate run/cache identity and append/update the registry before scoring. Frozen protocol preserves the validated c79ab07 implementation; no speculative executor for missing models was added. Reuse scripts.sayyed.extract_multiretain_fixed, fit_multiretain_new_arm and verify_multiretain_new_arm for the qualified native path; bind each new protocol/registry to the candidate and exact old cohorts. Read the completed unit contracts and run training-only smoke via verify_new_arm_smoke; physical8/logical8,logical1,repeat12train rows, original atol1e-4/rtol1e-5. No heldout scoring until strict loading/smoke pass. Complete H3 extraction/fit/audit first, then other5, only new heads with exact old grouped CVfolds and base heads. Extend contrast interfaces only for actual available endpoints; independently validate direct paired draws rather than promoting nonadjacent comparisons. Never reuse the R3 cache as a new R2/R4 candidate. Perturbations require actual parent identity and a separate descriptive/causal decision. Keep GPU locks/historical ledger and other agents intact. Stop again with exact missing inputs if no delivery.\n')
for p in (r/'figures').glob('stage_coverage.*'):shutil.copy2(p,d/'figures'/p.name)
save(r/'FIGURE_INPUTS.json',dict(stage_coverage_source_sha256=sha(r/'tables/STAGE_ANCHORS_AUROC.csv'),display={'layer':'decoder_layer_16','cv_seed':42,'policy':'refit'},new_measurements=False,figures=[dict(path=str(p),sha256=sha(p)) for p in sorted((r/'figures').glob('*'))]))
print('Report and coverage visualization written; all numerical measurements explicitly reused.',flush=True)
