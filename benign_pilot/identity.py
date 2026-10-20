"""Pinned original-reference identity and immutable resume provenance."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import uuid

MODEL_REVISION = '2279e1df422c991037470302360edd40d0d2ea1e'
CHECKPOINT_SHA256 = '8ffba7d0e6445a8f2c92d9ff1c4e772c7f73ca9179f5e0c699b8b0ca1b966f64'
BACKEND_SPEC = Path(__file__).resolve().parents[1]/'configs/evo2_backend_identity.json'
COMPATIBILITY_FIELDS = ('manifest_sha256','config_sha256','checkpoint_sha256','source_hashes','packages','backend_files')


def file_sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def checkpoint_identity(path):
    measured = file_sha256(path)
    if measured != CHECKPOINT_SHA256:
        raise ValueError(f'Original Evo2-1B checkpoint checksum mismatch: {measured}')
    return measured


def backend_identity():
    spec = json.loads(BACKEND_SPEC.read_text())
    for name,version in spec['packages'].items():
        if importlib.metadata.version(name) != version:
            raise ValueError(f'Pinned backend package mismatch: {name}')
    direct = importlib.metadata.distribution('evo2').read_text('direct_url.json')
    if not direct or json.loads(direct).get('vcs_info',{}).get('commit_id') != spec['evo2_commit']:
        raise ValueError('Evo2 distribution is not the pinned official source commit')
    roots = {name:Path(importlib.util.find_spec(name).origin).parent for name in ['evo2','vortex']}
    measured = {f'{name}/{path.relative_to(root)}':file_sha256(path)
                for name,root in roots.items() for path in root.rglob('*.py')}
    if measured != spec['files']:
        raise ValueError('Installed backend source differs from verified pinned source')
    for key,digest in spec['configuration_files'].items():
        name,relative = key.split('/',1)
        if file_sha256(roots[name]/relative) != digest:
            raise ValueError(f'Pinned model architecture configuration mismatch: {key}')
    return {str(roots[name]/relative):digest for key,digest in measured.items()
            for name,relative in [key.split('/',1)]}


def cache_key(context):
    fields = dict(manifest=context['manifest_sha256'],config=context['config_sha256'],
                  checkpoint=context['checkpoint_sha256'],source=context['source_hashes'],
                  packages=context['packages'],backend=context['backend_files'])
    return hashlib.sha256(json.dumps(fields,sort_keys=True).encode()).hexdigest()


def execution_provenance(run, candidate, stage):
    """Check before writing; retain the first execution record byte-for-byte."""
    run = Path(run)
    attempts = run/'resume_attempts'
    attempts.mkdir(parents=True,exist_ok=True)
    record = dict(utc=datetime.now(timezone.utc).isoformat(),stage=stage,
                  candidate=candidate,accepted=False,original_inference_source_commit=None)
    destination = attempts/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex+'.json')
    existing_path = run/'run_manifest.json'
    try:
        if not isinstance(candidate,dict) or any(field not in candidate for field in COMPATIBILITY_FIELDS):
            raise ValueError('Incomplete attempted execution provenance')
        references = []
        if existing_path.exists():
            previous = json.loads(existing_path.read_text())
            record['original_inference_source_commit'] = previous.get('source_commit')
            references.append(('execution',previous))
        if stage == 'pilot':
            if not (run/'model_smoke_results.json').is_file() or not (run/'smoke_provenance.json').is_file():
                raise ValueError('Complete a compatible smoke stage before pilot execution')
            references.append(('smoke',json.loads((run/'smoke_provenance.json').read_text())))
        for label,previous in references:
            for field in COMPATIBILITY_FIELDS:
                if field not in candidate or previous.get(field) != candidate[field]:
                    raise ValueError(f'{label.capitalize()} provenance mismatch: {field}')
        record['accepted'] = True
        if not existing_path.exists():
            # Exclusive creation prevents accidental replacement by another writer.
            with existing_path.open('x') as stream:
                json.dump(candidate,stream,indent=2,allow_nan=False)
    except Exception as exc:
        record['rejection'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        destination.write_text(json.dumps(record,indent=2,allow_nan=False))
    return candidate
