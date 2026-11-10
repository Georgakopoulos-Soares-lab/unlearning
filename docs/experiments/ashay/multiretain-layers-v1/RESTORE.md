# Recovery order

Use the final Git `backup_receipt.json` for the immutable private dataset revision, archive/sidecar paths, bytes, SHA256 and payload count. That receipt is written after packaging; an older receipt does not cover this run. Authenticate privately through an HF credential store or hidden input; never paste a key into command arguments, reports or source.

1. Download both recorded files from `ashay-sriv/undo-evo2-pilot-backup-20261020`, repo type `dataset`, at the receipt's exact revision, into a fresh directory. Use `hf_hub_download(..., revision=receipt['remote_revision'], force_download=True)` for each path with your securely configured authentication. Keep stale `HF_TOKEN` / `HUGGING_FACE_HUB_TOKEN` overrides absent when using a credential store.
2. Check archive byte size and SHA256 against the trusted Git receipt, and run `sha256sum --check ARCHIVE.tar.gz.sha256` from the download directory. The producer verified the exact archive contains only regular files/directories, one declared root, no links/traversal/duplicates, with complete relative checksum coverage. Do not extract a different or unverified archive.
3. Choose a new, empty extraction directory; run `tar --extract --gzip --file ARCHIVE.tar.gz --directory FRESH_DIRECTORY --no-same-owner`. From the extracted payload root run `sha256sum --check CHECKSUMS.sha256`. Never restore over a historical run. Preserve original absolute paths inside receipts; the verifier remaps them.
4. For CPU audit, create a separate Python 3.12 environment with numpy 2.5.4, scipy 1.18.1, scikit-learn 1.7.2, joblib 1.5.2 and threadpoolctl 3.8.0. Source is under `PAYLOAD/source`; set `PYTHONPATH=PAYLOAD/source`. Run, separately for `H3` and `other_five`:

   ```bash
   python -m scripts.sayyed.verify_multiretain_units \
     --run PAYLOAD --original-root /workspace/meeting-artifacts/multiretain-layers-v1 \
     --group H3 --threads 4 --output NEW_AUDIT_DIRECTORY
   ```

   Use a fresh audit directory and `--group other_five` for the other group. All saved features, heads, predictions, folds, selection traces, LM sums/counts and bootstrap draws required by this CPU check are included. The new scientific payload does not depend on the old recovery archive for those checks. Only load joblib files after their trusted archive/payload hashes pass.
5. GPU regeneration additionally needs excluded model shards and a rebuilt runtime. Exact Drive file IDs, sizes and SHA256s are in `base_download_receipt.json` (128 shards) and `maxent_download_receipt.json` (one shard), using shared folder `1pM5-kFeki5Oq1oLjQNXH0U2f2TlGNuzi`. Small configs/tokenizers/.metadata are included under `checkpoint-assets`. Use the pinned qualified registry and extraction identities, not an arbitrary folder match. Reconstruct the isolated BioNeMo/Bridge/Megatron/Torch/TE route from `runtime_environment_lock.txt` and logs, including its documented dependency exception. Run the training-only fixed-physical-8 smoke before any new inference; a fresh protocol/cache identity is required if inputs change.

The package is standalone for the new CPU saved-output scientific audit, not an offline GPU environment. Original historical source results, model weights and installed environments are excluded. The independently verified old archive (revision `0713f0906803e49911b33024b8411dbe012c1478`, SHA256 `94e7e86f007fa6b317a433d4be0e402819f7fc5e834c92dc804e00c73edf6d46`) is optional historical context, not a prerequisite for the new saved-output audit. Package hashes establish byte identity; they do not independently reproduce GPU extraction.
