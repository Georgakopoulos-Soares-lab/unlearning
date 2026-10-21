"""Extension of the official evo2_classifier.py: train a classification head
from a SPECIFIC INTERMEDIATE decoder layer's hidden states, instead of only
the final layer's output.

Useful beyond just this immediate need -- this is exactly the per-layer
linear-probing infrastructure needed later for RMU's joint_probe target
direction mode, or for a causal layer-localization study (both discussed
and deferred earlier in this project).

UNVERIFIED ASSUMPTION, flagged rather than silently trusted: this assumes
`model.decoder.layers` is an indexable ModuleList with one entry per
Hyena/attention layer, and that each layer's forward() output is either a
plain tensor or a tuple whose first element is the hidden state (same
defensive pattern a prior Evo-1 RMU reference implementation used for its
own hook-based activation capture). Smoke test before trusting results from
this script -- if decoder.layers doesn't exist or isn't indexable this way,
the hook registration / forward pass will raise loudly rather than silently
misbehave.

Usage: identical CLI to evo2_classifier.py, plus one new flag:
    --probe-layer N    (0-indexed; omit for the original final-layer behavior)
"""

import sys
from dataclasses import dataclass
from typing import Optional

import torch
from torch import Tensor

from bionemo.evo2.models.evo2_provider import Hyena1bModelProvider

# Import everything from the official script rather than duplicating it.
from evo2_classifier import (
    CLASSIFIER_PROVIDER_OPTIONS,
    HyenaForSequenceClassification,
    HyenaForSequenceClassificationProvider,
    _parse_args,
    evo2_1b_classifier_config,
    train_classifier,
)


class HyenaForSequenceClassificationAtLayer(HyenaForSequenceClassification):
    """Same as HyenaForSequenceClassification, but pools from a SPECIFIC
    intermediate decoder layer's output (captured via a forward hook)
    instead of the final decoder output, when probe_layer is set.
    """

    def __init__(self, *, probe_layer: Optional[int] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.probe_layer = probe_layer
        self._captured_hidden: Optional[Tensor] = None
        self._hook_handle = None
        if self.probe_layer is not None:
            # UNVERIFIED: see module docstring.
            target_layer = self.decoder.layers[self.probe_layer]
            self._hook_handle = target_layer.register_forward_hook(self._capture_hook)

    def _capture_hook(self, _module, _inputs, output) -> None:
        self._captured_hidden = output[0] if isinstance(output, tuple) else output

    def forward(  # type: ignore[override]
        self,
        input_ids: Tensor,
        position_ids: Optional[Tensor] = None,
        attention_mask: Optional[Tensor] = None,
        labels: Optional[Tensor] = None,
        pool_mask: Optional[Tensor] = None,
        **_unused,
    ) -> Tensor:
        """Identical to the parent class's forward(), except hidden_states is
        swapped for the captured intermediate layer's output when
        probe_layer is set.
        """
        if position_ids is None:
            seq_len = input_ids.shape[1]
            position_ids = torch.arange(seq_len, device=input_ids.device).unsqueeze(0).expand_as(input_ids)

        decoder_input, rotary_pos_emb, rotary_pos_cos, rotary_pos_sin, sequence_len_offset = self._preprocess(
            input_ids=input_ids,
            position_ids=position_ids,
            decoder_input=None,
            inference_context=None,
            packed_seq_params=None,
        )

        hidden_states = self.decoder(
            hidden_states=decoder_input,
            attention_mask=attention_mask,
            inference_context=None,
            rotary_pos_emb=rotary_pos_emb,
            rotary_pos_cos=rotary_pos_cos,
            rotary_pos_sin=rotary_pos_sin,
            packed_seq_params=None,
            sequence_len_offset=sequence_len_offset,
        )

        if self.probe_layer is not None:
            if self._captured_hidden is None:
                raise RuntimeError(
                    f"Forward hook on decoder.layers[{self.probe_layer}] never fired -- "
                    "the decoder.layers indexing/structure assumption is likely wrong. "
                    "Inspect model.decoder's actual submodule structure directly."
                )
            hidden_states = self._captured_hidden
            self._captured_hidden = None  # reset for the next forward call

        hidden_states_bsh = hidden_states.transpose(0, 1).contiguous()
        pooled = self._pool(hidden_states_bsh, pool_mask)
        head_dtype = next(self.classification_head.parameters()).dtype
        return self.classification_head(pooled.to(head_dtype))


@dataclass
class HyenaForSequenceClassificationAtLayerProvider(HyenaForSequenceClassificationProvider):
    """Provider for HyenaForSequenceClassificationAtLayer -- identical to the
    official provider, plus a probe_layer field threaded through to the
    model constructor.
    """

    probe_layer: Optional[int] = None

    def provide(self, pre_process=None, post_process=None, vp_stage=None) -> HyenaForSequenceClassificationAtLayer:
        from bionemo.evo2.models.evo2_provider import _configure_fa4_for_device
        from bionemo.evo2.models.megatron.hyena.hyena_layer_specs import get_hyena_stack_spec
        from megatron.bridge.utils.vocab_utils import calculate_padded_vocab_size
        from megatron.core import parallel_state

        _configure_fa4_for_device(self)
        self.bias_activation_fusion = False if self.remove_activation_post_first_layer else self.bias_activation_fusion
        assert self.vocab_size is not None, "vocab_size must be configured before calling provide()."

        padded_vocab_size = (
            calculate_padded_vocab_size(self.vocab_size, self.make_vocab_size_divisible_by, self.tensor_model_parallel_size)
            if self.should_pad_vocab
            else self.vocab_size
        )
        hyena_stack_spec = get_hyena_stack_spec(
            use_te=self.use_te,
            vortex_style_fp8=self.vortex_style_fp8,
            unfused_rmsnorm=self.unfused_rmsnorm,
            plain_row_linear=self.plain_row_linear,
        )
        return HyenaForSequenceClassificationAtLayer(
            probe_layer=self.probe_layer,
            num_classes=self.num_classes,
            classifier_hidden_size=self.classifier_hidden_size,
            classifier_dropout=self.classifier_dropout,
            pool=self.pool,
            transformer_config=self,
            hyena_stack_spec=hyena_stack_spec,
            vocab_size=padded_vocab_size,
            max_sequence_length=self.seq_length,
            num_groups_hyena=self.num_groups_hyena,
            num_groups_hyena_medium=self.num_groups_hyena_medium,
            num_groups_hyena_short=self.num_groups_hyena_short,
            hybrid_override_pattern=self.hybrid_override_pattern,
            position_embedding_type=self.position_embedding_type,
            rotary_percent=self.rotary_percent,
            rotary_base=self.rotary_base,
            seq_len_interpolation_factor=self.seq_len_interpolation_factor,
            pre_process=(False if self.pre_process is False else (pre_process if pre_process is not None else parallel_state.is_pipeline_first_stage())),
            post_process=(False if self.post_process is False else (post_process if post_process is not None else parallel_state.is_pipeline_last_stage())),
            share_embeddings_and_output_weights=self.share_embeddings_and_output_weights,
            hyena_init_method=self.hyena_init_method,
            hyena_output_layer_init_method=self.hyena_output_layer_init_method,
            remove_activation_post_first_layer=self.remove_activation_post_first_layer,
            add_attn_proj_bias=self.add_attn_proj_bias,
        )


@dataclass
class Hyena1bClassifierAtLayerProvider(Hyena1bModelProvider, HyenaForSequenceClassificationAtLayerProvider):
    """1B Evo2 backbone, classification head at a specific intermediate layer.

    Plain multiple inheritance, mirroring the official script's OWN pattern
    exactly (Hyena1bClassifierProvider(Hyena1bModelProvider,
    HyenaForSequenceClassificationProvider)) -- this is what correctly gives
    us Hyena1bModelProvider's size-specific defaults (hidden_size=1920,
    num_layers=25, etc.) combined with our probe_layer field, via normal
    dataclass MRO. No extra plumbing needed.
    """


def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    # Pull --probe-layer out before handing the rest to the official parser,
    # since _parse_args (from evo2_classifier.py) doesn't know this flag.
    probe_layer = None
    filtered_argv = []
    i = 0
    while i < len(argv):
        if argv[i] == "--probe-layer":
            probe_layer = int(argv[i + 1])
            i += 2
        elif argv[i].startswith("--probe-layer="):
            probe_layer = int(argv[i].split("=", 1)[1])
            i += 1
        else:
            filtered_argv.append(argv[i])
            i += 1

    args = _parse_args(filtered_argv)

    # Monkey-patch the provider lookup so evo2_1b_classifier_config builds
    # OUR probe-capable class instead of the official one -- avoids
    # duplicating that entire (large) config-building function.
    CLASSIFIER_PROVIDER_OPTIONS["evo2_1b_base"] = Hyena1bClassifierAtLayerProvider

    cfg = evo2_1b_classifier_config(
        base_ckpt_dir=args.base_ckpt_dir,
        train_jsonl=args.train_jsonl,
        val_jsonl=args.val_jsonl,
        test_jsonl=args.test_jsonl,
        num_classes=args.num_classes,
        result_dir=args.result_dir,
        experiment_name=args.experiment_name,
        model_size=args.model_size,
        tensor_model_parallel_size=args.tensor_model_parallel_size,
        seq_length_tokens=args.seq_length_tokens,
        backbone_seq_length=args.backbone_seq_length,
        train_iters=args.train_iters,
        global_batch_size=args.global_batch_size,
        micro_batch_size=args.micro_batch_size,
        lr=args.lr,
        min_lr=args.min_lr,
        warmup_iters=args.warmup_iters,
        decay_steps=args.decay_steps,
        weight_decay=args.weight_decay,
        eval_interval=args.eval_interval,
        eval_iters=args.eval_iters,
        save_interval=args.save_interval,
        log_interval=args.log_interval,
        seed=args.seed,
        classifier_hidden_size=args.classifier_hidden_size,
        classifier_dropout=args.classifier_dropout,
        pool=args.pool,
        use_lora=args.lora_finetune,
        lora_dim=args.lora_dim,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        lora_target_modules=args.lora_target_modules,
        tokenizer_path=args.tokenizer_path,
        no_activation_checkpointing=not args.activation_checkpointing,
        precision_recipe=args.precision_recipe,
        log_throughput_to_tensorboard=args.log_throughput_to_tensorboard,
        throughput_window_size=args.throughput_window_size,
        wandb_project=args.wandb_project,
        wandb_entity=args.wandb_entity,
        wandb_run_name=args.wandb_run_name,
        wandb_save_dir=args.wandb_save_dir,
    )
    # Thread probe_layer onto the already-constructed model provider instance.
    cfg.model.probe_layer = probe_layer
    train_classifier(cfg)


if __name__ == "__main__":
    Hyena1bClassifierAtLayerProvider.__module__ = "evo2_classifier_probe"
    main(sys.argv[1:])
