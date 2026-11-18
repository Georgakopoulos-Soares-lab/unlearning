Preservation attempt `preservation-20261118T093411Z`. Research entry `6b4c927a845e73f62bd1f38fcb19bad773352c5b`. Prompt `8d7647bc2bef18f4f369ac76905b99e62abb2d0f:Preserve, document, and back up.md`, SHA256 `8917b3a037eb399329094c8570ef552f95374043210fa8a9c10478fcb0602817`. Status **PRESERVATION_COMPLETE_PENDING_INDEPENDENT_VERIFICATION**.

This is Pod B's preservation entry point. It records completed work and preserves evidence for a separately approved future session. It grants no execution, retirement or shutdown authority.

Read in this order:

1. [CURRENT_STATE.md](CURRENT_STATE.md) — science versus engineering versus parameter analysis.
2. [HANDOFF.md](HANDOFF.md) and [OPEN_DEPENDENCIES.md](OPEN_DEPENDENCIES.md) — exact stop/resume boundary.
3. [RESULTS_AND_CLAIMS.md](RESULTS_AND_CLAIMS.md) — supported results and interpretation limits.
4. [SESSION_HISTORY.md](SESSION_HISTORY.md) and [LOG_INDEX.md](LOG_INDEX.md) — available history, sanitized visible records and omissions.
5. [RECOVERY_INVENTORY.json](RECOVERY_INVENTORY.json), [BACKUP_MANIFEST.json](BACKUP_MANIFEST.json) and [RECOVERY_COVERAGE.md](RECOVERY_COVERAGE.md) — new and inherited coverage, exclusions and verification.
6. [ENVIRONMENT_AND_REPRODUCTION.md](ENVIRONMENT_AND_REPRODUCTION.md) and [RESTORE_RUNBOOK.md](RESTORE_RUNBOOK.md) — byte restoration without model execution.
7. [RESOURCE_AND_APPROVAL_HISTORY.md](RESOURCE_AND_APPROVAL_HISTORY.md) and [VALIDATION.json](VALIDATION.json) — preserved budgets, approval and checks.

Only research POD_B is writable. The prompts repository and every other branch/worktree remain read-only. Legacy controls and historical PASS values remain unchanged. No automatic resume, experiment, stage queue or shutdown exists. Token remediation is a separate operator action; no revocation is evidenced.

Initial pinned readback passed at HF revision `836c443a000948aa4541d667a9e79127cfd8000b`. Ten payload parts plus metadata/MANIFEST were freshly downloaded: 25,842,127,952 compressed bytes. All 35,849 objects were byte-hashed; 74,029 regular files and 43 symlink metadata records verified. Multi-chunk files were streamed in order for full-file hashing; one-chunk files bind directly to verified object hashes. Four key B04/B05 evidence files were separately materialized. This is initial executor verification,not independent verification or runtime/model qualification.

Closure supplement: revision `65da6cf06c1497cd17396a688b66f4acdff134f0`, `POD_B/preservation/20261118T093411Z/closure-metadata.tar.zst`, SHA256 `d8044fe3723697848cf64a3e454dfe2837031c38e3ae4d6885ec0f7f7f4051ab`; 36 metadata files passed fresh readback. It preserves the final documentation/private closure records,sanitized visible-session tail and read-only prompt-clone state. The primary data remains pinned at `836c443a000948aa4541d667a9e79127cfd8000b`. Final Git publication/verification is recorded externally afterward.
