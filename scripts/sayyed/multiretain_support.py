"""CPU-testable contracts for the separately versioned all-layer workflow."""
import hashlib
import json
import math
import os
from pathlib import Path
import time


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(f'.{path.name}.{os.getpid()}.tmp')
    with temporary.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def remaining_seconds(limit, used):
    """An explicit null means uncapped; absent authorization is rejected upstream."""
    if not isinstance(used, (int, float)) or not math.isfinite(used) or used < 0:
        raise ValueError('Invalid measured usage')
    if limit is None:
        return math.inf
    if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or limit < 0:
        raise ValueError('Invalid limit')
    return max(0., limit - used)


class SessionBudget:
    """Caller must hold the shared historical GPU lock for the entire stage."""
    def __init__(self, ledger, config):
        self.path = Path(ledger)
        self.config = Path(config)
        self.config_hash = hashlib.sha256(self.config.read_bytes()).hexdigest()
        self.inputs = json.loads(self.config.read_text())
        for key in ('AUTHORIZED_GPU_STAGE_SECONDS', 'AUTHORIZED_RENTAL_WALL_MINUTES'):
            if key not in self.inputs:
                raise ValueError('Missing explicit authorization: ' + key)
            remaining_seconds(self.inputs[key], 0)

    def read(self):
        state = json.loads(self.path.read_text())
        if (state['effective_config_sha256'] != self.config_hash
                or hashlib.sha256(self.config.read_bytes()).hexdigest() != self.config_hash):
            raise ValueError('Session configuration changed; use a new ledger identity')
        if state.get('active_since'):
            raise ValueError('Unreconciled active session stage')
        rental = self.inputs['AUTHORIZED_RENTAL_WALL_MINUTES']
        return min(remaining_seconds(self.inputs['AUTHORIZED_GPU_STAGE_SECONDS'], state['used_seconds']),
                   remaining_seconds(None if rental is None else rental * 60,
                                     max(0., time.time() - state['session_started_epoch'])))

    def begin(self):
        if self.read() < 60:
            raise ValueError('Insufficient authorized time')
        state = json.loads(self.path.read_text())
        self.started = time.monotonic()
        state['active_since'] = time.time()
        state['pid'] = os.getpid()
        atomic_json(self.path, state)

    def end(self):
        state = json.loads(self.path.read_text())
        elapsed = time.monotonic() - self.started
        state['used_seconds'] += elapsed
        state['active_since'] = None
        state.setdefault('stages', []).append(dict(pid=os.getpid(), gpu_stage_wall_seconds=elapsed))
        atomic_json(self.path, state)


def layer_specs(model):
    """Enumerate actual decoder blocks; preserve the historical layer16 array key."""
    specs = [(f'decoder_layer_{i}', f'decoder.layers.{i}', module)
             for i, module in enumerate(model.decoder.layers)]
    if len(specs) <= 16:
        raise ValueError('Historical anchor decoder.layers[16] absent')
    return specs + [('final_norm', 'decoder.final_norm', model.decoder.final_norm)]


def pooled_activation(output, lengths, width):
    import torch
    hidden = output[0] if isinstance(output, tuple) else output
    if hidden.ndim != 3 or hidden.shape[1:] != (len(lengths), width):
        raise ValueError('Unexpected sequence,batch,width hook shape')
    if (lengths < 1).any() or (lengths > hidden.shape[0]).any():
        raise ValueError('Invalid nucleotide lengths')
    mask = torch.arange(hidden.shape[0], device=hidden.device)[:, None] < lengths[None, :]
    if not torch.isfinite(hidden).all():
        raise ValueError('Nonfinite activation')
    return (hidden.float() * mask[:, :, None]).sum(0) / lengths[:, None]
