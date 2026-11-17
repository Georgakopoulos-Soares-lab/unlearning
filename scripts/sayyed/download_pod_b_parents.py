"""Reacquire only the two declared parents, against trusted historical hashes."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import time

import requests
from bs4 import BeautifulSoup

root = Path('/workspace/meeting-artifacts/relearning-benign-v1')
old = root / 'recovery/base_h3_archive/multiretain-layers-v1-final-20261110T140836Z'
if not (root / 'recovery/base_h3_archive.json').exists():
    raise ValueError('Historical archive must pass complete payload verification first')


def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def download(job):
    series, item = job
    folder = root / 'parents' / series
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / item['name']
    if path.exists():
        if path.stat().st_size == item['bytes'] and digest(path) == item['sha256']:
            return item
        raise ValueError('Existing parent asset mismatch')
    session = requests.Session()
    response = session.get('https://drive.google.com/uc',
                           params={'export': 'download', 'id': item['id']}, stream=True, timeout=120)
    if 'text/html' in response.headers.get('Content-Type', ''):
        form = BeautifulSoup(response.text, 'html.parser').find('form')
        if form is None:
            raise ValueError('No Drive confirmation form')
        params = {i['name']: i.get('value', '') for i in form.find_all('input') if i.get('name')}
        response = session.get(form['action'], params=params, stream=True, timeout=120)
    response.raise_for_status()
    temporary = path.with_name('.' + path.name + '.partial')
    with temporary.open('xb') as stream:
        for block in response.iter_content(8 * 1024 * 1024):
            stream.write(block)
    if temporary.stat().st_size != item['bytes'] or digest(temporary) != item['sha256']:
        raise ValueError('Parent hash or size mismatch')
    temporary.replace(path)
    return item


started = time.monotonic()
base = json.loads((old / 'base_download_receipt.json').read_text())
post = json.loads((old / 'maxent_download_receipt.json').read_text())
jobs = [('base', f) for f in base] + [('maxent', dict(name='__0_0.distcp', id=post['file_id'],
                                                 bytes=post['bytes'], sha256=post['sha256']))]
with ThreadPoolExecutor(max_workers=4) as pool:
    for i, result in enumerate(pool.map(download, jobs)):
        if i % 20 == 0:
            print('Verified parent files', i + 1, '/', len(jobs), flush=True)
for series in ('base', 'maxent'):
    source = old / 'checkpoint-assets' / series
    for p in source.iterdir():
        if p.is_file() and not p.name.endswith('.distcp'):
            dest = root / 'parents' / series / p.name
            if dest.exists():
                raise ValueError('Do not overwrite existing metadata')
            shutil.copyfile(p, dest)
(root / 'PARENT_DOWNLOAD_COMPLETE.json').write_text(json.dumps(dict(
    status='HASH_VERIFIED', files=len(jobs), wall_seconds=time.monotonic()-started,
    pinned_base_files=base, pinned_maxent=post), indent=2) + '\n')
print('Both declared parent payloads hash-verified', flush=True)
