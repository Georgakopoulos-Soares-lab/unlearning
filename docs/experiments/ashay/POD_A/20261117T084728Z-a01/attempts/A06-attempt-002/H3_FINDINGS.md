# Predeclared H3 displays and interpretation

Seed42 and both anchors were fixed in A05 before R5 outcomes. Each cell is estimate [pointwise exploratory unadjusted95% group-bootstrap interval], conditional on fitted heads. Full precision/all26 hooks/all3seeds/bothpolicies/all5metrics are in RESULTS_LONG.csv and PAIRED_CONTRASTS.csv. Higher AUROC is favorable; deltas are R5 minus reference.

| Split | Hook | Policy | R5 AUROC | R5−base AUROC | R5−R1 AUROC |
|---|---|---|---|---|---|
| dev | decoder.layers.16 | independent_refit | 0.956395 [0.946514, 0.965306] | 0.022331 [0.013200, 0.031675] | 0.005999 [0.000416, 0.011744] |
| dev | decoder.layers.16 | fixed_original_base | 0.826049 [0.805459, 0.845785] | -0.108015 [-0.126474, -0.089932] | -0.000637 [-0.009926, 0.008734] |
| dev | decoder.final_norm | independent_refit | 0.856530 [0.836552, 0.874706] | 0.036640 [0.020509, 0.054997] | 0.017171 [0.005465, 0.029746] |
| dev | decoder.final_norm | fixed_original_base | 0.845878 [0.825470, 0.864524] | 0.025988 [0.009316, 0.040669] | 0.152447 [0.128119, 0.176536] |
| test_exploratory | decoder.layers.16 | independent_refit | 0.950033 [0.939053, 0.960383] | 0.014709 [0.005569, 0.024075] | -0.000705 [-0.007436, 0.005727] |
| test_exploratory | decoder.layers.16 | fixed_original_base | 0.842445 [0.822099, 0.861995] | -0.092879 [-0.112626, -0.075081] | -0.005373 [-0.014232, 0.003165] |
| test_exploratory | decoder.final_norm | independent_refit | 0.866880 [0.848522, 0.884200] | 0.033784 [0.017265, 0.051035] | 0.024189 [0.012895, 0.036053] |
| test_exploratory | decoder.final_norm | fixed_original_base | 0.837729 [0.816990, 0.857717] | 0.004632 [-0.009251, 0.018817] | 0.169022 [0.142722, 0.192990] |

The previously examined H3 test remains separate and exploratory. These are descriptive checkpoint measurements. Supplied membership declarations do not prove parentage, equal tokens/objectives, realized exposure or biological independence. CV seeds are not independent checkpoint-training replicates. No causal mixture effect, unseen-task generalization, equivalence/noninferiority or successful-forgetting claim follows. Adverse, flat and favorable effects are all retained; no score determined coverage or technical gate passage.
