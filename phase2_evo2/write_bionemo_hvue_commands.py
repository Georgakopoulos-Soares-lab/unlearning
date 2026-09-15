"""Write BioNeMo Evo2 HVUE head-only and LoRA launch scripts.

This file intentionally stays local to ``phase2_evo2`` and writes generated
scripts under ``data/evo2``.  It assumes the NVIDIA BioNeMo recipe environment
provides ``evo2_classifier.py`` and the Evo2 conversion utilities described in
the BioNeMo Evo2 LoRA tutorial.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path


DEFAULT_DATA_DIR = "data/evo2/bionemo_hvue"
DEFAULT_RUN_DIR = "data/evo2/bionemo_runs/hvue_host_tropism"
DEFAULT_CKPT_DIR = "data/evo2/bionemo_ckpts/evo2_1b_bf16_mbridge"


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def common_prefix(args: argparse.Namespace) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

cd {shell_quote(str(Path.cwd()))}

CLASSIFIER=${{BIONEMO_EVO2_CLASSIFIER:-{shell_quote(args.classifier)}}}
if [[ ! -f "$CLASSIFIER" ]]; then
  echo "Missing evo2_classifier.py at $CLASSIFIER" >&2
  echo "Set BIONEMO_EVO2_CLASSIFIER=/path/to/evo2_classifier.py from the BioNeMo Evo2 LoRA tutorial." >&2
  exit 2
fi

"""


def train_script(args: argparse.Namespace, *, lora: bool) -> str:
    exp_name = args.lora_experiment if lora else args.head_experiment
    lr = args.lora_lr if lora else args.head_lr
    min_lr = args.lora_min_lr if lora else args.head_min_lr
    train_iters = args.lora_train_iters if lora else args.head_train_iters
    warmup = args.lora_warmup_iters if lora else args.head_warmup_iters
    global_batch = args.lora_global_batch_size if lora else args.head_global_batch_size
    micro_batch = args.lora_micro_batch_size if lora else args.head_micro_batch_size
    lora_flags = ""
    if lora:
        lora_flags = (
            f" \\\n  --lora-finetune"
            f" --lora-dim {args.lora_dim}"
            f" --lora-alpha {args.lora_alpha}"
            f" --lora-dropout {args.lora_dropout}"
        )
    return (
        common_prefix(args)
        + f"""torchrun --nproc_per_node={args.num_gpus} "$CLASSIFIER" \\
  --train-jsonl {shell_quote(str(Path(args.data_dir) / f"{args.prefix}_train.jsonl"))} \\
  --val-jsonl {shell_quote(str(Path(args.data_dir) / f"{args.prefix}_val.jsonl"))} \\
  --test-jsonl {shell_quote(str(Path(args.data_dir) / f"{args.prefix}_test.jsonl"))} \\
  --base-ckpt-dir {shell_quote(args.base_ckpt_dir)} \\
  --result-dir {shell_quote(args.run_dir)} \\
  --experiment-name {shell_quote(exp_name)} \\
  --num-classes {args.num_classes} \\
  --seq-length-tokens {args.seq_length_tokens} \\
  --train-iters {train_iters} \\
  --global-batch-size {global_batch} \\
  --micro-batch-size {micro_batch} \\
  --lr {lr} \\
  --min-lr {min_lr} \\
  --warmup-iters {warmup} \\
  --eval-interval {args.eval_interval} \\
  --eval-iters {args.eval_iters} \\
  --save-interval {args.save_interval}{lora_flags}
"""
    )


def convert_script(args: argparse.Namespace) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

cd {shell_quote(str(Path.cwd()))}

python - <<'PY'
from pathlib import Path
from bionemo.common.data.load import load
from bionemo.common.utils.subprocess_utils import run_subprocess_safely
from bionemo.evo2.data.dataset_tokenizer import DEFAULT_HF_TOKENIZER_MODEL_PATH_512

mbridge = Path({args.base_ckpt_dir!r})
if mbridge.exists():
    print(f"MBridge checkpoint already exists: {{mbridge}}")
else:
    nemo2 = load({args.nemo_checkpoint!r})
    cmd = f'''evo2_convert_nemo2_to_mbridge \\
      --nemo2-ckpt-dir {{nemo2}} \\
      --mbridge-ckpt-dir {{mbridge}} \\
      --model-size {args.model_size} \\
      --mixed-precision-recipe {args.mixed_precision_recipe} \\
      --seq-length {args.convert_seq_length} \\
      --tokenizer-path {{DEFAULT_HF_TOKENIZER_MODEL_PATH_512}}'''
    print(cmd)
    result = run_subprocess_safely(cmd)
    if result["returncode"] != 0:
        raise SystemExit(result)
print(f"MBridge checkpoint: {{mbridge.absolute()}}")
PY
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--run-dir", default=DEFAULT_RUN_DIR)
    parser.add_argument("--script-dir", default="data/evo2/bionemo_hvue/scripts")
    parser.add_argument("--base-ckpt-dir", default=DEFAULT_CKPT_DIR)
    parser.add_argument("--classifier", default="phase2_evo2/bionemo/evo2_classifier.py")
    parser.add_argument("--prefix", default="host_tropism")
    parser.add_argument("--num-classes", type=int, default=2)
    parser.add_argument("--seq-length-tokens", type=int, default=512)
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--eval-interval", type=int, default=100)
    parser.add_argument("--eval-iters", type=int, default=10)
    parser.add_argument("--save-interval", type=int, default=100)

    parser.add_argument("--head-experiment", default="head_only")
    parser.add_argument("--head-train-iters", type=int, default=1000)
    parser.add_argument("--head-global-batch-size", type=int, default=32)
    parser.add_argument("--head-micro-batch-size", type=int, default=32)
    parser.add_argument("--head-lr", default="1e-3")
    parser.add_argument("--head-min-lr", default="1e-4")
    parser.add_argument("--head-warmup-iters", type=int, default=30)

    parser.add_argument("--lora-experiment", default="lora")
    parser.add_argument("--lora-train-iters", type=int, default=1000)
    parser.add_argument("--lora-global-batch-size", type=int, default=8)
    parser.add_argument("--lora-micro-batch-size", type=int, default=4)
    parser.add_argument("--lora-lr", default="5e-4")
    parser.add_argument("--lora-min-lr", default="5e-5")
    parser.add_argument("--lora-warmup-iters", type=int, default=30)
    parser.add_argument("--lora-dim", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.1)

    parser.add_argument("--nemo-checkpoint", default="evo2/1b-8k-bf16:1.0")
    parser.add_argument("--model-size", default="evo2_1b_base")
    parser.add_argument("--mixed-precision-recipe", default="bf16_mixed")
    parser.add_argument("--convert-seq-length", type=int, default=8192)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    script_dir = Path(args.script_dir)
    write_executable(script_dir / "00_convert_evo2_1b_to_mbridge.sh", convert_script(args))
    write_executable(script_dir / "10_train_head_only.sh", train_script(args, lora=False))
    write_executable(script_dir / "20_train_lora.sh", train_script(args, lora=True))

    manifest = {
        "data_dir": args.data_dir,
        "run_dir": args.run_dir,
        "base_ckpt_dir": args.base_ckpt_dir,
        "classifier": args.classifier,
        "scripts": {
            "convert": str(script_dir / "00_convert_evo2_1b_to_mbridge.sh"),
            "head_only": str(script_dir / "10_train_head_only.sh"),
            "lora": str(script_dir / "20_train_lora.sh"),
        },
        "notes": [
            "Run these scripts inside the NVIDIA BioNeMo Evo2 recipe environment.",
            "Set BIONEMO_EVO2_CLASSIFIER if evo2_classifier.py lives outside this repo.",
        ],
    }
    manifest_path = script_dir / "bionemo_hvue_command_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    for name, path in manifest["scripts"].items():
        print(f"[bionemo-hvue] {name}: {path}")
    print(f"[bionemo-hvue] manifest: {manifest_path}")


if __name__ == "__main__":
    main()
