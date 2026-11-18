# Pod A: one-page summary

**The available-endpoint analysis is complete; the full incremental sequence remains incomplete.** A09 reports and recovers previously verified science without adding fits, forwards or intervals.

**Readout policy changes the conclusion.** Human-TF official-dev final-norm/seed-42 AUROC is 0.705340 [0.660109, 0.749089] for the R4 refit, 0.480620 [0.427147, 0.533411] using the unchanged base readout, and 0.679673 for base. The refitted and fixed heads answer different questions. Their discrepancy is compatible with a changed feature/readout relationship; it does not prove information erasure or forgetting.

**A refit gain need not survive the original base head.** At the same final-norm/seed-42 display, core-promoter R4−base AUROC is 0.108573 [0.070237, 0.150233] under refitting and -0.013093 [-0.052640, 0.025376] under fixed transfer. The latter interval crosses zero; this is inconclusive rather than evidence of equivalence. These predeclared displays are not selected best layers.

**R6 is not uniformly better than R4, and location matters.** The mouse-TF final-norm/seed-42 refit AUROC change is -0.091893 [-0.132478, -0.051743]. Splice is 0.032578 [0.008669, 0.058619] at block 16 but -0.019191 [-0.058705, 0.019562] at final norm; core promoter is -0.024370 [-0.044487, -0.003972] at block 16. All effects are the predeclared **nonadjacent** R6−R4 comparison. Its two planned additions and unmatched training changes cannot be separated causally.

**Likelihood and probe behavior can disagree.** R4 human-TF corpus NLL is 1.198158 [1.176056, 1.217985] against base 1.343778, despite weak fixed-base classification above. R6−R4 splice NLL is -0.081878 [-0.091077, -0.072583], while the final-norm refit AUROC interval is inconclusive. NLL and discriminative readouts measure different properties; no cross-task capability average is constructed.

The readable displays use official dev, seed 42 and predeclared block 16/final norm. All layers, three seeds, both policies and five metrics are retained in the [full results](RESULTS.md), [tables](TABLE_INDEX.json) and [31-figure gallery](FIGURE_GALLERY.md). Intervals are conditional, pointwise and unadjusted; zero-crossing is not equivalence and CV seeds are not intervention replicas.

Coverage is 2,340/3,276 heads and separately 2,340/3,276 fixed applications, 35/49 primary LM units and 36 shared controls. R2/R5 each lack 468 heads; R3 cross-runtime contrasts need the live bridge. All five adjacent edges remain missing; R6−R4 is nonadjacent. Training ancestry, objective and realized exposure gaps prevent a causal mixture or optimality claim. A04 remains PARTIAL. H3 exploratory test remains separate.

[Claims and exact row keys](CLAIMS_TO_EVIDENCE.csv), [missing inputs](MISSING_INPUTS_DRAFT.md) and [saved-analysis recovery](BACKUP_VERIFICATION.json) make the evidence and remaining dependencies reviewable.
