# Restore A04-attempt-004 evidence — saved TRAIN checks only

The bounded private evidence archive contains the six sealed TRAIN qualification outputs, exact code, the three same-checkpoint R3 anchor bundles, frozen 12-row training manifest, prompts, source/environment locks, original mirror receipts and detailed metadata. It excludes model weights and installed runtime binaries. Native R3/R5 assets are durable dependencies in the explicitly approved private immutable mirror; see [payload index](PAYLOAD_RECOVERY_INDEX.json). No second GPU sweep or full GPU/runtime rebuild is claimed.

## Current-Pod command after backup completion

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/pod-a-tools/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A04-attempt-004/code/restore4.py --backup /workspace/wt-pod-a/docs/experiments/ashay/POD_A/20261117T084728Z-a01/attempts/A04-attempt-004/BACKUP_MANIFEST.json --destination /workspace/recovery/POD_A/20261117T084728Z-a01/A04-attempt-004/manual-evidence-consumer-001 --cpu-python /workspace/venvs/a03-cpu-audit-20261117/bin/python
```

The destination must be a new absolute path. This exact CLI syntax was checked with --help. It is documentation, not an automatically scheduled job. The tool uses the immutable revision, archive SHA256/size and member-manifest SHA256 from BACKUP_MANIFEST.json. It forces a fresh download into a new cache, rejects unsafe paths, symlinks/hardlinks, duplicate/undeclared members and corruption, then verifies every extracted member.

## Fresh-server entry

Obtain the research commit named by the separate final delivery receipt, and read current SESSION_HANDOFF.md/RESUME_MANIFEST.json. Copy CODE/restore4.py and the pinned BACKUP_MANIFEST.json from this attempt. Establish the exact recorded transfer SDK environment and CPU Python3.12.3 with NumPy2.5.4; the saved comparison tool imports no Torch/model/GPU or probe-fitting library. Use existing authorized private-HF authentication without copying credentials into artifacts. Change only the --destination and --cpu-python paths to that server's new owned paths. The restore tool explicitly translates --control, --artifacts, --anchor-root and --report to restored directories, preserving original producer receipts as provenance. No shared Pod B /workspace is assumed.

The CPU check reruns exactly189 saved-array comparison rows: all26hooks plus LM, bidirectional logical/repeat checks, all three R3 historical anchors and actual-logit CE witnesses. It requires identical result JSON and CSV to the producer, zero tolerance violations, the original atol1e-4/rtol1e-5 and no Torch/model forward. This recovers qualification evidence, not production performance, missing R2, or the installed GPU runtime. Raw arrays/training sequences remain private.

For native assets, [checkpoint identities](CHECKPOINT_IDENTITIES.json) and [payload index](PAYLOAD_RECOVERY_INDEX.json) give all eight original relative paths, Drive IDs/revisions, immutable HF revisions, byte sizes and hashes. A future explicitly approved GPU recreation would reacquire only missing exact files from those revisions, preserve native layout and use the [qualified runtime recipe](RUNTIME_REBUILD.md). This stage does not launch such a rebuild after successful qualification.

## Recorded transfer and CPU packages

[TRANSFER_ENVIRONMENT_LOCK.json](TRANSFER_ENVIRONMENT_LOCK.json) records actual transfer-SDK package versions and the exact CPU Python/NumPy interpreter used. The installed GPU runtime remains a separately excluded rebuild dependency.
