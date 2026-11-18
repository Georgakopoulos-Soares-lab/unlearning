# A08 CPU recovery

The three immutable scientific archives below passed force-fresh download into separate empty consumers and exact safe-member validation. Restore only these pinned revisions. Keep the dataset private.

## R4

Revision `d10c34a50b37bb8f12782b6b2684611953110db1`; archive `POD_A/20261117T084728Z-a01/A08/A08-attempt-001/R4-checkpoint-001/A08-R4-checkpoint-001.tar.gz`. SHA256 `bdc5884a259900cc91a139480012a569637a9632b7c0fe87e66c388c9e1443df`; 179,918,975 bytes; 1,841 members checked.

Existing checked consumer: `/workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/R4-fresh-001/consumer/A08-R4-checkpoint-001`. Exact CPU check command:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/R4-fresh-001/consumer/A08-R4-checkpoint-001/artifacts/code/restore_audit.py --root /workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/R4-fresh-001/consumer/A08-R4-checkpoint-001 --candidate R4
```

## R6

Revision `9a398582de6287f28f1bccfdea6fd3753072929b`; archive `POD_A/20261117T084728Z-a01/A08/A08-attempt-001/R6-checkpoint-001/A08-R6-checkpoint-001.tar.gz`. SHA256 `8250d61baad68e6d8f0de42b7ae9939159c2a038f18e0c25003628218e02c1cd`; 180,115,610 bytes; 1,859 members checked.

Existing checked consumer: `/workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/R6-fresh-001/consumer/A08-R6-checkpoint-001`. Exact CPU check command:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/R6-fresh-001/consumer/A08-R6-checkpoint-001/artifacts/code/restore_audit.py --root /workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/R6-fresh-001/consumer/A08-R6-checkpoint-001 --candidate R6
```

## analysis

Revision `5da5c27920eb1aeaa7abc0bf4963a5d3e6feb56e`; archive `POD_A/20261117T084728Z-a01/A08/A08-attempt-001/analysis-checkpoint-001/A08-analysis-checkpoint-001.tar.gz`. SHA256 `12eb4fe1f93f8b126c6af7bd481fc73712d9991ee70d9ce41fa45ea482105155`; 68,390,649 bytes; 1,796 members checked.

Existing checked consumer: `/workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/analysis-fresh-001/consumer/A08-analysis-checkpoint-001`. Exact CPU check command:

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/analysis-fresh-001/consumer/A08-analysis-checkpoint-001/artifacts/code/restore_audit.py --root /workspace/recovery/POD_A/20261117T084728Z-a01/A08-attempt-001/analysis-fresh-001/consumer/A08-analysis-checkpoint-001 --analysis
```

## Fresh-machine sequence and limitations

Use the frozen CPU environment in ENVIRONMENT_CHECK.json. Download each archive with `huggingface_hub.hf_hub_download`, `repo_type='dataset'`, the exact revision and path above, `force_download=True`, and a new empty cache. Verify archive byte count and SHA256 before opening it. Reject absolute/traversing paths, symlinks, hardlinks, duplicate or unexpected members; compare the exact member set and all MEMBER_MANIFEST.json size/digest entries before consuming arrays or trusted serialized audit heads. The owned checkpoint_phase.py and protect_delivery.py supply the executable validation sequence.

Each scientific archive contains DEPENDENCIES.json with exact immutable A03/A06/A07 references and path translations. Restore missing dependencies safely by those revisions; reverify every member. Replace consumer-root entries in a copied DEPENDENCIES.json with the corresponding new consumer roots, preserving the original dependency receipts. Run the command above with the new `--root` and restored source path. Do not substitute original producer paths for recovery consumers. Both candidate consumers must exist before the analysis check. All command options were checked against the owned restore CLI.

The recorded panel checks 40 candidate probability/metric paths, both candidates, all five tasks, both anchors and both readout policies, plus two restored audit-refit heads. It also checks the new human-TF layer-16 seed-42 R6−R4 contrast for both policies, all five metrics and all 2,000 draws, plus new human-TF dev LM NLL/PPL points. This supplements the full live-input numerical audit. It is neither GPU/runtime recreation nor a second 780-head refit. Weights and unchanged historical payloads are referenced rather than repacked; derived reference caches are regenerable. The final public report/code/figure snapshot is protected separately after push, with an immutable metadata revision and final-receipt revision in the run's DELIVERY_RECEIPT.json.

No science automatically resumes after recovery. A08 is complete for its qualified scope; A09 requires separate direct approval. R2/R5 backfill and R3 qualification are outside that reporting scope.
