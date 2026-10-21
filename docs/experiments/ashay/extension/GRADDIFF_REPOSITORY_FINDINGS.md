# GradDiff repository findings and backup verification

The new six-task Evo2 supplement is now backed up in the existing PRIVATE HF dataset, uploaded at `54832ea5536cb6ce519fb280b36dcd4cd9422cd6`, force-downloaded into a fresh directory and both files checksum-verified. Archive SHA256 `bf775c1a6ce5d767a62b75cab3f4592b04d8699b038bf6843d3d0dbbb94eb656` (198,138,054 bytes). The archive retains historical pending-backup wording as a snapshot; the newer adjacent backup receipt supersedes that status. No credential saved in source, artifacts or backup.

## What is actually in the repository

Fresh fetch inspected main, undo, bionemo and both experiment branches without switching/resetting worktrees. Exact immutable ref heads and per-file hashes retained in this follow-up run.

1. **BioNeMo Evo2 GradDiff implementation and evaluation launchers exist.** `bionemo@5c5eb74144991271fe3aef40431f01aaddb58b9a:Project_Setup.md` sections12–13 describes full-parameter Gradient Difference and warns about wrong tokenizer/checkpoint loading. The GUE evaluation launcher uses `/projects/MENTISLab/unlearning/results/evo2_graddiff/eval_pointer`, converted base `evo2_1b_base_mbridge`, a separate nucleotide tokenizer, seq_length1024 and GUE test evaluation. It is an HPC script, not a saved corrected checkpoint or measured comparison. It was not executed; official test sequences remain unopened/unscored here. No backbone/unlearning training was performed.

2. **Evo2 adaptation code also exists on undo.** `phase1_evo2/utils.py` and `phase2_evo2/utils.py` load Evo2; the defaults are `evo2_7b_base`, and `phase2_evo2/unlearn_gd.py` defaults outputs to `data/phase2_evo2/checkpoints`. Its header still says Evo-1, so a filename/header alone cannot establish a completed Evo2 run. No corrected 1B checkpoint artifact or immutable iteration/weight hash is supplied by this code.

3. **There ARE historical base-vs-GD result tables, but they belong to the earlier Evo-1 route.** `data/phase2/benchmark_pilot_lean/base` and `gd_full_ar5` contain archived aggregate evaluation CSVs on undo. Their evaluator imports `phase1.utils.load_local_checkpoint` (Evo1), and the associated GD metadata lists32 layers, while our original Evo2-1B has25. Their paths are `data/phase2`, not the Evo2 adaptation output path. These are evidence of an archived comparison, not a corrected BioNeMo Evo2 checkpoint handoff.

## Existing historical benign comparison — not new inference

Values below were recomputed from checked-in aggregate metrics only, averaged across the same seven saved layers. They are **historical test metrics** usually using1500 train/500 validation (splice2250/750), with per-task test counts, not our1024/512 official-dev protocol. No test sequences were opened, no test examples scored, no model fit/forward run. Association with Evo1 follows the producer imports/path and32-layer metadata; individual checkpoint weight hashes are not supplied. No comparability to our Evo2 results is claimed.

| Benign task | Historical base mean AUROC | Historical GD mean AUROC | Change |
|---|---:|---:|---:|
| gue_emp_h3 | 0.9097 | 0.8392 | -0.0704 |
| gue_prom_300_all | 0.9294 | 0.8430 | -0.0864 |
| gue_splice_reconstructed | 0.7486 | 0.6313 | -0.1172 |
| gue_prom_core_all | 0.8422 | 0.7659 | -0.0763 |
| gue_human_tf_0 | 0.8527 | 0.7484 | -0.1043 |
| gue_mouse_0 | 0.6559 | 0.5464 | -0.1095 |

The negative changes are collateral classification-performance changes in archived benign metrics. They do not establish hazardous-knowledge removal, and they cannot substitute for the corrected Evo2 comparison. Layer averages are correlated descriptive summaries, not independent replications or new confidence intervals.

## What blocks the requested corrected Evo2 comparison

Only original base weights are present under /workspace/models. The referenced HPC checkpoint/pointer is absent. Need: immutable corrected iteration and accessible files/checksums; exact pretrained parent and conversion lineage; tokenizer/config/precision and supported loading route; actual training/retain/forget exposure manifests; which checkpoint-selection-error results are superseded. Without those, neither fixed-base-readout nor independently refitted base/post comparison can be executed faithfully. The source docs explicitly establish prior checkpoint-loading pitfalls; they do not resolve this missing handoff.

No new GPU job ran. Shared ledger remains579.830295/7200 seconds and inactive. Main/reference branches and all old/new measurement artifacts preserved.

Follow-up artifacts: `/workspace/meeting-artifacts/evo2-graddiff-handoff-20261021T124350Z`. `historical_benign_gd_comparison.json`, six-task filtered archived CSVs, source snapshots/hashes and exact remote refs are retained.

GitHub connector searches for GradDiff/checkpoint in repository issues and PRs returned no matches; GitHub releases and remote tags were empty. Commit search found the generic checkpoint-handling commit da8a8e07184e6a4f5025ecec1ad98f06a894ce0c, not a corrected BioNeMo handoff.

## Important evidence recovered from deleted Git history

Commit82bb4fb9626e5335e599bc431010ef17aa883466 removed tracked SLURM logs; they remain readable at f002639c8089433f37cbb1057ffca33b36d9da5b. I inspected the checkpoint-loading/save/cancellation lines without running the jobs:

- `evo2_unlearn_pipeline/graddiff_smoketest_10749103.out`: lines245 and271–273 record loading the smoke-run checkpoint directory at iteration0 and saving iteration20. This is a logged smoke-run save, not accessible weight bytes or a corrected checkpoint checksum.
- `evo2_unlearn_pipeline/graddiff_train_10885842.out`: line246 loads the converted base at iteration0; last reported training progress is40/2200. Associated `.err` line373 records SLURM cancellation at2026-10-07T01:12:39. This particular archived log does not establish a completed2200-step result or a corrected checkpoint selection. It does not establish that no later off-repository run exists.
- `evo2_causal_lm_finetune/evo2_baseline_ppl_10708844.out` records base loading at iteration0; baseline logs alone are not a matched corrected post-GradDiff comparison. No historical forget-task metrics are reproduced in this report.

`deleted_log_evidence.json` retains immutable blob hashes and selected checkpoint/cancellation line references. The discovered HPC paths still do not exist on this Pod. Actual corrected model bytes, iteration/hash, parent/conversion/tokenizer and exposure metadata remain the execution blockers.
