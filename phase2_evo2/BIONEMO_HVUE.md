# BioNeMo Evo2 HVUE Adaptation

This workflow keeps BioNeMo-specific Evo2 adaptation localized to:

- code: `phase2_evo2/`
- data and generated scripts: `data/evo2/`

It targets `hvue_human_host_tropism` first.

## 1. Prepare JSONL Splits

Run from `unlearning/`:

```bash
python phase2_evo2/prepare_bionemo_hvue_classifier.py \
  --manifest data/evo2/benchmarks/hvue_gue_manifest.csv \
  --task hvue_human_host_tropism \
  --out-dir data/evo2/bionemo_hvue \
  --prefix host_tropism \
  --max-length 512
```

Outputs:

```text
data/evo2/bionemo_hvue/host_tropism_train.jsonl
data/evo2/bionemo_hvue/host_tropism_val.jsonl
data/evo2/bionemo_hvue/host_tropism_test.jsonl
data/evo2/bionemo_hvue/host_tropism_metadata.json
```

## 2. Write BioNeMo Launch Scripts

```bash
python phase2_evo2/write_bionemo_hvue_commands.py \
  --data-dir data/evo2/bionemo_hvue \
  --run-dir data/evo2/bionemo_runs/hvue_host_tropism \
  --base-ckpt-dir data/evo2/bionemo_ckpts/evo2_1b_bf16_mbridge \
  --seq-length-tokens 512
```

Outputs:

```text
data/evo2/bionemo_hvue/scripts/00_convert_evo2_1b_to_mbridge.sh
data/evo2/bionemo_hvue/scripts/10_train_head_only.sh
data/evo2/bionemo_hvue/scripts/20_train_lora.sh
```

Run these scripts inside the NVIDIA BioNeMo Evo2 recipe environment.

If `evo2_classifier.py` is not at `phase2_evo2/bionemo/evo2_classifier.py`, set:

```bash
export BIONEMO_EVO2_CLASSIFIER=/path/to/evo2_classifier.py
```

## 3. Convert / Train

Inside the BioNeMo environment:

```bash
bash data/evo2/bionemo_hvue/scripts/00_convert_evo2_1b_to_mbridge.sh
bash data/evo2/bionemo_hvue/scripts/10_train_head_only.sh
bash data/evo2/bionemo_hvue/scripts/20_train_lora.sh
```

The generated commands follow NVIDIA's Evo2 LoRA recipe pattern:

- head-only: frozen Evo2 backbone, trainable classification head
- LoRA: frozen backbone plus LoRA adapters and trainable classification head

## 4. Compare With K-mer

Once BioNeMo predictions are available, compare them to the existing k-mer baselines:

```bash
python phase2_evo2/compare_bionemo_hvue.py \
  --head-predictions <head_only_test_predictions.csv-or-jsonl> \
  --lora-predictions <lora_test_predictions.csv-or-jsonl> \
  --out-csv data/evo2/bionemo_runs/hvue_host_tropism/comparison.csv
```

Existing k-mer baselines:

```text
data/evo2/kmer_baselines/hvue_host_tropism_matched_512.csv
data/evo2/kmer_baselines/hvue_host_tropism_full_sequence.csv
```

The current full-sequence k-mer AUROC is `0.8366406969541881`; Evo2 LoRA needs
to beat that to clear the target-validity shortcut-baseline check.
