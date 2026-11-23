# Proposed package amendment — review only, not published

Base package commit: `558592c1985ed180745599709595c543476644f7`. Proposed version1.1.0. Exact patch: `PROPOSED_PACKAGE_AMENDMENT.patch`, SHA256 `0a9054f33ca257156352ef9422dc1d6d2512eac369f7258299bca89a15aa61f6`. The isolated draft package digest is `3b089d6b7d7ab16812272a500519db269050c855f0a0f29e3333752d9a62a5e9`; this is a computed review-copy digest, not a published commit or new execution authority. Future publication commit remains null.

| Correction | Affected files | Intended behavior | Minimum acceptance | Latest safe implementation |
| --- | --- | --- | --- | --- |
| 1. Original-base heads | S03, S04, S05, S07 prompts; S_STAGE_MAP.json; S_validate_package.py; controller schema | Recovered/qualified in S03, exact reuse seals in S04, mandatory affected S05 entry, unchanged S07 reuse | S05 must reject absent/unscoped original-base references | Before S05, bind by S04 closure |
| 2. Initial panel/contrasts | S04, S05, S08, S09 prompts; S_STAGE_MAP.json; validator; controller schema | Initial full/H3 audit and contrast keys freeze in S04 before producer outcomes; later phases verify original receipt-bound seals | Reject S04 closure missing freeze, missing H3 subset, altered late panel/family or mismatched S04 receipt | S04 closure, before S05 |
| 3. Provider evidence | S_RESULT_SCHEMAS.json; S_validate_package.py; S_ARTIFACT_CONTRACT.md | Add remote_evidence separately from Git evidence, honest null reasons and declared/local checksum semantics | Reject missing revision null reason or a provider checksum claiming local verification | Preserve S01/S02 local schemas now; publish before affected new package use |
| 4. Route/readback separation | S03 prompt; S_STAGE_MAP.json; validator; artifact contract; controller schema | S03 entry needs backup_route_identified only; substantial_compute action needs private_write_readback_verified | Route-only entry passes; substantial compute without roundtrip fails; no S02 upload | Before S03 begins |
| 5. Concrete resumption | S_START_HERE.md; S_ARTIFACT_CONTRACT.md; S03 prompt; validator; controller schema | S03+ entry requires run/phase/attempt/prompt pins, seals, unfinished/transfer totals, owned PID/start/boot identity, decisions, next action and single-writer reconciliation | Reject missing/stale resume binding; exact process identity and sealed-unit reuse remain operator duties | Throughout S02 now; before every later entry/checkpoint/handoff |

The active package already contains much of the right scientific prose; this amendment makes prerequisite timing and guard representation explicit. It preserves all scientific goals, phase boundaries, no-deadline policy, R2 exclusion, S01 PARTIAL status, both readouts and historical scope. It does not authorize any scientific work.

Exact changed files:
- `S03_RECOVERY_RUNTIME_QUALIFICATION.md`
- `S04_PROTOCOL_COVERAGE_FREEZE.md`
- `S05_H3_EXTRACTION_PROBE_GATE.md`
- `S07_REMAINING_PROBES_FIXED_BASE.md`
- `S08_INDEPENDENT_VERIFICATION.md`
- `S09_LAYERWISE_SWEEP_ANALYSIS.md`
- `S_ARTIFACT_CONTRACT.md`
- `S_RESULT_SCHEMAS.json`
- `S_SOURCE_PROVENANCE.json`
- `S_STAGE_MAP.json`
- `S_START_HERE.md`
- `S_support/CONTROLLER_STATE.schema.json`
- `S_validate_package.py`
- `S_PACKAGE_FILES.json`
- `S_SHA256SUMS`

Validation completed in an isolated small-file copy: package checksum/manifest/schema/graph/link validation and existing synthetic self-tests pass. The exact patch passes git apply --check and produces bytes equal to the full isolated draft. Focused tests in PROPOSED_AMENDMENT_VALIDATION.json cover route-only entry, roundtrip gate, original heads, H3 panel, S04 receipt/panel tampering, null provider revision/origin and resume reconciliation. No prompt checkout/branch was edited.

Safe publication procedure after explicit authorization: verify remote canonical branch ancestry and preserve intervening work; apply this reviewed patch to a separate publication worktree at the approved package; inspect exact S namespace; validate again; regenerate S_SHA256SUMS if any content changes; ordinary fast-forward commit/push; read back every package blob at the actual immutable commit; then explicitly migrate schema/controller bindings to that pin with a migration receipt and obtain direct scoped S03 approval at the real pin. Do not silently migrate the running S02 state or claim this proposal implemented.

A guard is a non-dispatching consistency check, not an execution sandbox or proof that recorded chat/freeze claims are authentic. Operator must match actual direct approval, source-bound qualification and pre-outcome artifacts. S04 close checks a locally sealed candidate receipt before accepting/publishing closure. Later exact seals preserve its original panel/family rather than selecting after outcomes.

S02 completion is independent from S03 readiness. Current package/backup guard amendment remains the concrete administrative blocker to S03 entry. Additional parent/timing/seed/exposure questions constrain specific comparisons; candidate-only recovery of all nine is already conditionally selected and need not wait for every causal question.

Review revision2 additionally requires private_roundtrip_binding and verifies the actual receipt bytes/hash, private destination, fresh download, matching payload digests/sizes, immutable revision/route and unique current-run S03 prefix. A resolved status string alone does not satisfy that proof gate. Prior review bytes/tests are preserved privately.
