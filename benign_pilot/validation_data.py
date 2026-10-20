"""Read-only source, selection and provenance checks for saved pilot artifacts."""
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile

import numpy as np
from sklearn.model_selection import train_test_split

from .identity import BACKEND_SPEC, CHECKPOINT_SHA256, MODEL_REVISION, file_sha256

TASKS = {'gue_emp_h3':'EMP/H3','gue_prom_300_all':'prom/prom_300_all','gue_splice_reconstructed':'splice/reconstructed'}
LAYERS = ['blocks.7','blocks.15']
C_GRID = [0.1,1.,10.]


class ValidationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ValidationError(message)


def unique_object(pairs):
    result = {}
    for key,value in pairs:
        require(key not in result,f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def decode(text):
    def reject(token):
        raise ValidationError(f'Nonfinite JSON: {token}')
    return json.loads(text,object_pairs_hook=unique_object,parse_constant=reject)


def read_json(path):
    try:
        value = decode(Path(path).read_text())
    except (OSError,ValueError,TypeError) as exc:
        raise ValidationError(f'Invalid required JSON {path}: {exc}') from exc
    require(isinstance(value,(dict,list)),f'Invalid JSON structure: {path}')
    return value


def read_jsonl(path):
    try:
        rows = [decode(line) for line in Path(path).read_text().splitlines()]
    except (OSError,ValueError,TypeError) as exc:
        raise ValidationError(f'Invalid required JSONL {path}: {exc}') from exc
    require(bool(rows) and all(isinstance(r,dict) for r in rows),f'Empty/malformed required records: {path}')
    return rows


def text_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical_backend(files):
    result = {}
    require(isinstance(files,dict) and bool(files),'Missing backend source fingerprints')
    for path,digest in files.items():
        pieces = Path(path).parts
        start = next((i for i,part in enumerate(pieces) if part in ['evo2','vortex']),None)
        require(start is not None,f'Unexpected backend path: {path}')
        name = '/'.join(pieces[start:])
        require(name not in result,f'Duplicate backend path: {name}')
        result[name] = digest
    return result


def verify_provenance(run, config, source_root=None, expected_source_commit=None):
    context,smoke = read_json(run/'run_manifest.json'),read_json(run/'smoke_provenance.json')
    require(context.get('config')==config,'Execution configuration differs from saved configuration')
    config_sha,manifest_sha = text_sha(json.dumps(config,sort_keys=True)),file_sha256(run/'subset_manifest.jsonl')
    require(context.get('config_sha256')==config_sha,'Configuration hash does not match actual configuration')
    require(context.get('manifest_sha256')==manifest_sha,'Manifest hash does not match actual selected records')
    require(context.get('checkpoint_sha256')==CHECKPOINT_SHA256,'Wrong original checkpoint fingerprint')
    require(config.get('model_revision')==MODEL_REVISION,'Wrong checkpoint revision')
    require(config.get('model_repo')=='arcinstitute/evo2_1b_base' and config.get('model_name')=='evo2_1b_base','Wrong reference model')
    commit=context.get('source_commit')
    require(isinstance(commit,str) and len(commit)==40 and all(c in '0123456789abcdef' for c in commit),'Malformed inference source commit')
    if expected_source_commit is not None:
        require(commit==expected_source_commit,'Unexpected original inference source commit')
    source_root=Path(source_root) if source_root else run/'source-at-run'
    hashes=context.get('source_hashes')
    require(isinstance(hashes,dict) and bool(hashes),'Missing inference source fingerprints')
    for relative,digest in hashes.items():
        path=Path(relative)
        require(not path.is_absolute() and '..' not in path.parts,f'Unsafe source path: {relative}')
        require((source_root/path).is_file(),f'Missing inference source snapshot: {relative}')
        require(file_sha256(source_root/path)==digest,f'Inference source fingerprint mismatch: {relative}')
    trusted=read_json(BACKEND_SPEC)
    require(canonical_backend(context.get('backend_files'))==trusted['files'],'Recorded backend differs from independently pinned official source')
    for name,version in trusted['packages'].items():
        require(context.get('packages',{}).get(name)==version,f'Recorded backend package mismatch: {name}')
    require(config.get('evo2_revision')==trusted['evo2_commit'],'Wrong official Evo2 source revision')
    for key in ['manifest_sha256','config_sha256','checkpoint_sha256','source_hashes','packages','backend_files','source_commit']:
        require(context.get(key)==smoke.get(key),f'Smoke/execution provenance mismatch: {key}')
    actual=dict(manifest=manifest_sha,config=config_sha,checkpoint=CHECKPOINT_SHA256,
                source={p:file_sha256(source_root/p) for p in hashes},packages=context['packages'],backend=context['backend_files'])
    return context,text_sha(json.dumps(actual,sort_keys=True))


def independent_normalize(value):
    value=''.join(value.upper().split())
    require(bool(value) and not set(value)-set('ACGTRYSWKMBDHVN'),'Unsupported source nucleotide alphabet')
    return ''.join(base if base in 'ACGT' else 'N' for base in value)


def independent_overlap(rows):
    answer={}
    complement=str.maketrans('ACGTN','TGCAN')
    for field in ['full_sequence','sequence']:
        for canonical in [False,True]:
            groups=defaultdict(list)
            for row in rows:
                sequence=row[field]
                key=min(sequence,sequence.translate(complement)[::-1]) if canonical else sequence
                groups[key].append({'id':row['id'],'split':row['split']})
            duplicates=[members for members in groups.values() if len(members)>1]
            key=field+('_reverse_complement_canonical' if canonical else '_exact')
            answer[key]=dict(within_split_groups=sum(any(sum(m['split']==s for m in g)>1 for s in ['train','validation']) for g in duplicates),
                             cross_split_groups=sum(len({m['split'] for m in g})>1 for g in duplicates),groups=duplicates)
    return answer


def verify_dataset(run,config,manifest,archive):
    require(archive is not None,'Official train/dev archive required for sequence and split verification')
    require(file_sha256(archive)==config.get('data_archive_sha256'),'GUE source archive checksum mismatch')
    recorded=read_json(run/'data_provenance.json')
    require(set(recorded)==set(TASKS),'Missing/unexpected data-provenance tasks')
    results={}
    with zipfile.ZipFile(archive) as source:
        for task,directory in TASKS.items():
            task_rows=[r for r in manifest if r['task']==task];full_rows=[]
            for split,filename,limit in [('train','train.csv',config['train_size']),('validation','dev.csv',config['validation_size'])]:
                selected=[r for r in task_rows if r['split']==split]
                matches=[n for n in source.namelist() if n.endswith('/'+directory+'/'+filename)]
                require(len(matches)==1,f'Unresolved official task/split: {task}/{filename}')
                raw=source.read(matches[0])  # Test contents are never opened.
                records=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))));labels=[int(r['label']) for r in records]
                meta=recorded[task][split]
                require(meta['source_member']==matches[0] and meta['source_sha256']==hashlib.sha256(raw).hexdigest(),f'Source-member mismatch: {task}/{split}')
                require(meta['source_rows']==len(records) and meta['source_class_counts']=={str(k):v for k,v in Counter(labels).items()},f'Source counts mismatch: {task}/{split}')
                require(set(labels)==set(config['label_schemas'][task]),f'Source label schema mismatch: {task}')
                expected=np.arange(len(records))
                if len(expected)>limit:
                    expected,_=train_test_split(expected,train_size=limit,stratify=labels,random_state=config['seed'])
                expected=sorted(int(i) for i in expected)
                require([r['original_row_index'] for r in selected]==expected,f'Selected row/order mismatch: {task}/{split}')
                require(meta['selected_class_counts']=={str(k):v for k,v in Counter(r['label'] for r in selected).items()},f'Selected class-count mismatch: {task}/{split}')
                for row,index in zip(selected,expected):
                    raw_row=records[index];full=independent_normalize(raw_row['sequence']);prefix=full[:config['max_length']]
                    values=dict(id=raw_row.get('id') or f'{task}:{filename}:{index}',task=task,split=split,label=labels[index],sequence=prefix,
                        full_sequence_sha256=text_sha(full),scored_prefix_sha256=text_sha(prefix),original_length=len(full),scored_length=len(prefix),
                        truncated=len(full)>len(prefix),ambiguous_bases_scored=prefix.count('N'),dataset_source=config['data_source_revision'],
                        group_id=raw_row.get('group') or raw_row.get('group_id') or None)
                    require(all(row.get(k)==v for k,v in values.items()),f'Sequence/ID/label/normalization mismatch: {task}/{split}/{index}')
                    full_rows.append(dict(row,full_sequence=full))
            overlaps=independent_overlap(full_rows)
            for name,actual in overlaps.items():
                require(actual==recorded[task]['overlap'].get(name),f'Exact/RC overlap mismatch: {task}/{name}')
                require(actual['cross_split_groups']==0,f'Ineligible task has train/dev overlap: {task}/{name}')
            results[task]=dict(train_count=sum(r['split']=='train' for r in task_rows),validation_count=sum(r['split']=='validation' for r in task_rows),
                class_counts={s:dict(Counter(r['label'] for r in task_rows if r['split']==s)) for s in ['train','validation']},overlap=overlaps)
    return results
