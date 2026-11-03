"""Local immutable recovery package for new benign results; never uploads credentials."""
import argparse,hashlib,json,tarfile,time
from pathlib import Path

def digest(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--archive',required=True);a=ap.parse_args();run=Path(a.run).resolve();archive=Path(a.archive).resolve();start=time.monotonic()
    if archive.is_relative_to(run):raise ValueError('Archive must be outside the payload directory')
    if archive.exists():raise FileExistsError('Do not overwrite an existing recovery archive')
    entries=list(run.rglob('*'))
    if any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in entries):raise ValueError('Only regular payload files/directories allowed')
    files=sorted(p for p in entries if p.is_file() and p.name!='CHECKSUMS.sha256')
    if any(p.is_symlink() for p in files):raise ValueError('Recovery payload must not contain symlinks')
    sums={p.relative_to(run).as_posix():digest(p) for p in files};(run/'CHECKSUMS.sha256').write_text(''.join(f'{h}  {name}\n' for name,h in sums.items()))
    with tarfile.open(archive,'w:gz',compresslevel=1) as tar:tar.add(run,arcname=run.name,recursive=True)
    # Independent archive readback without extracting over the original payload.
    checked=0
    with tarfile.open(archive,'r:gz') as tar:
        members={m.name:m for m in tar.getmembers() if m.isfile()}
        expected={run.name+'/'+name:h for name,h in sums.items()}
        if set(members)!=set(expected)|{run.name+'/CHECKSUMS.sha256'}:raise ValueError('Archive payload coverage')
        for name,h in expected.items():
            source=tar.extractfile(members[name]);actual=hashlib.file_digest(source,'sha256').hexdigest()
            if actual!=h:raise ValueError('Archive hash mismatch '+name)
            checked+=1
    h=digest(archive);archive.with_suffix(archive.suffix+'.sha256').write_text(h+'  '+archive.name+'\n')
    receipt=dict(archive=str(archive),sha256=h,bytes=archive.stat().st_size,payload_files_verified_by_archive_readback=checked,wall_seconds=time.monotonic()-start,off_pod_upload=False,off_pod_retrieval_verified=False,remote_revision=None,backup_status='LOCAL_VERIFIED; private upload pending securely configured authentication',scope='Contains new benign cached features/probes/predictions/manifests and source/runtime references; excludes model weights and installed environment')
    archive.with_suffix(archive.suffix+'.receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2),flush=True)
if __name__=='__main__':main()
