"""Activation-steering sanity check for an Evo-2 probe direction."""

import argparse
import os
import sys

import numpy as np
import torch

if __package__ is None and __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from phase1_evo2.utils import (
    extract_hidden,
    forward_inference,
    get_block,
    load_huggingface_checkpoint,
    module_device,
    normalize_layer_output,
    pad_batch,
    tokenize_sequences,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Activation steering sanity check using an Evo-2 probe vector."
    )
    parser.add_argument("--model-name", default="evo2_7b_base")
    parser.add_argument("--local-path", default=None)
    parser.add_argument("--use-kernels", action="store_true")
    parser.add_argument("--probe", required=True)
    parser.add_argument("--layer-idx", type=int, required=True)
    parser.add_argument("--sequence", default="ACGTACGTACGT")
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--alpha", type=float, default=1.0)
    parser.add_argument("--input-device", default=None)
    parser.add_argument(
        "--representation",
        choices=["raw", "next_norm"],
        default="raw",
        help="Representation used to train the probe.",
    )
    args = parser.parse_args()
    if args.representation != "raw":
        raise ValueError(
            "Steering a next_norm probe direction at the raw block output is not "
            "well-defined; use a probe trained with --representation raw."
        )

    loaded = load_huggingface_checkpoint(
        model_name=args.model_name,
        local_path=args.local_path,
        use_kernels=args.use_kernels,
    )
    model = loaded.model
    model.eval()
    block = get_block(model, args.layer_idx)
    input_device = (
        torch.device(args.input_device)
        if args.input_device
        else module_device(model.embedding_layer)
    )

    probe_data = np.load(args.probe)
    probe = {
        "coef": torch.from_numpy(probe_data["coef"]).float(),
        "intercept": torch.from_numpy(probe_data["intercept"]).float(),
        "mean": torch.from_numpy(probe_data["scaler_mean"]).float(),
        "scale": torch.from_numpy(probe_data["scaler_scale"]).float(),
    }

    token_ids = tokenize_sequences(
        [args.sequence],
        loaded.tokenizer,
        args.max_length,
    )
    input_ids, mask = pad_batch(token_ids, loaded.tokenizer.pad_id)
    input_ids = input_ids.to(input_device)

    def run(steer: bool) -> float:
        pooled_store = {}

        def hook(_module, _inputs, output):
            hidden = extract_hidden(output)
            if steer:
                coef = probe["coef"].to(hidden.device)
                scale = probe["scale"].to(hidden.device).clamp(min=1e-12)
                hidden = hidden + args.alpha * (coef / scale).view(1, 1, -1)

            probe_hidden = normalize_layer_output(
                model,
                hidden,
                args.layer_idx,
                args.representation,
            )
            local_mask = mask.to(probe_hidden.device, dtype=probe_hidden.dtype)
            denominator = local_mask.sum(dim=1, keepdim=True).clamp(min=1)
            pooled_store["pooled"] = (
                probe_hidden * local_mask.unsqueeze(-1)
            ).sum(dim=1) / denominator

            if not steer:
                return None
            if isinstance(output, tuple):
                return (hidden, *output[1:])
            if isinstance(output, list):
                return [hidden, *output[1:]]
            if isinstance(output, dict):
                replacement = dict(output)
                replacement["hidden_states"] = hidden
                return replacement
            return hidden

        handle = block.register_forward_hook(hook)
        try:
            forward_inference(loaded, input_ids)
        finally:
            handle.remove()

        pooled = pooled_store["pooled"].float()
        local_probe = {
            key: value.to(pooled.device)
            for key, value in probe.items()
        }
        if pooled.shape[-1] != local_probe["mean"].numel():
            raise ValueError(
                f"Probe expects {local_probe['mean'].numel()} features, "
                f"but layer {args.layer_idx} produced {pooled.shape[-1]}."
            )
        standardized = (
            pooled - local_probe["mean"]
        ) / local_probe["scale"].clamp(min=1e-12)
        return (
            standardized @ local_probe["coef"].T + local_probe["intercept"]
        ).item()

    baseline = run(steer=False)
    steered = run(steer=True)
    print(f"Probe score baseline: {baseline:.4f}")
    print(f"Probe score steered (+alpha={args.alpha}): {steered:.4f}")


if __name__ == "__main__":
    main()
