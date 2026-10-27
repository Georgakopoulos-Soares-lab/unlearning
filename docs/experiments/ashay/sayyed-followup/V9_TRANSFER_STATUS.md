# v9 saved-login transfer check

**Recovery was already complete before v9.** The parent and follow-up were uploaded and fresh-downloaded successfully at the immutable revisions below; their 173 and 95 payload checksums passed. Current saved-login authentication is unavailable, so v9 performed no new remote verification or duplicate upload. The earlier successful receipt remains valid and is not relabeled as a v9 check.

| Archive | Previously verified immutable HF revision | Restore order |
|---|---|---:|
| Original H3 | 117c01edd97d595c68bd04e9d28f3c4c4e9852f1 | 1 |
| Follow-up supplement | dfae7d29f0550430d1c64605501f403445059ff6 | 2 |

The supplement depends on the original cache; it is not self-contained. See [recovery chain](recovery_chain.json) and [prior successful backup receipt](backup_receipt.json).

## Sanitized current diagnosis

HF CLI and library both report 2.3.0. The launcher removed HF_TOKEN and HUGGING_FACE_HUB_TOKEN before importing huggingface_hub in a fresh subprocess; only presence was reported. Both variables were absent in the parent and child.

The CLI and transfer shared effective HF_HOME=/workspace/.cache/huggingface/ and HF_TOKEN_PATH=/workspace/.cache/huggingface/token. No active credential file exists there. Neither active credentials nor stored-token files exist under the standard alternate /root/.cache/huggingface location. No credential contents were inspected or saved. The unspecified separate-terminal login environment cannot be independently attested.

This is **unavailable saved-login authentication**. An authenticated identity was not obtained, so current repository access and upload permissions were not tested. It is not evidence that the private repository was deleted or that an authenticated account lacks access. No exposed token was reused, no repository/visibility change occurred, and no identical failed request was retried.

To establish a login under exactly the transfer configuration, run interactively in the Pod terminal; never paste the token into chat:

```
env -u HF_TOKEN -u HUGGING_FACE_HUB_TOKEN HF_HOME=/workspace/.cache/huggingface/ HF_TOKEN_PATH=/workspace/.cache/huggingface/token /workspace/venvs/sayyed-base-tools/bin/hf auth login
```

## Manual fallback download list

If another independent off-Pod copy is needed while current login is unavailable, download all four existing files into one directory:

- /workspace/meeting-artifacts/sayyed-base-20261026-v1-recovery.tar.gz
- /workspace/meeting-artifacts/sayyed-base-20261026-v1-recovery.tar.gz.sha256
- /workspace/meeting-artifacts/sayyed-h3-followup-20261027T001154Z-supplement.tar.gz
- /workspace/meeting-artifacts/sayyed-h3-followup-20261027T001154Z-supplement.tar.gz.sha256

On the receiving machine, from that directory:

```
shasum -a 256 -c sayyed-base-20261026-v1-recovery.tar.gz.sha256
shasum -a 256 -c sayyed-h3-followup-20261027T001154Z-supplement.tar.gz.sha256
```

On Linux, sha256sum -c can replace shasum -a 256 -c. Both checks must report OK. V9 locally rechecked both archive identities and sidecars successfully; neither archive was changed.

## Source and jobs

Before v9 edits, local and remote HEAD both matched 38af9b0; five required receipt/handoff files matched their committed bytes. No merge, rebase, cherry-pick, index lock or unfinished work was found. The earlier nonzero compound-command result did not leave a failed Git delivery; commit/push and remote HEAD were verified.

No inference, classifier fitting or scientific audit was rerun. No experiment/GPU job is active; ledger 868.753177/7200 seconds remains inactive. Prior off-Pod recovery verification is complete for the completed H3 work; current saved-login access was not reverified. No Pod shutdown occurred.
