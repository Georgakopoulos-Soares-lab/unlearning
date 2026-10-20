"""Model-independent causal scoring and pooling, tested with synthetic inputs."""
import math

import torch
import torch.nn.functional as F


def causal_nll(logits, tokens, mask, special_ids=()):
    """No BOS: predict positions 1..L-1, excluding padding/special targets."""
    if logits.ndim != 3 or logits.shape[:2] != tokens.shape or mask.shape != tokens.shape:
        raise ValueError("Expected aligned [B,L,V] logits and [B,L] tokens/mask")
    if not torch.isfinite(logits).all():
        raise ValueError("Nonfinite logits")
    valid = mask[:, 1:].bool() & mask[:, :-1].bool()
    for token_id in special_ids:
        valid &= tokens[:, 1:] != token_id
    counts = valid.sum(1)
    if (counts == 0).any():
        raise ValueError("Zero valid causal targets")
    losses = F.cross_entropy(logits[:, :-1].float().transpose(1, 2), tokens[:, 1:], reduction="none")
    sums = (losses.double() * valid).sum(1)
    if not torch.isfinite(sums).all():
        raise ValueError("Nonfinite NLL")
    return sums.cpu().tolist(), counts.cpu().tolist()


def aggregate(rows):
    if not rows or any(not isinstance(r['n_tokens'], int) or r['n_tokens'] <= 0 for r in rows):
        raise ValueError("Positive integer target counts required")
    if any(not math.isfinite(r['nll_sum']) or r['nll_sum'] < 0 for r in rows):
        raise ValueError("Finite nonnegative NLL sums required")
    count = sum(r['n_tokens'] for r in rows)
    nll = math.fsum(r['nll_sum'] for r in rows) / count
    overflow = nll > math.log(float.fromhex('0x1.fffffffffffffp+1023'))
    return dict(corpus_nll=nll, n_tokens=count, n_examples=len(rows),
                perplexity=None if overflow else math.exp(nll), perplexity_overflow=overflow)


def masked_pool(hidden, mask):
    if hidden.ndim != 3 or hidden.shape[:2] != mask.shape or not mask.bool().any(1).all():
        raise ValueError("Nonempty aligned pooling masks required")
    if not torch.isfinite(hidden).all():
        raise ValueError("Nonfinite representations")
    weights = mask.to(dtype=torch.float32).unsqueeze(-1)
    return ((hidden.float() * weights).sum(1) / weights.sum(1)).detach().cpu()
