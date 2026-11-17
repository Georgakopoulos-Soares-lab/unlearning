"""Restore pinned scientific dependencies into fresh Pod B directories."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import time

from huggingface_hub import hf_hub_download


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    root = Path('/workspace/meeting-artifacts/relearning-benign-v1/recovery')
    root.mkdir(parents=True, exist_ok=True)
    inputs = json.loads(Path('docs/experiments/ashay/incremental-retain-eval-v1/RESTORE_DEPENDENCIES.json').read_text())
    for key in ('base_h3_archive', 'controls_archive', 'R3_archive'):
        spec = inputs[key]
        dest = root / key
        receipt = root / (key + '.json')
        if receipt.exists():
            raise RuntimeError('Dependency already restored; inspect receipt rather than overwrite')
        started = time.monotonic()
        repo = spec.get('repo', spec.get('remote_repository'))
        revision = spec.get('revision', spec.get('remote_revision'))
        filename = spec.get('archive', spec.get('remote_archive_path'))
        paths = [Path(hf_hub_download(repo, f, repo_type='dataset', revision=revision,
                                    local_dir=root / 'downloads'))
                 for f in (filename + '.sha256', filename)]
        sidecar, archive = paths
        if archive.stat().st_size != spec['bytes'] or digest(archive) != spec['sha256']:
            raise ValueError('Pinned archive identity mismatch: ' + key)
        if sidecar.read_text().split()[0] != spec['sha256']:
            raise ValueError('Sidecar mismatch')
        if dest.exists():
            raise ValueError('Fresh extraction directory required')
        with tarfile.open(archive) as bundle:
            members = bundle.getmembers()
            seen = set()
            for member in members:
                name = PurePosixPath(member.name)
                if (name.is_absolute() or '..' in name.parts or '\\' in member.name
                        or not name.parts or name.parts[0] != spec['payload_root']
                        or not (member.isdir() or member.isfile()) or str(name) in seen):
                    raise ValueError('Unsafe or duplicate member: ' + member.name)
                seen.add(str(name))
            dest.mkdir()
            bundle.extractall(dest, filter='data')
        payload = dest / spec['payload_root']
        checked = set()
        for line in (payload / 'CHECKSUMS.sha256').read_text().splitlines():
            expected, relative = line.split(maxsplit=1)
            relative = relative.lstrip('*')
            name = PurePosixPath(relative)
            if name.is_absolute() or '..' in name.parts or '\\' in relative or str(name) in checked:
                raise ValueError('Unsafe or duplicate checksum path')
            checked.add(str(name))
            if digest(payload / relative) != expected:
                raise ValueError('Payload checksum mismatch: ' + relative)
        actual = {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
        if actual != checked | {'CHECKSUMS.sha256'}:
            raise ValueError('Incomplete checksum coverage')
        result = dict(status='RESTORED_CHECKSUM_VERIFIED', dependency=key, revision=revision,
                      archive_sha256=spec['sha256'], bytes=spec['bytes'], payload=str(payload),
                      payload_files=len(checked), wall_seconds=time.monotonic()-started)
        receipt.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
