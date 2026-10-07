"""LoRA fine-tuning for binary classification on top of a frozen(-ish) Evo2 backbone.

USAGE (single GPU, matches the H200 smoke-test setup):
    python train_classifier.py \
        --fasta-path /projects/MENTISLab/unlearning/data/evo2/benchmarks/hvue_gue_manifest.fasta \
        --finetune-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
        --result-dir /projects/MENTISLab/unlearning/results/evo2_classification_smoketest \
        --max-steps 20 --seq-length 1024 --micro-batch-size 4 --global-batch-size 4

IMPORTANT CAVEATS (read before a long run):
1. This reuses `bionemo.evo2.recipes.evo2._evo2_common`, a PRIVATE (underscore-prefixed)
   helper. It's not public API and could change between bionemo-framework versions
   without notice -- if this script breaks after a `git pull` on that repo, this
   function's signature is the first place to check.
2. We construct the base config with a placeholder `dataset_config_path`, then
   overwrite `cfg.dataset` afterward -- this works because Evo2DatasetProvider only
   reads that path lazily inside `build_datasets()`, which we replace entirely.
   `_evo2_common` never calls `build_datasets()` itself, so the placeholder is never
   actually touched.
3. `LabeledFastaDatasetProvider.build_datasets()` returns plain torch Datasets, not
   Megatron `GPTDataset`s. Whether Megatron-Bridge's dataloader-building machinery
   accepts this transparently is INFERRED from `DatasetProvider`'s own abstract
   docstring example (which does exactly this for an S3-backed dataset), not
   confirmed by reading that code path. Run the smoke test below before trusting
   a long run.
4. Loading a checkpoint for fine-tuning (not from-scratch pretraining) means the
   checkpoint's LOAD path needs to point at your converted mbridge checkpoint.
   This script wires that through `--finetune-ckpt-dir`, matching train_evo2's own
   `--finetune-ckpt-dir` flag semantics, but we haven't traced that exact loading
   code path here -- watch the first run's logs for confirmation it actually loads
   the checkpoint weights (vs. silently initializing from scratch).
"""

import argparse
from pathlib import Path

from megatron.bridge.training.pretrain import pretrain

from bionemo.evo2.models.evo2_lora import Evo2LoRA
from bionemo.evo2.recipes.evo2 import _evo2_common

from evo2_classification.dataset_provider import LabeledFastaDatasetProvider
from evo2_classification.forward_step import classification_forward_step
from evo2_classification.model import HyenaClassificationModelProvider


def build_config(args: argparse.Namespace):
    cfg = _evo2_common(
        model_provider=HyenaClassificationModelProvider,
        # Placeholder to satisfy _evo2_common's branch logic -- never actually read,
        # see caveat #2 above.
        dataset_config_path="__unused_placeholder__",
        train_iters=args.max_steps,
        global_batch_size=args.global_batch_size,
        micro_batch_size=args.micro_batch_size,
        seq_length=args.seq_length,
        lr=args.lr,
        min_lr=args.min_lr,
        lr_warmup_iters=args.warmup_steps,
        dir=args.result_dir,
        name="evo2_classification",
        lora_finetune=True,
        lora_alpha=args.lora_alpha,
        lora_dim=args.lora_dim,
        lora_dropout=args.lora_dropout,
    )

    # Overwrite the dataset with our own labeled-FASTA provider.
    cfg.dataset = LabeledFastaDatasetProvider(
        fasta_path=Path(args.fasta_path),
        seq_length=args.seq_length,
    )

    # _evo2_common hardcodes eval_interval=100, eval_iters=32 internally (not
    # exposed as parameters) -- override here. eval_iters is a SUBSET for
    # periodic monitoring during training, not a full pass over the val set
    # (138K samples would take as long as training itself at every check).
    cfg.train.eval_iters = args.eval_iters
    cfg.train.eval_interval = args.eval_interval
    cfg.train.save_interval = args.eval_interval

    # Point checkpoint loading at the converted mbridge checkpoint for fine-tuning.
    # IMPORTANT: do NOT also set cfg.checkpoint.load here -- that field is for
    # resuming THIS experiment's own (initially empty) run directory, which
    # _evo2_common already set correctly. Setting it to the base checkpoint
    # directory caused Megatron-Bridge to try loading the base (dense, no-LoRA)
    # checkpoint into the LoRA-wrapped model's state dict after PEFT wrapping --
    # a real shape mismatch, not a benign one, as seen in the previous run's
    # apply_factory_merges ValueError.
    cfg.checkpoint.pretrained_checkpoint = args.finetune_ckpt_dir
    cfg.checkpoint.finetune = True
    # The Savanna->mbridge conversion appears to never populate TE's per-layer
    # "_extra_state" metadata placeholders (Savanna's own format has no such
    # concept), so a strict checkpoint load fails on missing keys that are
    # benign -- they're FP8/TE bookkeeping, not actual model weights. Tolerate
    # this explicitly rather than silently working around it via exceptions.
    # Confirmed via direct inspection of the checkpoint's .metadata file: 0
    # "_extra_state" keys present, 254 real weight keys present.
    cfg.checkpoint.dist_ckpt_strictness = "ignore_all"

    # _evo2_common already builds `peft=Evo2LoRA(...)` internally when lora_finetune=True
    # via the same code path evo2.py's causal-LM recipes use, so cfg.peft should already
    # be set correctly here -- but double-check after this script errors or succeeds:
    #   print(type(cfg.peft), cfg.peft)
    # should show Evo2LoRA with your requested target_modules.

    return cfg


def main():
    parser = argparse.ArgumentParser(description="LoRA classification fine-tuning for Evo2.")
    parser.add_argument("--fasta-path", type=str, required=True)
    parser.add_argument("--finetune-ckpt-dir", type=str, required=True)
    parser.add_argument("--result-dir", type=str, required=True)
    parser.add_argument("--max-steps", type=int, default=30000, help="~2 epochs at global_batch_size=64 over 640,016 train sequences")
    parser.add_argument("--seq-length", type=int, default=1024)
    parser.add_argument("--micro-batch-size", type=int, default=16)
    parser.add_argument("--global-batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--min-lr", type=float, default=3e-6)
    parser.add_argument("--warmup-steps", type=int, default=500)
    parser.add_argument("--eval-iters", type=int, default=50, help="Periodic monitoring subset, NOT a full pass over the 138K-sample val set (that would take as long as training)")
    parser.add_argument("--eval-interval", type=int, default=1000, help="Also used as checkpoint save-interval -> ~20 checkpoints over a 20,000-step run")
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dim", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.1)
    args = parser.parse_args()

    cfg = build_config(args)
    pretrain(cfg, classification_forward_step)


if __name__ == "__main__":
    main()
