"""Extract layer-wise mean-pooled Evo-2 features."""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict

import numpy as np
import torch
from tqdm import tqdm


if __package__ is None and __name__ == "__main__":
    sys.path.append(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )


from phase1_evo2.utils import (
    FeatureWriter,
    extract_hidden,
    forward_inference,
    get_blocks,
    load_huggingface_checkpoint,
    normalize_layer_output,
    pad_batch,
    read_manifest,
    tokenize_sequences,
)


def parse_layers(
    specification: str,
    num_layers: int,
) -> list[int]:
    """Parse layer specifications such as 'all' or '0-10,14'."""
    if specification == "all":
        return list(range(num_layers))

    layers: list[int] = []

    for part in specification.split(","):
        part = part.strip()
        if not part:
            continue

        range_separator = part.find("-", 1)
        if range_separator != -1:
            start = int(part[:range_separator])
            end = int(part[range_separator + 1 :])

            if start > end:
                raise ValueError(
                    f"Invalid descending layer range {part!r}"
                )

            layers.extend(range(start, end + 1))
        else:
            layers.append(int(part))

    layers = sorted(set(layers))

    if not layers:
        raise ValueError("No layers were selected")

    for layer_idx in layers:
        if not 0 <= layer_idx < num_layers:
            raise ValueError(
                f"Layer {layer_idx} is outside "
                f"[0, {num_layers - 1}]"
            )

    return layers


def resolve_input_device(
    model: torch.nn.Module,
    requested_device: str | None,
) -> torch.device:
    """Resolve the device on which input IDs should be allocated."""
    if requested_device:
        device = torch.device(requested_device)

        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                f"Requested {device}, but CUDA is unavailable"
            )

        return device

    for parameter in model.parameters():
        if parameter.device.type != "meta":
            return parameter.device

    raise RuntimeError(
        "Could not infer input device from model parameters. "
        "Pass --input-device explicitly."
    )



def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Extract layer-wise mean-pooled features from Evo-2."
        )
    )
    parser.add_argument(
        "--manifest",
        default=(
            "data/evo2/family_targets/"
            "coronaviridae/manifest.csv"
        ),
    )
    parser.add_argument(
        "--model-name",
        default="evo2_7b_base",
    )
    parser.add_argument(
        "--local-path",
        default=None,
    )
    parser.add_argument(
        "--use-kernels",
        action="store_true",
    )
    parser.add_argument(
        "--out-dir",
        default=(
            "data/evo2/family_targets/"
            "coronaviridae/features"
        ),
    )
    parser.add_argument(
        "--input-device",
        default=None,
        help=(
            "Input device, such as cuda:0. If omitted, infer it "
            "from the model."
        ),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=512,
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=256,
    )
    parser.add_argument(
        "--representation",
        choices=["raw", "next_norm"],
        default="raw",
        help=(
            "Use raw until Evo-2 next-layer normalization has "
            "been inspected and implemented."
        ),
    )
    parser.add_argument(
        "--layers",
        default="all",
        help="Examples: all, 0-10, or 0-10,14",
    )
    args = parser.parse_args()

    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive")

    if args.max_length <= 0:
        raise ValueError("--max-length must be positive")

    records = read_manifest(args.manifest)
    if not records:
        raise RuntimeError(
            f"Manifest contains no records: {args.manifest}"
        )

    sequences = [record.sequence for record in records]
    labels = np.array(
        [record.label for record in records],
        dtype=np.int64,
    )
    splits = np.array(
        [record.split for record in records]
    )
    record_ids = np.array(
        [record.record_id for record in records]
    )

    os.makedirs(args.out_dir, exist_ok=True)

    np.save(
        os.path.join(args.out_dir, "labels.npy"),
        labels,
    )
    np.save(
        os.path.join(args.out_dir, "splits.npy"),
        splits,
    )
    np.save(
        os.path.join(args.out_dir, "ids.npy"),
        record_ids,
    )

    loaded = load_huggingface_checkpoint(
        model_name=args.model_name,
        local_path=args.local_path,
        use_kernels=args.use_kernels,
    )

    model = loaded.model
    model.eval()

    blocks = get_blocks(model)
    num_layers = len(blocks)
    layers = parse_layers(args.layers, num_layers)
    layer_set = set(layers)

    input_device = resolve_input_device(
        model,
        args.input_device,
    )

    metadata = {
        "model_family": "evo2",
        "model_name": args.model_name,
        "local_path": args.local_path,
        "use_kernels": args.use_kernels,
        "representation": args.representation,
        "max_length": args.max_length,
        "batch_size": args.batch_size,
        "layers": layers,
        "num_model_layers": num_layers,
        "manifest": args.manifest,
        "input_device": str(input_device),
    }

    with open(
        os.path.join(args.out_dir, "metadata.json"),
        "w",
    ) as file:
        json.dump(metadata, file, indent=2)

    writer = FeatureWriter(
        args.out_dir,
        num_layers=num_layers,
        chunk_size=args.chunk_size,
    )

    block_to_indices: dict[
        torch.nn.Module,
        list[int],
    ] = {}

    for layer_idx, block in enumerate(blocks):
        block_to_indices.setdefault(
            block,
            [],
        ).append(layer_idx)

    state: dict[str, object] = {
        "mask": None,
        "call_counts": None,
    }

    def make_hook(block: torch.nn.Module):
        indices = block_to_indices[block]

        def hook(_module, _inputs, output):
            call_counts = state["call_counts"]
            if call_counts is None:
                return None

            call_index = call_counts[block]

            if call_index >= len(indices):
                raise RuntimeError(
                    "Block hook was called more times than expected"
                )

            layer_idx = indices[call_index]
            call_counts[block] += 1

            if layer_idx not in layer_set:
                return None

            hidden = extract_hidden(output)

            hidden = normalize_layer_output(
                model=model,
                hidden=hidden,
                layer_idx=layer_idx,
                representation=args.representation,
            )

            mask = state["mask"]

            if not isinstance(mask, torch.Tensor):
                raise RuntimeError(
                    "No padding mask is active during feature extraction"
                )

            local_mask = mask.to(
                device=hidden.device,
                dtype=hidden.dtype,
            )

            denominator = local_mask.sum(
                dim=1,
                keepdim=True,
            ).clamp(min=1)

            pooled = (
                hidden * local_mask.unsqueeze(-1)
            ).sum(dim=1) / denominator

            writer.add(layer_idx, pooled)

            # Do not replace the model's block output.
            return None

        return hook

    handles = [
        block.register_forward_hook(make_hook(block))
        for block in block_to_indices
    ]

    completed = False

    try:
        with torch.no_grad():
            for start in tqdm(
                range(0, len(sequences), args.batch_size),
                desc="Extracting Evo-2 features",
            ):
                sequence_batch = sequences[
                    start : start + args.batch_size
                ]

                token_ids = tokenize_sequences(
                    sequence_batch,
                    loaded.tokenizer,
                    max_length=args.max_length,
                )

                input_ids, mask = pad_batch(
                    token_ids,
                    loaded.tokenizer.pad_id,
                )

                input_ids = input_ids.to(input_device)
                mask = mask.to(input_device)

                state["mask"] = mask
                state["call_counts"] = {
                    block: 0
                    for block in block_to_indices
                }

                _ = forward_inference(
                    loaded,
                    input_ids,
                    padding_mask=mask,
                )

                call_counts = state["call_counts"]
                total_calls = sum(call_counts.values())
                state["call_counts"] = None

                if total_calls != num_layers:
                    raise RuntimeError(
                        f"Expected {num_layers} block calls, "
                        f"observed {total_calls}"
                    )

        writer.flush_all()
        completed = True
    finally:
        state["call_counts"] = None

        for handle in handles:
            handle.remove()

    if completed:
        print(
            f"Wrote Evo-2 features to {args.out_dir}"
        )


if __name__ == "__main__":
    main()
