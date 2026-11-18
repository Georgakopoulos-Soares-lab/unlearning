# A09 saved-analysis restore

This tool restores the declared report/consumer payload and verifies its archive and every member before loading trusted serialized heads. It does not run a scientific production CLI, fit, model forward, new draw or checkpoint qualification. Model weights and installed GPU/runtime binaries are excluded; see [reacquisition map](REACQUISITION_MAP.json). Full GPU recreation remains unverified.

## Current-Pod recovery with existing verified restored dependencies

The concrete owned command, after BACKUP_MANIFEST.json is sealed, is:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' /workspace/venvs/pod-a-tools/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A09-attempt-001/code/restore.py --backup /workspace/wt-pod-a/docs/experiments/ashay/POD_A/20261117T084728Z-a01/attempts/A09-attempt-001/BACKUP_MANIFEST.json --destination /workspace/recovery/POD_A/20261117T084728Z-a01/A09-attempt-001/manual-consumer-001 --use-recorded-dependencies
```

The destination must not exist. The tool forces a fresh download into its new cache, rejects unsafe/duplicate/extra members and checks each declared SHA256/size. It uses the pinned dataset revision in BACKUP_MANIFEST.json, not a moving branch. Every dependency is pinned in [the graph](RECOVERY_DEPENDENCY_GRAPH.json) and reverified before the frozen CPU consumer panel. The currently restored roots are prior fresh consumers, not original producer paths.

## Fresh-server sequence

Clone research POD_A at the exact report-delivery/metadata commit identified by the final delivery receipt. Recover this A09 prompt/approval/source snapshot. Create Python 3.12.3 with NumPy 2.5.4, SciPy 1.18.1, scikit-learn 1.7.2, joblib 1.5.2 and threadpoolctl 3.8.0; use the exact inherited environment recipe and wheel/source identities referenced by ENVIRONMENT_CHECK.json and the A04 metadata archive. Use existing authorized private-dataset authentication without copying account files into payloads. Install the recorded transfer-tool environment separately; do not upgrade the numerical environment opportunistically.

Run the same owned restore CLI with `--restore-dependencies` in place of `--use-recorded-dependencies`. Use a new absolute destination appropriate to that server. The tool downloads only the exact declared archives/objects, verifies their immutable sizes/hashes, restores all members safely and creates a copied dependency-root translation context. It never edits historical producer receipts. No shared /workspace with Pod B is assumed. This can require the complete declared historical saved-analysis dependency graph; do not download model weights. If valid local restored dependencies already exist, use `--context` with the copied root translation and preserve original receipts.

After a restore, the exact CPU consumer invocation has this form; the restore tool prints the concrete command with real new paths:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python <restored-payload>/code/consumer.py --root <restored-payload> --context <translated-context.json>
```

The angle-bracket notation is documentation of translated paths, not a runnable production command. The restore CLI above constructs those actual arguments and accepts `--cpu-python` for the exact rebuilt numerical interpreter. Its help/syntax is checked without launching science.

## Finite computational scope

Before outcomes, A09 froze R4/R6 × human TF/three-class splice × both policies at final norm/seed42/dev: eight saved prediction/metric paths. It additionally checks one saved A08 audit-refit head per candidate; human-TF/layer16/seed42 R6−R4 for both policies/five metrics/all 2,000 original draws; and the human-TF dev LM NLL/PPL contrast. The consumer checks every report-table/figure source hash and row identity needed for those claims. Probability tolerance is 1e−10; metrics, draws and intervals 1e−12. A08's prior 40-path proof is reused and attributed separately. Saved-feature analysis recovery does not establish full model/GPU recreation or complete missing science.

There is no automatic restart. After verified terminal A09 delivery, the owned administrative loop stops while the Pod remains running. Any further identity/qualification/backfill or perturbation work requires a new explicit scope and direct approval.
