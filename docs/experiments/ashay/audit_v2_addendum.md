# Evo2 pilot audit v2 addendum

The original three-task scientific measurements and execution files are preserved. This addendum records robustness repairs and a later CPU verification, not a replacement experiment. The removed clock deadlines remain removed.

## Findings and remediation

| Finding | Reproduced | Fix | Regression evidence |
|---|---|---|---|
| A: rejected resume replaces execution provenance | Yes, isolated synthetic fixture | Collect candidate provenance without writing; compare before model loading or any status/config change; retain original execution manifest and write separate attempted-resume records | Collection is read-only; rejected main() cannot reach model loading or replace provenance/config/status; early identity failure is recorded separately |
| B: empty probe lists return success | Yes, all_passed=true with zero checks | Require all three tasks, both layers, all 18 candidates and exactly six selections; validate file schemas, dimensions, IDs, splits, labels and finite values; recompute provenance associations and all scores | Missing probes/layers/tasks, duplicate selections/candidates, misaligned records, wrong labels, invalid provenance, equally wrong stored cache keys, nonfinite/misdimensioned features and empty task configuration are rejected |
| C: overlap does not affect eligibility | Yes, synthetic exact/RC-overlapping train/dev data received an ordinary completion | Gate before GPU scoring; block compromised tasks without resampling; continue clean eligible tasks; report blocked eligibility explicitly | Known duplicate train/dev sequences cannot create ordinary completion; existing unqualified completion is excluded from reporting; a separate clean task continues |

Final review also reproduced a finite classifier-intercept shift that leaves AUROC unchanged while changing probabilities. Nonzero refit differences are now explicitly qualified, cannot pass unqualified validation, and retain both saved/refit probabilities, coefficients, intercepts and scaler states. The actual pilot has zero such differences.

All required production validator checks use explicit exceptions. No diagnostic overlap override is provided. Official splits are retained; no examples, labels, layers or hyperparameters were changed to recover a score.

## Actual saved-result verification

Original source: `3d3da6bce62a19819a59ba063c11d9a3ac082a70`. Previously verified delivery: `7ad2ec73a12e7cb455e1ae6a5eed128cd9eb53b3`. Clean CPU verification source is `a7c26226747558e2f7dde98f8565abec9cf9a16b`. New delivery provenance is recorded separately in the audit handoff; old execution hashes are not rewritten to match newer source.

| Task | Train NLL | Dev NLL | Dev AUROC blocks.7 | Dev AUROC blocks.15 |
|---|---:|---:|---:|---:|
| gue_emp_h3 | 1.243030058108 | 1.251822394010 | 0.850183150183 | 0.839926739927 |
| gue_prom_300_all | 1.315804162005 | 1.318065238808 | 0.973876953125 | 0.959716796875 |
| gue_splice_reconstructed | 1.149546805875 | 1.149951912835 | 0.778736772487 | 0.767814153439 |

Each task retains 256 train and 128 official dev examples. Splice AUROC is macro one-vs-rest over source labels 0/1/2; binary tasks use class 1 as positive. All six selected classifier AUROCs reconstruct exactly. All 18 candidates were refitted using train-only StandardScaler and balanced lbfgs logistic regression, C in {0.1,1,10}, max_iter=2000, random_state=42. All candidate AUROC differences are zero; all six selected refits have zero maximum probability, coefficient, scaler-mean and scaler-scale difference, with identical predicted labels. All original selection and smaller-C tie rules agree.

Independent loss accounting uses math.fsum over saved per-example loss totals and integer valid-token totals, and does not import/call the producer aggregate() function. Train/dev NLL and perplexity both agree exactly. Full loss sums and target totals are in audit_loss_verification.csv and the audit JSON. These checks establish consistency of saved loss totals; original logits were not saved and were not regenerated.

Selected IDs, original row indices, normalized full-sequence/prefix hashes, lengths, truncation, class counts and official train/dev assignment were checked against the hash-verified GUE archive. Only train.csv/dev.csv members were opened. Exact/RC full-sequence and prefix overlap audits recompute to zero cross-split groups. No homology analysis or test-set evaluation was performed.

The NPZ feature matrices are finite and have the required 384 by 1920 shape per layer. They do not contain embedded row IDs/labels; their association is checked through manifest order, the original producer source and recomputed provenance keys. This is saved-artifact consistency plus independent CPU probe refitting, not independent reproduction of GPU feature extraction. No original metric changed. The pilot remains small and validation-selected.

## Model and backend identity

The expected original checkpoint SHA256 is enforced before model loading: `8ffba7d0e6445a8f2c92d9ff1c4e772c7f73ca9179f5e0c699b8b0ca1b966f64`, for arcinstitute/evo2_1b_base@2279e1df422c991037470302360edd40d0d2ea1e. The installed file was verified without model inference, and the exact SHA256 was independently confirmed against official Hugging Face LFS metadata at the pinned revision. Wrong bytes fail before optional model imports.

All 219 recorded backend Python source files match both the installed files and the pinned official Evo2 source / hash-verified Vortex 1.1.0 wheel. The original, installed and pinned official 1B architecture YAML hashes agree; future inference checks this configuration fingerprint too. Evo2 source is pinned to 53f195997257c56c00e5ef8d33a54f5baad143a6; pinned source fingerprints and the Vortex wheel checksum are committed in configs/evo2_backend_identity.json. The eight historical evaluator/config/runner source hashes were checked against Git objects at the original execution commit.

Team integration is deliberately narrow: the train-only StandardScaler, balanced L2 logistic-regression and saved coefficient/scaler pattern is adapted from phase1_evo2/train_probes.py on undo@17dafba0ba714ea8acf40f362e22653266760077. The evaluator executes its own scoring/pooling/data preparation and calls the official Evo2/Vortex inference backend; it does not directly import the team training pipeline. The 7B default team loader was not reused. BioNeMo and GradDiff checkpoint loading/compatibility has not been established, and no such equivalence is claimed.

## Tests, commands and preservation

Baseline: 13 pilot tests and all five inherited evaluator tests passed (18 total). The complete remediation suite passes 41 tests (28.20 seconds), including 23 new audit regressions and all five inherited evaluator tests; logs are stored in the separate audit directory. The final suite covers all three findings plus original numerical correctness. No optional broad test expansion, environment reinstallation, backbone training, unlearning, replacement GPU experiment or additional rented resource was used. The GPU budget remains 277.054459 / 7200 seconds; no reset occurred.

Commands:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 /workspace/venvs/evo2-pilot/bin/python -m pytest tests/test_benign_pilot.py tests/test_benign_pilot_audit.py tests/test_eval_benchmarks.py -q
/workspace/venvs/evo2-pilot/bin/python scripts/validate_benign_pilot_results.py /workspace/meeting-artifacts/evo2-audit-v2-20261020T1555/evidence_copy --output-dir /workspace/meeting-artifacts/<new-verification-output> --expected-source-commit 3d3da6bce62a19819a59ba063c11d9a3ac082a70
```

Audit artifacts: /workspace/meeting-artifacts/evo2-audit-v2-20261020T1555/. They contain before/after original hashes, archive inventory, synthetic reproductions, regression logs, actual validation/refit results, official backend/config verification and source associations. Outputs are separate from the original run. The original archive remains /workspace/meeting-artifacts/evo2-20261020T1437-recovery-7ad2ec7.tar.gz, SHA256 `16c749f1079d846bc2af7a0d7353373e17888d979cc5256e2ca454d46e698833`. Its own checksum and all 113 archived member hashes were verified.

The original run and archive must remain unchanged; a separately named audit recovery archive and basename-only checksum are supplied in the final handoff. On a Mac, download both to the same directory and use `shasum -a 256 -c <audit-recovery-basename>.tar.gz.sha256`. The checksum beginning 581ba5a belongs to the GUE dataset ZIP, not either recovery archive. OFF-POD BACKUP PENDING: no off-Pod destination has been explicitly authorized. A same-Pod copy is preparation, and the Pod is not automatically terminated. Verify the off-Pod download before stopping it; experiment timeouts do not stop rental billing.

## Meeting update and decisions

The three audit findings were reproduced and repaired, and the saved core results agree under independent loss accounting and CPU classifier refits. No scientific number changed; feature-extraction reproduction and BioNeMo/GradDiff integration remain unverified. The original execution and archive are preserved, with audited source and a new recovery handoff prepared separately. Sayyed/Aris should confirm the canonical reference/backend, provide accessible compatible BioNeMo/GradDiff checkpoints and actual qualified forget/retain training manifests, define biological groups, and agree on preservation criteria before new unlearning comparisons.
