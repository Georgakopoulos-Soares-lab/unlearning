# Evo2 benign-task pilot: final closeout

Pilot closeout is **COMPLETE**. The three-task frozen-reference run and its later saved-result audit are complete. Scientific measurements are unchanged. Source delivery and recovery identities are recorded separately below; **off-Pod backup remains PENDING** until a downloaded copy is verified. The GradDiff comparison has not started.

This is the authoritative closeout entry point. The [original core report](core_pilot_report.md) retains the execution history, numerical smoke results and runtime measurements. The [audit addendum](audit_v2_addendum.md) describes the later repairs and independent CPU verification. Neither historical document is rewritten to imply that the later safeguards existed during the GPU run. The original report's validator invocation is historical; the current [README](README.md) documents the required separate output directory.

## What was run and what it supports

A frozen, pretrained Evo2-1B reference scored three GUE tasks: H3 (`gue_emp_h3`), promoter (`gue_prom_300_all`) and splice (`gue_splice_reconstructed`). Each used 256 training and 128 official development examples: 768 train plus 384 dev, **1,152 records total**. Selection used seed 42 and class stratification within the official splits; selected rows were restored to source order. No test examples were evaluated.

Causal NLL scores the next nucleotide at positions 1 through L−1, with no added BOS/EOS and padding excluded. Corpus NLL is the sum of saved loss totals divided by the sum of valid target counts, in natural-log units; perplexity is exp(NLL). Sequences were normalized and capped at a 512-nucleotide prefix. The actual selected lengths were 500 for H3, 300 for promoter and 400 for splice, with no truncation or ambiguous scored bases. This yields respectively 499, 299 and 399 targets per example. The original GPU pilot used batch size 1 after its recorded numerical smoke checks.

Frozen representations at zero-based `blocks.7` and `blocks.15` were mean-pooled across nucleotide positions, including the first nucleotide and excluding padding. Each task's saved feature matrix has 384 rows and 1,920 columns per layer. A StandardScaler was fit on training features only, followed by balanced L2 logistic regression (`lbfgs`, max_iter=2000, random_state=42). C was chosen separately for each task/layer from {0.1, 1, 10} using dev AUROC, with exact ties favoring smaller C. Both prescribed layers and all 18 candidates are retained.

## Exact saved results

These values are copied at the saved JSON's round-trip precision from `A/verification-delivery/artifact_validation.json`, fields `losses` and `checks`. The table is checked against that artifact during closeout; no classifier or backbone was rerun to generate it. A pair in the final columns is **AUROC (selected C)**. Train/dev means the official train/dev subsets, not a new held-out split.

<!-- RESULTS:START -->
| Task | Train/dev | Train NLL | Dev NLL | Train perplexity | Dev perplexity | Block 7 AUROC (C) | Block 15 AUROC (C) |
|---|---:|---:|---:|---:|---:|---:|---:|
| H3 | 256/128 | 1.2430300581078038 | 1.2518223940100066 | 3.4661000538227844 | 3.4967095370065873 | 0.8501831501831502 (10) | 0.8399267399267399 (10) |
| Promoter | 256/128 | 1.315804162004922 | 1.3180652388076852 | 3.727747493148769 | 3.736185752713538 | 0.973876953125 (10) | 0.959716796875 (10) |
| Splice | 256/128 | 1.1495468058747063 | 1.149951912835443 | 3.1567619594901553 | 3.1580410447990217 | 0.7787367724867725 (0.1) | 0.7678141534391534 (0.1) |
<!-- RESULTS:END -->

Binary AUROC uses class 1 as positive. Splice retains source labels 0/1/2 and uses **macro one-vs-rest AUROC**; no biological class meaning is inferred from those integers. Train/dev target totals are H3 127,744/63,872; promoter 76,544/38,272; splice 102,144/51,072. Full loss sums and perplexity verification are in [audit_loss_verification.csv](audit_loss_verification.csv); all candidate checks are in [audit_candidate_checks.csv](audit_candidate_checks.csv).

The audit reconstructed all six saved classifier AUROCs and refit all 18 candidates on saved training features. Candidate AUROC differences were zero. For each of the six selected refits, maximum differences in probabilities, coefficients, intercepts, scaler means and scaler scales were **0.0**, and predicted labels were identical. This is an observed equality in the recorded CPU environment, not a guarantee across software or hardware changes.

## Evidence and revisions

Artifact aliases identify exact existing Pod directories and the corresponding recovery contents:

- **R**: `/workspace/meeting-artifacts/evo2-20261020T1437/`, the original run. Its recovery archive is nested unchanged inside the audit package, under `original/`.
- **A**: `/workspace/meeting-artifacts/evo2-audit-v2-20261020T1555/`, later audit evidence. Its read-only `evidence_copy/` matched R; the copy itself is omitted from the package to avoid duplicating the original archive.
- **C**: `/workspace/meeting-artifacts/evo2-closeout-v3-20261020T1658/`, final closeout checks and delivery handoff, supplied in the closeout supplement.
- **E**: original successful GPU execution `3d3da6bce62a19819a59ba063c11d9a3ac082a70`.
- **V**: clean saved-result verification `49c71afd6303e8dd342dc64b9bce1449ed1f5690`, at `2026-10-20T16:27:39.326458+00:00`. This is also the last audit delivery, not the original inference source.
- **D**: final closeout documentation delivery, the commit introducing this document. Its exact full hash and independently checked remote head are in **C/closeout_delivery.json**, created after commit/push and included in the supplement. D changes documentation only; it does not replace E or V. This avoids a self-referential commit hash in the committed file.

Earlier measured-report delivery was `7ad2ec73a12e7cb455e1ae6a5eed128cd9eb53b3`. The principal robustness repair was `a7c26226747558e2f7dde98f8565abec9cf9a16b`; V adds the numerical-disagreement qualification and final audit handoff. The addendum also describes an earlier clean verification at a7c2622; the final verification reused here is V.

| Claim | Actual supporting artifact | Verification method | Execution / verification revision | Remaining limitation |
|---|---|---|---|---|
| All 1,152 source associations, IDs, labels, train/dev assignments and hashes agree | R/subset_manifest.jsonl; R/data_provenance.json; A/verification-delivery/artifact_validation.json: `data`, `samples_verified` | `validation_data.verify_dataset` verified the hash-pinned GUE ZIP, opened only train/dev CSVs, reconstructed selected source rows/order, independently normalized sequences and checked full/prefix hashes, lengths and class counts | E produced records; V verified them | Deterministic member/row IDs are not biological group identifiers; no test content was opened |
| Target counts and train/dev NLL/perplexity agree | R/`<task>`/per_example_metrics.jsonl; R/`<task>`/complete.json; A/verification-delivery/artifact_validation.json: `losses` | `validation.validate_saved` checks L−1 targets per record; `independent_losses` uses math.fsum and integer token totals, then exp(NLL), without calling producer aggregate() | E / V | Independent accounting of saved totals; original logits were not retained or regenerated |
| All 18 candidate rows and six selections agree | R/baseline_probe_results.csv; R/`<task>`/probe_results.json and complete.json; A/verification-delivery/artifact_validation.json: `candidate_checks` | Complete task/layer/C coverage and record counts; refit each candidate using recorded settings; compare dev AUROC and smaller-C tie rule | E / V | Hyperparameters were selected on these same dev examples |
| Six saved classifiers reconstruct and refit exactly | R/`<task>`/features.npz and blocks.{7,15}.probe.npz; A/verification-delivery/artifact_validation.json: `checks[*].refit` | Finite shapes/classes checked; reconstruct saved classifier; independently fit train-only scaler and classifier; compare AUROC, probabilities, predicted labels, coefficients, intercepts, scaler mean/scale | E / V | Reuses saved embeddings; does not independently establish the GPU features' row identity or numerical correctness |
| Selected exact/RC full-sequence and prefix cross-split overlaps are zero | R/data_provenance.json: `overlap`; A/verification-delivery/artifact_validation.json: `data[*].overlap` | Independently group normalized full sequences and prefixes by exact sequence and min(sequence, RC); compare counts and membership | E / V | Selected records only; neither homology nor actual forget/retain training-set exposure is established |
| Original checkpoint identity is pinned and future inference enforces it | R/run_manifest.json and model_contract.json; A/upstream_checkpoint_identity.json; A/enforced_identity_release_verification.json; configs/evo2_backend_identity.json | Original tensor audit; local file SHA256 agrees with official pinned Hugging Face LFS metadata; wrong bytes rejected before model loading in regression test | E records original identity; audit source through V enforces it | No BioNeMo conversion or GradDiff equivalence is established |
| Backend/config and original evaluator source are traceable | R/run_manifest.json: `backend_files`, `source_hashes`; A/upstream_backend_verification.json; A/architecture_config_verification.json; A/inference_source_git_verification.json | All 219 backend Python files matched recorded, installed and pinned official source/wheel; official/installed/original 1B YAML agrees; eight evaluator/config/runner hashes matched E's Git blobs | E / V | Python/config identity does not prove universal binary-kernel or hardware equivalence |
| All three robustness failures were reproduced and repaired | A/findings_reproduced.json; A/remediation_tests_delivery.log; tests/test_benign_pilot_audit.py | Separate synthetic reproductions; final relevant suite recorded **41 passed**; exact regressions listed below | Pre-fix behavior from 7ad2ec7; repairs a7c2622 and V | Synthetic regressions establish repair behavior; historical measurements were not rerun with the later safeguards |
| Original measurements, archives and GPU budget remain unchanged | A/original_evidence_before.json; A/original_preservation_final.json; C/evidence_reuse_verification.json | Rehash all 114 original files and audit inputs; compare original archive/sidecar and cumulative ledger; check packaged audit payloads against inventory | E evidence preserved through V and closeout D | Same-Pod verification is not an external backup |
| Existing validation can be reused without another experiment | A/verification-delivery/artifact_validation.json: `verification_source`; C/evidence_reuse_verification.json | Its five validator/config source fingerprints match V's Git objects and current files; packaged validation matches on-Pod JSON; audit inputs, raw ZIP, local checkpoint/backend and budget remain unchanged | V reused at D | No new semantic validation, CPU refit or GPU extraction was claimed in closeout |
| Recovery packages are internally consistent | A/INVENTORY.json, CHECKSUMS.sha256, archive_verification.json; C/existing_archive_verification.json; supplement INVENTORY.json, CHECKSUMS.sha256 and outer sidecars | Outer basename-only SHA256, tar integrity, complete member coverage and member hashes; original nested archive and source recovery verified | Previous delivery 7ad2ec7, V; supplement at D | External download verification remains pending; weights/raw ZIP/environments require pinned redownloads |

Closeout uses hashes and inventories to establish that the already-successful audit is still applicable. It does not rerun the 41-test suite, independent loss aggregation, CPU refits or GPU stages merely to obtain another success message. The closeout supplement retains its checker and records; only documentation consistency/link checks are new.

## Scientific limits

- These are **small, validation-selected pilot results**, not untouched test-set estimates. No inferential confidence interval or formal preservation claim is supplied.
- The pilot evaluates a pretrained reference. It demonstrates neither unlearning nor hazardous-knowledge removal, and it does not establish capability preservation after an intervention.
- BioNeMo/GradDiff checkpoint compatibility remains unverified. Matching a model-size name or architecture is insufficient to establish identical weights, tokenizer semantics, layers or precision behavior.
- Exact/RC checks do not establish biological-group or homology independence, nor absence of overlap with the actual training/forget/retain corpora.
- Saved feature NPZs contain arrays and a cache key, **without embedded row IDs or labels**. The association uses task-filtered manifest order, source-at-run producer code, matching record counts/splits/classes and a provenance key recomputed from actual manifest/config/source hashes plus recorded checkpoint/backend identity. This detects inconsistent saved associations; it cannot independently prove which sequence generated each embedding.
- Saved-artifact verification and CPU refitting from saved features are distinct from independent GPU feature extraction. The latter did not occur during the audit or closeout. Saved logits also were not independently regenerated.
- Cross-task NLL differences are not a ranking of biological task performance. Sequence composition, lengths and task distributions differ.
- The original smoke recorded larger-batch numerical differences. Batch 1 was used for the pilot, and its repeated smoke agreed; padding/FFT/FP8/kernel contributions were not isolated. The [original report](core_pilot_report.md) retains those measurements and qualifications.

## Repaired robustness failures

| Finding | Status and repair | Specific evidence retained at V |
|---|---|---|
| A: failed resume could replace execution provenance before rejection | Reproduced, fixed, tested. Candidate provenance is collected without writing; identity/compatibility is checked first. Existing run_manifest.json is retained, with attempted resumes recorded separately | `test_provenance_collection_does_not_write`, `test_rejected_resume_preserves_execution_before_model_load`, `test_identity_failure_records_attempt_without_replacing_provenance` |
| B: empty probes could yield checks=[] and all_passed=true | Reproduced, fixed, tested. Require three tasks, two layers, 18 candidates, six selections, correct IDs/splits/labels/counts/dimensions, finite arrays and recomputed provenance. Validation writes only to a separate output directory | `test_corrupted_artifacts_cannot_pass` covers missing probes/layers and invalid associations/provenance; `test_validator_requires_separate_output_directory`. `test_finite_classifier_disagreement_is_qualified` also proves a finite intercept shift cannot pass merely because AUROC stays unchanged |
| C: detected train/dev overlap did not block ordinary completion | Reproduced, fixed, tested. Eligibility is enforced before scoring; compromised tasks are blocked without changing official splits and clean tasks continue. Reports exclude ineligible ordinary completions | `test_overlap_blocks_ordinary_completion_and_report`, `test_overlap_gate_continues_clean_tasks` |

The complete evidence is A/findings_reproduced.json and A/remediation_tests_delivery.log. These are later engineering repairs. The original E run's scientific numbers remain the historical measurements; they are not relabeled as having executed under the repaired runner.

## Readiness for the pretrained-reference versus existing GradDiff comparison

The next step requested in the supplied closeout prompt is Aris's pretrained-reference/GradDiff comparison using the same qualified benign-task protocol. The actual Slack thread is not present in the available evidence. No message was sent, checkpoint substituted, training pipeline constructed or comparison launched.

| Decision | Already established from repository/Pod evidence | Sayyed/Aris confirmation still required |
|---|---|---|
| Canonical base, checkpoint/backend/tokenizer | Pilot is official `arcinstitute/evo2_1b_base@2279e1df422c991037470302360edd40d0d2ea1e`, SHA256 `8ffba7d0e6445a8f2c92d9ff1c4e772c7f73ca9179f5e0c699b8b0ca1b966f64`; official Evo2 `53f195997257c56c00e5ef8d33a54f5baad143a6`, Vortex 1.1.0, CharLevelTokenizer(512), no BOS/EOS. The [undo loader](https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/17dafba0ba714ea8acf40f362e22653266760077/phase1_evo2/utils.py) defaults to 7B, so it is not an interchangeable reference | Confirm 1B versus 7B, exact original pretrained weights, conversion provenance, precision recipe, layer definitions, tokenizer/vocabulary/special-token semantics and the canonical inference backend for both checkpoints |
| Existing GradDiff availability and compatibility | [BioNeMo launcher](https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/5c5eb74144991271fe3aef40431f01aaddb58b9a/evo2_unlearn_pipeline/train_graddiff_emp_h3_host_tropism.sbatch) references a converted `evo2_1b_base_mbridge` and `nucleotide_fast_tokenizer_256`. The [evaluation script](https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/5c5eb74144991271fe3aef40431f01aaddb58b9a/evo2_unlearn_pipeline/eval_checkpoint_gue_test.sbatch) uses an HPC `eval_pointer`; neither referenced checkpoint path exists on this Pod. Only the official base weight file is present under /workspace/models | Supply the specific existing checkpoint iteration, immutable checksum, accessible location, format, base lineage, tokenizer files, training metadata and approved loading/conversion route. Script text or a moving pointer does not prove the actual checkpoint's identity or completed training |
| Evaluation manifests and grouping | Current selected manifests, train/dev splits, hashes, counts and exact/RC audits are frozen and recoverable. No biological groups were supplied. BioNeMo launcher names H3 retain data, making real training exposure a question to resolve rather than assume away | Qualify the evaluation against the checkpoint's actual train/forget/retain manifests; establish source/organism/locus or other justified biological groups and homology rules. If a split changes, use a new versioned comparison manifest and re-establish its base reference; do not rewrite this pilot |
| Fixed versus newly fitted probes | Saved base scalers/classifiers are available. The [undo evaluator](https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/17dafba0ba714ea8acf40f362e22653266760077/phase2_evo2/eval_unlearn.py) contains a `--fresh-probe` route; it was not imported/executed here | Agree whether to report both. Recommended proposal: fixed base scaler + classifier on each checkpoint measures stability of the original readout; fresh train-fitted scalers/classifiers on each checkpoint measure recoverable linear task information under the same fitting/selection budget. A fixed-readout drop alone cannot establish information removal. Freeze representation semantics, candidates, splits and reporting before comparison |
| Preservation, uncertainty, ownership and budget | This pilot supplies baseline values and per-example artifacts, not an accepted preservation margin or uncertainty design. Cumulative GPU-job ledger remains 277.054459/7200 seconds, with no active stage; removed clock deadlines did not reset it | Predeclare per-task acceptable AUROC decreases and NLL increases, paired comparison units, biological-group resampling/interval method and confidence level, multiplicity/selection handling, and decision rule. Agree an independent evaluation design before stronger claims. Assign checkpoint/protocol owners and a bounded first-comparison compute/storage allocation within the existing authorization; remaining ledger capacity alone is not authorization to start |

The evaluator adapts the train-only scaling and balanced logistic-probe pattern from `undo@17dafba0ba714ea8acf40f362e22653266760077:phase1_evo2/train_probes.py`. It implements its own data preparation, causal scoring and pooling, calling official Evo2/Vortex inference. It does not directly import the team's training pipeline or establish equivalence to the BioNeMo route. Read-only source snapshots/hashes for the readiness assessment are in C/repository-references/ and C/next_comparison_repository_evidence.json.

Draft Slack update, **not sent**:

> The frozen Evo2-1B benign pilot is closed out across H3, promoter and splice, with 256 train/128 dev examples each and both layers reported. The saved losses and all six selected probes verified; all 18 CPU refits agree and 41 tests passed. The three audit bugs are fixed, and the original measurements are unchanged. These are small, validation-selected reference results, not evidence of unlearning. The closeout links the results and recovery files. Before comparing the existing GradDiff checkpoint, we need to settle checkpoint/tokenizer compatibility, qualified manifests and groups, probe policy, preservation criteria and ownership/budget. Off-Pod download verification is still pending.

Questions that unlock the next comparison:

1. Which model size, exact pretrained revision/backend/tokenizer and immutable GradDiff checkpoint iteration/hash should be compared, and who can provide the checkpoint, conversion provenance and loading route?
2. Which evaluation manifests are qualified against its actual train/forget/retain sets, and what biological grouping/homology rules define independent comparison units?
3. Should we report both fixed base probes and fresh train-fitted probes under the same frozen selection budget, with the distinction above?
4. What per-task AUROC/NLL preservation margins, confidence level, paired group uncertainty method and multiplicity/validation-selection treatment should be agreed before results are seen?
5. Who owns checkpoint compatibility and protocol sign-off, and what cumulative compute/storage budget is approved for the first comparison?

## Recovery and the next action

Keep the existing audit package and add the small closeout supplement. **Complete pilot/audit/closeout recovery requires these four files**, all under `/workspace/meeting-artifacts/`:

1. `evo2-audit-v2-20261020T1555-recovery-49c71af.tar.gz`
2. `evo2-audit-v2-20261020T1555-recovery-49c71af.tar.gz.sha256`
3. `evo2-closeout-v3-20261020T1658-supplement.tar.gz`
4. `evo2-closeout-v3-20261020T1658-supplement.tar.gz.sha256`

The audit archive SHA256 remains `e4b78ef249c792499d107449971c2480dd11d1b716615ccfab61d5377351b19a`. It has 71 members, including the unchanged original `evo2-20261020T1437-recovery-7ad2ec7.tar.gz` (113 members, SHA256 `16c749f1079d846bc2af7a0d7353373e17888d979cc5256e2ca454d46e698833`) and its sidecar. Thus the old standalone original archive need not be downloaded again. Original configs, manifests/provenance, losses, features, classifiers, completions, logs, source snapshots, patches and Git recovery bundles are retained. Historical failed attempts remain distinguishable. The supplement adds this closeout/README, the received v3 prompt, evidence reuse checks, results source, source-reference records, final delivery/remote proof, documentation-check log, inventory/checksums and a Git bundle/patch for D.

The original/audit bundles require repository base `af92e593162478c8aa40b6303ed0f0e508affac7`; the closeout delta bundle requires V. Source snapshots and patches are also included. Verify bundle prerequisites in an existing repository clone before importing them; inspect **C/RECOVERY_HANDOFF.md** for exact restoration and verification commands. The packages exclude raw weights, the raw GUE ZIP, environments and credentials; their pinned references/hashes and environment lock permit redownload/reconstruction. Bitwise GPU reproduction is not promised. The checksum beginning `581ba5a` belongs to the raw GUE ZIP, not a recovery archive.

**Next concrete action:** use the Pod's Jupyter file browser to download the four files above. Put them in the same folder on your Mac and run:

```sh
shasum -a 256 -c evo2-audit-v2-20261020T1555-recovery-49c71af.tar.gz.sha256
shasum -a 256 -c evo2-closeout-v3-20261020T1658-supplement.tar.gz.sha256
```

Both must report `OK`. No authorized accessible off-Pod destination was supplied, so no external upload or external verification is claimed. A source push does not back up untracked measurements. Keep the Pod available until the external copy is verified; it has not been stopped automatically. No new inference, training, search or comparison job is left running by closeout.
