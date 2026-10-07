#!/bin/bash
#SBATCH --job-name=evo2_lora_ppl
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=evo2_lora_ppl_%j.out
#SBATCH --error=evo2_lora_ppl_%j.err

set -euo pipefail

module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2

cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate

export CPATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/include:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/lib:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}

python -c "import torch; assert torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0))"

# IMPORTANT: --result-dir/--experiment-name match the ORIGINAL train_lora.sbatch
# run exactly -- this makes cfg.checkpoint.load point at that run's own
# checkpoint directory, so the framework's normal RESUME logic (not
# --finetune-ckpt-dir) finds and loads the full saved state (base weights +
# trained LoRA adapters together). --finetune-ckpt-dir is still passed
# because train_evo2's CLI likely requires it when --lora-finetune is set,
# but it should be BYPASSED once an existing checkpoint is found in the
# resume path -- verify this in the log (see note below).
#
# max-steps = 20001 (one past the last saved checkpoint at iteration 20000)
# so the resume logic has something to do (a single lr=0 no-op step), then
# eval-interval=1 triggers evaluation immediately after.
train_evo2 \
    --dataset-config /projects/MENTISLab/unlearning/evo2_causal_lm_finetune/training_data_config.yaml \
    --dataset-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm \
    --finetune-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --model-size evo2_1b_base \
    --seq-length 1024 \
    --hf-tokenizer-model-path tokenizers/nucleotide_fast_tokenizer_256 \
    --micro-batch-size 16 \
    --global-batch-size 64 \
    --max-steps 20001 \
    --warmup-steps 500 \
    --constant-steps 500 \
    --eval-interval 1 \
    --eval-iters 2157 \
    --lr 0 \
    --min-lr 0 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_causal_lm \
    --experiment-name lora_continued_pretrain \
    --lora-finetune \
    --lora-dim 16 \
    --lora-alpha 32 \
    --lora-dropout 0.1
