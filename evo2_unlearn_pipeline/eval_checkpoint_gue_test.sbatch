#!/bin/bash
#SBATCH --job-name=evo2_ckpt_ppl_gue
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=evo2_ckpt_ppl_gue_%j.out
#SBATCH --error=evo2_ckpt_ppl_gue_%j.err

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

# ============================================================================
# SET THIS to the SAME checkpoint used in eval_checkpoint_hvue_test.sbatch,
# so the two numbers (forget-test PPL, retain-test PPL) describe the same
# model state. See chat for the symlink-pointer method if --finetune-ckpt-dir
# doesn't support selecting a specific iteration directly.
CHECKPOINT_DIR="/projects/MENTISLab/unlearning/results/evo2_graddiff/eval_pointer"
# ============================================================================

# Pure evaluation: --lr 0 --min-lr 0 guarantees exactly zero weight drift.
# This is the GUE retain-set test split -- measures whether general genomic
# capability was PRESERVED (not just how much HVUE was forgotten).
# eval-iters=2625 covers the FULL 167,976-sequence test set in one pass
# (ceil(167976/64)), verified via check_dataset_lengths.py.
train_evo2 \
    --dataset-config /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/training_data_config_gue.yaml \
    --dataset-dir /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/fasta_splits/preprocessed_causal_lm \
    --finetune-ckpt-dir "$CHECKPOINT_DIR" \
    --model-size evo2_1b_base \
    --seq-length 1024 \
    --hf-tokenizer-model-path /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron/tokenizers/nucleotide_fast_tokenizer_256 \
    --micro-batch-size 16 \
    --global-batch-size 64 \
    --max-steps 1 \
    --warmup-steps 0 \
    --constant-steps 0 \
    --eval-interval 1 \
    --eval-iters 2625 \
    --lr 0 \
    --min-lr 0 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_graddiff_eval \
    --experiment-name gue_retain_test_ppl
