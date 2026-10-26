# Sayyed base preparation

Execution has not begun. No new model metrics or GPU usage are claimed.

The complete user-designated v6.txt is retained in PROMPT.txt and at /workspace/runbooks/sayyed_base_execution_20261026.txt. prompt_receipt.json distinguishes the original chat source from the immutable GitHub retrieval. No alternate prompt was used.

Public H3 preparation completed using the supplied GUE_benchmark.zip, SHA256 de48cbc46c30ebf04b261d5711d737d3805e43bca6c79adf73b8143bd53b190e. This is a distinct dataset identity from the old GUE.zip. There are 11,971 train and 1,497 dev rows; CSV and JSONL agree. Train lengths are 11,969 x 500, one x 290 and one x 310 bases; dev lengths are all 500. Numeric labels are 0/1; biological class mapping is not supplied. No exact/RC duplicates within either split or across train/dev were found. These are sequence-identity checks, not homology qualification. Test contents remain unopened. See h3_qualification.json; deterministic archive/member/row IDs and sequences are in /workspace/data/sayyed-20261026/h3-qualified-v1/train_dev_manifest.jsonl.

The BioNeMo H3 launcher and actual log differ: actual 300 steps, global batch 8, micro batch 2, LR .001, warmup 20; later launcher arguments follow a missing continuation. The head is LayerNorm/Linear/GELU/Dropout/Linear. h3_source_audit.json pins code/log blobs and hashes. BioNeMo, Megatron, Evo2, Vortex, Transformer Engine and FlashAttention are absent on this Pod. Model checkpoint/conversion metadata is absent. Do not claim compatible BioNeMo execution or a matched historical comparison.

Private backup recovery attempted at 5f2d1a15f74b84cb7f268c14e0507f91d7800c19 returned HTTP 401. Interactive authentication command:

```
/workspace/venvs/sayyed-base-tools/bin/hf auth login
```

Never paste credentials into chat. Recovery and fresh-download private backup verification require access. The isolated system-site-packages tools venv contains huggingface_hub and gdown; it is not a restored experiment runtime. Base system reports Python 3.12.3, torch 2.8.0+cu128 and an available H100 80GB. No global environment was upgraded.

Historical artifact directories, environment locks, model files and original ledger are absent locally. The committed handoff records 579.830295/7200 GPU seconds and active_since null, but newer backup evidence has not been accessible for reconciliation. Do not zero the ledger or start GPU work before recovery/reconciliation. No ledger was created or overwritten.

The historical HVUE configuration is viral human-host tropism prediction. Training/evaluating that capability predictor is excluded; no HVUE classifier or operational pipeline was created. Benign H3 recovery and execution can proceed independently once dependencies and budget provenance are established.

Next: authenticate HF interactively, recover into a fresh directory with safe member inspection and checksums; reconcile ledger; rebuild isolated runtime from verified locks; obtain pinned original weights and check hashes; freeze H3 protocol.json before held-out access; run a train-only cost smoke before full extraction and head fitting. Preserve all historical results and branches. No experiment process remains running.
