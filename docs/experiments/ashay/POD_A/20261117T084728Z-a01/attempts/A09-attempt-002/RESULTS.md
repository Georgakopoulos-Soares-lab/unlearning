# Readout gains and regressions across the supplied genomic checkpoints

A verified evaluation of the available base/R1/R3/R4/R5/R6 configurations. Available-checkpoint analysis is complete at its declared scope; the full R1–R6 sequence and A04 remain PARTIAL because R2 is missing. This report adds a unified view and portable recovery, with zero new scientific measurements.

## Question and design

How do the supplied cumulative retain configurations change benign classification readouts and actual language-model loss? The planned order adds H3, human TF, core promoter, promoter300, splice and mouse TF. The delivered checkpoints and supplied declarations support descriptive comparisons; unknown lineage/training exposure prevents treating each step as a controlled addition.

A refitted readout learns a small label classifier on frozen TRAIN representations. An unchanged-base readout applies the original base classifier unchanged. They answer different questions about available label discrimination and compatibility with the original function. Actual LM NLL measures saved next-token prediction loss; lower is favorable. Classifier CE and actual LM NLL are different metrics.

## What was available

| Evidence | Available | Planned / remaining |
|---|---:|---|
| Refitted heads |2,808|3,276;468 R2 missing|
| Unchanged-base applications |2,808|Separate 3,276 universe;468 R2 missing|
| LM reporting units |42|36 dev +6 previously examined H3 test;7 R2 missing|
| Shared control heads |36|All reused; no extra fits for repeated displays|
| Eligible adjacent transitions |3|R4−R3, R5−R4, R6−R5|
| R2-dependent contrast slots |0 available|10,920 classifier +28 LM missing|

The integrated release contains 32,760 classifier marginal rows, 73,500 classifier paired rows, 84 LM marginals and 182 LM paired rows. These are reporting rows, not that many heads or independent experiments. [Exact counts](COUNT_EVIDENCE.json),[complete indexed tables](TABLE_INDEX.json),[data dictionary](DATA_DICTIONARY.md).

## Main findings

Classifier displays below use the predeclared seed42 and layer16/final-norm anchors; all other seeds, layers, tasks and policies remain accessible in the exhaustive appendix. Existing intervals are pointwise exploratory, unadjusted and conditional on fitted heads.

### 1. Promoter300 gains depend on readout and representation

Promoter 300, R4 − R3: final-norm AUROC changes by +0.114244 [+0.084795, +0.145774] with a refitted readout and +0.255253 [+0.205964, +0.305867] with the unchanged-base readout. Layer16 changes are +0.013642 [+0.001516, +0.028299] and +0.345678 [+0.284006, +0.410378], respectively.

Exact source rows and full precision: [F1 evidence](CLAIMS_TO_EVIDENCE.csv). Configuration-associated gain; parent/training settings/exposure are not controlled. No attribution to the added source.

### 2. Splice improvement is not uniform across representations

Splice, R5 − R4: layer16 AUROC changes by +0.025240 [+0.000367, +0.051418] refitted and +0.043496 [+0.013195, +0.074566] unchanged-base. At final norm the refitted change is -0.016351 [-0.054497, +0.023364] and the unchanged-base change is -0.019161 [-0.052629, +0.014412]. Both final-norm intervals cross zero.

Exact source rows and full precision: [F2 evidence](CLAIMS_TO_EVIDENCE.csv). Layer dependence; zero-crossing is inconclusive, not equivalence. The barely positive layer16 refit interval is exploratory across a large correlated grid.

### 3. Mouse performance declines from R5 to R6 while remaining above base

Mouse TF0, R6 − R5: final-norm AUROC changes by -0.095802 [-0.139971, -0.050811] refitted and -0.058260 [-0.095603, -0.020690] unchanged-base. Absolute refitted AUROC is base 0.610656, R5 0.844656 and R6 0.748855. R6 remains above base in this displayed setting.

Exact source rows and full precision: [F3 evidence](CLAIMS_TO_EVIDENCE.csv). A decline relative to R5 does not imply decline below base; one checkpoint per configuration.

### 4. Readout policy can change the apparent result

R5 H3 at layer16: refitted AUROC is 0.956395 while the unchanged-base readout gives 0.826049. A new readout can discriminate labels better than the unchanged original-base function on the same saved representation.

Exact source rows and full precision: [F4 evidence](CLAIMS_TO_EVIDENCE.csv). Descriptive policy comparison only. No policy-gap interval, information-erasure, alignment or rotation claim.

### 5. Higher scores can precede supplied-config declaration

Before mouse TF0 is declared in the supplied R5 retain configuration, final-norm R5 − base AUROC is +0.234000 [+0.183358, +0.284065] refitted and +0.217450 [+0.167218, +0.267655] unchanged-base.

Exact source rows and full precision: [F5 evidence](CLAIMS_TO_EVIDENCE.csv). Before declaration does not establish absent exposure, unseen-task generalization or causal transfer.

### 6. Actual LM loss can agree or disagree with readout changes

Actual LM loss gives a distinct view: splice R5 − R4 corpus NLL is -0.097867 [-0.109963, -0.085428] despite inconclusive final-norm classifier change. Mouse R6 − R5 NLL is +0.007193 [+0.003977, +0.010630]. R6 − R5 NLL is positive on each of the six dev tasks, with each existing pointwise interval above zero.

Exact source rows and full precision: [F6 evidence](CLAIMS_TO_EVIDENCE.csv). Lower NLL is favorable. The six correlated intervals do not establish a family-wide test; perplexity transforms the same loss information.

## Matched simple controls and adverse fixed-base results

At layer16/seed42, R5 unchanged-base AUROC is below matched pretrained base on all five non-H3 tasks. This correlated sign count is descriptive and does not show erased information. Each paired estimate and interval is retained in REPORT_DISPLAY_DATA.csv. Refitted probes and final norm show different patterns.

R5’s layer16/seed42 refitted splice AUROC exceeds matched forward4-mers by +0.227831 [+0.176042, +0.279473]. The corresponding core-promoter comparison is +0.026140 [-0.006950, +0.059665] and is inconclusive. All matched composition/4-mer results remain visible at the approved anchors. Repeated guides across layers are descriptive displays, not new all-layer paired control inference.

## Effects on all six tasks

The newly declared task is only one column of the scientific question. [All-task transition anchors](ADJACENT_TASK_ANCHORS.csv) show72 source-linked dev comparisons at seed42:three eligible transitions ×six tasks ×two anchors ×two policies. The current task-entry table retains all CV seeds and separate H3 exploratory test. Before-declaration behavior and already-declared-task changes are reported with actual supplied declaration evidence; realized training exposure stays UNKNOWN. [Absolute task-entry context](TASK_ENTRY_ABSOLUTE_CONTEXT.csv) prevents interpreting a relative decline as a below-base result.

## Figures and full evidence

Four main families emphasize coverage/declarations, task-entry transitions, full-layer readout-policy patterns and actual LM changes. [Main figures and inherited12-family appendix](FIGURE_GALLERY.md). The complete release retains the prior nonadjacent R3−R1 and R6−R4 results as historical comparisons; they are not substitutes for missing adjacent R2 edges.

## Methods, limits and reproducibility

[Methods and interpretation limits](METHODS_AND_LIMITS.md) give the frozen data, scaling, CV, class, metric and resampling conventions. One checkpoint per configuration, unknown training lineage/exposure and the absence of independent checkpoint-training replicates limit causal conclusions. Splice’s barely positive layer16 interval is exploratory; zero-crossing at final norm is inconclusive. H3 test is previously examined and separate from dev.

The original scientific protocol and all earlier measurement bytes are preserved. Original A07 COMPLETE_UNVERIFIED producer status stays in its source rows; the independently verified A08 overlay establishes current release. Historical alias/schema repairs are reused. The table index maps every compact row to the complete immutable original file, CSV line and row digest, without dropping scientific columns.

Source-controlled code, pinned prompts, private dependency identities and safe path translations support saved-analysis restoration. [Recovery dependency graph](RECOVERY_DEPENDENCY_GRAPH.json),[restore instructions](RESTORE.md),[actual fresh consumer check](FRESH_RESTORE_CHECK.json). All new members are checksum-verified; the computational sample is24 saved prediction paths, 60 classifier vectors and6 LM vectors under active producer-path denial. This is not full GPU/runtime reconstruction.

## What remains

R2 needs an exact native/config/tokenizer delivery and qualification under a separate scoped approval. Exact parents, training settings, source/token exposure and evaluation-overlap evidence would be needed for stronger causal interpretation. Biological-label aliases remain unresolved where authoritative metadata is absent. Full GPU reconstruction, perturbation evaluation and Pod B relearning are separate scopes; no automatic next stage follows. [Unsent missing-input draft](MISSING_INPUTS_DRAFT.md).

Available-checkpoint report completion does not complete the missing sequence or establish successful forgetting. No collaborator message was sent.
