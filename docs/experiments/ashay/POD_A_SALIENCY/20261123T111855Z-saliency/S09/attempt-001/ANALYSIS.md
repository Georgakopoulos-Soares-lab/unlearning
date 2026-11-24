# Benign accessibility and original-readout compatibility across supplied saliency checkpoints

The supplied checkpoints retain substantial task discrimination under TRAIN-refitted linear readouts, while the unchanged original readouts often behave differently. The clearest recurring feature is the separation between these two questions: a label can remain accessible after refitting even when the original scaler/head transfers poorly. This analysis establishes differences relative to the qualified original base and simple DNA controls. It does not identify immediate parents or establish a perturbation mechanism.

## What was compared and how to read it

Nine separately identified supplied endpoints, six benign tasks, all 25 decoder-block outputs plus final normalization, three frozen CV partitions and both readout policies are retained. No new models were fitted and no inference was run in S09. The refitted policy uses the already qualified TRAIN-only classifier selection/fitting; the fixed policy applies the exact original scaler/head unchanged. These answer linear task accessibility and original-readout compatibility, respectively.

The frozen inferential scope is 42,120 base-reference comparisons, 6,480 anchor DNA-control comparisons and 324 anchor AUROC policy gaps. Every difference is target minus reference within the exact same 2,000 original exact/RC-group draws, restricted to the explicit intersection of endpoint validity masks. Intervals are linear 2.5th/97.5th percentiles: **95% pointwise exploratory conditional intervals**, conditional on fitted readouts and these cohorts. They omit fitted-head and intervention-training uncertainty and give no familywise guarantee. Positive AUROC/AP/accuracy/balanced-accuracy differences favor the candidate; negative classifier-CE differences favor it. A signed policy gap has no universal desirable ordering.

All 42,228 deferred specifications retain their exact frozen keys and reasons: 42,120 immediate-parent comparisons and 108 LM-base comparisons. Original-base differences are never relabeled parent effects. Deferred means unresolved, not zero. The reporting organization was fixed after prior S05–S08 outcome exposure and is not represented as preregistered.

## Readout policy and representation profiles

Refitted AUROC exceeded unchanged-original-base AUROC in 324 of all 324 frozen anchor comparisons; paired point gaps ranged from 0.034778 to 0.503517. 3 of these pointwise intervals include zero. The smallest and largest gap records are linked by exact IDs in the machine-readable ledger; a positive point gap alone is not a causal interpretation.

For refitted AUROC, block16 (the seventeenth decoder block) exceeded final normalization in 162 of 162 supplied-checkpoint/task/CV-seed combinations. This is descriptive, with no new layer-to-layer inferential test. The all-layer atlas provides context: block16 was emphasized prospectively, but these data do not establish it as an optimal representation. All earlier and later layers remain available, including adverse/flat outcomes.

The following AUROC ranges cover all nine endpoints and all three seeds at each anchor (27 points per cell). They are descriptive observed ranges, not confidence intervals.

| Task | Readout | Block16 AUROC range | Final-normalization AUROC range |
|---|---|---|---|
| emp_H3 | independent_refit | 0.950469–0.955745 | 0.826702–0.844653 |
| emp_H3 | fixed_original_base | 0.827991–0.833874 | 0.725857–0.805337 |
| gue_tf_0 | independent_refit | 0.794531–0.800810 | 0.627805–0.646948 |
| gue_tf_0 | fixed_original_base | 0.642594–0.689833 | 0.459232–0.485677 |
| gue_prom_core_all | independent_refit | 0.838995–0.849020 | 0.766221–0.780642 |
| gue_prom_core_all | fixed_original_base | 0.476744–0.520845 | 0.557041–0.619178 |
| gue_prom_300_all | independent_refit | 0.963775–0.966217 | 0.735515–0.820096 |
| gue_prom_300_all | fixed_original_base | 0.461402–0.547448 | 0.335698–0.387106 |
| gue_splice_reconstructed | independent_refit | 0.714984–0.732211 | 0.589752–0.614352 |
| gue_splice_reconstructed | fixed_original_base | 0.527435–0.540307 | 0.540911–0.561017 |
| gue_mouse_0 | independent_refit | 0.821359–0.835527 | 0.640870–0.659298 |
| gue_mouse_0 | fixed_original_base | 0.593130–0.616992 | 0.559206–0.611969 |

The particularly weak fixed-readout behavior on some promoter and TF endpoints coexists with stronger refitted ranking. This is evidence about these specific fitted readouts. It does not establish removal of all task information, or explain which saliency construction produced the pattern. See the [full profile/heatmap atlas](FIGURE_GALLERY.md) and exact ranges in ANCHOR_AUROC_SUMMARY.jsonl.

## Comparisons with original-base and DNA references

Original-base comparisons were mixed across the complete grid: 10,227 candidate-minus-base points favored the candidate under their own metric direction, 31,775 were adverse and 118 were exactly equal, out of 42,120 comparisons. These counts combine different metrics only as a coverage summary, not as a capability score. The following summary shows all-layer AUROC comparisons by task and policy; every cell contains 702 comparisons (nine endpoints × 26 representations × three seeds). “CI above/below” refers only to the pointwise paired conditional interval, without full-grid adjustment.

| Task | Readout | Candidate point above base | Below | Equal | CI above zero | CI below zero | CI includes zero |
|---|---|---:|---:|---:|---:|---:|---:|
| emp_H3 | independent_refit | 546 | 156 | 0 | 457 | 42 | 203 |
| emp_H3 | fixed_original_base | 0 | 702 | 0 | 0 | 690 | 12 |
| gue_tf_0 | independent_refit | 202 | 500 | 0 | 0 | 3 | 699 |
| gue_tf_0 | fixed_original_base | 0 | 702 | 0 | 0 | 681 | 21 |
| gue_prom_core_all | independent_refit | 608 | 94 | 0 | 105 | 0 | 597 |
| gue_prom_core_all | fixed_original_base | 24 | 678 | 0 | 0 | 639 | 63 |
| gue_prom_300_all | independent_refit | 525 | 177 | 0 | 96 | 42 | 564 |
| gue_prom_300_all | fixed_original_base | 0 | 702 | 0 | 0 | 690 | 12 |
| gue_splice_reconstructed | independent_refit | 0 | 702 | 0 | 0 | 444 | 258 |
| gue_splice_reconstructed | fixed_original_base | 0 | 702 | 0 | 0 | 702 | 0 |
| gue_mouse_0 | independent_refit | 177 | 525 | 0 | 15 | 324 | 363 |
| gue_mouse_0 | fixed_original_base | 3 | 699 | 0 | 0 | 636 | 66 |

DNA comparisons use the exact shared composition and normalized forward-4mer heads and probabilities, with row/class/group/original-draw compatibility verified. They are restricted to the two frozen anchors and must not be extrapolated to all layers. The full table includes all five metrics and both references.

| Task | Readout | DNA AUROC points above control | Below | Equal | Paired CI above | Below | Includes zero |
|---|---|---:|---:|---:|---:|---:|---:|
| emp_H3 | independent_refit | 81 | 27 | 0 | 57 | 27 | 24 |
| emp_H3 | fixed_original_base | 27 | 81 | 0 | 0 | 69 | 39 |
| gue_tf_0 | independent_refit | 81 | 27 | 0 | 54 | 27 | 27 |
| gue_tf_0 | fixed_original_base | 27 | 81 | 0 | 27 | 60 | 21 |
| gue_prom_core_all | independent_refit | 81 | 27 | 0 | 27 | 27 | 54 |
| gue_prom_core_all | fixed_original_base | 0 | 108 | 0 | 0 | 108 | 0 |
| gue_prom_300_all | independent_refit | 81 | 27 | 0 | 81 | 27 | 0 |
| gue_prom_300_all | fixed_original_base | 0 | 108 | 0 | 0 | 108 | 0 |
| gue_splice_reconstructed | independent_refit | 108 | 0 | 0 | 81 | 0 | 27 |
| gue_splice_reconstructed | fixed_original_base | 54 | 54 | 0 | 21 | 0 | 87 |
| gue_mouse_0 | independent_refit | 81 | 27 | 0 | 66 | 27 | 15 |
| gue_mouse_0 | fixed_original_base | 54 | 54 | 0 | 33 | 54 | 21 |

Each DNA cell covers 108 comparisons: nine endpoints × two anchors × three seeds × two controls. Counts do not imply independent control replication: shared references are reused, with their exact identities retained. Exceeding a simple DNA control does not establish biological understanding. [Anchor forests](FIGURE_GALLERY.md) retain reference-specific effects, all seeds and uncertainty; COMPARISON_SUMMARY.jsonl and per-task CONTRASTS.jsonl retain every full-precision result.

## Metric disagreement and adverse outcomes

At 220 of 8,424 candidate/task/representation/seed/policy cells, candidate AUROC was above the base point estimate while classifier cross-entropy was worse (higher). Ranking and probability quality therefore cannot be used interchangeably. The complete search, including counterexamples to this particular disagreement pattern, is in the claim ledger. Accuracy and balanced accuracy use frozen decisions, AUROC/AP assess ranking, and classifier cross-entropy assesses predicted probabilities; none can substitute for the others.

One adverse disagreement example is ['candidate_07', 'gue_prom_core_all', 'decoder.layers.0', 42, 'fixed_original_base']: AUROC difference 0.000671 with classifier-CE difference +0.244165 nats/example. Both exact contrast IDs are recorded in METRIC_DISAGREEMENT.jsonl. This example was selected to illustrate the adverse loss tail after an exhaustive search, not as a preregistered primary endpoint.

S08’s saved-output diagnostics cover 7,020 non-H3 prediction paths: 279 binary paths had balanced accuracy exactly one-half and a single predicted class; 6,359 paths contained at least one confident error with probability above 0.99; 591 contained clipped true-class probabilities. These are **counts of affected paths**, not percentages of misclassified examples. They help explain why ranking and threshold/loss behavior can diverge and are not new S09 model tests.

## Seed sensitivity and supplied-checkpoint interpretation

Across 14,040 descriptive three-seed metric groups, 13,640 had exactly coincident point values; 28 of 14,040 three-seed base-comparison groups changed favorable point direction across seeds. Coincident fits are not independent intervention evidence. S08 separately established identical selected C, final parameter content, saved predictions and serialized heads for 1,104 of 1,170 non-H3 candidate/task/representation groups. This is an expected consequence when different CV partitions select the same regularization and the final fit uses the same all-TRAIN rows; counting the repeated predictions as independent training evidence would overstate replication. Full seed ranges and direction exceptions are exposed rather than selecting the most favorable partition.

Every supplied endpoint remains separate, including noise-5% step2000 and step2151. Labels and observed steps are shown together; nominal percentages are not treated as a calibrated common dose axis. Unknown parent, perturbation law/mask, realized dose and training exposure prevent causal strength or method rankings. The atlas contains no all-pairs checkpoint tests, fitted dose-response curve, new correlation or synthetic across-task loss score.

## LM sequence prediction, kept separate

All 108 previously verified LM units (216 NLL/perplexity marginal records) are reused at their actual checkpoint/task/split identities. DEV panels are primary and have the existing conditional intervals; TRAIN panels are diagnostics without invented intervals. They are not replicated across probe layers or CV seeds, and the 108 deferred exact LM-base comparisons remain inactive. Classifier CE is nats per labeled example; LM NLL is nats per valid next-token target. Perplexity is the exponential of aggregated LM NLL, not another classifier metric.

| Task | DEV NLL range over nine supplied endpoints | DEV perplexity range |
|---|---:|---:|
| emp_H3 | 1.261821–1.407216 | 3.531848–4.084568 |
| gue_tf_0 | 1.341846–1.347291 | 3.826101–3.846989 |
| gue_prom_core_all | 1.388296–1.392800 | 4.008016–4.026109 |
| gue_prom_300_all | 1.386966–1.450487 | 4.002689–4.265191 |
| gue_splice_reconstructed | 1.298836–1.344685 | 3.665030–3.836976 |
| gue_mouse_0 | 1.384227–1.394259 | 3.991738–4.031987 |

These are descriptive supplied-endpoint ranges, not matched-parent effects or checkpoint-pair significance tests. Exact sample/group/target counts and source hashes remain in LM_MARGINALS_REUSED.jsonl.

## Verification, reproducibility and interpretation limits

Every admitted specification passed production versus separate scalar reconstruction for its point, explicit mask intersection, entire draw vector and interval under absolute tolerance 1e-12, relative tolerance zero. No new draws, fitting, calibration, inference, test access or forget evaluation were performed. Reference probabilities were independently recomputed through rank and pairwise weighted metric implementations. Both implementations share Python/NumPy, frozen metric definitions and source evidence; this checks numerical implementation, not independent biological replication. The isolated plotting environment is separate from the unchanged NumPy/SciPy/scikit-learn scientific runtime.

The whole delivery inventory remains PARTIAL. Immediate parents, saliency masks/construction, realized doses, exposure and intervention seeds remain incompletely documented. Exact/RC bootstrap groups do not establish locus/homology independence. Candidate05’s original-upload privacy remains historically unknown. Matched collaborator forget aggregates are a separate S10 dependency; benign measurements alone cannot establish successful forgetting or selective unlearning. R2 is excluded and Pod B relearning remains separate. No-deadline continuity is preserved.

## Plain-language reading and next dependency

We asked whether simple trained readouts can recover six benign labels at every representation, and whether the original readouts still work unchanged. Refitting usually gives a different—and at the frozen anchors consistently higher—ranking score than retaining the original readout, while comparisons to original-base and simple DNA references remain metric- and task-dependent. The complete atlas makes those differences and their exceptions visible. Conditional bootstrap intervals describe the sampled cohorts and fixed fitted heads; they do not establish causal intervention effects, biological independence or forgetting. S10 must separately qualify collaborator-provided aggregate results against exact checkpoint, task, split, metric, denominator, protocol and reference identities before any joint interpretation. S10 is not executed here.
