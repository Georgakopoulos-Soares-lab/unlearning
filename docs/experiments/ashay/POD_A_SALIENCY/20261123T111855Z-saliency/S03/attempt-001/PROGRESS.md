# S03 partial technical qualification

Two distinct candidate contents were recovered and locally qualified; one is recovery-qualified for S04 planning. Seven other native shards are blocked by normal Google Drive full-file quota responses. The unique-model count across all nine is unknown. No endpoint was selected from outcomes.

| Candidate | Observed label / step | Local qualification | Recovery / S04 |
|---|---|---|---|
| candidate_01 | add_noise_top10.0p / 1500 | PASS | Eligible |
| candidate_02 | add_noise_top15.0p / 1500 | PASS | Fresh model quota blocked |
| candidate_03 | add_noise_top20.0p / 1500 | Native quota blocked | Not admitted |
| candidate_04 | add_noise_top5.0p / 2000 | Native quota blocked | Not admitted |
| candidate_05 | add_noise_top5.0p / 2151 | Native quota blocked | Not admitted |
| candidate_06 | reinit_top10.0p / 1500 | Native quota blocked | Not admitted |
| candidate_07 | reinit_top15.0p / 1500 | Native quota blocked | Not admitted |
| candidate_08 | reinit_top20.0p / 1500 | Native quota blocked | Not admitted |
| candidate_09 | reinit_top5.0p / 1500 | Native quota blocked | Not admitted |

All25decoder blocks plus final normalization pass width1920/finite/pooling/masking checks. Block16 is zero-based decoder.layers.16, the17thblock. Ten finite GPU units used exactly12frozen TRAIN rows, physical8,50physical batches/400rows,280fillers excluded. All per-coordinate batch/repeat comparisons pass `abs(observed-reference)<=1e-4+1e-5*abs(reference)`: worst scaled residual 0.011695370224, boundary1. Worst absolute batch/LM-sum residual6.103515625e-05; all three original-base historical TRAIN anchor comparisons are exactly0. Actual512-vocabulary LM-logit witnesses pass causal targets and FP32sequence/FP64corpus arithmetic; worst independent LM residual9.39743745221e-06. No task score ranking or scientific outcomes are reported.

All468original-base heads (six tasks×26representations×CVseeds42/17/1234) pass exact artifact/fold/producer/class/preprocessing joins and structural/TRAIN formula checks at CPU atol1e-10,rtol0, maximum residual0. H3uses3fold, other tasks5; classifier RNG42 is separate from CVseed. All36shared composition/forward4mer controls pass scoped checks. No refits, target recentering, heldout arrays or test forwards. R3's historical1092classifier/7LM bridge remains source-bound; R5 remains independently released and was not rerun.

Accepted research input bodies total58,996,077,180bytes in the exact scope in RESOURCE_CALIBRATION.json, excluding packages/compiler, route probes/HTML and transport overhead. Peak GPU allocated3222700032bytes/reserved4060086272bytes; peak hostRSS5793148KiB. Ten workers total465.135s wall/101.520s GPU-stage wall. These are not GPU-busy/billed time or production throughput. Provider rate/start/cost and total physical network bytes remain unknown. Persistent allocation1000GB; shared free space is not account quota.

Full pilot-native private upload failed storage quota. Contract-permitted compact protection passed: runtime checkpoint8ef16935e5057e1e6497aa2a0c83af828c77d82a, qualification001af4cccd8477ea40f152e60f22dea0778512aa200, qualification002023633fbfbe6512d7909a4bdf33beae1e2d37a82. Each received a forced fresh network download and exact member hash/set verification; qualification consumers reran CPU comparisons. Pilot fresh15.5GB source reacquisition plus private metadata strict model/smoke replay matches exactly0. Candidate02fresh source recovery failed quota before native bytes; producer cache fallback was denied. No full clean-runtime recreation or private raw-weight preservation is claimed. Immutable Drive revisions are unavailable; future source availability is not guaranteed.

Original POD_A, normal/published prompt checkouts, S00–S02, all older attempts and PodB remain preserved. Prompt package7007ebd05bf59432bf69109e5f69baad31ec0d3a, manifest SHA3b089d6b7d7ab16812272a500519db269050c855f0a0f29e3333752d9a62a5e9; supplemental file fromca827c4bfb3cd4121f8ceadcae6f25446e00857a is byte-identical to preparedf0dfbe673cacef522e8559e696c8922db83fcb7d, SHAe30b8a4475203e72025c3091cb9a880f16942ed30ec867ae93be5a854ea5a0a2. Model source published at3c6bdaf6430277c4a3f9ebcdb7c5796f18514285, source identitydeca2bc52950427f0810dfc657c8dfd4fb175241f9135438e71ba48c017e4c89.

See EXECUTION_FAILURES.json for original exits, caught unit failures and repairs; FINAL_PROCESS_RECONCILIATION.json for drained work and unlocked owned locks. No scientific work or S04 execution occurred. Final delivery commit and final private metadata backup are recorded externally after publication to avoid self-reference.

WAITING_FOR_APPROVAL: S04
