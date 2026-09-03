"""H3: re-score every arm on a homology-filtered test subset.

This is hurdle H3 in [docs/TARGET_SELECTION.md](../docs/TARGET_SELECTION.md) and the
criterion that decides whether an excess is real. It needs **no retraining** -- it masks
the leaked rows out of saved test predictions and recomputes the metric, so it is free
if predictions were saved and impossible if they were not. Save predictions on every arm.

Why this and not the reachability number
----------------------------------------
Reachability says a homologous relative exists; it does not say the excess depends on it.
Measured on the two candidate targets:

    filter          phage n   excess  ratio |  g_max n   excess  ratio
    official           4630  +0.0787   2.92 |      490  +0.1463   1.13
    id>=0.7/c0.3       4266  +0.0827   3.19 |      341  +0.0995   0.79
    id>=0.8/c0.5       4611  +0.0793   2.92 |      387  +0.1151   0.82
    id>=0.9/c0.5       4618  +0.0792   2.92 |      438  +0.1482   1.11

`phage_fragments` is insensitive -- its excess *grows* under the harshest filter.
`lncrna.g_max` loses 32% and falls below the gate, because filtering *raises* the CNN
(0.3653 -> 0.3813) while *lowering* the model (0.5116 -> 0.4809). Reachability alone
predicted neither outcome.

**A looser identity threshold removes MORE rows.** `id>=0.7/c0.3` detects the most
homology, so it filters most aggressively and is the strictest test. Read that row as the
headline; `id>=0.9` is the weakest filter, not the strongest.

Inputs
------
A prediction index CSV: ``task,arm,role,path[,seed]``. Each ``path`` is an ``.npz``
holding ``y_true`` and ``y_pred`` in test-set row order. Plus mask sources -- either an
mmseqs ``.m8`` hit table (query ids must encode the test row index, e.g. ``te123|label``)
or a plain text file of 0-based row indices to drop.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import statistics as st
import sys
from collections import defaultdict
from typing import Optional, Sequence

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from phase2.run_metadata import build_run_metadata, write_metadata

csv.field_size_limit(sys.maxsize)

FIELDNAMES = [
    "task", "filter", "n_test", "n_clean", "n_removed", "removed_frac",
    "metric", "model_arm", "model_score", "model_sd", "model_seeds",
    "binding_baseline", "baseline_score", "baseline_sd", "baseline_seeds",
    "excess", "gate", "ratio", "significant", "delta_vs_official",
]

QUERY_ROW = re.compile(r"(?:^|\|)te(\d+)(?:\||$)")


def score(y_true: np.ndarray, y_pred: np.ndarray, metric: str) -> float:
    from sklearn.metrics import f1_score, matthews_corrcoef, roc_auc_score
    if metric == "macro_f1":
        return float(f1_score(y_true, y_pred, average="macro", zero_division=0))
    if metric == "auroc":
        try:
            return float(roc_auc_score(y_true, y_pred))
        except ValueError:
            return float("nan")
    return float(matthews_corrcoef(y_true, y_pred))


def read_index(path: str) -> dict[str, dict[str, list[dict]]]:
    """``{task: {arm: [{path, role, seed}, ...]}}``"""
    out: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        missing = {"task", "arm", "role", "path"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Prediction index missing columns: {sorted(missing)}")
        for row in reader:
            task = (row.get("task") or "").strip()
            arm = (row.get("arm") or "").strip()
            pred_path = (row.get("path") or "").strip()
            if not task or not arm or not pred_path:
                continue
            out[task][arm].append({
                "path": pred_path,
                "role": (row.get("role") or "baseline").strip().lower(),
                "seed": row.get("seed") or "",
            })
    return out


def rows_to_drop(source: str, n_test: int) -> np.ndarray:
    """Row indices to remove, from an mmseqs .m8 hit table or a list of indices."""
    drop: set[int] = set()
    if not os.path.exists(source) or os.path.getsize(source) == 0:
        return np.zeros(0, dtype=int)
    with open(source) as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            first = line.split("\t")[0]
            match = QUERY_ROW.search(first)
            if match:
                drop.add(int(match.group(1)))
                continue
            if first.isdigit():                      # plain index list
                drop.add(int(first))
    bad = [i for i in drop if i >= n_test]
    if bad:
        raise ValueError(
            f"{source}: {len(bad)} row index/indices >= n_test ({n_test}), e.g. {bad[:3]}. "
            "The mask and the predictions are not in the same test-set order."
        )
    return np.array(sorted(drop), dtype=int)


def load_arm(entries: list[dict]) -> tuple[np.ndarray, list[np.ndarray]]:
    y_true = None
    preds = []
    for entry in entries:
        data = np.load(entry["path"])
        yt, yp = data["y_true"], data["y_pred"]
        if y_true is None:
            y_true = yt
        elif not np.array_equal(y_true, yt):
            raise ValueError(f"{entry['path']}: y_true differs from a sibling seed -- "
                             "predictions are not aligned to one test-set order")
        preds.append(yp)
    return y_true, preds


def evaluate(task: str, arms: dict[str, list[dict]], keep: np.ndarray, label: str,
             metric: str, official: Optional[float]) -> Optional[dict]:
    y_true = None
    scored: dict[str, dict] = {}
    for arm, entries in arms.items():
        yt, preds = load_arm(entries)
        y_true = yt if y_true is None else y_true
        vals = [score(yt[keep], p[keep], metric) for p in preds]
        scored[arm] = {
            "role": entries[0]["role"],
            "mean": float(np.mean(vals)),
            "sd": float(st.stdev(vals)) if len(vals) > 1 else 0.0,
            "n": len(vals),
        }
    models = {a: v for a, v in scored.items() if v["role"] == "model"}
    baselines = {a: v for a, v in scored.items() if v["role"] != "model"}
    if not models or not baselines:
        print(f"  [{label}] skip: need >=1 model arm and >=1 baseline arm")
        return None
    m_arm, m = max(models.items(), key=lambda kv: kv[1]["mean"])
    b_arm, b = max(baselines.items(), key=lambda kv: kv[1]["mean"])
    excess = m["mean"] - b["mean"]
    gate = 2.0 * math.sqrt(m["sd"] ** 2 + b["sd"] ** 2)
    ratio = excess / gate if gate > 0 else None
    n_test = len(y_true)
    return {
        "task": task, "filter": label, "n_test": n_test, "n_clean": int(keep.sum()),
        "n_removed": int(n_test - keep.sum()),
        "removed_frac": round(float(1 - keep.sum() / n_test), 4),
        "metric": metric,
        "model_arm": m_arm, "model_score": round(m["mean"], 4),
        "model_sd": round(m["sd"], 4), "model_seeds": m["n"],
        "binding_baseline": b_arm, "baseline_score": round(b["mean"], 4),
        "baseline_sd": round(b["sd"], 4), "baseline_seeds": b["n"],
        "excess": round(excess, 4),
        "gate": round(gate, 4) if gate else None,
        "ratio": round(ratio, 2) if ratio is not None else None,
        "significant": bool(ratio is not None and ratio > 1.0),
        "delta_vs_official": None if official is None else round(excess - official, 4),
        "all_arms": {a: {k: (round(v[k], 4) if isinstance(v[k], float) else v[k])
                         for k in ("role", "mean", "sd", "n")} for a, v in scored.items()},
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--prediction-index", required=True,
                        help="CSV: task,arm,role,path[,seed]")
    parser.add_argument("--mask", action="append", default=[], metavar="TASK:LABEL:PATH",
                        help="rows to drop for one task, e.g. "
                             "phage:id>=0.7/c0.3:hits.m8 . Repeatable.")
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-json", default="")
    parser.add_argument("--metadata-path", default="")
    parser.add_argument("--metric", default="mcc", choices=["mcc", "macro_f1", "auroc"])
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    index = read_index(args.prediction_index)
    if not index:
        print("[rescore] prediction index produced no usable rows")
        return 1

    masks: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for spec in args.mask:
        parts = spec.split(":", 2)
        if len(parts) != 3:
            raise SystemExit(f"--mask must be TASK:LABEL:PATH, got {spec!r}")
        masks[parts[0]].append((parts[1], parts[2]))

    results = []
    for task, arms in sorted(index.items()):
        y_true, _ = load_arm(next(iter(arms.values())))
        n_test = len(y_true)
        print(f"[rescore] {task}: n_test={n_test}, arms={sorted(arms)}")
        official = evaluate(task, arms, np.ones(n_test, bool), "official",
                            args.metric, None)
        if official is None:
            continue
        results.append(official)
        print(f"  [official]      n={official['n_clean']:6d} "
              f"{official['model_arm']} {official['model_score']:.4f} vs "
              f"{official['binding_baseline']} {official['baseline_score']:.4f} "
              f"excess {official['excess']:+.4f} ratio {official['ratio']}")
        for label, source in masks.get(task, []):
            drop = rows_to_drop(source, n_test)
            keep = np.ones(n_test, bool)
            keep[drop] = False
            if keep.sum() < 30 or len(np.unique(y_true[keep])) < 2:
                print(f"  [{label}] skip: only {keep.sum()} clean rows "
                      f"({len(np.unique(y_true[keep]))} class(es)) -- too few to score")
                continue
            record = evaluate(task, arms, keep, label, args.metric, official["excess"])
            if record is None:
                continue
            results.append(record)
            print(f"  [{label}] n={record['n_clean']:6d} removed {record['n_removed']:5d} "
                  f"({record['removed_frac']:.2%}) excess {record['excess']:+.4f} "
                  f"ratio {record['ratio']} "
                  f"delta {record['delta_vs_official']:+.4f}"
                  f"{'  SIGNIFICANT' if record['significant'] else '  below gate'}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out_csv)) or ".", exist_ok=True)
    with open(args.out_csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in results:
            writer.writerow(row)
    print(f"[rescore] wrote {args.out_csv}")

    if args.out_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.out_json)) or ".", exist_ok=True)
        with open(args.out_json, "w") as handle:
            json.dump(results, handle, indent=2)
        print(f"[rescore] wrote {args.out_json}")

    if args.metadata_path:
        write_metadata(args.metadata_path, build_run_metadata(
            args=args, data_paths=[args.prediction_index],
            extra={"n_rows": len(results)}))

    filtered = [r for r in results if r["filter"] != "official"]
    if filtered:
        survived = [r for r in filtered if r["significant"]]
        print(f"\n[rescore] {len(survived)}/{len(filtered)} filtered evaluations remain "
              "significant. The most aggressive filter (lowest identity threshold) is the "
              "one to report.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
