"""Sequence-level split audit: exact duplicates, reverse complements, class-conditional
leakage, and homology reachability.

``check_split_validity.py`` is the complementary check -- it verifies label balance and
that a disjoint split is harder than random under shortcut baselines. It does **not**
look at sequences. This script does, and it exists because three separate published
benchmarks passed the label-level checks while leaking badly.

What it catches, and why each check is here
-------------------------------------------
1. **Exact duplicates.** The original Nucleotide Transformer ``enhancers`` task has
   **100 of 400 test rows verbatim in train** (25%), 100% label-consistent.
   ``splice_sites_all`` has 221/3000 (7.4%). Removing the duplicated rows costs every
   architecture -- pretrained or not -- **0.17-0.21 MCC**, roughly 35% of the reported
   score. All twenty ``revised_*`` variants of the same benchmark are clean, which is
   presumably why they exist.

2. **Class-conditional leakage.** On that same task all 100 leaked rows are class 1 and
   the test set is balanced 200/200 -- so **half the positive class and none of the
   negative class** is memorisable. That is a directional shortcut, not noise, and an
   aggregate duplicate rate hides it completely. Always read the per-class breakdown.

3. **Reverse complements.** DNA read on the opposite strand is the same biological
   sequence and is invisible to string equality.

4. **Homology reachability, via ``mmseqs easy-search``.** ``easy-cluster -c 0.9``
   requires 90% *bidirectional* coverage, so a test sequence sharing half its length
   with a training sequence is not clustered with it: in a direct test it caught
   **0 of 150** such pairs, and a split it certified as identity-disjoint was 42-83%
   reachable by local alignment. Use ``easy-search`` (local alignment) for leakage
   questions and reserve ``easy-cluster`` for building splits.

   HVUE's official splits are **91-99.9% homologous on 6 of 7 tasks** with 0.00% exact
   duplicates -- they deduplicated the wrong thing.

Interpreting the verdict
------------------------
``FAIL`` means the split cannot support a generalisation claim as-is. It does not mean
the data is useless: report the leak-free subset alongside the full number, as the two
readings often differ in size but not in ranking.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from typing import Optional, Sequence

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from phase2.run_metadata import build_run_metadata, write_metadata

csv.field_size_limit(sys.maxsize)

COMPLEMENT = str.maketrans("ACGTN", "TGCAN")

# Thresholds a split must clear to support a generalisation claim.
MAX_EXACT_DUPLICATE_FRAC = 0.01
MAX_CLASS_DUPLICATE_FRAC = 0.02
MAX_REACHABLE_FRAC = 0.20        # diagnostic threshold only -- never fails a split
MAX_NN_MCC_WITHOUT_FLOOR = 0.30  # used only when --composition-floor is not supplied


def reverse_complement(seq: str) -> str:
    return seq.translate(COMPLEMENT)[::-1]


def clean_sequence(value: object) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch in {"A", "C", "G", "T", "N"})


def normalize_split(value: object) -> str:
    split = str(value or "").lower()
    return "val" if split in {"dev", "valid", "validation"} else split


def read_manifest(path: str, task_filter: Optional[set[str]], default_task: str) -> dict:
    """Return ``{(task, split_type): {split: [(sequence, label), ...]}}``."""
    grouped: dict[tuple[str, str], dict[str, list[tuple[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        missing = {"split", "sequence", "label"} - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Manifest missing required columns: {sorted(missing)}")
        for row in reader:
            task = row.get("task") or default_task
            if task_filter is not None and task not in task_filter:
                continue
            split = normalize_split(row.get("split"))
            seq = clean_sequence(row.get("sequence"))
            label = str(row.get("label", "")).strip()
            if split not in {"train", "val", "test"} or not seq or not label:
                continue
            split_type = (row.get("split_type") or "random").strip().lower() or "random"
            grouped[(task, split_type)][split].append((seq, label))
    return grouped


def audit_duplicates(splits: dict) -> dict:
    """Exact and reverse-complement overlap of test (and val) against train."""
    train = splits.get("train", [])
    train_seqs = {seq for seq, _ in train}
    train_rc = {reverse_complement(seq) for seq in train_seqs}
    train_labels: dict[str, set[str]] = defaultdict(set)
    for seq, label in train:
        train_labels[seq].add(label)

    report = {}
    for held in ("test", "val"):
        rows = splits.get(held, [])
        if not rows:
            continue
        exact = [(seq, label) for seq, label in rows if seq in train_seqs]
        rc_only = [(seq, label) for seq, label in rows
                   if seq not in train_seqs and seq in train_rc]
        label_consistent = sum(1 for seq, label in exact if label in train_labels[seq])
        per_class_total = Counter(label for _, label in rows)
        per_class_leaked = Counter(label for _, label in exact)
        report[held] = {
            "n_rows": len(rows),
            "n_exact_duplicates": len(exact),
            "exact_duplicate_frac": round(len(exact) / len(rows), 4),
            "n_reverse_complement_only": len(rc_only),
            "reverse_complement_frac": round(len(rc_only) / len(rows), 4),
            "n_label_consistent": label_consistent,
            "label_consistent_frac": round(label_consistent / len(exact), 4) if exact else None,
            "per_class": {
                label: {
                    "n_rows": per_class_total[label],
                    "n_leaked": per_class_leaked.get(label, 0),
                    "leaked_frac": round(per_class_leaked.get(label, 0) / per_class_total[label], 4),
                }
                for label in sorted(per_class_total)
            },
        }
        fracs = [v["leaked_frac"] for v in report[held]["per_class"].values()]
        report[held]["max_class_leaked_frac"] = round(max(fracs), 4) if fracs else 0.0
        report[held]["class_asymmetry"] = round(max(fracs) - min(fracs), 4) if fracs else 0.0
    return report


def mmseqs_reachability(splits: dict, mmseqs: str, identities: Sequence[float],
                        coverage: float, threads: int, sensitivity: float) -> Optional[dict]:
    """Fraction of test sequences reachable from train by local alignment.

    Uses ``easy-search``, not ``easy-cluster``: the latter needs bidirectional coverage
    and is blind to a test sequence that shares only part of its length with train.
    """
    train = splits.get("train", [])
    test = splits.get("test", [])
    if not train or not test:
        return None

    out: dict[str, object] = {"tool": "mmseqs easy-search", "coverage": coverage,
                              "cov_mode": 2, "sensitivity": sensitivity, "bands": {}}
    with tempfile.TemporaryDirectory() as tmp:
        query = os.path.join(tmp, "query.fasta")
        target = os.path.join(tmp, "target.fasta")
        with open(query, "w") as handle:
            for i, (seq, label) in enumerate(test):
                handle.write(f">test_{i}|{label}\n{seq}\n")
        with open(target, "w") as handle:
            for i, (seq, label) in enumerate(train):
                handle.write(f">train_{i}|{label}\n{seq}\n")
        for identity in identities:
            hits = os.path.join(tmp, f"hits_{identity}.m8")
            cmd = [
                mmseqs, "easy-search", query, target, hits, os.path.join(tmp, f"tmp_{identity}"),
                "--search-type", "3", "-s", str(sensitivity),
                "--min-seq-id", str(identity), "-c", str(coverage), "--cov-mode", "2",
                "--max-seqs", "50", "--threads", str(threads),
                "--format-output", "query,target,fident,alnlen,qcov",
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except (subprocess.CalledProcessError, OSError) as exc:  # pragma: no cover
                out["error"] = f"{type(exc).__name__}: {exc}"
                return out
            reached: set[str] = set()
            per_class: Counter[str] = Counter()
            if os.path.exists(hits):
                with open(hits) as handle:
                    for line in handle:
                        parts = line.split("\t")
                        if not parts:
                            continue
                        if parts[0] not in reached:
                            reached.add(parts[0])
                            per_class[parts[0].rsplit("|", 1)[-1]] += 1
            totals = Counter(label for _, label in test)
            out["bands"][f"id>={identity}"] = {
                "n_reachable": len(reached),
                "reachable_frac": round(len(reached) / len(test), 4),
                "per_class": {label: {"n_reachable": per_class.get(label, 0),
                                      "reachable_frac": round(per_class.get(label, 0) / totals[label], 4)}
                              for label in sorted(totals)},
            }
    return out


def label_transfer(splits: dict, mmseqs: str, identity: float, coverage: float,
                   threads: int, sensitivity: float) -> Optional[dict]:
    """Score a nearest-neighbour-by-homology classifier. This is the criterion that matters.

    Bare reachability is a proxy and it misleads in both directions. Measured on three
    tasks:

    * `lncrna.g_max` -- 30.4% reachable, but homologous pairs agree on the label only
      **71.1%** of the time and the NN classifier scores **0.187** against a k-mer floor
      of 0.143 and a supervised CNN at 0.365. The homology is real (soybean is a
      paleopolyploid, so paralogs abound) but it does **not** carry the label, because a
      duplicated pair often has one coding member and one degenerate one. Failing this
      task on reachability alone was wrong.
    * `NT_H3` -- 65.7% reachable, 94.0% label agreement, NN classifier **0.685** against
      k-mer 0.656 and a CNN at 0.783. A lookup gets 87% of the way to the supervised
      ceiling, so the task is substantially homology *retrieval*. Reachability alone
      understated this.
    * `phage_fragments` -- only 7.9% reachable but 99.2% label agreement. A lookup scores
      0.274 against a gLM at 0.920, so the other 92% must be generalisation. Clean.

    The number to compare against is the composition baseline: if the NN classifier beats
    it, homology is doing work that will be mistaken for learned biology.
    """
    train = splits.get("train", [])
    test = splits.get("test", [])
    if not train or not test:
        return None
    labels = [lab for _, lab in train]
    majority = Counter(labels).most_common(1)[0][0]
    with tempfile.TemporaryDirectory() as tmp:
        query = os.path.join(tmp, "q.fasta")
        target = os.path.join(tmp, "t.fasta")
        with open(query, "w") as handle:
            for i, (seq, lab) in enumerate(test):
                handle.write(f">te{i}|{lab}\n{seq}\n")
        with open(target, "w") as handle:
            for i, (seq, lab) in enumerate(train):
                handle.write(f">tr{i}|{lab}\n{seq}\n")
        hits = os.path.join(tmp, "hits.m8")
        cmd = [mmseqs, "easy-search", query, target, hits, os.path.join(tmp, "tmp"),
               "--search-type", "3", "-s", str(sensitivity), "--min-seq-id", str(identity),
               "-c", str(coverage), "--cov-mode", "2", "--max-seqs", "5",
               "--threads", str(threads),
               "--format-output", "query,target,fident,bits"]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, OSError) as exc:  # pragma: no cover
            return {"error": f"{type(exc).__name__}: {exc}"}
        best: dict[int, tuple[float, str]] = {}
        if os.path.exists(hits):
            with open(hits) as handle:
                for line in handle:
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) < 4:
                        continue
                    qi = int(parts[0].split("|")[0][2:])
                    bits = float(parts[3])
                    nn_label = parts[1].rsplit("|", 1)[-1]
                    if qi not in best or bits > best[qi][0]:
                        best[qi] = (bits, nn_label)
    if not best:
        return {"identity": identity, "n_reached": 0, "reached_frac": 0.0,
                "label_agreement": None, "nn_mcc_reached": None, "nn_mcc_all": None}
    y_true = [lab for _, lab in test]
    reached = sorted(best)
    agree = sum(1 for i in reached if best[i][1] == y_true[i]) / len(reached)
    classes = sorted({*y_true, *(v[1] for v in best.values())})
    idx = {c: n for n, c in enumerate(classes)}
    yr = [idx[y_true[i]] for i in reached]
    pr = [idx[best[i][1]] for i in reached]
    pred_all = [idx[best[i][1]] if i in best else idx.get(majority, 0) for i in range(len(test))]
    from sklearn.metrics import matthews_corrcoef
    return {
        "identity": identity,
        "n_reached": len(reached),
        "reached_frac": round(len(reached) / len(test), 4),
        "label_agreement": round(agree, 4),
        "nn_mcc_reached": round(float(matthews_corrcoef(yr, pr)), 4) if len(set(yr)) > 1 else None,
        "nn_mcc_all": round(float(matthews_corrcoef([idx[y] for y in y_true], pred_all)), 4),
    }


def verdict_for(dup: dict, reach: Optional[dict], transfer: Optional[dict] = None,
                composition_floor: Optional[float] = None) -> dict:
    """Verdict on duplicates, homology reachability, and label transfer.

    Label transfer is the load-bearing criterion when available; reachability is a
    diagnostic. See :func:`label_transfer` for why.
    """
    reasons: list[str] = []
    test = dup.get("test", {})
    if test:
        if test["exact_duplicate_frac"] > MAX_EXACT_DUPLICATE_FRAC:
            reasons.append(
                f"{test['n_exact_duplicates']}/{test['n_rows']} test rows "
                f"({test['exact_duplicate_frac']:.1%}) are verbatim in train"
            )
        if test["max_class_leaked_frac"] > MAX_CLASS_DUPLICATE_FRAC:
            worst = max(test["per_class"].items(), key=lambda kv: kv[1]["leaked_frac"])
            reasons.append(
                f"class '{worst[0]}' is {worst[1]['leaked_frac']:.1%} leaked "
                f"(asymmetry {test['class_asymmetry']:.1%}) -- directional shortcut"
            )
        if test["reverse_complement_frac"] > MAX_EXACT_DUPLICATE_FRAC:
            reasons.append(
                f"{test['n_reverse_complement_only']} test rows are reverse complements of train"
            )
    checked_homology = bool(reach and reach.get("bands") and not reach.get("error"))
    notes: list[str] = []
    if checked_homology:
        for band, stats in reach["bands"].items():
            if stats["reachable_frac"] > MAX_REACHABLE_FRAC:
                # Diagnostic only. High reachability with uninformative labels is fine;
                # `lncrna.g_max` is 30.4% reachable and its NN classifier scores 0.187
                # against a CNN at 0.365. Do not fail a split on this alone.
                notes.append(
                    f"{stats['reachable_frac']:.1%} of test reachable from train at {band} "
                    "(diagnostic; see label transfer)"
                )
    checked_transfer = bool(transfer and not transfer.get("error")
                            and transfer.get("nn_mcc_all") is not None)
    if checked_transfer:
        nn = transfer["nn_mcc_all"]
        if composition_floor is not None and nn > composition_floor:
            reasons.append(
                f"a nearest-neighbour-by-homology lookup scores {nn:.4f}, ABOVE the "
                f"composition floor {composition_floor:.4f} -- homology is doing work that "
                "will be mistaken for learned biology"
            )
        elif composition_floor is None and nn > MAX_NN_MCC_WITHOUT_FLOOR:
            reasons.append(
                f"a nearest-neighbour-by-homology lookup scores {nn:.4f} on the full test "
                f"set (>{MAX_NN_MCC_WITHOUT_FLOOR}); pass --composition-floor to judge this "
                "against the task's own k-mer baseline"
            )
        if transfer.get("label_agreement") is not None and transfer["label_agreement"] > 0.9 \
                and transfer["reached_frac"] > 0.3:
            notes.append(
                f"{transfer['reached_frac']:.1%} of test reached and homologous pairs agree "
                f"on the label {transfer['label_agreement']:.1%} of the time -- this task is "
                "substantially homology retrieval"
            )
    caveat = None
    if not checked_transfer:
        caveat = ("label transfer not measured: this verdict rests on duplicates"
                  + (" and reachability" if checked_homology else " only")
                  + ". Reachability alone misleads in both directions -- it fails tasks whose "
                    "homology is label-uninformative and understates tasks where a lookup "
                    "nearly solves the task.")
    return {
        "verdict": "FAIL" if reasons else "PASS",
        "reasons": reasons,
        "notes": notes,
        "homology_checked": checked_homology,
        "label_transfer_checked": checked_transfer,
        "caveat": caveat,
    }


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--benchmark-manifest", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--metadata-path", default="")
    parser.add_argument("--task-filter", default="")
    parser.add_argument("--default-task", default="unspecified")
    parser.add_argument("--mmseqs", default=os.environ.get("MMSEQS_BIN", "mmseqs"),
                        help="path to the mmseqs binary; skipped if not found")
    parser.add_argument("--skip-homology", action="store_true",
                        help="exact-duplicate checks only (fast, but see the PASS caveat)")
    parser.add_argument("--identities", nargs="+", type=float, default=[0.7, 0.9])
    parser.add_argument("--transfer-identity", type=float, default=0.7,
                        help="identity floor for the nearest-neighbour label-transfer test")
    parser.add_argument("--skip-label-transfer", action="store_true")
    parser.add_argument("--composition-floor", type=float, default=None,
                        help="the task's own k-mer/composition baseline score. The NN lookup "
                             "is judged against this; without it a blunt default is used.")
    parser.add_argument("--coverage", type=float, default=0.3,
                        help="target coverage for easy-search; low on purpose to catch partial overlap")
    parser.add_argument("--sensitivity", type=float, default=5.7)
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--fail-on-leak", action="store_true",
                        help="exit non-zero if any task FAILs (for use as a CI gate)")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    task_filter = ({p.strip() for p in args.task_filter.split(",") if p.strip()}
                   if args.task_filter else None)
    grouped = read_manifest(args.benchmark_manifest, task_filter, args.default_task)
    if not grouped:
        print("[split-audit] manifest produced no usable rows")
        return 1

    mmseqs_path = shutil.which(args.mmseqs) if not args.skip_homology else None
    if not args.skip_homology and mmseqs_path is None:
        print(f"[split-audit] mmseqs not found at '{args.mmseqs}' -- "
              "running exact-duplicate checks only; see the PASS caveat in each record")

    results = []
    for (task, split_type), splits in sorted(grouped.items()):
        dup = audit_duplicates(splits)
        reach = (mmseqs_reachability(splits, mmseqs_path, args.identities, args.coverage,
                                     args.threads, args.sensitivity)
                 if mmseqs_path else None)
        transfer = (label_transfer(splits, mmseqs_path, args.transfer_identity, args.coverage,
                                   args.threads, args.sensitivity)
                    if mmseqs_path and not args.skip_label_transfer else None)
        record = {
            "task": task,
            "split_type": split_type,
            "n_by_split": {name: len(rows) for name, rows in sorted(splits.items())},
            "duplicates": dup,
            "homology": reach,
            "label_transfer": transfer,
            "composition_floor": args.composition_floor,
        }
        record.update(verdict_for(dup, reach, transfer, args.composition_floor))
        results.append(record)

        test = dup.get("test", {})
        print(f"[split-audit] {task} / {split_type}: {record['verdict']}")
        if test:
            print(f"    exact dup {test['n_exact_duplicates']}/{test['n_rows']} "
                  f"({test['exact_duplicate_frac']:.2%}), rc-only {test['n_reverse_complement_only']}, "
                  f"worst class {test['max_class_leaked_frac']:.2%}, "
                  f"asymmetry {test['class_asymmetry']:.2%}")
        if reach and reach.get("bands"):
            for band, stats in reach["bands"].items():
                print(f"    reachable {band}: {stats['reachable_frac']:.2%}")
        if transfer and transfer.get("nn_mcc_all") is not None:
            print(f"    NN label transfer: reached {transfer['reached_frac']:.2%}, "
                  f"label agreement {transfer['label_agreement']:.1%}, "
                  f"NN-MCC(all)={transfer['nn_mcc_all']:.4f}"
                  + (f" vs composition floor {args.composition_floor:.4f}"
                     if args.composition_floor is not None else ""))
        for reason in record["reasons"]:
            print(f"    - {reason}")
        for note in record.get("notes", []):
            print(f"    ~ {note}")
        if record["caveat"]:
            print(f"    ! {record['caveat']}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out_json)) or ".", exist_ok=True)
    with open(args.out_json, "w") as handle:
        json.dump(results, handle, indent=2)
    print(f"[split-audit] wrote {args.out_json}")

    if args.metadata_path:
        write_metadata(args.metadata_path, build_run_metadata(
            args=args,
            data_paths=[args.benchmark_manifest],
            extra={"n_tasks": len(results),
                   "n_failed": sum(1 for r in results if r["verdict"] == "FAIL")},
        ))

    failed = [r for r in results if r["verdict"] == "FAIL"]
    if failed:
        print(f"[split-audit] {len(failed)}/{len(results)} task(s) FAILED")
        if args.fail_on_leak:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
