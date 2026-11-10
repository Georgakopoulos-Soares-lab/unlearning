# Multiretain independent CPU reporting

This package contains historical evidence mapping and CPU-only tools. It contains no new biological measurements. Stage 2 remains ineligible until the producer's fixed-physical-8 gates pass and finalized scientific `COMPLETE.json` units are published.

## Tools

- `scripts/sayyed/multiretain_verifier.py`: independently verifies receipt hashes, ID/label/group/sequence joins, binary and macro-OVR metrics, confusion counts, average precision, train-only folds, C selection, linear-probe reconstruction, LM sufficient statistics, and paired grouped bootstrap contrasts. It does not import producer metric helpers or fit a replacement classifier.
- `scripts/sayyed/multiretain_report.py`: creates six-task layer profiles, paired-difference heatmaps, per-seed tables, seed aggregates, and hashed PNG/PDF/SVG manifests.
- `scripts/sayyed/build_multiretain_evidence.py`: rebuilds the 420-row historical evidence index and 2,808-row planned coverage table from committed sources.

Use the isolated CPU environment with at most two worker threads and CUDA disabled. Example synthetic report:

```bash
CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  /workspace/venvs/multiretain-reporting/bin/python -m scripts.sayyed.multiretain_report \
  --metrics tests/fixtures/multiretain/SYNTHETIC_METRICS.csv \
  --differences tests/fixtures/multiretain/SYNTHETIC_DIFFERENCES.csv \
  --output /workspace/meeting-artifacts/multiretain-reporting-v1/synthetic-preview \
  --split dev --probe-policy independent_refit --synthetic
```

## Finalized-unit contract

The verifier accepts only `schema=multiretain-unit-v1` and `status=COMPLETE`. Every `files` entry needs a unique `role`, absolute `path`, exact `bytes`, and SHA256. Required roles are `protocol`, `manifest`, `predictions`, and `metrics`; optional roles are `folds`, `selection`, `losses`, `contrasts`, `bootstrap`, plus explicitly named linear feature/model roles.

`unit` is an object containing `task`, `split`, `checkpoint`, `layer`, `seed`, and `probe_policy`. The protocol's `manifest_sha256` must match the actual manifest. Prediction identity is `(task, split, id)`; every row also needs `label`, `group`, `sequence_sha256`, sorted integer `classes`, and a `probabilities` object. The evaluation split must have complete manifest coverage. Prediction order may differ because joins use IDs, not row position.

Metrics CSV uses `model,task,split,layer,metric,value`. Binary scores use the sorted class-1 column; multiclass AUROC is macro one-vs-rest. Every declared class needs positive evaluation mass. AP groups tied scores. Saved probabilities must be finite, in range, and sum to one within 1e-12. Metric agreement tolerance is absolute 1e-12.

Linear reconstruction is opt-in through `linear_model`, which names the probe, feature/model roles, feature and coefficient dtypes, and tolerance. Standardization preserves the declared input dtype; affine/probability computation uses float64. A fixed-base configuration must record the source model SHA256. Joblib artifacts are loaded only from the checksummed producer unit.

LM checks consume per-sequence `nll_sum` and positive `n_tokens`, then compute `sum(loss)/sum(targets)`. Unequal sequence target counts are therefore handled by token weighting. Bootstrap checks consume explicit IDs/groups/draws, regenerate draws from the protocol seed, use common IDs for both arms, count rejected missing-class draws, and report intervals as conditional on fitted probes and supplied groups.

## Reporting schemas

Metrics input columns are `task,split,checkpoint,checkpoint_role,layer,seed,probe_policy,metric,value,status,missing_reason`. Difference input replaces `value` with `difference,ci_low,ci_high`. Status is one of `expected`, `completed`, `blocked`, `invalid`, or `not_attempted`. Noncompleted values and interval fields must be empty with a reason; they are never zero. Exact layer names are `decoder.layers.0` through `decoder.layers.24` and `decoder.final_norm`.

The fixtures under `tests/fixtures/multiretain/` and generated preview are synthetic, not biological results. Real figures must be regenerated from finalized numerical tables without `--synthetic`; values must not be edited manually.

## Evidence and limits

`EVIDENCE_INDEX.csv` maps 420 historical scalar records to immutable source commits/paths and verification levels. `COMPARABILITY.md`, `COVERAGE_TEMPLATE.csv`, and `RETAIN_MIXTURE.csv` keep protocols and retain exposure separate. `CLAIMS_TO_EVIDENCE.csv` and `TEAM_SUMMARY_TEMPLATE.md` contain no unsupported multi-retain conclusion. `REVIEW_FINDINGS.md` lists producer-facing corrections and missing inputs.
