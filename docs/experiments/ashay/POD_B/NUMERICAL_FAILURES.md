# B04 failures, rejections and unattempted checks

**No real model numerical comparison was possible.** No native backbone/adapter forward ran. Real-model numerical PASS count0 and numerical FAIL count0 do not mean a successful qualification: all36 complete states remain identity-blocked, and all54 planned representative/matrix gate entries are explicitly unattempted.

The six planned representatives—base100/1800 and MaxEnt100/1600/1700/1800—passed fresh CPU file and adapter-tensor checks. Every real-case executable preflight then returned `IDENTITY_BLOCKED` before native backend import or GPU allocation. These are prerequisite rejections, not six failed neural forwards. The actual missing source/parent/extra-state association and original-route adapter reference remain external evidence gaps.

| Attempt/check | Result | Meaning and next action |
| --- | --- | --- |
| R0 original runtime | NOT_ATTEMPTED / IDENTITY_BLOCKED | Actual job source/runtime/command and complete inference-state bindings not recovered. Cannot relabel the preserved parent stack as R0 or generate a new original reference under guessed code. |
| R2 equivalent runtime | NOT_ATTEMPTED / RUNTIME_BLOCKED | Official source copies/API fields match statically. An independently authenticated same-state original-route adapter fixture and complete state association are missing. No candidate install/build/import/forward was attempted. |
| Selected six adapter files/tensors | PASS_CPU_INTEGRITY_ONLY |1,041,238,896 counted input bytes hashed;1,200 model tensor hashes/shapes/dtypes/finiteness and600 module instances agree with historical records. This does not qualify a full model. |
| Preserved Torch/DCP CPU worker | PASS_CPU_IMPORT_AND_RECOVERY | CUDA context stayed uninitialized. The native model/provider/TE/Hyena path remains untested. |
| Final contract suite |74 tests PASS | Disposable synthetic metadata/vectors/backends; expected invalid cases are rejected. This is not native algebra, a biological forward or an independent original reference. |

The CPU contract suite deliberately presents missing/duplicate/unexpected tensor mappings, incomplete shards, corrupt bytes, wrong dtype/shape, wrong parent or changed buffer, stale adapters/hooks/inference state, disabled adapters, training/optimizer flags, non-training populations, wrong masks/counts/positions, filler leakage, altered vocabulary/token IDs, one outlying layer, nonfinite values, wrong LM reduction, incorrect scaling/bias/normalized-input traces, candidate/parent-only references and stale source/binding hashes. Expected rejection is the test outcome. The owned timeout test stops only its disposable child process group. No private/historical input was corrupted for testing.

The synthetic tiny float64 algebra checks use an independent scalar oracle and a1e-12 test tolerance. They establish validator/control behavior only; they do not claim BF16 native attention/MLP/Hyena execution. Neural same-state smoke gates remain atol1e-4/rtol1e-5, with exact IDs/masks/counts/shapes. Historical probability1e-10 and metric/bootstrap1e-12 gates retain their separate scopes. No tolerance, pooling, precision, model, checkpoint or reference was changed to obtain a neural PASS.

Torch emitted a pynvml deprecation warning and DCP's expected single-process/no-distributed warning. Neither caused a failed tensor check; no unrelated package upgrade was made. Installed Torch is built for CUDA12.8; the system-default nvcc reports13.2. No new extension build was attempted, so this is an unqualified future build-toolchain concern, not an observed adapter ABI failure. The existing environment and host CUDA installation were preserved.

No OOM, failed native build, model-loading failure, hook/branch numerical error, learned-head diagnostic rerun, held-out evaluation or scientific score occurred. Exact CPU commands/source hashes/input hashes and complete logs remain under the B04 artifact root; the finite remedy is in `B04_EVIDENCE_REQUEST.md`.
