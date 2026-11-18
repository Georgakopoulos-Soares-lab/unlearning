Use this verification's [HANDOFF.md](HANDOFF.md) and [receipt](VERIFICATION_RECEIPT.json), then fetch exact preservation commit `60ffbf8cd1d139ba6708df27841111e11ecd8c05` into a fresh repository/directory. Read its [RESTORE_RUNBOOK.md](https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/60ffbf8cd1d139ba6708df27841111e11ecd8c05/docs/experiments/ashay/POD_B/preservation-20261118T093411Z/RESTORE_RUNBOOK.md) completely and use the supplied helper from that commit. Authenticate through an authorized credential store; never print tokens or use signed URLs as durable references.

Download all listed main objects from private dataset `ashay-sriv/undo-evo2-pilot-backup-20261020`, revision `836c443a000948aa4541d667a9e79127cfd8000b`, prefix `POD_B/preservation/20261118T093411Z`. Pin the main manifest SHA256 `d6e886fc27ee80b1fc673c1292ae0c57b3addc1feb8789728553a2a4d5a5c43c` before trusting filenames. Download closure objects separately from revision `65da6cf06c1497cd17396a688b66f4acdff134f0` and verify manifest SHA256 `7799b5e020a39a66a0d35fccae7d840fa769c1c67a5e76fb17ef1ce1fe87b998`. Resolve every older dependency by the receipt's exact revision/path/hash, including its embedded checksum manifest. The optional preparation reference was verified here too.

After pinned downloads, use fresh paths and an existing compatible Python3.11+/zstd installation:

```bash
python -B scripts/sayyed/restore_pod_b_preservation.py \
  --manifest /fresh/download/POD_B/preservation/20261118T093411Z/MANIFEST.json \
  --manifest-sha256 d6e886fc27ee80b1fc673c1292ae0c57b3addc1feb8789728553a2a4d5a5c43c \
  --download-root /fresh/download/POD_B/preservation/20261118T093411Z \
  --output /fresh/verified-pod-b \
  --restore-files
```

Independently hash the materialized files, resolve source coverage and metadata checksums, and retain symlinks as metadata. Account for 194 superseded object versions through the initial manifest rather than treating them as current required files. The closure has 36 payload files plus one embedded self-manifest. Never materialize over an active tree/environment or replay archived controls/launchers. Refer to the exact source snapshots for the additional checks performed here; they are audit provenance, not automatic stage controllers.

A byte restore does not authorize model imports, inference, fits, calibration, biological-outcome decoding, environment upgrades or GPU work. Original runtime/job-state evidence, fresh approval and new valid execution context remain prerequisites. Jupyter revocation is unverified. Retirement/deletion/shutdown require Ashay's own decision; none is triggered by restoration.
