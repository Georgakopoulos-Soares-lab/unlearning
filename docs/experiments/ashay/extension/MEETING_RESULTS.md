# Evo2 frozen benign extension: meeting results

Expanded protocol: 1024 official train / 512 official dev examples per GUE task. Selection: five fixed grouped training-only CV folds; balanced L2 logistic regression, fold-local scaling, C=.1/1/10. AUROC uses numeric class1 for binary tasks and macro OVR for splice. No untouched test data.

| Task | Evidence | Composition | 4-mer | Block7 | Block15 | Final RMSNorm | Dev NLL | Dev perplexity |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| gue_emp_h3 | NEW_GPU_COMPLETE + NEW_CPU_COMPLETE | 0.8313 | 0.8549 | 0.9275 | 0.9201 | 0.8193 | 1.253251 | 3.501707 |
| gue_prom_300_all | NEW_GPU_COMPLETE + NEW_CPU_COMPLETE | 0.6394 | 0.8921 | 0.9687 | 0.9576 | 0.9290 | 1.312282 | 3.714643 |
| gue_splice_reconstructed | NEW_GPU_COMPLETE + NEW_CPU_COMPLETE | 0.5029 | 0.5717 | 0.8038 | 0.8021 | 0.6667 | 1.144710 | 3.141532 |
| gue_prom_core_all | NEW_GPU_COMPLETE + NEW_CPU_COMPLETE | 0.7527 | 0.8353 | 0.8480 | 0.8408 | 0.8228 | 1.348162 | 3.850342 |
| gue_tf_0 | NEW_GPU_COMPLETE + NEW_CPU_COMPLETE | 0.5201 | 0.7896 | 0.8001 | 0.8187 | 0.7236 | 1.234731 | 3.437453 |
| gue_mouse_0 | NEW_GPU_COMPLETE + NEW_CPU_COMPLETE | 0.5267 | 0.7885 | 0.8992 | 0.8562 | 0.7998 | 1.340800 | 3.822099 |

Historical identity anchors: 6 examples; all passed=True. Every original layer feature and per-example NLL delta was exactly zero. This checks six selected anchors, not independent regeneration of all historical features.

## Counts and causal likelihood

| Task | Train/dev class counts | Train/dev targets | Train NLL | Dev NLL | Train perplexity | Dev perplexity |
|---|---|---|---:|---:|---:|---:|
| gue_emp_h3 | {'0': 498, '1': 526}/{'0': 251, '1': 261} | 510976/255488 | 1.252124 | 1.253251 | 3.497763 | 3.501707 |
| gue_prom_300_all | {'0': 512, '1': 512}/{'0': 257, '1': 255} | 306176/153088 | 1.312075 | 1.312282 | 3.713872 | 3.714643 |
| gue_splice_reconstructed | {'0': 226, '1': 224, '2': 574}/{'0': 112, '1': 111, '2': 289} | 408576/204288 | 1.148705 | 1.144710 | 3.154106 | 3.141532 |
| gue_prom_core_all | {'0': 513, '1': 511}/{'0': 254, '1': 258} | 70656/35328 | 1.352681 | 1.348162 | 3.867783 | 3.850342 |
| gue_tf_0 | {'0': 513, '1': 511}/{'0': 247, '1': 265} | 102400/51200 | 1.227615 | 1.234731 | 3.413079 | 3.437453 |
| gue_mouse_0 | {'0': 510, '1': 514}/{'0': 262, '1': 250} | 102400/51200 | 1.347762 | 1.340800 | 3.848804 | 3.822099 |

## Primary paired dev contrasts

Block7 minus 4-mer AUROC, 2000 paired bootstrap replicates. Intervals are pointwise exploratory and conditional on fitted models, exclude fitting/selection uncertainty and simultaneous coverage. Exact/RC duplicate groups used; no biological groups supplied. Unknown dependence remains. Missing-class resamples excluded and counted in saved contrasts.json.

| Task | Difference | 95% interval |
|---|---:|---|
| gue_emp_h3 | +0.0726 | [+0.0451, +0.1010] |
| gue_prom_300_all | +0.0766 | [+0.0525, +0.1016] |
| gue_splice_reconstructed | +0.2321 | [+0.1837, +0.2828] |
| gue_prom_core_all | +0.0128 | [-0.0211, +0.0485] |
| gue_tf_0 | +0.0105 | [-0.0252, +0.0460] |
| gue_mouse_0 | +0.1107 | [+0.0715, +0.1508] |

## Cached historical-row comparison

NEW_CPU_COMPLETE: both saved representations refit under NEW training-only selection. These rows/features inherit original manifest-order/producer/provenance association, since old arrays lack embedded IDs. This is not GPU reproduction. Original dev-selected scores are preserved separately.

| Task (256/128) | Composition | 4-mer | Block7 | Block15 | Block7–4mer interval |
|---|---:|---:|---:|---:|---|
| gue_emp_h3 | 0.8286 | 0.8361 | 0.8486 | 0.8381 | +0.0125 [-0.0582, +0.0803] |
| gue_prom_300_all | 0.6072 | 0.8784 | 0.9707 | 0.9565 | +0.0923 [+0.0457, +0.1490] |
| gue_splice_reconstructed | 0.5743 | 0.5191 | 0.7787 | 0.7678 | +0.2596 [+0.1641, +0.3515] |

## Evidence and interpretation

HISTORICAL_REUSED: original three-task NLL and dev-selected probe evidence remains unchanged. The historical C-grid has block7 > block15 at all three C values for each of the three tasks (nine correlated comparisons, not independent replications); see historical_c_sensitivity.csv.

The cached-row matched comparison shows a small uncertain block7 advantage over 4-mer on H3, and larger positive advantages on promoter and splice. Block7-minus-block15 cached intervals include zero on all three tasks; the direction alone does not establish a reliable layer advantage. 4-mer underperforms composition on cached splice, so a more elaborate simple feature is not uniformly better. The one fixed shuffled-training-label diagnostic repeats selection; it is a sanity check, not a formal test. H3 composition gave a suspiciously high 0.8112 shuffled-label dev AUROC despite shuffled-label mean CV 0.4483. The investigation independently reproduced that fit using only the same shuffled train labels (52.34% agreement with originals), recorded small coefficients, and found 0.9304 probability correlation with the ordinary composition fit. This is consistent with chance alignment to a low-dimensional composition signal, not proof of leakage or its absence. No alternative seed was searched; shuffled labels/model and investigation are saved. Full metrics include chosen C, every fold/candidate AUROC, convergence warnings, class counts, fixed-threshold accuracy/balanced accuracy/MCC, fitted pipelines and ID-aligned dev probabilities.

All original 256/128 rows are included in their corresponding expanded subsets. Differences in sample size or selection policy are not model effects. Numeric biological class mappings and tf/0/mouse/0 exact experiment aliases remain unverified; see TASK_QUALIFICATION.md. Source task definitions are known, but no biological meaning is inferred from integer IDs. No biological groups/homology independence is established. Cross-task NLL does not rank task capability. Simple controls outperforming a probe would not establish no model information, biological mechanism, or leakage.

## Explicit outstanding work

| Requested item | Status |
|---|---|
| vGUE viral genome identification | BLOCKED: labeled immutable task table, source/group/split/license metadata and full-genome protocol missing |
| vGUE viral-read identification | BLOCKED: labeled read/source-genome manifest, generation/split/license metadata missing |
| Corrected GradDiff comparison | BLOCKED: immutable corrected checkpoint, parent/loader/tokenizer/conversion/exposure handoff absent |

Aris Step1 is incomplete while viral tasks remain blocked. No GradDiff/unlearning or hazardous-knowledge removal result is claimed. Broader retain training is NOT_RUN and requires a subsequent team decision.

Next recommended experiment: obtain the corrected checkpoint handoff and exposure manifests; establish compatible base/post backend and evaluate both fixed base probes and separately train-CV-refitted probes on these same eligible rows, with paired token-weighted NLL and AUROC changes. Team questions: exact viral identification dataset tables/source groups and genome protocol; authoritative numeric class map and TF aliases; corrected checkpoint owner/iteration; qualified training exposure; agreed preservation margins.

## Verbal update (not sent)

We added train-only matched controls to the old pilot and expanded the six benign GUE tasks. The old-row results show that the probe advantage depends on the task: it is uncertain for H3 and clearer for promoter and splice; layer differences remain uncertain. These are exploratory official-dev measurements, with reused examples and incomplete biological grouping. Viral identification is still blocked on qualified data, and the corrected GradDiff checkpoint handoff is still needed. No unlearning claim is supported.

Artifact root: /workspace/meeting-artifacts/evo2-extension-20261021T0942. CPU source timing limitations are recorded in cpu_execution_identity.json; later delivery commits must not be relabeled as execution. Saved figures: baseline_controls.png, paired_differences.png and cached_paired_differences.png. Complete predictions/probes/CV scores are in expanded_matched/<task>; per-example likelihoods and identity-bearing features are in <task>. Source hashes and execution revision: extraction_identity.json when GPU extraction exists; later documentation commits are separate. Prompt receipt pins v5.txt at d158a3666c72a212c6c1cbc5b9c264f3c6dd3687, SHA256 0688904d96748076127f5ad9842cc35ca7ad39a4ebfc6fcdae1fbbda8c7c3ad4. Old HF backup remains verified; NEW supplement status belongs in backup_receipt.json and must not be confused with it.
