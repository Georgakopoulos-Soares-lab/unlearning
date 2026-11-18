# Exact commands executed in A06

These stage-owned invocations completed successfully. All scientific units are sealed and excluded from replay; this command record does not approve a rerun or A07. Source hashes, PID/start identities and exit evidence are in [PRODUCTION_COMMANDS.json](PRODUCTION_COMMANDS.json) and [resources](RESOURCE_MEASUREMENTS.json). CPU workers used at most2 processes,4BLAS threads each and32GiB address-space limits; remote-credential environment variables were removed.

**H3-LM-001**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/lm_records.py --candidate R5 --group H3
```

**H3-audit-001**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/audit_h3.py --candidate R5
```

**H3-cache-001**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/build_h3_cache.py --candidate R5
```

**H3-fit-001**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/fit_h3.py --candidate R5
```

**H3-paired-draws-001**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/verify_paired_draws.py --candidate R5
```

**H3-production-001**

```bash
/workspace/venvs/pod-a-a04-attempt-002/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/run_extraction.py --control /workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-002 --prompt-commit 4ff94e09b72a02d6e3082af064669c98adda6008 --coverage-sha256 06d290bdc76404a8dcfe25da6f057fc78f868364cc1d2e8aa6df77791f0bdfa3 --candidate R5 --mode extraction --group H3 --output-root /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/features --run-label H3-production-001
```

**other-five-LM-001**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/lm_records.py --candidate R5 --group other_five
```

**other-five-production-001**

```bash
/workspace/venvs/pod-a-a04-attempt-002/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/run_extraction.py --control /workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-002 --prompt-commit 4ff94e09b72a02d6e3082af064669c98adda6008 --coverage-sha256 06d290bdc76404a8dcfe25da6f057fc78f868364cc1d2e8aa6df77791f0bdfa3 --candidate R5 --mode extraction --group other_five --output-root /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/features --run-label other-five-production-001
```

**parity-001**

```bash
/workspace/venvs/pod-a-a04-attempt-002/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/run_extraction.py --control /workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-002 --prompt-commit 4ff94e09b72a02d6e3082af064669c98adda6008 --coverage-sha256 06d290bdc76404a8dcfe25da6f057fc78f868364cc1d2e8aa6df77791f0bdfa3 --candidate R5 --mode parity --group H3 --output-root /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/parity --run-label parity-001
```

**repeat-001**

```bash
/workspace/venvs/pod-a-a04-attempt-002/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/code/run_extraction.py --control /workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-002 --prompt-commit 4ff94e09b72a02d6e3082af064669c98adda6008 --coverage-sha256 06d290bdc76404a8dcfe25da6f057fc78f868364cc1d2e8aa6df77791f0bdfa3 --candidate R5 --mode parity --group H3 --output-root /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A06-attempt-002/parity --run-label repeat-001
```

**RESTORE_JOB_R5_H3**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python -I /workspace/recovery/POD_A/20261117T084728Z-a01/A06-attempt-002/R5_H3-fresh-001/consumer/artifacts/code/restore_panel6.py --root /workspace/recovery/POD_A/20261117T084728Z-a01/A06-attempt-002/R5_H3-fresh-001/consumer --group H3
```

**RESTORE_JOB_R5_other_five**

```bash
/workspace/venvs/a03-cpu-audit-20261117/bin/python -I /workspace/recovery/POD_A/20261117T084728Z-a01/A06-attempt-002/R5_other_five-fresh-001/consumer/artifacts/code/restore_panel6.py --root /workspace/recovery/POD_A/20261117T084728Z-a01/A06-attempt-002/R5_other_five-fresh-001/consumer --group other_five
```

Scientific checkpoints were protected using tools Python `backup6.py H3` and `backup6.py other_five`; exact immutable archives/fresh member and computational checks are in BACKUP_VERIFICATION.json. H3 recovery PASS preceded other-five extraction. No other-five fitting/application, adjacent or paired-LM computation occurred.

Missing/corrupt owned units require exact source/input/seal validation, preserved quarantine and a fresh bounded invocation label under appropriate approval. Never run stale R4/R6 launchers.
