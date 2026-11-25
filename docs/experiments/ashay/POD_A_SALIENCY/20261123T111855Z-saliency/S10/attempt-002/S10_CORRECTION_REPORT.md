# Corrective S10: existing forget-related log evidence

The supplied delivery contains forget-related scalar measurements. The previous S10 attempt admitted none and incorrectly described its bounded source scope as containing no supplied aggregate. This correction preserves that historical assessment and replaces its current reporting scope. It does not change S00–S09 results or complete the original layerwise retain-and-forget request.

## What was recovered

All nine exact event-file IDs were available through authenticated Google Drive reads. Their full 418,914,867 bytes match the stated snapshot sizes. Each locally computed SHA256, original filename, exact source locator and nullable provider fields is recorded in SOURCE_LOG_INVENTORY.json. The connector did not supply immutable revisions or provider checksums; neither was fabricated. The nine known files are exhausted; the broader original delivery inventory remains PARTIAL.

There are 4,069,391 complete TFRecord events, including nine non-scalar writer-metadata events, and 4,069,382 scalar observations. Every length boundary, length CRC and payload CRC passed. A maintained TensorBoard reader and an independent protobuf wire decoder agreed exactly on all scalar tags, values, steps, wall times and event/value orders. A separate full CSV roundtrip checked all 4,069,382 emitted rows against the independent source digest, with zero nonfinite values. No truncated record or unsupported scalar payload occurred.

The logs contain 14,090 step-axis training observations tagged `forget loss`, 23 step-axis observations tagged `forget loss validation`, and 23 corresponding step-axis `forget loss validation ppl` values. The sample-axis counterparts reproduce the same values; these are alternate axes, not additional independent measurements. Across all loss families there are 276 validation scalar records. QUALIFICATION_LEDGER.csv records 28,456 individual forget-related and all validation decisions, joined by source-hash/event/value identity. The remaining scalar diagnostics inherit the explicit unqualified source profile, with every tag/count and original scalar row retained.

All original full-precision scalar records are protected privately in nine compressed CSVs, indexed by exact size/hash. Public scalars/ holds full-precision loss-related projections, including retain/maxent and alternate axes. FORGET_VALIDATION_OBSERVATIONS.csv contains all 92 forget validation loss/ppl records across both axes; it does not count them as 92 independent evaluations. Original tags are preserved, and no value is replaced by zero or chosen by last-observation policy.

## Ambiguities preserved

Reinit-5% A contains two distinct `forget loss validation` observations at step1500: **1.3953843116760254** and **1.3952388763427734**. Their corresponding logged ppl values are **4.036525726318359** and **4.035938739776611**. Both original event orders are retained. Across the three validation loss families, ppl and alternate axes, this produces 12 duplicate-tag/axis-position observations. There is one duplicate in the primary step-axis forget-validation series; its23 records occupy22 unique source/step pairs. Duplicate validation does not itself establish a restart. No tag's axis position decreased within a file, and no session-log restart marker was found; this does not rule out an unlogged restart or extra invocation.

Reinit-5% B has training observations only through step1439 and validations at500/1000. Its relationship to A and the delivered step1500 tensors remains unresolved. Noise-5% has distinct validation observations at2000 and2151 in one source file; the two delivered checkpoint identities remain distinct endpoints and are not independent seeds. The matrix explicitly records each endpoint and the source observations at the same logged step without declaring a content match.

Exact recovered configuration hashes confirm eval_iters702/eval_interval500 for noise-5% and reinit-5%, versus1/1000 for the other six families. Declared global/micro batches128/16 do not establish actual unique examples, valid targets, repeat exposure, masking or distributed reductions. Counterpart sample-axis positions equal step×128 in the inspected loss series; this is a logged-counter relation, not a sample-denominator proof. The supplied scalar records and configurations do not bind the exact training/evaluation implementation revision. The local research implementations are not established as the producing implementation.

## What is usable

The extraction and source integrity are verified. Original-tag/value quotations, source-level traces, duplicate diagnostics and the configuration-effort discrepancy are usable with their provenance and limitations. The three exported source-trace figure formats show unsmoothed logs with all validation points, including duplicates, and make no checkpoint-matched performance claim. METRIC_SEMANTICS.md distinguishes this source description from scientific metric qualification.

**Zero scientific descriptive aggregates and zero checkpoint-matched comparisons qualify under the exact identity/protocol contract.** Folder membership, a timestamp and an equal step are insufficient to bind a value to delivered tensor content. Cohort/split membership, metric definition/direction, denominator, aggregation and implementation identity remain missing. The checker localizes these missing gates; it does not turn successful transport into scientific admission. A higher reported loss is not evidence of useful forgetting.

No combined retain/forget view is fabricated. Verified S09 retain outputs remain unchanged:42,120 classifier marginals,108 LM units/216 metrics,48,924 admitted and42,228 deferred specifications. Refitted and unchanged-base policies, six tasks,26 representations, three probe CV seeds, block16 and finalnorm emphasis remain intact. No new bootstrap draws, thresholds, calibration, fitting, inference or raw forget evaluation occurred.

There is **no qualified layerwise forget-performance evidence**. Layer-indexed gradient norms are optimization diagnostics. The9×26 candidate/representation coverage has234 empty performance slots for an unspecified forget task/metric. The full task/split/readout/policy/seed grid is not defined, so its missing-cell count remains null with reason. It would be misleading to manufacture a denominator from the six benign retain tasks or copy a model-level value across layers.

## What changed and what remains

Pinned attempt-001 validator defects reproduce: out-of-range confidence levels and empty method metadata could be accepted; malformed uncertainty could crash; some invalid intervals discarded a valid point; reported reference fields could pass while the actual target task/cohort/split/protocol/readout differed. New versioned code distinguishes point validity, reported-interval qualification and comparison compatibility.47 adversarial cases and a separate Fraction-based checker cover these defects and the nonempty scalar ingestion adapter. Synthetic fixtures remain separate from actual source observations.

EARLIER_STAGE_IMPACT_REVIEW.md identifies the S01 metadata-only boundary, S02 missing qualification, S09's separate external dependency and the S10 filename-heuristic/reporting error. This is a precise source assessment correction, not an invalidation of the retained numerical release. Original branches, historical attempts, canonical package and S04 freeze remain immutable.

The unsent collaborator request asks only for unresolved content/invocation bindings, source implementation/metric/cohort/denominator semantics, compatible reference/uncertainty metadata and genuine layerwise aggregate results. No message was sent. Parentage, masks, realized dose, training exposure, independent intervention replication, candidate05 historical upload privacy and broader delivery completeness remain bounded historical limitations.

S11 can accurately report verified retain science plus explicitly unqualified source-log evidence, with exact checkpoint-matched and layerwise forget integration pending. S11 requires its separate direct approval and has not started. Recovery and publication receipts name their actual verified scopes and immutable delivery identities; they do not claim model replay, clean-runtime recreation or repeated evaluation.

FORGET_SCIENTIFIC_STATUS: EXTRACTION_ONLY_PENDING_QUALIFICATION

LAYERWISE_FORGET_STATUS: PENDING_QUALIFIED_LAYERWISE_PERFORMANCE

HOLD_BEFORE_S11
