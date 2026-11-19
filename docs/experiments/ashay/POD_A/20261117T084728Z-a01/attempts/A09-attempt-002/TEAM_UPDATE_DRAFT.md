# Unsent team update draft

Draft only; no message has been sent.

The available base/R1/R3/R4/R5/R6 evaluation is complete at its verified scope. Full project/A04 remains PARTIAL: R2 is missing. No new scientific measurements were added for this report.

- Promoter 300, R4 − R3: final-norm AUROC changes by +0.114244 [+0.084795, +0.145774] with a refitted readout and +0.255253 [+0.205964, +0.305867] with the unchanged-base readout. Layer16 changes are +0.013642 [+0.001516, +0.028299] and +0.345678 [+0.284006, +0.410378], respectively.
- Splice, R5 − R4: layer16 AUROC changes by +0.025240 [+0.000367, +0.051418] refitted and +0.043496 [+0.013195, +0.074566] unchanged-base. At final norm the refitted change is -0.016351 [-0.054497, +0.023364] and the unchanged-base change is -0.019161 [-0.052629, +0.014412]. Both final-norm intervals cross zero.
- Mouse TF0, R6 − R5: final-norm AUROC changes by -0.095802 [-0.139971, -0.050811] refitted and -0.058260 [-0.095603, -0.020690] unchanged-base. Absolute refitted AUROC is base 0.610656, R5 0.844656 and R6 0.748855. R6 remains above base in this displayed setting.
- R5 H3 at layer16: refitted AUROC is 0.956395 while the unchanged-base readout gives 0.826049. A new readout can discriminate labels better than the unchanged original-base function on the same saved representation.
- Before mouse TF0 is declared in the supplied R5 retain configuration, final-norm R5 − base AUROC is +0.234000 [+0.183358, +0.284065] refitted and +0.217450 [+0.167218, +0.267655] unchanged-base.
- Actual LM loss gives a distinct view: splice R5 − R4 corpus NLL is -0.097867 [-0.109963, -0.085428] despite inconclusive final-norm classifier change. Mouse R6 − R5 NLL is +0.007193 [+0.003977, +0.010630]. R6 − R5 NLL is positive on each of the six dev tasks, with each existing pointwise interval above zero.

These are descriptive supplied-checkpoint comparisons. Existing pointwise intervals are exploratory/unadjusted; one checkpoint per configuration and unknown training lineage/exposure prevent attributing effects to added task sources. All layers, seeds, policies, controls and separate H3 exploratory test remain accessible.

Coverage:2,808/3,276 heads and separate applications;36 controls;36 dev +6exploratory-test LM units out of49 planned. Only R2-dependent adjacent edges remain missing. Recovery is24 saved prediction paths, 60 classifier vectors and6 LM vectors plus all-file integrity; full GPU recreation remains untested.

[Full results](RESULTS.md) · [Figures](FIGURE_GALLERY.md) · [Methods/limits](METHODS_AND_LIMITS.md) · [Complete tables](TABLE_INDEX.json) · [Source claims](CLAIMS_TO_EVIDENCE.csv)
