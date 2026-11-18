# Pod A results: verified available checkpoints, incomplete incremental sequence

**Qualified available-endpoint analysis is complete. The full R1–R6 sequence and A04 remain partial.** A09 adds usable reports and fresh saved-analysis recovery; it adds no model forwards, fitting, draws or new scientific estimates. Relative to the November 10 historical base/R1/R3 evidence, the package now contains independently verified R4/R6 measurements across all six tasks, 26 representations and three CV seeds. That new science was produced in A06/A07 and released in A08, not measured again here.

The study currently has 2,340 of 3,276 final heads and a separate 2,340 of 3,276 unchanged-base applications. R2 and R5 each lack 468 head cells. Primary causal LM coverage is 35 of 49 units; 36 shared control fits are reused. Every cell remains in the 6,637-unit ledger. [Count evidence](COUNT_EVIDENCE.json), [coverage](COVERAGE.csv), [table index](TABLE_INDEX.json) and [goals](GOALS_STATUS.csv) retain the denominators.

## Main findings

1. **Readout policy changes the conclusion.** Human-TF official-dev final-norm/seed-42 AUROC is 0.705340 [0.660109, 0.749089] for the R4 refit, 0.480620 [0.427147, 0.533411] using the unchanged base readout, and 0.679673 for base. The refitted and fixed heads answer different questions. Their discrepancy is compatible with a changed feature/readout relationship; it does not prove information erasure or forgetting.

2. **A refit gain need not survive the original base head.** At the same final-norm/seed-42 display, core-promoter R4−base AUROC is 0.108573 [0.070237, 0.150233] under refitting and -0.013093 [-0.052640, 0.025376] under fixed transfer. The latter interval crosses zero; this is inconclusive rather than evidence of equivalence. These predeclared displays are not selected best layers.

3. **R6 is not uniformly better than R4, and location matters.** The mouse-TF final-norm/seed-42 refit AUROC change is -0.091893 [-0.132478, -0.051743]. Splice is 0.032578 [0.008669, 0.058619] at block 16 but -0.019191 [-0.058705, 0.019562] at final norm; core promoter is -0.024370 [-0.044487, -0.003972] at block 16. All effects are the predeclared **nonadjacent** R6−R4 comparison. Its two planned additions and unmatched training changes cannot be separated causally.

4. **Likelihood and probe behavior can disagree.** R4 human-TF corpus NLL is 1.198158 [1.176056, 1.217985] against base 1.343778, despite weak fixed-base classification above. R6−R4 splice NLL is -0.081878 [-0.091077, -0.072583], while the final-norm refit AUROC interval is inconclusive. NLL and discriminative readouts measure different properties; no cross-task capability average is constructed.

All brackets below are **pointwise, unadjusted 95% exact/RC-group bootstrap intervals conditional on the fitted heads**, not familywise claims across correlated tasks/layers/seeds. An interval crossing zero does not establish equivalence or preservation. Three CV seeds are not checkpoint-training replications. Every displayed value is machine-joined to an immutable released row in [claims](CLAIMS_TO_EVIDENCE.csv).

## Both predeclared anchors and both readouts

The following official-dev tables use seed 42 for readability. Block 16 is the zero-based **17th decoder block**; final norm is a separate hook. All 26 representations, all three seeds and all five metrics remain in the complete source tables and [figure gallery](FIGURE_GALLERY.md). Historical marginal intervals absent from the inherited reports remain null; no new marginal interval was manufactured.

### Block 16 — refitted readout

| Task | Base AUROC | R1 AUROC | R4 AUROC | R6 AUROC | R6−R4 AUROC |
|---|---:|---:|---:|---:|---:|
| H3 | 0.934064 | 0.950395 | 0.954668 [0.943746, 0.963721] | 0.953977 [0.943483, 0.963935] | -0.000691 [-0.006087, 0.004793] |
| Human TF | 0.829975 | 0.801619 | 0.825178 [0.789147, 0.861190] | 0.830219 [0.794404, 0.864066] | 0.005042 [-0.015227, 0.024226] |
| Core promoter | 0.816868 | 0.846564 | 0.874992 [0.845592, 0.904567] | 0.850623 [0.816898, 0.882796] | -0.024370 [-0.044487, -0.003972] |
| Promoter 300 | 0.954391 | 0.963638 | 0.980072 [0.968393, 0.989072] | 0.976593 [0.964674, 0.986059] | -0.003479 [-0.010117, 0.003520] |
| Splice (three classes) | 0.787862 | 0.722105 | 0.774303 [0.735823, 0.809100] | 0.806882 [0.770139, 0.840346] | 0.032578 [0.008669, 0.058619] |
| Mouse TF | 0.876947 | 0.834092 | 0.900840 [0.874140, 0.925874] | 0.906992 [0.880717, 0.930395] | 0.006153 [-0.009558, 0.021530] |

### Block 16 — unchanged base readout

| Task | Base AUROC | R1 AUROC | R4 AUROC | R6 AUROC | R6−R4 AUROC |
|---|---:|---:|---:|---:|---:|
| H3 | 0.934064 | 0.826686 | 0.812980 [0.791571, 0.833797] | 0.812134 [0.791051, 0.833167] | -0.000845 [-0.007744, 0.006104] |
| Human TF | 0.829975 | 0.644794 | 0.651226 [0.600995, 0.695574] | 0.684363 [0.637009, 0.726727] | 0.033137 [0.002799, 0.062435] |
| Core promoter | 0.816868 | 0.593817 | 0.669337 [0.622852, 0.715897] | 0.629891 [0.580313, 0.676884] | -0.039446 [-0.069751, -0.010361] |
| Promoter 300 | 0.954391 | 0.562921 | 0.739986 [0.696263, 0.780906] | 0.808362 [0.769099, 0.846298] | 0.068376 [0.038254, 0.102555] |
| Splice (three classes) | 0.787862 | 0.503159 | 0.631743 [0.593487, 0.669769] | 0.667171 [0.630839, 0.704795] | 0.035428 [0.003480, 0.067902] |
| Mouse TF | 0.876947 | 0.597069 | 0.769466 [0.727654, 0.810244] | 0.755695 [0.712976, 0.797686] | -0.013771 [-0.033395, 0.006415] |

### Final norm — refitted readout

| Task | Base AUROC | R1 AUROC | R4 AUROC | R6 AUROC | R6−R4 AUROC |
|---|---:|---:|---:|---:|---:|
| H3 | 0.819890 | 0.839359 | 0.848612 [0.828583, 0.867407] | 0.856180 [0.836292, 0.874041] | 0.007569 [0.001719, 0.013396] |
| Human TF | 0.679673 | 0.641601 | 0.705340 [0.660109, 0.749089] | 0.747430 [0.704124, 0.788767] | 0.042090 [0.004364, 0.079292] |
| Core promoter | 0.761384 | 0.773286 | 0.869957 [0.840497, 0.900748] | 0.822148 [0.786803, 0.858348] | -0.047809 [-0.072749, -0.023016] |
| Promoter 300 | 0.836912 | 0.833890 | 0.950576 [0.930174, 0.967166] | 0.954131 [0.934221, 0.970816] | 0.003555 [-0.008065, 0.015516] |
| Splice (three classes) | 0.633834 | 0.592868 | 0.636111 [0.596829, 0.676052] | 0.616920 [0.576949, 0.654428] | -0.019191 [-0.058705, 0.019562] |
| Mouse TF | 0.610656 | 0.658534 | 0.840748 [0.806041, 0.873727] | 0.748855 [0.706616, 0.790170] | -0.091893 [-0.132478, -0.051743] |

### Final norm — unchanged base readout

| Task | Base AUROC | R1 AUROC | R4 AUROC | R6 AUROC | R6−R4 AUROC |
|---|---:|---:|---:|---:|---:|
| H3 | 0.819890 | 0.693431 | 0.818880 [0.797094, 0.838641] | 0.841188 [0.820556, 0.860358] | 0.022308 [0.014051, 0.031204] |
| Human TF | 0.679673 | 0.444580 | 0.480620 [0.427147, 0.533411] | 0.502559 [0.453307, 0.553096] | 0.021939 [-0.020973, 0.069620] |
| Core promoter | 0.761384 | 0.545718 | 0.748291 [0.706201, 0.789237] | 0.700116 [0.657496, 0.744747] | -0.048175 [-0.076932, -0.019168] |
| Promoter 300 | 0.836912 | 0.278614 | 0.911849 [0.886630, 0.936220] | 0.900542 [0.874164, 0.926071] | -0.011307 [-0.029502, 0.006974] |
| Splice (three classes) | 0.633834 | 0.543252 | 0.550882 [0.512699, 0.588459] | 0.554077 [0.515457, 0.593659] | 0.003194 [-0.030991, 0.037843] |
| Mouse TF | 0.610656 | 0.628260 | 0.760443 [0.717153, 0.798795] | 0.769847 [0.728080, 0.808380] | 0.009405 [-0.020771, 0.040596] |

## Changes relative to base, R1 and simple DNA controls

The paired differences below retain matched cohorts, shared group draws and reference-policy semantics. Controls are shared input baselines: composition uses four canonical A/C/G/T fractions, and normalized forward 4-mers use 256 features without reverse-complement collapsing. There are 36 total historical fits, not a new fit per checkpoint or layer. Formal control comparisons are restricted to these anchors and frozen seeds; horizontal control lines in all-layer plots do not add an all-layer inferential family.

### Block 16 — refitted paired AUROC changes

| Task / candidate | −base | −R1 | −composition | −forward 4-mer |
|---|---:|---:|---:|---:|
| H3 / R4 | 0.020605 [0.010831, 0.030238] | 0.004273 [-0.000925, 0.009727] | 0.131167 [0.111673, 0.152596] | 0.060932 [0.047033, 0.075653] |
| H3 / R6 | 0.019914 [0.010140, 0.029721] | 0.003582 [-0.002636, 0.009848] | 0.130476 [0.110392, 0.152274] | 0.060241 [0.045544, 0.075088] |
| Human TF / R4 | -0.004797 [-0.035096, 0.026376] | 0.023558 [-0.008617, 0.056428] | 0.305087 [0.245627, 0.363300] | 0.035582 [0.000903, 0.070804] |
| Human TF / R6 | 0.000244 [-0.029547, 0.031513] | 0.028600 [-0.006924, 0.062261] | 0.310129 [0.251003, 0.366775] | 0.040623 [0.004473, 0.076346] |
| Core promoter / R4 | 0.058124 [0.026849, 0.092223] | 0.028429 [-0.000078, 0.058456] | 0.122314 [0.080211, 0.163620] | 0.039721 [0.008805, 0.071721] |
| Core promoter / R6 | 0.033755 [0.001844, 0.067577] | 0.004059 [-0.025866, 0.033610] | 0.097945 [0.053616, 0.142192] | 0.015351 [-0.017561, 0.048592] |
| Promoter 300 / R4 | 0.025681 [0.011260, 0.042119] | 0.016434 [0.005389, 0.028911] | 0.340642 [0.289600, 0.388076] | 0.087968 [0.064157, 0.114666] |
| Promoter 300 / R6 | 0.022202 [0.008479, 0.039002] | 0.012955 [0.002976, 0.024141] | 0.337163 [0.285442, 0.384520] | 0.084489 [0.060631, 0.111023] |
| Splice (three classes) / R4 | -0.013559 [-0.047972, 0.019167] | 0.052198 [0.017141, 0.084529] | 0.271402 [0.218299, 0.323901] | 0.202591 [0.153352, 0.252870] |
| Splice (three classes) / R6 | 0.019020 [-0.014105, 0.050800] | 0.084776 [0.050329, 0.120615] | 0.303980 [0.249455, 0.355986] | 0.235170 [0.183018, 0.286776] |
| Mouse TF / R4 | 0.023893 [-0.002498, 0.051201] | 0.066748 [0.036348, 0.099621] | 0.374160 [0.316745, 0.429508] | 0.112382 [0.072754, 0.152062] |
| Mouse TF / R6 | 0.030046 [0.004738, 0.056773] | 0.072901 [0.042363, 0.103714] | 0.380313 [0.324118, 0.435646] | 0.118534 [0.077860, 0.158851] |

### Block 16 — fixed base paired AUROC changes

| Task / candidate | −base | −R1 | −composition | −forward 4-mer |
|---|---:|---:|---:|---:|
| H3 / R4 | -0.121084 [-0.140318, -0.101833] | -0.013706 [-0.021716, -0.005836] | -0.010522 [-0.038630, 0.018860] | -0.080757 [-0.101342, -0.059835] |
| H3 / R6 | -0.121929 [-0.140731, -0.102115] | -0.014552 [-0.023754, -0.005165] | -0.011367 [-0.039578, 0.018291] | -0.081602 [-0.102414, -0.059155] |
| Human TF / R4 | -0.178749 [-0.228837, -0.130018] | 0.006432 [-0.046722, 0.061480] | 0.131136 [0.058376, 0.200024] | -0.138370 [-0.189151, -0.090556] |
| Human TF / R6 | -0.145611 [-0.192330, -0.100040] | 0.039569 [-0.018806, 0.094511] | 0.164273 [0.099541, 0.224881] | -0.105233 [-0.153796, -0.059849] |
| Core promoter / R4 | -0.147531 [-0.198198, -0.095689] | 0.075520 [0.017714, 0.131349] | -0.083341 [-0.141997, -0.027314] | -0.165934 [-0.221015, -0.110006] |
| Core promoter / R6 | -0.186977 [-0.241185, -0.128450] | 0.036074 [-0.026680, 0.097525] | -0.122787 [-0.184259, -0.063559] | -0.205381 [-0.261124, -0.149711] |
| Promoter 300 / R4 | -0.214405 [-0.257989, -0.172181] | 0.177066 [0.106199, 0.244354] | 0.100557 [0.032036, 0.166525] | -0.152117 [-0.201203, -0.101385] |
| Promoter 300 / R6 | -0.146029 [-0.185397, -0.106198] | 0.245441 [0.185531, 0.300864] | 0.168933 [0.119699, 0.220293] | -0.083742 [-0.126048, -0.039931] |
| Splice (three classes) / R4 | -0.156119 [-0.197187, -0.116789] | 0.128584 [0.078350, 0.178363] | 0.128842 [0.070550, 0.189747] | 0.060031 [0.010588, 0.113931] |
| Splice (three classes) / R6 | -0.120691 [-0.159343, -0.083157] | 0.164012 [0.117532, 0.211518] | 0.164270 [0.108393, 0.220371] | 0.095459 [0.044129, 0.148376] |
| Mouse TF / R4 | -0.107481 [-0.148623, -0.067695] | 0.172397 [0.131410, 0.215338] | 0.242786 [0.189150, 0.294687] | -0.018992 [-0.071756, 0.032203] |
| Mouse TF / R6 | -0.121252 [-0.164805, -0.079795] | 0.158626 [0.115854, 0.203068] | 0.229015 [0.173413, 0.286248] | -0.032763 [-0.087588, 0.019743] |

### Final norm — refitted paired AUROC changes

| Task / candidate | −base | −R1 | −composition | −forward 4-mer |
|---|---:|---:|---:|---:|
| H3 / R4 | 0.028721 [0.011856, 0.046793] | 0.009252 [-0.002354, 0.021032] | 0.025110 [0.004739, 0.046474] | -0.045125 [-0.062098, -0.028375] |
| H3 / R6 | 0.036290 [0.019844, 0.054052] | 0.016821 [0.005352, 0.029369] | 0.032679 [0.011928, 0.054385] | -0.037556 [-0.054757, -0.020841] |
| Human TF / R4 | 0.025666 [-0.032666, 0.086001] | 0.063738 [0.004825, 0.124654] | 0.185249 [0.127947, 0.240886] | -0.084256 [-0.133106, -0.035312] |
| Human TF / R6 | 0.067756 [0.015897, 0.119870] | 0.105828 [0.049926, 0.162779] | 0.227339 [0.170873, 0.281004] | -0.042166 [-0.086707, 0.004095] |
| Core promoter / R4 | 0.108573 [0.070237, 0.150233] | 0.096670 [0.064950, 0.128960] | 0.117279 [0.083378, 0.151949] | 0.034685 [-0.000704, 0.069037] |
| Core promoter / R6 | 0.060764 [0.019658, 0.102562] | 0.048862 [0.013799, 0.084524] | 0.069470 [0.033497, 0.104869] | -0.013123 [-0.055086, 0.027149] |
| Promoter 300 / R4 | 0.113664 [0.081124, 0.146625] | 0.116686 [0.083147, 0.151179] | 0.311147 [0.258199, 0.359393] | 0.058473 [0.032195, 0.085212] |
| Promoter 300 / R6 | 0.117220 [0.085536, 0.152229] | 0.120241 [0.087786, 0.154665] | 0.314702 [0.260790, 0.363445] | 0.062028 [0.034622, 0.090321] |
| Splice (three classes) / R4 | 0.002277 [-0.039081, 0.045960] | 0.043243 [-0.008853, 0.093992] | 0.133209 [0.077943, 0.188026] | 0.064399 [0.011134, 0.120011] |
| Splice (three classes) / R6 | -0.016913 [-0.057261, 0.024059] | 0.024052 [-0.028991, 0.076471] | 0.114019 [0.056372, 0.169855] | 0.045208 [-0.005042, 0.096414] |
| Mouse TF / R4 | 0.230092 [0.179188, 0.281172] | 0.182214 [0.130341, 0.232183] | 0.314069 [0.254280, 0.374322] | 0.052290 [0.006377, 0.098223] |
| Mouse TF / R6 | 0.138198 [0.074488, 0.200899] | 0.090321 [0.035094, 0.143205] | 0.222176 [0.160346, 0.281397] | -0.039603 [-0.091493, 0.011996] |

### Final norm — fixed base paired AUROC changes

| Task / candidate | −base | −R1 | −composition | −forward 4-mer |
|---|---:|---:|---:|---:|
| H3 / R4 | -0.001011 [-0.019674, 0.015981] | 0.125449 [0.103139, 0.146753] | -0.004622 [-0.024732, 0.013751] | -0.074857 [-0.096017, -0.053972] |
| H3 / R6 | 0.021297 [0.005278, 0.035995] | 0.147757 [0.124401, 0.172591] | 0.017686 [0.000008, 0.034549] | -0.052549 [-0.071819, -0.034217] |
| Human TF / R4 | -0.199053 [-0.262016, -0.137569] | 0.036040 [-0.037955, 0.106667] | -0.039470 [-0.128544, 0.047529] | -0.308976 [-0.373688, -0.244837] |
| Human TF / R6 | -0.177114 [-0.248048, -0.106818] | 0.057979 [-0.011594, 0.124329] | -0.017531 [-0.089607, 0.053984] | -0.287037 [-0.353409, -0.224120] |
| Core promoter / R4 | -0.013093 [-0.052640, 0.025376] | 0.202573 [0.146047, 0.261716] | -0.004387 [-0.035406, 0.027987] | -0.086980 [-0.130906, -0.044333] |
| Core promoter / R6 | -0.061268 [-0.104411, -0.016097] | 0.154398 [0.088480, 0.221805] | -0.052562 [-0.088333, -0.015146] | -0.135155 [-0.180665, -0.088044] |
| Promoter 300 / R4 | 0.074937 [0.037879, 0.111835] | 0.633234 [0.574527, 0.690834] | 0.272419 [0.229349, 0.312385] | 0.019745 [-0.007017, 0.048117] |
| Promoter 300 / R6 | 0.063630 [0.030574, 0.098061] | 0.621927 [0.558972, 0.683369] | 0.261112 [0.216700, 0.302855] | 0.008438 [-0.021265, 0.039076] |
| Splice (three classes) / R4 | -0.082951 [-0.126502, -0.037875] | 0.007630 [-0.044378, 0.058931] | 0.047981 [-0.003268, 0.098701] | -0.020830 [-0.075477, 0.035857] |
| Splice (three classes) / R6 | -0.079757 [-0.125005, -0.031602] | 0.010825 [-0.033902, 0.054754] | 0.051175 [0.005087, 0.097527] | -0.017636 [-0.069122, 0.040203] |
| Mouse TF / R4 | 0.149786 [0.097210, 0.201813] | 0.132183 [0.078327, 0.187104] | 0.233763 [0.172906, 0.292437] | -0.028015 [-0.082688, 0.021867] |
| Mouse TF / R6 | 0.159191 [0.102072, 0.217130] | 0.141588 [0.085289, 0.198622] | 0.243168 [0.184684, 0.301176] | -0.018611 [-0.070760, 0.032305] |

## Where changes appear and what the seeds mean

All-layer profiles show the full block-0–24 and final-norm axes, rather than choosing a favorable hook after looking at scores. The distinct splice results at block 16 and final norm above illustrate why a final-norm-only headline is insufficient. Human-TF fixed transfer also varies substantially across representations while its refitted readout remains useful. The profiles expose these differences for every task and both policies; the paired anchor tables supply uncertainty at the prospectively chosen displays.

A08 verified that 251 of 260 candidate/task/representation groups have identical final parameter content across all three CV seeds; nine have two parameter sets. Different frozen folds can select the same regularization C and yield an identical deterministic full-TRAIN fit. This is explained by fold/selection/parameter identities and the prescribed sampled refit panel. It does **not** establish broad seed robustness or independent checkpoint-training replication. [Seed evidence](../A08-attempt-001/SEED_SAMENESS_AUDIT.json) and [full seed sensitivity](../A08-attempt-001/SEED_SENSITIVITY.csv) retain the scope.

## Task entry and already-declared tasks

The supplied cumulative design is H3 → human TF → core promoter → promoter 300 → splice → mouse TF. [Configuration evidence](INCLUSION_EXPOSURE_PLAN.csv) distinguishes planned membership, first evidenced declaration, exact dataset/version, sampled rows, realized exposure and parent/objective/token-budget comparability. Unknown exposure is not zero exposure.

The following R4 refit changes relative to R1 occur before splice/mouse appear in R4's supplied retain declaration. They are descriptive checkpoint associations, not isolated inclusion transitions or proof of unseen-training-data generalization:

| Task | Block-16 R4−R1 AUROC | Final-norm R4−R1 AUROC |
|---|---:|---:|
| Splice (three classes) | 0.052198 [0.017141, 0.084529] | 0.043243 [-0.008853, 0.093992] |
| Mouse TF | 0.066748 [0.036348, 0.099621] | 0.182214 [0.130341, 0.232183] |

For already-declared H3, human TF, core promoter and promoter 300, the complete anchor tables show changes under both policies. Apparent preservation under a refitted head does not guarantee unchanged-base transfer or establish a noninferiority margin. Unknown parents, objectives, training steps, schedules and realized source/token exposure prevent a controlled causal retain-diversity interpretation. One supplied cumulative ordering cannot identify an optimal mixture.

All five actual adjacent edges—R2−R1, R3−R2, R4−R3, R5−R4 and R6−R5—remain pending or bridge-gated. Their 27,300 classifier keys and 70 LM keys retain null estimates and reasons. R6−R4 is not substituted for either missing adjacent edge.

## Actual causal LM evidence within each task

NLL is total actual next-token loss divided by total valid shifted targets, using saved float32 per-sequence loss sums and float64 corpus aggregation; perplexity is exp(corpus NLL). It is not classifier cross-entropy, an average of sequence perplexities, or a per-layer/seed score. The 12 A06 TRAIN diagnostics remain separate from the 35 available primary units. No task ranking by raw loss or pooled task capability score is justified.

| Task | Base NLL | R1 NLL | R4 NLL | R6 NLL | R6−R4 NLL | R6−R4 perplexity |
|---|---:|---:|---:|---:|---:|---:|
| H3 | 1.307634 | 1.448961 | 1.225060 [1.216481, 1.233303] | 1.226317 [1.218404, 1.234271] | 0.001257 [-0.001769, 0.004457] | 0.004282 [-0.006039, 0.015111] |
| Human TF | 1.343778 | 1.347805 | 1.198158 [1.176056, 1.217985] | 1.186291 [1.164681, 1.206068] | -0.011867 [-0.017903, -0.005552] | -0.039093 [-0.059055, -0.018101] |
| Core promoter | 1.382613 | 1.394802 | 1.298768 [1.285298, 1.311206] | 1.316643 [1.306625, 1.325910] | 0.017875 [0.010659, 0.026129] | 0.066097 [0.039417, 0.095773] |
| Promoter 300 | 1.377407 | 1.451836 | 1.290896 [1.279246, 1.301518] | 1.295791 [1.284453, 1.306033] | 0.004895 [0.001731, 0.008247] | 0.017841 [0.006332, 0.030104] |
| Splice (three classes) | 1.273222 | 1.360422 | 1.183482 [1.167711, 1.199486] | 1.101604 [1.081141, 1.121911] | -0.081878 [-0.091077, -0.072583] | -0.256738 [-0.283291, -0.229425] |
| Mouse TF | 1.387184 | 1.394936 | 1.342015 [1.334109, 1.349094] | 1.336124 [1.327734, 1.343907] | -0.005891 [-0.009599, -0.002251] | -0.022476 [-0.036554, -0.008642] |

## Historical R3: accepted domain only

R3 and its base/R1 comparisons remain useful in their verified historical runtime domain. The table below stays separate from current R4/R6 effects; no R4−R3 effect is constructed by subtracting baseline-relative differences. Missing R3 native payload/bridge dependencies remain explicit.

| Task / hook / readout | R3 AUROC | R3−base | R3−R1 (nonadjacent) |
|---|---:|---:|---:|
| H3 / block 16 / refit | 0.955275 | 0.021212 [0.011314, 0.031352] | 0.004880 [-0.000909, 0.010617] |
| H3 / block 16 / fixed | 0.819015 | -0.115048 [-0.134120, -0.096199] | -0.007670 [-0.014239, -0.001044] |
| H3 / final norm / refit | 0.855909 | 0.036019 [0.019890, 0.053485] | 0.016550 [0.005709, 0.028097] |
| H3 / final norm / fixed | 0.837943 | 0.018053 [0.000737, 0.033620] | 0.144512 [0.122195, 0.167058] |
| Human TF / block 16 / refit | 0.828432 | -0.001543 [-0.031863, 0.029524] | 0.026812 [-0.006171, 0.060078] |
| Human TF / block 16 / fixed | 0.659308 | -0.170667 [-0.218291, -0.123553] | 0.014514 [-0.035283, 0.066075] |
| Human TF / final norm / refit | 0.714246 | 0.034573 [-0.019029, 0.090457] | 0.072645 [0.015145, 0.130728] |
| Human TF / final norm / fixed | 0.487755 | -0.191918 [-0.255414, -0.132976] | 0.043175 [-0.032285, 0.112777] |
| Core promoter / block 16 / refit | 0.879799 | 0.062931 [0.030901, 0.098080] | 0.033236 [0.005188, 0.062930] |
| Core promoter / block 16 / fixed | 0.698270 | -0.118599 [-0.166553, -0.066592] | 0.104453 [0.050339, 0.156231] |
| Core promoter / final norm / refit | 0.837011 | 0.075627 [0.035948, 0.117341] | 0.063725 [0.031698, 0.095819] |
| Core promoter / final norm / fixed | 0.748505 | -0.012879 [-0.051534, 0.025884] | 0.202786 [0.149395, 0.260671] |
| Promoter 300 / block 16 / refit | 0.966430 | 0.012039 [-0.002300, 0.026993] | 0.002792 [-0.008700, 0.014209] |
| Promoter 300 / block 16 / fixed | 0.394308 | -0.560082 [-0.612261, -0.509719] | -0.168612 [-0.232867, -0.109993] |
| Promoter 300 / final norm / refit | 0.836332 | -0.000580 [-0.040356, 0.041734] | 0.002441 [-0.036227, 0.042105] |
| Promoter 300 / final norm / fixed | 0.656596 | -0.180316 [-0.235816, -0.122800] | 0.377981 [0.320872, 0.440956] |
| Splice (three classes) / block 16 / refit | 0.772349 | -0.015513 [-0.048207, 0.020142] | 0.050243 [0.018868, 0.082140] |
| Splice (three classes) / block 16 / fixed | 0.565251 | -0.222611 [-0.264228, -0.179736] | 0.062091 [0.025503, 0.103080] |
| Splice (three classes) / final norm / refit | 0.583155 | -0.050679 [-0.096799, -0.002135] | -0.009713 [-0.052729, 0.035328] |
| Splice (three classes) / final norm / fixed | 0.511555 | -0.122279 [-0.173519, -0.069280] | -0.031697 [-0.074456, 0.011917] |
| Mouse TF / block 16 / refit | 0.878260 | 0.001313 [-0.027421, 0.029687] | 0.044168 [0.015725, 0.073613] |
| Mouse TF / block 16 / fixed | 0.727710 | -0.149237 [-0.191749, -0.107806] | 0.130641 [0.090653, 0.172424] |
| Mouse TF / final norm / refit | 0.848153 | 0.237496 [0.183113, 0.292489] | 0.189618 [0.136037, 0.241254] |
| Mouse TF / final norm / fixed | 0.784641 | 0.173985 [0.118564, 0.227030] | 0.156382 [0.103106, 0.209314] |

## Exploratory test, limits and reproducibility

H3's previously examined test records are explicitly `test_exploratory` and appear in separate tables/figures. They are not an untouched test, were not pooled with dev, and did not select C, a layer or a seed. Other tasks use the established official dev only. Numeric label consistency does not resolve missing biological TF/label metadata. Exact/RC groups prevent the frozen duplicate leakage definition; they do not prove locus/homology independence.

These benign measurements alone establish neither successful unlearning/forgetting nor information erasure or resistance to relearning. Pod B owns relearning on another server. Saliency/perturbation remains deferred to a separate scope and approval. No missing checkpoint was interpolated or downloaded in A09.

A08 independently checked every eligible saved-output probability, point metric, draw mask/value, paired delta and interval at the frozen tolerances. Its 60-unit independent refit panel is sampled; it is not a second fit of all 780 heads. A09's [audit release table](AUDIT_RELEASE_STATUS.csv) reconciles the frozen plan with those completed receipts without rewriting producer seals. [Report repairs](REPORT_REPAIR_LOG.json) retain the original handoff, plan and control IDs. [Data dictionary](DATA_DICTIONARY.md), [figure gallery](FIGURE_GALLERY.md), [recovery graph](RECOVERY_DEPENDENCY_GRAPH.json), [restore commands](RESTORE.md) and [handoff](SESSION_HANDOFF.md) bind exact sources and scope. Saved-analysis recovery is distinct from full GPU/model recreation.
