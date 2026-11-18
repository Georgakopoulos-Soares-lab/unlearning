# A04-attempt-004 qualification handoff

| Endpoint | Payload identity/integrity | Strict loading, hooks and LM | Numerical / historical bridge | New evidence recovery |
|---|---|---|---|---|
| R3 selected iteration2151 | PASS, historical native digest matches | PASS, three variants | 135/135 rows PASS, including81 historical rows | PASS:387members + fresh189rowCPUrecovery |
| R5 selected iteration2000 | PASS, fresh provider-bound digest | PASS, three variants | 54/54 self-comparison rows PASS | PASS:387members + fresh189rowCPUrecovery |
| base/R1/R4/R6 | Preserved | 12variants/378rows REUSED_VALIDATED | Original source identities retained | Prior proof reused |
| R2 | Unidentified; discovery excluded | 3variants pending | 54rows pending | External delivery/admission |

This new A04 scope has passed its numerical work; overall A04/full project remain PARTIAL. No later stage is started. Source and environment are unchanged. New comparison maxima are R3 `1.52587890625e-05` and R5 `6.103515625e-05`; every coordinate passes both directions at atol1e-4/rtol1e-5, with zero violations. The189rows cover4193280feature coordinates and84LMvalues; 12 unique TRAINING rows are used across six fresh processes. All254model tensors/1108319488elements per model and the trained tied512-column output head are checked. Exact typed empty metadata remains distinct from learned parameters.

[Numerical results](SMOKE_RESULTS.json), [comparison rows](SMOKE_COMPARISONS.csv), [qualifications](QUALIFICATION_MATRIX.csv), [strict loading](LOADING_REPORT.json), [metadata](NATIVE_METADATA_AUDIT.json), [LM](LM_QUALIFICATION.json), [resources](RESOURCE_CALIBRATION.json), [payload recovery](PAYLOAD_RECOVERY_INDEX.json) and [new evidence backup](BACKUP_VERIFICATION.json) retain separate statuses. Fresh private evidence recovery has passed and the qualified-subset proposal is protected. Immutable mirrored weights are referenced without redundant large archives.

[A05 requirements](A05_REQUIREMENTS.md), [proposal](A05_PROPOSAL.json), [remaining gaps](MISSING_INPUTS_DRAFT.md) and [future comparison readiness](COMPARISON_READINESS.csv) exclude completed work. Original A09 release remains [historical](../A09-attempt-001/SESSION_HANDOFF.md), with no changed production score or uncertainty family. R2, parent/objective/exposure and source-label gaps remain explicit. No observer/scheduler restart, purchase or shutdown occurs. Unknown original/rental start, rate and cost remain null; no deadline or reserve is recreated.

## Protected handoff

Qualification commit `906e808af4b61eeb7f8b229fea30e735f1cf818f`. Private evidence revision `5c4fd12f1df0fc96a056e2bad8d83b34822a6bff`, archive SHA256 `1286c91b9e941b395f9a1c5d189e733c755e8407dd0da19e448602a9d4ece565`; all `387` members passed and restored 189-row JSON/CSV equal the producer exactly. The native R3/R5 mirrors remain separately pinned, with original-byte verification and no redundant large archive. Model weights and installed runtime binaries are excluded from this bounded evidence archive; full GPU rebuilding was not tested.

A05_PROPOSAL.json SHA256 `27cbc1fddf44b0682d1245b722649c21b6f0a9cffbcd3b7be6edd123f25d5d8d`. Overall A04 and the full experiment remain PARTIAL because R2 is unresolved; the explicitly accepted R3/R5 scope is COMPLETE. Owned scientific/transfer/recovery workers exited and locks are available; the observer stays STOPPED. The Pod remains running. Final Git metadata and separate private delivery proof are published afterward without a self-hash cycle.

WAITING_FOR_APPROVAL: A05
