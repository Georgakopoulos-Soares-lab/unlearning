"""Gradient Difference unlearning: full-parameter fine-tuning to forget HVUE
(host-tropism) knowledge while retaining general genomic understanding (GUE).

Reuses bionemo.evo2.recipes.evo2._evo2_common (same private-helper pattern we
used for our earlier classification work) to get a fully-valid ConfigContainer
(correct optimizer/scheduler/DDP/precision settings), then overrides
cfg.dataset with our GradDiffDualDatasetProvider and passes our own
graddiff_forward_step to pretrain() (train_evo2's own CLI hardcodes
hyena_forward_step, so a custom loss requires this standalone-script
approach, same as our classification pipeline).

IMPORTANT DESIGN NOTE: unlike our LoRA work, this is FULL-PARAMETER
fine-tuning (lora_finetune=False -> peft=None) -- GRIN's own benchmark
results showed LoRA "yields inconsistent results, often underperforming in
forgetting" compared to full fine-tuning, so genuine forgetting should not be
attempted via LoRA.
"""

import argparse
from pathlib import Path

from megatron.bridge.training.pretrain import pretrain

from bionemo.evo2.models.evo2_provider import Hyena1bModelProvider
from bionemo.evo2.recipes.evo2 import _evo2_common

from dual_dataset_provider import GradDiffDualDatasetProvider
from graddiff_forward_step import graddiff_forward_step


def build_config(args: argparse.Namespace):
    cfg = _evo2_common(
        model_provider=Hyena1bModelProvider,
        hf_tokenizer_model_or_path=args.hf_tokenizer_model_path,
        dataset_config_path="__unused_placeholder__",  # never read; cfg.dataset is overwritten below
        train_iters=args.max_steps,
        global_batch_size=args.global_batch_size,
        micro_batch_size=args.micro_batch_size,
        seq_length=args.seq_length,
        lr=args.lr,
        min_lr=args.min_lr,
        lr_warmup_iters=args.warmup_steps,
        dir=args.result_dir,
        name=args.experiment_name,
        lora_finetune=False,  # full-parameter training -- see module docstring
    )

    cfg.dataset = GradDiffDualDatasetProvider(
        forget_dataset_config_path=args.forget_dataset_config,
        forget_dataset_dir=args.forget_dataset_dir,
        retain_dataset_config_path=args.retain_dataset_config,
        retain_dataset_dir=args.retain_dataset_dir,
        seq_length=args.seq_length,
    )

    cfg.checkpoint.pretrained_checkpoint = args.base_ckpt_dir
    cfg.checkpoint.finetune = True
    cfg.checkpoint.dist_ckpt_strictness = "ignore_all"  # same Savanna-conversion _extra_state gap as before

    cfg.train.eval_iters = args.eval_iters
    cfg.train.eval_interval = args.eval_interval
    cfg.train.save_interval = args.save_interval
    # Full-parameter checkpoints (all ~1B params + full Adam optimizer state)
    # are much larger than our prior LoRA adapter-only checkpoints. Frequent
    # saving over a long run can consume a LOT of disk -- bound retention
    # explicitly rather than keeping every single save forever (Megatron's
    # default most_recent_k=-1 means "keep all", which is almost certainly
    # not what you want at save_interval=100 over 20,000 steps).
    cfg.checkpoint.most_recent_k = args.keep_last_n_checkpoints

    # Custom fields the forward step reads via getattr(state.cfg, ...).
    # Defaults (alpha_forget=1.0, alpha_retain=5.0) match a prior,
    # independently-validated Gradient Difference implementation for Evo-1 --
    # see graddiff_forward_step.py's module docstring for the divergence
    # warning this ratio is meant to guard against.
    cfg.graddiff_alpha_forget = args.alpha_forget
    cfg.graddiff_alpha_retain = args.alpha_retain
    cfg.graddiff_forget_loss_cap = args.forget_loss_cap

    # Disable CUDA graphs -- they assume one forward() call per step; we call
    # the model TWICE (forget + retain). Unverified whether this would
    # actually break with CUDA graphs on, but safer to disable explicitly
    # than find out the hard way.
    cfg.model.cuda_graph_modules = []
    cfg.model.enable_cuda_graph = False

    return cfg


def main():
    parser = argparse.ArgumentParser(description="Gradient Difference unlearning for Evo2.")
    parser.add_argument("--forget-dataset-config", type=str, required=True, help="Path to HVUE's training_data_config.yaml")
    parser.add_argument("--forget-dataset-dir", type=str, required=True, help="Path to HVUE's preprocessed_causal_lm dir")
    parser.add_argument("--retain-dataset-config", type=str, required=True, help="Path to GUE's training_data_config.yaml")
    parser.add_argument("--retain-dataset-dir", type=str, required=True, help="Path to GUE's preprocessed dir")
    parser.add_argument("--base-ckpt-dir", type=str, required=True)
    parser.add_argument(
        "--hf-tokenizer-model-path",
        type=str,
        default="/projects/MENTISLab/bionemo-framework/recipes/evo2_megatron/tokenizers/nucleotide_fast_tokenizer_256",
        help="MUST match the tokenizer the base checkpoint was converted/trained with. "
        "_evo2_common defaults to 'EleutherAI/gpt-neox-20b' (WRONG, ~50K-vocab English "
        "tokenizer) if this isn't passed explicitly -- this was the root cause of an "
        "earlier worse-than-random-loss bug.",
    )
    parser.add_argument("--result-dir", type=str, required=True)
    parser.add_argument("--experiment-name", type=str, required=True)
    parser.add_argument("--max-steps", type=int, default=1000)
    parser.add_argument("--seq-length", type=int, default=1024)
    parser.add_argument("--micro-batch-size", type=int, default=4)
    parser.add_argument("--global-batch-size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--min-lr", type=float, default=1e-6)
    parser.add_argument("--warmup-steps", type=int, default=10)
    parser.add_argument("--eval-iters", type=int, default=20)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--save-interval", type=int, default=100, help="Steps between checkpoint saves (independent of --eval-interval)")
    parser.add_argument(
        "--keep-last-n-checkpoints",
        type=int,
        default=5,
        help=(
            "Bound disk usage: only keep the N most recent checkpoints (Megatron's "
            "default of -1 keeps ALL of them, which is dangerous for full-parameter "
            "checkpoints saved frequently over a long run). -1 to disable and keep all."
        ),
    )
    parser.add_argument("--alpha-forget", type=float, default=1.0, help="Weight on the (negated/ascended) forget-loss term")
    parser.add_argument("--alpha-retain", type=float, default=5.0, help="Weight on the retain-loss term. A prior validated Evo-1 GD implementation defaults to 5.0 (not 1.0) specifically to resist divergence -- see module docstring in graddiff_forward_step.py")
    parser.add_argument(
        "--forget-loss-cap",
        type=float,
        default=0.0,
        help=(
            "Optional upper bound on the forget cross-entropy before weighting/negation. "
            "0.0 (default) disables clamping. The -alpha_forget*L_forget term is "
            "unbounded below, so this is a safety valve against divergence if the "
            "default alpha_forget/alpha_retain ratio isn't enough."
        ),
    )
    args = parser.parse_args()

    cfg = build_config(args)
    pretrain(cfg, graddiff_forward_step)


if __name__ == "__main__":
    main()
