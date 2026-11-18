Analysis spec SHA256: `9471098adb38e70a9f9ede6dbe5782a4e379af7bfb697b1fe4b43ae48882bff3`. Formula version: `POD_B.adapter_trajectory.spec.v1`.

Run from the dedicated POD_B worktree using the existing `/workspace/venvs/evo2-pilot/bin/python`; no install, model load or GPU is required. ENVIRONMENT_LOCK.json pins the interpreter version, numerical/plot packages and exact helper/test bytes. SOURCE_SNAPSHOT.json identifies the immutable private source used by bulk geometry. The safe extraction's exact historical source and subsequent strengthening/optimization are retained in the private source-phase history.

Inputs: the original 36 inventoried DCP adapter payloads, `.metadata`, configs and historical CHECKPOINT_REGISTRY.json; the unchanged ANALYSIS_SPEC.json; and the attempt's APPROVAL.json. The private INPUT_MANIFEST.json gives all 7,200 BF16 tensor identities and chunk extents. Public INPUT_MANIFEST.json preserves checkpoint lineage and the private full-manifest hash. No parent checkpoint, dataset, held-out score or classifier artifact is a dependency.

The following are the recorded execution commands (R and O denote this attempt's private artifact root and public documentation root). They describe reproduction, not authorization to launch another attempt. The helpers enforce the recorded scheduling deadline and output ownership. A future rerun requires separately approved fresh identities/window; do not edit this receipt to defeat that guard.

```bash
export CUDA_VISIBLE_DEVICES=''
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/workspace/wt-POD_B
/workspace/venvs/evo2-pilot/bin/python -B -P -m unittest discover -s tests -p test_adapter_trajectory.py -v
/workspace/venvs/evo2-pilot/bin/python -B -P -m scripts.sayyed.adapter_trajectory prepare --run "$R"
/workspace/venvs/evo2-pilot/bin/python -B -P -m scripts.sayyed.adapter_trajectory run --run "$R" --output "$O" --workers 4
/workspace/venvs/evo2-pilot/bin/python -B -P -m scripts.sayyed.verify_adapter_trajectory --run "$R" --output "$O"
/workspace/venvs/evo2-pilot/bin/python -B -P -m scripts.sayyed.plot_adapter_trajectory --run "$R" --output "$O"
```

The deterministic real dense validation is retained privately as `validate_real.py` with its exact source hash in the backup file manifest. It selects the predeclared minimum-block module for each of six target types and three family-covered pairs. The full dense metrics and bounded 64×64 spectral scope are explicitly recorded in VALIDATION.json. Raw failed diagnostics remain alongside corrected results.

Factor caches are reproducible float32 conversions of BF16 inputs and are intentionally omitted from Git and the new small backup. Restoring original adapter inputs requires the existing immutable backup revision and archive in ARTIFACT_DEPENDENCIES.json, plus historical registry/receipts. The new backup is an evidence/analysis package, not a full environment or model-state restore. The bounded fresh readback checks that package's bytes and table/figure content; it does not qualify a model or complete B09.

CSV interpretation: `checkpoint` and `left/right` join exact IDs to ANALYSIS_SPEC.json and INPUT_MANIFEST.json; `module` joins explicit A/B keys, complete layouts, shapes and BF16 lineage in the spec. `edge_id` joins comparison status and job membership; `first_delivered_relative` and `adjacent` remain distinct rows. Every CSV carries the immutable spec hash, which pins the formula version and full input identities. EDGE_METRICS uses the source-supported serialized-operator scope; all U values remain declared-parameterization quantities, not authenticated original runtime updates. `scope=CONDITIONAL_SAME_NOMINAL_COORDINATES` marks cross-series comparisons. Empty cosine-reason fields mean a valid nonzero comparison; no current unit is missing. P/U norm, spectral norm, RMS and distance have parameter units; inner products have squared parameter units; relative distance/cosine/ranks are dimensionless. `singular_values` contains all 16 P singular values, with effective-zero conventions in the spec.

Figures are derived only from the published CSVs. FIGURE_MANIFEST.json binds source hashes, plotting source and all PDF/SVG/PNG exports. `magnitude_trajectory`, `adjacent_distance`, `step_by_block` and `restart_neighborhood` cover all observed steps/blocks or the explicitly registered restart neighborhood; no interpolated model states are presented as observations.
