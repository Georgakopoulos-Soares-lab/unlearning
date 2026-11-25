# S10 corrective evidence package

Start with S10_CORRECTION_REPORT.md, COVERAGE.json and S11_HANDOFF.json. This attempt corrects the previous no-source assessment; it does not rewrite historical attempts or change the frozen retain release.

| Need | Exact artifact |
|---|---|
| Source identities, full private scalar-table hashes and null reasons | SOURCE_LOG_INVENTORY.json |
| Full-precision public loss-related scalar records | scalars/*.relevant.csv |
| Every original tag and its count | SOURCE_TAG_COUNTS.csv |
| Forget validation loss/ppl across both original axes | FORGET_VALIDATION_OBSERVATIONS.csv |
| All validation scalar families | ALL_VALIDATION_OBSERVATIONS.csv |
| Individual decisions and shared explicit missing-metadata profile | QUALIFICATION_LEDGER.csv and QUALIFICATION_PROFILES.json |
| Candidate-to-log associations, never inferred exact joins | CHECKPOINT_BINDING_MATRIX.csv |
| Evaluation effort and comparability | EVALUATION_COMPARABILITY_MATRIX.csv and CONFIG_EVALUATION_FACTS.json |
| Duplicate observations, source runs and alternate axes | DUPLICATE_AND_RESTART_REGISTER.csv, SOURCE_RUN_SUMMARY.csv, ALTERNATE_AXIS_EQUIVALENCE.csv |
| Semantic limits and loss/ppl arithmetic checks | METRIC_SEMANTICS.md and PPL_CONSISTENCY.csv |
| Source-only trace figure | figures/SOURCE_LOG_TRACES.png, .svg and .pdf; FIGURE_MANIFEST.json |
| Defects reproduced and independently checked | VALIDATOR_CORRECTIONS.md, VALIDATOR_TESTS.json, REAL_INGESTION_INDEPENDENT_CHECKS.json and FULL_TABLE_INDEPENDENT_VALIDATION.json |
| Earlier assessment correction | EARLIER_STAGE_IMPACT_REVIEW.md and EARLIER_STAGE_EVIDENCE.json |
| Missing inputs without contact | PENDING_FORGET_INPUTS.json and UNSENT_COLLABORATOR_REQUEST.md |
| Canonical S10 output mappings | COLLABORATOR_FORGET_INPUTS.json, EXACT_JOIN_ELIGIBILITY.json, RETAIN_FORGET_VIEWS.json, INTEGRATION_LIMITS.md, S10_RECEIPT.json |
| Immutable private original source and regeneration proof | PRIVATE_RECOVERY_PROOF.json and RESTORE.md; exact restricted locator retained in control |
| Delivery and continuation | DELIVERY_CONTEXT.json, RESUME_MANIFEST.json, S11_HANDOFF.json; final future commit proof external to its own commit |

All full original scalar tables reside privately in the exact recovery member set; public projections exclude unrelated system/parameter diagnostic bulk while retaining all loss-related scalars and every validation observation. The source inventory gives each full table's filename, SHA256 and byte size. No source event binary, model payload, raw dataset, feature/head/probability payload, credential or private repository locator is published.
