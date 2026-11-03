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

## Five-task official-dev extension

Each task uses1024 official training rows and512 official dev rows from the historical hash-pinned GUE archive. No test member contents were opened. Five identical task-local grouped training CV folds per model; same C grid, scaling and balanced logistic policy as above. Binary decision p(class1)>=.5; splice uses3-class argmax and macro one-vs-rest AUROC. These reused dev analyses are exploratory. TF aliases/numeric biological class meanings remain incompletely qualified; mouse/0 is a benign TF task, not host tropism. No cross-task causal-NLL ranking or preservation margin is asserted.

|Task|Representation|Base AUROC|MaxEnt refit AUROC|Refit difference [paired95% CI]|Base accuracy|MaxEnt accuracy|
|---|---|---:|---:|---|---:|---:|
|Promoter|Final norm|0.836912|0.833890|-0.003021 [-0.043876, +0.038179]|0.763672|0.740234|
|Promoter|decoder.layers[16]|0.954391|0.963638|+0.009247 [-0.003233, +0.022708]|0.894531|0.890625|
|Splice (macro OVR)|Final norm|0.633477|0.593323|-0.040155 [-0.087416, +0.006897]|0.398438|0.382812|
|Splice (macro OVR)|decoder.layers[16]|0.787930|0.721980|-0.065951 [-0.100909, -0.032580]|0.656250|0.560547|
|Core promoter|Final norm|0.761384|0.773286|+0.011903 [-0.031836, +0.054586]|0.675781|0.724609|
|Core promoter|decoder.layers[16]|0.816868|0.846564|+0.029695 [-0.004860, +0.063562]|0.748047|0.783203|
|Human TF (tf/0)|Final norm|0.679673|0.641601|-0.038072 [-0.102639, +0.025286]|0.642578|0.599609|
|Human TF (tf/0)|decoder.layers[16]|0.829975|0.801619|-0.028355 [-0.061276, +0.005762]|0.755859|0.722656|
|Mouse TF (mouse/0)|Final norm|0.610656|0.658534|+0.047878 [-0.018430, +0.112736]|0.587891|0.623047|
|Mouse TF (mouse/0)|decoder.layers[16]|0.876947|0.834092|-0.042855 [-0.076295, -0.012301]|0.773438|0.751953|

### Fixed-base probe transfer on official dev

|Task|Representation|Fixed-base probe on MaxEnt AUROC|Difference from base [paired95% CI]|
|---|---|---:|---|
|Promoter|Final norm|0.278614|-0.558297 [-0.620338, -0.491869]|
|Promoter|decoder.layers[16]|0.562921|-0.391470 [-0.445187, -0.336626]|
|Splice (macro OVR)|Final norm|0.543825|-0.089652 [-0.138026, -0.038671]|
|Splice (macro OVR)|decoder.layers[16]|0.503239|-0.284691 [-0.334999, -0.235129]|
|Core promoter|Final norm|0.545718|-0.215666 [-0.279983, -0.152207]|
|Core promoter|decoder.layers[16]|0.593817|-0.223051 [-0.283185, -0.167297]|
|Human TF (tf/0)|Final norm|0.444580|-0.235093 [-0.305707, -0.165357]|
|Human TF (tf/0)|decoder.layers[16]|0.644794|-0.185181 [-0.239495, -0.130310]|
|Mouse TF (mouse/0)|Final norm|0.628260|+0.017603 [-0.049387, +0.083776]|
|Mouse TF (mouse/0)|decoder.layers[16]|0.597069|-0.279878 [-0.334495, -0.226705]|

Splice and mouse-TF layer16 refit differences are negative with pointwise conditional intervals excluding zero; H3 is positive. Other refit intervals include zero. These task/layer-dependent reference-model findings do not establish a verified causal before/after intervention, general biological capability loss, or knowledge removal. Fixed-probe transfer often degrades substantially while refitting recovers stronger task performance; both policies remain visible. All intervals are unadjusted, conditional on fitted probes, and account only for available exact/RC groups rather than unknown homology dependence.

232 metric rows and32 paired-contrast rows are scalar records, not232 independent experiments. Independent verification covered11108 prediction rows and42 model/layer/split conditions. All2000 draws per reported AUROC contrast were reconstructed with maximum difference4.44e-16; rejected missing-class draws are explicitly counted (all zero here).

Paired H3 test causal NLL difference: +0.14514574 [0.12537835,0.16381101]; perplexity difference +0.57931071 [0.49536052,0.65969770]. These reuse the same prespecified whole-sequence draws and aggregate loss sums/target counts.

## Completion, compute and recovery

All six benign tasks, both prespecified representations and both probe policies are complete. New raw features:22645 rows/model,45290 total; no new backbone training. Actual additional GPU-stage wall time charged: 555.235429s; cumulative 1423.988606/7200s, inactive. This is recorded GPU-stage wall time, not rental billing. CPU fitting/uncertainty and download/setup are separately recorded. No extra GPU job remains.

New raw outputs are under /workspace/meeting-artifacts/maxent-benign-v16; headers/metadata/code and small numerical reports are committed here. A local checked recovery package is prepared separately; off-Pod upload and retrieval verification are pending securely configured private-HF authentication. No token was persisted or reused from conversation history. Historical parent/supplement backups remain unchanged.

The next useful action is immutable parent/conversion-lineage and training-exposure confirmation, then a separately authorized diverse benign retain experiment using splice/mouse-TF as monitoring tasks. A first retain mixture/proportions has not been finalized; this run did not train one. No HVUE predictor evaluation was performed or completed.

Runtime qualification: this locally executed route uses native checkpoint BF16/FP32 values, shared unfused TE attention and explicit hooks. It is not a claim of historical cluster/runtime equivalence. See RUNTIME_STATUS.md for declared dependency exceptions and the exact validated scope.

Final loss verification independently recomputed all42 classifier cross-entropies with actual saved-model float64 probability precision, plus28 causal-NLL/perplexity scalar records from sequence loss/count statistics. Maximum difference1.78e-15. Together with rank/count verification, all232 new scalar metric records were recomputed; this does not constitute independent GPU replication. The initial independent CE checker incorrectly assumed float32 and was corrected using fitted-model dtype evidence; measured results were unchanged.

Local recovery archive: /workspace/meeting-artifacts/maxent-benign-v16-recovery.tar.gz; SHA256 94e7e86f007fa6b317a433d4be0e402819f7fc5e834c92dc804e00c73edf6d46; 700410986 bytes;5914 payloads verified through archive readback. Off-Pod upload/retrieval remains pending; no new HF revision claimed. The additional loss-verification receipt postdates this immutable scientific-payload snapshot and is saved in Git.
