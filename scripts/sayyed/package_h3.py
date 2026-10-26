"""Create a credential-free H3 recovery archive with a payload inventory."""
import hashlib
import json
from pathlib import Path
import re
import tarfile

RUN=Path('/workspace/meeting-artifacts/sayyed-base-20261026-v1')


def main():
    for name in ['metrics.json','independent_verification.json','extraction_complete.json','head_execution_identity.json']:
        if not (RUN/name).is_file():raise ValueError('Incomplete run: '+name)
    if not json.loads((RUN/'independent_verification.json').read_text())['passed']:raise ValueError('Verification failed')
    files=sorted(p for p in RUN.rglob('*') if p.is_file() and p.name not in ['CHECKSUMS.sha256','INVENTORY.json'] and not p.name.endswith('.partial'))
    inventory=[]
    for p in files:
        if p.is_symlink():raise ValueError('Symlink forbidden')
        if p.suffix in ['.json','.txt','.md','.py','.log']:
            if re.search(rb'hf_[A-Za-z0-9]{25,}',p.read_bytes()):raise ValueError('Credential-like content: '+p.name)
        inventory.append(dict(path=str(p.relative_to(RUN)),size=p.stat().st_size,sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()))
    (RUN/'INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n')
    (RUN/'CHECKSUMS.sha256').write_text(''.join(f'{x["sha256"]}  {x["path"]}\n' for x in inventory))
    archive=RUN.parent/(RUN.name+'-recovery.tar.gz')
    if archive.exists():raise ValueError('Archive already exists; do not overwrite')
    with tarfile.open(archive,'w:gz') as t:
        for p in [*files,RUN/'INVENTORY.json',RUN/'CHECKSUMS.sha256']:
            t.add(p,arcname=str(Path(RUN.name)/p.relative_to(RUN)),recursive=False)
    digest=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
    Path(str(archive)+'.sha256').write_text(f'{digest}  {archive.name}\n')
    print(json.dumps(dict(archive=str(archive),sha256=digest,files=len(files),bytes=archive.stat().st_size)))


if __name__=='__main__':main()
