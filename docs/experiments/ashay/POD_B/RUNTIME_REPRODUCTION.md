# B04 reproduction and implementation limits

Reusable code is in `scripts/sayyed/pod_b_runtime/{contracts.py,gate.py,__init__.py}` with focused tests in `tests/test_pod_b_runtime_contracts.py`. It implements a fail-closed manifest/tensor/output gate and a source-pinned native-backend interface. **No native inference backend or scientifically qualified route is included.** No generic LoRA substitution, embedding resize, head slicing, optimizer resume, fitting or generation of an original-route baseline is implemented.

From a research POD_B checkout, the existing CPU interpreter can rerun the disposable contract suite:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 /workspace/venvs/evo2-pilot/bin/python -m unittest discover -s tests -p test_pod_b_runtime_contracts.py -v
```

This command runs synthetic CPU checks only. It does not construct a BioNeMo model, import a candidate adapter, acquire the GPU lock or create scientific qualification evidence. The source is portable through the published research commit; the absolute interpreter path is a current-Pod mapping, not a complete environment image.

The real-case preflight entrypoint is:

```bash
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 /workspace/venvs/evo2-pilot/bin/python -m scripts.sayyed.pod_b_runtime.gate preflight --plan /workspace/meeting-artifacts/POD_B/B04-runtime-20261117T095758Z/B04_QUALIFICATION_PLAN.json --checkpoint-id base/iter_0000100 --binding /workspace/meeting-artifacts/POD_B/B04-runtime-20261117T095758Z/NO_AUTHORITATIVE_BINDING.json
```

Expected current result is exit2/`IDENTITY_BLOCKED`, before reading a missing binding or importing a native backend. All six planned representatives were exercised this way. A `PASS_MANIFEST_PREFLIGHT_ONLY` would still not be scientific qualification: provenance truth requires authoritative review and a pinned binding hash, plus all native numerical gates.

An eventual source-authenticated backend must implement `load`, `snapshot`, `forward`, `set_adapter_enabled` and `close`. Snapshot accounting includes every native parent tensor/buffer, all200 adapter keys exactly once, head identity, eval/gradient/optimizer flags, transient state and load generation. Forward outputs carry exact IDs/sequence digests, all26 coordinates, actual full-vocabulary logits, canonical loss sums/counts, token/position/target masks, physical/logical/filler metadata, hook calls and actual native adapter-branch calls. `contracts.py` defines the required schema. Sources, inputs and same-state original fixture hashes must be frozen in the plan; changing them invalidates the deterministic gate key.

The matrix controller compares the same state with its original reference, repeats, logical1/8 at physical8, final partial batch, hook neutrality, disabled adapter versus the qualified parent, same-parent A→B→A swap and a separate fresh process. It never requires equality between different checkpoints. Source/native algebra still needs real backend execution; synthetic validator tests cannot fill that gap. R0 first-fixture generation and route-only inheritance without per-payload same-state fixtures remain explicitly unimplemented/unqualified at this blocked boundary.

Before any future native execution, renewed B04/B06 authorization must be running and match the execution plan. The original cutoff must leave a full bounded job plus verification time. New scoped GPU config/ledger files must be prepared and hashed; the existing shared lock serializes ownership while old ledgers are read/preserved, not reset. Cache/temp paths must all point to new stage directories, with bytecode writes disabled. Matrix and fresh workers are separate bounded processes; owned timeout cleanup cannot kill unrelated processes. None of this native execution path ran in B04.

`ENVIRONMENT_LOCK.json` records the actual preserved Python/Torch/DCP CPU import, package/build/CXX-ABI metadata, interpreter/Torch_C hashes, system-default nvcc13.2, driver/H100 facts and clean recorded source HEADs. Torch's CUDA build is12.8. No new environment, wheel set, ABI repair or candidate import occurred. Future candidate compilation needs an explicitly compatible pinned toolchain after identity/reference prerequisites clear; do not upgrade the working environment or system CUDA opportunistically. A package list alone is not a self-contained reproduction guarantee.

Private CPU tensor reports, raw listings, tests/logs and helper snapshots live under the new B04 artifact root and need B09-approved packaging. The old private929-file qualification archive preserves historical adapters/qualification, not new B01–B04 evidence, parent weights or installed environments. Public source/blob/commit pointers remain independently recoverable. No new off-Pod restore verification is claimed.
