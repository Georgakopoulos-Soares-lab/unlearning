# Review findings for the producer

No producer file was modified. These are consumer review findings and schema requests.

1. **High — stage 2 is not yet eligible.** `/workspace/agent-handoff/multiretain-v1/PROGRESS.json` reports `stage2_eligible=false`, no completed scientific units, and pending full repeat/H3 fixed-8 validation. Preserve the fixed physical batch-8 gate; do not consume smoke/partial files as final results.

2. **High — the multi-retain arm remains unidentified.** `/workspace/meeting-artifacts/multiretain-layers-v1/CHECKPOINT_REGISTRY.json` identifies H3-only configs, not a broader retain checkpoint. Do not substitute or relabel H3-only. Required correction: supply the exact broader-retain checkpoint folder/config, parent, retain aliases/proportions, row exposure, and comparable processed-token accounting, or keep the arm blocked.

3. **Medium — authoritative contract status is stale.** `ARTIFACT_CONTRACT.json` still says `BLOCKED_RECOVERY_AUTH`, while the later `PROGRESS.json` and recovery receipt record a verified restore. Producer should update its own status chronology; the consumer has not overwritten the contract. This does not change the fixed-8 gate.

4. **Medium — finalized units need explicit consumer roles and identities.** In each `COMPLETE.json`, add a unique `role` to every checksummed file and a structured `unit` object (`task/split/checkpoint/layer/seed/probe_policy`). Save prediction sequence hashes and sorted class columns in addition to IDs/labels/groups. Declare linear feature/coefficient dtypes and reconstruction tolerance. These additions allow `multiretain_verifier.py` to fail visibly rather than infer semantics.

5. **High — historical launcher comments are not execution evidence.** At `b90fc1853d1d3be79922a98a2649c91c89716637`, `headonly_emp_h3_last_layer.sbatch:45` lacks a shell continuation before the intended 750-step arguments on lines 46-48. The actual log records 300 steps, global batch 8, and initial LR 1e-3. Preserve this discrepancy in any comparison.

6. **Medium — keep uncertainty sources separate.** Report every probe seed and all layers. Bootstrap intervals condition on fitted probes and available groups; they do not include seed/fitting uncertainty, unknown homology dependence, or simultaneous coverage. Missing-class draw rejection counts must remain explicit.

Minimal missing inputs that could change execution/interpretation: exact multi-retain source and retain/exposure/token metadata; any supplied-noise checkpoint's parent, selected fraction, scale, selection rule, and seed; qualified biological grouping evidence. No broad questionnaire or duplicate generic parent question is needed.
