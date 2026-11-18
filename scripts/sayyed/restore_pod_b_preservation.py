"""Offline byte verification/restoration for the POD_B preservation package.

No network, pickle, model imports, inference, environment activation or symlink
creation. Run only against pinned, independently authenticated manifests/parts.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile

HEX=re.compile(r'^[0-9a-f]{64}$')

def digest(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def safe_relative(value):
    p=PurePosixPath(value)
    if p.is_absolute()or not p.parts or any(x in {'..','.'}for x in p.parts)or '\\'in value:
        raise ValueError('Unsafe relative archive/manifest path')
    return Path(*p.parts)

def checked_archive(path,expected,output,objects,seen):
    if path.stat().st_size!=expected['bytes']or digest(path)!=expected['sha256']:
        raise ValueError('Compressed archive identity mismatch: '+path.name)
    proc=subprocess.Popen(['zstd','-d','-q','-c','--',str(path)],stdout=subprocess.PIPE)
    count=0;total=0
    try:
        with tarfile.open(fileobj=proc.stdout,mode='r|')as t:
            for member in t:
                if not member.isfile()or member.size<0 or member.size>256*1024**2:
                    raise ValueError('Unsupported member type or size')
                rel=safe_relative(member.name)
                if objects:
                    parts=rel.parts
                    if len(parts)!=3 or parts[0]!='objects'or not HEX.fullmatch(parts[2])or parts[1]!=parts[2][:2]:
                        raise ValueError('Unexpected content-addressed member')
                    expected_hash=parts[2]
                else:
                    if rel.parts[0]!='metadata':raise ValueError('Unexpected metadata archive namespace')
                    expected_hash=None
                key=str(rel)
                if key in seen:raise ValueError('Duplicate archive member')
                seen.add(key);dest=output/rel;dest.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();n=0
                with t.extractfile(member)as src,dest.open('xb')as dst:
                    while True:
                        data=src.read(4*1024*1024)
                        if not data:break
                        h.update(data);dst.write(data);n+=len(data)
                if n!=member.size or expected_hash is not None and h.hexdigest()!=expected_hash:
                    raise ValueError('Uncompressed object identity mismatch')
                count+=1;total+=n
    finally:
        proc.stdout.close();rc=proc.wait()
    if rc:raise ValueError('zstd decompression failed')
    return dict(members=count,bytes=total)

def verify(manifest_path,download_root,output,expected_manifest_hash,restore=False):
    if digest(manifest_path)!=expected_manifest_hash:raise ValueError('Top-level manifest SHA256 mismatch')
    m=json.loads(manifest_path.read_text())
    output=output.resolve()
    if output.exists():raise ValueError('Fresh output directory required')
    output.mkdir(parents=True,exist_ok=False)
    seen=set();parts=[]
    for entry in m['payload_parts']:
        path=download_root/safe_relative(entry['filename'])
        parts.append(checked_archive(path,entry,output,True,seen))
    e=m['metadata_archive'];checked_archive(download_root/safe_relative(e['filename']),e,output,False,seen)
    mf=output/safe_relative(m['backed_file_manifest']['path'])
    if digest(mf)!=m['backed_file_manifest']['sha256']:raise ValueError('Backed-file manifest mismatch')
    files=0;symlinks=0;bytes_total=0;restored=0;file_paths=set();multi=0
    with mf.open()as f:
        for line in f:
            row=json.loads(line);rel=safe_relative(row['archive_path'])
            if str(rel)in file_paths:raise ValueError('Duplicate restored path')
            file_paths.add(str(rel))
            if row['backed_kind']=='symlink_metadata':
                if hashlib.sha256(row['link_target'].encode()).hexdigest()!=row['sha256']:
                    raise ValueError('Symlink metadata hash mismatch')
                symlinks+=1;continue
            chunks=row['chunks'];size=0;h=hashlib.sha256();dest=output/'restored-files'/rel if restore else None
            if dest:dest.parent.mkdir(parents=True,exist_ok=True)
            dst=dest.open('xb')if dest else None
            try:
                for c in chunks:
                    if not HEX.fullmatch(c['sha256']):raise ValueError('Malformed chunk hash')
                    p=output/'objects'/c['sha256'][:2]/c['sha256']
                    if not p.is_file()or p.stat().st_size!=c['bytes']:raise ValueError('Missing chunk or size mismatch')
                    size+=c['bytes']
                    # Every object was byte-hashed during archive extraction.
                    # A one-chunk file is exactly that verified object.
                    if len(chunks)==1 and not restore:continue
                    with p.open('rb')as src:
                        while True:
                            data=src.read(4*1024*1024)
                            if not data:break
                            h.update(data)
                            if dst:dst.write(data)
                calculated=chunks[0]['sha256']if len(chunks)==1 and not restore else h.hexdigest()
                if calculated!=row['sha256']or size!=row['backed_bytes']:raise ValueError('Reconstructed file identity mismatch')
                if dest:dest.chmod(row['mode']&0o777);restored+=1
                files+=1;bytes_total+=size;multi+=len(chunks)>1
            finally:
                if dst:dst.close()
    return dict(status='PASS',regular_files_verified=files,symlink_metadata_verified=symlinks,regular_file_bytes=bytes_total,multichunk_files_reconstructed_and_hashed=multi,regular_files_materialized=restored,payload_parts_verified=len(parts),objects_verified=sum(x['members']for x in parts),unique_object_bytes=sum(x['bytes']for x in parts),symlinks_created=0,model_imported=False,network_access=False,restore_root=str(output))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--download-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--restore-files',action='store_true');a=p.parse_args()
    result=verify(a.manifest,a.download_root,a.output,a.manifest_sha256,a.restore_files)
    (a.output/'RESTORE_VERIFICATION.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
