#!/bin/bash
#SBATCH --job-name=evo2_auroc_eval
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=hvue_base_eval_%j.out
#SBATCH --error=hvue_base_eval_%j.err

set -euo pipefail

module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2

cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate

export CPATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/include:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/lib:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}

cd /projects/MENTISLab/unlearning/evo2_classifier_official/evaluations

torchrun --nproc-per-node 1 evaluate_auroc.py \
    --ckpt-dir /projects/MENTISLab/unlearning/results/evo2_official/base_hvue/pooled_last_layer/checkpoints \
    --jsonl /projects/MENTISLab/unlearning/data/evo2/HVUE_v2/test.jsonl \
    --micro-batch-size 64
