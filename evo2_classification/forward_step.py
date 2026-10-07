from functools import partial
from typing import Iterable

import torch

from .model import HyenaForSequenceClassification


def classification_data_step(data_iterator: Iterable) -> dict[str, torch.Tensor]:
    """Pull one microbatch and move it to GPU.

    NOTE: this deliberately skips Megatron-Bridge's `get_batch_from_iterator`
    (used by causal-LM `hyena_forward_step`) because that function's device/host
    key routing is built around the LM batch schema (tokens/labels/loss_mask
    with per-pipeline-stage conditionals). We're running TP=1/PP=1/CP=1 for
    this classification setup, so pipeline-stage routing is unnecessary --
    we just move everything to GPU directly. If you later scale this up to
    multi-GPU with pipeline parallelism, this function will need the same
    stage-aware key routing `get_batch_from_iterator` does.
    """
    batch = next(data_iterator)
    return {k: v.cuda(non_blocking=True) for k, v in batch.items()}


def classification_forward_step(state, data_iterator: Iterable, model: HyenaForSequenceClassification):
    """Forward step for classification fine-tuning.

    Mirrors the shape of `hyena_forward_step` in evo2_provider.py: returns
    (output_tensor, loss_function_partial).
    """
    batch = classification_data_step(data_iterator)
    tokens = batch["tokens"]
    position_ids = batch["position_ids"]
    labels = batch["label"]
    loss_mask = batch["loss_mask"]

    logits = model(
        input_ids=tokens,
        position_ids=position_ids,
        attention_mask=None,
        loss_mask=loss_mask,
    )

    loss_function = partial(classification_loss_function, labels)
    return logits, loss_function


def classification_loss_function(
    labels: torch.Tensor,
    output_tensor: torch.Tensor,
    check_for_nan_in_loss: bool = True,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, tuple[torch.Tensor, torch.Tensor]]]:
    """Classification loss, following the same (loss, count, reporting_dict)
    contract as `masked_next_token_loss` -- SUM of per-sample losses and a
    COUNT of samples, so that Megatron-Bridge's cross-data-parallel-rank
    averaging (sum(loss)/sum(count)) produces a correct global mean, exactly
    analogous to how the LM loss uses sum-of-token-losses / count-of-tokens.
    """
    logits = output_tensor.float()
    loss = torch.nn.functional.cross_entropy(logits, labels, reduction="sum")

    if check_for_nan_in_loss:
        if torch.isnan(loss).any() or torch.isinf(loss).any():
            raise FloatingPointError("NaN or Inf in classification loss forward calculation")

    num_samples = torch.tensor(labels.numel(), dtype=torch.int, device=loss.device)
    reporting_loss = torch.cat([loss.clone().detach().view(1), num_samples.view(1)])

    return loss, num_samples, {"cls loss": reporting_loss}
