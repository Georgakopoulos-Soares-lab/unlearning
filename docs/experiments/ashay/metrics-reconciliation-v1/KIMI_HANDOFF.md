# Kimi handoff: genomic unlearning

## Executive summary

No new biological results were produced by reconciliation or this handoff. The strongest available local evidence is saved metric JSON/CSV and aggregate collaborator logs. Historical benign predictions/features/probes are absent locally, but pinned historical recovery receipts identify backups. Recovering those benign artifacts could permit prediction-level verification on CPU without new GPU inference. A matched pretrained/post-model benign comparison remains blocked on checkpoint and loading provenance. Do not construct, run or troubleshoot an HVUE human-host-tropism predictor; review aggregate results only.

The active local reconciliation branch contains commit59de97d (full SHA below). It has not been pushed. Preserve the other worktrees, including uncommitted retain preparation. Numerical evidence and useful benign experimental progress take priority; no LaTeX/presentation work.

## Project and team

Research asks whether a genomic model's measured capabilities change after unlearning while benign capabilities are preserved. A probe decrease alone cannot establish durable information removal. Pretrained baselines, matched parent/post evaluation and proposed progressively diverse benign retain sets are separate stages.

Ashay completed the independent benign reference work and committed to sharing results/configuration/branch with Sayyed. Sayyed develops the BioNeMo pipeline and reported provisional GradDiff concerns and a four-nucleotide MaxEnt variant; the proposed division has him developing two noise ideas with H3 retention and Ashay potentially adding incremental retain sets. Aris proposed pretrained classification/causal-LM baselines, matched post evaluation and diverse retention. Ilias Georgakopoulos-Soares is a collaborator; no specific implementation assignment is established here. These roles follow v10 handoff notes, not verified speaker diarization. H3+promoter+splice was a candidate, not a finalized meeting decision; no calendar deadline is inferred.

## Repository and current state

Research: https://github.com/Georgakopoulos-Soares-lab/unlearning
Prompts: https://github.com/ashay-sriv-06/test-prompts-push

AGENTS.md is applicable. Current explicit authorization for the isolated reconciliation branch supersedes its older writable-path restriction. Preserve historical results, no reset/clean/force-push/shutdown. Do not access test contents beyond specifically authorized benign saved-artifact work. No GPU work in this handoff. Historical prescribed runtime/data paths are currently absent.

Observed branches (fresh origin fetch; branch names do not prove ownership):

| Branch | Purpose | Observed SHA | Local path | Evidence role |
|---|---|---|---|---|
| experiments-ashay | three-task pilot | 06fb273ae0cf3578f4c79d3c97052b93c4f6300a | not checked out | historical; remote fetched |
| experiments-ashay-benign-v2 | six-task extension | 5bb08f502d6739e6ce84f2fe77799d4f4ba71cc3 | not checked out | historical; remote fetched |
| experiments-ashay-sayyed-base-v1 | supplied-H3 baseline/follow-up | 89c7e934fb025fe1048d9e06dd0fb039211fe46a | /workspace/unlearning-codex | historical clean checkout; remote fetched |
| bionemo | collaborator implementation/logs | b90fc1853d1d3be79922a98a2649c91c89716637 | not checked out | source and aggregate evidence; remote fetched |
| experiments-ashay-metrics-reconciliation-v1 | numerical inventory | 59de97dd5faac3e275709ee7fdb5420c2d5f0397 | /workspace/wt-metrics-reconciliation-v1 | active local; remote branch not found by ls-remote |
| experiments-ashay-codex-benign-v1 | offline retain preparation | 89c7e93 | /workspace/wt-codex-benign-v1 | local only, three untracked paths preserved |

Observation time UTC: 2026-11-03T12:03:41.486587+00:00. Remote URL checked through git remote -v. Prompts main resolved to ec87e8fde8cd38462dfafdab36d07642b71f5fbb; local prompts HEAD may remain older because fetch does not check out files. v11 receipt correctly pins9c9d13ac1a5fe3a68dcadb1de6d76ba1b1805a2b. v12 verbatim/receipt are adjacent. No remote push is inferred from a local commit.

## Experiment history and evidence

1. **Pilot:** frozen original Evo2-1B,256 train/128 dev per H3/promoter/splice; mean-pooled blocks7/15, logistic C chosen on dev. Test not scored. Dev AUROC block7/block15: H3 .850183/.839927; promoter .973877/.959717; splice macro OVR .778737/.767814. Historical report only: docs/experiments/ashay/core_pilot_report.md. Execution3d3da6bce62a19819a59ba063c11d9a3ac082a70. No new reproduction here.
2. **Extension:**1024 train/512 dev per six tasks; original Evo2-1B blocks7/15/final RMSNorm, composition and normalized overlapping forward4-mer controls. Balanced L2 logistic, fold-local scaling, five training-only grouped CV folds, C=.1/1/10. Execution GPU927651a106b7b6c7375be9f11e11c4a76b956a03; CPU source timing is mixed (dirty06fb273 source later e81b8b4); see extension/SESSION_HANDOFF.md. Saved-result verification historically checked identities, predictions/scalers and NLL; not repeated now. Paired2000-resample intervals condition on fitted models/split and unknown dependence remains. Historical pilot rows were reused; sample-size/selection changes are not model effects.
3. **Supplied H3:**11971 train/1497 dev/1497 test. Original arcinstitute/evo2_1b_base@2279e1df422c991037470302360edd40d0d2ea1e, backend53f195997257c56c00e5ef8d33a54f5baad143a6. Mean final RMSNorm1920. CPU MLP LayerNorm→Linear1920→GELU→Dropout.1→Linear2;300 steps,batch8,replacement sampling,seed42,LR.001,warmup20/cosine; every50-step checkpoint, dev-selected250; threshold.5. Execution735394ea52ed1c08c6e034d4b025813b16516fcc. Historical verification reconstructed saved heads/identities and metrics, not all GPU features. This session checked NLL=sum/count and PPL=exp(NLL), six equalities across three splits.
4. **Follow-up:**same cached H3 features, balanced logistic with three identical training-only exact/RC-grouped folds, local scaling,C=.1/1/10, all-train refit. Post-hoc after original test known. Execution d64c943ab272120a82c67a04a40da1501cfdcf69; seed sensitivity4f1d9c566bf7dcc13e6bf6a87d29392a2b4a1280. Original selected MLP saw2000 draws/1842 unique rows(15.39%); extracting all rows did not imply gradient exposure. Additional seeds17/1234 AUROC .820964/.840581, original42 .831817; no winner replacement. Historical verification reconstructed probes/heads and paired resamples; absent local payload prevents repeating it now.
5. **Reconciliation:**59de97d collected192 CSV data rows, excluding header:120 extension +30 follow-up +18 supplied-H3 +18 pilot +6 BioNeMo aggregate.174 was before adding18 pilot rows. Each row is one metric/configuration, not an independent experiment; pilot includes C candidates. No new predictions, fitting or biological measurements. SESSION_HANDOFF.md's174 count is a stale intermediate statement; CSV count192 was directly checked. Only aggregate arithmetic was newly recomputed.

## Important results and status

Six-task dev AUROC; source docs/experiments/ashay/extension/classification_metrics.csv and MEETING_RESULTS.md. All rows: **Historical report only** (saved aggregate CSV read; no local predictions).

| Task | Composition |4-mer|Block7|Block15|Final norm|Verification status|
|---|---:|---:|---:|---:|---:|---|
| gue_emp_h3 | 0.8313 | 0.8549 | 0.9275 | 0.9201 | 0.8193 | Historical report only |
| gue_prom_300_all | 0.6394 | 0.8921 | 0.9687 | 0.9576 | 0.9290 | Historical report only |
| gue_splice_reconstructed | 0.5029 | 0.5717 | 0.8038 | 0.8021 | 0.6667 | Historical report only |
| gue_prom_core_all | 0.7527 | 0.8353 | 0.8480 | 0.8408 | 0.8228 | Historical report only |
| gue_tf_0 | 0.5201 | 0.7896 | 0.8001 | 0.8187 | 0.7236 | Historical report only |
| gue_mouse_0 | 0.5267 | 0.7885 | 0.8992 | 0.8562 | 0.7998 | Historical report only |

Supplied-H3 test; sources docs/experiments/ashay/sayyed-base/metrics.json and sayyed-followup/{supplemental_metrics.json,FOLLOWUP_RESULTS.md}. Intervals are historical2000 paired sequence-bootstrap percentile intervals conditional on fitted models/split; exclude training/selection uncertainty, unknown homology dependence and multiplicity correction.

| Readout | AUROC [95% interval] | Accuracy | Verification status |
|---|---|---:|---|
| Original MLP | .8318 [.8097,.8519] | .7027 | Historical report only |
| Final-norm logistic | .8469 [.8272,.8655] | .7622 | Historical report only |
| Composition | .8054 [.7815,.8267] | .7388 | Historical report only |
|4-mer | .8955 [.8794,.9114] | .8210 | Historical report only |
|Evo2 logistic minus4-mer AUROC|-.0485 [-.0657,-.0322]|—|Historical report only|
|Evo2 logistic minus composition AUROC|+.0416 [.0240,.0602]|—|Historical report only|
|Original MLP minus logistic AUROC|-.0151 [-.0258,-.0047]|—|Historical report only|
|Causal LM NLL|1.2557225272213952|—|Recomputed from aggregate sufficient statistics|
|LM perplexity|3.5103737989026302|—|Recomputed from aggregate sufficient statistics|

NLL uses saved938028.4950019639 loss sum /747003 valid next-token targets. PPL is exp(NLL). Arithmetic agreement is not prediction-level reproduction, checkpoint validation or GPU replication. Classifier CE is a different quantity. No metric here has status “Recomputed from available predictions”; those payloads are absent.

Collaborator aggregate logs: bionemo:evo2_classifier_official/evo2_classifier_official/evaluations/ at the observed bionemo SHA above.

| Task/model label |N|AUROC|Accuracy|Source basename|Verification status|
|---|---:|---:|---:|---|---|
|H3 base|1497|.7667|.6941|emp_h3_base_eval_11278119.out|Historical report only|
|HVUE base|51187|.7439|.9648|hvue_base_eval_11270906.out|Historical report only|
|HVUE MaxEnt|51187|.6498|.9647|hvue_maxent_eval_11286039.out|Historical report only|

HVUE prevalence .0353 makes majority accuracy approximately .9647 (rounded reported values only). AUROC must not be called accuracy. Both aggregate base and MaxEnt logs exist, but exact checkpoint/split pairing and probe policy remain unverified. Meeting-reported H3 layer16 post AUROC .9561 lacks a clear matched base layer16 value (source v10_PROMPT in other worktree); this is participant-reported only. Do not infer a missing counterpart or an Ashay HVUE benchmark completion.

## Comparability and scientific limits

Original Vortex backend and BioNeMo conversion are not automatically equivalent. Historical BioNeMo references converted base iter1, head iter300 and nucleotide_fast_tokenizer_512, all cluster paths rather than local assets. Our selected head250 differs from300, seed42 differs from1234, LR curves differ, right-padding multiple16 differs from fixed1000, backend/precision differ, decoder hook equivalence to post-final RMSNorm is unestablished. A missing-head warning alone does not prove subsequent head overlay failed. Detailed sources: sayyed-followup/COMPARABILITY.md and MATCHED_H3_HANDOFF.md.

Within-protocol readout/control comparisons and same-protocol six-task dev contrasts are descriptive supported analyses. Cross-backend/pre-post subtraction is unsupported without immutable actual parent/post identities, load/conversion/tokenizer provenance and identical benign rows. Fixed base-trained probes test transfer in a common coordinate system; independently refitted probes test accessible information after readout adaptation. Report both separately. Unknown exposure is not proof of no contamination. Exact/RC duplicate checks do not establish homology independence. Follow-up and reused known test analyses are exploratory. Keep historical MaxEnt, later four-nucleotide modified MaxEnt and provisional GradDiff distinct; no lower probe score proves knowledge removal.

## Artifact/recovery inventory

All repository-relative files below resolve in the active worktree unless explicitly marked otherwise.

| Needed asset | Location / identity | Classification |
|---|---|---|
|Source/configuration|benign_pilot/, scripts/sayyed/, configs/|Present locally and checked|
|Metric files|extension/classification_metrics.csv; sayyed-base/metrics.json; sayyed-followup/supplemental_metrics.json, under docs/experiments/ashay/|Present locally and checked|
|Split manifest|historical run supplied-H3 subset manifest SHA de2c348126fa84771ceeff38225703231848ac860f8b59a3ed41d9eb0b3f0938|Referenced in a verified historical backup receipt|
|Benign predictions|parent H3 run and follow-up supplement|Referenced in a verified historical backup receipt|
|Benign features/probes|same parent/supplement|Referenced in a verified historical backup receipt|
|Parent/post-model weights and loader bundle|original parent identity documented, converted/post bytes absent|Referenced but currently inaccessible|
|Current runtime/data/ledger|/workspace/venvs/evo2-pilot; /workspace/data/gue/GUE.zip; /workspace/meeting-artifacts/evo2-pilot.gpu-budget.json|Not located|
|Recovery receipts|sayyed-followup/recovery_chain.json, backup_receipt.json; sayyed-base/backup_receipt.json|Present locally and checked|

Private HF dataset: ashay-sriv/undo-evo2-pilot-backup-20261020. Restore parent first, then dependent supplement into fresh staging after safe-member/hash checks; never overwrite historical payloads.

|Order|Archive|Pinned revision|Expected SHA256|
|---|---|---|---|
|1|sayyed-base-20261026-v1-recovery.tar.gz|117c01edd97d595c68bd04e9d28f3c4c4e9852f1|af4dd220e8b9968ca4acde3850fc66e9c57755b78885309ea77f1375fc44edb8|
|2|sayyed-h3-followup-20261027T001154Z-supplement.tar.gz|dfae7d29f0550430d1c64605501f403445059ff6|19bc96a4513d37f56f77ece0dda189734e92a8c0165dac35aa636f91134b97f5|

Latest receipts record173 parent +95 supplement payload checks historically. Older pending wording in reports/source_receipt.json is superseded by recovery_chain.json. No current HF access/download verification was attempted. Absent locally does not mean lost. Recovery could enable CPU metric/prediction/probe reconstruction without new inference; use recorded environment locks and do not refit merely to reconstruct saved outputs. No large downloads needed for this handoff.

## Implementation map

|Stage|Actual entry points|Inputs → outputs / dependencies|
|---|---|---|
|Configuration|configs/benign_pilot.json, benign_extension.json, evo2_backend_identity.json|task/split/identity policy; pinned original backend|
|Loading|benign_pilot/data.py; scripts/sayyed/prepare_h3.py|qualified archive + config → ID/hash-bearing manifests, overlap audit; NumPy/sklearn|
|Extraction|benign_pilot/run.py, extension_gpu.py; scripts/sayyed/run_h3.py|manifest/model/runtime → cached features/causal losses; Torch/Evo2/CUDA|
|Probe fitting|benign_pilot/probes.py, extension.py; scripts/sayyed/h3_followup.py, h3_seed_sensitivity.py|cached train features/folds → fitted heads, CV and probabilities; sklearn/joblib/Torch|
|Metrics|benign_pilot/metrics.py; extension.py; h3_followup.py|labels/probabilities/loss/count pairs → separate classifier and LM metrics/paired intervals|
|Verification|scripts/verify_benign_extension.py; scripts/sayyed/verify_h3.py, verify_h3_followup.py|saved manifests/pipelines/predictions → identity and reconstruction checks; may hardcode historical run paths|
|Packaging|scripts/package_benign_extension.py; scripts/sayyed/package_h3.py, package_h3_followup.py|explicit payload/source lists → checksummed archives; do not rerun for its own sake|

These interfaces are source-inspected or historical documented execution, not commands newly executed here. Do not launch scripts blindly: verifier/package scripts may hardcode absent paths or write output. No historical environment was reconstructed. This session successfully used git inspection, stdlib CSV/JSON counting and process/GPU queries only. Reconciliation successfully checked aggregate NLL arithmetic. pytest was absent during older retain preparation; direct synthetic invariants passed instead.

Uncommitted retain prototype: /workspace/wt-codex-benign-v1/benign_pilot/retain.py with tests/test_retain.py and docs/experiments/ashay/codex-retain-v1/. Deterministic no-replacement whole-row sampling; rejects held-out rows/duplicates, reports nucleotide-length proxy budgets and shortfalls. Not biological preparation or packed-token accounting. BioNeMo dual_dataset_provider.py wraps shorter datasets modulo and consumes packed retain_* tensors; no adapter contract has been agreed. Missing held-out audit must block biological use.

## Next work ordered by value

|Task / question|Prerequisites|Available / missing|Compute|Deliverable / completion criterion|
|---|---|---|---|---|
|Recover saved benign payload: do metrics reconstruct?|Authorized private dataset access; safe fresh staging|Pinned revisions/hashes present; current accessible payload/auth missing|CPU/download only|parent then supplement hashes and relevant payloads checked; saved prediction metrics reconstructed without refitting|
|Establish matched readiness: are models comparable?|actual parent/post checkpoint+loader/tokenizer/config and split identity|reference protocol present; post bundle and exact parent bytes missing|CPU metadata first|explicit ready/blocked gate with immutable identities|
|Matched benign evaluation: what changes under common protocol?|ready gate; frozen fixed/refitted policies, margins and budget; compatible runtime|historical protocol available; assets/runtime/ledger missing|GPU gate then measured bounded inference; CPU probes|paired same-row AUROC/AP/NLL and uncertainty, provenance/actual compute recorded|
|Incremental retention: does diversity preserve benign capability?|evaluation prerequisites and team mixture/interface agreement|offline prototype present; mixture proportions/packed accounting missing|CPU preparation first; no training authorized here|qualified train-only manifest plus actual tokenizer/loss-mask accounting and shortfalls|

Historical H3 inference288.9 GPU seconds/model is a recorded measurement; ~578 seconds for comparable two-model extraction is only an estimate and excludes setup/all-layer changes. Restore and reconcile authentic ledger (last historical868.753177/7200s,inactive), never reset. No established local executable budget means finish CPU work and present measured estimate before GPU launch. Do not repeat broad audits or backups without a concrete discrepancy.

## Minimal team request (draft only)

- Sayyed: accessible hash-pinned post checkpoint and its actual pretrained parent, method/iteration, tokenizer/config, supported loader/runtime and conversion lineage. Unblocks compatibility/readiness gate.
- Sayyed/Aris: confirm exact benign manifest/labels and training-exposure hashes, or explicitly mark exposure unknown. Unblocks valid matching/overlap interpretation.
- For recovery: provide authorized access to the existing private backup through secure authentication; no chat tokens. Unblocks CPU saved-prediction verification.
- After evaluation readiness: agree first benign mixture/proportions and retain adapter. Historical head/sampler is unnecessary unless exact historical reproduction is requested.

No messages sent. No experiment jobs observed; nvidia-smi returned no compute applications. Service/shell/Codex processes remain active. This handoff used0 GPU seconds and created no biological results. No Pod shutdown.
