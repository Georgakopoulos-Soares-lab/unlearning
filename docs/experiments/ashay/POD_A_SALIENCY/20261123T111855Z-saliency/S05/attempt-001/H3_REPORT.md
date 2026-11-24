# S05 H3 technical report

All nine supplied candidate endpoints passed their individual H3 technical and private-recovery gates. This establishes source-bound, reproducible standalone H3 measurements. It does not establish successful forgetting, causal saliency selectivity, biological function, equivalence or intervention replication.

H3 uses11,971 TRAIN rows and1,497 dev rows. Exact/RC groups: TRAIN 11971, dev 1497. Three saved TRAIN-only group folds choose C from0.1,1,10 by mean validation AUROC (ties prefer smaller C), with fold-local StandardScaler and balanced L2 LBFGS. Final refits use all TRAIN rows. Both refitted and unchanged original-base scaler/head policies are retained without dev selection or target recentering. All26 representations and CV seeds42/17/1234 are included.

Coverage:18 bundles,121,212 logical rows;702 final refits;702 unchanged-reference applications;1,404 dev probability paths;7,020 classifier metric rows and36 LM metric rows (18LM units). Exactly21 prospective full-CV audit refits passed. Initial production optimizer calls7,020, retries 85; initial audit calls210, retries 0. Physical rows121,320 include108 excluded fillers; filler rows never enter features or metrics.

Every dev probability path was reconstructed from its upstream saved head and float32 features using separate scaler/linear/logistic code. All five points,2000 saved draw values, validity masks/counts and linear percentile endpoints were recomputed by the independent implementation. Maximum probability residual 0.0 (atol1e-10); maximum point/draw/interval residual 3.552713678800501e-15 (atol1e-12), rtol0. Both TRAIN/dev LM units were independently aggregated from actual per-example FP32 loss sums and target counts. LM uses summed loss / summed targets, then exponentiation; TRAIN is diagnostic with no bootstrap. Numerical tolerances are not confidence intervals.

All nine immutable private checkpoints were freshly fetched through explicit HTTPS, with every safe regular member byte-verified. The numerical recovery panel uses the exact21 frozen H3 audit head keys under both policies:42 probability paths/all210 classifier metric records and18LM units. It uses restored code/features/heads/labels/draws with producer data fallback denied. It does not claim fresh full-CV fitting, GPU replay or clean-runtime recreation. Native weights and runtime dependencies use exact prior immutable references.

H3_ANCHOR_MARGINALS.csv contains all five metrics at the predeclared zero-based block16 (17th block) and final normalization, seed42, for each endpoint and policy. Each full-precision source row includes its direction, sample/group count, interval, release status and artifact joins. candidates/*/H3_MARGINALS.jsonl retains every layer,seed,policy and metric, including adverse or flat measurements. H3_LM_INDEX.json contains all LM counts/points/intervals. MARGINAL_SOURCE_INDEX.jsonl provides stable row joins. No model ranking, favorable subset or new contrast is selected.

Intervals are95% pointwise exploratory exact/RC-group bootstrap intervals conditional on fitted heads, using the original2000 draws (seed20261103). They omit intervention-training variability and fitted-head training uncertainty, do not correct full-grid searching, and exact/RC grouping does not establish locus/homology independence. Seed ranges describe sensitivity, not confidence intervals. No S09 policy/base/control/parent/LM-reference contrasts were calculated.

Immediate parents, mask identities, perturbation laws/timing, realized training exposure and independent intervention/seed roles remain unresolved. Steps1500/2000/2151 do not prove matched exposure. Both noise5% endpoints remain distinct; neither is selected or averaged. Original-base readout compatibility does not identify the immediate parent. S01 whole-delivery completeness remains PARTIAL; candidate05 original-upload privacy remains unknown. Collaborator forget results remain a separate dependency; raw forget data were not accessed. Pod B remains separate.

Resource measurements and definitions are in RESOURCE_SUMMARY.json, each candidate EXTRACTION_RESOURCE.json and the verification/recovery receipts. Overlapping wall times are not added as elapsed duration or billed GPU usage. Account billing/cost is unknown. The no-deadline amendment remains active.

The following compact AUROC anchors use seed42 throughout (higher is better; n=1497, exact/RC groups=1497). Brackets are the pointwise conditional95% intervals defined above. Each linked cell resolves to its exact full-precision row; both policies and both predetermined representations are shown for every endpoint. The other four metrics and their source IDs are in H3_ANCHOR_MARGINALS.csv.

| Candidate | Endpoint / step | Representation | Policy | AUROC [95% pointwise interval] |
|---|---|---|---|---|
| candidate_01 | saliency_maxent_ht_emp_h3_add_noise_top10.0p / 1500 | decoder.layers.16 | independent_refit | [0.950469 [0.939571, 0.960197]](candidates/candidate_01/H3_MARGINALS.jsonl#L481) |
| candidate_01 | saliency_maxent_ht_emp_h3_add_noise_top10.0p / 1500 | decoder.layers.16 | fixed_original_base | [0.828509 [0.807922, 0.848804]](candidates/candidate_01/H3_MARGINALS.jsonl#L486) |
| candidate_01 | saliency_maxent_ht_emp_h3_add_noise_top10.0p / 1500 | decoder.final_norm | independent_refit | [0.840115 [0.819484, 0.859799]](candidates/candidate_01/H3_MARGINALS.jsonl#L751) |
| candidate_01 | saliency_maxent_ht_emp_h3_add_noise_top10.0p / 1500 | decoder.final_norm | fixed_original_base | [0.805337 [0.783606, 0.825678]](candidates/candidate_01/H3_MARGINALS.jsonl#L756) |
| candidate_02 | saliency_maxent_ht_emp_h3_add_noise_top15.0p / 1500 | decoder.layers.16 | independent_refit | [0.953752 [0.943527, 0.963269]](candidates/candidate_02/H3_MARGINALS.jsonl#L481) |
| candidate_02 | saliency_maxent_ht_emp_h3_add_noise_top15.0p / 1500 | decoder.layers.16 | fixed_original_base | [0.827991 [0.807089, 0.847765]](candidates/candidate_02/H3_MARGINALS.jsonl#L486) |
| candidate_02 | saliency_maxent_ht_emp_h3_add_noise_top15.0p / 1500 | decoder.final_norm | independent_refit | [0.841909 [0.821573, 0.861940]](candidates/candidate_02/H3_MARGINALS.jsonl#L751) |
| candidate_02 | saliency_maxent_ht_emp_h3_add_noise_top15.0p / 1500 | decoder.final_norm | fixed_original_base | [0.801825 [0.779476, 0.822795]](candidates/candidate_02/H3_MARGINALS.jsonl#L756) |
| candidate_03 | saliency_maxent_ht_emp_h3_add_noise_top20.0p / 1500 | decoder.layers.16 | independent_refit | [0.951729 [0.941338, 0.961524]](candidates/candidate_03/H3_MARGINALS.jsonl#L481) |
| candidate_03 | saliency_maxent_ht_emp_h3_add_noise_top20.0p / 1500 | decoder.layers.16 | fixed_original_base | [0.833874 [0.813169, 0.853440]](candidates/candidate_03/H3_MARGINALS.jsonl#L486) |
| candidate_03 | saliency_maxent_ht_emp_h3_add_noise_top20.0p / 1500 | decoder.final_norm | independent_refit | [0.841629 [0.820965, 0.861162]](candidates/candidate_03/H3_MARGINALS.jsonl#L751) |
| candidate_03 | saliency_maxent_ht_emp_h3_add_noise_top20.0p / 1500 | decoder.final_norm | fixed_original_base | [0.800402 [0.778467, 0.821319]](candidates/candidate_03/H3_MARGINALS.jsonl#L756) |
| candidate_04 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2000 | decoder.layers.16 | independent_refit | [0.955677 [0.945434, 0.965014]](candidates/candidate_04/H3_MARGINALS.jsonl#L481) |
| candidate_04 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2000 | decoder.layers.16 | fixed_original_base | [0.831082 [0.810761, 0.850907]](candidates/candidate_04/H3_MARGINALS.jsonl#L486) |
| candidate_04 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2000 | decoder.final_norm | independent_refit | [0.829021 [0.808549, 0.848297]](candidates/candidate_04/H3_MARGINALS.jsonl#L751) |
| candidate_04 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2000 | decoder.final_norm | fixed_original_base | [0.726670 [0.701900, 0.750579]](candidates/candidate_04/H3_MARGINALS.jsonl#L756) |
| candidate_05 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2151 | decoder.layers.16 | independent_refit | [0.955745 [0.945581, 0.965044]](candidates/candidate_05/H3_MARGINALS.jsonl#L481) |
| candidate_05 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2151 | decoder.layers.16 | fixed_original_base | [0.830800 [0.810296, 0.850731]](candidates/candidate_05/H3_MARGINALS.jsonl#L486) |
| candidate_05 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2151 | decoder.final_norm | independent_refit | [0.826702 [0.806232, 0.846045]](candidates/candidate_05/H3_MARGINALS.jsonl#L751) |
| candidate_05 | saliency_maxent_ht_emp_h3_add_noise_top5.0p / 2151 | decoder.final_norm | fixed_original_base | [0.725857 [0.700641, 0.749833]](candidates/candidate_05/H3_MARGINALS.jsonl#L756) |
| candidate_06 | saliency_maxent_ht_emp_h3_reinit_top10.0p / 1500 | decoder.layers.16 | independent_refit | [0.952583 [0.942311, 0.962111]](candidates/candidate_06/H3_MARGINALS.jsonl#L481) |
| candidate_06 | saliency_maxent_ht_emp_h3_reinit_top10.0p / 1500 | decoder.layers.16 | fixed_original_base | [0.832350 [0.811581, 0.852087]](candidates/candidate_06/H3_MARGINALS.jsonl#L486) |
| candidate_06 | saliency_maxent_ht_emp_h3_reinit_top10.0p / 1500 | decoder.final_norm | independent_refit | [0.840174 [0.819862, 0.860218]](candidates/candidate_06/H3_MARGINALS.jsonl#L751) |
| candidate_06 | saliency_maxent_ht_emp_h3_reinit_top10.0p / 1500 | decoder.final_norm | fixed_original_base | [0.796193 [0.773834, 0.817420]](candidates/candidate_06/H3_MARGINALS.jsonl#L756) |
| candidate_07 | saliency_maxent_ht_emp_h3_reinit_top15.0p / 1500 | decoder.layers.16 | independent_refit | [0.952843 [0.942694, 0.962329]](candidates/candidate_07/H3_MARGINALS.jsonl#L481) |
| candidate_07 | saliency_maxent_ht_emp_h3_reinit_top15.0p / 1500 | decoder.layers.16 | fixed_original_base | [0.830239 [0.809817, 0.850330]](candidates/candidate_07/H3_MARGINALS.jsonl#L486) |
| candidate_07 | saliency_maxent_ht_emp_h3_reinit_top15.0p / 1500 | decoder.final_norm | independent_refit | [0.844653 [0.824403, 0.864283]](candidates/candidate_07/H3_MARGINALS.jsonl#L751) |
| candidate_07 | saliency_maxent_ht_emp_h3_reinit_top15.0p / 1500 | decoder.final_norm | fixed_original_base | [0.803296 [0.781216, 0.823931]](candidates/candidate_07/H3_MARGINALS.jsonl#L756) |
| candidate_08 | saliency_maxent_ht_emp_h3_reinit_top20.0p / 1500 | decoder.layers.16 | independent_refit | [0.954493 [0.944372, 0.963989]](candidates/candidate_08/H3_MARGINALS.jsonl#L481) |
| candidate_08 | saliency_maxent_ht_emp_h3_reinit_top20.0p / 1500 | decoder.layers.16 | fixed_original_base | [0.833758 [0.813028, 0.853682]](candidates/candidate_08/H3_MARGINALS.jsonl#L486) |
| candidate_08 | saliency_maxent_ht_emp_h3_reinit_top20.0p / 1500 | decoder.final_norm | independent_refit | [0.841663 [0.821675, 0.862018]](candidates/candidate_08/H3_MARGINALS.jsonl#L751) |
| candidate_08 | saliency_maxent_ht_emp_h3_reinit_top20.0p / 1500 | decoder.final_norm | fixed_original_base | [0.795684 [0.773041, 0.817090]](candidates/candidate_08/H3_MARGINALS.jsonl#L756) |
| candidate_09 | saliency_maxent_ht_emp_h3_reinit_top5.0p / 1500 | decoder.layers.16 | independent_refit | [0.952515 [0.941971, 0.962207]](candidates/candidate_09/H3_MARGINALS.jsonl#L481) |
| candidate_09 | saliency_maxent_ht_emp_h3_reinit_top5.0p / 1500 | decoder.layers.16 | fixed_original_base | [0.828243 [0.807029, 0.848552]](candidates/candidate_09/H3_MARGINALS.jsonl#L486) |
| candidate_09 | saliency_maxent_ht_emp_h3_reinit_top5.0p / 1500 | decoder.final_norm | independent_refit | [0.841345 [0.821258, 0.861211]](candidates/candidate_09/H3_MARGINALS.jsonl#L751) |
| candidate_09 | saliency_maxent_ht_emp_h3_reinit_top5.0p / 1500 | decoder.final_norm | fixed_original_base | [0.802462 [0.780259, 0.822984]](candidates/candidate_09/H3_MARGINALS.jsonl#L756) |

NPZ_write_seconds includes serialization, fsync and exact readback validation; synchronized_forward_capture_seconds includes model forward, hook pooling, actual-head loss and host copies. GPU stage wall time also includes initialization/loading/I/O and is not billed utilization. Producer/audit retries are additional optimizer calls; valid completed-call reuse never repeats a fit.
