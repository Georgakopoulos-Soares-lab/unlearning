"""Download only inventoried Pod B assets; preserve bytes and immutable receipts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import time

import requests
from bs4 import BeautifulSoup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--weights', action='store_true')
    ap.add_argument('--tokenizers', action='store_true')
    args = ap.parse_args()
    root = Path('/workspace/meeting-artifacts/relearning-benign-v1')
    inventory = json.loads((root / 'DRIVE_INVENTORY.json').read_text())
    jobs = []
    tokenizer_files = {f['id']: f['files'] for f in json.loads((root / 'TOKENIZER_INVENTORY.json').read_text())} if args.tokenizers else {}
    for node in inventory['checkpoints']:
        dest = root / 'checkpoints' / node['series'] / f"iter_{node['step']:07d}"
        dest.mkdir(parents=True, exist_ok=True)
        for f in node['files']:
            if args.tokenizers:
                if f['title'] == 'tokenizer':
                    token_dest = dest / 'tokenizer'
                    token_dest.mkdir(exist_ok=True)
                    jobs.extend((token_dest, child) for child in tokenizer_files[f['id']])
                continue
            if f['file_or_folder'] == 'folder':
                continue
            if f['title'].endswith('.distcp') != args.weights:
                continue
            jobs.append((dest, f))

    def one(job):
        dest, f = job
        path = dest / f['title']
        receipt = dest / (f['title'] + '.download.json')
        if receipt.exists():
            old = json.loads(receipt.read_text())
            if old['drive_id'] != f['id'] or old['bytes'] != path.stat().st_size:
                raise ValueError('Existing receipt mismatch')
            return old
        started = time.monotonic()
        if not path.exists():
            tmp = dest / ('.' + f['title'] + '.partial')
            session = requests.Session()
            response = session.get('https://drive.google.com/uc',
                                   params={'export': 'download', 'id': f['id']},
                                   stream=True, timeout=120)
            if 'text/html' in response.headers.get('Content-Type', ''):
                form = BeautifulSoup(response.text, 'html.parser').find('form')
                if form is None:
                    raise ValueError('No Drive confirmation form: ' + f['id'])
                params = {i['name']: i.get('value', '') for i in form.find_all('input') if i.get('name')}
                response = session.get(form['action'], params=params, stream=True, timeout=120)
            response.raise_for_status()
            with tmp.open('xb') as stream:
                for block in response.iter_content(8 * 1024 * 1024):
                    stream.write(block)
            if tmp.stat().st_size != int(f['size']):
                raise ValueError('Downloaded size mismatch: ' + f['id'])
            tmp.replace(path)
        if path.stat().st_size != int(f['size']):
            raise ValueError('Existing asset size mismatch')
        with path.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        result = dict(drive_id=f['id'], path=str(path), bytes=path.stat().st_size,
                      sha256=sha, wall_seconds=time.monotonic()-started,
                      provider_modified_time=f.get('modified_time'))
        receipt.write_text(json.dumps(result, indent=2) + '\n')
        return result

    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(one, jobs):
            print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
