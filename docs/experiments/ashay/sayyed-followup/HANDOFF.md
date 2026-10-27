# H3 follow-up handoff

1. **Measured:** original selected head unchanged; three training-only-CV-selected logistic readouts on identical dev/test rows; two fixed additional MLP seeds; whole-sequence paired uncertainty.
2. **New evidence:** selected original head saw 1,842 unique training rows; 4-mers outperform the final-normalized Evo2 logistic probe under this protocol, while Evo2 exceeds composition; original MLP seed sensitivity is reported without selecting a winner.
3. **Supported:** performance depends on readout/training procedure. Additional predictive information relative to composition is conditional on this protocol. No causal biological understanding, unlearning effect, or broad project completion is established.
4. **Uncertain:** biological grouping/homology, unseen deployment distribution, training/selection uncertainty, dataset/converted-backbone/tokenizer parity with BioNeMo. Known test scores make the supplement post-hoc exploratory.
5. **Direct Sayyed comparison ready?** No. Current results are an independent original-backend reference.
6. **Needed:** immutable converted base iteration 1 and trained H3 head iteration 300 weights/checksums; run_config/tokenizer/loader/environment/parent conversion provenance; exact split-ID/sequence-hash/label tables; sampler/selection record. Agree normalization hook, padding, precision, LR curve and decision rule.
7. **Highest-value next experiment:** bounded, predeclared training-only token/hidden-state/logit/head parity check once those files are accessible, before a matched benchmark comparison.

Original input run: /workspace/meeting-artifacts/sayyed-base-20261026-v1 (read-only). Follow-up: /workspace/meeting-artifacts/sayyed-h3-followup-20261027T001154Z. Python: /workspace/venvs/sayyed-base-runtime/bin/python. Branch: experiments-ashay-sayyed-base-v1.

Reproducible CPU entry point from /workspace/wt-sayyed-base (use a fresh output directory for new execution):

```
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup freeze --original /workspace/meeting-artifacts/sayyed-base-20261026-v1 --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup exposure --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 /workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup fit --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup bootstrap --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.verify_h3_followup --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
```

Create the new output directory first. Reusing completed follow-up artifacts requires only the verifier, not refitting or bootstrap regeneration. Optional seed stage must first freeze its amendment; never expand beyond 17/1234.

No additional GPU work was performed; shared ledger 868.753177 / 7200 seconds remains inactive. No experiment job remains after delivery. Private remote backup remains pending replacement securely configured HF credentials. Do not reuse the exposed chat token. The complete local archive, checksum and source/delivery receipts are recorded separately; preserve the original verified backup.

Local supplement: /workspace/meeting-artifacts/sayyed-h3-followup-20261027T001154Z-supplement.tar.gz

SHA256: 19bc96a4513d37f56f77ece0dda189734e92a8c0165dac35aa636f91134b97f5. Its sidecar is /workspace/meeting-artifacts/sayyed-h3-followup-20261027T001154Z-supplement.tar.gz.sha256. All95 payload files passed local archive verification. This is not an uploaded/fresh-downloaded remote backup. The supplement requires the preserved original H3 backup for cached Evo2 features.

Measured successful scientific stages used 90.941 CPU process-seconds, excluding imports, orchestration, failed verifier preflights and setup; additional GPU time was0. No experiment remains active.
