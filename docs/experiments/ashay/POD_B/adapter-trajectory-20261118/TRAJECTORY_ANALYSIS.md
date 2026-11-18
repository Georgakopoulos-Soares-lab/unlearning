Analysis spec SHA256: `9471098adb38e70a9f9ede6dbe5782a4e379af7bfb697b1fe4b43ae48882bff3`. Formula version: `POD_B.adapter_trajectory.spec.v1`.

All 36 delivered adapters were analyzed successfully across 100 modules in 25 decoder blocks. The package contains 3,600 checkpoint/module measurements and 8,600 comparison/module rows: 86 comparison kinds representing 84 distinct checkpoint pairs. No missing units, nonfinite values, zero factors or numerically zero products were found. The original scientifically qualified model count remains **0/36**.

| Descriptive measurement | Base-labelled series | MaxEnt-labelled series |
|---|---:|---:|
| First delivered step | 100 | 100 |
| Last delivered step | 1800 | 1800 |
| Declared update norm at step 100 | 1.265425155 | 0.843313944 |
| Declared update norm at step 1800 | 18.545607926 | 17.688226689 |
| Endpoint / first-delivered norm | 14.655634 | 20.974664 |
| Adjacent distance range | 0.435502–5.821903 | 0.425822–5.946554 |
| Unweighted median module stable rank, step 100 | 1.934927 | 1.433362 |
| Unweighted median module stable rank, step 1800 | 2.161710 | 1.935335 |

The norm increases at every delivered step in both series. These are magnitudes of the saved adapter products. The ratios are neither change from true step zero nor evidence of capability, exposure, unlearning or biological effect. The intervening unsaved path is unknown. Step labels and job IDs are delivery metadata, not measurements of training tokens.

The MaxEnt 1600→1700 cross-job distance is **0.429428978**, with Frobenius cosine **0.999736116** and symmetric relative distance **0.024591915**. It is 0.867604 times the median of 16 within-job adjacent edges and ranks 16th of 17 when ordered largest first. There is **no exceptional upward boundary jump in this parameter metric**. This does not establish that the resumed job loaded the delivered step-1600 checkpoint. [RESTART_BOUNDARY.md](RESTART_BOUNDARY.md) gives all three neighboring edges and their contributors.

Every module product has numerical rank 16 under the frozen FP64 threshold, but stable rank ranges from 1.000139 to 10.244676 and the count explaining 90% of squared singular-value energy ranges from 1 to 14. Thus algebraic/numerical rank alone conceals substantial spectral concentration. Stable rank is per module; there is no claimed global model rank.

At step 1800, linear_fc1 contributes 51.1373% of base and 50.3377% of MaxEnt summed squared update magnitude; dense_projection contributes 29.4636% and 30.3933%. These totals depend on matrix size and parameterization. Per-module RMS values are supplied to expose the size effect. Neither total nor RMS estimates forward-pass influence. All 25 blocks and all six target types are retained, including small contributors. No final_norm adapter exists in the supplied keys.

The 18 optional same-step cross-series cosines span 0.022635–0.380801. These comparisons use matching nominal serialized coordinates and the same declared scale, and are marked CONDITIONAL_SAME_NOMINAL_COORDINATES in EDGE_METRICS.csv. Unknown parent identity prevents their interpretation as full-model distances or matched-exposure effects. They are excluded from the primary within-series figures and from the restart comparator median.

Six module pairs fall below the declared numerical comparison tolerance on every registered edge: block 23 linear_fc1/linear_fc2, and all four block 24 adapters. This yields 516 numerically agreeing module-edge rows (6×86), despite no exact factor-value identities. Their very small absolute products/differences are retained rather than rounded away; the block heatmap uses a full-range logarithmic scale so these small block totals remain visible. Agreement here means distance ≤ 1e-12 + 5e-11×max(endpoint U norms), not exact equality or proof of absent optimization. Product-zero classification uses a separate factor-scaled roundoff bound.

The 36 payload SHA256 values and 36 full tensor-content fingerprints are distinct. Among the 84 distinct evaluated checkpoint pairs, no global declared product is numerically indistinguishable under the frozen tolerance. This covers the registered comparison set, not all 630 possible unordered pairs. Numerical inequality of BF16 deliveries does not establish the original optimization history.

What the quantities mean

For A∈R^(r×n) and B∈R^(m×r), the serialized product is P=BA. Saved configs declare r=16, alpha=32 and s=2. The reported U=2BA is a **declared-parameterization adapter update**. Its orientation and scaling are supported by the recorded source/config evidence, but the source is not authenticated to the original jobs. In particular the historical adapter implementation includes runtime semantics beyond a plain matrix product. The actual job-bound operator, backbone, merge state and complete inference state remain unresolved. SEMANTICS_SOURCE_RECORDS.json preserves those evidence levels.

Global norm/distance means Euclidean concatenation of the same 100 serialized parameter blocks: sqrt(sum of squared module norms/distances). Global cosine sums module inner products before dividing by global norms; it is not a mean of module cosines. No function-space orthogonality is assumed. U norm/distance equals twice P norm/distance here; cosine, relative distance and rank diagnostics are scale-invariant for this common positive scale. The raw P quantities remain available independently of the runtime interpretation of U.

Computation is CPU FP64 after lossless BF16→FP32 cache conversion. It does not recover lost BF16 precision. QR decompositions and small-core SVDs avoid reconstructing dense model updates. Differences use a stable factored expression, not subtraction of nearly equal squared norms. All 17 adjacent and 17 first-delivered-relative edges per series are present as separate edge kinds. Two pairs overlap, explaining the 86-kind/84-pair distinction. No comparison is a rate per token.

Audit strength and limits

The consumed original payload, metadata and config hashes were checked, and all 7,200 logical BF16 tensor hashes matched historical fingerprints. Inert allowlisted metadata decoding and weights_only CPU tensor chunk loading reconstructed all 225 model chunks per checkpoint, including split GLU tensors; optimizer, RNG and backbone tensors were not loaded. Frozen source/input/spec identities and original BF16 lineage are recorded.

Seventeen focused tests passed, including nonorthogonal gauge invariance, sign/rescaling, cancellation, near-identical products, unequal ranks, changed scales and malformed inputs. Eighteen metadata-selected real-module cases covered all six target types and all three job families. Full dense FP64 norms, distances and inner products agreed within rtol=5e-11, atol=1e-12; the maximum absolute discrepancy was 5.12e-13. Independent dense spectral checks used bounded 64×64 slices, not a full high-dimensional dense SVD. A separate Gram/trace implementation checked every point and distinct pair, global aggregates and contribution fractions; all passed. VALIDATION.json records the actual scope and retained diagnostic fixes.

This is an exploratory analysis. ANALYSIS_SPEC.json records prior exposure and was frozen before new geometry outcomes. No layers or edges were selected after inspecting their geometry. Plots show observed saved steps; the MaxEnt job boundary is marked and the magnitude plot does not draw an observed within-job path across it. Four figures are available in PDF/SVG/PNG with exact CSV hashes in FIGURE_MANIFEST.json.

Contribution to the eventual benign capability study

This provides a complete, validated parameter trajectory and a descriptive restart check for the delivered files. It identifies future, separately declared exploratory covariates (magnitude, direction, spectral concentration) and preserves their lineage. It neither supplies nor alters B05 coverage, cohorts, calibration, scores or qualification. Associating these quantities with benign capability requires separately approved qualified model scoring and an explicit analysis protocol. The next material dependency remains producer evidence binding full parent state, original loading/operator route and the restart source to each job family; another unchanged folder audit will not resolve it.
