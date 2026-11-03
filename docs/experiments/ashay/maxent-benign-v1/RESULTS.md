# New benign BioNeMo reference-model comparison

H3 primary result is complete. These are genuinely new frozen-checkpoint extractions and logistic-probe measurements, separately from recovered original-backend history. Checkpoint lineage is path-documented but not hash-verified against an upstream parent; describe this as a common-protocol reference comparison, not a verified causal unlearning effect. The supplied test is reused and exploratory.

|Task/split|Exact representation|Probe policy|Base AUROC|MaxEnt AUROC|MaxEnt−base [paired95% CI]|Base accuracy|MaxEnt accuracy|
|---|---|---|---:|---:|---|---:|---:|
|H3/test|decoder.final_norm|separately fitted|0.833097|0.842689|+0.009593 [-0.007612, +0.028001]|0.758183|0.762859|
|H3/test|decoder.final_norm|fixed base scaler/probe|0.833097|0.668706|-0.164390 [-0.191629, -0.136912]|0.758183|0.511690|
|H3/test|decoder.layers[16] output|separately fitted|0.935324|0.950736|+0.015412 [+0.005651, +0.025530]|0.871075|0.882432|
|H3/test|decoder.layers[16] output|fixed base scaler/probe|0.935324|0.847823|-0.087501 [-0.105526, -0.070158]|0.871075|0.739479|

Final-norm refit interval includes zero; layer16 refit difference is positive within this conditional exploratory analysis. Fixed-probe degradation accompanies stronger refitted performance and does not establish absent information or knowledge removal. All prespecified layers/policies are reported.

Test causal LM NLL/perplexity: converted base1.3106501334/3.7085840028; MaxEnt1.4557958699/4.2878947144. These aggregate summed next-token losses by actual valid target counts; classifier CE is separate. Cross-task NLL does not rank biological capability.

Protocol:11971 train/1497 dev/1497 test; original hash-pinned supplied manifest retained. Three identical stratified exact/RC-grouped training folds, fold-local StandardScaler, balanced L2 logistic, C=.1/1/10 (smaller-C ties), seed42, all-train refit. Binary decision p(class1)>=.5. Numeric biological class meanings are not guessed. Pairing uses same1497 examples and2000 fixed resamples; intervals condition on fitted heads/split and do not capture fitting uncertainty, unknown homology dependence or multiple comparisons. Exact/RC groups are singleton; that does not establish homology independence.

Native loading runtime: recipe7dd1659f2103982562d7a23896fb2091200a1f1d, Bridge18ef1b61309dd45bc0535fb7c60064b9d8829a35, Core92c8482e6dcd11c3666c61bb8d1f7e8d0730ed13; Torch2.8.0+cu128, TE2.3.0. TE unfused attention is shared; right-pad1000/pad1, no BOS/EOS insertion for single sequences, nucleotide-only mean pooling. Checkpoint BF16/FP32 values preserved; MaxEnt BF16 filter values are exactly promoted to shared FP32 filter computation. Only TE extra-state differences were permitted; no missing backbone weights or random substitutes. Both backbones frozen/eval and inference_mode. CPU tensor validation found254 finite tensors/model,234 changed. Source scripts and exact cache identities are saved.

Implementation layer16 is explicitly zero-indexed decoder.layers[16], matching the source sweep naming/--probe-layer16 convention; it is not silently called blocks.15. Meeting score lineage is not independently established. Original-backend historical logistic .8469 and4mer .8955 remain separate references and are not subtracted from the new BioNeMo scores as unlearning effects.

Independent checks: all5988 prediction rows (two representations × dev/test) matched original IDs/labels/groups;12 condition/split metrics reconstructed through independent tied-rank/contingency accounting. All2000 paired resamples per condition reconstructed; maximum discrepancy4.44e-16. Three focused tests passed: missing/nonfinite backbone rejection, label association, macro-OVR averaging. This is saved-prediction verification, not independent GPU replication. Full base/maxent extraction stages171.78/171.84 seconds; forward135.24/135.93 seconds; peak3.45GB. H3 CPU fitting/uncertainty99.26 wall seconds and352.26 CPU process seconds. Smokes/failures are included in the cumulative ledger, not hidden.

Artifacts: /workspace/meeting-artifacts/maxent-benign-v16/{base-H3,maxent-H3,H3-probes}. Local shard hashes/IDs in base_download_receipt.json and maxent_download_receipt.json; configs/tokenizers at /workspace/maxent-assets. Dataset/manifests and original recovery artifacts are under /workspace/recovery/maxent-benign. Newly produced raw features/probes/predictions stay outside Git. Private backup for new outputs is pending current securely configured authentication; no credential was persisted or recovered from chat history. No HVUE evaluation or new unlearning training occurred.
