# Source provenance and execution boundary

These are the exact S05 numerical sources sealed before outcomes by SOURCE_IDENTITY.json and exercised by READINESS_TEST_REPORT.json. The active private RUN_CONFIG and READINESS receipts, direct phase approval and frozen S04 cohort/protocol bindings are mandatory dispatch inputs.

Use s05_gpu.py only for the approved H3 TRAIN/dev extraction, s05_cpu.py for the frozen producer/audit/LM units, and s05_verify.py for independent reconstruction. Their scope checks reject test/other-task dispatch. A later S06 implementation must keep this H3 source immutable and introduce its own approved, source-bound adapter around the qualified functions.

historical_h3_followup_SOURCE_ONLY.py is verbatim historical provenance, not an executable entry point for this workflow. Its original main includes test access and must never be invoked or imported here. inherited_fit.py contains only the recovered safe estimator functions; the S05 adapter does not call that historical main.

GPU, producer, auditor and verifier identities are separate. Changed numerical source needs a new immutable execution identity and an explicit affected-unit map; do not silently rebind existing results. Administrative transfer/supervision repairs remain separately recorded and do not replace the pinned numerical sources.
