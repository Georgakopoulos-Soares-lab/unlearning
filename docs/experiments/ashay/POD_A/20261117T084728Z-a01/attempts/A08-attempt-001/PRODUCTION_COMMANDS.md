# A08 commands and environments

These commands are records, not an automatic resume queue. A08 only was approved. Scientific core version audit-source-001 remains unchanged. GPU visibility is empty; ordinary workers use four BLAS/OpenMP threads and a 32-GiB address-space ceiling.

### analysis-LM-001

PID `54446`, start ticks `10815767`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/analysis_pairs.py --stage A08 --kind LM
```

### analysis-emp_H3-001

PID `53743`, start ticks `10787340`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/analysis_pairs.py --stage A08 --kind classifier --task emp_H3
```

### analysis-gue_mouse_0-001

PID `54424`, start ticks `10812849`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/analysis_pairs.py --stage A08 --kind classifier --task gue_mouse_0
```

### analysis-gue_prom_300_all-001

PID `54112`, start ticks `10804986`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/analysis_pairs.py --stage A08 --kind classifier --task gue_prom_300_all
```

### analysis-gue_prom_core_all-001

PID `54092`, start ticks `10802215`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/analysis_pairs.py --stage A08 --kind classifier --task gue_prom_core_all
```

### analysis-gue_splice_reconstructed-001

PID `54403`, start ticks `10808842`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/analysis_pairs.py --stage A08 --kind classifier --task gue_splice_reconstructed
```

### analysis-gue_tf_0-001

PID `54071`, start ticks `10799355`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/analysis_pairs.py --stage A08 --kind classifier --task gue_tf_0
```

### audit-R4-gue_mouse_0-001

PID `51322`, start ticks `10716013`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R4 --task gue_mouse_0
```

### audit-R4-gue_prom_300_all-001

PID `51266`, start ticks `10709181`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R4 --task gue_prom_300_all
```

### audit-R4-gue_prom_core_all-001

PID `50964`, start ticks `10704730`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R4 --task gue_prom_core_all
```

### audit-R4-gue_splice_reconstructed-001

PID `51295`, start ticks `10712460`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R4 --task gue_splice_reconstructed
```

### audit-R4-gue_tf_0-001

PID `50779`, start ticks `10679774`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R4 --task gue_tf_0
```

### audit-R6-gue_mouse_0-001

PID `52608`, start ticks `10751872`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R6 --task gue_mouse_0
```

### audit-R6-gue_prom_300_all-001

PID `52543`, start ticks `10745435`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R6 --task gue_prom_300_all
```

### audit-R6-gue_prom_core_all-001

PID `52249`, start ticks `10741236`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R6 --task gue_prom_core_all
```

### audit-R6-gue_splice_reconstructed-001

PID `52572`, start ticks `10748632`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R6 --task gue_splice_reconstructed
```

### audit-R6-gue_tf_0-001

PID `52223`, start ticks `10738074`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --candidate R6 --task gue_tf_0
```

### initial-independent-audit-001

PID `50439`, start ticks `10661149`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/audit_units.py --stage A08 --unit R4/gue_tf_0/final_norm/seed42 --unit R4/gue_splice_reconstructed/final_norm/seed42
```

### sampled-refits-R4-001

PID `51624`, start ticks `10720416`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/refit_panel.py --stage A08 --candidate R4
```

### sampled-refits-R6-001

PID `52910`, start ticks `10755988`, state `EXITED_PASS`, exit `0`.

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /workspace/venvs/a03-cpu-audit-20261117/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/refit_panel.py --stage A08 --candidate R6
```

## Rendering and reporting

The isolated figure environment did not alter the frozen audit/runtime environments. Reporting-only changes retained original source spellings, scientific values and private seals while filling exact LM/reference provenance. Rendering revisions corrected exploratory-test legend overlap, header spacing and explicit tight-bbox title inclusion. Final rendering uses completed provenance tables; prior unsealed layout diagnostics are preserved privately. See FIGURE_ENVIRONMENT.json and REPORT_PROVENANCE_NORMALIZATION.json.

```bash
/workspace/venvs/pod-a-a08-figures/bin/python /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A08-attempt-001/code/plot_verified.py --docs /workspace/wt-pod-a/docs/experiments/ashay/POD_A/20261117T084728Z-a01/attempts/A08-attempt-001
```

The saved reporting order is report_tables.py → control_table.py → context_and_analysis.py → enrich_provenance.py → plot_verified.py → complete_plot_keys.py → closeout.py. Regeneration of completed files is unnecessary for reporting reuse. Numerical CLI options were exercised in the actual job records; restore CLI commands are in RESTORE.md.
