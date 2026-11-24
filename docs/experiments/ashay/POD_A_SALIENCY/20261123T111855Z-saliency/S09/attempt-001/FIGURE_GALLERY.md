# Figure atlas and source guide

All 111 figures are available as readable PNG and vector PDF/SVG. Every displayed value and interval bound was checked against exact source rows; complete machine-readable plot specifications and hashes are in PLOT_SOURCE_INDEX.json. Figures are descriptive/exploratory, with pointwise conditional uncertainty where shown. Source tables retain full precision.

## Compact reading sequence

The following figures illustrate the questions discussed in ANALYSIS.md. This reading sequence was chosen after outcome exposure; the complete atlas below preserves every task, metric, checkpoint, policy and seed.

### Frozen scientific scope · nine checkpoints / six benign tasks

[PNG](figures/coverage.png) · [PDF](figures/coverage.pdf) · [SVG](figures/coverage.svg)

Frozen intended comparison universe with admitted and deferred categories explicitly separated. Deferred cells are unknown, not measured zero. Whole-delivery inventory remains PARTIAL despite complete admitted nine-checkpoint benign scope. 48,924 admitted and42,228 deferred keys exhaust the frozen91,152 specification universe; deferred is not a measured zero.

### emp_H3 · AUROC · all checkpoints / policies / CV seeds

[PNG](figures/profiles-emp_H3-AUROC.png) · [PDF](figures/profiles-emp_H3-AUROC.pdf) · [SVG](figures/profiles-emp_H3-AUROC.svg)

All 26 representations and all three CV seeds; seed42 has 95% pointwise exploratory conditional marginal intervals. Colors distinguish CV partitions, not intervention replicates. Block16 is the seventeenth decoder block; FN is final normalization. Ranking accessibility and original-readout compatibility differ across supplied endpoints; no layer is selected for inference. Displayed point values span 0.508506 to 0.958182; 1404 of 1404 displayed points are positive. These are displayed observations, with repeated/shared dependencies retained, not independent replicates.

### gue_prom_300_all · all 54 admitted anchor policy gaps

[PNG](figures/gaps-gue_prom_300_all.png) · [PDF](figures/gaps-gue_prom_300_all.pdf) · [SVG](figures/gaps-gue_prom_300_all.svg)

All admitted anchor AUROC(refitted)-AUROC(original readout) gaps, three seeds and nine checkpoints. Bars are paired 95% pointwise exploratory conditional intervals. Positive means greater refitted AUROC, with no universal higher-is-better ordering or causal mechanism claim. Displayed point values span 0.358282 to 0.503517; 54 of 54 displayed points are positive. These are displayed observations, with repeated/shared dependencies retained, not independent replicates.

### gue_prom_300_all · cross_entropy · differences from original base

[PNG](figures/heatmaps-gue_prom_300_all-cross_entropy.png) · [PDF](figures/heatmaps-gue_prom_300_all-cross_entropy.pdf) · [SVG](figures/heatmaps-gue_prom_300_all-cross_entropy.svg)

Complete candidate-by-representation signed candidate-minus-original-base differences for every CV seed and policy. A common zero-centered scale is used across panels within this metric/task. Values are descriptive; cell color does not imply familywise significance. Readout compatibility need not follow refitted accessibility. Complete signed effects span -0.081756 to 8.305954; 522 negative, 882 positive and 0 exactly zero cells. Favorability follows the metric direction, with lower classifier CE better.

### gue_prom_300_all · ranking, decisions and classifier probability loss

[PNG](figures/metrics-gue_prom_300_all.png) · [PDF](figures/metrics-gue_prom_300_all.pdf) · [SVG](figures/metrics-gue_prom_300_all.svg)

All five classifier metrics at the two frozen anchors for all checkpoints, both policies and three seeds. CE is in nats; all other values are unitless. Ranking, thresholded decisions and probability loss need not agree. LM remains separately displayed in the supplied-endpoint figures; no synthetic capability score is used. Displayed anchor point ranges: AUROC 0.335698–0.966217; AP 0.409345–0.968134; accuracy 0.417969–0.906250; balanced_accuracy 0.419501–0.906172; cross_entropy 0.242934–7.041146. Ranges are metric-specific and descriptive.

### Supplied endpoints · DEV primary LM measurements

[PNG](figures/supplied-LM-dev.png) · [PDF](figures/supplied-LM-dev.pdf) · [SVG](figures/supplied-LM-dev.svg)

Each supplied checkpoint is a separate labeled endpoint with observed intervention label and checkpoint step. LM NLL and perplexity are distinct from classifier CE. DEV is primary; TRAIN is diagnostic in its separate figure. No verified common lineage, matched exposure, seed/layer replication or checkpoint-pair inference is implied. The two noise-5% endpoints at steps2000 and2151 remain separate. Each task/metric has its own labeled axis, with NLL and perplexity kept distinct; TRAIN panels are diagnostic only.

## Complete supplementary atlas

### Coverage and deferred comparisons

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| Frozen scientific scope · nine checkpoints / six benign tasks | [PNG](figures/coverage.png) | [PDF](figures/coverage.pdf) | [SVG](figures/coverage.svg) | [JSON](figure-specs/coverage.json) |

### Complete layer profiles

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| emp_H3 · AP · all checkpoints / policies / CV seeds | [PNG](figures/profiles-emp_H3-AP.png) | [PDF](figures/profiles-emp_H3-AP.pdf) | [SVG](figures/profiles-emp_H3-AP.svg) | [JSON](figure-specs/profiles-emp_H3-AP.json) |
| emp_H3 · AUROC · all checkpoints / policies / CV seeds | [PNG](figures/profiles-emp_H3-AUROC.png) | [PDF](figures/profiles-emp_H3-AUROC.pdf) | [SVG](figures/profiles-emp_H3-AUROC.svg) | [JSON](figure-specs/profiles-emp_H3-AUROC.json) |
| emp_H3 · accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-emp_H3-accuracy.png) | [PDF](figures/profiles-emp_H3-accuracy.pdf) | [SVG](figures/profiles-emp_H3-accuracy.svg) | [JSON](figure-specs/profiles-emp_H3-accuracy.json) |
| emp_H3 · balanced_accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-emp_H3-balanced_accuracy.png) | [PDF](figures/profiles-emp_H3-balanced_accuracy.pdf) | [SVG](figures/profiles-emp_H3-balanced_accuracy.svg) | [JSON](figure-specs/profiles-emp_H3-balanced_accuracy.json) |
| emp_H3 · cross_entropy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-emp_H3-cross_entropy.png) | [PDF](figures/profiles-emp_H3-cross_entropy.pdf) | [SVG](figures/profiles-emp_H3-cross_entropy.svg) | [JSON](figure-specs/profiles-emp_H3-cross_entropy.json) |
| gue_mouse_0 · AP · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_mouse_0-AP.png) | [PDF](figures/profiles-gue_mouse_0-AP.pdf) | [SVG](figures/profiles-gue_mouse_0-AP.svg) | [JSON](figure-specs/profiles-gue_mouse_0-AP.json) |
| gue_mouse_0 · AUROC · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_mouse_0-AUROC.png) | [PDF](figures/profiles-gue_mouse_0-AUROC.pdf) | [SVG](figures/profiles-gue_mouse_0-AUROC.svg) | [JSON](figure-specs/profiles-gue_mouse_0-AUROC.json) |
| gue_mouse_0 · accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_mouse_0-accuracy.png) | [PDF](figures/profiles-gue_mouse_0-accuracy.pdf) | [SVG](figures/profiles-gue_mouse_0-accuracy.svg) | [JSON](figure-specs/profiles-gue_mouse_0-accuracy.json) |
| gue_mouse_0 · balanced_accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_mouse_0-balanced_accuracy.png) | [PDF](figures/profiles-gue_mouse_0-balanced_accuracy.pdf) | [SVG](figures/profiles-gue_mouse_0-balanced_accuracy.svg) | [JSON](figure-specs/profiles-gue_mouse_0-balanced_accuracy.json) |
| gue_mouse_0 · cross_entropy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_mouse_0-cross_entropy.png) | [PDF](figures/profiles-gue_mouse_0-cross_entropy.pdf) | [SVG](figures/profiles-gue_mouse_0-cross_entropy.svg) | [JSON](figure-specs/profiles-gue_mouse_0-cross_entropy.json) |
| gue_prom_300_all · AP · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_300_all-AP.png) | [PDF](figures/profiles-gue_prom_300_all-AP.pdf) | [SVG](figures/profiles-gue_prom_300_all-AP.svg) | [JSON](figure-specs/profiles-gue_prom_300_all-AP.json) |
| gue_prom_300_all · AUROC · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_300_all-AUROC.png) | [PDF](figures/profiles-gue_prom_300_all-AUROC.pdf) | [SVG](figures/profiles-gue_prom_300_all-AUROC.svg) | [JSON](figure-specs/profiles-gue_prom_300_all-AUROC.json) |
| gue_prom_300_all · accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_300_all-accuracy.png) | [PDF](figures/profiles-gue_prom_300_all-accuracy.pdf) | [SVG](figures/profiles-gue_prom_300_all-accuracy.svg) | [JSON](figure-specs/profiles-gue_prom_300_all-accuracy.json) |
| gue_prom_300_all · balanced_accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_300_all-balanced_accuracy.png) | [PDF](figures/profiles-gue_prom_300_all-balanced_accuracy.pdf) | [SVG](figures/profiles-gue_prom_300_all-balanced_accuracy.svg) | [JSON](figure-specs/profiles-gue_prom_300_all-balanced_accuracy.json) |
| gue_prom_300_all · cross_entropy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_300_all-cross_entropy.png) | [PDF](figures/profiles-gue_prom_300_all-cross_entropy.pdf) | [SVG](figures/profiles-gue_prom_300_all-cross_entropy.svg) | [JSON](figure-specs/profiles-gue_prom_300_all-cross_entropy.json) |
| gue_prom_core_all · AP · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_core_all-AP.png) | [PDF](figures/profiles-gue_prom_core_all-AP.pdf) | [SVG](figures/profiles-gue_prom_core_all-AP.svg) | [JSON](figure-specs/profiles-gue_prom_core_all-AP.json) |
| gue_prom_core_all · AUROC · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_core_all-AUROC.png) | [PDF](figures/profiles-gue_prom_core_all-AUROC.pdf) | [SVG](figures/profiles-gue_prom_core_all-AUROC.svg) | [JSON](figure-specs/profiles-gue_prom_core_all-AUROC.json) |
| gue_prom_core_all · accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_core_all-accuracy.png) | [PDF](figures/profiles-gue_prom_core_all-accuracy.pdf) | [SVG](figures/profiles-gue_prom_core_all-accuracy.svg) | [JSON](figure-specs/profiles-gue_prom_core_all-accuracy.json) |
| gue_prom_core_all · balanced_accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_core_all-balanced_accuracy.png) | [PDF](figures/profiles-gue_prom_core_all-balanced_accuracy.pdf) | [SVG](figures/profiles-gue_prom_core_all-balanced_accuracy.svg) | [JSON](figure-specs/profiles-gue_prom_core_all-balanced_accuracy.json) |
| gue_prom_core_all · cross_entropy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_prom_core_all-cross_entropy.png) | [PDF](figures/profiles-gue_prom_core_all-cross_entropy.pdf) | [SVG](figures/profiles-gue_prom_core_all-cross_entropy.svg) | [JSON](figure-specs/profiles-gue_prom_core_all-cross_entropy.json) |
| gue_splice_reconstructed · AP · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_splice_reconstructed-AP.png) | [PDF](figures/profiles-gue_splice_reconstructed-AP.pdf) | [SVG](figures/profiles-gue_splice_reconstructed-AP.svg) | [JSON](figure-specs/profiles-gue_splice_reconstructed-AP.json) |
| gue_splice_reconstructed · AUROC · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_splice_reconstructed-AUROC.png) | [PDF](figures/profiles-gue_splice_reconstructed-AUROC.pdf) | [SVG](figures/profiles-gue_splice_reconstructed-AUROC.svg) | [JSON](figure-specs/profiles-gue_splice_reconstructed-AUROC.json) |
| gue_splice_reconstructed · accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_splice_reconstructed-accuracy.png) | [PDF](figures/profiles-gue_splice_reconstructed-accuracy.pdf) | [SVG](figures/profiles-gue_splice_reconstructed-accuracy.svg) | [JSON](figure-specs/profiles-gue_splice_reconstructed-accuracy.json) |
| gue_splice_reconstructed · balanced_accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_splice_reconstructed-balanced_accuracy.png) | [PDF](figures/profiles-gue_splice_reconstructed-balanced_accuracy.pdf) | [SVG](figures/profiles-gue_splice_reconstructed-balanced_accuracy.svg) | [JSON](figure-specs/profiles-gue_splice_reconstructed-balanced_accuracy.json) |
| gue_splice_reconstructed · cross_entropy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_splice_reconstructed-cross_entropy.png) | [PDF](figures/profiles-gue_splice_reconstructed-cross_entropy.pdf) | [SVG](figures/profiles-gue_splice_reconstructed-cross_entropy.svg) | [JSON](figure-specs/profiles-gue_splice_reconstructed-cross_entropy.json) |
| gue_tf_0 · AP · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_tf_0-AP.png) | [PDF](figures/profiles-gue_tf_0-AP.pdf) | [SVG](figures/profiles-gue_tf_0-AP.svg) | [JSON](figure-specs/profiles-gue_tf_0-AP.json) |
| gue_tf_0 · AUROC · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_tf_0-AUROC.png) | [PDF](figures/profiles-gue_tf_0-AUROC.pdf) | [SVG](figures/profiles-gue_tf_0-AUROC.svg) | [JSON](figure-specs/profiles-gue_tf_0-AUROC.json) |
| gue_tf_0 · accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_tf_0-accuracy.png) | [PDF](figures/profiles-gue_tf_0-accuracy.pdf) | [SVG](figures/profiles-gue_tf_0-accuracy.svg) | [JSON](figure-specs/profiles-gue_tf_0-accuracy.json) |
| gue_tf_0 · balanced_accuracy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_tf_0-balanced_accuracy.png) | [PDF](figures/profiles-gue_tf_0-balanced_accuracy.pdf) | [SVG](figures/profiles-gue_tf_0-balanced_accuracy.svg) | [JSON](figure-specs/profiles-gue_tf_0-balanced_accuracy.json) |
| gue_tf_0 · cross_entropy · all checkpoints / policies / CV seeds | [PNG](figures/profiles-gue_tf_0-cross_entropy.png) | [PDF](figures/profiles-gue_tf_0-cross_entropy.pdf) | [SVG](figures/profiles-gue_tf_0-cross_entropy.svg) | [JSON](figure-specs/profiles-gue_tf_0-cross_entropy.json) |

### Paired anchor reference effects

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| emp_H3 · AP · paired anchor comparisons | [PNG](figures/forests-emp_H3-AP.png) | [PDF](figures/forests-emp_H3-AP.pdf) | [SVG](figures/forests-emp_H3-AP.svg) | [JSON](figure-specs/forests-emp_H3-AP.json) |
| emp_H3 · AUROC · paired anchor comparisons | [PNG](figures/forests-emp_H3-AUROC.png) | [PDF](figures/forests-emp_H3-AUROC.pdf) | [SVG](figures/forests-emp_H3-AUROC.svg) | [JSON](figure-specs/forests-emp_H3-AUROC.json) |
| emp_H3 · accuracy · paired anchor comparisons | [PNG](figures/forests-emp_H3-accuracy.png) | [PDF](figures/forests-emp_H3-accuracy.pdf) | [SVG](figures/forests-emp_H3-accuracy.svg) | [JSON](figure-specs/forests-emp_H3-accuracy.json) |
| emp_H3 · balanced_accuracy · paired anchor comparisons | [PNG](figures/forests-emp_H3-balanced_accuracy.png) | [PDF](figures/forests-emp_H3-balanced_accuracy.pdf) | [SVG](figures/forests-emp_H3-balanced_accuracy.svg) | [JSON](figure-specs/forests-emp_H3-balanced_accuracy.json) |
| emp_H3 · cross_entropy · paired anchor comparisons | [PNG](figures/forests-emp_H3-cross_entropy.png) | [PDF](figures/forests-emp_H3-cross_entropy.pdf) | [SVG](figures/forests-emp_H3-cross_entropy.svg) | [JSON](figure-specs/forests-emp_H3-cross_entropy.json) |
| gue_mouse_0 · AP · paired anchor comparisons | [PNG](figures/forests-gue_mouse_0-AP.png) | [PDF](figures/forests-gue_mouse_0-AP.pdf) | [SVG](figures/forests-gue_mouse_0-AP.svg) | [JSON](figure-specs/forests-gue_mouse_0-AP.json) |
| gue_mouse_0 · AUROC · paired anchor comparisons | [PNG](figures/forests-gue_mouse_0-AUROC.png) | [PDF](figures/forests-gue_mouse_0-AUROC.pdf) | [SVG](figures/forests-gue_mouse_0-AUROC.svg) | [JSON](figure-specs/forests-gue_mouse_0-AUROC.json) |
| gue_mouse_0 · accuracy · paired anchor comparisons | [PNG](figures/forests-gue_mouse_0-accuracy.png) | [PDF](figures/forests-gue_mouse_0-accuracy.pdf) | [SVG](figures/forests-gue_mouse_0-accuracy.svg) | [JSON](figure-specs/forests-gue_mouse_0-accuracy.json) |
| gue_mouse_0 · balanced_accuracy · paired anchor comparisons | [PNG](figures/forests-gue_mouse_0-balanced_accuracy.png) | [PDF](figures/forests-gue_mouse_0-balanced_accuracy.pdf) | [SVG](figures/forests-gue_mouse_0-balanced_accuracy.svg) | [JSON](figure-specs/forests-gue_mouse_0-balanced_accuracy.json) |
| gue_mouse_0 · cross_entropy · paired anchor comparisons | [PNG](figures/forests-gue_mouse_0-cross_entropy.png) | [PDF](figures/forests-gue_mouse_0-cross_entropy.pdf) | [SVG](figures/forests-gue_mouse_0-cross_entropy.svg) | [JSON](figure-specs/forests-gue_mouse_0-cross_entropy.json) |
| gue_prom_300_all · AP · paired anchor comparisons | [PNG](figures/forests-gue_prom_300_all-AP.png) | [PDF](figures/forests-gue_prom_300_all-AP.pdf) | [SVG](figures/forests-gue_prom_300_all-AP.svg) | [JSON](figure-specs/forests-gue_prom_300_all-AP.json) |
| gue_prom_300_all · AUROC · paired anchor comparisons | [PNG](figures/forests-gue_prom_300_all-AUROC.png) | [PDF](figures/forests-gue_prom_300_all-AUROC.pdf) | [SVG](figures/forests-gue_prom_300_all-AUROC.svg) | [JSON](figure-specs/forests-gue_prom_300_all-AUROC.json) |
| gue_prom_300_all · accuracy · paired anchor comparisons | [PNG](figures/forests-gue_prom_300_all-accuracy.png) | [PDF](figures/forests-gue_prom_300_all-accuracy.pdf) | [SVG](figures/forests-gue_prom_300_all-accuracy.svg) | [JSON](figure-specs/forests-gue_prom_300_all-accuracy.json) |
| gue_prom_300_all · balanced_accuracy · paired anchor comparisons | [PNG](figures/forests-gue_prom_300_all-balanced_accuracy.png) | [PDF](figures/forests-gue_prom_300_all-balanced_accuracy.pdf) | [SVG](figures/forests-gue_prom_300_all-balanced_accuracy.svg) | [JSON](figure-specs/forests-gue_prom_300_all-balanced_accuracy.json) |
| gue_prom_300_all · cross_entropy · paired anchor comparisons | [PNG](figures/forests-gue_prom_300_all-cross_entropy.png) | [PDF](figures/forests-gue_prom_300_all-cross_entropy.pdf) | [SVG](figures/forests-gue_prom_300_all-cross_entropy.svg) | [JSON](figure-specs/forests-gue_prom_300_all-cross_entropy.json) |
| gue_prom_core_all · AP · paired anchor comparisons | [PNG](figures/forests-gue_prom_core_all-AP.png) | [PDF](figures/forests-gue_prom_core_all-AP.pdf) | [SVG](figures/forests-gue_prom_core_all-AP.svg) | [JSON](figure-specs/forests-gue_prom_core_all-AP.json) |
| gue_prom_core_all · AUROC · paired anchor comparisons | [PNG](figures/forests-gue_prom_core_all-AUROC.png) | [PDF](figures/forests-gue_prom_core_all-AUROC.pdf) | [SVG](figures/forests-gue_prom_core_all-AUROC.svg) | [JSON](figure-specs/forests-gue_prom_core_all-AUROC.json) |
| gue_prom_core_all · accuracy · paired anchor comparisons | [PNG](figures/forests-gue_prom_core_all-accuracy.png) | [PDF](figures/forests-gue_prom_core_all-accuracy.pdf) | [SVG](figures/forests-gue_prom_core_all-accuracy.svg) | [JSON](figure-specs/forests-gue_prom_core_all-accuracy.json) |
| gue_prom_core_all · balanced_accuracy · paired anchor comparisons | [PNG](figures/forests-gue_prom_core_all-balanced_accuracy.png) | [PDF](figures/forests-gue_prom_core_all-balanced_accuracy.pdf) | [SVG](figures/forests-gue_prom_core_all-balanced_accuracy.svg) | [JSON](figure-specs/forests-gue_prom_core_all-balanced_accuracy.json) |
| gue_prom_core_all · cross_entropy · paired anchor comparisons | [PNG](figures/forests-gue_prom_core_all-cross_entropy.png) | [PDF](figures/forests-gue_prom_core_all-cross_entropy.pdf) | [SVG](figures/forests-gue_prom_core_all-cross_entropy.svg) | [JSON](figure-specs/forests-gue_prom_core_all-cross_entropy.json) |
| gue_splice_reconstructed · AP · paired anchor comparisons | [PNG](figures/forests-gue_splice_reconstructed-AP.png) | [PDF](figures/forests-gue_splice_reconstructed-AP.pdf) | [SVG](figures/forests-gue_splice_reconstructed-AP.svg) | [JSON](figure-specs/forests-gue_splice_reconstructed-AP.json) |
| gue_splice_reconstructed · AUROC · paired anchor comparisons | [PNG](figures/forests-gue_splice_reconstructed-AUROC.png) | [PDF](figures/forests-gue_splice_reconstructed-AUROC.pdf) | [SVG](figures/forests-gue_splice_reconstructed-AUROC.svg) | [JSON](figure-specs/forests-gue_splice_reconstructed-AUROC.json) |
| gue_splice_reconstructed · accuracy · paired anchor comparisons | [PNG](figures/forests-gue_splice_reconstructed-accuracy.png) | [PDF](figures/forests-gue_splice_reconstructed-accuracy.pdf) | [SVG](figures/forests-gue_splice_reconstructed-accuracy.svg) | [JSON](figure-specs/forests-gue_splice_reconstructed-accuracy.json) |
| gue_splice_reconstructed · balanced_accuracy · paired anchor comparisons | [PNG](figures/forests-gue_splice_reconstructed-balanced_accuracy.png) | [PDF](figures/forests-gue_splice_reconstructed-balanced_accuracy.pdf) | [SVG](figures/forests-gue_splice_reconstructed-balanced_accuracy.svg) | [JSON](figure-specs/forests-gue_splice_reconstructed-balanced_accuracy.json) |
| gue_splice_reconstructed · cross_entropy · paired anchor comparisons | [PNG](figures/forests-gue_splice_reconstructed-cross_entropy.png) | [PDF](figures/forests-gue_splice_reconstructed-cross_entropy.pdf) | [SVG](figures/forests-gue_splice_reconstructed-cross_entropy.svg) | [JSON](figure-specs/forests-gue_splice_reconstructed-cross_entropy.json) |
| gue_tf_0 · AP · paired anchor comparisons | [PNG](figures/forests-gue_tf_0-AP.png) | [PDF](figures/forests-gue_tf_0-AP.pdf) | [SVG](figures/forests-gue_tf_0-AP.svg) | [JSON](figure-specs/forests-gue_tf_0-AP.json) |
| gue_tf_0 · AUROC · paired anchor comparisons | [PNG](figures/forests-gue_tf_0-AUROC.png) | [PDF](figures/forests-gue_tf_0-AUROC.pdf) | [SVG](figures/forests-gue_tf_0-AUROC.svg) | [JSON](figure-specs/forests-gue_tf_0-AUROC.json) |
| gue_tf_0 · accuracy · paired anchor comparisons | [PNG](figures/forests-gue_tf_0-accuracy.png) | [PDF](figures/forests-gue_tf_0-accuracy.pdf) | [SVG](figures/forests-gue_tf_0-accuracy.svg) | [JSON](figure-specs/forests-gue_tf_0-accuracy.json) |
| gue_tf_0 · balanced_accuracy · paired anchor comparisons | [PNG](figures/forests-gue_tf_0-balanced_accuracy.png) | [PDF](figures/forests-gue_tf_0-balanced_accuracy.pdf) | [SVG](figures/forests-gue_tf_0-balanced_accuracy.svg) | [JSON](figure-specs/forests-gue_tf_0-balanced_accuracy.json) |
| gue_tf_0 · cross_entropy · paired anchor comparisons | [PNG](figures/forests-gue_tf_0-cross_entropy.png) | [PDF](figures/forests-gue_tf_0-cross_entropy.pdf) | [SVG](figures/forests-gue_tf_0-cross_entropy.svg) | [JSON](figure-specs/forests-gue_tf_0-cross_entropy.json) |

### Complete original-base effect heatmaps

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| emp_H3 · AP · differences from original base | [PNG](figures/heatmaps-emp_H3-AP.png) | [PDF](figures/heatmaps-emp_H3-AP.pdf) | [SVG](figures/heatmaps-emp_H3-AP.svg) | [JSON](figure-specs/heatmaps-emp_H3-AP.json) |
| emp_H3 · AUROC · differences from original base | [PNG](figures/heatmaps-emp_H3-AUROC.png) | [PDF](figures/heatmaps-emp_H3-AUROC.pdf) | [SVG](figures/heatmaps-emp_H3-AUROC.svg) | [JSON](figure-specs/heatmaps-emp_H3-AUROC.json) |
| emp_H3 · accuracy · differences from original base | [PNG](figures/heatmaps-emp_H3-accuracy.png) | [PDF](figures/heatmaps-emp_H3-accuracy.pdf) | [SVG](figures/heatmaps-emp_H3-accuracy.svg) | [JSON](figure-specs/heatmaps-emp_H3-accuracy.json) |
| emp_H3 · balanced_accuracy · differences from original base | [PNG](figures/heatmaps-emp_H3-balanced_accuracy.png) | [PDF](figures/heatmaps-emp_H3-balanced_accuracy.pdf) | [SVG](figures/heatmaps-emp_H3-balanced_accuracy.svg) | [JSON](figure-specs/heatmaps-emp_H3-balanced_accuracy.json) |
| emp_H3 · cross_entropy · differences from original base | [PNG](figures/heatmaps-emp_H3-cross_entropy.png) | [PDF](figures/heatmaps-emp_H3-cross_entropy.pdf) | [SVG](figures/heatmaps-emp_H3-cross_entropy.svg) | [JSON](figure-specs/heatmaps-emp_H3-cross_entropy.json) |
| gue_mouse_0 · AP · differences from original base | [PNG](figures/heatmaps-gue_mouse_0-AP.png) | [PDF](figures/heatmaps-gue_mouse_0-AP.pdf) | [SVG](figures/heatmaps-gue_mouse_0-AP.svg) | [JSON](figure-specs/heatmaps-gue_mouse_0-AP.json) |
| gue_mouse_0 · AUROC · differences from original base | [PNG](figures/heatmaps-gue_mouse_0-AUROC.png) | [PDF](figures/heatmaps-gue_mouse_0-AUROC.pdf) | [SVG](figures/heatmaps-gue_mouse_0-AUROC.svg) | [JSON](figure-specs/heatmaps-gue_mouse_0-AUROC.json) |
| gue_mouse_0 · accuracy · differences from original base | [PNG](figures/heatmaps-gue_mouse_0-accuracy.png) | [PDF](figures/heatmaps-gue_mouse_0-accuracy.pdf) | [SVG](figures/heatmaps-gue_mouse_0-accuracy.svg) | [JSON](figure-specs/heatmaps-gue_mouse_0-accuracy.json) |
| gue_mouse_0 · balanced_accuracy · differences from original base | [PNG](figures/heatmaps-gue_mouse_0-balanced_accuracy.png) | [PDF](figures/heatmaps-gue_mouse_0-balanced_accuracy.pdf) | [SVG](figures/heatmaps-gue_mouse_0-balanced_accuracy.svg) | [JSON](figure-specs/heatmaps-gue_mouse_0-balanced_accuracy.json) |
| gue_mouse_0 · cross_entropy · differences from original base | [PNG](figures/heatmaps-gue_mouse_0-cross_entropy.png) | [PDF](figures/heatmaps-gue_mouse_0-cross_entropy.pdf) | [SVG](figures/heatmaps-gue_mouse_0-cross_entropy.svg) | [JSON](figure-specs/heatmaps-gue_mouse_0-cross_entropy.json) |
| gue_prom_300_all · AP · differences from original base | [PNG](figures/heatmaps-gue_prom_300_all-AP.png) | [PDF](figures/heatmaps-gue_prom_300_all-AP.pdf) | [SVG](figures/heatmaps-gue_prom_300_all-AP.svg) | [JSON](figure-specs/heatmaps-gue_prom_300_all-AP.json) |
| gue_prom_300_all · AUROC · differences from original base | [PNG](figures/heatmaps-gue_prom_300_all-AUROC.png) | [PDF](figures/heatmaps-gue_prom_300_all-AUROC.pdf) | [SVG](figures/heatmaps-gue_prom_300_all-AUROC.svg) | [JSON](figure-specs/heatmaps-gue_prom_300_all-AUROC.json) |
| gue_prom_300_all · accuracy · differences from original base | [PNG](figures/heatmaps-gue_prom_300_all-accuracy.png) | [PDF](figures/heatmaps-gue_prom_300_all-accuracy.pdf) | [SVG](figures/heatmaps-gue_prom_300_all-accuracy.svg) | [JSON](figure-specs/heatmaps-gue_prom_300_all-accuracy.json) |
| gue_prom_300_all · balanced_accuracy · differences from original base | [PNG](figures/heatmaps-gue_prom_300_all-balanced_accuracy.png) | [PDF](figures/heatmaps-gue_prom_300_all-balanced_accuracy.pdf) | [SVG](figures/heatmaps-gue_prom_300_all-balanced_accuracy.svg) | [JSON](figure-specs/heatmaps-gue_prom_300_all-balanced_accuracy.json) |
| gue_prom_300_all · cross_entropy · differences from original base | [PNG](figures/heatmaps-gue_prom_300_all-cross_entropy.png) | [PDF](figures/heatmaps-gue_prom_300_all-cross_entropy.pdf) | [SVG](figures/heatmaps-gue_prom_300_all-cross_entropy.svg) | [JSON](figure-specs/heatmaps-gue_prom_300_all-cross_entropy.json) |
| gue_prom_core_all · AP · differences from original base | [PNG](figures/heatmaps-gue_prom_core_all-AP.png) | [PDF](figures/heatmaps-gue_prom_core_all-AP.pdf) | [SVG](figures/heatmaps-gue_prom_core_all-AP.svg) | [JSON](figure-specs/heatmaps-gue_prom_core_all-AP.json) |
| gue_prom_core_all · AUROC · differences from original base | [PNG](figures/heatmaps-gue_prom_core_all-AUROC.png) | [PDF](figures/heatmaps-gue_prom_core_all-AUROC.pdf) | [SVG](figures/heatmaps-gue_prom_core_all-AUROC.svg) | [JSON](figure-specs/heatmaps-gue_prom_core_all-AUROC.json) |
| gue_prom_core_all · accuracy · differences from original base | [PNG](figures/heatmaps-gue_prom_core_all-accuracy.png) | [PDF](figures/heatmaps-gue_prom_core_all-accuracy.pdf) | [SVG](figures/heatmaps-gue_prom_core_all-accuracy.svg) | [JSON](figure-specs/heatmaps-gue_prom_core_all-accuracy.json) |
| gue_prom_core_all · balanced_accuracy · differences from original base | [PNG](figures/heatmaps-gue_prom_core_all-balanced_accuracy.png) | [PDF](figures/heatmaps-gue_prom_core_all-balanced_accuracy.pdf) | [SVG](figures/heatmaps-gue_prom_core_all-balanced_accuracy.svg) | [JSON](figure-specs/heatmaps-gue_prom_core_all-balanced_accuracy.json) |
| gue_prom_core_all · cross_entropy · differences from original base | [PNG](figures/heatmaps-gue_prom_core_all-cross_entropy.png) | [PDF](figures/heatmaps-gue_prom_core_all-cross_entropy.pdf) | [SVG](figures/heatmaps-gue_prom_core_all-cross_entropy.svg) | [JSON](figure-specs/heatmaps-gue_prom_core_all-cross_entropy.json) |
| gue_splice_reconstructed · AP · differences from original base | [PNG](figures/heatmaps-gue_splice_reconstructed-AP.png) | [PDF](figures/heatmaps-gue_splice_reconstructed-AP.pdf) | [SVG](figures/heatmaps-gue_splice_reconstructed-AP.svg) | [JSON](figure-specs/heatmaps-gue_splice_reconstructed-AP.json) |
| gue_splice_reconstructed · AUROC · differences from original base | [PNG](figures/heatmaps-gue_splice_reconstructed-AUROC.png) | [PDF](figures/heatmaps-gue_splice_reconstructed-AUROC.pdf) | [SVG](figures/heatmaps-gue_splice_reconstructed-AUROC.svg) | [JSON](figure-specs/heatmaps-gue_splice_reconstructed-AUROC.json) |
| gue_splice_reconstructed · accuracy · differences from original base | [PNG](figures/heatmaps-gue_splice_reconstructed-accuracy.png) | [PDF](figures/heatmaps-gue_splice_reconstructed-accuracy.pdf) | [SVG](figures/heatmaps-gue_splice_reconstructed-accuracy.svg) | [JSON](figure-specs/heatmaps-gue_splice_reconstructed-accuracy.json) |
| gue_splice_reconstructed · balanced_accuracy · differences from original base | [PNG](figures/heatmaps-gue_splice_reconstructed-balanced_accuracy.png) | [PDF](figures/heatmaps-gue_splice_reconstructed-balanced_accuracy.pdf) | [SVG](figures/heatmaps-gue_splice_reconstructed-balanced_accuracy.svg) | [JSON](figure-specs/heatmaps-gue_splice_reconstructed-balanced_accuracy.json) |
| gue_splice_reconstructed · cross_entropy · differences from original base | [PNG](figures/heatmaps-gue_splice_reconstructed-cross_entropy.png) | [PDF](figures/heatmaps-gue_splice_reconstructed-cross_entropy.pdf) | [SVG](figures/heatmaps-gue_splice_reconstructed-cross_entropy.svg) | [JSON](figure-specs/heatmaps-gue_splice_reconstructed-cross_entropy.json) |
| gue_tf_0 · AP · differences from original base | [PNG](figures/heatmaps-gue_tf_0-AP.png) | [PDF](figures/heatmaps-gue_tf_0-AP.pdf) | [SVG](figures/heatmaps-gue_tf_0-AP.svg) | [JSON](figure-specs/heatmaps-gue_tf_0-AP.json) |
| gue_tf_0 · AUROC · differences from original base | [PNG](figures/heatmaps-gue_tf_0-AUROC.png) | [PDF](figures/heatmaps-gue_tf_0-AUROC.pdf) | [SVG](figures/heatmaps-gue_tf_0-AUROC.svg) | [JSON](figure-specs/heatmaps-gue_tf_0-AUROC.json) |
| gue_tf_0 · accuracy · differences from original base | [PNG](figures/heatmaps-gue_tf_0-accuracy.png) | [PDF](figures/heatmaps-gue_tf_0-accuracy.pdf) | [SVG](figures/heatmaps-gue_tf_0-accuracy.svg) | [JSON](figure-specs/heatmaps-gue_tf_0-accuracy.json) |
| gue_tf_0 · balanced_accuracy · differences from original base | [PNG](figures/heatmaps-gue_tf_0-balanced_accuracy.png) | [PDF](figures/heatmaps-gue_tf_0-balanced_accuracy.pdf) | [SVG](figures/heatmaps-gue_tf_0-balanced_accuracy.svg) | [JSON](figure-specs/heatmaps-gue_tf_0-balanced_accuracy.json) |
| gue_tf_0 · cross_entropy · differences from original base | [PNG](figures/heatmaps-gue_tf_0-cross_entropy.png) | [PDF](figures/heatmaps-gue_tf_0-cross_entropy.pdf) | [SVG](figures/heatmaps-gue_tf_0-cross_entropy.svg) | [JSON](figure-specs/heatmaps-gue_tf_0-cross_entropy.json) |

### All admitted anchor policy gaps

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| emp_H3 · all 54 admitted anchor policy gaps | [PNG](figures/gaps-emp_H3.png) | [PDF](figures/gaps-emp_H3.pdf) | [SVG](figures/gaps-emp_H3.svg) | [JSON](figure-specs/gaps-emp_H3.json) |
| gue_mouse_0 · all 54 admitted anchor policy gaps | [PNG](figures/gaps-gue_mouse_0.png) | [PDF](figures/gaps-gue_mouse_0.pdf) | [SVG](figures/gaps-gue_mouse_0.svg) | [JSON](figure-specs/gaps-gue_mouse_0.json) |
| gue_prom_300_all · all 54 admitted anchor policy gaps | [PNG](figures/gaps-gue_prom_300_all.png) | [PDF](figures/gaps-gue_prom_300_all.pdf) | [SVG](figures/gaps-gue_prom_300_all.svg) | [JSON](figure-specs/gaps-gue_prom_300_all.json) |
| gue_prom_core_all · all 54 admitted anchor policy gaps | [PNG](figures/gaps-gue_prom_core_all.png) | [PDF](figures/gaps-gue_prom_core_all.pdf) | [SVG](figures/gaps-gue_prom_core_all.svg) | [JSON](figure-specs/gaps-gue_prom_core_all.json) |
| gue_splice_reconstructed · all 54 admitted anchor policy gaps | [PNG](figures/gaps-gue_splice_reconstructed.png) | [PDF](figures/gaps-gue_splice_reconstructed.pdf) | [SVG](figures/gaps-gue_splice_reconstructed.svg) | [JSON](figure-specs/gaps-gue_splice_reconstructed.json) |
| gue_tf_0 · all 54 admitted anchor policy gaps | [PNG](figures/gaps-gue_tf_0.png) | [PDF](figures/gaps-gue_tf_0.pdf) | [SVG](figures/gaps-gue_tf_0.svg) | [JSON](figure-specs/gaps-gue_tf_0.json) |

### Supplied endpoints and separate LM splits

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| Supplied endpoints · DEV primary LM measurements | [PNG](figures/supplied-LM-dev.png) | [PDF](figures/supplied-LM-dev.pdf) | [SVG](figures/supplied-LM-dev.svg) | [JSON](figure-specs/supplied-LM-dev.json) |
| Supplied endpoints · TRAIN LM diagnostics only | [PNG](figures/supplied-LM-train.png) | [PDF](figures/supplied-LM-train.pdf) | [SVG](figures/supplied-LM-train.svg) | [JSON](figure-specs/supplied-LM-train.json) |

### Ranking, decisions and classifier probability loss

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| emp_H3 · ranking, decisions and classifier probability loss | [PNG](figures/metrics-emp_H3.png) | [PDF](figures/metrics-emp_H3.pdf) | [SVG](figures/metrics-emp_H3.svg) | [JSON](figure-specs/metrics-emp_H3.json) |
| gue_mouse_0 · ranking, decisions and classifier probability loss | [PNG](figures/metrics-gue_mouse_0.png) | [PDF](figures/metrics-gue_mouse_0.pdf) | [SVG](figures/metrics-gue_mouse_0.svg) | [JSON](figure-specs/metrics-gue_mouse_0.json) |
| gue_prom_300_all · ranking, decisions and classifier probability loss | [PNG](figures/metrics-gue_prom_300_all.png) | [PDF](figures/metrics-gue_prom_300_all.pdf) | [SVG](figures/metrics-gue_prom_300_all.svg) | [JSON](figure-specs/metrics-gue_prom_300_all.json) |
| gue_prom_core_all · ranking, decisions and classifier probability loss | [PNG](figures/metrics-gue_prom_core_all.png) | [PDF](figures/metrics-gue_prom_core_all.pdf) | [SVG](figures/metrics-gue_prom_core_all.svg) | [JSON](figure-specs/metrics-gue_prom_core_all.json) |
| gue_splice_reconstructed · ranking, decisions and classifier probability loss | [PNG](figures/metrics-gue_splice_reconstructed.png) | [PDF](figures/metrics-gue_splice_reconstructed.pdf) | [SVG](figures/metrics-gue_splice_reconstructed.svg) | [JSON](figure-specs/metrics-gue_splice_reconstructed.json) |
| gue_tf_0 · ranking, decisions and classifier probability loss | [PNG](figures/metrics-gue_tf_0.png) | [PDF](figures/metrics-gue_tf_0.pdf) | [SVG](figures/metrics-gue_tf_0.svg) | [JSON](figure-specs/metrics-gue_tf_0.json) |

### Descriptive CV-seed sensitivity

| Figure | PNG | PDF | SVG | Exact source specification |
|---|---|---|---|---|
| emp_H3 · descriptive sensitivity to frozen CV partitions | [PNG](figures/seeds-emp_H3.png) | [PDF](figures/seeds-emp_H3.pdf) | [SVG](figures/seeds-emp_H3.svg) | [JSON](figure-specs/seeds-emp_H3.json) |
| gue_mouse_0 · descriptive sensitivity to frozen CV partitions | [PNG](figures/seeds-gue_mouse_0.png) | [PDF](figures/seeds-gue_mouse_0.pdf) | [SVG](figures/seeds-gue_mouse_0.svg) | [JSON](figure-specs/seeds-gue_mouse_0.json) |
| gue_prom_300_all · descriptive sensitivity to frozen CV partitions | [PNG](figures/seeds-gue_prom_300_all.png) | [PDF](figures/seeds-gue_prom_300_all.pdf) | [SVG](figures/seeds-gue_prom_300_all.svg) | [JSON](figure-specs/seeds-gue_prom_300_all.json) |
| gue_prom_core_all · descriptive sensitivity to frozen CV partitions | [PNG](figures/seeds-gue_prom_core_all.png) | [PDF](figures/seeds-gue_prom_core_all.pdf) | [SVG](figures/seeds-gue_prom_core_all.svg) | [JSON](figure-specs/seeds-gue_prom_core_all.json) |
| gue_splice_reconstructed · descriptive sensitivity to frozen CV partitions | [PNG](figures/seeds-gue_splice_reconstructed.png) | [PDF](figures/seeds-gue_splice_reconstructed.pdf) | [SVG](figures/seeds-gue_splice_reconstructed.svg) | [JSON](figure-specs/seeds-gue_splice_reconstructed.json) |
| gue_tf_0 · descriptive sensitivity to frozen CV partitions | [PNG](figures/seeds-gue_tf_0.png) | [PDF](figures/seeds-gue_tf_0.pdf) | [SVG](figures/seeds-gue_tf_0.svg) | [JSON](figure-specs/seeds-gue_tf_0.json) |

Every individual caption, including its descriptive observed range and interpretation limits, is recorded in [FIGURE_CAPTIONS.json](FIGURE_CAPTIONS.json). The searchable [HTML gallery](FIGURE_GALLERY.html) displays captions and source links together.
