# Stage 1: recovery blocked; preparation implemented

The starter at 0c9867653969ce83533f902b8a99f2527b4d6b36 authorized this worktree/branch and sequential stages. The stage pack/config is pinned consistently to the clean /workspace/repos/test-prompts-push HEAD 162f6a8110e22538634838866bacba12ba753c25. The other prompt clone differs; nothing was checked out/reset or pushed there. Stage 2/3 prompts have not been read. Verbatim inputs and SHA256 receipts are adjacent.

Private HF recovery sidecar download returned HTTP 401 (RepositoryNotFoundError) at the exact requested revision. Securely configure read access to ashay-sriv/undo-evo2-pilot-backup-20261020, then run from this worktree:

```bash
/workspace/venvs/sayyed-base-tools/bin/python -m scripts.sayyed.recover_multiretain \
  --inputs /workspace/meeting-artifacts/multiretain-layers-v1/inputs/effective_session_inputs.json \
  --download-directory /workspace/meeting-artifacts/multiretain-layers-v1/download \
  --destination /workspace/meeting-artifacts/multiretain-layers-v1/recovery-01
```

This verifies revision/download identity, archive size/SHA256/sidecar, safe archive members and all 5914 payload checksums before publishing a recovery receipt. The utility is implemented and CPU-tested for rejection cases; the actual private archive has not been restored here. A failed extraction must be retained and a fresh destination used.

Initial worktree was clean at b5f700ff4f96a305b4c84d12346baccd94a22cdc. Authorized branch experiments-ashay-multiretain-layers-v1; Kimi's worktree untouched. Read-only fetch confirmed access to the research repository. H100 80GB idle, no experiment/transfer jobs observed, 179GB disk available at preflight.

Checkpoint evidence: downloaded base iteration1 config declares 25 blocks/width1920/vocab256. MaxEnt iteration2000 declares 25/1920/512 and explicitly points to H3 retain config/data. Both GradDiff iteration1000 candidates also explicitly point to H3 retain config/data. Folder metadata does not establish shard identity or a multi-retain mixture. Multi-retain arm remains BLOCKED_NOT_IDENTIFIED; no H3 checkpoint was relabeled. No weights downloaded, no new noise arm supplied. Parent confirmation is recorded as a collaborator statement, separately from missing shard-lineage proof. Config hashes and Drive listing evidence are in the artifact root.

Pinned MaxEnt manifests, cached features and fitted heads are absent locally. Existing original-backend H3 data/features are preserved and not substituted. No historical metrics have been newly verified or relabeled as new measurements. Data counts/grouping/hash qualification awaits restoration. No new held-out/test content opened.

A separate all-layer extraction entrypoint extends the historical native route: actual decoder block enumeration plus final_norm, immediate masked pooling, strict backbone/key/dtype checks inherited from the validated route, hash-separated caches and atomic completion receipts. GPU correctness is NOT established here. Remaining smoke requirements include strict loading, tokenizer/mask checks, repeatability, batch-size effects and historical training-anchor comparisons; measure throughput/storage only afterward. Existing two-hook historical scripts remain unchanged. Existing runtime lacks BioNeMo/Megatron/tokenizers and the requested evo2-pilot interpreter is absent; restore the documented isolated runtime after recovery. Do not claim original-backend/BioNeMo equivalence.

Explicit null time limits are supported as uncapped. Effective inputs record the starter authorization overriding the committed 300-second/minute limits; original input bytes are preserved. Session GPU ledger starts at zero for NEW work only. The shared historical ledger is untouched at 868.753177 seconds, whereas the latest completed MaxEnt documentation records 1423.988606. Reconcile verified recovered evidence before GPU execution. New extraction takes both historical lock names and uses the separate session ledger. No automatic shutdown or hardware changes.

PROTOCOL_DRAFT.json is ineligible, not a frozen scientific protocol: missing manifest/checkpoint/runtime identities must be qualified first. It prespecifies all 26 representations, three CV seeds with identical grouped training folds across arms, fold-local scaling, balanced L2 C=.1/1/10, independent refits and fixed-base transfer, all seed outcomes, 2000 paired conditional bootstrap draws, and no invented preservation margin. Kimi's ARTIFACT_CONTRACT.json is published under /workspace/agent-handoff/multiretain-v1; no collaborator message sent.

CPU verification: eight focused tests passed (1.46s pytest wall report) for uncapped/finite/missing authorization, config identity and active-ledger rejection, all-layer indexing and padding/finiteness handling, and unsafe archive paths/link rejection. Initial test caught missing on-disk config rehash; fixed before delivery. Compile and diff whitespace checks also pass. These tests do not validate GPU inference or the actual archive restore.

New GPU usage: 0 seconds. New classifier fits: 0. Provider rental/cost unknown; no billing estimate. No jobs launched or remaining. Local preparation/source can be recovered from this branch plus the separately checksummed artifact package; a new off-Pod scientific backup is not verified because HF authentication failed. Historical backups remain unchanged.

Next eligibility: recover and checksum-verify the archive, run discriminating CPU saved-output verification, reconcile the historical ledger, recover hash-matching shards/tokenizers/runtime, qualify manifests, finalize protocol/source identity, and pass the training-only all-layer smoke. Then automatically read codex_prompt_v2.txt from the SAME pinned stage-pack commit and run the eligible base/H3 fallback; missing optional multi-retain must not block it. Stage 1 is not complete and stages 2/3 must not be advanced falsely.

Delivery: implementation/preparation commit ffc18f555401adac14ec4d9b97f2db96cb7fcf39 pushed and remote head verified. Local preparation-only recovery archive SHA256 69501c8681857eed5b7709e94ed152858236ea18c9ff019372faf37161789f6e, 84980 bytes, all38 packaged payloads verified. See preparation_backup_receipt.json and shared STAGE1_PREPARATION_RECEIPT.json. No new off-Pod artifact transfer verified.

## V25 resume checkpoint

Prompt v25.txt@30f83d1a743b1a98369744509e2f00cf15d5d225 read fully; stage pack remains pinned162f6a8110e22538634838866bacba12ba753c25. Named auth CLI and saved token path absent; supplied credential used via hidden terminal input in process memory, not saved. Exact private revision download succeeded. Archive hash/size and5914 payloads verified into recovery-01. Six data tasks qualified with expected counts, no cross-split exact/RC overlaps or conflicting labels; one within-split splice duplicate group preserved.24 historical scalar metrics independently recomputed. Shared historical ledger reconciled from verified archive to1423.988606s; old ledger copy preserved. New GPU0s. New isolated multiretain-runtime setup and hash-matched checkpoint downloads in progress. Smoke plan/tolerances declared before GPU execution. Multi-retain deferred.

Training-only smoke uncovered native BF16 batch-shape sensitivity. Repeated batch8 outputs exact; base layer16/final_norm historical anchors exact, NLL maxdelta3.05e-5. Batch1 differences exceed original tolerance (late blocks23/24 have scale~9.1e16; normalized max difference~0.0021). Variable physical batch route is ineligible. New separately versioned extract_multiretain_fixed.py enforces physical8, pads filler rows and excludes them from all saved outputs. Original smokes preserved; tolerances unchanged.13 CPU tests passed8.47s. Fixed-physical8 smoke validation remains mandatory before stage2.

## Stage1 complete for authorized base/H3 fallback

Fixed-physical8 smoke PASS:116 comparisons across both models,26 representations, repeats/batch variants and historical training anchors. Stage1 GPU implementation902ed12; finalized receipts/checksums in STAGE1_COMPLETE.json. Frozen protocol SHA256 c65bf5d518ba1a2fdfa5c7f7733cd2596ce6df4e18379e34e545b6278773018a. New GPU-stage usage 80.09750188607723s (includes failed native batch protocol); no new heldout measurements or fits. Main multi-retain comparison deferred, not completed. Stage2 eligible on qualified base/H3 arms. Read codex_prompt_v2.txt only from162f6a8110e22538634838866bacba12ba753c25; stage3 not yet eligible. Source/runtime/data/checkpoint receipt paths and resource estimates are adjacent.
