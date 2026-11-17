| Component | Expected | Passed | Failed | Blocked |
|---|---:|---:|---:|---:|
| Package files |31|31|0|0|
| Software checks |26|26|0|0|
| Selected checkpoints |6|4|0|2|
| Training-only variants |18|12|0|6|
| Feature/LM comparison rows |567|378|0|189|
| New scientific measurements, fitted heads, held-out forwards |0|0|0|0|

A04 is **PARTIAL**. **WAITING_FOR_APPROVAL: A05**. Qualified: base, R1, R4, R6. Excluded: R3, R5. R3 and R5 native shards remain unavailable after bounded exact-ID transfer attempts; R5 explicitly reports Drive download quota exceeded. No candidate substitution was made. The next action is separate approval for A05 planning/calibration of the qualified subset, or a separately approved A04 repair of the missing payload dependencies. A05 has not started.

The 12 sealed variants reuse the exact 12 training rows at physical batch 8, with three fresh processes per qualified checkpoint. All 26 hooks and the actual 512-column LM head are checked. Every comparison uses unchanged atol=1e-4/rtol=1e-5, in the pinned direction and also its reverse. Maximum feature residual: 0.0; maximum LM-sum residual: 6.103515625e-05. Full denominators, worst coordinates and violations are in SMOKE_COMPARISONS.csv. Independent actual-logit CE checks, causal masks and length-minus-one target counts are in LM_QUALIFICATION.json. No probe fitting, production extraction or held-out inference occurred.

The prompt is pinned at f3e6b08d203485494611e215144fabe9b936ae1c. SOURCE_IDENTITY.json, ENVIRONMENT_LOCK.json and CHECKPOINT_IDENTITIES.json bind source, runtime and full asset identities. ADAPTER_REUSE_RECORD.json explains why the completed base passes remain valid after the intervention-only metadata repair. All failed setup attempts are retained separately from passed qualification units. Historical A03 artifacts remain unchanged; live family eligibility is listed separately in REUSE_BRIDGE_MATRIX.csv.

RESOURCE_CALIBRATION.json records observed timing, memory and disk. The provider allocation is500GB; the GPU is an H100 NVL. Cost, original start and rental start remain unknown. The explicit time-policy supersession remains active; there is no revived deadline, reserve or GPU cap. Smoke throughput is preliminary and does not forecast full production coverage.

BACKUP_VERIFICATION.json records the bounded private checkpoint, fresh member-by-member restore and CPU comparison/witness checks. Original weights and installed runtime are excluded with exact reacquisition/rebuild references. This is not a fresh GPU rebuild. REMOTE_HANDOFF.json and the separate post-push delivery receipt bind research delivery without a self-hash cycle. At closure all owned compute/transfer/build jobs are quiescent. Use RESUME_MANIFEST.json to resume only missing units after fresh approval; preserve completed receipts. No future-stage worker or scheduler exists.
