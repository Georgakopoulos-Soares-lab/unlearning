Restore the existing base/H3 archive first, controls second, and the new scientific supplement third into separate empty directories. Exact prior archive revisions, byte counts and SHA256 values are in [RESTORE_DEPENDENCIES.json](RESTORE_DEPENDENCIES.json); the sealed supplement also contains RESTORE_DEPENDENCIES.json. The final new archive identity and successful fresh-download receipt are in [BACKUP_VERIFICATION.json](BACKUP_VERIFICATION.json). This is dependent recovery, not a standalone three-arm archive.

For each download pin the dataset repository revision, verify its recorded size and SHA256 plus sidecar before extraction. Reject absolute paths, traversal, duplicate members, links and non-file/non-directory entries. Extract into a fresh empty directory. Verify every relative CHECKSUMS.sha256 entry and require exact file coverage (plus CHECKSUMS.sha256 itself). Never overwrite historical runs. Existing private authentication is required; never put credentials in command arguments, logs or saved scripts.

The supplement includes new pooled features, per-sequence LM sums/target counts, heads/scalers/CV/folds, predictions, bootstrap artifacts, exact cohort manifests, audits, tables/plots, configuration/state/tokenizer descriptors and source. It excludes all model weight shards, installed runtime and unchanged prior large caches. For GPU regeneration, reacquire the selected new shard using CHECKPOINT_DOWNLOAD.json's Drive ID, exact bytes and SHA256; verify against the recorded trusted digest. Recreate the pinned native Evo2/BioNeMo/Bridge/Megatron environment from runtime_environment_lock.txt and the original runtime policy; preserve fixed physical batches8, BF16/FP32/unfused attention and strict loader exceptions. CPU saved-output reconstruction needs the recorded numpy2.5.4/scipy1.18.1/sklearn1.7.2/joblib1.5.2 versions, not GPU weights.

The fresh restored-output smoke uses only the newly restored supplement and the two separately restored dependencies. Run with bytecode disabled to preserve verified payload checksums:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 python -B NEW/check_restored_outputs.py --new NEW --reference OLD --controls CONTROLS --output /fresh-audit/restored-smoke.json
```

Replace NEW/OLD/CONTROLS with the extracted payload roots and create the output directory outside those roots. This checks H3 binary and splice multiclass first12 dev rows at layer0/seed42, reconstructs new-refit/new-fixed-base/base probabilities and joins controls. It supplements the complete pre-transfer468-unit audit and full post-download payload hashes; it does not claim independent GPU regeneration or repeat all CV fits.

The full independent saved-output audit can be rerun if needed, writing outside the verified payload:

```bash
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=NEW/source python -B -m scripts.sayyed.verify_multiretain_new_arm --run NEW --original-root /workspace/meeting-artifacts/multiretain-comparison-v1 --reference-run OLD --group H3 --threads 4 --output /fresh-audit/H3
```

Repeat with group other_five. Absolute original producer paths are remapped through --original-root/--reference-run. Reusing immutable old archives is required for base-feature/head verification. The packaged source commit records the scientific delivery snapshot; final backup and restored-smoke receipts necessarily postdate the archive and are preserved in Git. Do not regenerate plots in verified payload directories without first copying to a working directory.
