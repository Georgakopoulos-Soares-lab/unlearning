"""Qualify supplied H3 train/dev only; never open held-out members."""
import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(archive, output):
    output.mkdir(parents=True, exist_ok=False)
    archive_sha = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
    summary = {'archive_sha256': archive_sha, 'task': 'GUE_benchmark/emp_H3',
               'test_contents_opened': False, 'splits': {}}
    groups = {}
    with zipfile.ZipFile(archive) as z, (output / 'train_dev_manifest.jsonl').open('w') as manifest:
        for split in ('train', 'dev'):
            member = f'GUE_benchmark/emp_H3/{split}.jsonl'
            raw = z.read(member)
            rows = [json.loads(line) for line in raw.splitlines()]
            csv_rows = list(csv.DictReader(io.StringIO(z.read(f'GUE_benchmark/emp_H3/{split}.csv').decode())))
            if len(csv_rows) != len(rows):
                raise ValueError('CSV/JSONL count mismatch')
            labels, lengths, alphabet = Counter(), Counter(), Counter()
            exact, rc = Counter(), Counter()
            for i, (row, csv_row) in enumerate(zip(rows, csv_rows)):
                sequence = ''.join(row['sequence'].upper().split())
                if set(sequence) - set('ACGTN'):
                    raise ValueError('Unexpected alphabet; protocol review required')
                label = int(row['label'])
                if label not in (0, 1) or csv_row['sequence'] != row['sequence'] or int(csv_row['label']) != label:
                    raise ValueError('Label/schema or CSV/JSONL mismatch')
                reverse = sequence.translate(str.maketrans('ACGTN', 'TGCAN'))[::-1]
                group = sha(min(sequence, reverse).encode())
                record = dict(id=f'{archive_sha}:{member}:{i}', split=split, source_row=i,
                              source_member=member, label=label, sequence=sequence,
                              sequence_sha256=sha(sequence.encode()), exact_rc_group=group)
                manifest.write(json.dumps(record, sort_keys=True) + '\n')
                labels[label] += 1
                lengths[len(sequence)] += 1
                alphabet.update(sequence)
                exact[record['sequence_sha256']] += 1
                rc[group] += 1
            groups[split] = (exact, rc)
            summary['splits'][split] = dict(rows=len(rows), labels=dict(labels), lengths=dict(lengths),
                alphabet=dict(alphabet), source_sha256=sha(raw), csv_jsonl_match=True,
                exact_duplicate_groups=sum(v > 1 for v in exact.values()),
                exact_rc_duplicate_groups=sum(v > 1 for v in rc.values()),
                majority_baseline=max(labels.values()) / len(rows))
    summary['train_dev_overlap'] = dict(exact_groups=len(groups['train'][0].keys() & groups['dev'][0].keys()),
                                      exact_rc_groups=len(groups['train'][1].keys() & groups['dev'][1].keys()))
    summary['limitations'] = ['No supplied biological group IDs or class-name map',
        'Deterministic IDs identify archive member/row, not biological independence',
        'Archive hash records downloaded bytes; no publisher checksum supplied',
        'Held-out contents remain unopened pending frozen protocol']
    summary['manifest_sha256'] = sha((output / 'train_dev_manifest.jsonl').read_bytes())
    (output / 'qualification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    prepare(args.archive, args.output)
