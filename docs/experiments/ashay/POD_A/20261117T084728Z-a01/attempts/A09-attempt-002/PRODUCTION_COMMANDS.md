# Actual A09 commands and exact recovery entry

The following standalone command completed the fresh report recovery. Its argv,PID/start identity,exit codes and times are in BACKUP_VERIFICATION.json and FRESH_RESTORE_CHECK.json.

```bash
/workspace/venvs/pod-a-tools/bin/python -B /workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A09-attempt-002/code/fetch_restore9.py --receipt /workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A09-attempt-002/REPORT_PAYLOAD_UPLOADED.json --destination /workspace/recovery/POD_A/20261117T084728Z-a01/A09-attempt-002/report-fresh-001 --cpu-python /workspace/venvs/a03-cpu-audit-20261117/bin/python --plot-python /workspace/venvs/pod-a-a08-figures/bin/python
```

For a new server, first restore required inherited archives from RECOVERY_DEPENDENCY_GRAPH.json and verify their hashes/member manifests. Supply a JSON archive-SHA256-to-restored-consumer-root mapping using --dependency-roots. Use a new --destination; a nonempty prior attempt is rejected. Required interpreter versions and hard per-worker limits are in ENVIRONMENT_CHECK.json and RESTORE.md. Download/auth uses the tools environment; numerical/render children remove credentials and producer PYTHONPATH,disable GPU visibility,and enforce32GiB address space and4threads. No fit/model forward/bootstrap draw is authorized.

The committed code/plot9.py --input plot_data/main_figures.json --output NEW_DIRECTORY reproduces all4 main layouts with the qualified plotting interpreter. code/render_report9.py --root PUBLIC_REPORT_ROOT --figures NEW_DIRECTORY --output NEW_REPORT_DIRECTORY produces the14-page PDF and page previews. These commands were executed through launch9.py; source identities and exactargv are preserved privately under control/jobs. Earlier failed layout/source-reader attempts remain preserved in the archive and repair log.
