# A06 acceptance reconciliation

A06 computation is accepted from the pinned handoff. Its original PAIRED_CONTRASTS.csv fails its declared schema because lineage is missing. The immutable original and every original field/value/key/order remain unchanged. The owned normalized v1 copy adds measurement lineage NEW (relative to A06 production), ingestion REUSED_IN_A07 and evidence-derived receipt provenance. Base/R1/control measurements remain REUSED. This repair does not recompute or change probabilities, estimates, intervals, validity counts, unresolved comparisons or training lineage.

All 6,776 original rows and keys were compared field-for-field in order. A04 remains PARTIAL; R2/R5 and R3 bridge gaps remain. See A06_REPORT_SCHEMA_REPAIR.json for source/output digests and mapping.
