"""Score a candidate unlearning target against the two-criterion gate.

The rule in the README appendix -- "a target qualifies only if the model shows
reproducible, model-specific headroom over the strongest reasonable non-foundation
baseline" -- is necessary but **not sufficient**. A 22-task audit found six tasks that
pass it and are still useless as targets, because a baseline reconstructs 96-98% of the
capability the moment you remove the model-specific part:

    task                     excess   ratio   recoverability
    promoter_all             +0.031    6.10           96.7%
    coding_vs_intergenomic   +0.024    5.42           97.3%
    human_or_worm            +0.021    5.03           97.8%
    splice_acceptors         +0.014    1.06           98.5%

Erase ``promoter_all``'s +0.031 perfectly and a from-scratch CNN still scores 0.924
against the model's 0.956. "Unlearning succeeded" and "capability denied" come apart
completely. So two quantities are needed:

* ``excess = model - max(baselines)`` -- the only part weight-space unlearning can
  remove. Anything a baseline recovers from the same labelled data is not held uniquely
  in the pretrained weights.
* ``recoverability = max(baselines) / model`` -- what survives a perfect removal. Low is
  good: it means removal actually costs the capability.

These two trade off, and the trade-off is the finding. Excess is large only where
baselines are weak; baselines are weak on hard tasks; hard tasks are small and noisy.
So precise measurements tend to be worthless targets and valuable targets tend to be
imprecise. Escaping that needs a task that is hard for baselines *and* has a large test
set.

``ratio = excess / (2 * sqrt(sd_model^2 + sd_baseline^2))`` gates on seed noise. It is a
signal-to-noise measure, **not a p-value**, and it captures only training randomness --
not test-set sampling error, which is why ``--paired-bootstrap-note`` is printed for
anything close to the line. Use ``signed_bootstrap.py`` on saved predictions for a real
interval.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections import defaultdict
from typing import Optional, Sequence

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from phase2.run_metadata import build_run_metadata, write_metadata

INPUT_COLUMNS = {"task", "arm", "role", "score"}

FIELDNAMES = [
    "task",
    "metric",
    "model_arm",
    "model_score",
    "model_sd",
    "model_seeds",
    "binding_baseline",
    "baseline_score",
    "baseline_sd",
    "baseline_seeds",
    "n_baselines",
    "excess",
    "gate",
    "ratio",
    "recoverability",
    "significant",
    "removal_meaningful",
    "verdict",
    "notes",
]


def parse_float(value: object) -> Optional[float]:
    if value in (None, "", "NA", "null", "None"):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def read_scores(path: str) -> dict[str, dict]:
    """Read a long-format score table.

    Required columns: ``task``, ``arm``, ``role`` (``model`` or ``baseline``), ``score``.
    Optional: ``score_sd``, ``n_seeds``, ``metric``.
    """
    tasks: dict[str, dict] = defaultdict(
        lambda: {"model": None, "all_models": [], "baselines": [], "metric": ""})
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        missing = INPUT_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Score table missing required columns: {sorted(missing)}")
        for row in reader:
            task = (row.get("task") or "").strip()
            score = parse_float(row.get("score"))
            if not task or score is None:
                continue
            entry = {
                "arm": (row.get("arm") or "").strip() or "unnamed",
                "score": score,
                "sd": parse_float(row.get("score_sd")),
                "n_seeds": int(parse_float(row.get("n_seeds")) or 0),
            }
            role = (row.get("role") or "").strip().lower()
            if row.get("metric"):
                tasks[task]["metric"] = row["metric"].strip()
            if role == "model":
                tasks[task].setdefault("all_models", []).append(entry)
                current = tasks[task]["model"]
                if current is None or score > current["score"]:
                    tasks[task]["model"] = entry
            else:
                tasks[task]["baselines"].append(entry)
    return tasks


def qualify(task: str, payload: dict, args) -> dict:
    model = payload["model"]
    all_models = payload.get("all_models") or ([model] if model else [])
    baselines = payload["baselines"]
    notes: list[str] = []

    if model is None:
        return {"task": task, "verdict": "NO_MODEL_ARM", "notes": "no row with role=model"}
    if not baselines:
        return {"task": task, "verdict": "NO_BASELINE",
                "notes": "no baseline arm -- a model score alone cannot qualify a target"}

    binding = max(baselines, key=lambda entry: entry["score"])
    excess = model["score"] - binding["score"]
    recoverability = binding["score"] / model["score"] if model["score"] else float("nan")

    model_sd = model["sd"] or 0.0
    base_sd = binding["sd"] or 0.0
    gate = 2.0 * math.sqrt(model_sd ** 2 + base_sd ** 2)
    ratio = excess / gate if gate > 0 else None

    if model["n_seeds"] and model["n_seeds"] < args.min_seeds:
        notes.append(f"model has {model['n_seeds']} seed(s); >= {args.min_seeds} required")
    if binding["n_seeds"] and binding["n_seeds"] < args.min_seeds:
        notes.append(f"binding baseline has {binding['n_seeds']} seed(s); "
                     f">= {args.min_seeds} required")
    if gate == 0.0:
        notes.append("no seed SD supplied on either arm -- significance not assessed")
    elif base_sd == 0.0:
        # A deterministic baseline (k-mer, alignment) has no seed spread, so the gate
        # collapses to the model's SD alone and `ratio` is inflated -- often several-fold.
        # Do not read that as strong evidence.
        notes.append(f"binding baseline '{binding['arm']}' has no seed SD, so the gate "
                     "uses only the model's spread and the ratio is an OVER-estimate; "
                     "confirm with a paired bootstrap over saved predictions")
    elif model_sd == 0.0:
        notes.append("model arm has no seed SD, so the gate is an under-estimate")
    if len(baselines) < args.min_baselines:
        notes.append(f"only {len(baselines)} baseline arm(s); >= {args.min_baselines} "
                     "recommended (composition, supervised CNN, alignment)")

    significant = bool(ratio is not None and ratio > 1.0)
    removal_meaningful = bool(recoverability == recoverability
                              and recoverability <= args.max_recoverability)

    if ratio is not None and 0.7 < ratio < 1.5:
        notes.append("ratio is near the line -- gate on a paired bootstrap over saved "
                     "predictions, not seed SD alone")

    # An inflated gate must not be able to produce a QUALIFIED verdict on its own.
    blocking = [n for n in notes if "required" in n or "OVER-estimate" in n]
    if not significant:
        verdict = "NOT_QUALIFIED_NO_EXCESS"
    elif not removal_meaningful:
        verdict = "NOT_QUALIFIED_COSMETIC"
    elif blocking:
        verdict = "PROVISIONAL"
    else:
        verdict = "QUALIFIED"

    return {
        "task": task,
        "metric": payload["metric"],
        "model_arm": model["arm"],
        "model_score": round(model["score"], 4),
        "model_sd": round(model_sd, 4) if model_sd else None,
        "model_seeds": model["n_seeds"] or None,
        "binding_baseline": binding["arm"],
        "baseline_score": round(binding["score"], 4),
        "baseline_sd": round(base_sd, 4) if base_sd else None,
        "baseline_seeds": binding["n_seeds"] or None,
        "n_baselines": len(baselines),
        "excess": round(excess, 4),
        "gate": round(gate, 4) if gate else None,
        "ratio": round(ratio, 2) if ratio is not None else None,
        "recoverability": round(recoverability, 4),
        "significant": significant,
        "removal_meaningful": removal_meaningful,
        "verdict": verdict,
        "notes": "; ".join(notes),
        "all_baselines": sorted(
            ({"arm": b["arm"], "score": round(b["score"], 4)} for b in baselines),
            key=lambda entry: -entry["score"],
        ),
        # Every model arm against the SAME binding baseline. Reporting only the winner
        # hides that an excess can belong to one model rather than to "gLMs": on
        # `phage_fragments`, NT-v2 is +0.0783 (ratio 2.86) while DNABERT-2, GENA-LM and
        # HyenaDNA are all BELOW the tuned CNN (-0.019, -0.125, -0.034).
        "per_model": sorted(
            ({"arm": e["arm"], "score": round(e["score"], 4),
              "sd": round(e["sd"], 4) if e["sd"] else None, "n_seeds": e["n_seeds"] or None,
              "excess": round(e["score"] - binding["score"], 4),
              "ratio": (round((e["score"] - binding["score"])
                              / (2.0 * math.sqrt((e["sd"] or 0.0) ** 2 + base_sd ** 2)), 2)
                        if ((e["sd"] or 0.0) or base_sd) else None)}
             for e in all_models),
            key=lambda entry: -entry["excess"],
        ),
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--scores-csv", required=True,
                        help="long format: task,arm,role,score[,score_sd,n_seeds,metric]")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", default="")
    parser.add_argument("--metadata-path", default="")
    parser.add_argument("--max-recoverability", type=float, default=0.90,
                        help="reject above this: removal leaves the capability reconstructable")
    parser.add_argument("--min-seeds", type=int, default=3)
    parser.add_argument("--min-baselines", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    tasks = read_scores(args.scores_csv)
    if not tasks:
        print("[qualify] score table produced no usable rows")
        return 1

    results = [qualify(task, payload, args) for task, payload in sorted(tasks.items())]
    order = {"QUALIFIED": 0, "PROVISIONAL": 1, "NOT_QUALIFIED_COSMETIC": 2,
             "NOT_QUALIFIED_NO_EXCESS": 3, "NO_BASELINE": 4, "NO_MODEL_ARM": 5}
    results.sort(key=lambda r: (order.get(r["verdict"], 9), -(r.get("excess") or 0)))

    os.makedirs(os.path.dirname(os.path.abspath(args.out_csv)) or ".", exist_ok=True)
    with open(args.out_csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print(f"[qualify] wrote {args.out_csv}")

    if args.out_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.out_json)) or ".", exist_ok=True)
        with open(args.out_json, "w") as handle:
            json.dump(results, handle, indent=2)
        print(f"[qualify] wrote {args.out_json}")

    if args.metadata_path:
        write_metadata(args.metadata_path, build_run_metadata(
            args=args, data_paths=[args.scores_csv],
            extra={"n_tasks": len(results),
                   "n_qualified": sum(1 for r in results if r["verdict"] == "QUALIFIED")},
        ))

    print()
    print(f"{'task':32s} {'excess':>8s} {'ratio':>6s} {'recov':>7s}  verdict")
    for row in results:
        if row["verdict"] in {"NO_MODEL_ARM", "NO_BASELINE"}:
            print(f"{row['task'][:32]:32s} {'--':>8s} {'--':>6s} {'--':>7s}  {row['verdict']}")
            continue
        ratio = f"{row['ratio']:.2f}" if row["ratio"] is not None else "--"
        print(f"{row['task'][:32]:32s} {row['excess']:+8.4f} {ratio:>6s} "
              f"{row['recoverability']*100:6.1f}%  {row['verdict']}")
        for entry in row.get("per_model", []):
            if len(row.get("per_model", [])) < 2:
                break
            r = f"{entry['ratio']:.2f}" if entry["ratio"] is not None else "--"
            print(f"{'':4s}{entry['arm'][:26]:26s}   vs {row['binding_baseline'][:10]:10s} "
                  f"{entry['excess']:+.4f} (ratio {r})")
        if row["notes"]:
            print(f"{'':32s} {'':8s} {'':6s} {'':7s}  ! {row['notes']}")

    qualified = [r for r in results if r["verdict"] == "QUALIFIED"]
    print(f"\n[qualify] {len(qualified)}/{len(results)} qualified "
          f"(excess above seed noise AND recoverability <= {args.max_recoverability:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
