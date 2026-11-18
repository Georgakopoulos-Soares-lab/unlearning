Analysis spec SHA256: `9471098adb38e70a9f9ede6dbe5782a4e379af7bfb697b1fe4b43ae48882bff3`. Formula version: `POD_B.adapter_trajectory.spec.v1`.

The saved MaxEnt adapter products show no exceptional upward change at the 1600→1700 job boundary in the defined global parameter metric. All 100 modules are complete, and both endpoints declare scale 2 with the same schema/layout. These facts permit the descriptive comparison; they do not prove causal restart continuity.

| Delivered edge | Job transition | P distance | Declared U distance | Symmetric relative distance | Cosine | Scale left/right |
|---|---|---:|---:|---:|---:|---|
| 1500→1600 | 11776574→11776574 | 0.218790922517 | 0.437581845033 | 0.025282473334 | 0.999720876189 | 2 / 2 |
| 1600→1700 | 11776574→11803647 | 0.214714489238 | 0.429428978477 | 0.024591915411 | 0.999736116034 | 2 / 2 |
| 1700→1800 | 11803647→11803647 | 0.212910940363 | 0.425821880726 | 0.024175849891 | 0.999743736552 | 2 / 2 |

There are 17 MaxEnt adjacent edges. The 16 within-job comparators comprise 15 edges in job 11776574 (100→200 through 1500→1600) and one edge in job 11803647 (1700→1800). Their median U distance is 0.494959374871. The boundary/median ratio is 0.867604494993; its descending rank is 16/17, where rank 1 is largest. This is a descriptive ordering, with no p-value or exceptional-change threshold. The wide early-to-late variation and unequal job edge counts limit any pooled comparison.

All 17 comparator rows and job memberships are in GLOBAL_EDGE_METRICS.csv (kind=adjacent, left_series=maxent). The three neighboring global edges and all 300 module rows are retained there and in EDGE_METRICS.csv. Block and target fractions use squared distances, with fixed module sets and no missing denominator changes.

| Target type | 1500→1600 fraction | 1600→1700 fraction | 1700→1800 fraction |
|---|---:|---:|---:|
| dense | 6.497053% | 6.457087% | 6.478434% |
| dense_projection | 34.184368% | 34.750689% | 34.548299% |
| linear_fc1 | 48.432915% | 47.915861% | 48.059051% |
| linear_fc2 | 8.227852% | 8.229419% | 8.211470% |
| linear_proj | 0.255936% | 0.247443% | 0.256470% |
| linear_qkv | 2.401877% | 2.399501% | 2.446276% |

At the boundary, all 100 raw module distances are nonzero, but six modules are numerically indistinguishable under the declared comparison tolerance (block 23 linear_fc1/linear_fc2 and all four block 24 adapters). Their U distances range from 2.74e-20 to 2.41e-17. Nonzero raw values do not imply resolved optimization in these modules. The other 94 exceed that tolerance. The five largest module contributions are:

| Module | Fraction of squared boundary distance |
|---|---:|
| decoder.layers.0.mixer.dense_projection.adapter | 3.184034% |
| decoder.layers.1.mlp.linear_fc1.adapter | 2.969362% |
| decoder.layers.0.mlp.linear_fc1.adapter | 2.943409% |
| decoder.layers.21.mlp.linear_fc1.adapter | 2.656961% |
| decoder.layers.16.mlp.linear_fc1.adapter | 2.525159% |

All 25 blocks contribute nonzero distance. The five largest block fractions are block 0: 6.5700%, block 1: 5.6280%, block 21: 5.5263%, block 15: 5.3689%, block 14: 5.1201%. The largest single module contributes only 3.1840%, and the largest block 6.5700%; changes are distributed across the fixed inventory while concentrating by target type, especially linear_fc1 and dense_projection. These are size-sensitive parameter contributions, not biological or functional importance. The complete module/block/type tables make that statement auditable.

Three separate questions remain distinct. A config/job change is documented at this boundary. A tensor-space jump is measurable and small relative to the registered comparison set. Which concrete checkpoint and full parent state the new job loaded remains unproven. Gradual optimization, different update schedules, BF16 quantization, copied/modified adapter state, an unrecorded parent change or different runtime semantics cannot be adjudicated by these products alone. No claim of a wrong parent, absent optimization or successful resume follows.

Producer evidence should bind job 11803647 to its exact resumed checkpoint bytes, original job source/config/loading command, full nonadapter parent state and merge state. Until then, this boundary remains a valid adapter-space descriptive edge and an unresolved original-model provenance boundary. No labels, sequences, held-out scores or performance results were inspected to explain the pattern.
