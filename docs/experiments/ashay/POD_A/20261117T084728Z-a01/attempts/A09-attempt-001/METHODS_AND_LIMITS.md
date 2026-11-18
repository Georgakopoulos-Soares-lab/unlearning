# Methods and interpretation limits

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
