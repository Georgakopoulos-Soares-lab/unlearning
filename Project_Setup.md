# BioNeMo Evo2 Project Setup Guide

Environment setup and infrastructure guide for BioNeMo Evo2 genomic language model fine-tuning and unlearning.

This guide is meant to work on any Linux GPU cluster. Steps that only apply to the cluster we first set up on (Northeastern's HPC with Rocky Linux 9.3 and H200 GPUs) are marked:

> 🏷️ **Cluster-specific:** these steps may be unnecessary, or need different values, on other clusters.

## Table of Contents
0. [Path Conventions](#0-path-conventions)
1. [Cluster Prerequisites](#1-cluster-prerequisites)
2. [Conda Environment Creation](#2-conda-environment-creation)
3. [Module Loading & Environment Variables](#3-module-loading--environment-variables)
4. [Repository Clone & venv Build](#4-repository-clone--venv-build)
5. [Build Fixes](#5-build-fixes)
6. [Environment Verification](#6-environment-verification)
7. [SLURM Job Submission](#7-slurm-job-submission)
8. [Checkpoint Conversion](#8-checkpoint-conversion)
9. [Data Pipelines](#9-data-pipelines)
10. [Classification](#10-classification)
11. [Causal-LM Continued Pretraining](#11-causal-lm-continued-pretraining-evo2_causal_lm_finetune)
12. [Perplexity Evaluation](#12-perplexity-evaluation)
13. [Unlearning Pipeline](#13-unlearning-pipeline-evo2_unlearn_pipeline)
14. [Known Issues / Gotchas](#14-known-issues--gotchas-cross-referenced-keep-checking-these)
15. [Project Status Summary](#15-project-status-summary)

---

## 0. Path Conventions

All paths in this guide are defined relative to a few variables. Set them once per cluster; every other command uses them.

| Variable | Meaning | Example (original cluster) |
|---|---|---|
| `PROJECT_ROOT` | Directory where you clone `bionemo-framework` (pick a large, shared filesystem, not `$HOME` if quota is small) | `/projects/Unlearning` |
| `RECIPE_DIR` | `${PROJECT_ROOT}/bionemo-framework/recipes/evo2_megatron` | (derived) |
| `CONDA_ENV_NAME` | Name of the conda env | `bionemo_evo2` |
| `CONDA_ENV_PATH` | Location of the conda env. Use `$CONDA_PREFIX` after `conda activate` | `~/.conda/envs/bionemo_evo2` |
| `CKPT_DIR` | Where converted checkpoints are written | `${PROJECT_ROOT}/unlearning/checkpoints` |
| `BUILD_TMP` | Scratch space for building wheels | `${TMPDIR:-/tmp}` |

```bash
export PROJECT_ROOT=/path/to/your/project/space
export RECIPE_DIR="${PROJECT_ROOT}/bionemo-framework/recipes/evo2_megatron"
export CONDA_ENV_NAME=bionemo_evo2
export CKPT_DIR="${PROJECT_ROOT}/unlearning/checkpoints"
export BUILD_TMP="${TMPDIR:-/tmp}"
```

Unless stated otherwise, commands from section 4 onward assume you are in `${RECIPE_DIR}`.

---

## 1. Cluster Prerequisites

### Hardware & Drivers
- **GPU**: an NVIDIA GPU whose driver supports CUDA ≥ 12.8. Check with `nvidia-smi` (top-right "CUDA Version").
  - 🏷️ **Cluster-specific:** the original setup used an H200 (143 GB), the recommended GPU. Smaller GPUs should work for smaller model sizes but other GPUs are untested.
- **CUDA toolkit**: 12.8 (must not exceed the driver's CUDA version). Load it through a module if the cluster has one, or use a local install.
- **GCC**: a version supported by CUDA 12.8 (GCC ≤ 12). The original setup used 11.5.0.

### Software
- **Python**: 3.12 from conda. Do not use a system Python 3.13+, because the recipe's dependencies don't support it.
- **Conda**: any recent conda, mamba or miniforge install.
  - 🏷️ **Cluster-specific:** on the original cluster, conda 4.13.0 is at `/shared/centos7/anaconda3/2022.05`.
- **git**: any recent version (system git or a module).
  - 🏷️ **Cluster-specific:** on the original cluster, `module load git/2.52.0`.

### Why pip-only (no Docker)
The official recipe's Docker image (`nvcr.io/nvidia/pytorch`) ships a pinned NVIDIA-internal nightly PyTorch build tied to CUDA 13.0. That build is not published on PyPI or pytorch.org. We rebuild an equivalent environment from public pip packages, using a stable PyPI torch build (cu128), and manually fix the dependencies that assume the container's pre-built environment.

> If the target cluster's driver supports CUDA 13 **and** the cluster allows containers (Docker, Apptainer/Singularity, Enroot), the official container is the simpler route and most of sections 2–5 can be skipped.

---

## 2. Conda Environment Creation

Create a dedicated conda environment with Python 3.12:

```bash
conda create -n "${CONDA_ENV_NAME}" python=3.12 -y
conda activate "${CONDA_ENV_NAME}"
pip install --upgrade pip
```

To put the env somewhere other than the default (for example on a project filesystem with more quota), use `conda create -p "${PROJECT_ROOT}/envs/${CONDA_ENV_NAME}" python=3.12 -y` and activate it by that path.

---

## 3. Module Loading & Environment Variables

**Every job session must do the following, in this order.** The `env_setup.sh` script in [Quick Reference](#quick-reference-env_setupsh-template) does all of it.

### Load Modules
🏷️ **Cluster-specific:** module names and versions differ between clusters (use `module avail cuda` to see yours). Skip this step if the cluster has no module system and CUDA/git are already on `PATH`.

```bash
module load cuda/12.8.0
module load git/2.52.0
```

### Activate Conda
In non-interactive shells (batch jobs), conda isn't initialized automatically, so load its shell hook first:

```bash
eval "$(conda shell.bash hook)"        # works if `conda` is on PATH
# or: source <conda_base>/etc/profile.d/conda.sh
conda activate "${CONDA_ENV_NAME}"
```

🏷️ **Cluster-specific:** on the original cluster, `<conda_base>` is `/shared/centos7/anaconda3/2022.05`.

### Set NVIDIA Library Paths
`CPATH` and `LD_LIBRARY_PATH` must include the NCCL and cuDNN headers and libraries bundled with torch, because they're not on the compiler or linker search path by default. Get the conda env's site-packages path from Python instead of hard-coding it. Run this **after** `conda activate` and **before** activating `.venv`:

```bash
SITE_PACKAGES="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
export CPATH="${SITE_PACKAGES}/nvidia/nccl/include:${SITE_PACKAGES}/nvidia/cudnn/include:${CPATH:-}"
export LD_LIBRARY_PATH="${SITE_PACKAGES}/nvidia/nccl/lib:${SITE_PACKAGES}/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}"
```

### Activate the venv
```bash
cd "${RECIPE_DIR}"
source .venv/bin/activate   # after .venv exists (see section 4)
```

---

## 4. Repository Clone & venv Build

### Clone BioNeMo Framework
```bash
cd "${PROJECT_ROOT}"
git clone https://github.com/NVIDIA/bionemo-framework.git
cd "${RECIPE_DIR}"
```

### Install uv (required by .ci_build.sh)
```bash
pip install uv
```

### Set Build Environment Variables
```bash
export NVTE_CUDA_ARCHS=90        # target GPU architecture; a single arch speeds up the TE compile
export NVTE_WITH_NCCL_EP=0       # disables the MoE/expert-parallel code path (not needed for dense Evo2; avoids a torch-version-mismatch header error)
```

🏷️ **Cluster-specific:** `NVTE_CUDA_ARCHS` must match your GPU's compute capability: `80` for A100, `86` for A40/A6000, `89` for L40S, `90` for H100/H200, `100` for B200. Check with `nvidia-smi --query-gpu=compute_cap --format=csv`. For a mix of GPU types, separate values with semicolons (for example `"80;90"`).

### Run the Build Script
```bash
bash .ci_build.sh
```

This creates `.venv/` with most dependencies. Some known build issues need the fixes in section 5.

---

## 5. Build Fixes

Apply these in order. Each fix notes whether it applies everywhere or only to some clusters.

### 5.1 FIX: nvidia-resiliency-ext (Missing Wheel for Older glibc)

🏷️ **Cluster-specific:** only needed if the system glibc is older than 2.39 (check with `ldd --version`). The original cluster runs Rocky Linux 9.3 with glibc 2.34, which can't use PyPI's `manylinux_2_39` wheels. On newer systems (for example Ubuntu 24.04), skip this step.

Build the wheel locally:

```bash
mkdir -p "${BUILD_TMP}/nvrx_build" && cd "${BUILD_TMP}/nvrx_build"
git clone --branch v0.6.0 https://github.com/NVIDIA/nvidia-resiliency-ext.git
cd nvidia-resiliency-ext
pip install pybind11
python -m pip wheel . --no-deps --no-build-isolation -w "${BUILD_TMP}/nvrx_wheels"
export UV_FIND_LINKS="${BUILD_TMP}/nvrx_wheels"
cd "${RECIPE_DIR}"
bash .ci_build.sh   # uv will now prefer the local wheel
```

Note: `UV_FIND_LINKS` must still be set, and the wheel directory must still exist, whenever you re-run `.ci_build.sh`. If `${TMPDIR}` is wiped between jobs, set `BUILD_TMP` to a persistent location.

### 5.2 FIX: causal_conv1d / nv-grouped-gemm Missing torch as Build Dependency

Applies on all clusters. These packages need torch at build time but don't declare it, so `--no-build-isolation` builds fail. Edit `pyproject.toml` in `${RECIPE_DIR}`:

Find the `[tool.uv.extra-build-dependencies]` section and add:
```toml
causal_conv1d = ["torch"]
nv-grouped-gemm = ["torch"]
```

Then re-run `bash .ci_build.sh`.

### 5.3 FIX: Install a Stable torch (cu128) Manually

Applies to every pip-only setup. The recipe pins an internal nightly PyTorch that has no stable PyPI equivalent, so install a stable release into the **conda env**:

```bash
pip install torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1 \
  --index-url https://download.pytorch.org/whl/cu128
```

`.ci_build.sh` runs `uv venv --system-site-packages`, so the venv picks up this torch from the parent conda env and uv does not try to reinstall it.

### 5.4 FIX: Install Transformer Engine (Not in build_requirements)

Applies on all clusters. With conda active and the build/library variables from sections 3 and 4 set (`NVTE_CUDA_ARCHS`, `NVTE_WITH_NCCL_EP`, `CPATH`, `LD_LIBRARY_PATH`):

```bash
pip install --no-build-isolation "transformer_engine[pytorch]"
```

### 5.5 CRITICAL: Install cuDNN into .venv's Own site-packages

Applies on all clusters. Transformer Engine's runtime library loader only checks the active interpreter's sysconfig path, so cuDNN must be physically inside `.venv`, not just in the parent conda env:

```bash
cd "${RECIPE_DIR}"
.venv/bin/python -m pip install --ignore-installed --no-deps \
  nvidia-cudnn-cu12==9.10.2.21
```

The cuDNN version should match the one torch was built against. Check with `pip show nvidia-cudnn-cu12` in the conda env. `9.10.2.21` matches torch 2.9.1 + cu128.

**IMPORTANT**: Always use `.venv/bin/python -m pip` explicitly, not bare `pip`. `uv venv` doesn't install a `pip` binary into `.venv` by default, so a bare `pip` can silently resolve to the parent conda env's pip.

---

## 6. Environment Verification

Run these on a **GPU node** from `${RECIPE_DIR}` (otherwise `torch.cuda.is_available()` returns `False`):

```bash
.venv/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
.venv/bin/python -c "import transformer_engine.pytorch as te; print(te.__version__)"
.venv/bin/python -c "import megatron.bridge; print('OK')"
train_evo2 --help
```

All four should finish without errors.

---

## 7. SLURM Job Submission

🏷️ **Cluster-specific (whole section):** partition names, GRES strings and walltime limits differ between clusters. Check yours with `sinfo -s` and `scontrol show partition`. If the cluster doesn't use SLURM (for example PBS or LSF), translate the directives.

### Interactive Session (for building/debugging)
```bash
# Original cluster:
srun -p gpu-interactive --gres=gpu:h200:1 --time=00:20:00 --pty /bin/bash
# Generic form:
srun -p <interactive_gpu_partition> --gres=gpu:<gpu_type>:1 --time=<hh:mm:ss> --pty /bin/bash
```

### Batch Job Submission
- **Max walltime**: 8 hours on the `gpu` partition of the original cluster. Check your cluster's limit.
- **For long training**: submit several sequential jobs that resume from checkpoints.

```bash
#!/bin/bash
#SBATCH -p gpu                  # 🏷️ partition name
#SBATCH --gres=gpu:h200:1       # 🏷️ GPU type/count
#SBATCH --time=08:00:00         # 🏷️ walltime limit

# PROJECT_ROOT must be set here or exported before sbatch (sbatch passes the environment through by default)
export PROJECT_ROOT=/path/to/your/project/space
source "${PROJECT_ROOT}/bionemo-framework/recipes/evo2_megatron/env_setup.sh"

# Your training/evaluation command here
```

---

## 8. Checkpoint Conversion

### Overview
Evo2 checkpoints on HuggingFace are in "Savanna" format (the Arc Institute's original training codebase). The recipe ships a converter: `evo2_convert_savanna_to_mbridge`.

### Important Requirement
**Run it on a GPU node**, not the login node. The script calls `torch.cuda.synchronize()` while saving the checkpoint and fails with "Found no NVIDIA driver" otherwise.

### Conversion Command
Run from `${RECIPE_DIR}`, because the tokenizer path is relative to it:

```bash
evo2_convert_savanna_to_mbridge \
  --savanna-ckpt-path arcinstitute/savanna_evo2_1b_base \
  --revision <commit_sha> \
  --mbridge-ckpt-dir "${CKPT_DIR}/evo2_1b_base_mbridge" \
  --model-size evo2_1b_base \
  --tokenizer-path tokenizers/nucleotide_fast_tokenizer_256 \
  --verbose
```

If compute nodes have no internet access (common on some clusters), first download the HuggingFace repo on a login node (`huggingface-cli download arcinstitute/savanna_evo2_1b_base --revision <commit_sha>`) and set `HF_HOME` to a shared filesystem so the compute node can find the cache.

### Important: Pin the Revision
The tool strongly recommends pinning a specific commit SHA (not "latest") for reproducibility and security. Find the current commit at:
```
https://huggingface.co/<org>/<repo>/commits/main
```

### Result Format
A PyTorch Distributed Checkpoint (DCP): a directory (e.g. `iter_0000001/`) containing:
- `__*.distcp` shard files
- `.metadata`
- `metadata.json`
- `common.pt`
- `train_state.pt`
- `tokenizer/` subfolder

**Not a single `.pt` file.**

### Known Gap: Missing _extra_state Keys
The converted checkpoint has no `*._extra_state` keys (TransformerEngine's FP8/metadata placeholders). Savanna's native format has no such concept, so they're simply absent. Loading this checkpoint into a model that expects those keys fails by default.

**Fix**: set this in your config:
```python
cfg.checkpoint.dist_ckpt_strictness = "ignore_all"
```

This is safe. Direct inspection of the checkpoint's `.metadata` file confirmed that 0 `_extra_state` keys exist, while all 254 real weight keys (embeddings, layer weights, final_norm, etc.) are present and correct.

### Verify Checkpoint Contents (Without Loading a Model)
```python
from torch.distributed.checkpoint import FileSystemReader
reader = FileSystemReader('<ckpt_dir>/iter_XXXXXXX')
metadata = reader.read_metadata()
print(sorted(metadata.state_dict_metadata.keys()))
```

---

## 9. Data Pipelines

### 9.1 HVUE (forget set)
- **Classification format**: `fasta_to_jsonl.py` converts the labeled
  manifest FASTA into `train/val/test.jsonl` ({"sequence", "label"}).
- **Causal-LM format**: `extract_train_only_fasta.py` (generalizes to any
  split value) pulls out plain per-split FASTAs, then `preprocess_evo2`
  (3 separate config entries, one per split, each with a single
  `train_split`/`valid_split`/`test_split` ratio = 1.0) produces the real
  `.bin`/`.idx` files. **Caveats confirmed twice**: each `output_prefix`
  entry produces ALL THREE `_train`/`_val`/`_test` suffixed files, but only
  the one matching its own ratio has real content — the other two are
  0-byte placeholders. Always `ls -lh` and check real file sizes before
  writing a `training_data_config.yaml`, never assume the suffix naming.
- Real counts (verified via `check_dataset_lengths.py`):
  train=727,892 / val=276,092 / test=276,048 docs (~1000 tokens/doc).
  Causal-LM test count (276,048) is ~2x the classification JSONL count
  (138,024) because `embed_reverse_complement: true` doubles the data.

### 9.2 GUE (retain set)
Same `preprocess_evo2` pattern, user-provided FASTA. Full combined GUE:
train=1,448,334 / val=167,976 / test=167,976 docs (~672-980 tokens/doc).
**`emp_h3` subtask** (used in a later unlearning run) is a much smaller,
short-sequence GUE subtask — suspected (not yet confirmed) to need heavy
document-concatenation per training window, which may explain a severe
dataloading slowdown (see section 12).

---

## 10. Classification

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

## 11. Causal-LM Continued Pretraining (`evo2_causal_lm_finetune/`)

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

## 12. Perplexity Evaluation

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

## 13. Unlearning Pipeline (`evo2_unlearn_pipeline/`)

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

---

## 14. Known Issues / Gotchas (cross-referenced, keep checking these)

1. **`--fasta-data`/`--fasta-file` is broken** in this `train_evo2`
   version — use `--dataset-config` instead (section 11).
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
7. 🏷️ **Cluster-specific:** **Job preemption observed on heavily-shared nodes** (e.g. `d4054`) —
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

## 15. Project Status Summary

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

---

## Quick Reference: env_setup.sh Template

Save this as `${RECIPE_DIR}/env_setup.sh` and source it in every job. It finds its own location, so it works wherever the repo is cloned. The cluster-specific parts can be overridden with environment variables.

```bash
#!/bin/bash
# Usage: source env_setup.sh
# Optional overrides (set before sourcing):
#   CONDA_ENV_NAME  (default: bionemo_evo2)
#   CONDA_BASE      path to conda install, used only if `conda` isn't on PATH
#   CUDA_MODULE     (default: cuda/12.8.0; set to "" to skip)
#   GIT_MODULE      (default: git/2.52.0;  set to "" to skip)

RECIPE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-bionemo_evo2}"

# --- Modules (🏷️ cluster-specific; skipped if no module system) ---
if command -v module >/dev/null 2>&1; then
    [ -n "${CUDA_MODULE-cuda/12.8.0}" ] && module load "${CUDA_MODULE-cuda/12.8.0}"
    [ -n "${GIT_MODULE-git/2.52.0}" ]   && module load "${GIT_MODULE-git/2.52.0}"
fi

# --- Conda ---
if command -v conda >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)"
elif [ -n "${CONDA_BASE:-}" ]; then
    source "${CONDA_BASE}/etc/profile.d/conda.sh"
    # 🏷️ original cluster: CONDA_BASE=/shared/centos7/anaconda3/2022.05
else
    echo "env_setup.sh: conda not found; set CONDA_BASE" >&2
    return 1
fi
conda activate "${CONDA_ENV_NAME}"

# --- NVIDIA headers/libs bundled with torch (from the conda env, before the venv) ---
SITE_PACKAGES="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
export CPATH="${SITE_PACKAGES}/nvidia/nccl/include:${SITE_PACKAGES}/nvidia/cudnn/include:${CPATH:-}"
export LD_LIBRARY_PATH="${SITE_PACKAGES}/nvidia/nccl/lib:${SITE_PACKAGES}/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}"

# --- Recipe venv ---
cd "${RECIPE_DIR}"
source .venv/bin/activate
```

---

## Status Summary

🏷️ **Cluster-specific:** this records the state on the original cluster. Re-check every item after installing on a new cluster.

| Component | Status |
|---|---|
| Environment setup (conda + module loading) | ✅ Complete & verified |
| Build with required fixes | ✅ Complete |
| Checkpoint conversion | ✅ One-time setup complete |
| venv verification | ✅ All checks passing |
