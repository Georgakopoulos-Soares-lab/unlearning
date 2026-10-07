# BioNeMo Evo2 Project Guide
Explorer Cluster (Northeastern), H200 GPU, pip-only environment (no container)

This supersedes the earlier `bionemo_evo2_setup_notes.txt` — everything from
that file is folded in here, plus everything built since (official
classification pipeline, causal-LM continued-pretraining, perplexity
evaluation, and the unlearning pipeline).

---

## 1. Project Goal

Probe whether the Evo2 genomic language model has inherent capability on HVUE and GUE database tasks,
then **unlearn** capability related to HVUE while preserving general genomic-sequence
understanding — using a combination of Gradient Difference unlearning/MaxEntropy Unlearning/RMU/others,
gradient-ratio-based saliency scoring (similar to GRIN), and distillation-based
robustification (UNDO).

---

## 2. Directory Map

```
~/projects/MENTISLab~/bionemo-framework/recipes/evo2_megatron/   <- BioNeMo recipe + .venv
~/projects/MENTISLab~/unlearning/
  checkpoints/evo2_1b_base_mbridge/                            <- converted base checkpoint (iter_0000001)
  data/evo2/
    benchmarks/
      hvue_gue_manifest.fasta                                  <- original labeled HVUE FASTA (train/val/test, label=)
      hvue_train_only.fasta / hvue_val_only.fasta / hvue_test_only.fasta
      jsonl/{train,val,test}.jsonl                              <- classification format
      preprocessed_causal_lm/                                   <- HVUE causal-LM .bin/.idx (hvue_manual_*)
    GUE_benchmark/
      fasta_splits/preprocessed_causal_lm/                      <- GUE (full combined) causal-LM .bin/.idx
      emp_h3_fasta_splits/preprocessed_emp_h3/                   <- GUE EMP-H3 subtask (small, short sequences)
  evo2_classification/                  <- our custom (superseded) classification pipeline
  evo2_classifier_official/             <- OFFICIAL evo2_classifier.py-based classification pipeline (CURRENT)
  evo2_causal_lm_finetune/              <- causal-LM continued pretraining (LoRA + baseline PPL eval)
  evo2_unlearn_pipeline/                <- unlearning pipeline (Gradient Difference, Saliency)
  results/                               <- all job outputs, organized by experiment name
```

---

## 3. Environment Setup

(Unchanged from before — see `bionemo_evo2_setup_notes.txt` section 1 for the
full pip-only build process: conda env, `.ci_build.sh`, the
nvidia-resiliency-ext / causal_conv1d / torch / transformer_engine fixes.)

Every job script sources this pattern:
```bash
module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2
cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate
export CPATH=.../nvidia/nccl/include:.../nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=.../nvidia/nccl/lib:.../nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}
```

**Tokenizer** (used everywhere, always as an absolute path):
```
/projects/MENTISLab/bionemo-framework/recipes/evo2_megatron/tokenizers/nucleotide_fast_tokenizer_256
```
Real vocab_size=256 (byte-level nucleotide), padded to 512 in the model's
embedding table. **Confirmed critical bug**: if this path is omitted when
calling `_evo2_common` directly (as our custom scripts do), it silently
defaults to `"EleutherAI/gpt-neox-20b"` (~50K vocab, completely wrong) —
always pass it explicitly.

---

## 4. Checkpoint Conversion (one-time, already done)

```bash
evo2_convert_savanna_to_mbridge \
  --savanna-ckpt-path arcinstitute/savanna_evo2_1b_base \
  --revision <commit_sha> \
  --mbridge-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
  --model-size evo2_1b_base \
  --tokenizer-path tokenizers/nucleotide_fast_tokenizer_256
```
Must run on a GPU node. Requires `dist_ckpt_strictness = "ignore_all"`
everywhere this checkpoint is loaded (Savanna format has no `_extra_state`
keys that MBridge's loader otherwise expects — confirmed harmless, 254 real
weight keys present and correct).

---

## 5. Data Pipelines

### 5.1 HVUE (forget set)
- **Classification format**: `fasta_to_jsonl.py` converts the labeled
  manifest FASTA into `train/val/test.jsonl` ({"sequence", "label"}).
- **Causal-LM format**: `extract_train_only_fasta.py` (generalizes to any
  split value) pulls out plain per-split FASTAs, then `preprocess_evo2`
  (3 separate config entries, one per split, each with a single
  `train_split`/`valid_split`/`test_split` ratio = 1.0) produces the real
  `.bin`/`.idx` files. **Gotcha confirmed twice**: each `output_prefix`
  entry produces ALL THREE `_train`/`_val`/`_test` suffixed files, but only
  the one matching its own ratio has real content — the other two are
  0-byte placeholders. Always `ls -lh` and check real file sizes before
  writing a `training_data_config.yaml`, never assume the suffix naming.
- Real counts (verified via `check_dataset_lengths.py`):
  train=727,892 / val=276,092 / test=276,048 docs (~1000 tokens/doc).
  Causal-LM test count (276,048) is ~2x the classification JSONL count
  (138,024) because `embed_reverse_complement: true` doubles the data.

### 5.2 GUE (retain set)
Same `preprocess_evo2` pattern, user-provided FASTA. Full combined GUE:
train=1,448,334 / val=167,976 / test=167,976 docs (~672-980 tokens/doc).
**`emp_h3` subtask** (used in a later unlearning run) is a much smaller,
short-sequence GUE subtask — suspected (not yet confirmed) to need heavy
document-concatenation per training window, which may explain a severe
dataloading slowdown (see section 8).

---

## 6. Classification

**Use `evo2_classifier_official/` (the official BioNeMo example), not the
earlier custom `evo2_classification/` pipeline** — the official version
avoids two serious bugs we hit in our own implementation (manually
reconstructing `final_norm` when `post_process=False`, and hand-written
`sharded_state_dict` silently failing to load weights) by simply keeping
`post_process=True` and not calling the output layer.

```bash
torchrun --nproc-per-node 1 evo2_classifier_official/evo2_classifier.py \
    --train-jsonl .../jsonl/train.jsonl --val-jsonl .../val.jsonl --test-jsonl .../test.jsonl \
    --base-ckpt-dir .../evo2_1b_base_mbridge \
    --result-dir .../results/evo2_official --experiment-name <head_only|lora> \
    --num-classes 2 --seq-length-tokens 1024 \
    --train-iters 20000 --global-batch-size 64 --micro-batch-size 16 \
    --warmup-iters 500 --lr 3e-5 --min-lr 3e-6 \
    [--lora-finetune --lora-dim 16 --lora-alpha 32]   # omit for head-only baseline
```
`dataloader_type="cyclic"` by default (reshuffles every epoch — better than
our own earlier `"single"` + one-time-shuffle workaround).

**AUROC evaluation**: `evaluate_auroc.py` calls the script's own `predict()`
with `return_logits=True`, computes AUROC via sklearn. One sbatch per
checkpoint (`eval_head_only_test.sbatch`, `eval_lora_test.sbatch`).

---

## 7. Causal-LM Continued Pretraining (`evo2_causal_lm_finetune/`)

**`train_evo2`'s native `--fasta-data`/`--fasta-file` flags are BROKEN in
this installed version** — `train.py` never actually wires `args.fasta_file`
into anything; `_evo2_common` has no corresponding branch at all (its
`else` clause is a literal `raise ValueError("TODO unsure how to handle
this case")`). The real, working path is `--dataset-config`:

```bash
train_evo2 \
    --dataset-config .../training_data_config.yaml \
    --dataset-dir .../preprocessed_causal_lm \
    --finetune-ckpt-dir .../evo2_1b_base_mbridge \
    --model-size evo2_1b_base --seq-length 1024 \
    --hf-tokenizer-model-path .../nucleotide_fast_tokenizer_256 \
    [--lora-finetune --lora-dim 16 ...]   # full-param fine-tune if omitted
```
`training_data_config.yaml` is a 3-entry list of
`{dataset_prefix, dataset_split, dataset_weight}`.

---

## 8. Perplexity Evaluation

**Pure eval trick** (used throughout): `--max-steps 1 --lr 0 --min-lr 0`
guarantees exactly zero weight drift (a zero-LR optimizer step is a no-op),
with `--eval-iters` sized to cover the *entire* test set in one pass
(`ceil(num_docs / global_batch_size)`), not a sampled subset.

- **Evaluating the original base checkpoint**: point `--finetune-ckpt-dir`
  at `evo2_1b_base_mbridge` directly.
- **Evaluating a LoRA-trained checkpoint**: do NOT use `--finetune-ckpt-dir`
  for this (that mechanism is for loading a *pre-LoRA* base checkpoint,
  before fresh adapters are initialized — pointing it at an
  already-LoRA-trained checkpoint silently drops the adapter weights and
  re-randomizes them). Instead, treat it as a **resume**: same
  `--result-dir`/`--experiment-name` as the original training run, same
  `--lora-finetune` flags, bump `--max-steps` one past the last save.
  **Always verify** the log's `successfully loaded checkpoint from ...`
  line shows the right path and iteration — this exact class of bug
  (checkpoint silently not loading, no error) has bitten us multiple times.
- **Evaluating a full-parameter (no-LoRA) checkpoint** (e.g. Gradient
  Difference output): `--finetune-ckpt-dir` pointing directly at it DOES
  work correctly here, since there's no PEFT transform to conflict with —
  confirmed empirically (embedding weight `first5` values matched the raw
  checkpoint file exactly). For a *specific* iteration among several saved
  checkpoints: either check `train_evo2 --help` for a native
  iteration-selection flag, or use an unambiguous symlink-pointer directory
  containing only that one `iter_XXXXXXX` folder.

---

## 9. Unlearning Pipeline (`evo2_unlearn_pipeline/`)

### Stage 1: Gradient Difference (`train_graddiff.py`) — BUILT, VALIDATED

Objective: `loss = -alpha_forget * CE(forget) + alpha_retain * CE(retain)`
(ascend forget loss, descend retain loss), **full-parameter** (no LoRA —
a validated reference implementation found LoRA "underperforms in
forgetting" compared to full fine-tuning).

Key components:
- `dual_dataset_provider.py`: combines forget (HVUE) + retain (GUE) datasets
  by reusing `Evo2DatasetProvider` independently for each side, then zipping
  samples under `forget_*`/`retain_*` key prefixes into one batch dict.
- `graddiff_forward_step.py`: two forward passes per step (forget, retain),
  combined loss, backward on the combined scalar (correctly backprops
  through both forward graphs in one call — standard autograd).
- CLI exposes `--alpha-forget`/`--alpha-retain` (reference defaults: 1.0/5.0
  — NOT 1.0/1.0 — specifically to resist divergence) and
  `--forget-loss-cap` (0.0=disabled; clamps the unbounded-below forget term
  as a safety valve). **The objective is genuinely unbounded below and CAN
  diverge** — a validated reference saw retain PPL climb 4-9x even at the
  safer 5.0 ratio. Watch "retain loss"/"retain loss PPL" in eval log lines;
  checkpoint frequently (`--save-interval`) so an earlier, less-diverged
  state is recoverable.
- `--save-interval`/`--keep-last-n-checkpoints` decoupled from
  `--eval-interval` (full-parameter checkpoints are much larger than our
  earlier LoRA adapter-only checkpoints — bound retention explicitly,
  default Megatron behavior of "keep everything" can silently exhaust disk).

Run order: `smoketest.sbatch` (tiny, ~20 steps) before any real run, always
— this exact pipeline has caught a wrong-tokenizer bug (worse-than-random
loss, traced via comparing live vs. raw-checkpoint embedding weights) and a
scheduler crash (`lr_decay_steps` going negative when warmup+constant
exceeds max_steps) that would have silently wasted hours of GPU time
otherwise.

### Stage 2: Saliency (`compute_saliency.py`) — BUILT, **NOT YET SMOKE-TESTED**

Computes `score[θᵢ] = |G_f[θᵢ]| / (|G_r[θᵢ]| + ε)` on **θ⁰** (the ORIGINAL
pre-unlearning checkpoint, not the unlearned one — matches GRIN's own
approach), ε = 5th percentile of `|G_r|` (global, single scalar for the
whole model). Per-element masking (not per-tensor).

Standalone script (not `pretrain()`-based) because saliency needs G_f and
G_r computed from two FULLY INDEPENDENT backward passes (zeroed between),
incompatible with `pretrain()`'s one-backward-per-step training loop and
its DDP gradient-bucketing hooks. Reuses only previously-proven components:
- Model construction: same standalone pattern as the official
  `evo2_classifier.py`'s own `_build_classifier_from_checkpoint`.
- Data reading: `IndexedDataset` directly (no tokenizer dependency, unlike
  `GPTDataset`/`BlendedMegatronDatasetBuilder` which needs a specially
  wrapped tokenizer with a `unique_identifiers` property that a plain
  `HuggingFaceTokenizer` lacks — confirmed via a direct failed attempt).
- Labels/loss_mask: replicates the simple shift-by-one scheme empirically
  confirmed earlier (`tokens[i+1]==labels[i]`).

**Known unverified risk**: `IndexedDataset.__getitem__`'s exact return
type/shape has never actually been exercised (only `len()` and
`.sequence_lengths` were used before, in `check_dataset_lengths.py`) — run
the tiny smoke test (`--num-forget-batches 2 --num-retain-batches 2`)
before trusting this on the real subset size.

Default subset size: 50 batches × micro_batch_size 16 = 800 sequences per
side (a representative sample, not the full corpus — adjustable via CLI).

Output: `grad_forget.pt`, `grad_retain.pt`, `saliency_scores.pt`, plus a
printed percentile table of the score distribution — **deliberately does
NOT pick a top-p% threshold automatically**; inspect the distribution first,
then choose p for Stage 3.

### Stages 3 (Noise) and 4 (Distill) — NOT YET BUILT

Noise: clone θ_unlearned, add `N(0, σ²)` only where the Stage 2 mask
selects. Distill: θ_unlearned (frozen teacher) → θ_noisy (student), forward
KL divergence, retain-set data only.

### Deferred: RMU

Considered as an alternative/additional unlearning method, using an Evo-1
reference implementation as a guide. **Paused** — the user's preferred
configuration (`target_direction=joint_probe`, `condition=localized`) both
depend on prerequisite infrastructure we don't have (a trained-probe system,
and a causal layer-localization study) — effectively two more sub-projects
before RMU itself could be built. Set aside in favor of continuing the
Gradient-Difference/Saliency/Noise/Distill pipeline.

---

## 10. Known Issues / Gotchas (cross-referenced, keep checking these)

1. **`--fasta-data`/`--fasta-file` is broken** in this `train_evo2`
   version — use `--dataset-config` instead (section 7).
2. **`preprocess_evo2` single-ratio configs produce 3 files per prefix,
   only 1 real** — always verify with `ls -lh`, never assume.
3. **`_evo2_common` silently defaults to the wrong tokenizer** if
   `hf_tokenizer_model_or_path` isn't passed explicitly — caused a
   worse-than-random-loss bug that took several debugging rounds to trace.
4. **`--finetune-ckpt-dir` ≠ resume** — it's for loading a *pre-PEFT* base
   checkpoint; loading an already-adapted/already-trained checkpoint needs
   the resume mechanism (`cfg.checkpoint.load`, matching
   `--result-dir`/`--experiment-name`) instead.
5. **Scheduler crash** (`lr_decay_steps must be > 0`) whenever
   `warmup_steps + constant_steps >= max_steps` — always check this
   arithmetic for small/smoke-test step counts.
6. **Gradient Difference is unbounded below and can diverge** — monitor
   retain loss/PPL every eval, checkpoint frequently.
7. **Job preemption observed on heavily-shared nodes** (e.g. `d4054`) —
   SIGTERM kills at ~1h regardless of a longer `--time` request, with
   `MaxRSS` far below the memory limit (ruling out OOM) and no evidence of
   a node-wide hardware failure (other users' jobs kept completing
   normally). Suspected scheduler preemption; confirm with cluster admins.
   Workaround: automated resubmit loop relying on checkpoint-resume.
8. **Short-sequence retain datasets may cause severe CPU-bound dataloading
   bottlenecks** (suspected with GUE's `emp_h3` subtask: ~15x GPU-utilization
   drop observed) — short documents require heavy concatenation to fill
   `seq_length`, and without background worker processes
   (`num_workers>0`), this blocks the GPU idle every step. Added
   `num_workers=4`/`persistent_workers=True` to `dual_dataset_provider.py`
   as a fix — **not yet confirmed** whether this actually resolves it, or
   whether the root cause is something else entirely (an unexplained
   0.86B vs. the expected 0.96B total-parameter-count mismatch was also
   observed in that same run and remains uninvestigated).

---

## 11. Status Summary

| Component | Status |
|---|---|
| Environment | Working, verified |
| Checkpoint conversion | Done |
| Classification (official pipeline) | Working, head-only + LoRA both run, AUROC eval built |
| Causal-LM continued pretraining | Working (LoRA validated; baseline PPL eval built) |
| Gradient Difference unlearning | Built, smoke-tested, validated run completed; a second (emp_h3) run hit dataloading/preemption issues, unresolved |
| Saliency (Stage 2) | Built, **not yet smoke-tested** |
| Noise injection (Stage 3) | Not yet built |
| Distillation (Stage 4) | Not yet built |
| RMU | Deferred — needs probe infrastructure + layer-localization study first |