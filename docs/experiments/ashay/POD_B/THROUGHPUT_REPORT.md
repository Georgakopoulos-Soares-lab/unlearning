This report is a CPU-only conditional forecast. **No B05 calibration, GPU use, inference, fitting, bootstrap or scoring was performed.** Detailed values, sources, assumptions and null totals are in B05_RESOURCE_FORECAST.json. B04 stays blocked0/36 and its ledgers/deadlines are unchanged.

| Option | Models | Final refitted heads | CV candidate-fold fits | Nominal total estimator fits | Fixed-base transfer units | LM eval/population units | Raw features GB (GiB) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
|full|36|16,848|235,872|252,720|16,848|252/468|162.783 (151.604)|
|balanced|14|6,552|91,728|98,280|6,552|98/182|63.305 (58.957)|
|core|8|3,744|52,416|56,160|3,744|56/104|36.174 (33.690)|

Counts are exact source-derived arithmetic before reuse/retries: one model has26×3×6=468 final heads; C-grid3 times the sum of fold counts(3+5×5), times26 layers×3 seeds gives6552 CV fits,7020 total. Fixed-base transfer performs no new estimator fit. Existing468 base scaler/head pairs and36 controls are shared dependencies. No new target heads/features can currently be deducted by exact identity. LM has13 task/split sufficient-statistic populations (including train), seven evaluation populations, and no layer/seed multiplier. Proposed future evaluation remains contingent on separate approval; all currently executable units are empty.

Full selects all18 steps per series. Balanced selects common100/500/1000/1400/1600/1700/1800 (14 models). Core selects100/1600/1700/1800 (8). Balanced/core preserve all tasks/layers/seeds and both restart sides, lose intervening step detail and have only four included adjacent-delivered differences across both series; sparse gaps are not adjacent transitions. Full has34 adjacent differences. No option is activated.

Historical observations, with limits:

- Three completed reference-model pairs (base,H3-only,R3) each cover14965 H3 and7680 other-five rows, all26 features. Their extraction progress receipts report elapsed time including the recorded model-load stage, synchronized forward time and a3,224,296,960-byte historical GPU peak. Each pair consists of two task-group invocations/loads; a new combined or adapter route may differ. These are full-population references, not12-row smoke extrapolations.
  - base_h3/base: elapsed323.136654s, forward235.520678s.
  - base_h3/maxent: elapsed328.044372s, forward235.206873s.
  - R3/new: elapsed330.999181s, forward235.056980s.
- The prior384-row parent run reports elapsed11.041761s and forward7.026997s. It is a training-only parent timing/consistency reference, not a full-cohort adapter forecast.
- Timing-only projection of468 archived R3 head/transfer/bootstrap units sums to2080.398763s of sequential unit wall time and4143.516457s of explicitly recorded parent+CV-worker CPU work. It omits task-level LM, independent audit, reporting and backup.7020 nominal fits produced7048 attempts, including28 retries at10000 iterations; observed retry fraction0.398860%. No saved outcome arrays or research scores were analyzed. Per-task extrema and all source hashes are retained privately.
- Eight earlier training-only single-fit timings cover H3 and TF0, block16/final_norm and C0.1/10, at one BLAS thread. They are not six complete search units or multiclass timing evidence. New-feature convergence remains unmeasured.

| Option | Historical reference extraction proxy, seconds | R3 one-arm unit-wall proxy, hours | Four fully busy one-thread CPU workers: ideal work floor, hours | Conservative task-max unit-wall stress proxy, hours |
| --- | ---: | ---: | ---: | ---: |
|full|11632.9–11916.0|20.80|10.36|140.44|
|balanced|4523.9–4634.0|8.09|4.03|54.61|
|core|2585.1–2648.0|4.62|2.30|31.21|

These are **estimates under stated historical applicability assumptions**, not qualified supplied-model measurements or guaranteed lower/upper performance bounds. The four-worker floor divides recorded CPU work by4 and assumes complete utilization, ignores serial dependencies/I/O and changes the historical orchestration; it is not promised speedup. The conservative scenario assigns every unit its task's historical maximum; it is deliberately a sensitivity envelope, not a confidence bound. R3 includes its narrower bootstrap/transfer scope; new trajectory contrasts, target-head convergence and audited source adaptation can add cost.

| Option | Future GPU envelope | Seconds available/model | Headroom after conservative historical extraction proxy | Interpretation |
| --- | ---: | ---: | ---: | --- |
|full|7200|200.00|-4716.0s|NO_UNDER_HISTORICAL_PARENT_PROXY_BEFORE_OTHER_COSTS|
|full|9000|250.00|-2916.0s|NO_UNDER_HISTORICAL_PARENT_PROXY_BEFORE_OTHER_COSTS|
|balanced|7200|514.29|2566.0s|UNKNOWN_PENDING_QUALIFIED_CALIBRATION|
|balanced|9000|642.86|4366.0s|UNKNOWN_PENDING_QUALIFIED_CALIBRATION|
|core|7200|900.00|4552.0s|UNKNOWN_PENDING_QUALIFIED_CALIBRATION|
|core|9000|1125.00|6352.0s|UNKNOWN_PENDING_QUALIFIED_CALIBRATION|

The full36 option exceeds both7200/9000-second envelopes under the historical elapsed-extraction proxy, before extra gate/failure/cleanup costs. A different bound route could change that; calibration is needed to establish whether the required200/250 seconds per model is attainable. Balanced/core have arithmetic headroom under that proxy but no feasibility guarantee. B04 qualification overhead and future B05 calibration are separate prerequisite stages: do not add their unspent credits to B06 or silently double-count them as fresh budgets. Any same-envelope inclusion must explicitly subtract them.

Retry pricing is explicit: each nominal estimator may have at most one documented10000 retry, so maximum additional attempts equal nominal fits. The source forecast includes sensitivities of1%,5%,100% *additional* retries at the observed historical retry mean. Historical unit totals already include28 retries; sensitivities add stress, not an estimated event probability. The100% case can exhaust useful wall time or fail convergence; no alternative hyperparameter/solver protocol is allowed. Actual new-head retry rates and complete search/serialization timing require the separately approved six-unit calibration.

Bootstrap work is priced by the intended families. Per model there are1092 classification task/split/layer/seed/policy populations, five metrics and2000 attempted draws, producing10,920,000 elementary metric values if all are retained. Seven shared task/split resampling matrices can reuse5553 exact/RC groups and5554 rows; int32 draw indices require44,424,000 bytes and all seven float64 row-weight matrices88,864,000 bytes before working buffers. The1092 probability populations require1404 class-score rank sorts per model (six binary populations plus three OVR splice classes, times26×3×2). Rank sorts combine ties once per prediction/class ordering; drawing costs scale with2000×population and subtraction reuses paired metric vectors. Do not independently resample every contrast.

- full: proposed absolute36, adjacent-delivered34, first-delivered34, common-step18, first-delivered DID17. Q3/Q4-dependent contrasts remain conditional/unavailable, not zero effects.
- balanced: proposed absolute14, adjacent-delivered4, first-delivered12, common-step7, first-delivered DID6. Q3/Q4-dependent contrasts remain conditional/unavailable, not zero effects.
- core: proposed absolute8, adjacent-delivered4, first-delivered6, common-step4, first-delivered DID3. Q3/Q4-dependent contrasts remain conditional/unavailable, not zero effects.

New complete bootstrap, independent prediction/head/metric/LM audit, plots/report, compression/upload/download/restore timing are null with explicit reasons. Historical unit timings cover part of this work and must not be added a second time as a separately priced duplicate bootstrap. No credible total wall time is available until those missing components and source compatibility are resolved. Feasibility is UNKNOWN_PENDING_QUALIFIED_CALIBRATION.

Storage and working memory:

- Raw features are N×22645×26×1920×4 bytes; full36=162,783,129,600 bytes. Per model=4,521,753,600 bytes. These exclude IDs, losses, probabilities, joblib metadata, bootstrap values, temporary duplication and backups. Compression ratio1 is assumed; no invented savings.
- The plan prices two-copy and three-copy feature-only stress footprints separately. Original artifacts are never deleted to meet a forecast. New caches are chunked, hash-sealed, disk-backed and processed one model at a time; all36 are not assumed resident in RAM. No production full logits retained by default.
- Raw two-policy class-probability values are14,501,760 bytes/model; row NLL/count statistics271,740 bytes/model; elementary classification bootstrap values87,360,000 bytes/model and LM values224,000 bytes/model. Actual serialization/metadata/head files and temporary matrices add overhead. Save elementary draws once and contrast summaries, rather than persisting every duplicate pairwise vector unless needed for verification.
- Read-only hardware snapshot: 128 logical CPUs in affinity but cgroup CPU quota15.3 cores; RAM hard limit214,999,998,464 bytes, observed use86,337,703,936 bytes. Proposed future total host soft cap70%=150,499,998,924 bytes must include existing use and be rechecked. At most4 one-thread workers plus bounded nonoversubscribed helpers. GPU metadata: NVIDIA H100 NVL, 95830 MiB, 0 MiB, 595.112.07. No scientific stack was imported to obtain it.
- statvfs reports325,667,354,640,384 available bytes on the shared filesystem. This is not a project quota guarantee, reserved space or a sustained bandwidth measurement; do not assume the entire reported free pool is dedicated. Storage quota/bandwidth and verified backup overhead remain launch prerequisites.

The dependency-critical wall path is identity evidence → B04 scientific qualification → reviewed scope → approved B05 calibration/rebinding → pipeline max(GPU extraction, CPU after sealed features) → remaining contrast/audit → reporting and verified backup → closure reserve. CPU fitting can overlap a later model's extraction only after the previous qualified feature unit is sealed and with separate resource ceilings; one GPU owner always. Failure/import/load/idle/cleanup occupation is charged. The pipeline cannot start from empty scientifically eligible coverage.

Proposed closure reserve is at least the maximum of any still-applicable inherited reserve,45 minutes, and measured audit/report/backup/restore time plus20% margin. A later approval must bind actual start, forward cutoff, closure deadline, cumulative accounting and whether calibration/qualification is included. No future B05/B06 window exists now. The historical host/setup planning deadline20:33:21UTC remains recorded; no provider lease extension or shutdown timer is inferred.

B04 stays at1675.5146971674585/9000 occupied GPU seconds, engineering1675.5146971674585/1800; its fixed18:11:46UTC forward and18:56:46UTC closure deadlines are unchanged. PLAN_ONLY authorizes0 GPU seconds and transfers no B04 remaining credit. Provider rental start/rate are unknown. Future phase7200/9000 envelopes are planning scenarios, not current allocations. A precise later resource amendment must specify scope,cumulative cap,actual window and reserve without resetting earlier usage.

Smallest next action: obtain the existing two core state/route assertions for the three producing jobs using the unsent B04_PRODUCER_REQUEST_DELTA.md, then separately approve affected B04 qualification. After a reviewed useful qualified scope, separately approve the prepared B05 calibration/rebinding recipe. Reuse this package; do not repeat unchanged audits or alter design after viewing outcomes. B06 needs separate exact-plan approval. Private planning evidence is local only; B09 backup/restore remains pending.

Proposed production forward arithmetic preserves two original manifest streams/model, not separate extraction for every normalized task/split view: ceil(14965/8)+7680/8=2831 physical batches,22648 physical rows and3 excluded filler rows/model. At pad length1000 that is22,648,000 padded positions/model. Full/balanced/core would have101916/39634/22648 batches respectively if that route is later qualified; these are planned arithmetic, not executed counts or timing measurements.
