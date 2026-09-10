from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Optional

import torch


# Permit:
#     python phase1_evo2/env_test.py
if __package__ is None and __name__ == "__main__":
    sys.path.append(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )


def resolve_input_device(
    loaded: LoadedEvo2,
    requested_device: Optional[str],
) -> torch.device:
    """Choose the device on which input token IDs should be placed."""
    if requested_device:
        device = torch.device(requested_device)

        if device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                f"Requested {device}, but CUDA is not available"
            )

        return device

    for parameter in loaded.model.parameters():
        if parameter.device.type != "meta":
            return parameter.device

    raise RuntimeError(
        "Could not infer the Evo-2 input device from model parameters. "
        "Pass --input-device explicitly."
    )


def tensor_summary(tensor: torch.Tensor) -> dict:
    """Return compact numerical diagnostics for a tensor."""
    values = tensor.detach().float()

    return {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype),
        "device": str(tensor.device),
        "requires_grad": bool(tensor.requires_grad),
        "finite": bool(torch.isfinite(values).all().item()),
        "mean": float(values.mean().item()),
        "std": float(values.std(unbiased=False).item()),
        "min": float(values.min().item()),
        "max": float(values.max().item()),
        "mean_l2": float(
            torch.linalg.vector_norm(
                values.reshape(values.shape[0], -1),
                dim=1,
            ).mean().item()
        ),
    }


def check_forward_hook(
    loaded: LoadedEvo2,
    input_ids: torch.Tensor,
    layer_idx: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Run inference while capturing one block's output."""
    block = get_block(loaded.model, layer_idx)
    captured: dict[str, torch.Tensor] = {}

    def capture_hook(_module, _inputs, output):
        hidden = extract_hidden(output)
        captured["hidden"] = hidden.detach()

        # Returning None leaves the block output unchanged.
        return None

    handle = block.register_forward_hook(capture_hook)

    try:
        logits = forward_inference(loaded, input_ids)
    finally:
        handle.remove()

    if "hidden" not in captured:
        raise RuntimeError(
            f"Forward hook for layer {layer_idx} was never called"
        )

    return logits, captured["hidden"]

def check_selected_layer_backward(
    loaded: LoadedEvo2,
    input_ids: torch.Tensor,
    layer_idx: int,
) -> dict:
    """Verify gradients reach parameters in one selected block."""
    model = loaded.model
    block = get_block(model, layer_idx)

    original_requires_grad = {
        id(parameter): parameter.requires_grad
        for parameter in model.parameters()
    }

    try:
        model.zero_grad(set_to_none=True)

        # Freeze the entire model, then enable only the selected block.
        for parameter in model.parameters():
            parameter.requires_grad_(False)

        for parameter in block.parameters():
            parameter.requires_grad_(True)

        trainable_parameters = [
            parameter
            for parameter in block.parameters()
            if parameter.requires_grad
        ]

        if not trainable_parameters:
            raise RuntimeError(
                f"Layer {layer_idx} contains no trainable parameters"
            )

        logits = forward_differentiable(loaded, input_ids)

        # A simple scalar objective is sufficient for a gradient smoke test.
        loss = logits.float().square().mean()

        if not loss.requires_grad:
            raise RuntimeError(
                "Differentiable forward produced a loss without gradients"
            )

        loss.backward()

        gradients = [
            parameter.grad
            for parameter in trainable_parameters
            if parameter.grad is not None
        ]

        if not gradients:
            raise RuntimeError(
                f"No gradients reached layer {layer_idx}"
            )

        finite = all(
            torch.isfinite(gradient.float()).all().item()
            for gradient in gradients
        )
        total_squared_norm = sum(
            gradient.detach().float().square().sum().item()
            for gradient in gradients
        )

        return {
            "layer": layer_idx,
            "loss": float(loss.detach().item()),
            "trainable_parameter_count": sum(
                parameter.numel()
                for parameter in trainable_parameters
            ),
            "parameters_with_gradients": len(gradients),
            "gradients_finite": bool(finite),
            "gradient_l2": float(total_squared_norm**0.5),
        }
    finally:
        model.zero_grad(set_to_none=True)

        for parameter in model.parameters():
            parameter.requires_grad_(
                original_requires_grad[id(parameter)]
            )

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test a real Evo-2 checkpoint and Phase 1 utilities."
    )
    parser.add_argument(
        "--model-name",
        default="evo2_7b_base",
        help="Official Evo-2 checkpoint name.",
    )
    parser.add_argument(
        "--local-path",
        default=None,
        help=(
            "Optional local Evo-2 checkpoint. If omitted, the official "
            "loader uses the Hugging Face cache or downloads the checkpoint."
        ),
    )
    parser.add_argument(
        "--sequence",
        default="ACGTACGTACGTACGT",
        help="Short DNA sequence used for the smoke test.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=128,
    )
    parser.add_argument(
        "--layer",
        type=int,
        default=0,
        help="Block whose output should be captured.",
    )
    parser.add_argument(
        "--input-device",
        default=None,
        help=(
            "Device for input IDs, such as cuda:0. If omitted, infer it "
            "from the model's first non-meta parameter."
        ),
    )
    parser.add_argument(
        "--use-kernels",
        action="store_true",
        help="Enable optional Vortex Triton inference kernels.",
    )
    parser.add_argument(
        "--check-backward",
        action="store_true",
        help=(
            "Also run a selected-layer gradient check. This requires "
            "considerably more GPU memory than inference."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.max_length <= 0:
        raise ValueError("--max-length must be positive")

    sequence = clean_sequence(args.sequence)
    if not sequence:
        raise ValueError(
            "--sequence contains no valid A, C, G, T, or N bases"
        )

    sequence = sequence[: args.max_length]

    print(
        f"[evo2-test] loading model={args.model_name}",
        flush=True,
    )
    load_started = time.perf_counter()

    loaded = load_huggingface_checkpoint(
        model_name=args.model_name,
        local_path=args.local_path,
        use_kernels=args.use_kernels,
    )

    load_seconds = time.perf_counter() - load_started
    loaded.model.eval()

    blocks = get_blocks(loaded.model)
    num_layers = len(blocks)

    if not 0 <= args.layer < num_layers:
        raise ValueError(
            f"--layer {args.layer} is outside "
            f"[0, {num_layers - 1}]"
        )

    input_device = resolve_input_device(
        loaded,
        args.input_device,
    )

    token_ids = tokenize_sequences(
        [sequence],
        loaded.tokenizer,
        max_length=args.max_length,
    )

    if len(token_ids) != 1 or not token_ids[0]:
        raise RuntimeError(
            "Tokenizer did not produce tokens for the test sequence"
        )

    input_ids = torch.tensor(
        token_ids,
        dtype=torch.int,
        device=input_device,
    )

    print(
        "[evo2-test] "
        f"layers={num_layers} "
        f"tokens={input_ids.shape[1]} "
        f"input_device={input_device}",
        flush=True,
    )

    forward_started = time.perf_counter()
    logits, hidden = check_forward_hook(
        loaded,
        input_ids,
        args.layer,
    )
    forward_seconds = time.perf_counter() - forward_started

    if logits.shape[0] != input_ids.shape[0]:
        raise RuntimeError(
            "Logit batch dimension does not match input batch dimension"
        )

    if logits.shape[1] != input_ids.shape[1]:
        raise RuntimeError(
            "Logit sequence dimension does not match input sequence dimension"
        )

    if hidden.shape[0] != input_ids.shape[0]:
        raise RuntimeError(
            "Hidden-state batch dimension does not match input"
        )

    if hidden.shape[1] != input_ids.shape[1]:
        raise RuntimeError(
            "Hidden-state sequence dimension does not match input"
        )

    logits_diagnostics = tensor_summary(logits)
    hidden_diagnostics = tensor_summary(hidden)

    if not logits_diagnostics["finite"]:
        raise RuntimeError("Evo-2 logits contain NaN or infinity")

    if not hidden_diagnostics["finite"]:
        raise RuntimeError(
            f"Evo-2 layer {args.layer} contains NaN or infinity"
        )

    result = {
        "status": "ok",
        "model_family": "evo2",
        "model_name": args.model_name,
        "local_path": args.local_path,
        "use_kernels": args.use_kernels,
        "num_layers": num_layers,
        "checked_layer": args.layer,
        "sequence_length_bases": len(sequence),
        "sequence_length_tokens": int(input_ids.shape[1]),
        "input_dtype": str(input_ids.dtype),
        "input_device": str(input_ids.device),
        "load_seconds": load_seconds,
        "forward_seconds": forward_seconds,
        "logits": logits_diagnostics,
        "hidden": hidden_diagnostics,
    }

    if args.check_backward:
        print(
            f"[evo2-test] checking gradients at layer {args.layer}",
            flush=True,
        )
        result["backward"] = check_selected_layer_backward(
            loaded,
            input_ids,
            args.layer,
        )

        if not result["backward"]["gradients_finite"]:
            raise RuntimeError(
                "Selected-layer backward pass produced nonfinite gradients"
            )

    if torch.cuda.is_available():
        result["cuda"] = {
            "device_count": torch.cuda.device_count(),
            "allocated_gb": torch.cuda.memory_allocated()
            / (1024**3),
            "reserved_gb": torch.cuda.memory_reserved()
            / (1024**3),
        }

    print(json.dumps(result, indent=2))
    print("[evo2-test] PASS", flush=True)


if __name__ == "__main__":
    main()