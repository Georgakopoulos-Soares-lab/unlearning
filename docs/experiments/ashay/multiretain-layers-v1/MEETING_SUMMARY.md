# Meeting summary

Completed the available base/H3-only benign comparison across six tasks, 25 decoder blocks plus final norm, three training-CV seeds, refitted and fixed-base readouts. All 468 units passed independent saved-output audits; multi-retain remains deferred and noise was not supplied.

At block16/seed42, H3-test refit AUROC increases .935324→.950738; splice-dev macro-OVR decreases .787862→.722105; mouse-TF dev decreases .876947→.834092. Pointwise conditional intervals for all three differences exclude zero under exact/RC grouping. All layers and seeds remain in the report; no optimal held-out layer is claimed.

Fixed-base and refitted readouts differ substantially. H3-test NLL worsens 1.310650→1.455799 despite improved refitted classification. These are checkpoint/readout observations, not a causal result about retain diversity or hazardous-knowledge removal.

To answer the original assignment, obtain the actual broader-retain checkpoint and exact mixture/exposure/token-budget/initialization metadata. Biological grouping and intervention-seed replication remain more valuable than a larger decorative sweep. See [RESULTS.md](RESULTS.md), exact CSVs, full audit receipts and the final private backup receipt.
