# Restoring the project backup

Use the exact immutable revisions and SHA256 identities in PRIVATE_BACKUP_RECOVERY.json. The restricted object paths and complete source-to-recovery index are held in the private closing capsule and the local BACKUP/attempt-001 control directory. Authentication credentials are intentionally excluded.

Download both archive and manifest from the authorized private Hugging Face destination at the recorded commit. Check their full sizes and SHA256. Restore into an empty directory; reject unsafe names, links, duplicates, undeclared members, oversized members and any missing or mismatched member hash. The private RECOVERY_GUIDE.md and protect_new.py provide the byte-verification procedure and source-root mapping. Do not execute recovered code automatically.

FILE_RECOVERY_COVERAGE_v2.jsonl identifies every inventoried regular file, including inherited members and native objects at existing immutable revisions. Existing payloads retain their earlier restoration proofs and received fresh provider metadata checks; their complete bodies were not restored again in this backup pass. New snapshots received fresh uncached HTTP downloads and every member was checked against its SHA256. A complete research Git bundle, prompt Git bundle and final incremental research bundle preserve repository history without changing historical branches.

Environment/cache subtrees and repeated recovery consumers are explicit reconstruction/redundancy boundaries. Link metadata is preserved without traversal. This is project-recovery protection, not a live disk image. Existing scientific limitations and pending external evidence remain unchanged.
