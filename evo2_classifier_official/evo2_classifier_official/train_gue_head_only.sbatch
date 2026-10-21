#!/bin/bash
#SBATCH --job-name=evo2_official_headonly
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=evo2_official_gue_emp_H3_headonly_maxent%j.out
#SBATCH --error=evo2_official_gue_emp_H3_headonly_maxent%j.err

#set -euo pipefail

module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2

cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate

export CPATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/include:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/lib:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}

python -c "import torch; assert torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0))"

# HEAD-ONLY BASELINE: backbone frozen, only the classification head trains.
# This is the "does Evo2 have inherent capability" probe -- no --lora-finetune
# flag, so PEFT freezes everything except classification_head.
# RESUMABLE: rerun this exact script unchanged to continue from the last
# checkpoint in --result-dir/--experiment-name/checkpoints.
torchrun --nproc-per-node 1 /projects/MENTISLab/unlearning/evo2_classifier_official/evo2_classifier.py \
    --train-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/train.jsonl \
    --val-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/dev.jsonl \
    --test-jsonl /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_H3/test.jsonl \
    --base-ckpt-dir /projects/MENTISLab/unlearning/results/evo2_maxent/emp_h3_human_host_tropism/checkpoints \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_official_gue/emp_H3/maxent \
    --experiment-name head_only \
    --num-classes 2 \
    --model-size evo2_1b_base \
    --seq-length-tokens 500 \
    --train-iters 200 \
    --global-batch-size 64 \
    --micro-batch-size 16 \
    --warmup-iters 20 \
    --eval-interval 10 \
    --eval-iters 12 \
    --save-interval 100 \
    --lr 3e-4 \
    --min-lr 3e-5
