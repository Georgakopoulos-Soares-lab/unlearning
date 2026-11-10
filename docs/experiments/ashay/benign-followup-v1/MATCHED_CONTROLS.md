# Matched low-complexity controls

Exploratory follow-up to the completed scientific run, explicitly designed after seeing its results. New CPU work: 36 final control fits (2 controls ×6 tasks ×3 CV seeds); existing Evo2/H3-only features, probes and predictions remain unchanged. No GPU, backbone training or untouched test access. This does not answer the missing multi-retain question.

Composition uses four A/C/G/T counts divided by canonical-base count. 4-mers use all256 lexicographic ACGT overlapping forward-strand counts divided by the number of valid windows. N/ambiguous bases and windows are excluded from denominators; no RC averaging, length feature, padding or special tokens. Zero denominator raises. Definitions recovered unchanged from benign_pilot/extension.py at scientific commit3d82ba6. Existing historical controls were not declared compatible, so all36 were newly fitted on exact current manifests. Historical H3 AUROC0.8955 is not a matched effect estimate here.

Same saved grouped training folds for42/17/1234, fold-local StandardScaler, balanced L2 LBFGS, C=.1/1/10, training-CV AUROC and smaller-C tie, all-training refit, optimizer42, tol1e-4,2000 then10000 convergence retry. CV seeds vary folds/C selection, not intervention replicates. Controls fit once per task/seed and reused at both predeclared representations. H3 test is explicitly exploratory reuse; other tasks use their existing official-dev cohorts only. H3 dev is included in full CSVs separately.

## AUROC comparison

All seeds shown; binary class1 except splice macro-OVR. Decoder layer16 is zero-based (17th block). Nine-decimal display; full machine precision in metrics.csv. Controls are the same fitted heads across layer rows, not repeated fits.

| Task/split | Layer | CV seed | Composition | 4-mer | Base refit | H3-only refit | H3-only fixed-base |
|---|---|---:|---:|---:|---:|---:|---:|
| emp_H3/test | decoder_layer_16 | 42 | 0.805360490 | 0.895451706 | 0.935324253 | 0.950738116 | 0.847817783 |
| emp_H3/test | decoder_layer_16 | 17 | 0.805353350 | 0.895451706 | 0.935324253 | 0.950738116 | 0.847817783 |
| emp_H3/test | decoder_layer_16 | 1234 | 0.805360490 | 0.895451706 | 0.935324253 | 0.950738116 | 0.847817783 |
| emp_H3/test | final_norm | 42 | 0.805360490 | 0.895451706 | 0.833096517 | 0.842691134 | 0.668706378 |
| emp_H3/test | final_norm | 17 | 0.805353350 | 0.895451706 | 0.833096517 | 0.842691134 | 0.668706378 |
| emp_H3/test | final_norm | 1234 | 0.805360490 | 0.895451706 | 0.833096517 | 0.842691134 | 0.668706378 |
| gue_prom_300_all/dev | decoder_layer_16 | 42 | 0.639429313 | 0.892103456 | 0.954390784 | 0.963637751 | 0.562920577 |
| gue_prom_300_all/dev | decoder_layer_16 | 17 | 0.639429313 | 0.892103456 | 0.954390784 | 0.963637751 | 0.562920577 |
| gue_prom_300_all/dev | decoder_layer_16 | 1234 | 0.639429313 | 0.892103456 | 0.954390784 | 0.963637751 | 0.562920577 |
| gue_prom_300_all/dev | final_norm | 42 | 0.639429313 | 0.892103456 | 0.836911574 | 0.833890288 | 0.278614481 |
| gue_prom_300_all/dev | final_norm | 17 | 0.639429313 | 0.892103456 | 0.836911574 | 0.833890288 | 0.278614481 |
| gue_prom_300_all/dev | final_norm | 1234 | 0.639429313 | 0.892103456 | 0.836911574 | 0.832242313 | 0.278614481 |
| gue_prom_core_all/dev | decoder_layer_16 | 42 | 0.752678081 | 0.835271318 | 0.816868095 | 0.846563511 | 0.593816761 |
| gue_prom_core_all/dev | decoder_layer_16 | 17 | 0.752830678 | 0.835271318 | 0.816868095 | 0.846563511 | 0.593816761 |
| gue_prom_core_all/dev | decoder_layer_16 | 1234 | 0.752678081 | 0.835271318 | 0.816868095 | 0.846563511 | 0.593816761 |
| gue_prom_core_all/dev | final_norm | 42 | 0.752678081 | 0.835271318 | 0.761383751 | 0.773286333 | 0.545718122 |
| gue_prom_core_all/dev | final_norm | 17 | 0.752830678 | 0.835271318 | 0.761383751 | 0.773286333 | 0.545718122 |
| gue_prom_core_all/dev | final_norm | 1234 | 0.752678081 | 0.835271318 | 0.761383751 | 0.773286333 | 0.545718122 |
| gue_splice_reconstructed/dev | decoder_layer_16 | 42 | 0.502901710 | 0.571712077 | 0.787861982 | 0.722105246 | 0.503159423 |
| gue_splice_reconstructed/dev | decoder_layer_16 | 17 | 0.502901710 | 0.571712077 | 0.787861982 | 0.722105246 | 0.503159423 |
| gue_splice_reconstructed/dev | decoder_layer_16 | 1234 | 0.502901710 | 0.571712077 | 0.787861982 | 0.722105246 | 0.503159423 |
| gue_splice_reconstructed/dev | final_norm | 42 | 0.502901710 | 0.571712077 | 0.633833638 | 0.592868187 | 0.543251829 |
| gue_splice_reconstructed/dev | final_norm | 17 | 0.502901710 | 0.571712077 | 0.633833638 | 0.592868187 | 0.543251829 |
| gue_splice_reconstructed/dev | final_norm | 1234 | 0.502901710 | 0.571712077 | 0.633833638 | 0.592868187 | 0.543251829 |
| gue_tf_0/dev | decoder_layer_16 | 42 | 0.520090138 | 0.789595906 | 0.829974792 | 0.801619433 | 0.644794133 |
| gue_tf_0/dev | decoder_layer_16 | 17 | 0.519799863 | 0.789595906 | 0.829974792 | 0.801619433 | 0.644794133 |
| gue_tf_0/dev | decoder_layer_16 | 1234 | 0.520090138 | 0.789595906 | 0.829974792 | 0.801619433 | 0.644794133 |
| gue_tf_0/dev | final_norm | 42 | 0.520090138 | 0.789595906 | 0.679673058 | 0.641601100 | 0.444580246 |
| gue_tf_0/dev | final_norm | 17 | 0.519799863 | 0.789595906 | 0.679673058 | 0.640485830 | 0.444580246 |
| gue_tf_0/dev | final_norm | 1234 | 0.520090138 | 0.789595906 | 0.679673058 | 0.640485830 | 0.444580246 |
| gue_mouse_0/dev | decoder_layer_16 | 42 | 0.526679389 | 0.788458015 | 0.876946565 | 0.834091603 | 0.597068702 |
| gue_mouse_0/dev | decoder_layer_16 | 17 | 0.526374046 | 0.788458015 | 0.876946565 | 0.834091603 | 0.597068702 |
| gue_mouse_0/dev | decoder_layer_16 | 1234 | 0.526480916 | 0.788458015 | 0.876946565 | 0.834091603 | 0.597068702 |
| gue_mouse_0/dev | final_norm | 42 | 0.526679389 | 0.788458015 | 0.610656489 | 0.658534351 | 0.628259542 |
| gue_mouse_0/dev | final_norm | 17 | 0.526374046 | 0.788458015 | 0.610656489 | 0.658534351 | 0.628259542 |
| gue_mouse_0/dev | final_norm | 1234 | 0.526480916 | 0.788458015 | 0.610656489 | 0.658534351 | 0.628259542 |

## Evidence beyond controls

- emp_H3, decoder_layer_16: H3-only refit minus 4-mer has positive conditional interval for 3/3 CV seeds, negative for 0/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- emp_H3, final_norm: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 3/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_prom_300_all, decoder_layer_16: H3-only refit minus 4-mer has positive conditional interval for 3/3 CV seeds, negative for 0/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_prom_300_all, final_norm: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 3/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_prom_core_all, decoder_layer_16: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 0/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_prom_core_all, final_norm: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 3/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_splice_reconstructed, decoder_layer_16: H3-only refit minus 4-mer has positive conditional interval for 3/3 CV seeds, negative for 0/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_splice_reconstructed, final_norm: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 0/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_tf_0, decoder_layer_16: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 0/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_tf_0, final_norm: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 3/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_mouse_0, decoder_layer_16: H3-only refit minus 4-mer has positive conditional interval for 3/3 CV seeds, negative for 0/3; all exact differences/intervals in AUROC_CONTRASTS.csv.
- gue_mouse_0, final_norm: H3-only refit minus 4-mer has positive conditional interval for 0/3 CV seeds, negative for 3/3; all exact differences/intervals in AUROC_CONTRASTS.csv.

These counts describe pointwise conditional intervals, not an adjusted family-level test or independent replication. Positive differences support predictive performance beyond a specific control under the measured linear-probe protocol; they do not establish biological understanding, causal mechanisms, successful unlearning, or absent information. Negative intervals and unresolved differences remain visible. Composition and 4-mer do not exhaust all low-complexity methods.

Exact paired model-minus-control contrasts for both controls, all three model policies, all seeds, both anchors and all five metrics are in contrasts.csv; AUROC_CONTRASTS.csv is the primary-split subset. Intervals use the original2000 exact/RC-group draws on identical examples, conditional on fixed fitted heads. No homology guarantee, multiplicity adjustment or preservation margin; nonsignificance is uncertainty. Fixed-base transfer and refits answer different readout questions.

Independent verification uses separate pairwise-wins AUROC and threshold-indicator AP, all metric resamples and intervals, saved-head reconstruction, exact ID/label/class/group/sequence joins and CV-selection/convergence accounting. See VERIFICATION.json and SUPPLEMENTAL_VERIFICATION.json. A first attempt misinterpreted historical bootstrap arrays as absolute metrics; they actually store post-minus-base contrasts. Failure log preserved, saved first head reused, and corrected comparisons independently reconstructed without repeating that fit or changing feature definitions. No released units from the failed attempt.

Source anchor files and original receipt hashes are recorded in SOURCE_ANCHORS.json; copied predictions/bootstrap/results are included in the new backup. CPU saved-output checks do not regenerate GPU features. The source scientific artifacts remain read-only. Runtime, execution and final backup receipts accompany the report; model weights and installed runtime are excluded. No Pod shutdown or collaborator messages.

## Short answer across both controls

At block16, the following task/model pairs have positive model-minus-control AUROC intervals for **both controls in all three seeds** (descriptive count of correlated, unadjusted intervals):

- base_refit: emp_H3, gue_mouse_0, gue_prom_300_all, gue_splice_reconstructed, gue_tf_0.
- h3_only_refit: emp_H3, gue_mouse_0, gue_prom_300_all, gue_splice_reconstructed.

These observations support performance beyond these specific controls at the declared anchor; they do not establish global significance across layers/tasks or information absence elsewhere. All outcomes, including final-normalization deficits and inconclusive comparisons, remain in the tables.

Same search policy does not equalize feature dimension/capacity (4/256 control dimensions versus1920 model features). This is performance relative to specified controls, not a mechanistic attribution. Private archive/sidecar and446 payload hashes passed forced-download verification; all36 restored control heads/42 heldout probability arrays reconstructed exactly. See backup_receipt.json and RESTORE.md.
