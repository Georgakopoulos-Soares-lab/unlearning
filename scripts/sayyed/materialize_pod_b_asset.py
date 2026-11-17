"""Read one scoped download URL from stdin; never persist or print that URL."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

spec = json.loads(sys.stdin.readline())
target = Path(spec['path'])
if target.exists():
    raise ValueError('Refusing to overwrite an asset')
target.parent.mkdir(parents=True, exist_ok=True)
temporary = target.with_name('.' + target.name + '.partial')
try:
    with urllib.request.urlopen(spec['download_url'], timeout=120) as response, temporary.open('xb') as out:
        while block := response.read(8 * 1024 * 1024):
            out.write(block)
    if temporary.stat().st_size != spec['bytes']:
        raise ValueError('Asset byte count mismatch')
    with temporary.open('rb') as stream:
        sha = hashlib.file_digest(stream, 'sha256').hexdigest()
    temporary.replace(target)
    receipt = dict(drive_id=spec['drive_id'], path=str(target), bytes=spec['bytes'],
                   sha256=sha, route='authenticated Drive connector streamed file reference')
    target.with_name(target.name + '.download.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)
except Exception as exc:
    # Network exception messages may include signed URLs.
    print(type(exc).__name__ + ': download failed; inspect status without logging URL', file=sys.stderr)
    raise SystemExit(1)
