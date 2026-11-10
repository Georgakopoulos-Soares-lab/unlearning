"""Prepare a scoped scientific recovery tree, excluding weights and credentials."""
import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    args = parser.parse_args()
    root, dest = args.run.resolve(), args.destination.resolve()
    if dest.exists() or dest.is_relative_to(root):
        raise ValueError('Fresh destination outside run required')
    if json.loads((root/'STAGE2_COMPLETE.json').read_text())['status'] != 'COMPLETE_AVAILABLE_SCOPE':
        raise ValueError('Scientific gate required')
    dest.mkdir(parents=True)
    folders = ['features', 'probes', 'manifests', 'inputs', 'producer_audit',
               'consumer_views', 'reports', 'reviewer_source', 'smokes', 'smokes-fixed8']
    files = [p for p in root.iterdir() if p.is_file() and p.suffix in {'.json', '.yaml', '.txt', '.md', '.log', '.csv', '.py', '.sha256'}
             and p.name not in {'CHECKSUMS.sha256', 'backup_worker_state.json', 'READY_FOR_BACKUP.json'}]
    for folder in folders:
        source = root/folder
        if source.exists():
            for path in source.rglob('*'):
                if path.is_symlink():
                    raise ValueError('Symlink in scientific payload')
            shutil.copytree(source, dest/folder)
    for source in files:
        if source.is_symlink():
            raise ValueError('Symlink in scientific payload')
        shutil.copy2(source, dest/source.name)
    # Small checkpoint descriptors and receipts suffice to identify/reacquire weights.
    for source in (root/'checkpoint-assets').rglob('*'):
        if source.is_file() and source.suffix != '.distcp':
            target = dest/source.relative_to(root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    old = root/'recovery-01/maxent-benign-v16/delivery_snapshot'
    for name in ['base_download_receipt.json', 'maxent_download_receipt.json']:
        shutil.copy2(old/name, dest/name)
    source_root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
    shutil.copytree(source_root/'scripts/sayyed', dest/'source/scripts/sayyed',
                    ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(source_root/'docs/experiments/ashay/multiretain-layers-v1', dest/'source/docs')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    (dest/'RECOVERY_SCOPE.json').write_text(json.dumps(dict(
        original_root=str(root), delivery_source_commit=head,
        scope='CPU saved-output recovery: all features, fitted probes, predictions, resamples, manifests, audits and reporting',
        excluded=['model weights', 'installed runtime', 'raw dataset archive', 'credentials', 'historical recovery archive'],
        gpu_reproduction='Requires reacquiring exact checkpoint shards and reconstructing pinned runtime; not offline GPU recovery',
        source_execution='See feature identities and FIT_COMPLETE receipts; delivery commit may postdate execution',
    ), indent=2))
    print(dest)


if __name__ == '__main__':
    main()
