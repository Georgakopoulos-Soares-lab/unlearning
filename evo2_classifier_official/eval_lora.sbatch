#!/bin/bash
#SBATCH --job-name=evo2_auroc_eval_lora
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=evo2_auroc_eval_lora_emp_H3_%j.out
#SBATCH --error=evo2_auroc_eval_lora_emp_H3_%j.err

set -euo pipefail

module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2

cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate

export CPATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/include:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/lib:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}

cd /projects/MENTISLab/unlearning/evo2_classifier_official

torchrun --nproc-per-node 1 evaluate_auroc.py \
    --ckpt-dir /projects/MENTISLab/unlearning/results/evo2_official_gue/emp_H3/lora/checkpoints \
    --jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/test.jsonl \
    --micro-batch-size 64
