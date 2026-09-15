# DNABERT-2 HVUE Adapter

This folder is the DNABERT-2 analogue of `phase2_evo2`, kept localized so it does not disturb the Evo/Evo2 paths. It prepares the same HVUE host-tropism split, trains DNABERT-2 with either head-only, LoRA, or full fine-tuning, then compares the score against the existing Evo2 and k-mer baselines.

## Prepare Data

```bash
python phase2_dnabert2/prepare_hvue_classifier.py \
  --manifest data/evo2/benchmarks/hvue_gue_manifest.csv \
  --out-dir data/dnabert2/hvue \
  --max-length 512
```

## Install Minimal Extra Packages

Use this inside the environment where you want to run DNABERT-2:

```bash
python -m pip install transformers peft accelerate scikit-learn
```

DNABERT-2 is loaded through Hugging Face with `trust_remote_code=True`.

## Run LoRA

```bash
python phase2_dnabert2/eval_hvue.py \
  --mode lora \
  --data-dir data/dnabert2/hvue \
  --out-dir data/dnabert2/runs/hvue_host_tropism \
  --epochs 3 \
  --batch-size 8 \
  --max-length 512
```

DNABERT-2 uses fused attention projections, so the default LoRA target is `Wqkv`.

Other supported modes:

```bash
python phase2_dnabert2/eval_hvue.py --mode head_only
python phase2_dnabert2/eval_hvue.py --mode full_ft
```

Outputs are written under:

```text
data/dnabert2/runs/hvue_host_tropism/<mode>/
```

## Build Unlearning Splits

For host tropism, `label=1` is the default forget class and `label=0` is retain:

```bash
python phase2_dnabert2/build_unlearn_splits.py \
  --data-dir data/dnabert2/hvue \
  --out-dir data/dnabert2/unlearn_splits \
  --forget-label 1
```

For a cheap smoke run, cap the train rows:

```bash
python phase2_dnabert2/build_unlearn_splits.py \
  --forget-max-train 1024 \
  --retain-max-train 1024
```

## Run LoRA Unlearning

The DNABERT-2 unlearning script always trains PEFT LoRA adapters. It supports three classifier-logit objectives:

```text
gradient_ascent           - maximize forget CE, minimize retain CE
ga_retain_kl              - maximize forget CE, preserve retain logits vs frozen reference
uniform_forget_retain_kl  - push forget logits toward uniform, preserve retain logits vs frozen reference
```

Recommended first pass:

```bash
python phase2_dnabert2/unlearn_hvue.py \
  --objective ga_retain_kl \
  --split-dir data/dnabert2/unlearn_splits \
  --out-dir data/dnabert2/unlearn_runs/hvue_host_tropism \
  --steps 500 \
  --eval-every 100 \
  --batch-size 8 \
  --max-length 512
```

Alternative:

```bash
python phase2_dnabert2/unlearn_hvue.py --objective uniform_forget_retain_kl
python phase2_dnabert2/unlearn_hvue.py --objective gradient_ascent
```

## Compare

```bash
python phase2_dnabert2/compare_hvue.py \
  --run-root data/dnabert2/runs/hvue_host_tropism \
  --out data/dnabert2/runs/hvue_host_tropism/comparison.csv
```

The comparison includes DNABERT-2 test metrics if present, plus the existing Evo2 frozen-head and k-mer baseline files.
