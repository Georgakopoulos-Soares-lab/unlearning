# S06: complete other-five feature and LM foundation

All nine frozen candidates are represented in their original order. The S04 scientific freeze and no-deadline amendment are unchanged. S06 performs no classifier fitting, fixed-head application, intervention training, candidate ranking, forgetting evaluation or S09 contrast.

## Exact coverage

| Quantity | New S06 | Reused S05 H3 | Combined |
|---|---:|---:|---:|
| Extraction bundles | 90 | 18 | 108 |
| Logical row executions | 69,120 | 121,212 | 190,332 |
| Representation matrices | 2,340 | 468 | 2,808 |
| Primary dev LM units | 45 | 9 | 54 |
| Diagnostic TRAIN LM units | 45 | 9 | 54 |
| LM metric records | 180 | 36 | 216 |

All 360 exact frozen S06 specification keys join to verified receipts: 90 extraction, 90 LM, 180 LM-metric records. These dependent specifications are not independent experiments. All 26 representations are retained, including zero-based `decoder.layers.16` (17th block) and `decoder.final_norm`.

Successful production: 270 chunks, 8640 physical batches, 69120 physical rows, 0 fillers. Each task/candidate has exact TRAIN 1,024 and dev 512 rows. Splice dev retains 512 rows and 511 exact/RC groups, with all three classes. No deduplication or new sampling.

## Numerical and recovery evidence

Maximum independent LM point/draw/interval absolute residual across original and fresh restored checks: `0.0`; fixed `atol=1e-12`, `rtol=0`. FP32 per-row loss sums and integer valid target counts feed a token-weighted FP64 corpus ratio; PPL exponentiates that ratio. Padding/fillers are excluded. The actual causal head has 512 logits.

Numeric metric estimates: 180/180. Scientifically valid explicit-null estimates: 0. Available dev metric intervals: 90/90; explicitly unavailable zero-valid-draw intervals: 0. TRAIN has no bootstrap intervals. Each task uses its original exact 2,000 group draws/IDs/mapping and seed20261103; no new draws. Intervals are 95% pointwise exploratory conditional, without multiplicity adjustment or biological/intervention independence guarantees.

Every new candidate checkpoint is independently protected: full exact regular-member set/size/SHA verification from fresh immutable HTTPS download, followed by restored-code readers over all ten bundles/all260matrices, all ten LM point pairs/allfive dev uncertainty outputs, and resolution of390future refits plus390fixed applications. No producer path fallback. Existing qualified CPU interpreter is external; this does not demonstrate new fitting/head application, GPU recreation, clean-runtime installation or new native-weight backup.

## All primary dev standalone LM measurements

Full precision, masks, denominators, missingness and source-linked receipts are in `LM_MARGINALS.jsonl`; TRAIN diagnostics are included there. Rows below follow the frozen candidate/task order and do not rank interventions.

| Candidate | Task | NLL | NLL 95% interval | PPL | PPL 95% interval |
|---|---|---:|---|---:|---|
| candidate_01 (saliency_maxent_ht_emp_h3_add_noise_top10.0p, step 1500) | gue_tf_0 | 1.3419113 | 1.3274571 – 1.3548905 | 3.8263497 | 3.7714407 – 3.8763363 |
| candidate_01 (saliency_maxent_ht_emp_h3_add_noise_top10.0p, step 1500) | gue_prom_core_all | 1.388393 | 1.383388 – 1.3929269 | 4.0084035 | 3.9883913 – 4.0266185 |
| candidate_01 (saliency_maxent_ht_emp_h3_add_noise_top10.0p, step 1500) | gue_prom_300_all | 1.3870276 | 1.381181 – 1.3917687 | 4.0029341 | 3.9795988 – 4.0219574 |
| candidate_01 (saliency_maxent_ht_emp_h3_add_noise_top10.0p, step 1500) | gue_splice_reconstructed | 1.2995335 | 1.2842118 – 1.314229 | 3.6675853 | 3.61182 – 3.7218805 |
| candidate_01 (saliency_maxent_ht_emp_h3_add_noise_top10.0p, step 1500) | gue_mouse_0 | 1.3844722 | 1.3794595 – 1.3887232 | 3.9927179 | 3.9727538 – 4.0097273 |
| candidate_02 (saliency_maxent_ht_emp_h3_add_noise_top15.0p, step 1500) | gue_tf_0 | 1.3421362 | 1.327817 – 1.3552324 | 3.8272105 | 3.7727982 – 3.877662 |
| candidate_02 (saliency_maxent_ht_emp_h3_add_noise_top15.0p, step 1500) | gue_prom_core_all | 1.3882965 | 1.3833234 – 1.3926731 | 4.0080164 | 3.9881337 – 4.0255965 |
| candidate_02 (saliency_maxent_ht_emp_h3_add_noise_top15.0p, step 1500) | gue_prom_300_all | 1.3873007 | 1.3813026 – 1.3923339 | 4.0040273 | 3.9800828 – 4.0242312 |
| candidate_02 (saliency_maxent_ht_emp_h3_add_noise_top15.0p, step 1500) | gue_splice_reconstructed | 1.2988364 | 1.2835449 – 1.3134646 | 3.6650297 | 3.6094121 – 3.7190364 |
| candidate_02 (saliency_maxent_ht_emp_h3_add_noise_top15.0p, step 1500) | gue_mouse_0 | 1.3842266 | 1.3791108 – 1.3884599 | 3.9917376 | 3.9713688 – 4.0086714 |
| candidate_03 (saliency_maxent_ht_emp_h3_add_noise_top20.0p, step 1500) | gue_tf_0 | 1.3423013 | 1.3279372 – 1.3552956 | 3.8278424 | 3.773252 – 3.8779072 |
| candidate_03 (saliency_maxent_ht_emp_h3_add_noise_top20.0p, step 1500) | gue_prom_core_all | 1.388821 | 1.383759 – 1.3931682 | 4.0101195 | 3.9898714 – 4.0275901 |
| candidate_03 (saliency_maxent_ht_emp_h3_add_noise_top20.0p, step 1500) | gue_prom_300_all | 1.3888147 | 1.3828958 – 1.3937317 | 4.010094 | 3.9864289 – 4.0298602 |
| candidate_03 (saliency_maxent_ht_emp_h3_add_noise_top20.0p, step 1500) | gue_splice_reconstructed | 1.2990144 | 1.283524 – 1.3137467 | 3.6656819 | 3.6093366 – 3.7200855 |
| candidate_03 (saliency_maxent_ht_emp_h3_add_noise_top20.0p, step 1500) | gue_mouse_0 | 1.3852436 | 1.3801275 – 1.389478 | 3.9957991 | 3.9754086 – 4.0127548 |
| candidate_04 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2000) | gue_tf_0 | 1.34696 | 1.3328942 – 1.3598112 | 3.8457167 | 3.7920022 – 3.8954576 |
| candidate_04 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2000) | gue_prom_core_all | 1.3925425 | 1.3874923 – 1.396968 | 4.0250708 | 4.0047945 – 4.0429231 |
| candidate_04 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2000) | gue_prom_300_all | 1.4358707 | 1.42737 – 1.4440906 | 4.2033031 | 4.1677237 – 4.2379964 |
| candidate_04 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2000) | gue_splice_reconstructed | 1.3362666 | 1.3198683 – 1.3516346 | 3.804812 | 3.7429283 – 3.8637361 |
| candidate_04 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2000) | gue_mouse_0 | 1.3931918 | 1.3878589 – 1.3976523 | 4.0276852 | 4.006263 – 4.0456906 |
| candidate_05 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2151) | gue_tf_0 | 1.3472907 | 1.3332334 – 1.3601711 | 3.8469887 | 3.793289 – 3.89686 |
| candidate_05 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2151) | gue_prom_core_all | 1.3928003 | 1.3876943 – 1.3972473 | 4.0261086 | 4.0056038 – 4.0440527 |
| candidate_05 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2151) | gue_prom_300_all | 1.4504869 | 1.4404874 – 1.4600511 | 4.2651907 | 4.2227533 – 4.3061794 |
| candidate_05 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2151) | gue_splice_reconstructed | 1.3446846 | 1.3274194 – 1.3607397 | 3.8369762 | 3.7712984 – 3.8990763 |
| candidate_05 (saliency_maxent_ht_emp_h3_add_noise_top5.0p, step 2151) | gue_mouse_0 | 1.3942593 | 1.3889586 – 1.3987269 | 4.031987 | 4.0106714 – 4.0500405 |
| candidate_06 (saliency_maxent_ht_emp_h3_reinit_top10.0p, step 1500) | gue_tf_0 | 1.3420403 | 1.3278508 – 1.3550092 | 3.8268433 | 3.7729257 – 3.8767965 |
| candidate_06 (saliency_maxent_ht_emp_h3_reinit_top10.0p, step 1500) | gue_prom_core_all | 1.3883085 | 1.3832633 – 1.3926945 | 4.0080647 | 3.987894 – 4.0256825 |
| candidate_06 (saliency_maxent_ht_emp_h3_reinit_top10.0p, step 1500) | gue_prom_300_all | 1.3869663 | 1.3809699 – 1.3919401 | 4.0026887 | 3.9787587 – 4.0226468 |
| candidate_06 (saliency_maxent_ht_emp_h3_reinit_top10.0p, step 1500) | gue_splice_reconstructed | 1.2988706 | 1.2835041 – 1.3133089 | 3.6651549 | 3.609265 – 3.7184573 |
| candidate_06 (saliency_maxent_ht_emp_h3_reinit_top10.0p, step 1500) | gue_mouse_0 | 1.3846369 | 1.3795642 – 1.3888906 | 3.9933756 | 3.9731697 – 4.0103983 |
| candidate_07 (saliency_maxent_ht_emp_h3_reinit_top15.0p, step 1500) | gue_tf_0 | 1.3418462 | 1.3276162 – 1.3549164 | 3.8261009 | 3.7720408 – 3.8764371 |
| candidate_07 (saliency_maxent_ht_emp_h3_reinit_top15.0p, step 1500) | gue_prom_core_all | 1.388663 | 1.3836399 – 1.3929549 | 4.0094856 | 3.9893962 – 4.0267313 |
| candidate_07 (saliency_maxent_ht_emp_h3_reinit_top15.0p, step 1500) | gue_prom_300_all | 1.3881749 | 1.3822897 – 1.3930385 | 4.0075292 | 3.9840132 – 4.0270676 |
| candidate_07 (saliency_maxent_ht_emp_h3_reinit_top15.0p, step 1500) | gue_splice_reconstructed | 1.2997067 | 1.2844839 – 1.3142792 | 3.6682207 | 3.6128028 – 3.722067 |
| candidate_07 (saliency_maxent_ht_emp_h3_reinit_top15.0p, step 1500) | gue_mouse_0 | 1.3846568 | 1.3795739 – 1.3889161 | 3.993455 | 3.9732082 – 4.0105007 |
| candidate_08 (saliency_maxent_ht_emp_h3_reinit_top20.0p, step 1500) | gue_tf_0 | 1.3426816 | 1.3284203 – 1.3558742 | 3.8292985 | 3.7750753 – 3.8801514 |
| candidate_08 (saliency_maxent_ht_emp_h3_reinit_top20.0p, step 1500) | gue_prom_core_all | 1.3883453 | 1.383236 – 1.3927517 | 4.0082121 | 3.9877854 – 4.025913 |
| candidate_08 (saliency_maxent_ht_emp_h3_reinit_top20.0p, step 1500) | gue_prom_300_all | 1.3891284 | 1.3832424 – 1.3939705 | 4.0113521 | 3.9878109 – 4.0308226 |
| candidate_08 (saliency_maxent_ht_emp_h3_reinit_top20.0p, step 1500) | gue_splice_reconstructed | 1.2996601 | 1.2843187 – 1.3141795 | 3.6680496 | 3.612206 – 3.7216961 |
| candidate_08 (saliency_maxent_ht_emp_h3_reinit_top20.0p, step 1500) | gue_mouse_0 | 1.3848438 | 1.3798361 – 1.3891026 | 3.9942018 | 3.9742503 – 4.0112486 |
| candidate_09 (saliency_maxent_ht_emp_h3_reinit_top5.0p, step 1500) | gue_tf_0 | 1.3420158 | 1.3277841 – 1.35514 | 3.8267497 | 3.7726741 – 3.8773037 |
| candidate_09 (saliency_maxent_ht_emp_h3_reinit_top5.0p, step 1500) | gue_prom_core_all | 1.3888977 | 1.3837851 – 1.3932729 | 4.010427 | 3.9899753 – 4.0280117 |
| candidate_09 (saliency_maxent_ht_emp_h3_reinit_top5.0p, step 1500) | gue_prom_300_all | 1.388489 | 1.3824659 – 1.3934555 | 4.0087883 | 3.9847154 – 4.0287472 |
| candidate_09 (saliency_maxent_ht_emp_h3_reinit_top5.0p, step 1500) | gue_splice_reconstructed | 1.2988656 | 1.2834498 – 1.3134279 | 3.6651368 | 3.6090688 – 3.7189 |
| candidate_09 (saliency_maxent_ht_emp_h3_reinit_top5.0p, step 1500) | gue_mouse_0 | 1.3844827 | 1.3794276 – 1.3887409 | 3.9927598 | 3.9726271 – 4.0097981 |

## Recovery pointers

| Candidate | Immutable private revision | Archive SHA256 |
|---|---|---|
| candidate_01 | `f389ed573d034fd80180207bd517debdee81c5d2` | `9b4c0aabc4726a840e658d41264abe75a93a0f95e908b9b2e2c5fdc82b009005` |
| candidate_02 | `15736f312dff14361e822c4bd9a0fb24f6e5cb2a` | `936b66b5b777523e95652a92b0c4a17985129cd8bcac4d7e56b2b6bc24ee6772` |
| candidate_03 | `de07146b55e45daefacd6c9faa700641d9f9f957` | `72617b492fd51f727cc43b37884f5c23384972ab534c0cfc7ea1a03768e779f1` |
| candidate_04 | `50d8589f087dcc4f68b311d3bd06980a9b454ec5` | `53756143ca36c24885994f2410833228835f2201cfa60477d3bb03a01f76957c` |
| candidate_05 | `3aa90b072b3361044c349d64ddf91d8d0a111c49` | `55d62417b01dac0c7bc0ff61bb76c61665e6a630f28d604e40031c5d9c3d148d` |
| candidate_06 | `7d15bcfb697fdbe7d4c0f3923d344e24473ade28` | `f85e1351d7960ed31478f2927d49a2e1e5000892f307196270e44f8e82b0c6f0` |
| candidate_07 | `6433bee39c118f055dc530e1cb5bec982beef4a9` | `62646ffeb4ec8408707da5398ab4da578b344e76964a4036ce9b2f6c8ae2309f` |
| candidate_08 | `9d5b22fb198d2e10fe3f02a771a46e0b9d85b917` | `6839b3d249f5c4e937a4bda547c6e36b349f59b605e8b7d6d574c75e7d892b50` |
| candidate_09 | `ab111a486975ba0c2c9459969c99240784386f9a` | `d8d8d86c5d418918b801b192c4a72e81eb57d1d0a3619547d67f42f3303402e7` |

Exact private repository/object locators and unchanged dependency reacquisition graph remain in private control and protected final metadata; public receipts bind their hashes.

## Resources and preserved failures

Measured synchronized forward/capture time: 698.993s; extraction process wall time: 1377.294s. These are not billing or GPU-busy duration. Peak allocated/reserved GPU bytes: 3222700032/3997171712; peak GPU-worker host RSS: 5904134144 bytes. Each CPU worker remained under8GiB. Current allocation accounting and every next-case admission retained a64GiB storage reserve and48GiB host headroom. S05 consumption is part of the initial baseline, not a new allowance. Rate, rental start, billing, transport overhead and exact unused provider quota remain unknown at the stated scopes.

Candidate application upload bytes: 12189661123; fresh HTTPS body readback bytes: 12189661123. Failures and repairs remain in `EXECUTION_FAILURES.json` and private command logs; no failed attempt is erased or relabeled successful. No blanket file scan, shutdown or unrelated-process termination.

## Remaining scientific dependencies

- Immediate parents unproved: No arbitrary reference difference is intervention-causal. Resolver: S09/S10 exact parent evidence.
- Masks/intervention law/strength units incompletely established: Folder percentages are declarations, not calibrated comparable doses. Resolver: S10 collaborator metadata.
- Actual exposure/objectives and endpoint history incomplete: Method/dose/duration/parent may be confounded; keep noise5 steps2000/2151 distinct. Resolver: S10 provenance.
- Independent intervention seeds unproved: Three future CV seeds measure probe partition sensitivity, not trained-checkpoint replication. Resolver: S09 interpretation/S10 provenance.
- S01 whole-delivery inventory PARTIAL: Nine frozen candidates are exact evaluated scope, not exhaustive delivery. Resolver: External inventory evidence.
- Candidate05 original-upload privacy history unknown: Current private recovery cannot settle historical visibility. Resolver: External provenance.
- Matched aggregate forget evidence absent/separate: Retain measurements do not establish forgetting/selectivity/robustness. Resolver: S10 collaborator aggregates; no raw forget access.
- Exact/RC grouping not biological independence: Pointwise intervals omit training and biological dependencies. Resolver: S09/S10 interpretation.
- Original-base paired per-example LM evidence incomplete: Do not reconstruct paired contrasts from aggregates or silently activate missing edges. Resolver: S09 frozen eligibility.

## Handoff boundary

S07 inputs are technically ready for the nine exact candidates, subject to new direct approval and current admission checks. S07 has 3,510 remaining refits and separately3,510 unchanged-reference applications. Preserve/reuse all702S05 H3 heads/applications and21audits. S08 retains105original remaining audits; S09 retains its original contrast family and missing-edge dispositions.

Read `S07_HANDOFF.json`, each candidate `S07_INPUT_BINDINGS.json`, and the final delivery/private metadata proofs. Stop before S07.

`APPROVE S07 at 7007ebd05bf59432bf69109e5f69baad31ec0d3a`
