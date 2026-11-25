# Unsent request for Sayyed

**DRAFT ONLY — not sent. Aggregate-only outputs and provenance; no raw forget examples, sequences, per-example predictions or losses.**

Sayyed, the benign layerwise analysis is verified for all nine supplied checkpoints. To associate your forget measurements with it, please provide an aggregate result table/report and enough metadata to identify each evaluated checkpoint/content and exact endpoint, config/tokenizer (or a verified artifact mapping), task/split/cohort, protocol/version, readout and representation scope, metric definition/direction/units, supplied estimate precision and denominator. Please state any sharing restrictions.

For reference comparisons, please include the exact reference checkpoint and compatible evaluation definition. If uncertainty was computed, include its type/level/method/resampling/conditioning; otherwise say that it was not computed. An identified point can still be described without an interval.

For the original layerwise request, please distinguish actual layerwise probe results from a whole-model/output-head score, and supply hook/index definitions when available. Zero-based block16 is the seventeenth decoder block; final normalization is separate. A global score will not be counted as26 layer measurements.

For stronger causal/selectivity interpretations only, the remaining needs are immediate parents, intervention algorithm/timing, masks/realized dose, exposure and independent replication. These do not block the current retain-only report. We can already report the complete verified benign evidence; we cannot yet report measured forgetting, a retain–forget trade-off or successful selective unlearning.

Please keep these exact endpoints separate; full typed config/tokenizer/content bindings and affected conclusions are in EXACT_JOIN_ELIGIBILITY.json and PENDING_FORGET_INPUTS.json:

| Candidate | Supplied label | Step | Logical model-content SHA256 |
|---|---|---:|---|
| candidate_01 | saliency_maxent_ht_emp_h3_add_noise_top10.0p | 1500 | `ba02bd040b1be80ac2308a104cad20a7c802397b6ef3505590c5ecb844d99279` |
| candidate_02 | saliency_maxent_ht_emp_h3_add_noise_top15.0p | 1500 | `57cec2a1c2a0ed999beaa92f54c497e1697031bd2a456730bdab2b0ae5756b90` |
| candidate_03 | saliency_maxent_ht_emp_h3_add_noise_top20.0p | 1500 | `54851a4d9f374f8775661e6bc78421d64d468a606ed5213998c2a8be1ab216d4` |
| candidate_04 | saliency_maxent_ht_emp_h3_add_noise_top5.0p | 2000 | `05b9573e0bd6f4fa7e00dcaedb70a31d2f73ac2d9edc01242ea81212a63a6af0` |
| candidate_05 | saliency_maxent_ht_emp_h3_add_noise_top5.0p | 2151 | `e0e9659ddb315428591abdcf9351dc282d1761e60229ea5318b1f3808f4fa844` |
| candidate_06 | saliency_maxent_ht_emp_h3_reinit_top10.0p | 1500 | `d3a66b9d3344dcaa4499841dd9661e008018c185c82b1d06d1040f87d38f4e70` |
| candidate_07 | saliency_maxent_ht_emp_h3_reinit_top15.0p | 1500 | `a9eff2a1312586e0baf72503840224df9c06a04a535b3a576ee85d6971c92cdd` |
| candidate_08 | saliency_maxent_ht_emp_h3_reinit_top20.0p | 1500 | `eb93bccc3d01d8648c2ca5640a85b22d35107e2937c8d55258647f0e5fdfc4f1` |
| candidate_09 | saliency_maxent_ht_emp_h3_reinit_top5.0p | 1500 | `d5658d3c621c318d752795015aebbc128c6d3a5026e8740e6b3a382a57563d29` |
