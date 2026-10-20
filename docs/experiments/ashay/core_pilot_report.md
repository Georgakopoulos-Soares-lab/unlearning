# Original Evo2-1B core pilot: completed

All three core GUE tasks completed on the existing H100 Pod. This evaluates a frozen pretrained reference; it does not establish unlearning, retention or selective forgetting.

## MEASURED results

Each task used 256 training and 128 official development examples. C was selected separately per layer on development AUROC from {0.1, 1, 10}; exact ties favor smaller C. Both fixed layers are reported. These are validation-selected engineering results, not unbiased held-out benchmark estimates.

| Task | Block (zero-based) | Selected C | Dev AUROC | Dev corpus NLL | Dev perplexity |
|---|---:|---:|---:|---:|---:|
| gue_emp_h3 | blocks.7 | 10 | 0.850183 | 1.251822 | 3.496710 |
| gue_emp_h3 | blocks.15 | 10 | 0.839927 | 1.251822 | 3.496710 |
| gue_prom_300_all | blocks.7 | 10 | 0.973877 | 1.318065 | 3.736186 |
| gue_prom_300_all | blocks.15 | 10 | 0.959717 | 1.318065 | 3.736186 |
| gue_splice_reconstructed | blocks.7 | 0.1 | 0.778737 | 1.149952 | 3.158041 |
| gue_splice_reconstructed | blocks.15 | 0.1 | 0.767814 | 1.149952 | 3.158041 |

H3 and promoter use binary AUROC with class 1 positive. Splice has source labels 0/1/2 and uses macro one-vs-rest AUROC. All 18 candidate scores and warnings are saved in baseline_probe_results.csv; no convergence warnings occurred. Raw NLL does not rank accuracy across unrelated tasks.

## TESTED correctness and saved-artifact reproduction

13 new CPU tests passed after the actual checkpoint-audit fix; the earlier evaluator integration test also passed. Final verification is recorded in final_verification.log. Tests are independent of optional Evo2 imports and use synthetic correctness fixtures only.

| Check | Evidence |
|---|---|
| Causal shift and known-logit losses | Hand-computed synthetic fixture |
| Padding, special targets, partial batch, empty targets | CPU tests |
| Corpus aggregation across repartitioned token losses | CPU invariant test |
| Train-only scaling, positive-class mapping, multiclass AUROC, ties | CPU tests |
| Nonempty pooling masks and nonfinite rejection | CPU tests |
| Wrong branch/model rejection, tied alias and cumulative budget | CPU tests |
| 1,152 saved IDs, target counts and corpus losses | Independently reaggregated exactly |
| Six saved selected probe objects and feature matrices | Reconstructed AUROCs match exactly |

Recheck without a GPU: `/workspace/venvs/evo2-pilot/bin/python scripts/validate_benign_pilot_results.py /workspace/meeting-artifacts/evo2-20261020T1437`.

## VERIFIED data protocol

Official GUE archive linked by MAGICS-LAB/DNABERT_2@f25bed9ee20db966dff39e5c1571249d04e36404. Actual task directories: GUE/EMP/H3, GUE/prom/prom_300_all and GUE/splice/reconstructed. Only train.csv and dev.csv contents were opened. No test content was inspected or scored.

| Task | Train class counts | Dev class counts | Sequence length | Truncated | Ambiguous scored bases |
|---|---|---|---:|---:|---:|
| gue_emp_h3 | {'1': 132, '0': 124} | {'0': 63, '1': 65} | 500–500 | 0 | 0 |
| gue_prom_300_all | {'0': 128, '1': 128} | {'1': 64, '0': 64} | 300–300 | 0 | 0 |
| gue_splice_reconstructed | {'2': 144, '0': 56, '1': 56} | {'2': 72, '1': 28, '0': 28} | 400–400 | 0 | 0 |

Seed 42, class stratification, selected rows restored to original order. Original IDs are deterministic source-member/row references when no explicit ID exists. Full-sequence and scored-prefix hashes, lengths, row indices, source hashes and actual label schemas are saved in the manifest/provenance. No biological group IDs were invented.

Protocol: maximum-512-nucleotide-prefix-no-bos-v1. Uppercase/strip whitespace; map IUPAC ambiguity to N; reject unsupported symbols. ASCII byte CharLevelTokenizer(512), pad=1/eos=0, no BOS/EOS inserted. Causal targets are positions 1 through L-1; the first nucleotide has no target. Inputs are right-padded to a multiple of 16 for FP8 GEMMs. Pooling averages nucleotide positions, excludes padding, and includes the first nucleotide.

Exact and reverse-complement checks cover selected records only; all cross-split full-sequence/prefix counts are zero. Within-split groups and IDs are retained in data_provenance.json. These checks are not homology analysis or an audit of actual forget/retain training sets. No inferential confidence intervals are claimed without biological grouping.

## EXECUTED model and numerical smoke

Model: `arcinstitute/evo2_1b_base@2279e1df422c991037470302360edd40d0d2ea1e`, original FP8 reference, 1,107,989,760 parameters, 25 blocks, width 1920, supported context 8192. Official Evo2 backend commit `53f195997257c56c00e5ef8d33a54f5baad143a6`; Vortex vtx 1.1.0. Python 3.12.3, torch 2.8.0+cu128, CUDA 12.8, Transformer Engine 2.3.0, FlashAttention 2.8.3.post2. Exact resolved packages and backend source-file hashes are retained.

Backbone eval/frozen/inference mode; original upstream FP8 input projections and checkpoint precision recipe retained. Both layers (blocks.7 and blocks.15, eighth/sixteenth block outputs) are captured in one pass and promptly pooled to CPU. The strict tensor audit verified no missing/shape-mismatched weights. Extra unembed.weight was accepted only after bitwise equality with embedding_layer.weight; extra legacy non-tensor metadata is explicitly listed in model_contract.json.

No 7B or BF16-trained substitute was used. This standalone official inference result is not validated as equivalent to the team BioNeMo-trained checkpoints. Import logs retain a Transformer Engine FlashAttention-version warning; actual finite forward/scoring succeeded, and broader backend compatibility is not claimed.

| Smoke batch | Corpus NLL delta from batch 1 | Maximum per-example mean NLL delta |
|---|---:|---:|
| 1 | 0.000000000 | 0.000000000 |
| 2 | 0.000210633 | 0.004313359 |
| 4 | -0.000526468 | 0.002337743 |
| 1_repeat | 0.000000000 | 0.000000000 |

Same tiny heterogeneous training-prefix set at each batch size; repeated batch 1 was identical. Larger-batch numerical discrepancies are measured, with no invented acceptance tolerance. The pilot uses batch 1 throughout. Padding/FFT/FP8/backend contributions were not isolated; CPU aggregation invariants passed. No nonfinite values, zero-target examples or perplexity overflows occurred.

Timed smoke: 32 examples in 1.020 s (31.38 examples/s; 15659 scored tokens/s). Warmup plus numerical checks were separately 3.739 s.

## MEASURED runtime and memory

| Task | Extraction/scoring seconds | Examples/s | Scored tokens/s | Peak allocated GiB |
|---|---:|---:|---:|---:|
| gue_emp_h3 | 14.243 | 26.96 | 13453 | 2.276 |
| gue_prom_300_all | 13.968 | 27.49 | 8220 | 2.220 |
| gue_splice_reconstructed | 14.203 | 27.04 | 10788 | 2.244 |

Extraction/scoring total: 42.413 s. Cumulative GPU-job wall time including the failed first attempt, loading and stage overhead: 277.054 s of 7,200 s; no active GPU stage remains. The user removed both absolute clock deadlines; elapsed budgets were preserved. The native Transformer Engine build overlapped CPU work and is documented separately; previous troubleshooting time is unknown. No additional resource was rented.

## VERIFIED FROM SOURCE / resolved failures / limitations

Read-only review verified phase1_evo2 and phase2_evo2 on undo@17dafba0ba714ea8acf40f362e22653266760077. Its loader defaults to 7B. The balanced logistic/scaler pattern was adapted from phase1_evo2/train_probes.py while omitting its test evaluation. bionemo@5c5eb74144991271fe3aef40431f01aaddb58b9a contains a separate training route; it was not run or imported. Supplied handoff/audit documents were absent, so no audit-only claims are presented as verified.

Resolved operational failures: sandbox user namespaces unavailable (normal approved execution used); base pytest absent (isolated venv); guessed source metadata URLs; archive aliases differed from repository names; splice required three labels; strict checkpoint audit initially rejected the exact tied-weight alias. Failed runs and the first smoke attempt are retained. The original torch/driver environment and other worktrees were preserved; no competing writer or prior active GPU job was found.

The Pod reports an H100 NVL with 95,830 MiB VRAM. Cgroup limits: 15.3 CPU cores and 140,999,999,488 bytes RAM. Shared-filesystem free space is not a verified workspace quota; downloads stayed well below the reported 100 GB allowance.

## Source, run and recovery provenance

Initial implementation: `beb9f107066f38f16c59fd852a2f3f710265bac9`. Actual successful GPU smoke/pilot source: `3d3da6bce62a19819a59ba063c11d9a3ac082a70`. The later delivery commit adds the measured report, saved-result validator and final completed-sample status fix; it is not the GPU-run source. Final commit/verified remote hashes are recorded in delivery_manifest.json and the final handoff after the push.

Manifest SHA256: `7a71f56ddbfc66d05095d709cd169c4bc1b6e8f64d115b61c8fab1af4af66cf3`. Checkpoint SHA256: `8ffba7d0e6445a8f2c92d9ff1c4e772c7f73ca9179f5e0c699b8b0ca1b966f64`. Archive SHA256: `581ba5a69843769f4cbc34470e2fe970f8ee371280914bd66574af01ee60cd79`. Exact model/data revisions and redownload locations remain in configs/benign_pilot.json; raw weights, environments and full raw archive are excluded from Git and recovery.

Artifacts: `/workspace/meeting-artifacts/evo2-20261020T1437`. The source push contains code and small measured report/CSV evidence. The separate allowlisted recovery archive contains selected manifests, pooled features, probe coefficients, per-example losses, logs, source recovery and checksums. OFF-POD BACKUP PENDING until the user downloads and verifies it; no off-Pod destination was supplied. Use the Pod Jupyter file browser to download the final recovery archive and its SHA256 file, then run `sha256sum -c <archive>.sha256` in the download directory. Verify this before stopping the Pod; experiment timeouts do not stop rental billing.

DEFERRED: unlearning/backbone training, checkpoint transfer/retention comparisons, R1–R4/UNDO and optional stretch tasks. The requested three-task core is complete. Team decisions for future work: canonical model/backend, compatible checkpoints, qualified forget/retain tasks and real training manifests, biological grouping and preservation tolerances.
