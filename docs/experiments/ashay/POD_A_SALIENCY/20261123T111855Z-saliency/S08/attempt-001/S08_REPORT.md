# S08 independent verification and release

The complete frozen nine-candidate, other-five-task scope passed independent verification, the original full-CV audit panel and declared private recovery. A separate S08 overlay releases the passing evidence. The original S07 records remain byte-identical and retain `COMPLETE_UNVERIFIED`; they are consumed with the source-bound S08 overlay.

## Coverage and meaning

| Quantity | Newly checked in S08 | Reused S05 H3 | Combined six-task scope |
|---|---:|---:|---:|
| Refitted heads | 3,510 | 702 | 4,212 |
| Fixed-original-base applications | 3,510 | 702 | 4,212 |
| Development probability paths | 7,020 | 1,404 | 8,424 |
| Marginal metric records | 35,100 | 7,020 | 42,120 |
| Fresh full-CV audit refits | 105 | 21 previously completed | 126 original panel cases |

All **107,085 typed evidence keys** reconcile exactly: 105,300 existing S07 producer-evidence keys plus 1,785 new audit keys (105 refits and 1,680 initial calls). This includes 49,140 saved scientific endpoint keys and 56,160 producer initial-call provenance records. Provenance checks are not fresh fits. S07’s **56,295 actual calls / 135 retries** were independently reconciled. S08 made **1,680 audit calls**, comprising 1,680 initial calls and **0 permitted retries**.

All **35,100 estimates and intervals** are available. Of **70,200,000 attempted bootstrap metric values**, **70,200,000** are valid and **0** invalid. Validity was independently calculated, not assumed from S07.

S06’s 90 feature bundles, 69,120 logical rows, 2,340 matrices, 90 LM units and 180 LM metric records were reused unchanged. No new feature extraction, backbone forward, LM evaluation, control fit, test access or intervention training occurred. The 390 other-five original-base heads support 3,510 applications; they were not retrained. The full 468 original-base references and 36 shared DNA controls remain immutable dependencies.

## How verification was independent

Saved probabilities were reconstructed from each saved scaler and linear head without calling the producer prediction method. In-place float32 scaling preserves the qualified arithmetic before float64 classifier probabilities. The verifier independently checks candidate content, task, split, row order, class columns, layer, seed, cohort, fold, feature hash witness and original-reference identity. Every final head is linked to its exact 16-call selection/fitting provenance.

The five point metrics and all original draw vectors, masks and intervals were reconstructed with pairwise wins and threshold indicators, separate from the producer rank implementation. A separate group-weight adapter uses the exact original draws and lexical group mapping. Splice retains 512 rows and 511 exact/RC groups; the shared group receives shared multiplicity. No replacement sampling was performed. Metrics use the source-bound saved float64 endpoint after independent function reconstruction; full precision is retained.

The original 105 remaining audit cases repeated all 15 CV fits plus a fresh all-TRAIN final fit. They used fold-local StandardScaler, balanced L2 LBFGS, C = 0.1 / 1 / 10, mean fold AUROC with exact ties to smaller C, tol = 1e-4, optimizer random_state = 42, and a fresh 10,000-iteration retry only after the permitted 2,000-iteration convergence warning. Development outputs did not select C, folds or panel membership. Production heads were never replaced.

Audit acceptance preserves the qualified S05 criteria: exact selected C, fold AUROC within absolute 1e-12 and reconstructed final probabilities within absolute 1e-10, all with rtol = 0. Serialization byte equality is diagnostic rather than an acceptance requirement. The 21 H3 audits were reused through their original verified identities.

Independence is at the implementation and execution level, with explicitly shared NumPy, SciPy, BLAS, sklearn estimator/scoring specification and joblib decoding. This does not constitute independent library, hardware or clean-runtime recreation. Adversarial fixtures challenge analytic binary/multiclass metrics, ties, clipping, shared groups, missing classes, incorrect columns/rows/identities/precision, invalid masks/percentiles, stale source, corrupt archives, partial writes, duplicate writers and retry boundaries.

## Numerical acceptance and exact worst locations

| Check | Worst absolute residual | Gate | Candidate / task / representation / seed / policy | Coordinate |
|---|---:|---:|---|---|
| audit_CV | 0 | 1e-12 | candidate_01 / gue_mouse_0 / decoder.layers.16 / 1234 / audit | [0] |
| audit_probability | 0 | 1e-10 | candidate_01 / gue_mouse_0 / decoder.layers.16 / 1234 / audit | [0, 0] |
| saved_probability | 0 | 1e-10 | candidate_01 / gue_tf_0 / decoder.layers.0 / 1234 / independent_refit | [0, 0] |
| metric_point | 3.5527136788005009e-15 | 1e-12 | candidate_04 / gue_splice_reconstructed / decoder.layers.17 / 1234 / fixed_original_base | [0] |
| metric_draw | 2.1316282072803006e-14 | 1e-12 | candidate_09 / gue_splice_reconstructed / decoder.layers.0 / 1234 / fixed_original_base | [1643] |
| metric_CI | 8.8817841970012523e-15 | 1e-12 | candidate_05 / gue_splice_reconstructed / decoder.layers.14 / 1234 / fixed_original_base | [1] |

Every comparison used unrounded values and rtol = 0. Coordinates and exact planned unit IDs are retained in the global indexes and task ledgers. Per-example probabilities remain private. Reconstruction tolerance is not scientific uncertainty.

## Descriptive diagnostics prompted by already visible S07 outcomes

These diagnostics were requested after S07 outcomes were visible; they are not presented as preregistered before those outcomes. They check identity and numerical meaning without changing the experiment.

- paths: **7020**.
- binary balanced accuracy exactly half: **279**.
- paths with confident errors p above 0 99: **6359**.
- paths with clipped true probabilities: **591**.
- half BA single predicted class: **279**.

Across **1170** candidate/task/representation groups, all three seeds selected the same C in **1104** groups; refitted parameter content coincided in **1104**, saved probability bytes in **1104**, and serialized head bytes in **1104**. All seed records remain. Different TRAIN folds can legitimately select the same C and produce the same all-TRAIN model.

Binary balanced accuracy of exactly 0.5 was checked against predicted-class counts and full confusion matrices, rather than assumed to mean single-class prediction. Large classifier cross-entropy was checked through confidence, errors and inherited clipping; no recalibration occurred. AUROC measures ranking, whereas classifier cross-entropy measures true-class probability quality. Neither is autoregressive LM NLL. S06 LM checkpoint identities were matched and its evidence reused without re-evaluation or new contrasts.

`decoder.layers.16` is zero-based layer 16, the seventeenth decoder block. `decoder.final_norm` is the post-block normalization. All 26 representations remain included.

Refitted probes measure task-label accessibility to the frozen linear classifier family. Fixed-original-base applications measure compatibility with the exact original scaler/head. Weak linear accessibility does not establish absence of information. The original full-precision values and all favorable, adverse and inconclusive outcomes remain in S07’s 45 marginal tables, now joined to the S08 release overlay; each S08 task index pins its exact table bytes. No winner, effect contrast or across-task capability score was computed here.

The 95% intervals are pointwise exploratory intervals conditional on fitted heads, using the original 2,000 grouped draws and linear 2.5/97.5 percentiles. They omit intervention-training uncertainty, do not establish biological independence and are unadjusted for full-grid searching. CV seed ranges are not confidence intervals.

## Private recovery: what passed and what was excluded

All newly required S08 verification records, fresh audit estimators/final heads, call histories, source/configuration and identity bindings are protected at nine immutable private revisions. Each archive and its separately addressed member manifest were freshly downloaded and checked at the same revision. Safe restoration enforces the exact member set, sizes and hashes and rejects traversal, aliases, links, extra/duplicate members and unbounded expansion.

The recovery panel was sealed before S08 execution: the original 105 audit selectors under both policies, totaling **210 saved paths / 1,050 metric vectors / 2.1 million attempted draw values**, plus reconstruction of **all 105 new audit-head functions**. The restored consumer used only explicitly restored selected S06 feature projections, saved heads, probabilities, groups and original draws. All four candidate eligibility mappings regenerated byte-for-byte in each consumer. There was no producer-path fallback, repeated full-CV fitting during recovery, GPU replay, native-weight repacking or clean-runtime recreation.

| Candidate | Immutable private revision | Archive SHA256 |
|---|---|---|
| candidate_01 | `8e0ea3329bb319c6121eb6b631d55d47d45c6a91` | `292be3cdb7ae51c18eb0dfd51af1b7121777240bc5b00882dc4fdbbaba49b958` |
| candidate_02 | `94a4c5356827b9402dbfed5f185324fd9d283491` | `7128e715eb7bc5b230cb4df147870be30d612d915bab93b03aadf95314b33d07` |
| candidate_03 | `870c6b92aecb6588cbf1dc31672a5a016653eb83` | `c5c301b117ec4c55a638294bf941c3fd686a2e0030289fcfaa259b42388d860b` |
| candidate_04 | `da6f40923d210b7364d9e9f165938e224d9858fc` | `6aa067715cc21e1d71551a991aea44e750525bc0548712cec96db06794c130f3` |
| candidate_05 | `3d7af65f039636a6c53e66ce2b93105911410fcb` | `d74004761df5fc3882a77214e185bfd75df52d8b807facba2364398e398c11a8` |
| candidate_06 | `ec75119fe64ed54a19bd67dc65ca44a59ae05398` | `818eed523205c8f21a2eb9e0823697df437cd069d68a2cf37ae012473b6a4fe4` |
| candidate_07 | `8acefbd880a9d70d10cee10d45e5fd7f42558bb8` | `52d148f340a7cfc1aca27ec2f5a11cc612bf723a010f1267703b5bf9c6920924` |
| candidate_08 | `0e455aecabfd786319f7a9a557a363ee95ecd0a2` | `16032b4071c7c45967970840f7ec025d6ace84f1b34fdb08cb171e75531e3c67` |
| candidate_09 | `ad3080329aaa7c9f5118d35f023090cbf5181711` | `19538a4b585530e6bc9c759de162762de787cdf2790b70652c319a2788dbb8eb` |

Private object locators, external member manifests and exact unchanged-dependency recipes are retained in private control and final protected metadata. Scientific content, recovery receipts and later final administrative/Git proofs are separate layers to avoid future self-hashes.

## Resources and preservation

Aggregate scientific-unit CPU process time: **3311.291300 seconds**; peak observed numerical worker RSS: **213,762,048 bytes**. Execution stayed within two workers, four BLAS threads per worker, 8 GiB worker RSS / 24 GiB stage budgets and 48 GiB host admission headroom. Application uploads and explicit fresh HTTP bodies were **732,317,976 / 732,317,976 bytes** for candidate protection, including manifest sidecars.

Previous S05/S06/S07 storage consumption remained charged in the baseline. Closed-case stat witnesses and a bounded final metadata allowance preserve the 64 GiB reserve. Shared filesystem free space is not provider quota. Rental start, hourly rate, cost, provider-unused-quota API value and physical network overhead remain null with reasons. No Pod shutdown, resize, scheduler or observer was activated.

Preparation/inspection failures and expected rejection fixtures are preserved separately from scientific failures. No unexplained numerical mismatch affects a released result; no tolerance, method, audit member or producer artifact was changed. Historical A-series work, S00–S07 sealed attempts, original POD_A, prompt checkouts, the canonical package and S04 scientific freezes remain unchanged.

## Interpretation limits and next phase

- S01 whole-delivery coverage remains PARTIAL; nine evaluated candidates do not establish exhaustive delivery.
- Immediate parents remain unresolved. Masks, saliency definitions, realized perturbation doses and training exposure remain incompletely established.
- Three probe CV seeds are partition-sensitivity records, not independent intervention-training replications.
- Candidate 05 historical original-upload privacy remains unresolved; current private recovery cannot establish past visibility.
- Exact/reverse-complement grouping does not establish locus, homology or biological independence.
- Collaborator-generated matched forget aggregates remain an external dependency. No raw forget data or forget-task evaluation was accessed.
- R2 is excluded and was not searched for. Pod B relearning remains separate.
- These benign readouts alone establish neither successful unlearning, erasure, biological function, causal selectivity nor safety.

S09 must consume the exact release indexes and immutable reused endpoints, preserve all **48,924 admitted / 42,228 deferred** contrast specifications (42,120 immediate-parent and 108 LM-base deferred), and reconcile the final scientific/administrative/Git proofs before execution. No S09 contrast was computed or silently activated.

Read `S09_HANDOFF.json`, `RELEASE_OVERLAY.json`, the exhaustive verification indexes and candidate recovery receipts. Final metadata recovery and actual Git delivery identities are linked separately after content sealing.

Next direct approval: `APPROVE S09 at 7007ebd05bf59432bf69109e5f69baad31ec0d3a`.
