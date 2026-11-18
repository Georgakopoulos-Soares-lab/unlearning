# Predeclared R5 other-five descriptive display

Provisional producer outputs, pending independent A08 release. All 20 seed42 cells (five tasks × layer16/final_norm × two policies) were declared before outcomes. Each value is estimate [pointwise exploratory unadjusted 95% saved-group-bootstrap interval], conditional on fitted heads. Effects are R5 minus the named reference. No best layer/seed selection.

| Task | Hook | Policy | R5 AUROC | R5−base | R5−R1 | R5−composition | R5−kmer4 |
|---|---|---|---|---|---|---|---|
| gue_tf_0 | decoder.layers.16 | independent_refit | 0.827576 [0.792972, 0.861776] | -0.002399 [-0.032427, 0.028679] | 0.025957 [-0.007923, 0.059912] | 0.307486 [0.248809, 0.365148] | 0.037980 [0.002931, 0.074053] |
| gue_tf_0 | decoder.layers.16 | fixed_original_base | 0.646444 [0.598859, 0.691732] | -0.183531 [-0.232806, -0.135088] | 0.001650 [-0.051270, 0.054853] | 0.126354 [0.057615, 0.192896] | -0.143152 [-0.195106, -0.094720] |
| gue_tf_0 | decoder.final_norm | independent_refit | 0.743335 [0.698122, 0.783477] | 0.063662 [0.010363, 0.116858] | 0.101734 [0.042027, 0.160726] | 0.223245 [0.164045, 0.278267] | -0.046261 [-0.089594, -0.003000] |
| gue_tf_0 | decoder.final_norm | fixed_original_base | 0.529402 [0.476259, 0.580742] | -0.150271 [-0.214880, -0.089219] | 0.084822 [0.009523, 0.151955] | 0.009312 [-0.076357, 0.089907] | -0.260194 [-0.327988, -0.197841] |
| gue_prom_core_all | decoder.layers.16 | independent_refit | 0.861411 [0.829525, 0.892975] | 0.044543 [0.013636, 0.079897] | 0.014848 [-0.014396, 0.045121] | 0.108733 [0.066907, 0.152529] | 0.026140 [-0.006950, 0.059665] |
| gue_prom_core_all | decoder.layers.16 | fixed_original_base | 0.635506 [0.587433, 0.681241] | -0.181362 [-0.233304, -0.130679] | 0.041690 [-0.014024, 0.096165] | -0.117172 [-0.176800, -0.058886] | -0.199765 [-0.255395, -0.145589] |
| gue_prom_core_all | decoder.final_norm | independent_refit | 0.871971 [0.842068, 0.902251] | 0.110587 [0.072112, 0.149611] | 0.098685 [0.061449, 0.137349] | 0.119293 [0.079189, 0.158950] | 0.036700 [0.000598, 0.072642] |
| gue_prom_core_all | decoder.final_norm | fixed_original_base | 0.747589 [0.705311, 0.789388] | -0.013795 [-0.052508, 0.026036] | 0.201871 [0.146575, 0.259555] | -0.005089 [-0.033040, 0.025112] | -0.087682 [-0.131706, -0.043069] |
| gue_prom_300_all | decoder.layers.16 | independent_refit | 0.976745 [0.964427, 0.986134] | 0.022354 [0.007929, 0.038629] | 0.013107 [0.001021, 0.025087] | 0.337316 [0.285197, 0.385028] | 0.084642 [0.059603, 0.111225] |
| gue_prom_300_all | decoder.layers.16 | fixed_original_base | 0.702235 [0.657129, 0.745255] | -0.252155 [-0.299061, -0.206339] | 0.139315 [0.071125, 0.205066] | 0.062806 [-0.003821, 0.127170] | -0.189868 [-0.239868, -0.138078] |
| gue_prom_300_all | decoder.final_norm | independent_refit | 0.957534 [0.939378, 0.974012] | 0.120623 [0.086384, 0.157227] | 0.123644 [0.091466, 0.158506] | 0.318105 [0.264798, 0.368059] | 0.065431 [0.037066, 0.094686] |
| gue_prom_300_all | decoder.final_norm | fixed_original_base | 0.945190 [0.923869, 0.963715] | 0.108278 [0.074326, 0.143752] | 0.666575 [0.612686, 0.719427] | 0.305760 [0.255289, 0.351873] | 0.053086 [0.026127, 0.081492] |
| gue_splice_reconstructed | decoder.layers.16 | independent_refit | 0.799543 [0.763674, 0.833878] | 0.011681 [-0.022490, 0.045457] | 0.077438 [0.039549, 0.115389] | 0.296642 [0.244502, 0.347037] | 0.227831 [0.176042, 0.279473] |
| gue_splice_reconstructed | decoder.layers.16 | fixed_original_base | 0.675240 [0.638536, 0.711226] | -0.112622 [-0.152044, -0.076365] | 0.172080 [0.125092, 0.220219] | 0.172338 [0.117467, 0.227225] | 0.103527 [0.053955, 0.155270] |
| gue_splice_reconstructed | decoder.final_norm | independent_refit | 0.619760 [0.579039, 0.660046] | -0.014074 [-0.054360, 0.026124] | 0.026892 [-0.023686, 0.077516] | 0.116858 [0.060604, 0.172416] | 0.048048 [-0.001470, 0.097623] |
| gue_splice_reconstructed | decoder.final_norm | fixed_original_base | 0.531721 [0.493416, 0.572365] | -0.102112 [-0.148757, -0.053607] | -0.011531 [-0.056663, 0.033241] | 0.028820 [-0.016110, 0.075978] | -0.039991 [-0.092262, 0.018825] |
| gue_mouse_0 | decoder.layers.16 | independent_refit | 0.896809 [0.870177, 0.921900] | 0.019863 [-0.005794, 0.047101] | 0.062718 [0.032851, 0.094590] | 0.370130 [0.313470, 0.425140] | 0.108351 [0.067775, 0.148418] |
| gue_mouse_0 | decoder.layers.16 | fixed_original_base | 0.782733 [0.741135, 0.821630] | -0.094214 [-0.134482, -0.054570] | 0.185664 [0.144533, 0.228098] | 0.256053 [0.202326, 0.307946] | -0.005725 [-0.056637, 0.043089] |
| gue_mouse_0 | decoder.final_norm | independent_refit | 0.844656 [0.810138, 0.874081] | 0.234000 [0.183358, 0.284065] | 0.186122 [0.129135, 0.240316] | 0.317977 [0.256251, 0.380517] | 0.056198 [0.011951, 0.098741] |
| gue_mouse_0 | decoder.final_norm | fixed_original_base | 0.828107 [0.791679, 0.861084] | 0.217450 [0.167218, 0.267655] | 0.199847 [0.146579, 0.253496] | 0.301427 [0.236745, 0.363586] | 0.039649 [-0.008282, 0.083136] |

The complete [3900-row task/layer/seed view](TASK_LAYER_SEED_VIEW.csv), [all marginal metrics](RESULTS_LONG.csv) and [all paired effects](PAIRED_CONTRASTS.csv) retain favorable, flat and adverse results across all 26 hooks, all three CV seeds and all five metrics. Intervals and correlated layers do not establish independent replication.

Goals: fixed versus refitted readouts measure different forms of preservation; the layer grid describes representation dependence; saved simple controls provide matched anchors. Earlier-retained tasks and before-declared-inclusion tasks retain their supplied membership labels, but declared configuration, planned membership and demonstrated training exposure are distinct. R5 splice inclusion alone does not identify a causal effect. Adjacent checkpoint analysis belongs to A08 and requires comparable lineage/exposure. No optimal mixture, unseen-example inference, successful forgetting, equivalence/noninferiority, biological independence or causal retain-diversity benefit is established.

The A06 H3 results and actual causal-LM measurements remain unchanged and linked in REUSED_EVIDENCE.json; no LM recomputation or paired LM analysis occurred here. Three CV seeds are not three independently trained checkpoints. R2 gaps and R3 domain-specific saved-output eligibility remain visible.
