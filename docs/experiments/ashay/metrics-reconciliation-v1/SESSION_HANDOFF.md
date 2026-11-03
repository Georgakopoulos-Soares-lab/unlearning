# Reconciliation handoff

Prompt v11@9c9d13ac1a5fe3a68dcadb1de6d76ba1b1805a2b. Branch experiments-ashay-metrics-reconciliation-v1 starts89c7e93; older dirty retain worktree preserved. Read COMPARABILITY.md for exact blockers. No model inference, probe fitting or predictions produced. GPU0 seconds; no experiment jobs observed. No pushes/messages/shutdown.

Checks actually run:
- train: NLL=sum/targets; PPL=exp(NLL) passed
- dev: NLL=sum/targets; PPL=exp(NLL) passed
- test: NLL=sum/targets; PPL=exp(NLL) passed
- CSV produced with 174 metric records and explicit evidence levels.
