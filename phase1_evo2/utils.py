"""Shared utilities for Evo-2 Phase 1 localization."""

# from attr.validators import max_len
from __future__ import annotations

import csv
import gzip
import os
import random
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
import torch
from evo2 import Evo2


@dataclass
class LoadedEvo2:
    """Evo-2 wrapper and its underlying model components."""

    wrapper: Evo2
    model: torch.nn.Module
    tokenizer: object
    model_name: str


@dataclass
class ManifestRecord:
    """One sequence example from a target manifest."""

    record_id: str
    label: int
    split: str
    sequence: str
    source: str
    length: int


def load_huggingface_checkpoint(
    model_name: str = "evo2_7b_base",
    local_path: str | None = None,
    use_kernels: bool = False,
) -> LoadedEvo2:
    """Load an Evo-2 checkpoint, downloading it from Hugging Face if needed.

    Vortex handles model device placement. Do not manually call ``model.to()``
    when the checkpoint may be distributed across multiple GPUs.
    """
    wrapper = Evo2(
        model_name=model_name,
        local_path=local_path,
        use_kernels=use_kernels,
    )

    return LoadedEvo2(
        wrapper=wrapper,
        model=wrapper.model,
        tokenizer=wrapper.tokenizer,
        model_name=model_name,
    )


def tokenize_sequences(
    sequences: List[str],
    tokenizer: object,
    max_length: int,
) -> List[List[int]]:
    """Tokenize DNA sequences after truncating them to ``max_length``."""
    if max_length <= 0:
        raise ValueError("max_length must be positive")

    return [
        tokenizer.tokenize(sequence[:max_length])
        for sequence in sequences
    ]


def pad_batch(
    token_ids: List[List[int]],
    pad_id: int,
) -> Tuple[torch.Tensor, torch.Tensor]:
    """Right-pad tokenized sequences and return token IDs plus a logical mask.

    The mask is useful for pooling. It should not be passed to Evo-2 unless
    the selected Vortex forward implementation explicitly supports it.
    """
    if not token_ids:
        raise ValueError("Cannot pad an empty batch")

    if any(len(tokens) == 0 for tokens in token_ids):
        raise ValueError("Tokenized sequences must not be empty")

    max_length = max(len(tokens) for tokens in token_ids)

    batch = np.full(
        (len(token_ids), max_length),
        fill_value=pad_id,
        dtype=np.int64,
    )
    mask = np.zeros(
        (len(token_ids), max_length),
        dtype=np.int64,
    )

    for row_index, tokens in enumerate(token_ids):
        sequence_length = len(tokens)
        batch[row_index, :sequence_length] = tokens
        mask[row_index, :sequence_length] = 1

    return torch.from_numpy(batch), torch.from_numpy(mask)


def _extract_logits(output: object) -> torch.Tensor:
    """Extract a rank-three logits tensor from an Evo-2/Vortex output."""
    if isinstance(output, torch.Tensor):
        logits = output
    elif isinstance(output, dict):
        if "logits" not in output:
            raise TypeError(
                f"Output dictionary has no 'logits' entry: {list(output)}"
            )
        logits = _extract_logits(output["logits"])
    elif isinstance(output, (tuple, list)) and output:
        logits = _extract_logits(output[0])
    else:
        raise TypeError(
            f"Could not extract logits from output of type {type(output)!r}"
        )

    if logits.ndim != 3:
        raise RuntimeError(
            "Expected logits with shape [batch, sequence, vocabulary], "
            f"received {tuple(logits.shape)}"
        )

    return logits


def forward_inference(
    loaded: LoadedEvo2,
    input_ids: torch.Tensor,
    padding_mask: torch.Tensor | None = None,
) -> torch.Tensor:
    """Run padding-aware Evo-2 inference and return logits."""
    with torch.no_grad():
        output = loaded.model(
            input_ids,
            padding_mask=padding_mask,
        )

    return _extract_logits(output)


def forward_differentiable(
    loaded: LoadedEvo2,
    input_ids: torch.Tensor,
    padding_mask: torch.Tensor | None = None,
) -> torch.Tensor:
    """Run a padding-aware Evo-2 forward pass with autograd enabled."""
    output = loaded.model(
        input_ids,
        padding_mask=padding_mask,
    )

    return _extract_logits(output)


def forward_logits(
    loaded: LoadedEvo2,
    input_ids: torch.Tensor,
    padding_mask: torch.Tensor | None = None,
) -> torch.Tensor:
    """Compatibility alias for inference."""
    return forward_inference(
        loaded,
        input_ids,
        padding_mask=padding_mask,
    )


def get_blocks(model: torch.nn.Module) -> List[torch.nn.Module]:
    """Return Evo-2's ordered model blocks."""
    if not hasattr(model, "blocks"):
        raise TypeError("Evo-2 model does not expose a 'blocks' attribute")

    blocks = list(model.blocks)
    if not blocks:
        raise RuntimeError("Evo-2 model contains no blocks")

    return blocks


def get_block(
    model: torch.nn.Module,
    layer_idx: int,
) -> torch.nn.Module:
    """Return one Evo-2 block after validating its index."""
    blocks = get_blocks(model)

    if not 0 <= layer_idx < len(blocks):
        raise IndexError(
            f"Layer {layer_idx} is outside [0, {len(blocks) - 1}]"
        )

    return blocks[layer_idx]

def module_device(module: torch.nn.Module) -> torch.device:
    """Return the device of a module's first parameter or buffer."""
    for parameter in module.parameters():
        if parameter.device.type != "meta":
            return parameter.device

    for buffer in module.buffers():
        if buffer.device.type != "meta":
            return buffer.device

    raise RuntimeError(
        f"Could not determine device for {type(module).__name__}"
    )

def extract_hidden(output: object) -> torch.Tensor:
    """Extract the hidden-state tensor returned by a forward hook."""
    if isinstance(output, torch.Tensor):
        hidden = output
    elif isinstance(output, (tuple, list)) and output:
        hidden = output[0]
    elif isinstance(output, dict) and "hidden_states" in output:
        hidden = output["hidden_states"]
    else:
        raise TypeError(
            "Could not extract hidden states from hook output of type "
            f"{type(output)!r}"
        )

    if not isinstance(hidden, torch.Tensor):
        raise TypeError(
            f"Expected hidden states to be a tensor, got {type(hidden)!r}"
        )

    if hidden.ndim != 3:
        raise RuntimeError(
            "Expected hidden states with shape [batch, sequence, hidden], "
            f"received {tuple(hidden.shape)}"
        )

    return hidden


def normalize_layer_output(
    model: torch.nn.Module,
    hidden: torch.Tensor,
    layer_idx: int,
    representation: str,
) -> torch.Tensor:
    """Convert a block output into the requested representation.

    ``raw`` returns the residual stream after the selected block.

    ``next_norm`` applies the normalization that prepares that residual
    stream for the following block. For the last block, it applies the
    model's final normalization.
    """
    if representation == "raw":
        return hidden

    if representation != "next_norm":
        raise ValueError(
            f"Unsupported representation {representation!r}; "
            "expected 'raw' or 'next_norm'"
        )

    blocks = get_blocks(model)

    if not 0 <= layer_idx < len(blocks):
        raise IndexError(
            f"Layer {layer_idx} is outside "
            f"[0, {len(blocks) - 1}]"
        )

    if layer_idx + 1 < len(blocks):
        normalizer = getattr(
            blocks[layer_idx + 1],
            "pre_norm",
            None,
        )

        if normalizer is None:
            raise AttributeError(
                f"Evo-2 block {layer_idx + 1} does not expose pre_norm"
            )
    else:
        normalizer = getattr(model, "norm", None)

        if normalizer is None:
            raise AttributeError(
                "Evo-2 model does not expose a final norm"
            )

    # Evo-2 may distribute adjacent blocks across GPUs.
    normalizer_device = module_device(normalizer)
    hidden = hidden.to(normalizer_device)

    return normalizer(hidden)


def read_manifest(path: str) -> List[ManifestRecord]:
    """Read a target-manifest CSV."""
    records: List[ManifestRecord] = []

    with open(path, newline="") as file:
        reader = csv.DictReader(file)

        required_columns = {"id", "label", "split", "sequence"}
        available_columns = set(reader.fieldnames or [])
        missing_columns = required_columns - available_columns
        if missing_columns:
            raise ValueError(
                f"Manifest {path!r} is missing columns: "
                f"{sorted(missing_columns)}"
            )

        for row_number, row in enumerate(reader, start=2):
            sequence = row["sequence"]
            label = int(row["label"])
            split = row["split"]

            if label not in {0, 1}:
                raise ValueError(
                    f"Row {row_number} has invalid label {label}; "
                    "expected 0 or 1"
                )

            if split not in {"train", "val", "test"}:
                raise ValueError(
                    f"Row {row_number} has invalid split {split!r}"
                )

            records.append(
                ManifestRecord(
                    record_id=row["id"],
                    label=label,
                    split=split,
                    sequence=sequence,
                    source=row.get("source", ""),
                    length=int(row.get("length") or len(sequence)),
                )
            )

    return records


def write_manifest(
    path: str,
    records: List[ManifestRecord],
) -> None:
    """Write records using the standard target-manifest schema."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    fieldnames = [
        "id",
        "label",
        "split",
        "sequence",
        "source",
        "length",
    ]

    with open(path, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for record in records:
            writer.writerow(
                {
                    "id": record.record_id,
                    "label": record.label,
                    "split": record.split,
                    "sequence": record.sequence,
                    "source": record.source,
                    "length": record.length,
                }
            )


def iter_fasta_gz(
    path: str,
) -> Iterable[Tuple[str, str]]:
    """Yield ``(header, sequence)`` records from a gzip-compressed FASTA."""
    header: str | None = None
    sequence_parts: List[str] = []

    with gzip.open(path, "rt") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue

            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(sequence_parts)

                header = line[1:]
                sequence_parts = []
            else:
                sequence_parts.append(line)

    if header is not None:
        yield header, "".join(sequence_parts)


def clean_sequence(sequence: str) -> str:
    """Uppercase DNA and remove characters other than A, C, G, T, and N."""
    return re.sub(r"[^ACGTN]", "", sequence.upper())


def sample_window(
    sequence: str,
    max_length: int,
    rng: random.Random,
) -> str:
    """Return the sequence or one reproducibly sampled contiguous window."""
    if max_length <= 0:
        raise ValueError("max_length must be positive")

    if len(sequence) <= max_length:
        return sequence

    start = rng.randint(0, len(sequence) - max_length)
    return sequence[start : start + max_length]


class FeatureWriter:
    """Buffer and save layer-wise feature arrays in numbered chunks."""

    def __init__(
        self,
        out_dir: str,
        num_layers: int,
        chunk_size: int = 256,
    ) -> None:
        if num_layers <= 0:
            raise ValueError("num_layers must be positive")

        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        self.out_dir = out_dir
        self.num_layers = num_layers
        self.chunk_size = chunk_size

        self.buffers: Dict[int, List[np.ndarray]] = {
            layer_idx: []
            for layer_idx in range(num_layers)
        }
        self.chunk_index: Dict[int, int] = {
            layer_idx: 0
            for layer_idx in range(num_layers)
        }

        os.makedirs(out_dir, exist_ok=True)
        for layer_idx in range(num_layers):
            os.makedirs(
                os.path.join(out_dir, f"layer_{layer_idx}"),
                exist_ok=True,
            )

    def _validate_layer(self, layer_idx: int) -> None:
        if not 0 <= layer_idx < self.num_layers:
            raise IndexError(
                f"Layer {layer_idx} is outside "
                f"[0, {self.num_layers - 1}]"
            )

    def add(
        self,
        layer_idx: int,
        features: torch.Tensor,
    ) -> None:
        """Add a feature batch and flush when the chunk threshold is reached."""
        self._validate_layer(layer_idx)

        if features.ndim != 2:
            raise ValueError(
                "Expected features with shape [batch, hidden], "
                f"received {tuple(features.shape)}"
            )

        array = features.detach().float().cpu().numpy()
        self.buffers[layer_idx].append(array)

        buffered_rows = sum(
            chunk.shape[0]
            for chunk in self.buffers[layer_idx]
        )
        if buffered_rows >= self.chunk_size:
            self.flush(layer_idx)

    def flush(self, layer_idx: int) -> None:
        """Atomically write one layer's currently buffered features."""
        self._validate_layer(layer_idx)

        if not self.buffers[layer_idx]:
            return

        chunk = np.concatenate(self.buffers[layer_idx], axis=0)
        chunk_path = os.path.join(
            self.out_dir,
            f"layer_{layer_idx}",
            f"chunk_{self.chunk_index[layer_idx]:04d}.npy",
        )
        temporary_path = chunk_path + ".tmp"

        try:
            with open(temporary_path, "wb") as file:
                np.save(file, chunk)
            os.replace(temporary_path, chunk_path)
        finally:
            if os.path.exists(temporary_path):
                os.remove(temporary_path)

        self.buffers[layer_idx] = []
        self.chunk_index[layer_idx] += 1

    def flush_all(self) -> None:
        """Write all remaining layer buffers."""
        for layer_idx in range(self.num_layers):
            self.flush(layer_idx)



if __name__ == "__main__":
    loaded = load_huggingface_checkpoint()
    tokenizer = loaded.tokenizer

    sequence = ["ATCGCGGGAGC", "ATCGAGAGC"]
    max_length = len(sequence[0])
    token_ids = tokenize_sequences(sequence, tokenizer, max_length=max_length) #Returns list of lists

    print("Sequence:", sequence)
    print("Token IDs:", token_ids)
    print("Number of tokens:", len(token_ids))

    # assert len(token_ids) > 0
    # assert all(len(tokens)<=max_length for tokens in token_ids), "tokenize_sequence not working"
    # assert all(
    #     isinstance(token_id, (int, np.integer))
    #     for tokens in token_ids
    #     for token_id in tokens
    # )

    # print("Tokenizer is working good\n\n")

    # print("Checking for Padding")
    token_ids, mask = pad_batch(token_ids, 0)
    # print(token_ids.size(), mask.size()) 

    # output = forward_inference(loaded, token_ids.to("cuda"), mask.to("cuda"))
    print(get_block(loaded.model, 23))




