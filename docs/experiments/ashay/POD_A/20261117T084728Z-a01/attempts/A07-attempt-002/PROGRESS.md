# A07 R5 other-five — RUNNING

gue_tf_0: 78 heads and applications accepted; fresh task recovery PASS (12 paths, 240 paired vectors).

Observed UTC: 2026-11-18T22:18:40.858077+00:00. Prompt `112bd37081f5e55896057c6046195e8603c5e751`; A06 input handoff `ba340d0f4706b1941f62a4d6256bf78ab99030eb`.

| Measure | Count |
|---|---:|
| planned_heads | 390 |
| producer_heads | 79 |
| producer_applications | 79 |
| prediction_paths | 158 |
| independently_released_new_heads | 0 |
| recovery_protected_heads | 78 |
| recovered_panel_paths | 12 |
| remaining_heads | 311 |
| initial_solver_calls | 1264 |
| actual_solver_calls | 1264 |
| retries | 0 |
| historical_released_heads | 2418 |
| historical_released_applications | 2418 |
| primary_LM_reused | 42 |
| shared_controls_reused | 36 |
| R2_heads_missing | 468 |
| R2_applications_missing | 468 |
| R2_primary_LM_missing | 7 |
| new_GPU_forwards | 0 |
| new_H3_fits | 0 |
| new_LM_aggregations | 0 |
| new_control_fits | 0 |
| new_adjacent_rows | 0 |

All new units remain COMPLETE_UNVERIFIED pending A08. Producer acceptance and sampled computational recovery do not release the full grid. Original A06 H3/LM and prior attempts remain immutable. R2 gaps and domain-specific R3 eligibility persist.

No deadline, GPU cap or closure reserve; original start, rental start, rate and cost remain unknown. CPU only, two workers, four BLAS threads each, 32 GiB AS each. Observer/reviewer/scheduler/publisher stay stopped; Pod stays running. No A08 execution.

See [inputs](A07_INPUTS.json), [manifest](A07_EXECUTION_MANIFEST.json), [expected keys](EXPECTED_TABLE_KEYS.json), [audit plan](A08_AUDIT_HANDOFF_PLAN.json), and [source](CPU_SOURCE_IDENTITY.json).

Next: Continue the finite R5 A07 queue only.
