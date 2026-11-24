# Frozen S04 evaluation protocol

This is a prospective plan for the nine exact checkpoint contents qualified in S03. It contains no new saliency results. Evaluate all six benign tasks, all 26 representations and both readout policies. Use the established dev split as primary evaluation. H3 test is excluded. Keep both noise-5% snapshots as separate descriptive endpoints; do not average them, select a preferred snapshot or interpret them as independent replicates.

## Measurements

`independent_refit` measures task information accessible to the specified newly fitted probe. `fixed_original_base` measures compatibility with the exact original-base scaler and head, applied unchanged. Neither establishes erasure, successful forgetting or biological function. A comparison with the original base is a reference-checkpoint difference; it is not an intervention effect against an assumed immediate parent.

H3 has 11,971 TRAIN and 1,497 dev rows. Each other task has 1,024 TRAIN and 512 dev rows. Splice dev has 512 rows in 511 exact-or-reverse-complement groups. These groups do not establish locus or homology independence. Ordered cohort, class, group and fold identities are bound in `COHORT_REFERENCE_BINDINGS.json`; row metadata remains private.

Extract each candidate/task/split once, collecting all 25 decoder blocks and final normalization together. Reuse those features across CV seeds and policies. Preserve the qualified runtime, masked means, physical batch eight, right padding and filler exclusion. The fixed anchors are zero-based `decoder.layers.16`—the 17th block—and `decoder.final_norm`. Retain every representation.

Use exact inherited TRAIN fold memberships: three folds for H3, five for each other task, and CV seeds `[42,17,1234]`. Fit StandardScaler only within the training fold, then on all TRAIN for the final fit. Use balanced L2 logistic regression, LBFGS, C `[0.1,1,10]`, arithmetic mean fold AUROC selection and exact ties to smaller C. Preserve the recorded 2,000/10,000 iteration convergence procedure. Optimizer RNG 42 is distinct from CV and intervention seeds. Dev outcomes cannot tune this procedure or select checkpoints, layers or seeds.

Report AUROC, AP, accuracy, balanced accuracy and classifier cross-entropy for all layers, seeds and policies. AUROC at the two anchors is the main presentation focus, not a confirmatory family. Seed 42 provides compact examples by this fixed rule; seeds 17 and 1234 provide sensitivity views. Actual-head LM is separate: FP32 per-example loss sums, FP64 corpus aggregation, NLL equal to total valid loss divided by total targets, and PPL equal to its exponential. TRAIN LM is diagnostic; dev LM is primary. There is no per-layer LM, per-CV-seed LM or combined capability score.

## Questions and reporting

| Question | Frozen evidence | Displays | Interpretation limit |
|---|---|---|---|
| Which inputs and comparisons are supported? | Content, provenance, eligibility and coverage | F1; T1, T2, T4, T5 | Nine observed endpoints do not resolve S01 delivery completeness |
| Where is information accessible to the refitted probe? | Complete independent-refit profiles | F2, F3; T2, T3 | Tested probe accessibility does not demonstrate erasure |
| Where does original-base readout compatibility change? | Fixed-base profiles and compatible reference differences | F2, F3; T3 | Reference difference is not an assumed-parent effect |
| How do policies and depth differ? | Full profiles and 324 anchor AUROC policy gaps | F3, F4; T3 | Pointwise intervals do not identify a localized mechanism |
| What accompanies declared method and strength labels? | Every supplied endpoint and its confounders | F5; T1, T5 | Percentages are not calibrated doses; exposure and matching remain unresolved |
| How does actual-head LM compare with classifiers? | 54 primary dev and 54 diagnostic TRAIN LM units | F6; T3, T5 | Separate units and scales; 108 LM reference contrasts are deferred |

`PROTOCOL_FREEZE.json` fixes six figure families and five table families. Every plotted point must resolve to an exact released full-precision row and artifact hash. Track repeated displays of the same row as uses, not additional evidence. Full-grid supplements retain adverse, flat, failed and missing cells. Do not draft favorable results or a novelty claim.

## Comparisons and uncertainty

The prospective admitted families contain 42,120 classifier reference differences, 6,480 anchor-only simple-DNA control differences and 324 signed anchor policy gaps. Admission means compatible specifications, not completed comparisons: future endpoints must satisfy their exact identity and independent-release prerequisites. The policy gap is AUROC(refit) minus AUROC(fixed), with no universal improvement direction and no third training policy. The 42,120 intended immediate-parent contrasts and 108 LM base-reference contrasts remain deferred with null comparators and explicit reasons. New metadata must not silently activate them. There is no all-pairs search.

Reuse the six exact restored dev draw artifacts: 2,000 draws, seed 20261103 and inherited lexical group order. S04 generated no draws. Future paired differences use identical ordered examples/groups and the explicit intersection of endpoint-valid masks. Require every numeric class and quantity-specific finiteness. Record attempted, valid and invalid counts and mask hashes. Recompute LM loss/target ratios within each draw; never average per-example perplexities. Use the inherited linear 2.5/97.5 percentiles. Zero common valid draws means a null interval and blocked affected inferential release, not a zero difference. Do not intersect cohorts or subtract CI endpoints.

Intervals are pointwise, exploratory, unadjusted and conditional on fitted heads. They omit intervention-training variability and unknown biological dependence. CV-seed ranges are sensitivity descriptions, not confidence intervals or independent intervention replicates. Equivalence, noninferiority and preservation-success claims are disabled without a separately authorized prospective margin, family and procedure. An interval crossing zero is inconclusive. Numerical tolerances are separate from statistical uncertainty.

## Verification and execution boundaries

The frozen fresh-refit panel contains 108 anchor and 18 non-anchor units: 126 total, 42 per CV seed, with an exact 21-unit H3 subset and 105 other-task units. It covers 20 representations; all 26 still require exhaustive independent saved-output verification. The audit requires 1,890 initial optimizer calls, separate from 63,180 production calls and convergence retries. Audit fits repeat full TRAIN CV and final fitting independently and never replace production heads.

Every released new probability, point metric, paired draw vector, valid mask and interval needs independent reconstruction. Use absolute tolerances 1e-10 for probabilities and 1e-12 for points/draws/intervals, with rtol zero. Preserve failures, quarantine affected releases and repair through new immutable attempts and scoped release overlays. Never widen gates or replace unfavorable audit units.

Historical A-series outcomes and S03's 12-row TRAIN technical witnesses were already inspected. This freeze does not retrospectively preregister examined comparisons. New saliency production outcomes were not accessed for S04 selection.

Use `code/plan_query.py` to inspect finite metadata selectors; it never launches jobs. Planned specification IDs are not learned parameter or future output hashes. Later producer receipts must join each planned ID to actual input, source, runtime, fitted-parameter and output identities. `RESOURCE_PLAN.json` specifies one GPU worker, separate CPU stages with at most two workers and four BLAS threads each, finite extraction chunks, RAM/disk guards, immutable checkpoints and interruption recovery. Full-cohort throughput, unused account quota and cost remain unknown. The no-deadline amendment remains active.

Read `S05_HANDOFF.json` and `S05_HANDOFF.md` for the exact next scope. Completing S04 does not authorize S05.
