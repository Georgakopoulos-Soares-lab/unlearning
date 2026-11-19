# Independently checked incremental-retain analysis

Question: how do the supplied cumulative retain configurations change benign readout performance and actual causal-LM measurements? Available endpoints are pretrained base and R1/R3/R4/R5/R6; R2 is missing. This A08 releases 390 R5 other-five units and verifies the three eligible adjacent transitions, while preserving all earlier science. One checkpoint per configuration, unequal historical training settings, unknown parents and unverified realized exposure limit causal conclusions.

## Supported findings

1. At layer16/seed42, R5 unchanged-base AUROC is below pretrained base on 5/5 other tasks. Human TF delta is -0.183531 [-0.232806, -0.135088], and splice delta is -0.112622 [-0.152044, -0.076365]. This is a descriptive set of correlated cells, not family-wide significance or proof of information erasure. Evidence: `a1a5c60c05d4345a7670bd1c685e01c747da6451b22135086c909c983d91a0ea`, `04878ea326a745d42237050eb57c347d08bb3136925acd0ed5c515852a9c4bfa`, `03c84f04757986acfb387b1ecce3a48e234c3d091ba536228bf27b1a2a3b7764`, `5ec1dcdaf03087c22c2a312ec208fc26a98f453b9084e263fbf6ab9392c08d12`, `3ac55353eae36dbfa3f9611779ddacc87240fb213f3de24ee72cef9ba6e32d3f`.

2. Promoter300 at R4−R3 has these AUROC deltas: layer16 refitted +0.013642 [+0.001516, +0.028299], fixed-base +0.345678 [+0.284006, +0.410378]; final norm refitted +0.114244 [+0.084795, +0.145774], fixed-base +0.255253 [+0.205964, +0.305867]. These are supplied-configuration comparisons, with no attribution to the added source under unknown training lineage/exposure. An interval crossing zero is inconclusive. Evidence: `7cf9f9c9910034136987c8f070cf07209b49d1f22da0424c7a391283c6861f17`, `2789f30aa78d95e4290f3284ebf6d2489a84c79b7e3c255cad538a42ca2477e1`, `8cd255ac1f61128148d977d58fec446bebf93355fa225a6f085b36539c771761`, `5fc6b9aae0f20baa5cba807243d77f8b13692db5306e4d877b7276da4b02d759`.

3. Splice at R5−R4 has these AUROC deltas: layer16 refitted +0.025240 [+0.000367, +0.051418], fixed-base +0.043496 [+0.013195, +0.074566]; final norm refitted -0.016351 [-0.054497, +0.023364], fixed-base -0.019161 [-0.052629, +0.014412]. These are supplied-configuration comparisons, with no attribution to the added source under unknown training lineage/exposure. An interval crossing zero is inconclusive. Evidence: `6efb89ffd494210ed05eefbc6f3cf0d1bae676aef2b00ae82d569ac9829783d1`, `d23baad71ea7f24196bc2d3ab720fec9ea159d34b776c8baa30df63b7798a55e`, `b09313e2fb4f20bc714ca8fc945c3edec115e56763ae89d6f964a1bf9f39d8d8`, `342a4ec9fd7fbca329c05d1ea2cbc32cc0c919fe279adcc028082960ad22b0dd`.

4. Mouse TF at R6−R5 has these AUROC deltas: layer16 refitted +0.010183 [-0.008445, +0.026969], fixed-base -0.027038 [-0.046318, -0.008207]; final norm refitted -0.095802 [-0.139971, -0.050811], fixed-base -0.058260 [-0.095603, -0.020690]. These are supplied-configuration comparisons, with no attribution to the added source under unknown training lineage/exposure. An interval crossing zero is inconclusive. Evidence: `32a1abf93929ddcc7ef0ebf563aa734242b9e35dc73e61d65790af1ff45b13a1`, `fe340dd079abf684f8ae9f91af352f80b7dc314e0d4adc882d84697083a3f08e`, `9cf7025c5f17e27d4e3dc5e609644f6a40a068c2133450f8a156bfd7652890b0`, `104a08d557d5a26a0b895745084ba303bb73b8e1a4a5a83b37cb85be05c77b8e`.

5. Before mouse TF is declared in the supplied R5 configuration, final-norm/seed42 R5−base AUROC is +0.234000 [+0.183358, +0.284065] refitted and +0.217450 [+0.167218, +0.267655] fixed-base. Before declaration does not mean unseen examples or verified absence of training exposure. Evidence: `4e478ed240f71196832e6b3891b1b8e71645a6366c565633a24e3dfd202b3d3e`, `f89a3ed9839db946f1e7e73675754b394c79d68f211cab51d1209e5a6b8baff3`.

6. Actual causal-head changes: splice R5−R4 NLL -0.097867 [-0.109963, -0.085428] and PPL -0.304465 [-0.340265, -0.268518]; mouse R6−R5 NLL +0.007193 [+0.003977, +0.010630] and PPL +0.027264 [+0.015034, +0.040371]. Lower loss is favorable. These within-task LM quantities are distinct from readout quality; no cross-task capability score is constructed. Evidence: `d85cc593bfdf181e4fe4a57fb589473ec2a6b2bb6120b4c5227662871dc1561b`, `10e69669ea35f7f4f4d009d4b417f6cf131d699ded2c1a67f05defcd4fadcce0`, `b48a5512223d32f1a5753034295c209a5de0dd30190a770445b547c71518d8f1`, `a67cf643119ba6d257e1dae8d4f2eea19f3ff046c85848e380a77fca90417b63`.

## Every eligible transition across all six tasks

The table uses the fixed layer16/seed42 display, with paired pointwise exploratory 95% intervals in raw AUROC units. These correlated cells are descriptive, with no family-wide significance claim. [Complete anchor summary](ADJACENT_TASK_SUMMARY.csv) includes final norm, exact logical IDs and declarations; [task-entry analysis](TASK_ENTRY_ANALYSIS.csv) includes all three CV seeds and the separately labeled H3 exploratory test. Full-layer effects remain in `plot_data/`.

| Transition | Task | Supplied-config category | Refitted ΔAUROC [95% interval] | Unchanged-base ΔAUROC [95% interval] |
|---|---|---|---:|---:|
| R4 − R3 | emp_H3 | already declared in supplied configuration | -0.0006 [-0.0052, +0.0040] | -0.0060 [-0.0118, -0.0004] |
| R4 − R3 | gue_tf_0 | already declared in supplied configuration | -0.0033 [-0.0200, +0.0146] | -0.0081 [-0.0333, +0.0174] |
| R4 − R3 | gue_prom_core_all | already declared in supplied configuration | -0.0048 [-0.0199, +0.0099] | -0.0289 [-0.0536, -0.0041] |
| R4 − R3 | gue_prom_300_all | newly declared in supplied configuration | +0.0136 [+0.0015, +0.0283] | +0.3457 [+0.2840, +0.4104] |
| R4 − R3 | gue_splice_reconstructed | before declaration in supplied retain configuration | +0.0020 [-0.0306, +0.0325] | +0.0665 [+0.0185, +0.1115] |
| R4 − R3 | gue_mouse_0 | before declaration in supplied retain configuration | +0.0226 [+0.0052, +0.0422] | +0.0418 [+0.0229, +0.0612] |
| R5 − R4 | emp_H3 | already declared in supplied configuration | +0.0017 [-0.0029, +0.0062] | +0.0131 [+0.0069, +0.0193] |
| R5 − R4 | gue_tf_0 | already declared in supplied configuration | +0.0024 [-0.0145, +0.0189] | -0.0048 [-0.0281, +0.0178] |
| R5 − R4 | gue_prom_core_all | already declared in supplied configuration | -0.0136 [-0.0299, +0.0033] | -0.0338 [-0.0598, -0.0071] |
| R5 − R4 | gue_prom_300_all | already declared in supplied configuration | -0.0033 [-0.0091, +0.0018] | -0.0378 [-0.0604, -0.0157] |
| R5 − R4 | gue_splice_reconstructed | newly declared in supplied configuration | +0.0252 [+0.0004, +0.0514] | +0.0435 [+0.0132, +0.0746] |
| R5 − R4 | gue_mouse_0 | before declaration in supplied retain configuration | -0.0040 [-0.0180, +0.0095] | +0.0133 [+0.0001, +0.0264] |
| R6 − R5 | emp_H3 | already declared in supplied configuration | -0.0024 [-0.0072, +0.0027] | -0.0139 [-0.0205, -0.0072] |
| R6 − R5 | gue_tf_0 | already declared in supplied configuration | +0.0026 [-0.0172, +0.0231] | +0.0379 [+0.0083, +0.0685] |
| R6 − R5 | gue_prom_core_all | already declared in supplied configuration | -0.0108 [-0.0326, +0.0095] | -0.0056 [-0.0376, +0.0280] |
| R6 − R5 | gue_prom_300_all | already declared in supplied configuration | -0.0002 [-0.0055, +0.0062] | +0.1061 [+0.0777, +0.1378] |
| R6 − R5 | gue_splice_reconstructed | already declared in supplied configuration | +0.0073 [-0.0050, +0.0192] | -0.0081 [-0.0276, +0.0100] |
| R6 − R5 | gue_mouse_0 | newly declared in supplied configuration | +0.0102 [-0.0084, +0.0270] | -0.0270 [-0.0463, -0.0082] |

Splice changes before declaration in the supplied R4 retain configuration: layer16/seed42 R4 − R3 is +0.0020 [-0.0306, +0.0325] refitted and +0.0665 [+0.0185, +0.1115] with the unchanged-base readout. The refitted interval is inconclusive if it contains zero. These are existing eligible adjacent comparisons, not a newly added inferential family. Exact evidence IDs: `1fef817e7e21177409abc5749512dd09a5193952d166a3b0dbebc23c52c98fbe`, `8be326c0b8f7e282ddfcbecefd089ac2abd98a79f9a083987dbf7f9f5efa9291`. Unknown realized training exposure is not absence of exposure.

The full profiles show representation and policy dependence rather than monotonic improvement across the retain-set order. All 25 block profiles and final norm are displayed for every supplied checkpoint, task and CV seed. Refitted and unchanged-base panels use comparable axes. The final norm is a separate representation, not a 26th block. [Readout-policy summary](READOUT_POLICY_SUMMARY.csv) reports descriptive point gaps and preserves their lack of a policy-gap confidence interval. Matched base/R1/composition/4-mer panels retain both favorable and adverse results; no control was fitted here.

Actual causal-LM changes need separate interpretation. The splice transition improves LM NLL while its final-norm classifier interval is inconclusive; mouse R6 − R5 worsens LM NLL and several readout settings. These observations do not identify training mechanisms or establish forgetting.

## Methods and evidence

All 390 R5 units/780 probability paths passed independent saved-scaler/coefficient reconstruction. All 3900 marginal and8400 paired 2,000-draw vectors were checked,24.6M attempted values. The frozen 30 full-CV-plus-final refits used 480 solver calls and reproduced fold scores/selected C/probabilities; six H3 audit refits were reused. New paired effects cover 16,380 classifier rows / 32.76M attempted deltas and 70 actual causal-LM rows / 140,000 attempted deltas, with two numerical routes. Absolute gates remain1e-10 probabilities and1e-12 points/draws/intervals.

Tables preserve original A07 status and values, adding a separate A08 release overlay. The exact 33,684-key amendment comprises 4,934 reused A06, 12,300 audited A07 and 16,450 new A08 keys. See [partition index](TABLE_PARTITIONS.json), [claims](CLAIMS_TO_EVIDENCE.csv), [task entry](TASK_ENTRY_ANALYSIS.csv), [readout policies](READOUT_POLICY_SUMMARY.csv), [seed sensitivity](SEED_SENSITIVITY.csv), [coverage](COVERAGE.csv), and [figure gallery](FIGURE_GALLERY.md).

## Interpretation and remaining gaps

All six tasks, all 26 representations, all three CV seeds and both policies are retained. No best layer/seed was chosen after dev inspection. Policy point gaps are descriptive; no unapproved policy-gap CI was calculated. Same final fits after different folds select the same C are expected under the fixed optimizer seed; three CV seeds are not three independently trained checkpoints.

H3 test was previously examined and remains separately labeled test_exploratory, excluded from primary dev figures. Exact/RC grouping does not establish locus/homology independence. Numeric binary positive1 and sorted splice classes0/1/2 remain unchanged; unresolved biological-label aliases are not relabeled. Planned membership, supplied-config declaration, dataset identity and realized consumption are separate. Dataset versions, sampler rows/tokens, parents/objective implementation and equal training exposure remain incompletely evidenced.

R3 comparisons use exactly the approved 1,092 classifier and 7 LM domains plus preserved native identity/TRAIN-bridge evidence; no global held-out runtime equality is claimed. R2 remains missing 468 heads,468 applications and7 primary LM units, and its two dependent edges retain 10,948 blocked classifier/LM keys. R3−R1 and R6−R4 remain historical nonadjacent comparisons. Full A04/project remains PARTIAL. No optimal-mixture, causal retain-diversity, successful forgetting, equivalence/noninferiority or robustness-to-recovery claim follows. No new GPU/model/LM forward, replacement production head, control fit or A09 execution occurred.
