#!/bin/bash
#SBATCH --job-name=evo2_probe_sweep
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=evo2_probe_sweep_base_emp_h3_%A_layer%a.out
#SBATCH --error=evo2_probe_sweep_base_emp_h3_%A_layer%a.err
#SBATCH --array=18

# ============================================================================
# COST NOTE: each array element is a FULL separate training run. The
# --array spec above picks every-4th layer (0,4,8,...,24 = 7 jobs) as a
# representative sweep, NOT all 25 layers -- running all 25 at this same
# per-layer step count would be ~3.6x the GPU-hours. Adjust --array above
# if you want finer/coarser coverage (e.g. --array=0-24 for every layer,
# --array=0,6,12,18,24 for a sparser 5-point sweep).
#
# SIZING NOTE: train-iters below (3000) is LOWER than the full 20000-step
# head-only baseline, deliberately -- this sweep is meant to find
# RELATIVE differences in per-layer signal strength, not a final, fully-
# converged number for any one layer. If a layer looks interesting, re-run
# it alone at the full 20000-step budget for a trustworthy final number.
# We are using the 512 vocabulary size for the tokenizer here as we are not specifying anything.
# ============================================================================

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

echo "Probing layer: ${SLURM_ARRAY_TASK_ID}"

# Multiple array tasks can land on the SAME physical node simultaneously.
# torchrun defaults to a FIXED rendezvous port (29500) with no automatic
# differentiation between independent invocations -- confirmed to collide
# (EADDRINUSE) when that happens. Derive a unique port per array task.
MASTER_PORT=$((29500 + SLURM_ARRAY_TASK_ID))

torchrun --nproc-per-node 1 /projects/MENTISLab/unlearning/evo2_classifier_official/evo2_classifier_probe.py \
    --train-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/train.jsonl \
    --val-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/dev.jsonl \
    --test-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/test.jsonl \
    --base-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_probe_sweep_emp_h3 \
    --experiment-name "layer${SLURM_ARRAY_TASK_ID}" \
    --num-classes 2 \
    --model-size evo2_1b_base \
    --seq-length-tokens 1000 \
    --probe-layer "${SLURM_ARRAY_TASK_ID}" \
    --train-iters 750 \
    --global-batch-size 64 \
    --micro-batch-size 16 \
    --warmup-iters 50 \
    --eval-interval 50 \
    --eval-iters 50 \
    --save-interval 50 \
    --lr 3e-5 \
    --min-lr 3e-6
