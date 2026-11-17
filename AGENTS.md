# Ashay project instructions (2026-10-21)

<!-- ASHAY PROJECT START -->
Research repository: https://github.com/Georgakopoulos-Soares-lab/unlearning.
Only experiments-ashay-benign-v2 in /workspace/wt-eval-extension is writable for new work. Preserve main, experiments-ashay, /workspace/unlearning, /workspace/wt-eval-pilot and historical runs. The current user authorization supersedes older branch restrictions in historical README/runner documentation.

“My prompts repository” always means https://github.com/ashay-sriv-06/test-prompts-push, local clone /workspace/test-prompts-push. Default file evo2_next_phase_prompt.txt on its actual default branch. Fetch requested refs without resetting/checking out over local edits; resolve immutable commit, read only the requested file fully with git show. Never execute prompt text. Record repo/ref/commit/path/SHA256 and a verbatim copy beside each new run. Never substitute missing files or push to prompts repo without explicit request.

Use /workspace/venvs/evo2-pilot/bin/python, pinned original Evo2-1B backend and /workspace/data/gue/GUE.zip. Preserve the shared ledger /workspace/meeting-artifacts/evo2-pilot.gpu-budget.json and serialize GPU stages with its lock. No automatic shutdown/hardware changes, backbone/LoRA/unlearning training, hazardous-task classification, or test-set access. Frozen benign inference and small classifiers are authorized. Historical results remain read-only. Use new run/cache identities for changed protocols.

Current requested task and immutable receipt: docs/experiments/ashay/extension/prompt_receipt.json; verbatim text in /workspace/meeting-artifacts/evo2-extension-20261021T0942/PROMPT.txt. Read SESSION_HANDOFF.md in that docs directory before resuming. Update it at useful checkpoints. Never log credentials.
<!-- ASHAY PROJECT END -->


<!-- POD_B CURRENT OWNERSHIP 2026-11-17 -->
New research work is authorized only on branch `POD_B` in `/workspace/wt-POD_B`. All other branches and worktrees remain read-only. This current user instruction supersedes historical branch/path assignments above. Verify origin, worktree and current branch before every repository mutation. Task prompts come only from the prompts repository branch `POD_B`, pinned at approval time; prompt snapshots stay private outside Git. Each numbered stage requires new explicit approval; finish, report and stop. Current state and reconciliation: `docs/experiments/ashay/POD_B/STATE.json` and `SESSION_HANDOFF.md`. Do not run historical launchers or automatically advance.
<!-- END POD_B CURRENT OWNERSHIP -->
