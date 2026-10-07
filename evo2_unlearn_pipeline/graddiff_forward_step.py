"""Forward step + loss function for Gradient Difference unlearning.

Standard full-parameter causal-LM forward passes (same mechanism as our
original --mock-data and --fasta-data/--dataset-config smoke tests -- model
called with labels= set, which triggers Megatron's internal fused
cross-entropy so the model itself returns PER-TOKEN LOSSES directly, not
logits). We call the model TWICE per training step -- once on a forget
batch, once on a retain batch -- then combine the two losses into Gradient
Difference's objective:

    L = -alpha_forget * mean(forget_per_token_loss) + alpha_retain * mean(retain_per_token_loss)

Minimizing this (via standard gradient DESCENT on L) is equivalent to
gradient ASCENT on the forget loss (pushing the model to do WORSE on forget
data, scaled by alpha_forget) jointly with gradient DESCENT on the retain
loss (keeping retain performance intact, scaled by alpha_retain) -- the
standard "Gradient Difference" unlearning objective.

DIVERGENCE WARNING (confirmed by a prior, independently-validated Evo-1 GD
implementation whose archived runs are the empirical basis for this): the
`-alpha_forget * L_forget` term is UNBOUNDED BELOW, so this objective can
diverge if run too long or too "hot" (too high alpha_forget relative to
alpha_retain, or too high an LR). That prior implementation's own archived
runs saw retain perplexity jump from ~4.2 to 15.7-37.9 even with
alpha_retain=5.0 (5x the forget weight) as the default. This is NOT a bug in
the formulation -- it's inherent to Gradient Difference, and is exactly why
`forget_loss_cap` exists as an optional safety valve (clamps the forget
cross-entropy before weighting/negation; default 0.0 = disabled).

ASSUMPTION TO VERIFY (see comment near batch key access below): this assumes
Evo2Dataset's per-sample dict has keys "tokens", "labels", "loss_mask",
"position_ids" -- the same keys the ORIGINAL hyena_forward_step/get_batch
pipeline consumes. We have not directly inspected Evo2Dataset.__getitem__'s
source to 100% confirm this; if the smoke test KeyErrors here, that's the
first thing to check (print(batch.keys()) to see the real key names).

LIMITATION: the loss-reporting "count=1 per microbatch" pattern below only
produces a CORRECT cross-rank average under single-GPU / no-data-parallelism
(our current H200 single-GPU setup). If this is ever scaled to multi-GPU
data parallelism, this reporting contract needs revisiting (should sum
token counts like the original masked_next_token_loss does, not report a
flat count=1).
"""

from functools import partial
from typing import Iterable

import torch


def graddiff_data_step(data_iterator: Iterable) -> dict[str, torch.Tensor]:
    """Pull one dual (forget+retain) microbatch and move it to GPU.

    Mirrors classification_data_step's simplification: skips Megatron-Bridge's
    stage-aware get_batch_from_iterator since we're TP=1/PP=1/CP=1. Would need
    updating for pipeline parallelism.
    """
    batch = next(data_iterator)
    return {k: v.cuda(non_blocking=True) if v is not None else None for k, v in batch.items()}


def graddiff_forward_step(state, data_iterator: Iterable, model, return_schedule_plan: bool = False):
    """Forward step: two full causal-LM forward passes (forget, retain) per step."""
    if return_schedule_plan:
        raise NotImplementedError("Schedule plans are not used by the Gradient Difference forward step.")

    batch = graddiff_data_step(data_iterator)

    forget_tokens = batch["forget_tokens"]
    forget_position_ids = batch["forget_position_ids"]
    forget_labels = batch["forget_labels"]
    forget_loss_mask = batch["forget_loss_mask"]

    retain_tokens = batch["retain_tokens"]
    retain_position_ids = batch["retain_position_ids"]
    retain_labels = batch["retain_labels"]
    retain_loss_mask = batch["retain_loss_mask"]

    forget_output = model(
        input_ids=forget_tokens,
        position_ids=forget_position_ids,
        attention_mask=None,
        loss_mask=forget_loss_mask,
        labels=forget_labels,
    )
    retain_output = model(
        input_ids=retain_tokens,
        position_ids=retain_position_ids,
        attention_mask=None,
        loss_mask=retain_loss_mask,
        labels=retain_labels,
    )

    alpha_forget = getattr(state.cfg, "graddiff_alpha_forget", 1.0)
    alpha_retain = getattr(state.cfg, "graddiff_alpha_retain", 5.0)
    forget_loss_cap = getattr(state.cfg, "graddiff_forget_loss_cap", 0.0)
    loss_function = partial(
        graddiff_loss_function,
        forget_loss_mask,
        retain_loss_mask,
        alpha_forget,
        alpha_retain,
        forget_loss_cap,
    )
    # Bundle both outputs into one tuple; the loss function unpacks them.
    # Calling .backward() on the combined scalar loss correctly backprops
    # through BOTH forward passes' computational graphs in one go (standard
    # PyTorch autograd semantics -- no special handling needed for the two
    # separate forward() calls feeding into one final loss).
    return (forget_output, retain_output), loss_function


def graddiff_loss_function(
    forget_loss_mask: torch.Tensor,
    retain_loss_mask: torch.Tensor,
    alpha_forget: float,
    alpha_retain: float,
    forget_loss_cap: float,
    output_tensor: tuple[torch.Tensor, torch.Tensor],
    check_for_nan_in_loss: bool = True,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, tuple[torch.Tensor, torch.Tensor]]]:
    """Gradient Difference loss: -alpha_forget*mean(forget_loss) + alpha_retain*mean(retain_loss).

    forget_loss_cap > 0.0 clamps the forget cross-entropy (BEFORE weighting
    and negation) at that value -- a safety valve against the unbounded-below
    divergence described in the module docstring. 0.0 (default) disables
    clamping entirely.
    """
    forget_output, retain_output = output_tensor

    forget_losses = forget_output.view(-1).float()
    retain_losses = retain_output.view(-1).float()
    fmask = forget_loss_mask.view(-1).float()
    rmask = retain_loss_mask.view(-1).float()

    forget_count = fmask.sum().clamp(min=1.0)
    retain_count = rmask.sum().clamp(min=1.0)
    forget_loss_mean = (forget_losses * fmask).sum() / forget_count
    retain_loss_mean = (retain_losses * rmask).sum() / retain_count

    forget_loss_effective = forget_loss_mean
    if forget_loss_cap > 0.0:
        forget_loss_effective = torch.clamp(forget_loss_mean, max=forget_loss_cap)

    weighted_forget_term = -alpha_forget * forget_loss_effective
    weighted_retain_term = alpha_retain * retain_loss_mean
    total_loss = weighted_forget_term + weighted_retain_term

    if check_for_nan_in_loss:
        if torch.isnan(total_loss).any() or torch.isinf(total_loss).any():
            raise FloatingPointError(
                f"NaN/Inf in Gradient Difference loss (forget={forget_loss_mean.item()}, "
                f"retain={retain_loss_mean.item()})"
            )

    # NOTE (see module docstring LIMITATION): count=1 is only correct for
    # single-GPU / no data parallelism.
    count = torch.tensor(1, dtype=torch.int, device=total_loss.device)
    reporting = torch.cat([total_loss.clone().detach().view(1), count.view(1)])
    forget_reporting = torch.cat([forget_loss_mean.clone().detach().view(1), count.view(1)])
    forget_effective_reporting = torch.cat([forget_loss_effective.clone().detach().view(1), count.view(1)])
    retain_reporting = torch.cat([retain_loss_mean.clone().detach().view(1), count.view(1)])

    return (
        total_loss,
        count,
        {
            "graddiff loss": reporting,
            "forget loss": forget_reporting,
            "forget loss effective": forget_effective_reporting,
            "retain loss": retain_reporting,
        },
    )
