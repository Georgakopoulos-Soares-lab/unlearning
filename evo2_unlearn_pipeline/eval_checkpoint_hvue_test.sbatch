#!/bin/bash
#SBATCH --job-name=evo2_ckpt_ppl_hvue
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=evo2_ckpt_ppl_hvue_%j.out
#SBATCH --error=evo2_ckpt_ppl_hvue_%j.err

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
# SET THIS to the checkpoint you want to evaluate -- either:
#  (a) the real checkpoints dir, if you've confirmed `--finetune-ckpt-dir`
#      correctly picks a SPECIFIC iteration (see `--help` check from chat), or
#  (b) a single-checkpoint "pointer" directory made via symlink (recommended,
#      unambiguous by construction) -- see chat for the exact command.
CHECKPOINT_DIR="/projects/MENTISLab/unlearning/results/evo2_graddiff/eval_pointer"
# ============================================================================

# Pure evaluation: --lr 0 --min-lr 0 guarantees exactly zero weight drift.
# This is the HELD-OUT HVUE forget-set test split (never trained on during
# either the original causal-LM work OR Gradient Difference unlearning) --
# measures whether the model actually forgot host-tropism-related sequences.
# eval-iters=4314 covers the FULL 276,048-sequence test set in one pass
# (ceil(276048/64)). NOTE: this is ~2x the originally-assumed 138,024 --
# the real preprocessed causal-LM test split includes each sequence's
# reverse-complement strand too (embed_reverse_complement: true in
# preprocess_config.yaml), which the classification JSONL conversion did
# not do. Verified via check_dataset_lengths.py, not assumed.
train_evo2 \
    --dataset-config /projects/MENTISLab/unlearning/evo2_causal_lm_finetune/training_data_config.yaml \
    --dataset-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm \
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
    --eval-iters 4314 \
    --lr 0 \
    --min-lr 0 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_graddiff_eval \
    --experiment-name hvue_forget_test_ppl
