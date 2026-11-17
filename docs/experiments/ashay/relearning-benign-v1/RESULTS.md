# Pod B: relearning checkpoint qualification

The delivered inventory contains **36 distinct adapter payloads: 18 base-labeled and 18 MaxEnt-labeled checkpoints, steps 100–1800**. All passed CPU integrity checks: 200 finite model tensors, 100 adapted modules, rank 16, and one complete sharded storage file per checkpoint. File and tensor-content hashes are recorded. These are adapter-only checkpoints, not standalone models.

**No supplied-adapter capability scores are available yet.** The configs reference `bionemo.evo2.models.evo2_lora.Evo2LoRA`, absent from the pinned historical runtime. A public upstream candidate was found at `NVIDIA-BioNeMo/bionemo-recipes@19ee43214fec23e87916efd468eaa62df47dba3e`; its relationship to the supplied training runtime is unverified and it was not executed. Generic LoRA substitution would leave reconstruction unqualified. Exact loader/source or known-output reconstruction evidence is required.

The configs declare different pretrained parents, but both series' resume paths name the MaxEnt adapter directory. The known base and H3-only parent payloads were reacquired with all 129 historical file hashes matching. This qualifies available parent inputs, without proving the actual initialization/resume chain of these adapter trajectories. No step-zero adapter was present in the18-folder listings. True-start-relative contrasts remain unavailable; step100 is not relabeled as step0.

Actual eligible execution completed:

- Restored and checksum-verified base/H3 14,550 files, controls 446 files, R3 8,199 files, and preservation supplement 86 files into fresh directories.
- Reconstructed the pinned native BioNeMo/Bridge/Core/Torch2.8/cu128/TE2.3 route. Six training-only parent runs passed 162 fixed8 comparisons across 26 representations, repeat/logical-size variants and historical outputs, at unchanged tolerances.
- A further 384-row, six-task training-only forward run passed 28 all-layer/loss/count comparisons against historical outputs.
- Eight training-only probe timing fits completed, without held-out scoring or saved new scientific heads. Ten focused fixed-batch/ledger/architecture tests and 13 archive-safety tests passed.
- Audited all 22,645 frozen cohort rows, exact IDs/hashes, numeric labels, expected splits and cross-split exact/RC exclusion. Historical cohorts were preserved. See DATA_IDENTITY.md for remaining biological identity/group limits.

`COVERAGE.csv` explicitly records all 16,848 potential task/layer/CV-seed cells as blocked; no failed or absent result is counted as complete. The prospective protocol retains seeds 42/17/1234, physical8, fold-local scaling, original C/solver/retry policy, fixed-reference/refitted heads and 2,000 paired exact/RC-group resamples. All inferential intervals would be exploratory, pointwise and conditional on fixed heads; no preservation margin exists.

The larger training-only run took 7.027 s in forward passes (384 rows/48 batches; steady batch median 0.09834 s). That suggests roughly 278 s of steady forward work per 22,645-example model and 2.78 h for 36, before adapter overhead, loading, IO, failed stages and audits. Historical complete fitting/bootstrap timings imply about 42 CPU-hours for 36 models and roughly 15 h if run as the prior serial four-worker schedule. Full coverage cannot be promised from GPU throughput. Any reduced coverage must use the same predeclared steps 100/500/1000/1400/1800 for both series, plus qualified true initial references, chosen before scores.

Uncompressed pooled features alone would occupy 162.8 GB for 36 models. Backups and independent recovery require additional space/time. Provider rental start/rate are unknown; measured GPU-stage time and CPU timings are recorded separately in RESOURCE_LEDGER.json. The scientific cutoff remains 2026-11-17 17:33:21 UTC and closure deadline 20:33:21 UTC.

The initial read-only peer fetch found no published `experiments-ashay-incremental-saliency-v1` remote ref. Integrated reporting is explicitly partial; no peer completion or metric is inferred. Prior verified reference studies remain at 3d82ba6 (base/H3),a745671 (controls),c79ab07 (three-source). Their results are historical references, not relearning measurements.

Recovery packaging and its immutable private roundtrip receipt are documented in BACKUP.md. The Pod remains running. No backbone training, hazardous-task evaluation, new test-set opening, collaborator message, branch merge, force push or hardware/shutdown action occurred.
