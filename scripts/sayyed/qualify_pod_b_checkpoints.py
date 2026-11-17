"""CPU-only qualification of supplied adapter payloads; no capability predictions."""
import datetime
import hashlib
import json
from pathlib import Path
import time

import torch
from torch.distributed.checkpoint import FileSystemReader
from torch.distributed.checkpoint.metadata import TensorStorageMetadata
import yaml

from scripts.sayyed.check_benign_checkpoint_pair import load

root = Path('/workspace/meeting-artifacts/relearning-benign-v1')
inventory = json.loads((root / 'DRIVE_INVENTORY.json').read_text())
started, cpu = time.monotonic(), time.process_time()
torch.set_num_threads(4)
nodes = []
fingerprints = {}
for node in sorted(inventory['checkpoints'], key=lambda n: (n['series'], n['step'])):
    folder = root / 'checkpoints' / node['series'] / f"iter_{node['step']:07d}"
    files = []
    for item in node['files']:
        if item['file_or_folder'] == 'folder':
            continue
        p = folder / item['title']
        receipt = json.loads(p.with_name(p.name + '.download.json').read_text())
        with p.open('rb') as stream:
            sha = hashlib.file_digest(stream, 'sha256').hexdigest()
        if (receipt['drive_id'] != item['id'] or p.stat().st_size != int(item['size'])
                or receipt['sha256'] != sha):
            raise ValueError('Acquired file identity mismatch')
        files.append(dict(name=p.name, drive_id=item['id'], bytes=p.stat().st_size, sha256=sha))
    cfg = yaml.safe_load((folder / 'run_config.yaml').read_text())
    if cfg['peft']['dim'] != 16 or cfg['peft']['alpha'] != 32:
        raise ValueError('Unexpected supplied adapter protocol')
    metadata = FileSystemReader(folder).read_metadata()
    storage_files = sorted({v.relative_path for v in metadata.storage_data.values()})
    if storage_files != ['__0_0.distcp']:
        raise ValueError('Missing or unexpected sharded storage payload')
    state = load(folder)
    if len(state) != 200 or any('.adapter.' not in k for k in state):
        raise ValueError('Unexpected adapter-only payload tensor set')
    expected = cfg['peft']['params_to_save']
    if set(state) != set(expected):
        raise ValueError('Config params_to_save differs from actual model payload')
    adapters = sorted({k.split('.adapter.')[0] for k in state})
    tensor_report = {}
    total_sha = hashlib.sha256()
    for key, value in sorted(state.items()):
        raw = value.contiguous().view(torch.uint8).numpy().tobytes()
        sha = hashlib.sha256(raw).hexdigest()
        tensor_report[key] = dict(shape=list(value.shape), dtype=str(value.dtype), sha256=sha,
                                  l2_norm=float(value.float().norm()), max_abs=float(value.float().abs().max()))
        total_sha.update(key.encode() + b'\0' + str(value.dtype).encode() + b'\0')
        total_sha.update(json.dumps(list(value.shape)).encode() + b'\0' + raw)
    for name in adapters:
        a, b = state[name + '.adapter.linear_in.weight'], state[name + '.adapter.linear_out.weight']
        if a.ndim != 2 or b.ndim != 2 or a.shape[0] != 16 or b.shape[1] != 16:
            raise ValueError('Adapter rank geometry mismatch')
    fingerprint = total_sha.hexdigest()
    fingerprints.setdefault(fingerprint, []).append([node['series'], node['step']])
    train = torch.load(folder / 'train_state.pt', map_location='cpu', weights_only=True)
    if int(train['step']) != node['step']:
        raise ValueError('Folder step and train-state step disagree')
    tokens = json.loads((folder / 'tokenizer/tokenizer.json').read_text())
    item = dict(series=node['series'], step=node['step'], folder_id=node['folder_id'],
                kind='adapter_only', model_tensors=200, adapted_modules=len(adapters),
                all_finite=True, payload_files=storage_files, files=files,
                weights_sha256=next(f['sha256'] for f in files if f['name'].endswith('.distcp')),
                tensor_content_fingerprint=fingerprint, tensors=tensor_report,
                consumed_train_samples=int(train['consumed_train_samples']),
                declared_parent_path=cfg['checkpoint']['pretrained_checkpoint'],
                resume_load_path=cfg['checkpoint']['load'],
                declared_loader=cfg['peft']['_target_'],
                peft={k:v for k,v in cfg['peft'].items() if k not in ('params_to_save',)},
                tokenizer_sha256=hashlib.sha256((folder/'tokenizer/tokenizer.json').read_bytes()).hexdigest(),
                architecture={k:cfg['model'][k] for k in ('num_layers','hidden_size','num_attention_heads')},
                descriptive_evaluation_status='BLOCKED_EXACT_ADAPTER_LOADER_QUALIFICATION',
                trajectory_initial_status='NOT_DELIVERED_IN_LISTED_TRAJECTORY_FOLDERS',
                actual_parent_lineage='DECLARED_PATH_ONLY; exact training initialization not independently proven')
    nodes.append(item)
    (folder / 'CPU_QUALIFICATION.json').write_text(json.dumps(item, indent=2) + '\n')
    print(node['series'], node['step'], 'PASS integrity; adapter tensors', len(state), flush=True)
report = dict(schema='pod-b-checkpoint-registry-v1', created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              inventory_sha256=hashlib.sha256((root/'DRIVE_INVENTORY.json').read_bytes()).hexdigest(),
              checkpoints=nodes, delivered_count=len(nodes), unique_tensor_payloads=len(fingerprints),
              duplicate_groups=[v for v in fingerprints.values() if len(v)>1],
              wall_seconds=time.monotonic()-started, cpu_process_seconds=time.process_time()-cpu,
              gpu_seconds=0, scope='CPU integrity and metadata qualification; no inference, fitting, or causal lineage proof')
(root / 'CHECKPOINT_REGISTRY.json').write_text(json.dumps(report, indent=2) + '\n')
print('Registry complete', len(nodes), 'unique adapter contents',len(fingerprints),flush=True)
