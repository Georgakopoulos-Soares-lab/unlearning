"""Shared utilities for Evo-2 Phase 2 unlearning."""
from __future__ import annotations

import json
import os
import random
import csv
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np
import torch


DEFAULT_LOCALIZED_LAYERS = [5, 6, 7, 8, 9]
DEFAULT_PRIMARY_TARGET_LAYER = 6
DEFAULT_LOCALIZED_LAYERS_PATH = "data/evo2/family_targets/coronaviridae/localized_layers.json"
PROBE_LAYERS = list(range(0, 11))
RANDOM_LAYER_POOL = list(range(11, 31))


@dataclass
class ManifestRecord:
    record_id: str
    label: int
    split: str
    sequence: str
    source: str
    length: int


def read_manifest(path: str) -> List[ManifestRecord]:
    records: List[ManifestRecord] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(
                ManifestRecord(
                    record_id=row["id"],
                    label=int(row["label"]),
                    split=row["split"],
                    sequence=row["sequence"],
                    source=row.get("source", ""),
                    length=int(row.get("length", len(row["sequence"]))),
                )
            )
    return records


def pad_batch(token_ids: List[List[int]], pad_id: int) -> Tuple[torch.Tensor, torch.Tensor]:
    if not token_ids:
        raise ValueError("Cannot pad an empty batch")
    if any(len(tokens) == 0 for tokens in token_ids):
        raise ValueError("Tokenized sequences must not be empty")

    max_length = max(len(tokens) for tokens in token_ids)
    batch = np.full((len(token_ids), max_length), fill_value=pad_id, dtype=np.int64)
    mask = np.zeros((len(token_ids), max_length), dtype=np.int64)
    for row_index, tokens in enumerate(token_ids):
        sequence_length = len(tokens)
        batch[row_index, :sequence_length] = tokens
        mask[row_index, :sequence_length] = 1
    return torch.from_numpy(batch), torch.from_numpy(mask)


def tokenize_sequences(sequences: List[str], tokenizer: object, max_length: int) -> List[List[int]]:
    if max_length <= 0:
        raise ValueError("max_length must be positive")
    return [tokenizer.tokenize(sequence[:max_length]) for sequence in sequences]


def _extract_logits(output: object) -> torch.Tensor:
    if isinstance(output, torch.Tensor):
        logits = output
    elif isinstance(output, dict) and "logits" in output:
        logits = _extract_logits(output["logits"])
    elif isinstance(output, (tuple, list)) and output:
        logits = _extract_logits(output[0])
    else:
        raise TypeError(f"Could not extract logits from output type {type(output)!r}")
    if logits.ndim != 3:
        raise RuntimeError(f"Expected rank-3 logits, received {tuple(logits.shape)}")
    return logits


def get_blocks(model: torch.nn.Module) -> List[torch.nn.Module]:
    if not hasattr(model, "blocks"):
        raise TypeError("Evo-2 model does not expose a 'blocks' attribute")
    blocks = list(model.blocks)
    if not blocks:
        raise RuntimeError("Evo-2 model contains no blocks")
    return blocks


def load_evo2_checkpoint(
    model_name: str = "evo2_7b_base",
    local_path: str | None = None,
    use_kernels: bool = False,
) -> object:
    from phase1_evo2.utils import load_huggingface_checkpoint

    return load_huggingface_checkpoint(
        model_name=model_name,
        local_path=local_path,
        use_kernels=use_kernels,
    )


def load_local_checkpoint(
    model_dir: str = "",
    config_path: str = "",
    device: str | None = None,
    model_name: str = "evo2_7b_base",
    local_path: str | None = None,
    use_kernels: bool = False,
):
    """Compatibility wrapper for copied Phase 2 scripts.

    Evo-2 loading is controlled by ``model_name`` / ``local_path``. The legacy
    ``model_dir`` and ``config_path`` parameters are accepted so copied Phase 2
    entrypoints can keep their CLI shape while switching loaders.
    """
    loaded = load_evo2_checkpoint(
        model_name=model_name,
        local_path=local_path or model_dir or None,
        use_kernels=use_kernels,
    )
    if device is not None:
        try:
            loaded.model.to(device)
        except RuntimeError:
            # Vortex may shard the model; in that case device placement is
            # handled by the loader and per-batch input-device resolution.
            pass
    return loaded


def model_from_loaded(loaded_or_model):
    return loaded_or_model.model if hasattr(loaded_or_model, "model") else loaded_or_model


def tokenizer_from_loaded(loaded: object):
    return loaded.tokenizer


def forward_logits(loaded_or_model, input_ids: torch.Tensor, padding_mask: torch.Tensor | None = None) -> torch.Tensor:
    model = model_from_loaded(loaded_or_model)
    output = model(input_ids, padding_mask=padding_mask)
    return _extract_logits(output)


def load_localized_config(path: str = DEFAULT_LOCALIZED_LAYERS_PATH) -> dict:
    if not path or not os.path.exists(path):
        return {
            "layers": DEFAULT_LOCALIZED_LAYERS,
            "primary_target_layer": DEFAULT_PRIMARY_TARGET_LAYER,
            "source": "default_fallback",
        }
    with open(path) as f:
        return json.load(f)


def get_localized_layers(path: str = DEFAULT_LOCALIZED_LAYERS_PATH) -> List[int]:
    data = load_localized_config(path)
    return sorted(set(int(layer) for layer in data.get("layers", DEFAULT_LOCALIZED_LAYERS)))


def get_primary_target_layer(path: str = DEFAULT_LOCALIZED_LAYERS_PATH) -> int:
    data = load_localized_config(path)
    return int(data.get("primary_target_layer", DEFAULT_PRIMARY_TARGET_LAYER))


def select_random_layers(seed: int, n: int) -> List[int]:
    rng = random.Random(seed)
    return sorted(rng.sample(RANDOM_LAYER_POOL, n))


def split_records(records: List[ManifestRecord]) -> Tuple[List[ManifestRecord], List[ManifestRecord]]:
    forget = [r for r in records if r.label == 1]
    retain = [r for r in records if r.label == 0]
    return forget, retain


def tokenize_batch(seqs: List[str], tokenizer: object, max_length: int, device: str) -> Tuple[torch.Tensor, torch.Tensor]:
    token_ids = tokenize_sequences(seqs, tokenizer, max_length=max_length)
    input_ids, mask = pad_batch(token_ids, tokenizer.pad_id)
    return input_ids.to(device), mask.to(device)


def language_model_loss(logits: torch.Tensor, input_ids: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    shift_logits = logits[:, :-1, :].contiguous().float()
    shift_labels = input_ids[:, 1:].contiguous()
    shift_mask = mask[:, 1:].contiguous().float()

    flat_logits = shift_logits.view(-1, shift_logits.shape[-1])
    flat_labels = shift_labels.view(-1)
    token_losses = torch.nn.functional.cross_entropy(
        flat_logits,
        flat_labels,
        reduction="none",
    ).view_as(shift_labels)
    denom = shift_mask.sum(dim=1).clamp(min=1)
    return ((token_losses * shift_mask).sum(dim=1) / denom).mean()


def iterate_batches(records: List[ManifestRecord], batch_size: int, shuffle: bool, rng: random.Random) -> Iterable[List[ManifestRecord]]:
    if shuffle:
        indices = list(range(len(records)))
        rng.shuffle(indices)
        records = [records[i] for i in indices]
    for start in range(0, len(records), batch_size):
        batch = records[start : start + batch_size]
        if batch:
            yield batch


def _blocks(model_or_loaded) -> list[torch.nn.Module]:
    return get_blocks(model_from_loaded(model_or_loaded))


def set_block_grad(model_or_loaded, block_indices: List[int], requires_grad: bool) -> None:
    blocks = _blocks(model_or_loaded)
    for layer_idx in block_indices:
        for parameter in blocks[layer_idx].parameters():
            parameter.requires_grad_(requires_grad)


def freeze_all(model_or_loaded) -> None:
    for parameter in model_from_loaded(model_or_loaded).parameters():
        parameter.requires_grad_(False)


def get_trainable_params(model_or_loaded) -> List[torch.nn.Parameter]:
    return [parameter for parameter in model_from_loaded(model_or_loaded).parameters() if parameter.requires_grad]


def count_trainable(model_or_loaded) -> int:
    return sum(parameter.numel() for parameter in model_from_loaded(model_or_loaded).parameters() if parameter.requires_grad)


def write_split_meta(path: str, condition: str, layers: List[int], extra: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(f"condition,{condition}\n")
        f.write(f"layers,{'|'.join(str(x) for x in layers)}\n")
        for key, value in extra.items():
            f.write(f"{key},{value}\n")
