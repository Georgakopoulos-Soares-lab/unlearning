# Inspected A07 production commands

The following exact argv arrays were executed by the bounded A07 controller; successful exit and source identity are in COMMANDS_EXECUTED.json and per-job receipts. The CLI accepts only A07; no GPU, A08 or automatic stage dispatcher exists. Two initial ordinary production units were reused in their later task batches after full seal validation.

`fit-R6-gue_mouse_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R6", "--task", "gue_mouse_0"]
```

`cache-R6-gue_mouse_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R6", "--task", "gue_mouse_0"]
```

`fit-R6-gue_splice_reconstructed-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R6", "--task", "gue_splice_reconstructed"]
```

`cache-R6-gue_splice_reconstructed-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R6", "--task", "gue_splice_reconstructed"]
```

`fit-R6-gue_prom_300_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R6", "--task", "gue_prom_300_all"]
```

`cache-R6-gue_prom_300_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R6", "--task", "gue_prom_300_all"]
```

`fit-R6-gue_prom_core_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R6", "--task", "gue_prom_core_all"]
```

`cache-R6-gue_prom_core_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R6", "--task", "gue_prom_core_all"]
```

`fit-R6-gue_tf_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R6", "--task", "gue_tf_0"]
```

`cache-R6-gue_tf_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R6", "--task", "gue_tf_0"]
```

`fit-R4-gue_mouse_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R4", "--task", "gue_mouse_0"]
```

`cache-R4-gue_mouse_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R4", "--task", "gue_mouse_0"]
```

`fit-R4-gue_splice_reconstructed-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R4", "--task", "gue_splice_reconstructed"]
```

`cache-R4-gue_splice_reconstructed-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R4", "--task", "gue_splice_reconstructed"]
```

`fit-R4-gue_prom_300_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R4", "--task", "gue_prom_300_all"]
```

`cache-R4-gue_prom_300_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R4", "--task", "gue_prom_300_all"]
```

`fit-R4-gue_prom_core_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R4", "--task", "gue_prom_core_all"]
```

`cache-R4-gue_prom_core_all-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R4", "--task", "gue_prom_core_all"]
```

`fit-R4-gue_tf_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--candidate", "R4", "--task", "gue_tf_0"]
```

`cache-R4-gue_tf_0-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/build_other_five_cache.py", "--candidate", "R4", "--task", "gue_tf_0"]
```

`initial-production-001`

```json
["/workspace/venvs/a03-cpu-audit-20261117/bin/python", "/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-001/code/fit_other_five.py", "--stage", "A07", "--unit", "R4/gue_tf_0/final_norm/seed42", "--unit", "R4/gue_splice_reconstructed/final_norm/seed42"]
```
