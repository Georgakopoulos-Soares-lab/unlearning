"""Select official GUE train/dev records without reading test members."""
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import zipfile

import numpy as np
from sklearn.model_selection import train_test_split


def digest(value):
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def normalize(sequence):
    sequence = ''.join(sequence.upper().split())
    if not sequence or set(sequence) - set('ACGTRYSWKMBDHVN'):
        raise ValueError('Empty sequence or unsupported nucleotide alphabet')
    return ''.join(c if c in 'ACGT' else 'N' for c in sequence)


def select_indices(labels, limit, seed):
    indices = np.arange(len(labels))
    if len(indices) <= limit:
        return indices.tolist()
    selected, _ = train_test_split(indices, train_size=limit, stratify=labels, random_state=seed)
    return sorted(selected.tolist())


def overlap_report(rows):
    report = {}
    complement = str.maketrans('ACGTN', 'TGCAN')
    for field in ['full_sequence', 'sequence']:
        for kind in ['exact', 'reverse_complement_canonical']:
            groups = defaultdict(list)
            for row in rows:
                sequence = row[field]
                key = min(sequence, sequence.translate(complement)[::-1]) if kind != 'exact' else sequence
                groups[digest(key)].append({'id': row['id'], 'split': row['split']})
            duplicates = [members for members in groups.values() if len(members) > 1]
            report[f'{field}_{kind}'] = {
                'within_split_groups': sum(any(sum(m['split'] == s for m in g) > 1 for s in ['train', 'validation']) for g in duplicates),
                'cross_split_groups': sum(len({m['split'] for m in g}) > 1 for g in duplicates),
                'groups': duplicates,
            }
    report['scope'] = 'Selected pilot examples only; exact/RC checks are not homology analysis'
    return report


def prepare(config, archive, run_dir):
    run_dir = Path(run_dir)
    manifests, metadata = [], {}
    with zipfile.ZipFile(archive) as source:
        names = source.namelist()  # member names only; test contents are never opened
        for task, directory in config['tasks'].items():
            selected_rows, task_meta = [], {}
            for split, filename, limit in [('train', 'train.csv', config['train_size']), ('validation', 'dev.csv', config['validation_size'])]:
                candidates = [n for n in names if n.endswith('/' + directory + '/' + filename)]
                if len(candidates) != 1:
                    raise ValueError(f'Unresolved official mapping: {task} {filename}: {candidates}')
                raw = source.read(candidates[0])
                records = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
                if not records or 'sequence' not in records[0] or 'label' not in records[0]:
                    raise ValueError(f'Unverified schema: {candidates[0]}')
                labels = [int(r['label']) for r in records]
                expected_labels = set(config.get('label_schemas', {}).get(task, [0, 1]))
                if set(labels) != expected_labels:
                    raise ValueError(f'Unexpected label schema: {task}: {set(labels)}')
                indices = select_indices(labels, limit, config['seed'])
                task_meta[split] = dict(source_member=candidates[0], source_sha256=digest(raw),
                                        label_schema=sorted(expected_labels),
                                        source_rows=len(records), source_class_counts=dict(Counter(labels)),
                                        selected_class_counts=dict(Counter(labels[i] for i in indices)),
                                        selection='sklearn train_test_split stratified seed42; sorted original row indices')
                for index in indices:
                    record = records[index]
                    full = normalize(record['sequence'])
                    sequence = full[:config['max_length']]
                    row = dict(task=task, split=split, id=record.get('id') or f'{task}:{filename}:{index}',
                               original_row_index=index, label=labels[index], sequence=sequence, full_sequence=full,
                               full_sequence_sha256=digest(full), scored_prefix_sha256=digest(sequence),
                               original_length=len(full), scored_length=len(sequence), truncated=len(full)>len(sequence),
                               group_id=record.get('group') or record.get('group_id') or None,
                               ambiguous_bases_scored=sequence.count('N'), dataset_source=config['data_source_revision'])
                    selected_rows.append(row)
            task_meta['overlap'] = overlap_report(selected_rows)
            metadata[task] = task_meta
            for row in selected_rows:
                row.pop('full_sequence')
            manifests.extend(selected_rows)
    manifest_text = ''.join(json.dumps(r, sort_keys=True)+'\n' for r in manifests)
    path = run_dir / 'subset_manifest.jsonl'
    if path.exists() and path.read_text() != manifest_text:
        raise ValueError('Refusing to change a saved subset manifest')
    path.write_text(manifest_text)
    (run_dir / 'data_provenance.json').write_text(json.dumps(metadata, indent=2))
    return dict(manifest_sha256=digest(manifest_text), samples=len(manifests), tasks=metadata)
