# Comparability and coverage

The studies below answer different questions. Their scores must not be subtracted across backends, sample sizes, representations, or selection policies.

| Study | Backend and checkpoint role | Rows and split | Selection / representations | Evidence status | Permissible comparison |
|---|---|---|---|---|---|
| Original pilot | Original Evo2; pretrained reference | 256 train / 128 dev for three tasks | Dev-selected logistic C; blocks.7 and blocks.15 | Historical aggregate table | Descriptive within the pilot only; exploratory dev |
| Six-task original-backend extension | Original Evo2; pretrained reference | 1,024 train / 512 official dev per task | Five-fold train-only grouped CV; composition, 4-mer, blocks.7/15, final norm | Historical saved-output study | Within-study method contrasts on identical dev rows; no untouched-test claim |
| Supplied-H3 original-backend study | Original Evo2; pretrained reference | 11,971 train / 1,497 dev / 1,497 test | Dev-selected MLP; post-hoc logistic and sequence controls; final norm | Historical saved outputs; test reused | Same-row readout/control contrasts; not a BioNeMo intervention effect |
| BioNeMo common-protocol H3-only comparison | Native base and H3-only MaxEnt references | H3 full split; other five 1,024/512 | Three/five-fold train-only CV; independent refits and fixed-base transfer; layer 16 and final norm | 232 historical scalar records independently recomputed in the prior audit | Base versus H3-only under that protocol; parent lineage/exposure confounds remain |
| Planned multi-retain/all-layer extension | Base, H3-only, and unidentified broader-retain arm | Same qualified six-task manifests | 25 zero-indexed blocks plus final norm; seeds 42/17/1234; independent refit and fixed-base policies | Expected/blocked; no new scientific unit available | Only finalized, identity-matched units under the frozen fixed-physical-8 protocol |

`decoder.layers[16]` is the zero-indexed 17th block. It is not `blocks.15`. Splice AUROC is macro one-vs-rest; binary AUROC uses numeric class 1. Binary accuracy uses probability class 1 >= 0.5; multiclass uses sorted-class argmax.

The latest completed BioNeMo comparison retained H3 only. It must not be labeled multi-retain. The transcript aliases “ENG H3, promoter 4, human TF0” do not establish exact datasets, proportions, exposure, or token budgets. Splice and mouse-TF exposure is unknown, not established absence.

All bootstrap intervals are pointwise, exploratory, conditional on fitted probes and supplied groups, and unadjusted for multiple comparisons. Exact/RC grouping does not establish homology independence. Seed variation is separate and is not captured by a bootstrap interval. A fixed-base probe failure can reflect representation/readout mismatch and does not prove information absence.

`COVERAGE_TEMPLATE.csv` contains 2,808 planned model/task/layer/seed/policy rows. Values are null until a finalized producer unit is available. Historical two-hook results remain in `EVIDENCE_INDEX.csv`; they are not used to claim all-layer coverage.
