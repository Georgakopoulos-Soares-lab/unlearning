# Available-checkpoint findings — one-page summary

The verified evaluation covers base, R1, R3, R4, R5, R6 across six frozen benign tasks. Available-checkpoint analysis is complete; full project/A04 remains PARTIAL because R2 is missing. A09 adds reporting and saved-analysis recovery, with zero new scientific measurements.

- **Promoter300:** R4−R3 final-norm/seed42 refitted ΔAUROC is +0.114244 [0.084795,0.145774].
- **Splice:** R5−R4 layer16/seed42 refitted ΔAUROC is +0.025240 [0.000367,0.051418]; the final-norm interval crosses zero and remains inconclusive.
- **Mouse TF0:** R6−R5 final-norm/seed42 refitted ΔAUROC is −0.095802 [−0.139971,−0.050811]. R6 still exceeds base at this anchor: 0.748855 versus 0.610656.
- **Readout policy:** R5 H3 layer16/seed42 AUROC is 0.956395 refitted versus 0.826049 with the unchanged-base readout. This is a descriptive policy comparison, with no new policy-gap interval.
- **Before declaration:** R5 mouse final-norm/seed42 ΔAUROC versus base is +0.234000 refitted and +0.217450 unchanged-base. Supplied-config declarations do not establish actual training exposure.
- **Actual LM:** splice R5−R4 NLL changes by −0.097867, while mouse R6−R5 changes by +0.007193. Lower is better. R6−R5 dev NLL worsens on all six tasks under their individual pointwise intervals; no pooled or family-wide test is claimed.

Existing intervals are pointwise exploratory, unadjusted and conditional on fitted heads. Three CV seeds are not checkpoint-training replicates. One checkpoint per configuration and unknown exact lineage/exposure limit causal interpretation. No result establishes forgetting, an optimal mixture or a universally best checkpoint.

Coverage: 2,808/3,276 heads and separate applications, 36 shared controls, 36 dev plus 6 previously examined H3-test LM units out of 49 planned. R2 remains missing 468 heads,468 applications and 7 LM units; its two dependent edges have 10,948 missing classifier/LM slots. R3 and R5 are admitted and evaluated within the documented domains.

The new A09 consumer checks 24 saved prediction paths, 60 existing classifier vectors and 6 LM vectors, regenerates report keys/plot data and renders a main figure with producer paths denied. Actual outcomes and residuals are in the fresh-restore receipt; full GPU recreation remains untested.

[Full report](RESULTS.md) · [PDF](REPORT.pdf) · [Figures](FIGURE_GALLERY.md) · [Exact claims](CLAIMS_TO_EVIDENCE.csv) · [Complete tables](TABLE_INDEX.json) · [Recovery](FRESH_RESTORE_CHECK.json)
