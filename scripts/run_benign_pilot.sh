#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
stage="${1:?stage required: preflight|prepare|smoke|pilot|report}"
run_dir="${2:?unique run directory required}"
shift 2
test "$(git branch --show-current)" = experiments-ashay
export HF_HOME=/workspace/.cache/huggingface
export HF_HUB_ENABLE_HF_TRANSFER=0
export PIP_CACHE_DIR=/workspace/.cache/pip
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
export PYTHONUNBUFFERED=1
python_bin="${PILOT_PYTHON:-/workspace/venvs/evo2-pilot/bin/python}"
mkdir -p "$run_dir"
printf '%s %q %q\n' "$(date -u +%FT%TZ)" "$stage" "$run_dir" >> "$run_dir/commands_executed.log"
if [[ "$stage" = smoke || "$stage" = pilot ]]; then
  exec 9>/workspace/meeting-artifacts/evo2-pilot.gpu.lock
  flock -n 9 || { echo 'Another pilot GPU job holds the lock' >&2; exit 73; }
  # timeout owns only its child process group, never the Pod or unrelated jobs.
  seconds="$($python_bin -c 'from datetime import datetime,timezone; print(max(0,min(7200,int((datetime(2026,10,20,15,15,tzinfo=timezone.utc)-datetime.now(timezone.utc)).total_seconds()))))')"
  (( seconds > 0 )) || { echo 'Experiment cutoff has passed' >&2; exit 74; }
  timeout --signal=TERM --kill-after=20s "${seconds}s" "$python_bin" -m benign_pilot.run "$stage" --run-dir "$run_dir" "$@" 2>&1 | tee -a "$run_dir/$stage.log"
else
  "$python_bin" -m benign_pilot.run "$stage" --run-dir "$run_dir" "$@" 2>&1 | tee -a "$run_dir/$stage.log"
fi
