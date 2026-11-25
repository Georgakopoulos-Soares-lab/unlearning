# Validator corrections and independence

The original attempt-001 producer and checker remain immutable. VALIDATOR_TESTS.json records their exact byte hashes and each observed result, including exceptions. Defects were reproduced using synthetic metadata derived from the actual candidate identity registry, never invented collaborator measurements.

The new qualification_v2.py is an explicit scalar-evidence adapter plus uncertainty/reference gate. It keeps source transport, valid numeric point, checkpoint identity, protocol qualification and reference compatibility separate. It is not a blanket replacement for the canonical metric, identity and biological evidence contracts. Current real log records lack the required exact model/cohort/metric metadata and remain unqualified.

Corrections demonstrated in the pinned code:

- Values such as confidence level0,1,-1,2 and nonnumeric/NaN levels were not range-validated. The new interval gate requires a finite0<level<1.
- Empty method/resampling/conditioning strings could pass because the previous check required only non-null values. New fields require meaningful, non-placeholder text.
- List/string/numeric uncertainty objects and nonnumeric bounds could raise exceptions. They now return a localized INVALID_UNCERTAINTY disposition. Nonfinite/reversed/incomplete bounds also remain localized; a finite source point survives without a qualified CI.
- Advertised reference fields could agree with a reference while the actual target task/cohort/split/protocol/readout disagreed. New reference eligibility compares the actual target and reference semantics as well as advertised identity fields. A valid point may remain descriptive while comparison eligibility is false.

47 focused cases cover confidence boundaries, missing/empty metadata, malformed intervals, actual semantic incompatibility, missing point/identity, two duplicate-step source values and invalid source hashes. The real ingestion adapter is exercised with missing model IDs and explicit null/malformed values. A separate independent_v2.py uses Fraction arithmetic and reconstructs the expected gates without importing producer qualification. Forged eligibility mutations are rejected.

Every actual forget-related scalar and every validation scalar passes through this adapter and independent check:28,456 records. Every source scalar is also independently decoded and every emitted full CSV row is reconciled with that decoder,4,069,382 rows. Shared inputs and standard arithmetic/CRC primitives are documented; the independent checks do not reproduce the original training/evaluation, establish missing biological semantics or turn unknown model IDs into proven matches.
