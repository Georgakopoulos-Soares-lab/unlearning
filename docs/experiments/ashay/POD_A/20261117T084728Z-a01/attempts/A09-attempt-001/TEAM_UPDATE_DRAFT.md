# Team update — unsent draft

Qualified Pod A available-endpoint analysis and verification are complete; the full incremental checkpoint sequence remains incomplete. Since the November 10 historical comparison, R4/R6 now have the complete qualified six-task/all-layer/three-seed readout grid, independently released in A08. A09 adds presentation and saved-analysis recovery rather than new measurements.

**Readout policy changes the conclusion.** Human-TF official-dev final-norm/seed-42 AUROC is 0.705340 [0.660109, 0.749089] for the R4 refit, 0.480620 [0.427147, 0.533411] using the unchanged base readout, and 0.679673 for base. The refitted and fixed heads answer different questions. Their discrepancy is compatible with a changed feature/readout relationship; it does not prove information erasure or forgetting.

**A refit gain need not survive the original base head.** At the same final-norm/seed-42 display, core-promoter R4−base AUROC is 0.108573 [0.070237, 0.150233] under refitting and -0.013093 [-0.052640, 0.025376] under fixed transfer. The latter interval crosses zero; this is inconclusive rather than evidence of equivalence. These predeclared displays are not selected best layers.

**R6 is not uniformly better than R4, and location matters.** The mouse-TF final-norm/seed-42 refit AUROC change is -0.091893 [-0.132478, -0.051743]. Splice is 0.032578 [0.008669, 0.058619] at block 16 but -0.019191 [-0.058705, 0.019562] at final norm; core promoter is -0.024370 [-0.044487, -0.003972] at block 16. All effects are the predeclared **nonadjacent** R6−R4 comparison. Its two planned additions and unmatched training changes cannot be separated causally.

**Likelihood and probe behavior can disagree.** R4 human-TF corpus NLL is 1.198158 [1.176056, 1.217985] against base 1.343778, despite weak fixed-base classification above. R6−R4 splice NLL is -0.081878 [-0.091077, -0.072583], while the final-norm refit AUROC interval is inconclusive. NLL and discriminative readouts measure different properties; no cross-task capability average is constructed.

The [results](RESULTS.md), [one-page summary](ONE_PAGE_SUMMARY.md) and [gallery](FIGURE_GALLERY.md) retain both readout policies, adverse/inconclusive outcomes, historical R3 and the separate exploratory H3 test. R2 and R5 remain unavailable for the full sequence; R3 needs its live bridge for affected new cross-runtime contrasts. Parent/objective/source/exposure evidence is still needed before causal retain-mixture or unseen-training-data claims.

No message has been sent. Missing-input requests are recorded in [a separate unsent draft](MISSING_INPUTS_DRAFT.md). Pod B owns relearning on its separate server. Saliency/perturbation requires a separately published and approved scope.
