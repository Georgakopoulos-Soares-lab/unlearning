The committed recipe is `scripts/sayyed/pod_b_runtime/reproduce.py`; its cache/setup template is `environment.sh.template`. Both are available from this research commit. The recipe reproduces the observed candidate source assembly using trusted existing binary dependencies. It does not acquire a historical job identity, rebuild wheels, run models, or claim a tested restore roundtrip.

Required dependencies, recovered separately before assembly:

- A trusted copy of the preserved Python3.12 binary venv, with the exact installed-root package versions in B04_RUNTIME_DISTRIBUTIONS.json and shared-library identities in B04_BINARY_DEPENDENCY_MANIFEST.json. The whole binary tree is required; these manifests contain no binaries. The former broad ENVIRONMENT_LOCK remains historical: its metadata enumeration included setuptools-vendored distribution metadata. The new lock observes only the retained venv's installed dist-info roots. It changes no package or runtime bytes.
- Read-only local Git checkouts at BioNeMo7dd1659f2103982562d7a23896fb2091200a1f1d, Bridge18ef1b61309dd45bc0535fb7c60064b9d8829a35 and Core92c8482e6dcd11c3666c61bb8d1f7e8d0730ed13.
- Exact official Evo2LoRA file SHA2569b481000249879695c266b2489ac40999732c3e8f81f024027f96b9d972a6af3, Git bloba79acacbd26139dd617b494ac96f8370ec8cdb85, from NVIDIA-BioNeMo/bionemo-recipes@1263f64629ecd27e9333f28923e728c381a9cf2c, path bionemo-recipes/recipes/evo2_megatron/src/bionemo/evo2/models/evo2_lora.py.
- The committed B04_NATIVE_BACKPORT.patch, SHA256ba9225905a35669f30ec59f753ae7cb43c76c3e8e09c416105679badeb8db4ee. Its exact observed build recipe archives each pinned source, copies the official class unchanged and applies this source-justified patch in the new tree. Native normalized-input/bias/scale/eval semantics remain unchanged. The recipe checks exact source pins and official/backport bytes.
- A compatible host/interpreter/driver for the retained Torch2.8+cu128/TE2.3 compiled dependencies. No system CUDA or driver changes are performed. Deep shared-library verification occurs once for an actual `--assemble`, not repeatedly for each native stage. Model parent/adapter/tokenizer manifests and approved training inputs remain separate dependencies.

Set absolute dependency paths, then validate without writing or importing native modules:

```bash
python3 -S scripts/sayyed/pod_b_runtime/reproduce.py --dry-run \
  --output "$NEW_RUNTIME_ROOT" \
  --binary-environment "$RECOVERED_BINARY_ENV" \
  --bionemo-source "$BIONEMO_SRC" --bridge-source "$BRIDGE_SRC" --core-source "$CORE_SRC" \
  --official-lora "$OFFICIAL_EVO2_LORA_FILE" \
  --patch "$RESEARCH_ROOT/docs/experiments/ashay/POD_B/B04_NATIVE_BACKPORT.patch" \
  --environment-lock "$RESEARCH_ROOT/docs/experiments/ashay/POD_B/B04_RUNTIME_DISTRIBUTIONS.json" \
  --binary-manifest "$RESEARCH_ROOT/docs/experiments/ashay/POD_B/B04_BINARY_DEPENDENCY_MANIFEST.json"
```

For an explicitly authorized replacement assembly, use `--assemble` with those same arguments and a nonexistent output directory. This physically copies the trusted venv with no links into originals, archives source pins, applies the exact patch, replaces editable .pth files only in the copy and corrects copied script entry points. It preserves input sources, checkpoints, environments and refs. This follow-up tested the dry-run and invalid-input rejection, not assembly/restore; it did not reinstall the working runtime.

For an existing compatible working runtime, reuse it. Freeze the repaired runner files and three input/pooling/loading helpers into a new immutable runner root. Copy package __init__ files too. Source the committed template after explicitly setting POD_B_ARTIFACT_ROOT to a new run root and POD_B_RUNNER_ROOT to that snapshot. Launch with Python `-P`; workers also use `cwd=runner_root`. Without safe-path execution, an old terminal directory can shadow a pinned helper even when PYTHONPATH is set. Every loaded runner/helper origin and file hash is checked before native execution. Runtime module origins and environment lock are independently pinned in the source manifest.

The inherited aggregate ledger remains `/workspace/meeting-artifacts/POD_B/B04-resume-20261117T121146Z/GPU_LEDGER.json`. Never initialize a zero-use replacement. A new scientific plan must carry the complete producer-bound state, fixture/reference contract, source/environment/module-origin manifest, fixed18:11:46Z forward/18:56:46Z closure deadlines and current counters. The external control record must be B04/RUNNING and bind the exact execution ID, direct approval file, immutable plan digest, root, permitted mode and ledger identity. Reopening a shell or presenting a known prompt hash does not authorize execution. The current follow-up plan is CPU_REMEDIATION with no model cases; it cannot launch native work.

Only after evidence clears and a new complete scientific child plan is approved/live, the executable workflow is:

```bash
"$PINNED_RUNTIME_PYTHON" -P -m scripts.sayyed.pod_b_runtime.qualification preflight --plan "$NEW_SCIENTIFIC_PLAN" --case "$CASE"
"$PINNED_RUNTIME_PYTHON" -P -m scripts.sayyed.pod_b_runtime.qualification run --plan "$NEW_SCIENTIFIC_PLAN" --case "$CASE" --phase matrix --output "$NEW_SCIENTIFIC_MATRIX"
"$PINNED_RUNTIME_PYTHON" -P -m scripts.sayyed.pod_b_runtime.qualification run --plan "$NEW_SCIENTIFIC_PLAN" --case "$CASE" --phase fresh --output "$NEW_SCIENTIFIC_FRESH"
"$PINNED_RUNTIME_PYTHON" -P -m scripts.sayyed.pod_b_runtime.finalize --plan "$NEW_SCIENTIFIC_PLAN" --case "$CASE" --matrix "$NEW_SCIENTIFIC_MATRIX" --fresh "$NEW_SCIENTIFIC_FRESH" --output "$NEW_SCIENTIFIC_RECEIPT"
```

R0 authenticates source/state before creating a first reference and never labels that self-comparison external agreement. R2 additionally verifies an independent original-route metadata/array bundle before allocation, including head, effective config, fixture, ordered IDs, sequence digests and extraction contract. Applicable qualified-route inheritance still requires independent per-job state binding. Scientific finalization verifies actual loaded tensors/config/contract, native source identity, separate observed worker events/PIDs and all required gates; engineering objects cannot be promoted.

Beyond the7,200-second planning threshold, a plan may include `reserve={reason,purpose,maximum_gpu_seconds,evidence_record}`. Purpose is repair or completion; the reason must be concrete and bounded, the cap at most1,800 seconds, and the evidence file hash pinned. Pass the exact same string as `--reserve-reason` to each relevant `run` invocation. A missing, blank, different or unapproved reason fails. The controller records the reason and observed start/end/process/event identities in the original cumulative ledger. The9,000-second hard ceiling,1,800 engineering-only ceiling, remaining allowance and fixed deadlines always apply. Counter-reset requests fail. No reserve was used in this follow-up.

Old engineering outputs, raw arrays, native binary environment and source archives remain local dependencies excluded from old backups. Recovery order: restore verified old inputs/receipts and v7 source snapshots; restore trusted binary/runtime dependencies; restore this follow-up's source/approval/plan/evidence index; validate hashes and status; obtain the missing authoritative facts and a live execution record before fresh qualification. Do not replay closed v6 or promote its arrays. Private remote packaging/restore verification remains B09. Provider rental start, hourly rate and provider termination deadline remain unknown.
