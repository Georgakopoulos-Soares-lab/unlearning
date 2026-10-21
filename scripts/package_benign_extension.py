"""Package only the new run and explicit source files; never include credentials/assets."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

RUN=Path('/workspace/meeting-artifacts/evo2-extension-20261021T0942')
PACKAGE=RUN.parent/'evo2-extension-20261021T0942-supplement.tar.gz'


def sha(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main():
    if PACKAGE.exists():raise FileExistsError('Preserve existing recovery archive; use a new version')
    snapshot=RUN/'source_snapshot';snapshot.mkdir(exist_ok=True)
    paths=[Path('AGENTS.md'),*Path('benign_pilot').glob('*.py'),Path('configs/benign_extension.json'),Path('configs/evo2_backend_identity.json'),Path('requirements-pilot.txt'),Path('scripts/report_benign_extension.py'),Path('scripts/diagnose_extension_shuffle.py'),Path('scripts/package_benign_extension.py'),Path('scripts/fit_completed_extension.py'),Path('scripts/verify_benign_extension.py'),Path('tests/test_benign_extension.py'),*Path('docs/experiments/ashay/extension').glob('*')]
    for path in paths:
        if not path.is_file():continue
        target=snapshot/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    files=[p for p in sorted(RUN.rglob('*')) if p.is_file() and p.name not in ['INVENTORY.json','CHECKSUMS.sha256']]
    if any(p.is_symlink() for p in files):raise ValueError('No symlinks in recovery allowlist')
    inventory={str(p.relative_to(RUN)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
    (RUN/'INVENTORY.json').write_text(json.dumps(inventory,indent=2)+'\n');(RUN/'CHECKSUMS.sha256').write_text(''.join(v['sha256']+'  '+k+'\n' for k,v in inventory.items()))
    files.extend([RUN/'INVENTORY.json',RUN/'CHECKSUMS.sha256'])
    with tarfile.open(PACKAGE,'w:gz',compresslevel=3) as out:
        for path in files:out.add(path,arcname=RUN.name+'/'+str(path.relative_to(RUN)),recursive=False)
    # Verify every packaged member against inventory without extracting over a run.
    with tarfile.open(PACKAGE,'r:gz') as source:
        members=source.getmembers()
        if any(not m.isfile() or Path(m.name).is_absolute() or '..' in Path(m.name).parts for m in members):raise ValueError('Unsafe recovery member')
        actual={m.name.removeprefix(RUN.name+'/'):m for m in members}
        if set(actual)!=set(inventory)|{'INVENTORY.json','CHECKSUMS.sha256'}:raise ValueError('Archive inventory mismatch')
        for name,v in inventory.items():
            if hashlib.file_digest(source.extractfile(actual[name]),'sha256').hexdigest()!=v['sha256']:raise ValueError('Archive member digest mismatch: '+name)
    digest=sha(PACKAGE);PACKAGE.with_suffix(PACKAGE.suffix+'.sha256').write_text(digest+'  '+PACKAGE.name+'\n')
    receipt=dict(new_supplement=str(PACKAGE),sha256=digest,bytes=PACKAGE.stat().st_size,members_verified=len(inventory),status='NEW SUPPLEMENT EXTERNAL BACKUP PENDING: secure local HF login required; old backup remains verified',old_backup_revision='72d0fe216ca7893f4ef3856fcf9c3c7e955faf9b',credentials_included=False,weights_raw_data_environments_included=False)
    (RUN.parent/'evo2-extension-20261021T0942-backup_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
