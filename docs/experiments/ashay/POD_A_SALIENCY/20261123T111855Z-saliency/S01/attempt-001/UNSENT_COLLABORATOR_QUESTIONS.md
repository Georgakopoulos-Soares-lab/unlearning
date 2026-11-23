# Unsent questions for Sayyed

Draft only; no message sent. Source root is the supplied saliency_sweep Drive folder. Questions apply to the observed reinit/add_noise top5/10/15/20% families, with exact IDs/steps in DELIVERY_INVENTORY.json.

1. For each of the nine observed checkpoint folders, what is the exact immediate unperturbed parent (payload/config/tokenizer identity and revision), distinct from the original training parent? Are any actually R4/R5? Config paths alone do not establish this.
2. Which endpoints should be evaluated and when was perturbation applied? All families show iter1500 except add_noise_top5.0p, which contains iter2000 and iter2151 and a latest pointer to2151. We retained both; please clarify their roles and any training/unlearning/relearning after perturbation. Provide an authoritative delivery/expected-grid manifest and text shard index if available.
3. What defines saliency and top-percent selection: scoring objective/source revision, ranking direction/normalization, global vs layer-local eligibility/ties, mask identity and fraction denominator? Separately specify noise scale/distribution or reinitialization law, independent saliency/mask/noise/training seeds, nested masks and any supplied random/magnitude controls.
4. Configs declare H3 retain inputs, RNG/data seed1234, LR3e-5/cosine and1500 iterations (2151 for noise5). Please provide safe metadata-only actual objective, step/token budgets, sampler/source versions, unique/repeated consumption and overlap/selection history. No raw examples, forget datasets or event binaries are requested.
5. When collaborator-generated forget aggregates become available, bind them to exact checkpoint/parent/step/cohort/protocol identities. They are a later external input; we are not requesting raw forget data or running forget evaluation.

Please prefer one family-wide explanation plus exact per-checkpoint exceptions; avoid duplicating already supplied architecture/config facts. Metadata adjudication of the observed subset can continue while these scoped questions remain pending.
