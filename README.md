# Genomic Capability Unlearning

A pipeline for **targeted capability unlearning in genomic language models**,
built on Evo-1: locate where a capability lives, remove it, measure the collateral
damage, and try to attack the removal.

Two documents, no more. This one is how to run and extend the pipeline.
[docs/RESULTS.md](docs/RESULTS.md) is the evidence record — every result, with a
`verified` / `unverified` provenance label per number, plus the lessons and open
work.

---

## Read this first

Three findings shape any work built on this.

1. **No configuration reached a usable forget/retain point.** Across 90
   checked-in runs, target removal and general genomic capability trade roughly
   one-for-one. Best forgetting cost 0.144 GUE AUROC; the run that preserved GUE
   forgot 0.006, with a CI straddling zero.
2. **None of the four target capabilities qualified.** A k-mer, composition,
   BLASTp or evolutionary baseline matched or beat the model on every one. So the
   Stage 2 numbers describe removing something the model does not distinctly
   possess — the single biggest caveat in this repository.
3. **The training-free baseline won.** `probe_nullspace` — a closed-form
   projection, no gradient steps — had the best selection score of anything
   tried. Run it first; it is the number your method must beat.

Practical consequences, in order: validate your target against a conventional
baseline ([appendix](#appendix--validating-a-target-task)); always evaluate with
refit probes and downstream tasks, never a frozen probe alone; always report
bootstrap intervals.

---

## Architecture

```
 Stage 1  LOCALIZATION      dataset → layer-wise probes → activation patching
 phase1/                    → localized_layers.json
                                        │ causal layers
                                        ▼
 Stage 2  UNLEARNING        gd | rmu | probe_guided | probe_repr | probe_nullspace
 phase2/                    × {full, localized, probe, random}   (× LoRA)
                            → internal diagnostics + downstream benchmarks
                                        │ unlearned checkpoint
                                        ▼
 Stage 3  ATTACKS           SFT and LoRA relearning over an LR grid
 phase3/
```

`random` is a load-bearing negative control: same parameter count, non-causal
layers. If your method forgets as well in `random` as in `localized`, you are
measuring generic damage, not targeted removal.

---

## Quickstart

```bash
conda env create -f environment.yml && conda activate unlearning
pip install git+https://github.com/evo-design/evo.git      # evo + stripedhyena
pip install -r requirements-extras.txt                     # only for the PLM controllers

python -c "import torch, evo, stripedhyena, safetensors, sklearn; print('ok')"
pytest                                                     # 142 passed, 2 skipped
```

The two skips need a generated artifact absent from a fresh clone. Verified on
Python 3.10 / torch 2.6.0 / scikit-learn 1.7.2.

**Interpreter.** Controllers spawn child processes. No path is hardcoded;
[phase2/project_python.py](phase2/project_python.py) resolves
`$PROJECT_PYTHON` → `$PHASE2_PYTHON` → `sys.executable` → `python3`.

```bash
export PROJECT_PYTHON="$(which python)"
```

Also honoured: `DEVICE` (default `cuda:0`), `BLAST_BIN_DIR` and
`NCBI_CONTACT_EMAIL` (PLM controllers only). Each `run.sh` lists its own
variables at the top.

**Model weights.** Put `evo-1-8k-base` in `./evo-1-8k-base/` (safetensors).
`python env_test.py` runs an end-to-end forward pass; needs the weights and a GPU.

**The `data/` tree is git-ignored** apart from curated results. Everything a
stage *reads* must be rebuilt locally — see
[what to regenerate](#what-to-regenerate).

---

## Retargeting

Everything here was run against Evo-1 and a viral host-tropism / Coronaviridae
target. Moving it is three edits, not a rewrite.

### A different genomic LM

| File | What to change |
|:--|:--|
| [phase1/utils.py](phase1/utils.py) | `load_local_checkpoint`, `read_manifest`, `pad_batch`. Return a model with blocks indexable as `model.blocks[i]` and the rest works unchanged. |
| [phase2/utils.py](phase2/utils.py) | `PROBE_LAYERS` (`range(0,11)`), `RANDOM_LAYER_POOL` (`range(11,31)`), `DEFAULT_LOCALIZED_LAYERS`. |
| [phase2/lora_utils.py](phase2/lora_utils.py) | `inject_lora_all_blocks`, `PooledEvoClassifier` (mean-pooled final normalized states + linear head). |

Two constants you must **re-derive, not inherit**:

- **The trustworthy layer range.** Evo-1 is capped at layers 0-10 because its
  activation norms diverge by ~7 orders of magnitude in bfloat16 above that
  (≈257 at layer 10 → ≈1.8×10⁶ at layer 11). Run
  [phase1/diagnose_features.py](phase1/diagnose_features.py) on your model first.
- **`RANDOM_LAYER_POOL` must stay disjoint from your causal layers**, or the
  negative control is not a control.

The tokenizer is already a parameter — `phase2.utils.tokenize_batch` takes it as
an argument.

### A different target

You need one CSV in the target-manifest schema
(`id,label,split,sequence,source,length`; `label=1` = forget). Then:

```bash
TARGET_ROOT=data/family_targets/<target> TARGET_FAMILY=<Family> bash phase1/run.sh all
```

If your target is not a taxonomic family, write the manifest yourself and run
`bash phase1/run.sh probes` then `patching`.

### First end-to-end run

```bash
bash phase1/run.sh all              # probes + causal layers
bash phase2/run.sh splits           # forget/retain CSVs
bash phase2/run.sh verify_retain    # retain MUST contain general-genomics rows
bash phase2/run.sh probe_nullspace  # training-free baseline — do this first
bash phase2/run.sh gd               # then a trained method
bash phase2/run.sh eval             # internal diagnostics
bash phase2/run.sh benchmark_pilot  # cheap downstream ranking
```

If `verify_retain` reports no general-genomics rows, add them with
[phase2/build_gue_augmented_retain.py](phase2/build_gue_augmented_retain.py)
before training anything.

---

## Stage 1 — Localization

Find the layers that *causally* carry the capability. **Driver:**
[phase1/run.sh](phase1/run.sh) (`manifest`, `baselines`, `probes`, `patching`,
`all`).

```bash
# 1. dataset            -> manifest.csv in the target-manifest schema
python phase1/build_refseq_family_target_dataset.py --out-dir <root> \
  --raw-dir data/refseq_family --target-family <Family> \
  --max-length 512 --windows-per-sequence 4 --seed 42

# 2. conventional baselines — if these match the probes, the capability is
#    composition, not the model. Stop and re-read the appendix.
python phase1/baseline_gc_1gram.py --manifest <m> --out-dir <root>/baselines --feature gc_1gram_length
python phase1/baseline_gc_1gram.py --manifest <m> --out-dir <root>/baselines --feature kmer --kmer-max 4 --kmer-binary

# 3. layer-wise probes  -> <root>/probes/probe_metrics_by_layer.csv + probe weights
python phase1/extract_features.py --manifest <m> --out-dir <root>/features \
  --batch-size 80 --max-length 512 --representation next_norm
python phase1/diagnose_features.py --feature-dir <root>/features --out <root>/features/feature_diagnostics.csv
python phase1/train_probes.py --feature-dir <root>/features --out-dir <root>/probes --c-grid 0.001,0.01,0.1,1

# 4. causal attribution -> localized_layers.json
python phase1/activation_patching.py --manifest <m> --probe-dir <root>/probes \
  --out-dir <root>/activation_patching --split test --n-pairs 16 --layers all --directions both
python phase1/select_localized_layers.py \
  --summary-csv <root>/activation_patching/patching_layer_summary.csv \
  --out <root>/localized_layers.json --stable-layers 0-10 \
  --min-abs-effect 0.05 --relative-threshold 0.25
```

Patching swaps one layer's activations between a positive and a negative sequence
and measures the change in probe probability — causal, unlike probe AUROC. The two
disagree sharply here: layer 0 has the *highest* probe AUROC (0.870) and
essentially *zero* causal effect (0.0002), so picking targets by probe salience
picks the wrong layers.

`localized_layers.json` is the handoff artifact:

```json
{"layers": [5,6,7,8,9], "primary_target_layer": 6,
 "selected_sparse_layers": [5,6,8,9], "stable_layers": [0,"...",10],
 "effect_column": "mean_abs_delta_target_prob", "max_effect": 0.355,
 "threshold": 0.0888, "seed": 42}
```

> If it is missing, `phase2.utils.load_localized_config` silently falls back to
> `[5,6,7,8,9]` and marks the config `source: default_fallback`. **Check that
> field before trusting a run.**

`n_pairs=16` is small — raise it before treating a per-layer ranking as settled.
Findings: [RESULTS.md §4](docs/RESULTS.md#4-stage-1--localization).

The root [run.sh](run.sh) is a separate, older driver reproducing the
viral-vs-plasmid pilot behind
[RESULTS.md §4a](docs/RESULTS.md#4a-viral-vs-plasmid-pilot-probes). Use
`phase1/run.sh` for new work.

---

## Stage 2 — Unlearning

**Driver:** [phase2/run.sh](phase2/run.sh) — run it with no valid target to list
subcommands.

Splits come from `bash phase2/run.sh splits`; by convention `label=1 → forget`,
`label=0 → retain`.

### The five methods

Shared CLI: `--forget-csv --retain-csv --condition --out-dir --run-name --steps
--lr --batch-size --max-length --seed --grad-clip --save-steps --device`.

| Key | Script | Forget objective | Retain anchor | Trains |
|:--|:--|:--|:--|:--|
| `gd` | [unlearn_gd.py](phase2/unlearn_gd.py) | **ascend** next-token CE | descend CE on retain | `--condition` layers |
| `rmu` | [unlearn_rmu.py](phase2/unlearn_rmu.py) | push activations toward a steering direction | representation MSE vs frozen ref | `--condition` layers |
| `probe_guided` | [unlearn_probe.py](phase2/unlearn_probe.py) | squared probe **logit** (`logit_zero`) or **component** (`component_zero`) | `hidden_mse` / `output_kl` / `ce` | probe target layers |
| `probe_repr` | [unlearn_probe_repr.py](phase2/unlearn_probe_repr.py) | squared standardized probe component | representation MSE + optional cosine | `--condition` layers, loss on target layers |
| `probe_nullspace` | [project_probe_nullspace.py](phase2/project_probe_nullspace.py) | **none — training-free** projection into the probe null space | n/a | localized layers, closed form |

LoRA is a *parameterization*, not a method — any of the five runs over adapters
via [lora_utils.py](phase2/lora_utils.py). That is what the archived `lora_*` runs
are.

**Conditions** — which parameters receive gradient:

| Condition | Layers | Role |
|:--|:--|:--|
| `full` | all 32 blocks | upper bound on effect and damage |
| `localized` | from `localized_layers.json` | the hypothesis under test |
| `probe` | 0-10 | probe-salience comparison (`gd`, `probe_repr`) |
| `random` | matched count, disjoint pool | **negative control** |

`gd` is the classic formulation,
`loss = -alpha_forget*CE(forget) + alpha_retain*CE(retain)`. It is **unbounded
below**, which is why archived runs pushed retain perplexity from 4.2 to 37.9;
`--forget-loss-cap` bounds the forget term (default `0.0` = disabled, reproducing
archived behaviour). `--init-ckpt` / `--init-from-run` chain interventions, e.g.
projection first then gradient training.

`probe_repr` and `probe_guided --forget-objective component_zero` compute the same
forget loss; they differ in what they train and in retain terms. Consolidating
them is open work.

### Checkpoint contract

Each run writes `<out-dir>/<run-name>/`: `weights.safetensors` (with a
`checkpoint_policy` metadata key), `meta.json` (config + provenance),
`log.json` (per-step objective components).

`checkpoint_policy` is auto-detected on load by
[checkpoint_io.py](phase2/checkpoint_io.py): `selected_modules` (default),
`delta`, `adapter`, `full`, `standalone_lora_reverse`. Saves are atomic and
disk-gated — a full disk fails the save rather than truncating a 30-hour run.

---

## Stage 2b — Evaluation

Two tiers. **Only the downstream tier supports conclusions.**

**Internal diagnostics** — fast, diagnostic only:

```bash
python phase2/eval_unlearn.py --ckpt <ckpt> \
  --internal-target-config phase2/internal_eval_targets.json \
  --forget-csv data/phase2/splits/forget.csv --retain-csv data/phase2/splits/retain.csv \
  --layers 0-15 --fresh-probe
```

Writes `eval_auroc.csv`, `eval_ppl.json`, `eval_representation.csv` into the
checkpoint directory. **Always `--fresh-probe`**: a fixed probe can be defeated by
rotating the representation without removing the information. Report
`separability = max(AUC, 1-AUC)` — a probe driven below 0.5 is still decoding.

**Downstream benchmarks** — authoritative:

```bash
bash phase2/run.sh benchmark_pilot     # subsampled, rank candidates
bash phase2/run.sh benchmark_full_top  # promote top-k
bash phase2/run.sh benchmarks          # base + every checkpoint, full manifest
```

[eval_benchmarks.py](phase2/eval_benchmarks.py) applies one fixed protocol to
every model: fresh LoRA adapters across all blocks, fresh linear head over
mean-pooled final normalized states, early-stop on validation, report test
metrics. `--training-mode` selects `lora` (default) or `full_ft`. The frozen-probe
variant lives in
[eval_benchmarks_probe_legacy.py](phase2/eval_benchmarks_probe_legacy.py) and
[eval_taxonomy_heldout.py](phase2/eval_taxonomy_heldout.py) (these take
`--layers`; `eval_benchmarks.py` does not).

Groups come from the manifest `group` column: `primary_forget` / `hvue_forget`
(want **down**), `secondary_forget` (down), `gue_retain` (**unchanged**),
`viral_retain` (unchanged — but see the caveat below).

Rank with `rank_benchmark_pilot.py` / `aggregate_hvue_lora.py`;
`full_rankings.csv` carries bootstrap CIs. **Report them.**
`selection_score = balanced_forget − max(0, −gue_delta)`.

> **Two rules.** (1) Do not mix `global_host_tropism` checkpoints with
> Coronaviridae-family checkpoints in one ranking — different targets. Confirm
> both `meta.json` agree on `forget_csv` and `retain_csv` first. (2) The
> `viral_retain` group is degenerate as implemented: all six ViroBench tasks are
> multiclass, report no AUROC, and fall back to macro-F1 (base 0.045). It does not
> enter `selection_score`, and `viral_delta` is not interpretable.

Before any formal claim: `check_split_validity.py`, `eval_taxonomy_heldout.py`,
`probe_validity_audit.py`, `probe_vs_sft.py`. The downstream-first re-audit
workflow is `phase2/downstream_reaudit.py` (`audit` → `write-commands` → run →
`aggregate`); only `selective_unlearning_candidate` is a pass state.

---

## Stage 3 — Relearning attacks

A capability an adversary can cheaply restore was suppressed, not removed.

```bash
bash phase3/run_attacks.sh data/phase2/checkpoints_tuned   # LR grid
bash phase3/run_attacks.sh summary                         # best-LR table
```

[attack_sft.py](phase3/attack_sft.py) (full fine-tune, CE, LR `5e-6..2e-5`) and
[attack_lora.py](phase3/attack_lora.py) (LoRA on localized layers, `5e-5..2e-4`)
fine-tune on **held-out** target sequences and report probe AUROC before/after.
The driver picks the LR that *maximizes* recovery — an adversary who tunes.

A richer recipe set is `DEFAULT_ATTACK_DISTRIBUTION` in
[next_steps_common.py](phase2/next_steps_common.py), with matching result fields
`RESULT_SCHEMA_FIELDS`. **No Stage 3 results are checked in — the largest open
gap.**

---

## Sweeps

```bash
python phase2/run_task2_sweeps.py <selectors> --config phase2/sweep_configs/<cfg>.json \
  --out-dir <root> --device cuda:0 --dry-run     # always dry-run first
```

```json
{"experiments": [
  {"group": "g", "name": "run_name", "method": "rmu",
   "args": {"condition": "full", "target_layer": 6, "lr": 5e-6, "steps": 200}}]}
```

`args` keys become `--kebab-case` flags, so a new method needs no driver change.
Selectors are aliases or group names from the config. Progress is resumable via
`sweep_progress.json`. Existing configs cover the RMU layer scan, RMU tuning,
RMU/LoRA Pareto search, the LoRA grid, and three projection variants.

---

## Data contracts

1. **Target manifest** (Stage 1 → 2): `id,label,split,sequence,source,length`
2. **Benchmark manifest** (Stage 2b): requires `split,sequence,label`; optional
   `benchmark,task,group,family,id,split_type`. Asking for a `--split-type` a
   manifest lacks is an error, not a silent no-op.
3. **`localized_layers.json`** — shape above.
4. **Checkpoint** — `weights.safetensors` + `meta.json` + `log.json`.

### What to regenerate

| Path | Produced by |
|:--|:--|
| `data/family_targets/<target>/` | `bash phase1/run.sh all` |
| `data/host_tropism*/` | `phase1/build_host_tropism_dataset.py`, `phase2/prepare_hiyata_host_tropism.py` |
| `data/phase2/splits/` | `bash phase2/run.sh splits` |
| `data/benchmarks/` | `bash phase2/run.sh prepare_benchmarks` |
| `data/phase2/kmer_baselines/` | `phase2/eval_kmer_baseline.py` |
| `./evo-1-8k-base/` | external download |

Check state before anything expensive: `bash phase2/run.sh audit`,
`python phase2/audit_storage_state.py`.

**Provenance.** [run_metadata.py](phase2/run_metadata.py) stamps each `meta.json`
with git commit, dirty flag, runtime, resolved args and input SHA-256s. This
applies to **new** runs only — none of the 90 archived `meta.json` files has a
`commit_hash`, so no existing artifact can be tied to its code version.

**Resumability.** Benchmarks take `--resume`; sweeps track `sweep_progress.json`;
the attack driver skips completed outputs. Watchdog wrappers restart crashed runs.

---

## Cost

| Stage | Per checkpoint |
|:--|:--|
| Stage 1 features + probes | ~1 GPU-hour per target |
| Stage 2 unlearning run | 5 min – 1 GPU-hour |
| Stage 2b **pilot** benchmark | ~2.1–2.3 GPU-hours |
| Stage 2b **full** benchmark | **~32–36 GPU-hours** |
| Stage 3 attack, per LR | ~1–2 GPU-hours |

Full suite: 38 tasks / 1,670,176 rows (2 primary forget, 3 secondary, 33 GUE
retain, **0 viral retain**). Sweep wide → screen internally → rank on the pilot →
promote only the top-k.

---

## Adding your own method

A new method is one script reading the standard splits and writing a standard
checkpoint. Evaluation, sweeps, ranking, audits and attacks then apply unchanged.

**Required flags** (the driver passes these by name): `--forget-csv --retain-csv
--out-dir --run-name --device --batch-size --max-length --save-steps --condition
--seed`. Anything else is yours.

Start from the closest existing method: [unlearn_gd.py](phase2/unlearn_gd.py)
(loss-space), [unlearn_rmu.py](phase2/unlearn_rmu.py) (representation-space,
hook-based), [unlearn_probe_repr.py](phase2/unlearn_probe_repr.py) (probe-directed
with trainable layers decoupled from loss layers), or
[project_probe_nullspace.py](phase2/project_probe_nullspace.py) (closed-form,
shortest complete example).

The five things your script must do:

1. Load the model **plus a frozen reference copy** for the retain anchor.
2. Select trainable parameters from `--condition` using
   `phase2_utils.get_localized_layers` / `select_random_layers` /
   `set_block_grad`, so your `random` control is matched the same way as everyone
   else's.
3. Train, logging **each objective term separately** into `log.json` — the only
   way to tell "the retain anchor is not binding" from "the forget term
   saturated".
4. `checkpoint_io.save_checkpoint(..., policy=..., min_free_disk_gb=10.0)`.
5. `write_metadata(..., build_run_metadata(...))`. A result without `meta.json`
   is uncitable.

Register it in `METHOD_SCRIPT` in
[run_task2_sweeps.py](phase2/run_task2_sweeps.py), add a sweep config that
**includes the controls**, and add a test.

**Tests** are CPU-only and ~1 minute. Stub heavy dependencies with
`register_stub` from [tests/_stub_support.py](tests/_stub_support.py), never by
assigning into `sys.modules` — pytest collects every module into one process, so
an unconditional stub leaks and breaks unrelated tests. That is a bug this
repository actually had. Skip (don't fail) when a generated artifact is missing,
with the path in the reason. Prefer extracting the objective into a pure function
(see `gd_loss_terms`) so the math is testable without a GPU.

**Then validate scientifically** — passing tests only means it runs:

- [ ] beats `project_probe_nullspace.py` on the same target
- [ ] `random` control forgets materially less than `localized`
- [ ] evaluated with `--fresh-probe`, reported as separability
- [ ] conclusions from downstream `eval_benchmarks.py`, not probe AUROC
- [ ] bootstrap CIs reported
- [ ] `verify_retain` passes
- [ ] survives `phase3/run_attacks.sh` at the adversary-optimal LR
- [ ] result added to [docs/RESULTS.md](docs/RESULTS.md) with its artifact path

Read [RESULTS.md § Lessons](docs/RESULTS.md#lessons--pitfalls-this-project-already-hit)
before starting. Every item there cost GPU time here.

### Protein language models

No PLM unlearning path exists yet; the PLM work here is target validation only
(ESM2, ESM-1b, SaProt). Model-agnostic and reusable as-is:
`signed_bootstrap.py`, `run_metadata.py`, `checkpoint_io.py`,
`next_steps_common.py`, `check_split_validity.py`. You must replace the loader,
the tokenizer, the hook location (`hook_location="next_norm"` is Evo-specific),
the layer trust range, and the baselines — for proteins the bar is BLASTp, HMMER
and evolutionary predictors, not k-mer. Split discipline is where all three PLM
studies failed: position-held-out for ProteinGym, proteome/genus-cluster holdout
for PHIStruct and EvoMIL.

---

## Repository layout

```text
phase1/   Stage 1 — datasets, layer-wise probes, activation patching
phase2/   Stage 2 — unlearning methods, evaluation, sweeps, audits,
          target-qualification controllers;  sweep_configs/ holds sweep JSON
phase3/   Stage 3 — SFT and LoRA relearning attacks
tests/    142 regression tests, no GPU required
tools/    plotting helpers
docs/     RESULTS.md — the evidence record
results/  compact top-level result tables
figures/  published figures (mapped in RESULTS.md)
data/     checked-in result artifacts for 90 unlearning runs
```

| Entry point | Role |
|:--|:--|
| [phase1/run.sh](phase1/run.sh) · [phase2/run.sh](phase2/run.sh) · [phase3/run.sh](phase3/run.sh) | stage drivers |
| [phase2/run_task2_sweeps.py](phase2/run_task2_sweeps.py) | config-driven sweeps |
| [phase2/eval_unlearn.py](phase2/eval_unlearn.py) · [phase2/eval_benchmarks.py](phase2/eval_benchmarks.py) | internal / downstream evaluation |
| [phase2/eval_kmer_baseline.py](phase2/eval_kmer_baseline.py) | the shortcut baseline to beat |
| [phase2/build_gue_augmented_retain.py](phase2/build_gue_augmented_retain.py) | add GUE rows to the retain split |
| [phase2/signed_bootstrap.py](phase2/signed_bootstrap.py) | paired grouped bootstrap |
| [phase2/checkpoint_io.py](phase2/checkpoint_io.py) · [phase2/run_metadata.py](phase2/run_metadata.py) | checkpoint policies, provenance |
| [phase2/downstream_reaudit.py](phase2/downstream_reaudit.py) | downstream-first re-audit |
| [phase2/aggregate_lora_kmer_comparison.py](phase2/aggregate_lora_kmer_comparison.py) · [phase2/plot_results.py](phase2/plot_results.py) | model-vs-baseline table, diagnostics plots |

---

## Known limitations

- **`data/` inputs are not in git** — corpora, manifests, Stage 1 artifacts
  (including `localized_layers.json`), splits and weights. Regenerate them.
- **No archived run records its code version** (0 of 90 `meta.json` have
  `commit_hash`).
- **Some documented numbers have no checked-in artifact** — labelled `unverified`
  in RESULTS.md.
- **`viral_retain` is degenerate**; viral-retain evaluation is effectively
  unsolved (vGUE was never converted into a task table).
- **`probe_repr` / `probe_guided` overlap**; consolidation open.
- **Test coverage is uneven** — CLI/metadata/IO plus the GD objective; RMU and the
  probe objectives have no math-level tests.
- **Forget and retain gradients are never separated** — every method calls
  `.backward()` once on the combined loss, so gradient-space interference is
  unmeasured. See [RESULTS.md § Open work](docs/RESULTS.md#open-work).
- **Layers 11+ of Evo-1 are numerically unreliable** in bfloat16.

---

## Appendix — validating a target task

Only relevant if you are *choosing* a target. If yours is decided, skip this.

An unlearning result is meaningful only if the capability removed is genuinely the
model's. If a k-mer count, GC fraction, BLAST hit or evolutionary predictor
already matches the model, the measured "removal" is dominated by whatever else
the intervention broke.

> A target **qualifies** only if the model shows reproducible, model-specific
> headroom over the **strongest reasonable non-foundation baseline**, under the
> **intended out-of-distribution evaluation**.

Four targets were tested here — HVUE/Evo, ProteinGym/ESM2, PHIStruct/SaProt,
EvoMIL/ESM-1b — and **all four failed**
([RESULTS.md §5](docs/RESULTS.md#5-stage-0--benchmark-qualification)).

**Pick the right comparator.**

| Task type | Comparator | Implementation |
|:--|:--|:--|
| DNA classification | k-mer logistic regression (k=1..4), GC + length | [eval_kmer_baseline.py](phase2/eval_kmer_baseline.py), [baseline_gc_1gram.py](phase1/baseline_gc_1gram.py) |
| Protein family / host | BLASTp, HMMER as sanity floor | [phistruct_qualification.py](phase2/phistruct_qualification.py) |
| Proteome-level | AA 3-mer TF-IDF, composition | [evomil_esm1b_qualification.py](phase2/evomil_esm1b_qualification.py) |
| Mutation effect | VESPA, VESPAl, S2F_MSA | [proteingym_esm2_qualification.py](phase2/proteingym_esm2_qualification.py) |
| Taxonomic labels | taxonomy-only predictor | [report_taxonomy_shortcut.py](phase2/report_taxonomy_shortcut.py) |

Three ways a baseline gets weakened, all inflating apparent headroom: capping
training samples (fit on the **full** split); a narrow `C` grid; and — the one
that decided the HVUE verdict — **truncating the baseline to the model's context
window.** Matched-input k-mer scores 0.8555 AUROC, full-sequence 0.8930, Evo
0.8911. The model leads by +0.036 against the handicapped baseline and is
level-or-behind against the fair one. Report both.

**Use a strict split.** Random splits leak; all four studies looked positive on
`random` and failed under the intended protocol. Use taxonomy-, cluster- or
position-held-out (`eval_taxonomy_heldout.py`, `check_split_validity.py`). Note a
split on `virus_tax_id` is species-like holdout, **not** family-held-out; and a
single-family task with no taxonomy columns admits no held-out check at all.

**Report an interval.** Use [signed_bootstrap.py](phase2/signed_bootstrap.py) —
paired, resampled at the leakage unit rather than the row, sign-consistent
`delta = model − baseline`, invalid replicates reported. The headline forget drop
of 0.0057 with CI `[-0.0064, +0.0185]` reads as a small success as a point
estimate and is zero with the interval.

Record the decision as `QUALIFIED`, `UNQUALIFIED`, `NO_QUALIFYING_HEADROOM`,
`<NAME>_FAILURE_NOT_STATISTICALLY_RESOLVED`, or `IN_PROGRESS` (never reportable),
with the comparator, delta and CI, and commit the summary JSON.

**Why all four failed**, which predicts the next candidate: composition carries
more signal than expected; homology is a very strong protein baseline (BLASTp
0.475 macro-F1 on 7-way phage host prediction); evolutionary information is
already in the public baselines, so a PLM's real advantage is not needing an MSA —
a cost argument, not headroom; random-split gains are leakage; and surviving
headroom was seed-unstable. Prefer targets not reducible to composition or
homology.

---

MIT — see [LICENSE](LICENSE).
