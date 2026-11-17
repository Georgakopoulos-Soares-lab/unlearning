"""Package Pod B qualification outputs, publish privately and verify a fresh recovery."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile
import time

from huggingface_hub import HfApi, CommitOperationAdd, hf_hub_download
from huggingface_hub._commit_api import _fetch_upload_modes

root=Path('/workspace/meeting-artifacts/relearning-benign-v1')
docs=Path('docs/experiments/ashay/relearning-benign-v1')



def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def safe_members(members,top):
    seen=set()
    for m in members:
        p=PurePosixPath(m.name)
        if (p.is_absolute() or '..' in p.parts or '\\' in m.name or not p.parts
                or p.parts[0]!=top or str(p) in seen or not (m.isfile() or m.isdir())):
            raise ValueError('Unsafe or duplicate archive member')
        seen.add(str(p))


def verify_payload(folder):
    checked=set()
    for line in (folder/'CHECKSUMS.sha256').read_text().splitlines():
        sha,relative=line.split(maxsplit=1)
        relative=relative.lstrip('*');p=PurePosixPath(relative)
        if p.is_absolute() or '..' in p.parts or '\\' in relative or relative in checked:
            raise ValueError('Unsafe checksum manifest')
        checked.add(relative)
        if digest(folder/relative)!=sha:
            raise ValueError('Payload checksum mismatch: '+relative)
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    if actual!=checked|{'CHECKSUMS.sha256'}:
        raise ValueError('Incomplete checksum coverage')
    return len(checked)


def main():
    stamp=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())
    name='relearning-benign-v1-qualification-'+stamp
    payload=root/'packages'/name
    payload.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()

    for folder in ['authorization','checkpoints','manifests','parent-smokes','throughput-training384',
                   'restored-head-smoke','candidate-loader']:
        shutil.copytree(root/folder,payload/folder)
    for path in root.iterdir():
        if path.is_file() and path.suffix in ['.json','.jsonl','.log','.txt']:
            shutil.copyfile(path,payload/path.name)
    shutil.copytree(docs,payload/'reports')
    (payload/'dependency-receipts').mkdir()
    for p in (root/'recovery').glob('*.json'):
        shutil.copyfile(p,payload/'dependency-receipts'/p.name)
    for folder in ['preservation','runtime-wheels']:
        for p in (root/'recovery'/folder).glob('*receipt.json'):
            shutil.copyfile(p,payload/'dependency-receipts'/(folder+'-'+p.name))
    (payload/'runtime-wheels').mkdir()
    wheel=root/'recovery/runtime-wheels/transformer_engine_torch-2.3.0-cp312-cp312-linux_x86_64.whl'
    if digest(wheel)!='557f6b27f5d05218e17932ce9f477ab461a073a590b73b781a18323e78169681':
        raise ValueError('Recovered TE extension wheel identity mismatch')
    shutil.copyfile(wheel,payload/'runtime-wheels'/wheel.name)

    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    source_tar=root/'packages'/(name+'-source.tar')
    with source_tar.open('wb') as stream:
        subprocess.run(['git','archive',source_commit,'scripts/sayyed','benign_pilot',
                        'tests/test_fixed_benign_batch.py','tests/test_multiretain_support.py','tests/test_pod_b_backup.py',
                        'docs/experiments/ashay/relearning-benign-v1'],stdout=stream,check=True)
    source=payload/'source';source.mkdir()
    with tarfile.open(source_tar) as bundle:
        members=bundle.getmembers()
        for m in members:
            p=PurePosixPath(m.name)
            if p.is_absolute() or '..' in p.parts or not (m.isfile() or m.isdir()):
                raise ValueError('Unsafe source archive member')
        bundle.extractall(source,filter='data')
    (payload/'SOURCE_SNAPSHOT.json').write_text(json.dumps(dict(commit=source_commit,
        runtime='Pinned external native sources and installed runtime excluded; see execution/runtime receipts',
        excluded='Parent weights, old large caches, installed environments, credentials, Git credential state',
        adapter_weights_included=True),indent=2)+'\n')

    patterns=[re.compile(rb'hf_[A-Za-z0-9]{24,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{30,}'),
              re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'Bearer [A-Za-z0-9._-]{24,}'),
              re.compile(rb'https://[^\s]+[?&](?:sig|token|access_token)=')]
    scanned=0
    for p in payload.rglob('*'):
        if not p.is_file() or p.stat().st_size>10*1024*1024:
            continue
        raw=p.read_bytes()
        try:raw.decode('utf-8')
        except UnicodeDecodeError:continue
        scanned+=1
        if any(pattern.search(raw) for pattern in patterns):
            raise ValueError('Credential-pattern match; packaging stopped without printing content')
    (payload/'CREDENTIAL_SCAN.json').write_text(json.dumps(dict(status='PASS',text_files_scanned=scanned,
        credential_values_logged=False,scope='Scoped text scan; credential stores never included'),indent=2)+'\n')
    files=sorted(p for p in payload.rglob('*') if p.is_file())
    (payload/'CHECKSUMS.sha256').write_text(''.join(digest(p)+'  '+p.relative_to(payload).as_posix()+'\n' for p in files))
    count=verify_payload(payload)
    print('PAYLOAD_VERIFIED',count,'files',flush=True)
    archive=root/'packages'/(name+'.tar.gz')
    with tarfile.open(archive,'w:gz',compresslevel=1) as bundle:
        for p in sorted(payload.rglob('*')):
            if p.is_file():bundle.add(p,arcname=name+'/'+p.relative_to(payload).as_posix(),recursive=False)
    sha=digest(archive)
    sidecar=archive.with_name(archive.name+'.sha256')
    sidecar.write_text(sha+'  '+archive.name+'\n')
    print('ARCHIVE_SEALED',archive.stat().st_size,'bytes',sha,flush=True)

    api=HfApi();repo='ashay-sriv/undo-evo2-pilot-backup-20261020'
    if api.dataset_info(repo).private is not True:
        raise ValueError('Private repository required')
    prefix='two-pod-20261116/pod-b/20261117T063321Z'
    remote_archive=prefix+'/'+archive.name
    remote_sidecar=prefix+'/'+sidecar.name
    if any(api.file_exists(repo,path,repo_type='dataset') for path in [remote_archive,remote_sidecar]):
        raise ValueError('Refusing to overwrite an existing backup')
    ops=[CommitOperationAdd(path_in_repo=remote_archive,path_or_fileobj=str(archive)),
         CommitOperationAdd(path_in_repo=remote_sidecar,path_or_fileobj=str(sidecar))]
    _fetch_upload_modes(additions=ops,repo_type='dataset',repo_id=repo,
                        headers=api._build_hf_headers(),revision='main')
    commit=api.create_commit(repo_id=repo,repo_type='dataset',operations=ops,
                             commit_message='Preserve Pod B checkpoint qualification and blocked scoring handoff')
    revision=commit.oid
    print('PRIVATE_UPLOAD_COMMITTED',revision,flush=True)
    fresh=root/'fresh-recovery'/stamp
    download=fresh/'download';download.mkdir(parents=True,exist_ok=False)
    retrieved=[Path(hf_hub_download(repo,filename,repo_type='dataset',revision=revision,
                                   force_download=True,local_dir=download))
               for filename in [remote_archive,remote_sidecar]]
    if (retrieved[0].stat().st_size!=archive.stat().st_size or digest(retrieved[0])!=sha
            or retrieved[1].read_bytes()!=sidecar.read_bytes()):
        raise ValueError('Fresh download archive/sidecar mismatch')
    dest=fresh/'extracted';dest.mkdir()
    with tarfile.open(retrieved[0]) as bundle:
        safe_members(bundle.getmembers(),name)
        bundle.extractall(dest,filter='data')
    restored=dest/name
    restored_count=verify_payload(restored)
    if restored_count!=count:
        raise ValueError('Restored checksum count mismatch')
    process=subprocess.run(['/workspace/venvs/evo2-pilot/bin/python',
                            str(restored/'source/scripts/sayyed/verify_pod_b_restored_heads.py'),str(restored)],
                           env={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1'},
                           text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
    head_check=json.loads(process.stdout)
    result=dict(status='VERIFIED_PRIVATE_FRESH_DOWNLOAD',repo=repo,revision=revision,
                remote_archive_path=remote_archive,remote_sidecar_path=remote_sidecar,
                sha256=sha,bytes=archive.stat().st_size,payload_root=name,payload_files=count,
                fresh_payload=str(restored),source_snapshot_commit=source_commit,
                private_repository_verified=True,upload_permission_preflight=True,
                full_payload_checksums=True,safe_extraction=True,restored_head_check=head_check,
                wall_seconds=time.monotonic()-started,credentials_persisted=False,
                dependencies='Parent weights/runtime excluded; historical full caches remain separately pinned',
                scientific_status='Qualification complete; actual supplied-model scoring remains blocked')
    (root/'BACKUP_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    (docs/'BACKUP_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FRESH_RECOVERY_VERIFIED',revision,count,'payload files',flush=True)


if __name__ == "__main__":
    main()
