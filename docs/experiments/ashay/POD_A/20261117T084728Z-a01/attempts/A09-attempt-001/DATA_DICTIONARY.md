# Data dictionary and table navigation

## Complete logical evidence

TABLE_INDEX.json pins every physical table by source commit, row count and digest. The logical classifier paired table is the union of four partitions: main A07 16,800 rows; H3 6,720; historical 16,380; new nonadjacent R6−R4 5,460, totaling 45,360 unique scientific keys. A09 uses a lossless H3 canonical-ID derivative; the other three are immutable A08 references. No combined export is needed and no partition is omitted. VERIFIED_METRICS has 27,300 rows; controls 210; primary LM points/paired tables 70/112. All 6,637 coverage keys and explicit 27,300 classifier/70 LM missing-edge keys are retained.

## Keys, types and missingness

Classifier key: original endpoint ID, task, split, canonical representation, CV seed, policy, metric and protocol hash. A paired row adds original reference ID and reference policy. Endpoint aliases never replace content/prediction identity. Controls have no representation axis; task/split/seed/control kind plus exact serialized-head and prediction-file digests disambiguate the alias. LM representation and CV seed are null; its primary unit is checkpoint/task/split, not metric or layer. H3 `test_exploratory` maps to original exposed `test`; dev/test are separate.

CSV empty means JSON null. Estimates/intervals retain full source precision. Row/group/token and resample counts are integers or explicitly unknown. Missing/blocked estimates remain null with a reason; unknown is not zero. Historical marginal CIs absent from source reports remain null with ci_missing_reason; paired CIs remain valid. Higher AUROC/AP/accuracy/balanced accuracy is favorable; lower classifier cross-entropy, causal NLL and perplexity is favorable. Delta direction is target−reference.

## Measurement origin and release

measurement_attempt/lineage describe the original measurement. ingestion_status and A09_ingestion_status describe later reuse; neither establishes checkpoint ancestry. A08 release overlays preserve original producer COMPLETE_UNVERIFIED seals. AUDIT_SCOPE_MATRIX is an immutable pre-execution plan; AUDIT_RELEASE_STATUS is the exact 780-unit current join. Only 60 units required fresh audit refits. All-member archive hashing and sampled restored computation are separate columns.

## Typed hash objects

Classifier prediction_sha256 binds an immutable NPZ file, with the full row key selecting policy/class columns. Current LM hashes bind saved float32 loss/count sufficient-statistics files. Historical LM hashes can bind FEATURE_UNIT_COMPLETE.json, which seals the feature/LM chunks; prediction_locator includes task/split/arm selectors. These are different object types, not interchangeable probability arrays. source_prediction_sha256 retains earlier export pointers where provenance normalization occurred. Original producer/audit/source/draw hashes and locators are preserved.

Control `control-head-sha256:` IDs bind serialized head-file bytes, not tensor/parameter-content identity. `control:composition` and `control:kmer4` are family aliases; they require the full identity tuple. ENDPOINT_ALIAS_MAP records all 480 affected H3 contrast keys, exact head/prediction digests and source identities. PAIRED_CONTRASTS.H3_canonical.v1 retains original_reference_endpoint_id/type, every original numeric/origin field, row order and source hash. Name-only or conflicting joins fail closed.

## Descriptive policies and plot uses

POLICY_POINT_DIFFERENCES contains refit-minus-fixed point summaries with null intervals; no extra inferential family was introduced. Plot-data record IDs identify rendering uses, not new fits: a shared control can occur in both readout panels. Seed spread is not a CI. Layer16 is the 17th block; final norm is a separate hook. R3 remains historical-domain-only and R6−R4 is nonadjacent. Consult RESULTS.md and METHODS_AND_LIMITS.md before interpreting comparisons.

REPORT_ANCHORS_FULL_PRECISION.csv supplements rounded Markdown displays. CLAIMS_TO_EVIDENCE.csv records exact original keys, hashes, status, source commit, measurement origin, uncertainty and limits for every reported scientific row. COUNT_EVIDENCE.json and CLAIM_SCOPE_INDEX.json separately bind coverage/protocol/audit/seed-count statements. No presentation-derived value is a new scientific measurement.
