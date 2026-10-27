"""Package a new H3 follow-up supplement without changing original evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import tarfile


def sha(path):
    return hashlib.file_digest(Path(path).open('rb'),'sha256').hexdigest()


def package(run,archive):
    required=['protocol.json','verification.json','FOLLOWUP_RESULTS.md','HANDOFF.md','environment_lock.txt','input_manifest.jsonl','source_delivery.bundle']
    for name in required:
        if not (run/name).is_file():raise ValueError('Required evidence missing: '+name)
    if not json.loads((run/'verification.json').read_text())['passed']:raise ValueError('Verification failed')
    if archive.exists():raise ValueError('Do not overwrite existing archives')
    files=sorted(p for p in run.rglob('*') if p.is_file() and p.name not in ['CHECKSUMS.sha256','INVENTORY.json'])
    inventory=[]
    for p in files:
        if p.is_symlink():raise ValueError('Symlink forbidden')
        if p.suffix in ['.json','.jsonl','.py','.txt','.md','.log'] and re.search(rb'hf_[A-Za-z0-9]{25,}',p.read_bytes()):
            raise ValueError('Credential-like text: '+p.name)
        inventory.append(dict(path=str(p.relative_to(run)),sha256=sha(p),bytes=p.stat().st_size))
    (run/'INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (run/'CHECKSUMS.sha256').write_text(''.join(f'{x["sha256"]}  {x["path"]}\n' for x in inventory))
    with tarfile.open(archive,'w:gz') as t:
        for p in [*files,run/'INVENTORY.json',run/'CHECKSUMS.sha256']:
            t.add(p,arcname=str(Path(run.name)/p.relative_to(run)),recursive=False)
    digest=sha(archive);side=Path(str(archive)+'.sha256');side.write_text(f'{digest}  {archive.name}\n')
    verified=0
    with tarfile.open(archive) as t:
        for m in t.getmembers():
            if Path(m.name).is_absolute() or '..' in Path(m.name).parts or not m.isfile():raise ValueError('Unsafe archive member')
        for record in inventory:
            stream=t.extractfile(str(Path(run.name)/record['path']))
            if hashlib.file_digest(stream,'sha256').hexdigest()!=record['sha256']:raise ValueError('Packaged checksum mismatch')
            verified+=1
    receipt=dict(archive=str(archive),sha256=digest,bytes=archive.stat().st_size,payload_files_verified=verified,
        local_archive_verification='Passed; archive members and payload hashes inspected without executing contents',
        remote_status='PENDING_REPLACEMENT_AUTHENTICATION',hf_revision=None,uploaded=False,fresh_remote_download_verified=False,
        reason='Configured replacement authentication returned401; previously exposed chat credential was not reused',
        utc=datetime.now(timezone.utc).isoformat())
    Path(str(archive)+'.receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--archive',required=True,type=Path);a=p.parse_args();package(a.run,a.archive)
