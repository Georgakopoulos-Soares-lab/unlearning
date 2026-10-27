# Original H3 training exposure addendum

The original selected MLP used 1,842 unique training rows (15.39% of 11,971 available), through 2,000 sampled draws at step 250. Its result remains unchanged. This is deterministic sampler reconstruction from the recorded executed code, Torch version and seed, not a draw trace logged during the original run. Batchwise and one-shot reconstruction agreed exactly.

| Step | Draws | Unique rows | Training coverage | Repeated draws | Draw classes 0 / 1 | Unique classes 0 / 1 |
|---|---:|---:|---:|---:|---|---|
| 50 | 400 | 390 | 3.26% | 10 | 179 / 221 | 175 / 215 |
| 100 | 800 | 773 | 6.46% | 27 | 376 / 424 | 366 / 407 |
| 150 | 1200 | 1141 | 9.53% | 59 | 572 / 628 | 548 / 593 |
| 200 | 1600 | 1499 | 12.52% | 101 | 778 / 822 | 731 / 768 |
| 250 | 2000 | 1842 | 15.39% | 158 | 953 / 1047 | 883 / 959 |
| 300 | 2400 | 2181 | 18.22% | 219 | 1125 / 1275 | 1027 / 1154 |

Available for fitting: 11,971 training rows. Features extracted: 14,965 rows across train/dev/test. Rows scored for original reported metrics: 11,971 train, 1,497 dev and 1,497 test. Gradient-exposed unique rows at selected step 250: 1,842; at the final step 300: 2,181. Repeated draws count draws beyond each row’s first appearance.

The saved head has 3,696,002 parameters: LayerNorm(1920), Linear(1920,1920), GELU, Dropout(0.1), Linear(1920,2). LayerNorm starts at unit scale/zero bias; linear weights use Normal(0,1/sqrt(in_features)) and zero bias. AdamW uses betas (0.9,0.95), epsilon 1e-8, no weight decay, batch 8 sampled uniformly with replacement using a separate seed-42 Torch generator. LR rises linearly to 1e-3 over 20 steps then follows cosine decay to 1e-4 at step 300. Only the head is trained.

Checkpoints at steps 50/100/150/200/250/300 were selected on dev AUROC, with exact ties resolved to the earlier step. The threshold was fixed at 0.5. Selected step 250 dev AUROC was 0.820656 and dev classification cross-entropy 0.569582; at step 300 these were 0.816344 and 0.535062. Better classification loss at the last checkpoint does not change the predeclared AUROC selection. The full six-point trajectory is retained in the original selection.json and follow-up figures.

The historical report phrase “All supplied rows were used in their designated splits” can overstate gradient-training coverage if read to mean every training row was used in updates. It describes available/extracted/scored rows, while the executed sampler used the smaller reconstructed set above. This addendum qualifies that wording without changing historical evidence. Limited exposure is a measured protocol limitation; it does not establish why the observed AUROC had its value.
