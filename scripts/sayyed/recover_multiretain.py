"""Restore the exact pinned MaxEnt payload without touching historical outputs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import time
from scripts.sayyed.multiretain_support import atomic_json


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate_members(members):
    seen = set()
    for member in members:
        name = PurePosixPath(member.name)
        if (name.is_absolute() or '..' in name.parts or '\\' in member.name
                or not name.parts or name.parts[0] != 'maxent-benign-v16'
                or not (member.isdir() or member.isfile()) or str(name) in seen):
            raise ValueError('Unsafe or duplicate archive member: ' + member.name)
        seen.add(str(name))


def restore(archive, sidecar, destination, inputs):
    archive, sidecar, destination = map(Path, (archive, sidecar, destination))
    if destination.exists():
        raise ValueError('Recovery destination already exists; choose a fresh identity')
    actual = digest(archive)
    if actual != inputs['OLD_BACKUP_SHA256'] or archive.stat().st_size != inputs['OLD_BACKUP_BYTES']:
        raise ValueError('Pinned archive identity mismatch')
    if sidecar.read_text().split()[0] != actual:
        raise ValueError('Sidecar mismatch')
    with tarfile.open(archive) as bundle:
        validate_members(bundle.getmembers())
        destination.mkdir(parents=True)
        bundle.extractall(destination, filter='data')
    root = destination / 'maxent-benign-v16'
    manifest = root / 'CHECKSUMS.sha256'
    count = 0
    checked = set()
    for line in manifest.read_text().splitlines():
        expected, relative = line.split(maxsplit=1)
        relative = relative.lstrip('*')
        name = PurePosixPath(relative)
        if name.is_absolute() or '..' in name.parts or '\\' in relative:
            raise ValueError('Unsafe checksum path')
        target = root / relative
        if str(name) in checked:
            raise ValueError('Duplicate checksum entry')
        checked.add(str(name))
        if digest(target) != expected:
            raise ValueError('Payload checksum mismatch: ' + relative)
        count += 1
    if count != 5914:
        raise ValueError(f'Unexpected pinned payload count: {count}')
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual_files != checked | {'CHECKSUMS.sha256'}:
        raise ValueError('Incomplete payload checksum coverage')
    result = dict(status='RESTORED_CHECKSUM_VERIFIED', archive_sha256=actual,
                  archive_bytes=archive.stat().st_size, payloads_verified=count,
                  destination=str(destination), remote_revision=inputs['OLD_BACKUP_REVISION'],
                  gpu_seconds=0, saved_output_computation_verification='PENDING')
    atomic_json(destination / 'recovery_receipt.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--download-directory', required=True)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    inputs = json.loads(Path(args.inputs).read_text())
    from huggingface_hub import hf_hub_download
    started, cpu = time.monotonic(), time.process_time()
    files = [hf_hub_download(repo_id=inputs['HF_DATASET_REPO'], repo_type='dataset',
                            revision=inputs['OLD_BACKUP_REVISION'], filename=inputs[key],
                            local_dir=args.download_directory)
             for key in ('OLD_BACKUP_SIDECAR', 'OLD_BACKUP_ARCHIVE')]
    result = restore(files[1], files[0], args.destination, inputs)
    result.update(wall_seconds=time.monotonic()-started, cpu_process_seconds=time.process_time()-cpu)
    atomic_json(Path(args.destination) / 'recovery_receipt.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
