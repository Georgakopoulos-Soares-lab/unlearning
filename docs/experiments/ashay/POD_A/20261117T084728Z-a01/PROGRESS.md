# A07 R5 other-five — RUNNING

gue_mouse_0: 78 heads and applications accepted; fresh task recovery PASS (12 paths, 240 paired vectors).

Observed UTC: 2026-11-18T22:29:40.123891+00:00. Prompt `112bd37081f5e55896057c6046195e8603c5e751`; A06 input handoff `ba340d0f4706b1941f62a4d6256bf78ab99030eb`.

| Measure | Count |
|---|---:|
| planned_heads | 390 |
| producer_heads | 390 |
| producer_applications | 390 |
| prediction_paths | 780 |
| independently_released_new_heads | 0 |
| recovery_protected_heads | 390 |
| recovered_panel_paths | 60 |
| remaining_heads | 0 |
| initial_solver_calls | 6240 |
| actual_solver_calls | 6258 |
| retries | 18 |
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

See [inputs](attempts/A07-attempt-002/A07_INPUTS.json), [manifest](attempts/A07-attempt-002/A07_EXECUTION_MANIFEST.json), [expected keys](attempts/A07-attempt-002/EXPECTED_TABLE_KEYS.json), [audit plan](attempts/A07-attempt-002/A08_AUDIT_HANDOFF_PLAN.json), and [source](attempts/A07-attempt-002/CPU_SOURCE_IDENTITY.json).

Next: Continue the finite R5 A07 queue only.
