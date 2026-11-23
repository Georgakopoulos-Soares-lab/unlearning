# S00: Initialize the pinned controller

## Entry guard and authorization

Read [S_START_HERE.md](S_START_HERE.md), [S_SCIENTIFIC_CONTRACT.md](S_SCIENTIFIC_CONTRACT.md) and [S_ARTIFACT_CONTRACT.md](S_ARTIFACT_CONTRACT.md) from the approved immutable prompt commit. Check [S_STAGE_MAP.json](S_STAGE_MAP.json) and [S_RESULT_SCHEMAS.json](S_RESULT_SCHEMAS.json). Package publication or a completed previous phase is not approval. Require a new direct chat approval for this exact phase and package commit, record its text/time/scope, and run the non-executing validator entry guard before any work.

Research origin must be https://github.com/Georgakopoulos-Soares-lab/unlearning.git, branch POD_A_SALIENCY only, in /workspace/pod-a-saliency/research-POD_A_SALIENCY. Fixed predecessor is 8c651c7ab3c3a2a47f5bbd0e464a69a197512c82; never silently update/rebase it. Write only docs/experiments/ashay/POD_A_SALIENCY/<run-id>/ in research; preserve POD_A, historical attempts and Pod B. No force push. Package/source identities stay pinned during work.

## Failure handling, recovery and stop

Use finite frozen units, one writer per identity, atomic writes and checksum-last receipts. Distinguish unresolved from false/zero. Persist partial failures and their exact affected units; continue independent eligible scopes only. A nonzero process exit cannot be rewritten as success; unknown child exits remain null with evidence. Seal/resume valid units without repeating finished forwards/fits. Source/protocol fixes create versioned identities; do not relax numeric gates after outcomes.

Maintain run PROGRESS.md, append-only EVENTS.jsonl and phase receipt. Report requested/new/reused/failed/verified units, scientific coverage, backup and external dependencies separately. Before phase closure drain owned work, verify PID/start identity and exits, checkpoint newly costly outputs privately and publish only sanitized owned paths. Bounded metadata/network operations use45s timeouts and local checks15s with before/after progress; one diagnosed transient retry only, no indefinite polling. Long approved transfers/compute have stage-specific heartbeats, resource guards and finite queues, not a45s blanket kill. No deadline/cutoff/reserve or ten-minute science cap applies. No purchases/resizing/shutdown, stage watchers or collaborator messages. Stop at this phase boundary and request the next specific phase approval; do not execute it.

## Prerequisites and unresolved inputs

Bootstrap authority is the direct package-build/S00 chat instruction; no previous scientific phase is required.
Required resolved input keys: package_publication, research_base_binding. Future unknowns resolve in their assigned phases in S_STAGE_MAP.json; they are not fictitious candidates. PARTIAL predecessors admit only their explicitly eligible passing scope; no global success inference.

## Permitted procedure

1. Verify the published package from immutable Git blobs with S_validate_package.py. Pin the actual 40-character package commit, S00 file digest and S_SHA256SUMS digest, fixed research base, run ID and owned paths. Never use the moving branch as stage authority.

2. Reuse setup records and supported Drive listing evidence. No new Drive inventory or checkpoint metadata retrieval here. Set candidate identities/counts and science expectations to null, completed scientific units to zero, and all S01–S11 approvals to false.

3. Persist the direct bootstrap chat instruction and its immutable instruction-file receipt as S00 authority. Record that it authorizes package publication and S00 only. Supersede historical R2 gaps prospectively and preserve no-deadline policy; leave old reports unchanged.

4. Seal sanitized records, review the exact owned-path diff, commit and push only the active research branch by normal fast-forward. Verify every committed file against local bytes and live remote reachability. Keep the final commit receipt outside its own commit to avoid self-reference.

## Exact outputs

Under the owned run root, use S00/attempt-<unique-id>/ for these files:

- `CONTROLLER_STATE.json`
- `SCOPE_AMENDMENT.json`
- `SOURCE_BINDING.json`
- `APPROVAL_RECORD.json`
- `EXTERNAL_DEPENDENCIES.json`
- `SESSION_HANDOFF.md`
- `S01_HANDOFF.md`
- `PROGRESS.md`
- `EVENTS.jsonl`
- `S00_RECEIPT.json`
- `OUTPUT_SHA256SUMS`

S00 additionally maintains the root controller/handoff/progress entrypoints. A new record is metadata, never scientific evidence.

## Acceptance checks

- Package readback passes and actual publication commit is bound; branch/base guard passes.
- Controller fields, scope, sources and dependencies are explicit; S01 is ready for approval only.
- No models, datasets, external forget examples, GPU jobs, stage dispatchers or collaborator messages.
- Research commit and remote delivery are verified, not inferred from a successful local commit.

## Boundary and next dependency

Next is S01, under a separate direct approval after its required inputs pass. This prompt file is a specification, not standing execution authority. R2 is excluded; no raw forget data, new interventions, checkpoint training or Pod B relearning.
