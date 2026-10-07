from dataclasses import dataclass

import torch
from megatron.core.utils import make_sharded_tensor_for_checkpoint
from megatron.core.extensions.transformer_engine import TENorm
from torch import nn

from bionemo.evo2.models.evo2_provider import Hyena1bModelProvider
from bionemo.evo2.models.megatron.hyena.hyena_model import HyenaModel as MCoreHyenaModel


class HyenaForSequenceClassification(nn.Module):
    """Wraps a Hyena backbone (post_process=False, i.e. raw hidden states) with a
    linear classification head over the LAST REAL TOKEN's hidden state.

    IMPORTANT FIX: when post_process=False, the backbone's own HyenaStack does
    NOT construct its final normalization layer at all (confirmed by reading
    hyena_block.py: `self.final_norm = None` when post_process=False, with an
    explicit comment "Ensure final_norm is always defined to avoid
    AttributeError"). This means the raw hidden states coming out of the
    backbone are UNNORMALIZED residual-stream activations, not the normalized
    representation the model was actually trained to produce. Feeding these
    directly into a freshly-initialized linear classifier caused a real loss
    explosion in the first training run (cls loss ~1e14, grad norm ~1e16) --
    not numerical noise, a genuine missing-normalization bug. We build our own
    copy of that same final norm layer here and load its pretrained weights
    from the checkpoint's "decoder.final_norm.weight" key (see
    sharded_state_dict below) so we reproduce the exact representation the
    model's own causal-LM head would have seen.
    """

    def __init__(self, backbone: MCoreHyenaModel, hidden_size: int, num_classes: int):
        super().__init__()
        self.backbone = backbone
        # Megatron-core utilities (get_model_config, DDP wrapping, etc.) expect
        # a `.config` attribute on the model -- reuse the backbone's config.
        self.config = backbone.config
        # Replicates HyenaStack's own final_norm (hyena_block.py), which the
        # backbone itself does NOT construct when post_process=False.
        self.final_norm = TENorm(
            config=self.config,
            hidden_size=hidden_size,
            eps=self.config.layernorm_epsilon,
        )
        self.classifier = nn.Linear(hidden_size, num_classes)

    def set_input_tensor(self, input_tensor):
        """Required by Megatron's pipeline-parallel input-tensor passing. With
        PP=1 (single GPU / no pipeline parallelism) this just forwards to the
        backbone, which is itself a no-op in that case.
        """
        self.backbone.set_input_tensor(input_tensor)

    def sharded_state_dict(self, prefix: str = "", sharded_offsets: tuple = (), metadata: dict | None = None):
        """Required by Megatron-Bridge's distributed checkpoint load/save.

        IMPORTANT: the base Evo2 checkpoint (converted from Savanna) was saved
        from a PLAIN HyenaModel with no wrapper -- its keys look like
        "embedding.word_embeddings.weight", "decoder.layers.0...", etc. We must
        NOT prepend "backbone." to those keys, or every single one will mismatch
        the checkpoint on disk and the backbone will silently load with random
        weights instead of the pretrained ones. So we delegate the backbone's
        sharded_state_dict with the SAME prefix we were given (passthrough),
        and only the new classifier head gets its own "classifier." namespace
        (which won't exist in the base checkpoint -- that's expected, since
        it's a newly-initialized head).
        """
        sharded_state_dict = self.backbone.sharded_state_dict(
            prefix=prefix, sharded_offsets=sharded_offsets, metadata=metadata
        )
        # Our final_norm doesn't live inside self.backbone (the backbone's own
        # version is None when post_process=False), so it isn't included in the
        # delegation above. Map OUR module's weight to the SAME key the
        # checkpoint actually has ("decoder.final_norm.weight"), not our own
        # naming ("final_norm.weight"), so the pretrained norm weights load
        # correctly instead of starting from random initialization.
        #
        # IMPORTANT: a raw/plain tensor here is silently NEVER populated by
        # the loader, even when the checkpoint key exists and no error is
        # raised (confirmed empirically -- final_norm.weight stayed at
        # TENorm's default all-1.0s init despite the checkpoint having real
        # trained values). Megatron-Core's dist_checkpointing loader requires
        # a properly wrapped ShardedTensor to know how to write loaded data
        # into a tensor; TENorm itself has no sharded_state_dict() method
        # (confirmed: `hasattr(TENorm, 'sharded_state_dict')` is False), so
        # whatever generic mechanism handles this for the REAL model's
        # final_layernorm must be doing this same wrapping, and we replicate
        # it explicitly here using the same helper Megatron-Core itself uses
        # (megatron.core.utils.make_sharded_tensor_for_checkpoint).
        final_norm_key = f"{prefix}decoder.final_norm.weight"
        sharded_state_dict[final_norm_key] = make_sharded_tensor_for_checkpoint(
            self.final_norm.weight, final_norm_key, prepend_offsets=sharded_offsets
        )
        classifier_prefix = f"{prefix}classifier."
        for name, param in self.classifier.state_dict(keep_vars=True).items():
            full_key = f"{classifier_prefix}{name}"
            sharded_state_dict[full_key] = make_sharded_tensor_for_checkpoint(
                param, full_key, prepend_offsets=sharded_offsets
            )
        return sharded_state_dict

    def forward(
        self,
        input_ids: torch.Tensor,
        position_ids: torch.Tensor,
        attention_mask: torch.Tensor | None,
        loss_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Returns classification logits, shape [batch, num_classes].

        Args:
            loss_mask: [batch, seq_len] with 1 for real (non-padding) tokens,
                0 for padding. Used to mean-pool only over real tokens.

        Pooling: MEAN over all real tokens (not last-token). A recent
        benchmark (Nature Communications, "Benchmarking DNA foundation
        models for genomic and genetic tasks") found mean pooling
        significantly outperforms last/summary-token pooling for sequence
        classification across DNA foundation models INCLUDING HyenaDNA
        (same architecture family as this backbone) -- avg. AUC improvement
        8.7% (IQR 4.6-12.9%) for HyenaDNA specifically, across 52 binary
        classification datasets. HyenaDNA's own codebase also treats
        pooling (mean/last/first) as a configurable choice, not a fixed
        recommendation.
        """
        hidden_states = self.backbone(
            input_ids=input_ids,
            position_ids=position_ids,
            attention_mask=attention_mask,
        )
        # Apply the normalization the backbone itself would have applied here
        # (post_process=False skips it entirely -- see class docstring).
        hidden_states = self.final_norm(hidden_states)
        # hidden_states: [seq_len, batch, hidden] (Megatron sequence-first convention,
        # confirmed from hyena_block.py docstrings: "[s, b, h]").
        mask = loss_mask.transpose(0, 1).unsqueeze(-1).to(hidden_states.dtype)  # [seq_len, batch, 1]
        summed = (hidden_states * mask).sum(dim=0)  # [batch, hidden]
        counts = loss_mask.sum(dim=1, keepdim=True).to(hidden_states.dtype)  # [batch, 1]
        pooled = summed / counts  # [batch, hidden] -- mean over real tokens only
        logits = self.classifier(pooled.to(self.classifier.weight.dtype))
        return logits.float()


@dataclass
class HyenaClassificationModelProvider(Hyena1bModelProvider):
    """Same architecture/hyperparameters as evo2_1b_base (Hyena1bModelProvider),
    but `provide()` builds the backbone with post_process=False and wraps it
    with a classification head instead of the causal-LM output layer.
    """

    num_classes: int = 2

    def provide(self, pre_process=None, post_process=None, vp_stage=None) -> HyenaForSequenceClassification:
        # Force post_process=False regardless of what the training loop passes in --
        # we never want the causal-LM output layer / vocab logits.
        self.post_process = False
        backbone = super().provide(pre_process=pre_process, post_process=False, vp_stage=vp_stage)
        return HyenaForSequenceClassification(
            backbone=backbone,
            hidden_size=self.hidden_size,
            num_classes=self.num_classes,
        )
