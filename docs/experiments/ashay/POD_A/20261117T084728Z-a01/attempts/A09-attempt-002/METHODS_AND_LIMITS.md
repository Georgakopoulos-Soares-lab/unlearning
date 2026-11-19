# Methods and interpretation limits

This report reuses the released evaluation of pretrained base and supplied R1/R3/R4/R5/R6 checkpoints on six frozen benign sequence-classification tasks. R2 remains missing. One checkpoint per supplied configuration was available; configuration order does not prove sequential initialization or matched training.

## Data and representations

H3 uses 11,971 TRAIN, 1,497 dev and 1,497 previously examined test examples. Other tasks use1,024 TRAIN and512 official dev examples each. Splice has 511 exact/RC groups in 512 dev rows. Numeric labels and sorted class mappings are preserved; unresolved biological aliases are not guessed. Exact/RC groups do not establish locus or homology independence. All 25 decoder blocks, indices0–24, and the separate final-norm representation have width1920. Layer16 is the zero-based17th block. Qualified historical extraction used physical batch 8, explicit filler exclusion, masked pooling and documented BF16/FP32 behavior; no extraction occurred in A09.

## Readouts, controls and actual language-model measurements

Refitted readouts are balanced L2 logistic models selected using frozen TRAIN-only folds: H3 three folds, other tasks five; CV seeds 42,17,1234; C grid0.1/1/10; mean fold AUROC with exact ties to smaller C. Fold-local scaling and final all-TRAIN scaling/fitting remain frozen. The unchanged-base policy applies the original pretrained-base scaler/head without recentering, recalibration or replacement. Composition and normalized forward4-mer controls are reused, with paired inference restricted to the two established anchors.

Binary positive class is numerical 1 and threshold0.5. Splice uses sorted classes 0/1/2, argmax, macro one-vs-rest AUROC, mean classwise AP and macro recall. Five classifier metrics are retained, including classifier cross-entropy with the original float64-epsilon clipping. Actual LM NLL uses the qualified autoregressive head, summed saved loss divided by valid-target count; perplexity is exp(corpus NLL). It is not average sequence perplexity or a hidden-layer classifier score. “Causal head” describes next-token prediction, not causal intervention evidence. No across-task loss average or invented capability score is used.

## Uncertainty and seed interpretation

Existing 2,000 exact/RC-group bootstrap draws, seed 20261103, and common class-completeness masks are preserved. Target minus matched reference is formed within each draw before the frozen2.5/97.5 percentiles. Intervals are pointwise, exploratory, unadjusted and conditional on fitted heads. They omit checkpoint-training variability. An interval crossing zero is inconclusive, not equivalence, preservation or noninferiority. Barely zero-excluding intervals are not confirmatory evidence after examining a large correlated grid.

Three CV seeds describe probe-selection sensitivity, not three independently trained checkpoints. In the 130 R5 other-five task/representation groups, 124 have identical final parameter hashes across CV seeds. Different frozen folds often selected the same C with a deterministic final optimizer. Identical functions are retained as distinct documented seed records, without counting them as independent replications. Policy point gaps carry no newly introduced interval.

## Eligibility, exposure and causal limits

R3 native identity and TRAIN bridge support exactly 1,092 approved classifier andseven LM saved-output domains. Global held-out runtime equality and causal training comparability were not established. Historical empty content fields remain intact under a separate effective tensor-identity overlay. R5 is fully evaluated and independently released within the available scope; it is not awaiting download or a new bridge.

Planned inclusion, supplied-config declarations, version identity and realized sampled exposure remain separate. Before declaration does not mean unexposed or unseen. Missing exact parents, objective implementation, steps/LR/token budgets and actual row/source consumption prevent attributing a performance difference to the added retain task. R2 would fill coverage but would not remove these design confounders.

The study does not establish optimal retain mixtures, successful forgetting, resistance to relearning, biological function or a universally best checkpoint. Perturbations require a separate scope; relearning is owned by Pod B. Full GPU/model/runtime recreation remains untested. Saved-artifact recovery is unrelated to recovering a model’s forgotten capability.

## Independent checks and recovery scope

Current A08 independently checked 390 R5 other-five units/780 probability paths, 3,900 marginal and8,400 paired vectors, with24.6million attempted saved values. Its prospective30 full-CV-plus-final audit refits used480 solver calls with zero retries; these are audit artifacts, not replacement production heads. Historical R4/R6 and six R5 H3 audit refits were reused. New A08 comparisons comprise16,380 classifier and70 LM rows, with independent numerical routes. Numerical tolerances remain absolute1e-10 for probabilities and 1e-12 for points/draws/intervals, rtol0.

A09 introduces no new measurements, fits, forwards, bootstrap draws or inference families. It integrates released rows, checks presentation joins and protects a fresh report archive. The declared new CPU consumer panel reconstructs24 saved R5 prediction/metric paths, 60 already-saved classifier vectors andsix LM vectors, with producer paths denied. Actual outcomes and maxima are in FRESH_RESTORE_CHECK.json. All new archive members receive byte checks. Inherited fresh-recovery proofs are explicitly reused and immutable remote availability rechecked; no unchanged multi-gigabyte history is repacked or gratuitously downloaded. Full GPU recreation is excluded.

Two early A08 supervisor bookkeeping errors left exact child exit codes unavailable. Those fields remain null; complete source-bound output seals, numerical checks and later process inspection support acceptance. Diagnostics and earlier attempts are preserved. No clean exit code or original/rental start, rate or cost is invented.
