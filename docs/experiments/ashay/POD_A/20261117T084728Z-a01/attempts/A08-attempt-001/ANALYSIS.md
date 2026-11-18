# A08 verified analysis of the qualified endpoints

A08 independently verifies the available R4/R6 readout grid. **The full project remains partial.** R2 and R5 contribute 936 pending head cells; the R3 live bridge is absent; A04 remains PARTIAL. No missing checkpoint was interpolated or admitted.

The new audit covered 780 A07 units, 1,560 saved probability paths, 7,800 marginal and 16,800 paired metric distributions: 49.2 million attempted draw values. Maximum probability residual was 0, point-metric residual 3.5527136788005009e-15, per-draw residual 7.7715611723760958e-16, and interval residual 4.3021142204224816e-16. Frozen gates remain 1e-10 for probabilities and 1e-12 for metrics/draws/intervals. The prospective 60-unit refit panel passed: 960 planned optimizer fits, 960 actual including 0 recorded retries. These are audit fits, not new production heads. All original A06/A07 seals remain unchanged.

## Readout behavior at the predeclared displays

The following official-dev AUROCs use **final norm, seed 42**. These were predeclared displays, not selected winners. Full 26-representation/three-seed/five-metric results and block 16 (17th block) anchors are retained in the CSVs and figures. Brackets are pointwise 95% exact/RC-group bootstrap intervals conditional on fitted heads.

| Task | R4 refit | R4 original-base | R6 refit | R6 original-base | R6−R4 refit |
|---|---:|---:|---:|---:|---:|
| H3 | 0.848612 [0.828583, 0.867407] | 0.818880 [0.797094, 0.838641] | 0.856180 [0.836292, 0.874041] | 0.841188 [0.820556, 0.860358] | 0.007569 [0.001719, 0.013396] |
| Human TF | 0.705340 [0.660109, 0.749089] | 0.480620 [0.427147, 0.533411] | 0.747430 [0.704124, 0.788767] | 0.502559 [0.453307, 0.553096] | 0.042090 [0.004364, 0.079292] |
| Core promoter | 0.869957 [0.840497, 0.900748] | 0.748291 [0.706201, 0.789237] | 0.822148 [0.786803, 0.858348] | 0.700116 [0.657496, 0.744747] | -0.047809 [-0.072749, -0.023016] |
| Promoter 300 | 0.950576 [0.930174, 0.967166] | 0.911849 [0.886630, 0.936220] | 0.954131 [0.934221, 0.970816] | 0.900542 [0.874164, 0.926071] | 0.003555 [-0.008065, 0.015516] |
| Splice | 0.636111 [0.596829, 0.676052] | 0.550882 [0.512699, 0.588459] | 0.616920 [0.576949, 0.654428] | 0.554077 [0.515457, 0.593659] | -0.019191 [-0.058705, 0.019562] |
| Mouse TF | 0.840748 [0.806041, 0.873727] | 0.760443 [0.717153, 0.798795] | 0.748855 [0.706616, 0.790170] | 0.769847 [0.728080, 0.808380] | -0.091893 [-0.132478, -0.051743] |

Human TF dev,finalnorm, seed 42: R4 refit AUROC 0.705340 [0.660109, 0.749089], fixed AUROC 0.480620 [0.427147, 0.533411], base AUROC 0.679673. Different readout behavior is compatible with changed feature/readout relationships; does not prove erasure, understanding or forgetting.

Core promoter dev,finalnorm, seed 42 R4-minus-base AUROC: refit 0.108573 [0.070237, 0.150233]; fixed -0.013093 [-0.052640, 0.025376]. Readout policy matters; these are predeclared pointwise displays, not best-layer/seed selection or family-wide evidence.

At the six predeclared final norm / seed 42 dev refit-AUROC displays, R6-minus-R4 point deltas are positive in 3 tasks and negative in 3; intervals and all layers/seeds remain in full tables. Descriptive anchor signs are not family-wide significance; R6-R4 is nonadjacent and cannot isolate splice or mouse addition.

Human TF R4 corpus NLL 1.198158 [1.176056, 1.217985] versus base 1.343778, while R4 fixed AUROC is 0.480620 [0.427147, 0.533411] versus base 0.679673. Within-task likelihood and linear-readout performance measure different properties; no cross-task capability score or causal/unlearning claim.

## Layers, seeds and controls

The profiles show every decoder block 0–24 and final norm, both policies and all three CV seeds. Layer 16 is zero-based block 17. Composition and normalized forward 4-mer controls reuse 36 unique historical fits (30 for the other-five tasks); repeated horizontal curves and paired applications do not create extra controls. Formal control comparisons remain at layer16/finalnorm and the three frozen seeds.

251 of 260 candidate/task/representation groups have identical final parameter content across all three seeds; nine have two parameter sets. Distinct frozen folds can select the same C, producing an identical deterministic full-TRAIN fit. This explanation was checked against fold hashes, C traces, parameter/probability identities and the 60-unit independent refit panel. A seed range describes readout-selection sensitivity; it is not a confidence interval or intervention-training replication.

## Actual causal LM evidence

NLL uses total actual causal-head loss divided by total valid shifted targets; PPL is exp(corpus NLL). It is not classifier cross-entropy, an average of sequence perplexities, or a per-layer/seed score. 35 of 49 primary LM units are available (21 historical + 14 A06); 12 A06 TRAIN diagnostics remain separate. The new predeclared R6−R4 family contains 14 LM metric rows, with independent sum/count and every-draw ratio checks.

| Task | R4 corpus NLL | R6 corpus NLL | R6−R4 NLL [95% pointwise CI] |
|---|---:|---:|---:|
| H3 | 1.225060 [1.216481, 1.233303] | 1.226317 [1.218404, 1.234271] | 0.001257 [-0.001769, 0.004457] |
| Human TF | 1.198158 [1.176056, 1.217985] | 1.186291 [1.164681, 1.206068] | -0.011867 [-0.017903, -0.005552] |
| Core promoter | 1.298768 [1.285298, 1.311206] | 1.316643 [1.306625, 1.325910] | 0.017875 [0.010659, 0.026129] |
| Promoter 300 | 1.290896 [1.279246, 1.301518] | 1.295791 [1.284453, 1.306033] | 0.004895 [0.001731, 0.008247] |
| Splice | 1.183482 [1.167711, 1.199486] | 1.101604 [1.081141, 1.121911] | -0.081878 [-0.091077, -0.072583] |
| Mouse TF | 1.342015 [1.334109, 1.349094] | 1.336124 [1.327734, 1.343907] | -0.005891 [-0.009599, -0.002251] |


## What the layer views add

The AUROC profiles show that final norm can differ sharply from the middle decoder blocks; the final-norm display must not stand in for the full representation grid. Human-TF discrimination under the original-base readout degrades across many later representations even where refitted readouts remain useful. Core-promoter and promoter-300 readouts also differ by policy. These are descriptive features of the released curves, not a newly selected best layer or a causal localization claim.

At the predeclared final-norm/seed-42 dev display, R6−R4 refit AUROC decreases for core promoter (−0.047809; pointwise interval −0.072749 to −0.023016) and mouse TF (−0.091893; −0.132478 to −0.051743). Splice is inconclusive at this display (−0.019191; −0.058705 to 0.019562), despite lower R6 corpus LM NLL. Promoter-300 refit AUROC changes little (0.003555; −0.008065 to 0.015516), while its NLL is higher. These examples preserve unfavorable and mixed evidence; none establishes equivalence or a family-wide result.

[All-layer dev AUROC profiles](figures/dev/profiles_auroc.png), [base/R1 paired anchors](figures/dev/anchors_auroc.png), [nonadjacent R6−R4 profiles](figures/dev/R6_minus_R4_auroc.png), [shared-control anchors](figures/dev/anchors__controls_auroc.png), [within-task LM](figures/dev/LM_within_task.png), [nonadjacent LM differences](figures/dev/LM_R6_minus_R4.png) and [coverage map](figures/coverage/availability_and_missing_edges.png) have matching standalone PDFs and full-precision source rows in PLOT_DATA/plotted_values.csv. All 31 figures have a per-file digest and caption in FIGURE_VALIDATION.json. See CLAIMS_TO_EVIDENCE.csv for exact endpoint IDs and row keys.

## Task declarations and interpretation limits

The supplied cumulative design is H3; then human TF, core promoter, promoter 300, splice, mouse TF. TASK_ENTRY_ANALYSIS joins measured rows to the stored configuration evidence. Planned inclusion, config declaration, exact dataset version, observed sampled rows and realized exposure remain distinct. Higher scores before a family appears in a supplied config do not prove unseen-training-data generalization. Unknown parents, objectives, steps, schedules and realized token/source exposure prevent causal mixture attribution; one cumulative ordering cannot establish an optimal mixture.

All five actual adjacent edges remain explicitly pending or bridge-gated. R6−R4 is predeclared and **nonadjacent**, spanning two planned additions and any other training differences. It never substitutes for R6−R5 or R5−R4. Historical R3 results and R3−R1 remain valid in their accepted domain; no new R3-to-R4/R6 effect was derived directly or by subtracting baseline-relative effects.

Intervals are pointwise exploratory and unadjusted across correlated tasks/layers/seeds. They are conditional on fitted heads. CI endpoints were never averaged or subtracted to invent a new interval. An interval crossing zero does not demonstrate equivalence/noninferiority. Exact/RC groups do not establish locus/homology independence. Numeric biological-label ambiguities remain. These benign capability measurements alone do not establish forgetting, resistance to recovery, information erasure or biological understanding.

## Historical reuse and exploratory test

A06 H3 and LM checks and the qualified base/R1/R3 historical audit graph are reused by exact identities. Historical marginal point reports do not carry all absolute CIs; those fields remain null with reasons, while accepted historical paired intervals remain available. The legacy policy spelling fixed_base_scaler_and_head is normalized to fixed_original_base with source spelling retained and original values unchanged. The pretrained base's own fixed application is the same original-base prediction function; it is not a new fit.

H3's previously examined exploratory test is kept in separate rows and figures. It was not an untouched test, was not pooled with dev, and was not used for layer/seed/C selection. No new held-out set was opened.

A06's original paired export still records FAIL_MISSING_REQUIRED_LINEAGE. The normalized derivative retains every original field/key/order and measurement origin A06; ingestion is REUSED_IN_A08. Reporting lineage is not checkpoint parentage.

The public logical paired table is the union of the four files in TABLE_PARTITIONS.json; missing adjacent-effect keys are separately enumerated with null estimates and precise reasons. Figure values come only from released rows. Private recovery claims are scoped CPU checks, not GPU/runtime recreation. See BACKUP_VERIFICATION.json,RESTORE.md and SESSION_HANDOFF.md for exact archives,hashes,commands and exclusions.

WAITING_FOR_APPROVAL: A09
