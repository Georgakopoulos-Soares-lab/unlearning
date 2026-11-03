"""Offline benign retain preparation; never loads models or held-out sequences."""
import hashlib
import json
import random
from collections import Counter

TASKS = {'gue_emp_h3', 'gue_prom_300_all', 'gue_prom_core_all',
         'gue_splice_reconstructed', 'gue_tf_0', 'gue_mouse_0'}


def identity(sequence):
    if not sequence or set(sequence) - set('ACGTN'):
        raise ValueError('Expected normalized ACGTN sequence')
    rc = sequence.translate(str.maketrans('ACGTN', 'TGCAN'))[::-1]
    return hashlib.sha256(min(sequence, rc).encode()).hexdigest()


def prepare(rows, budgets, seed=42, heldout_hashes=()):
    """Sample whole rows without replacement within per-task nucleotide budgets.

    Budgets count nucleotide lengths, NOT tokenizer tokens/loss-mask positions.
    heldout_hashes must be canonical exact/RC hashes from an external split audit.
    Every row requires source task/version and stable ID. Duplicate sequences
    across tasks are rejected rather than silently changing mixture weights.
    """
    if not budgets or set(budgets) - TASKS:
        raise ValueError('Unqualified task')
    if any(type(v) is not int or v <= 0 for v in budgets.values()):
        raise ValueError('Budgets must be positive integers')
    pools = {t: [] for t in budgets}
    seen, ids = set(), set()
    blocked = set(heldout_hashes)
    for row in rows:
        if row.get('split') != 'train':
            raise ValueError('Training input contains held-out rows')
        task = row.get('task')
        if task not in pools or not row.get('dataset_source') or not row.get('id'):
            raise ValueError('Missing provenance or unexpected task')
        key = (task, row['id'])
        h = identity(row['sequence'])
        if key in ids or h in seen or h in blocked:
            raise ValueError('Duplicate identity or exact/RC held-out overlap')
        ids.add(key)
        seen.add(h)
        pools[task].append(dict(row, canonical_sha256=h))
    selected, summary = [], {}
    for task in sorted(pools):
        pool = sorted(pools[task], key=lambda r: r['id'])
        random.Random(f'{seed}:{task}').shuffle(pool)
        used = 0
        chosen = []
        for row in pool:
            n = len(row['sequence'])
            if used + n <= budgets[task]:
                chosen.append(row)
                used += n
        selected.extend(chosen)
        summary[task] = dict(requested=budgets[task], processed=used,
                             shortfall=budgets[task]-used, unique_examples=len(chosen),
                             repeated_draws=0, available_examples=len(pool))
    payload = ''.join(json.dumps(r, sort_keys=True)+'\n' for r in selected)
    return selected, dict(schema_version=1, seed=seed, unit='nucleotide_length_proxy',
                         tasks=summary, manifest_sha256=hashlib.sha256(payload.encode()).hexdigest(),
                         heldout_audit='external_hashes_supplied' if blocked else 'NOT_SUPPLIED',
                         limitation='Exact/RC checks do not establish homology independence')
