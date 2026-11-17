# B02 reconstruction decision

All 36 delivered adapters remain blocked for full-model reconstruction. Their historical CPU integrity is established, and B02 found a source-supported adapter API candidate. Neither the actual training runtime nor a hash-bound parent assignment has been established. No candidate was imported, constructed or run. Evidence IDs below resolve in `INVENTORY_RECEIPT.json`; the JSONL registry is canonical.

## What the delivery establishes

E01 preserves 18 base-labeled and 18 MaxEnt-labeled payloads, steps100–1800, with distinct archival hashes **and** distinct tensor-content fingerprints. Each historical model extraction contains200 finite bf16 adapter tensors across100 modules. One required `__0_0.distcp` shard (173,352,705bytes) was historically complete. E03 confirms unchanged current file IDs/sizes/mtimes, not a new byte-hash audit. There are no newly discovered trajectory checkpoints or incomplete historical payloads. Optimizer descriptors exist in `common.pt`; model-only extraction excluded optimizer entries, so complete optimizer/RNG resumability is not established here.

E02 finds one shared tensor key/shape/dtype schema, SHA256 `38a84e1cd2b75b58e7a6d61fb2114238d17812f7301a5e00e2f5e1091b831e78`, expanded once in `ADAPTER_TENSOR_SCHEMA.json`. Saved keys end in `.adapter.linear_in.weight` or `.adapter.linear_out.weight`. The model tensor extraction contains no non-adapter model values. Separate adapter tensors do not prove that the absent backbone was never changed or merged earlier.

| Config family | Members | run_config.yaml SHA256 | Difference from base |
| --- | --- | --- | --- |
| base_all | base100–1800,18 | `69b1920a8bf46ab226d1282d83ae4ffab75167bb8c9cd8eaeb17b982055083a0` | reference |
| maxent_initial | MaxEnt100–1600,16 | `5e60857d3dc2781a9bd0664330f1cfc80b3bba1d7e42ea8ec572cf86ae890324` | pretrained parent path |
| maxent_restart | MaxEnt1700–1800,2 | `7f86c8f52cc04dd053bc466eee151dbef533e9e9257347f9d9ef976d27ec6812` | same MaxEnt parent; finetune=false instead of true |

The two differing YAML leaves are declarations, not observed loading events. All families declare rank16, alpha32 (nominal scale2), dropout0.1 before the adapter, Xavier A/zero B initialization, no skip-freeze modules, empty canonical mapping and these six targets: `dense_projection,dense,linear_qkv,linear_proj,linear_fc1,linear_fc2`. Serialized `params_to_save` is derived bookkeeping, not a constructor option to forward blindly. The saved actual tensors, not a generic target count, define required coverage.

Declared architecture is25 blocks, hidden1920,15 attention heads, vocab512 and tied embedding/output weights; seq_length1000. The tokenizer.json hash is `d8b5392d4795e3011b648b7e79a1e2f563cfa508200196d30d6dcbb0292d0803`. This does not prove tokenizer/head identity of the runtime actually used to train. Current absolute reconstruction requires the missing backbone identity even though adapter storage itself is intact.

## Original implementation versus candidates

No original training implementation has been directly identified. E06 traces the public Evo2LoRA implementation to [Apr23 commit1263f64](https://github.com/NVIDIA-BioNeMo/bionemo-recipes/blob/1263f64629ecd27e9333f28923e728c381a9cf2c/bionemo-recipes/recipes/evo2_megatron/src/bionemo/evo2/models/evo2_lora.py); its Git blob `a79acacbd26139dd617b494ac96f8370ec8cdb85` is identical at previously proposed [Nov12 commit19ee432](https://github.com/NVIDIA-BioNeMo/bionemo-recipes/blob/19ee43214fec23e87916efd468eaa62df47dba3e/recipes/evo2_megatron/src/bionemo/evo2/models/evo2_lora.py). A June16 source move explains the changed path. Although the later commit postdates the jobs, this class implementation predates them. Availability and byte identity do not prove that these jobs used it.

| Route | Exact source | Static decision | Remaining prerequisite |
| --- | --- | --- | --- |
| R0 original | unknown actual BioNeMo/Bridge/Core revisions plus any dirty diff | preferred if provided; not identified | source/runtime receipt and per-job loaded hashes |
| R1 direct drop-in to existing parent runtime | Evo2LoRA blob above + existing Bridge`18ef1b61309dd45bc0535fb7c60064b9d8829a35` | ruled out as an unchanged drop-in: required `_walk_model`/canonical/API fields absent | cannot call this exact-compatible merely because parent inference passed |
| R1b earliest recipe environment | Apr23 recipe pyproject pins Bridge`549e3cb970c170b1d7a86d021261efe05e8a5d9f` | class walk API exists, but saved `share_expert_adapters`/`normalize_moe_lora` fields absent; unchanged full-config route mismatches | an authoritative version/explicit equivalence qualification; do not silently discard fields |
| R2 official adapter API candidate | same Evo2LoRA blob + Bridge v0.5.0 resolved `fcbb6031103d0ca845c1a54d4fee55ecfcca17b6` (June16) | all inspected serialized adapter fields supported; tensor naming/scaling/selection and load order statically align | full provider/Core/TE/runtime compatibility and original/equivalent inference numerical gates; parent assignment still missing |
| R3 project launcher/example | unlearning `bionemo@b90fc1853d1d3be79922a98a2649c91c89716637` | relevant context, not exact executed launch; seq1024/GBS64/max20k/save1000 differ | actual job command/stdout; its eval comment cannot substitute for weight contents |

The R2 classification is **statically compatible adapter API**, not a qualified full runtime. The Nov12 whole pyproject also changes CUDA/FlashAttention/causal-conv dependencies; wholesale installation is neither justified nor B02-authorized. No arbitrary replacement LoRA implementation is proposed. A future bridge/backport route must record exactly which source semantics it preserves and obtain the same numerical qualification; it cannot inherit the name of the original implementation.

## Source-supported loading and forward behavior

E07 inspects Bridge v0.5.0 [`peft/lora.py`](https://github.com/NVIDIA-NeMo/Megatron-Bridge/blob/fcbb6031103d0ca845c1a54d4fee55ecfcca17b6/src/megatron/bridge/peft/lora.py), `base.py`, `module_matcher.py`, `lora_layers.py`, `utils.py`, `adapter_wrapper.py`, `training/setup.py` and `checkpointing.py`. Private inert text copies and per-file source/blob/hash receipts remain in the stage artifact.

1. The recipe constructs Evo2LoRA from LoRA CLI/config arguments. Target matching uses short names or anchored wildcard paths; empty exclusion/canonical maps retain explicit targets. Native mappings must enumerate exactly100 adapted modules and200 saved tensors. No unreported embedding/output/norm adapter or extra unfrozen base parameter is supported by this payload.
2. The PEFT pre-wrap hook loads `pretrained_checkpoint` into the backbone first, with finetune=true and `ignore_ckpt_step=True`, before attaching adapters. The inspected parent Bridge and R2 share this central ordering, although neither is proven to be the original job runtime.
3. After construction, an existing `checkpoint.load` directory sets finetune=false and resumes adapter/training state. Otherwise a fresh adapter remains on the separately loaded pretrained backbone. Saved early finetune=true and late false are consistent with this order; config capture timing/runtime identity are still unknown.
4. With explicit ckpt_step=null, current Bridge resolves an iteration-directory path directly, otherwise discovers latest via `latest_train_state.pt`, then the legacy pointer. Parent pre-wrap ignores the adapter's step override. A directory string does not identify the files selected on Nov9/10. Today's pointer cannot establish the pointer then.
5. PEFT resume filters model keys and loads non-strictly; the save path filters model state to adapter/trainable entries. This explains why a full parent is still required. B04 must independently assert exact key coverage rather than accept `ignore_all` or `strict=False` as success. Non-model optimizer/RNG state is irrelevant to frozen evaluation, but extra inference-relevant model state cannot be ignored.
6. `AdapterWrapper.state_dict/sharded_state_dict` preserves original backbone prefixes and adds `adapter.`; internal `.to_wrap` module names must not be normalized by arbitrary string deletion. Native sharded names must be matched explicitly against the shared200-key schema.
7. `ParallelLinearAdapter` computes a low-rank branch scaled by alpha/dim=2. `LoRALinear` adds it to the base output and preserves the base bias. For fused layernorm linears it uses the layernorm output, not necessarily raw x. A generic linear substitution can therefore be wrong despite matching matrix dimensions. B04 must check attention/MLP/Hyena target layouts and fused FC1 geometry.
8. Evaluation mode disables dropout and the training-only Hyena recompute-gradient patch. Tied embedding/output validation requires symmetric targeting/freezing; neither member is in the delivered targets. Do not invoke merge code: start with separate adapters and unchanged qualified output head. An existing merged-backbone history remains an external identity question.

## Parent/resume contradiction and competing explanations

Both **load and save** declarations, plus internal `.metadata` saved paths, name `/projects/MENTISLab/unlearning/results/evo2_causal_lm_maxent/lora_host_tropism_maxent/checkpoints`. Base pretrained declaration is `/projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge`; MaxEnt declares `/projects/MENTISLab/unlearning/results/evo2_maxent/emp_h3_human_host_tropism/checkpoints`. No authoritative command override or selected file hashes were found.

| Hypothesis | Supporting observation | Constraint/contradiction | Discriminating evidence | Status |
| --- | --- | --- | --- | --- |
| Output path reused after directory move/clear between runs | base job Nov9; MaxEnt jobs Nov10; separate delivered folders with same internal save path | no actual move/clear/startup log | job11760341/11776574 startup and filesystem/load receipts | unresolved |
| Copied/stale config path or hidden override | label/path disagreement and public launcher mismatch | internal checkpoint path agrees with config, so more than a filename is involved | executed command and resolved config/stdout | unresolved |
| MaxEnt resumed its own step1600 for1700/1800 | restart job11803647; finetune becomes false; counters continue | no resumed adapter hash/file identity or optimizer-success trace | restart stdout and hash of adapter actually resumed | consistent, not proven |
| Cross-series adapter resume was active from shared directory | both load declarations equal | early saved finetune=true would be inconsistent with an existing resume under inspected setup semantics, if captured after setup | original source plus initial startup/resume receipt | unresolved; conditional source evidence weighs against an early active resume |
| Resume completely overrides pretrained backbone | naive reading of shared load string; example comment claims full state | observed model payload contains only adapters; inspected pre-wrap explicitly loads distinct pretrained backbone first | original runtime/load transcript, including every parent payload hash | ruled out as an inference from paths/comment alone; actual shared backbone remains neither established nor excluded |
| Another runtime version resolves paths differently | original runtime unknown; saved fields newer than installed parent API | inspected versions agree on backbone-first PEFT ordering | original BioNeMo/Bridge/Core revisions and dirty diff | unresolved |

Available base conversioniter1 and H3iter2000 inputs have historical129-file identities (E11) and parent-only qualification (E12/E13). H3 current pointer is2000 and its small log records job11266761 on Oct20. These are available references, not proof of actual selected parents or full pre-relearning state. Initial adapters could have been fresh, resumed or otherwise initialized. Declared zero B initialization does not establish actual step0 when loading behavior is unknown.

## Starts, runs and exposure

E04 identifies base job11760341 (Nov9 17:57:27–20:32:37), MaxEnt job11776574 (Nov10 11:47:07 through1600 at14:04:11), and restart11803647 (16:48:20 start;1700 at16:57:29;1800 at17:11:47). `TRAJECTORY_MAP.csv` preserves these segments; the1600→1700 edge is not silently treated as hash-proven continuation. Multiple jobs are not established independent training seeds.

E05 statically reads the saved scalar schema without unpickling. All36 steps agree with common metadata; sample slots and scheduler count equal128×step, skipped samples0, valid counters0/44928/89856/134784. The source advances iteration/sample counters per processed global batch; skip paths and optimizer-success flags are separate. Logs' rounded tokens(billions) are a nominal samples×configured-sequence-length calculation. No valid-token, unique-example, packing, resampling or duplication accounting was supplied. Current counters show no visible reset at the restart; inherited absolute offsets and exact resumed state remain unproven. Dataset and RNG seed declarations1234 are not verified runtime seeds or biological replication.

No true step-zero adapter exists in the directly listed36 trajectory folders. The relevant older continued-pretrain sibling has only17000–20001 and config seq1024/GBS64, so it is not an initial reference for these series. Larger unrelated folders/datasets were not searched. Step100 is explicitly first delivered, never relabeled zero; neither H3/R3 nor an absent adapter is assumed to be the full initial state.

| Comparison family | Identity readiness now | Conditional future interpretation |
| --- | --- | --- |
| absolute,36 checkpoints | parent/source and adapter numerical qualification blocked | descriptive evaluation may proceed once technically qualified; missing exposure alone need not block |
| adjacent,34 ordering edges | same blockers; MaxEnt1600→1700 also unproven resume edge | describe contrasts between identified delivered states; continuity claims need restart binding |
| true-start-relative | true starts unavailable in addition to identity blockers | require full initial states, not step100 or a merely similar parent |
| first-delivered-relative | step100 exists in each series; identity blocked |34 non-self contrasts possible after B04 and explicit B05 convention approval |
| common step,18 pairs | identity blocked; counters exist | matched-iteration descriptive contrast, not matched exposure/objective attribution |
| matched actual exposure | actual accounting absent plus identity blockers | equal128×step is not valid-token/unique-example matching |
| difference in change | both initial reference arms missing plus identity blockers | require all exact reference arms and B05-approved contrast |

No family is computation-qualified in B02. Full-model identity, association with the named trajectory, and causal attribution are separate decisions. The JSONL and coverage CSV record these statuses for every checkpoint; first-checkpoint adjacent/self-reference rows are explicitly not contrasts.

## Proposed B04 qualification, not execution

First bind each job/config family to authoritative source and exact parent/adapter identities (questions Q1/Q2). Prefer R0. If the original source cannot be recovered, R2 requires an authoritative **training-only benign known-output fixture** from the original route, with hashed row IDs/token IDs/masks and outputs, sufficient to qualify an equivalent inference route. The candidate's own outputs cannot authenticate it. An exact source explanation can resolve provenance; numerical tests still remain.

Use a new POD_B artifact/cache identity for any changed backend. Keep existing weights, frozen manifests, controls and parent receipts read-only. Reuse E11–E13 for their recorded exact inputs/runtime; repeat parent checks only where a changed source/runtime/input invalidates compatibility. Parent-only PASS is not adapter qualification. Do not rerun historical drivers with hardcoded old output roots.

For each route, after approval, inventory the full200-key mapping and target shapes/dtypes; assert every required adapter tensor loaded exactly once, no unexpected inference-relevant tensors, no unintended non-adapter changes, adapter enabled, nominal scale2 and eval dropout disabled. Preserve backbone/tokenizer/output weight identity; assert tied output correspondence and vocab512. Check native layernorm/Hyena/fused linear semantics, masks, positions and causal LM output. Missing/extra backbone values may be expected only in the documented adapter-only load phase, not hidden by a permissive loader.

Numerical gates must use the existing training smoke manifest SHA256 `42d64d32b77e946bc962c32d2b801e485d41a095221af49a492079ff0f76fd30` and compatible historical anchors. Preserve physical batch8, right padding to1000 with pad1, filler-row exclusion and nucleotide-position mean pooling. Verify all25 blocks (`decoder.layers.0`–`.24`) plus `decoder.final_norm`; do not inspect just a favorable layer. Existing display anchors remain zero-based block16 and final norm. Retain **atol1e-4, rtol1e-5**, the original precision, masks and LM-output summed NLL/valid-target-count semantics. Compare all26 representations, valid counts and output-head statistics against authoritative original/equivalent-route training outputs, including repeatability and documented logical1/8 packing at fixed physical8. No new test/dev access or classifier fitting is part of this gate. Select test cases by metadata/config coverage (all three config families, both parent mappings), never scores; B04 must define remaining per-payload checks before use.

Stop/falsify a route for a parent/adapter hash mismatch; incompatible class constructor/provider dependencies; missing/extra target keys; altered scaling, fused-normalized inputs or output head; changed masks/row order/counts; nonfinite outputs; numerical tolerance failure; or a fixture produced solely by the candidate. Do not loosen tolerances, change pooling/precision, merge adapters opportunistically or treat successful imports as scientific identity. A failed candidate stays unqualified. No code implementing these gates was added or run in B02.

## Next-stage boundaries

B03 can reconcile existing recovery/cohort identities through immutable receipts while adapter provenance remains blocked; avoid new archive recovery or duplicate downloads unless its separately approved scope requires them. B04 should prioritize source/parent binding and evaluate R0/R2 under the gates above. B05 should preserve the frozen prospective protocol identity, distinguish the seven comparison families and restart boundary, and approve any first-delivered convention explicitly. None of those stages or their prompt files were opened in anticipation.
