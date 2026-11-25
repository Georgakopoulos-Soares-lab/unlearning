"""Bounded exact regular-member consumer; reject aliases and undeclared members."""
from pathlib import Path,PurePosixPath
import tarfile,hashlib

def restore(archive,manifest,destination,limits):
    destination=Path(destination);assert not destination.exists();destination.mkdir(parents=True);seen=set();expanded=0
    with tarfile.open(archive,'r|gz') as tar:
        for member in tar:
            name=member.name;q=PurePosixPath(name)
            assert member.isfile() and not q.is_absolute() and '..' not in q.parts and '\\' not in name and str(q)==name and name not in seen and name in manifest,'Unsafe, duplicate or unexpected member'
            seen.add(name);expanded+=member.size;assert len(seen)<=limits['members'] and expanded<=limits['expanded_bytes'] and member.size<=limits['member_bytes'],'Archive bounds exceeded';binding=manifest[name];assert member.size==binding['bytes'];p=destination/name;p.parent.mkdir(parents=True,exist_ok=True);h=hashlib.sha256();count=0
            with tar.extractfile(member) as source,p.open('xb') as target:
                while True:
                    b=source.read(1024**2)
                    if not b:break
                    count+=len(b);assert count<=member.size;h.update(b);target.write(b)
            assert count==member.size and h.hexdigest()==binding['sha256'],'Corrupt member'
    assert seen==set(manifest),'Missing archive member'
    return {'members':len(seen),'expanded_bytes':expanded}
