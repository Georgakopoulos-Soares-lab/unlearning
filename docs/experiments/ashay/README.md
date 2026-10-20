# Frozen original Evo2-1B GUE pilot

Audit remediation and historical saved-result verification are documented in
[audit_v2_addendum.md](audit_v2_addendum.md). The original GPU measurements
remain associated with `3d3da6bce62a19819a59ba063c11d9a3ac082a70`, rather than
the later validation/delivery commit. Do not rerun GPU stages in that original
directory or rewrite its manifests to match newer source.

The current validator is read-only and requires a separate output directory:

```bash
/workspace/venvs/evo2-pilot/bin/python scripts/validate_benign_pilot_results.py \
  /workspace/meeting-artifacts/evo2-20261020T1437 \
  --output-dir /workspace/meeting-artifacts/<new-audit-output> \
  --archive /workspace/data/gue/GUE.zip \
  --expected-source-commit 3d3da6bce62a19819a59ba063c11d9a3ac082a70
```

It checks all configured tasks/layers, source associations, all 18 candidates,
six selected classifiers, official train/dev records, and actual feature shapes.
Loss accounting does not call the producer's aggregation function. All candidate
classifiers are refitted on saved training features using the recorded settings.
Saved feature files lack embedded row IDs/labels; their order is associated through
the fixed manifest, producer source and recomputed cache key. This is saved-artifact
verification, not an independent reproduction of GPU feature extraction.

Future inference enforces the exact original weight SHA256 before model loading
and fingerprints the backend against the pinned official source/wheel. Resume
attempts are written separately and cannot replace an existing execution manifest.
Tasks with selected train/dev exact or RC overlap are blocked without changing
official splits, and clean eligible tasks can continue. No diagnostic override
is provided. These robustness changes do not revise the historical measurements.

Only `experiments-ashay` is writable. Run from its existing worktree:
`/workspace/wt-eval-pilot`. The original checkout `/workspace/unlearning`
remains on clean `main`. No new unlearning or backbone training is included.

The protocol is frozen in `configs/benign_pilot.json`. It uses the original
`arcinstitute/evo2_1b_base` checkpoint revision
`2279e1df422c991037470302360edd40d0d2ea1e`, official Evo2 commit
`53f195997257c56c00e5ef8d33a54f5baad143a6`, and upstream FP8 input projections.
Backend installation and exact resolved versions are recorded in the run's
environment lock and manifest. This standalone inference pilot has not been
validated as equivalent to the team's BioNeMo-trained checkpoints.

The official GUE download is linked by DNABERT-2 commit
`f25bed9ee20db966dff39e5c1571249d04e36404`. Archive SHA256:
`581ba5a69843769f4cbc34470e2fe970f8ee371280914bd66574af01ee60cd79`.
The archive's actual paths are `GUE/EMP/H3`, `GUE/prom/prom_300_all`,
and `GUE/splice/reconstructed`. The pilot opens only `train.csv` and `dev.csv`.
H3 and promoter retain binary labels 0/1. Splice retains its original three
labels 0/1/2 and uses macro one-vs-rest AUROC; no biological class meanings
are inferred from the integer IDs. Label sets and source row counts are verified
from the official train/dev CSVs before selection.
Initial preparation failed because repository aliases referred to flattened
paths; the archive's actual mappings are now explicit. That attempt is retained
in `/workspace/meeting-artifacts/evo2-20261020T1430`.

Source review verified `phase1_evo2` and `phase2_evo2` on `origin/undo` at
`17dafba0ba714ea8acf40f362e22653266760077`; the loader defaults to 7B.
The present pilot explicitly loads 1B. The balanced L2 logistic probe and
train-only scaler pattern is adapted from `phase1_evo2/train_probes.py`;
the pilot omits its test-set evaluation and records all validation candidates.
The BioNeMo branch at `5c5eb74144991271fe3aef40431f01aaddb58b9a`
contains a separate Evo2 training/classification route; no components were
imported from it. Missing audit/handoff documents were not reconstructed.

## Reproduction

Use `/workspace/venvs/evo2-pilot/bin/python` (system torch is inherited read-only).
CPU tests import no optional Evo2 modules. Synthetic fixtures test correctness
only. Set a **new** run directory for a changed configuration or implementation:

```bash
cd /workspace/wt-eval-pilot
RUN=/workspace/meeting-artifacts/<unique-run-id>
bash scripts/run_benign_pilot.sh preflight "$RUN"
bash scripts/run_benign_pilot.sh prepare "$RUN"
bash scripts/run_benign_pilot.sh smoke "$RUN"
bash scripts/run_benign_pilot.sh pilot "$RUN"
bash scripts/run_benign_pilot.sh report "$RUN"
```

The user removed the original clock deadlines while preserving the cumulative
compute budgets. The launcher records GPU-job time across attempts in
`/workspace/meeting-artifacts/evo2-pilot.gpu-budget.json`, including the failed
first smoke attempt. A changed scientific configuration requires a new run
directory. The launcher
locks GPU execution and propagates failures through `tee`. Completed task
caches require matching manifest, model, source, package and backend hashes.
Partial JSONL metrics survive interruptions; incomplete feature extraction
restarts that task. Full activations and logits are not saved.

The maximum-512-nucleotide-prefix protocol uppercases and strips whitespace,
maps IUPAC ambiguity to N, and rejects unsupported symbols. ASCII character
tokens have no BOS/EOS prepended. Targets are positions 1 through L-1;
pooling includes all nucleotide positions, excluding right padding. Input
lengths are rounded up to a multiple of 16 for Transformer Engine FP8 GEMMs.
Original sequence hashes refer to normalized full sequences. No biological
group IDs are invented. Exact/RC overlap checks cover selected pilot rows.

All C values (0.1,1,10) are fit on train only; validation AUROC selects C,
with ties favoring smaller C. These are validation-selected engineering
measurements, not unbiased held-out generalization estimates. Corpus NLL
is token weighted and should not be used to rank unrelated task accuracy.

OFF-POD BACKUP PENDING until the separate recovery archive is downloaded
and verified. Source pushes do not back up every measurement. Do not stop
the Pod before verification; experiment timeout does not stop rental billing.
