from __future__ import annotations

import csv
import json
from pathlib import Path

from phase2.audit_split_homology import (
    audit_duplicates,
    main,
    read_manifest,
    reverse_complement,
    verdict_for,
)


def write_manifest(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def row(split: str, sequence: str, label: str, task: str = "t1") -> dict[str, object]:
    return {"task": task, "split": split, "sequence": sequence, "label": label,
            "split_type": "random"}


def test_reverse_complement_round_trips() -> None:
    assert reverse_complement("AACGTN") == "NACGTT"
    assert reverse_complement(reverse_complement("ACGTACGT")) == "ACGTACGT"


def test_exact_and_reverse_complement_duplicates_are_separated() -> None:
    # "AAAACCCC" and "GGGGTTTT" are reverse complements of each other, so a train set
    # containing both makes every rc-duplicate also an exact duplicate. Pick a second
    # train sequence whose complement is absent so the two categories stay distinct.
    splits = {
        "train": [("AAAACCCC", "0"), ("AAATTTGG", "1")],
        "test": [
            ("AAAACCCC", "0"),                      # exact duplicate
            ("AAAACCCC", "1"),                      # exact duplicate, label disagrees
            (reverse_complement("AAATTTGG"), "1"),  # reverse-complement duplicate only
            ("TTTTTTTT", "0"),                      # clean
        ],
    }
    report = audit_duplicates(splits)["test"]
    assert report["n_exact_duplicates"] == 2
    assert report["n_reverse_complement_only"] == 1
    # One of the two exact duplicates carries a label that train does not associate.
    assert report["n_label_consistent"] == 1


def test_class_conditional_leakage_is_surfaced() -> None:
    """The NT `enhancers` failure mode: all leaked rows in one class.

    An aggregate duplicate rate of 50% hides that class 1 is fully memorisable while
    class 0 is untouched, which is a directional shortcut rather than noise.
    """
    splits = {
        "train": [("AAAA", "1"), ("CCCC", "1")],
        "test": [("AAAA", "1"), ("CCCC", "1"), ("GGGG", "0"), ("TTTT", "0")],
    }
    report = audit_duplicates(splits)["test"]
    assert report["per_class"]["1"]["leaked_frac"] == 1.0
    assert report["per_class"]["0"]["leaked_frac"] == 0.0
    assert report["max_class_leaked_frac"] == 1.0
    assert report["class_asymmetry"] == 1.0


def test_verdict_fails_on_leak_and_flags_missing_homology_check() -> None:
    splits = {"train": [("AAAA", "1")], "test": [("AAAA", "1"), ("GGGG", "0")]}
    result = verdict_for(audit_duplicates(splits), None)
    assert result["verdict"] == "FAIL"
    assert result["homology_checked"] is False
    assert any("verbatim in train" in reason for reason in result["reasons"])


def test_clean_split_passes_but_keeps_the_label_transfer_caveat() -> None:
    """A PASS without mmseqs must not read as 'homology-disjoint'.

    HVUE had 0.00% exact duplicates and 91-99.9% homology, so the caveat is the
    load-bearing part of this verdict.
    """
    splits = {
        "train": [("AAAACCCC", "0"), ("GGGGAAAA", "1")],
        "test": [("TTTTGGGG", "0"), ("CCCCTTTT", "1")],
    }
    result = verdict_for(audit_duplicates(splits), None)
    assert result["verdict"] == "PASS"
    assert result["reasons"] == []
    assert result["label_transfer_checked"] is False
    assert result["caveat"] is not None
    assert "label transfer not measured" in result["caveat"]


def test_high_reachability_alone_does_not_fail_a_split() -> None:
    """Reachability is a diagnostic, not a criterion.

    `lncrna.g_max` is 30.4% reachable, but homologous pairs agree on the label only
    71.1% of the time and an NN lookup scores 0.187 against a supervised CNN at 0.365 --
    the homology is real (paleopolyploid paralogs) and label-uninformative. Failing that
    split on reachability was wrong, so reachability now only emits a note.
    """
    splits = {"train": [("AAAACCCC", "0")], "test": [("TTTTGGGG", "0")]}
    reach = {"bands": {"id>=0.7": {"n_reachable": 9, "reachable_frac": 0.9, "per_class": {}}}}
    result = verdict_for(audit_duplicates(splits), reach)
    assert result["verdict"] == "PASS"
    assert result["homology_checked"] is True
    assert any("diagnostic" in note for note in result["notes"])


def test_label_transfer_above_the_composition_floor_fails_the_split() -> None:
    """NT_H3: an NN lookup scores 0.685 against a k-mer floor of 0.656."""
    splits = {"train": [("AAAACCCC", "0")], "test": [("TTTTGGGG", "0")]}
    transfer = {"reached_frac": 0.657, "label_agreement": 0.94,
                "nn_mcc_reached": 0.8788, "nn_mcc_all": 0.6851}
    result = verdict_for(audit_duplicates(splits), None, transfer, composition_floor=0.656)
    assert result["verdict"] == "FAIL"
    assert result["label_transfer_checked"] is True
    assert result["caveat"] is None
    assert any("ABOVE the composition floor" in reason for reason in result["reasons"])
    assert any("substantially homology retrieval" in note for note in result["notes"])


def test_label_transfer_below_the_composition_floor_passes() -> None:
    """lncrna.g_max: NN lookup 0.187 against a k-mer floor of 0.143 is a PASS at 0.30,
    but would fail against its own floor -- which is why the floor should be supplied."""
    splits = {"train": [("AAAACCCC", "0")], "test": [("TTTTGGGG", "0")]}
    transfer = {"reached_frac": 0.304, "label_agreement": 0.711,
                "nn_mcc_reached": 0.4234, "nn_mcc_all": 0.1874}
    result = verdict_for(audit_duplicates(splits), None, transfer)
    assert result["verdict"] == "PASS", "0.187 is below the 0.30 default"
    assert result["notes"] == [], "71% label agreement must not trigger the retrieval note"


def test_clean_task_with_informative_but_narrow_homology_passes() -> None:
    """phage_fragments: 99.2% label agreement but only 7.9% reached, NN lookup 0.274."""
    splits = {"train": [("AAAACCCC", "0")], "test": [("TTTTGGGG", "0")]}
    transfer = {"reached_frac": 0.079, "label_agreement": 0.992,
                "nn_mcc_reached": 0.9508, "nn_mcc_all": 0.2741}
    result = verdict_for(audit_duplicates(splits), None, transfer, composition_floor=0.629)
    assert result["verdict"] == "PASS"
    # High agreement on a narrow slice must not fire the retrieval note.
    assert result["notes"] == []


def test_read_manifest_groups_by_task_and_normalizes_dev_split(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [
        row("train", "AAAACCCC", "0", task="alpha"),
        row("dev", "GGGGTTTT", "1", task="alpha"),
        row("test", "ACGTACGT", "0", task="beta"),
    ])
    grouped = read_manifest(str(manifest), None, "unspecified")
    assert set(grouped) == {("alpha", "random"), ("beta", "random")}
    assert "val" in grouped[("alpha", "random")]


def test_main_writes_json_and_gates_with_fail_on_leak(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.csv"
    write_manifest(manifest, [
        row("train", "AAAACCCC", "1"),
        row("test", "AAAACCCC", "1"),
        row("test", "GGGGTTTT", "0"),
    ])
    out = tmp_path / "audit.json"
    code = main([
        "--benchmark-manifest", str(manifest),
        "--out-json", str(out),
        "--skip-homology",
        "--fail-on-leak",
    ])
    assert code == 2
    payload = json.loads(out.read_text())
    assert payload[0]["verdict"] == "FAIL"
    assert payload[0]["homology_checked"] is False
