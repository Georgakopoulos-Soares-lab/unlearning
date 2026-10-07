#!/bin/bash
#SBATCH --job-name=evo2_official_smoketest
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=evo2_official_smoketest_%j.out
#SBATCH --error=evo2_official_smoketest_%j.err

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

# Small smoke test (head-only baseline, since --lora-finetune is omitted) --
# validates the OFFICIAL script actually integrates correctly in our
# pip-only environment before trusting it for a real run.
torchrun --nproc-per-node 1 /projects/MENTISLab/unlearning/evo2_classifier_official/evo2_classifier.py \
    --train-jsonl /projects/MENTISLab/unlearning/data/evo2/benchmarks/jsonl/train_smoke.jsonl \
    --val-jsonl /projects/MENTISLab/unlearning/data/evo2/benchmarks/jsonl/val_smoke.jsonl \
    --test-jsonl /projects/MENTISLab/unlearning/data/evo2/benchmarks/jsonl/test_smoke.jsonl \
    --base-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_official_smoketest_${SLURM_JOB_ID} \
    --experiment-name smoketest \
    --num-classes 2 \
    --model-size evo2_1b_base \
    --seq-length-tokens 1024 \
    --train-iters 20 \
    --global-batch-size 4 \
    --micro-batch-size 4 \
    --warmup-iters 2 \
    --eval-interval 10 \
    --eval-iters 3 \
    --lr 3e-5 \
    --min-lr 3e-6	
