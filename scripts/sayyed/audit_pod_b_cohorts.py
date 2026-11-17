"""Audit exact frozen cohort identities without opening additional dataset partitions."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import time

root=Path('/workspace/meeting-artifacts/relearning-benign-v1')
reference=root/'recovery/base_h3_archive/multiretain-layers-v1-final-20261110T140836Z'
protocol=json.loads(Path('docs/experiments/ashay/multiretain-comparison-v1/COMPARISON_PROTOCOL.json').read_text())
expected={Path(x['path']).name:x['sha256'] for x in protocol['feature_manifests']}
started=time.monotonic()
tasks=defaultdict(list)
files=[]
for name in ['H3.jsonl','other_five.jsonl']:
    p=reference/'manifests'/name
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest==expected[name]
    rows=[json.loads(x) for x in p.read_text().splitlines()]
    assert len({r['id'] for r in rows})==len(rows)
    files.append(dict(path=str(p),sha256=digest,rows=len(rows)))
    for row in rows:
        tasks[row['task']].append(row)
reports=[]
complement=str.maketrans('ACGTN','TGCAN')
for task,rows in sorted(tasks.items()):
    counts=Counter(r['split'] for r in rows)
    assert dict(counts)==({'train':11971,'dev':1497,'test':1497} if task=='emp_H3' else {'train':1024,'dev':512})
    groups=defaultdict(list)
    split_groups=defaultdict(set)
    for row in rows:
        sequence=row['sequence']
        assert set(sequence)<=set('ACGTN') and 2<=len(sequence)<=1000
        sha=hashlib.sha256(sequence.encode()).hexdigest()
        rc_sequence=sequence.translate(complement)[::-1]
        group=hashlib.sha256(min(sequence,rc_sequence).encode()).hexdigest()
        if task=='emp_H3':
            assert row['sequence_sha256']==sha
        else:
            assert row['scored_prefix_sha256']==sha
        assert row['exact_rc_group']==group
        groups[group].append(row)
        split_groups[row['split']].add(group)
    conflicts=[g for g,items in groups.items() if len({r['label'] for r in items})>1]
    assert not conflicts
    overlaps={a+'__'+b:len(split_groups[a]&split_groups[b])
              for a in sorted(split_groups) for b in sorted(split_groups) if a<b}
    assert not any(overlaps.values())
    classes=sorted({r['label'] for r in rows})
    assert classes==([0,1,2] if task=='gue_splice_reconstructed' else [0,1])
    reports.append(dict(task=task,counts=dict(counts),classes=classes,
                        labels_by_split={s:dict(Counter(r['label'] for r in rows if r['split']==s)) for s in counts},
                        exact_rc_unique_groups=len(groups),
                        duplicate_groups=[dict(group=g,rows=len(items),split=items[0]['split'])
                                          for g,items in groups.items() if len(items)>1],
                        cross_split_exact_rc_overlap=overlaps,
                        original_sources=sorted({r.get('dataset_source','GUE.zip frozen archive identity in row IDs') for r in rows}),
                        biological_positive_label='Unresolved from these numerical manifests; no relabeling',
                        source_locus_genome_homology_groups='Unavailable in supplied frozen manifests'))
result=dict(status='PASS_EXACT_COHORT_AND_NUMERIC_LABEL_CONSISTENCY',files=files,tasks=reports,
            wall_seconds=time.monotonic()-started,new_dataset_test_members_opened=0,
            interpretation='Exact/RC exclusion is not source-genome or homology independence. H3 test was previously explored.',
            scientific_changes='None: no resampling, relabeling, replacement, or cohort edits')
(root/'COHORT_IDENTITY_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['status'],len(tasks),'tasks',sum(len(x) for x in tasks.values()),'rows')
