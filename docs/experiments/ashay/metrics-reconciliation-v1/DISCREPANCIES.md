# Discrepancies and misleading labels

1. Historical FOLLOWUP_RESULTS.md contains pending remote-backup prose. Later recovery_chain.json records verified original173 + supplement95 payload checks at immutable revisions. Preserve old report; use latest receipt for recovery status.
2. HVUE AUROC .7439/.6498 must not be labeled accuracy; actual logged accuracy .9648/.9647 is near the majority baseline. No missing score was inferred.
3. VERIFIED_METRICS.csv contains aggregate-source records, not newly prediction-verified metrics. Evidence status is explicit per row; raw predictions and fitted probes are unavailable in this Pod.
4. Historical BioNeMo classifier “CE loss PPL” is not causal LM perplexity. No causal LM value is inferred from those classifier logs.
