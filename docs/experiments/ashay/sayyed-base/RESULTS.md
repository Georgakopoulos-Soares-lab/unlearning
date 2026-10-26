# Independent frozen Evo2 H3 baseline

Completed the supplied EMP/H3 task with the pinned original Evo2-1B backbone frozen throughout. This is an independent original-backend reference; equivalence to the historical BioNeMo conversion is not established. No HVUE human-host-tropism predictor was trained or evaluated.

| Split | Rows | AUROC | Accuracy | Balanced accuracy | Class1 prevalence / majority baseline | Causal NLL | LM perplexity |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 11971 | 0.837216 | 0.715396 | 0.710670 | 0.513742 | 1.256722 | 3.513885 |
| dev | 1497 | 0.820656 | 0.702739 | 0.699810 | 0.509018 | 1.254565 | 3.506313 |
| test | 1497 | 0.831817 | 0.702739 | 0.701179 | 0.504342 | 1.255723 | 3.510374 |

The protocol was frozen before held-out content access. All supplied rows were used in their designated splits. Mean-pooled final RMSNorm features feed a LayerNorm/Linear/GELU/Dropout/Linear MLP trained on CPU for 300 steps, batch 8, initial LR 1e-3 with 20-step warmup and cosine decay. Checkpoints every 50 steps were compared on dev AUROC; step 250 was selected. The 0.5 threshold and all settings were fixed before test predictions. No test-based model or hyperparameter selection occurred. Classification cross-entropy is saved separately and is never called LM perplexity. Causal NLL sums next-nucleotide losses over positions1..L-1 and divides by total valid targets; perplexity is its exponential.

Independent verification checked all 14,965 row associations, labels, sequence hashes and causal target counts, reconstructed the saved head probabilities exactly (maximum delta0), and independently recomputed rank-based AUROC, confusion-based accuracy/balanced accuracy and token-weighted NLL/perplexity. All 41 existing evaluator tests passed. Features and losses on 1,536 rows shared with the recovered historical H3 extension matched exactly; this reused-row comparison is not independent replication.

No exact/RC cross-split overlap was found. The new train contains 1,024 historical train rows; the new dev contains 512 historical dev rows, with matching labels. None of these historical rows occurs exactly in the new test. No biological grouping/homology independence or authoritative biological meaning for numeric class1 is established. No confidence interval, broader generalization, unlearning, or matched BioNeMo performance claim is made. Historical launcher/log discrepancies remain documented separately.

All four historical recovery archives passed sidecars and 509 packaged payload checksums in fresh safe extraction directories. Original checkpoint SHA256 and 219 backend source files verified. Vortex, TE/CUDA and FlashAttention wheel hashes matched historical records; the TE PyTorch extension was rebuilt and its distinct hash retained. Runtime: /workspace/venvs/sayyed-base-runtime/bin/python; environment_lock.txt and wheel receipts are in the run. Model/data/environment binaries are excluded from Git.

GPU stage wall time charged: 288.922882s; extraction completion timing 288.825224s. Cumulative GPU ledger: 868.753177/7200s, active_since=null. No GPU job remains. No hardware change, backbone/LoRA/unlearning training or automatic shutdown occurred.

Run: /workspace/meeting-artifacts/sayyed-base-20261026-v1. Inference and head execution revision 735394ea52ed1c08c6e034d4b025813b16516fcc; exact source hashes and model/backend/protocol/cache identities are retained. Later report delivery is distinct from execution. Private backup round-trip status is recorded separately in backup_receipt.json after upload and fresh-download verification.
