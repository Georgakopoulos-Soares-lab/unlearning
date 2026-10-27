# H3 evidence for the team

The independent frozen original Evo2-1B reference is complete. These results compare readouts and sequence controls on the same 1,497 H3 test rows; they do not compare pretrained and post-unlearning models.

| Readout | Test AUROC [pointwise 95% interval] | Accuracy |
|---|---:|---:|
| Original MLP, unchanged | 0.8318 [0.8097, 0.8519] | 70.27% |
| Evo2 final-normalized logistic | 0.8469 [0.8272, 0.8655] | 76.22% |
| Composition logistic | 0.8054 [0.7815, 0.8267] | 73.88% |
| 4-mer logistic | 0.8955 [0.8794, 0.9114] | 82.10% |

Paired Evo2-logistic-minus-composition AUROC: +0.0416 [0.0240, 0.0602]. Evo2-logistic-minus-4-mer: −0.0485 [−0.0657, −0.0322]. The 4-mer control leads under this protocol. Intervals use 2,000 identical whole-sequence resamples, condition on fitted readouts/splits, are pointwise/unadjusted and exclude training/selection uncertainty and unknown homology dependence. The supplement is post-hoc exploratory because the original test score was already known.

The selected original MLP used 2,000 training draws from only 1,842 unique rows (15.39% of 11,971 available). Feature extraction and training-metric coverage were broader than gradient exposure. This measured limitation does not establish why the score had its value. Exactly two added seeds gave test AUROC 0.8210 and 0.8406; neither replaces the primary result.

There is no unlearning measurement here: no matched post-model checkpoint was evaluated, BioNeMo parent/tokenizer/conversion equivalence is unresolved, and numerical labels have no established biological class mapping. A readout/control difference does not establish biological mechanism or knowledge removal.

**Concrete request:** send an accessible immutable post-model checkpoint and parent identity/checksums, tokenizer/config and supported loader/runtime with conversion provenance; confirm reuse of our hash-pinned H3 splits and supply actual training/forget/retain exposure metadata, or state it is unknown. A new matched comparison does not require the old trained head or historical sampler state. See the [two-route handoff](MATCHED_H3_HANDOFF.md).

Use the existing [full results](FOLLOWUP_RESULTS.md), [paired-difference figure](figures/paired_differences.png), [performance figure](figures/performance.png), [exposure/trajectory figure](figures/exposure_trajectory.png) and [training-exposure addendum](TRAINING_EXPOSURE.md). This summary is prepared only; no message has been sent.
