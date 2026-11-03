# Drafts — not sent

Results/config: Six-task frozen Evo2 dev baselines and the separate supplied-H3 test table are ready in BASELINE_TABLES.csv. On supplied H3, original MLP AUROC .8318, final-norm logistic .8469, composition .8054, 4-mer .8955. Evo2 logistic minus 4-mer: -.0485 [ -.0657, -.0322 ]; this follow-up is exploratory and conditional on fitted readouts. Selected original MLP saw 1842 unique train rows (15.39%). These scores do not measure an unlearning effect. Six-task block7 H3 .9275 is dev under a different sample/selection protocol and cannot be subtracted from final-layer H3 test scores. Configuration differences and causal-LM/classifier-loss distinctions are in CONFIG_COMPARISON.md.

Coordination: Sayyed, could you review the configuration comparison and share immutable post/parent checkpoint identities, tokenizer/config/loader provenance and exact benign split IDs/labels? Historical fitted heads are only needed for exact historical reproduction. For my incremental retain preparation, can we agree H3 → H3+promoter → H3+promoter+splice (or core promoter alternative), token proportions and the retain-only manifest adapter? I have deterministic manifest/accounting preparation ready; actual packed loss-mask accounting still needs the pipeline interface. Your four-nucleotide MaxEnt is a distinct variant; GradDiff diagnosis remains provisional.

Historical report links:
- https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/89c7e93/docs/experiments/ashay/extension/MEETING_RESULTS.md
- https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/89c7e93/docs/experiments/ashay/sayyed-base/RESULTS.md
- https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/89c7e93/docs/experiments/ashay/sayyed-followup/FOLLOWUP_RESULTS.md

Local working branch (not pushed): experiments-ashay-codex-benign-v1. Intended branch URL, unavailable until a separately authorized push: https://github.com/Georgakopoulos-Soares-lab/unlearning/tree/experiments-ashay-codex-benign-v1
