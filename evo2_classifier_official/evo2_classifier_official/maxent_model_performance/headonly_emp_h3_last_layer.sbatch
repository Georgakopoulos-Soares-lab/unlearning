#!/bin/bash
#SBATCH --job-name=evo2_official_headonly_base_emp_h3
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=64G
#SBATCH --time=03:00:00
#SBATCH --output=headonly_maxent_emp_h3_%j.out
#SBATCH --error=headonly_maxent_emp_h3_%j.err

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

# BASELINE for the emp_H3 head-only comparison: IDENTICAL hyperparameters to
# the MaxEnt-unlearned-checkpoint run (train-iters=750, warmup-iters=50,
# eval-interval=100, eval-iters=50, save-interval=50, lr=3e-4, min-lr=3e-5,
# seq-length-tokens=1000 -- all extracted directly from that run's own
# config dump), with ONLY --base-ckpt-dir changed to the ORIGINAL,
# non-unlearned checkpoint. This is the "before" number the MaxEnt run's
# "after" number needs to be compared against.
torchrun --nproc-per-node 1 /projects/MENTISLab/unlearning/evo2_classifier_official/evo2_classifier.py \
    --train-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/train.jsonl \
    --val-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/dev.jsonl \
    --test-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/test.jsonl \
    --base-ckpt-dir /projects/MENTISLab/unlearning/results/evo2_maxent/emp_h3_human_host_tropism/checkpoints \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_official/maxent_emp_h3 \
    --experiment-name pooled_last_layer \
    --num-classes 2 \
    --model-size evo2_1b_base \
    --seq-length-tokens 1000 \
    --tokenizer-path /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron/tokenizers/nucleotide_fast_tokenizer_512
    --train-iters 750 \
    --global-batch-size 64 \
    --micro-batch-size 16 \
    --warmup-iters 100 \
    --eval-interval 100 \
    --eval-iters 50 \
    --save-interval 50 \
    --lr 3e-4 \
    --min-lr 3e-5
