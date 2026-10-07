#!/bin/bash
#SBATCH --job-name=evo2_causal_smoketest
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=evo2_causal_smoketest_%j.out
#SBATCH --error=evo2_causal_smoketest_%j.err

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

# Small smoke test: does --dataset-config + --finetune-ckpt-dir +
# --lora-finetune work together correctly.
train_evo2 \
    --dataset-config /projects/MENTISLab/unlearning/evo2_causal_lm_finetune/training_data_config.yaml \
    --dataset-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm \
    --finetune-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --model-size evo2_1b_base \
    --seq-length 1024 \
    --hf-tokenizer-model-path tokenizers/nucleotide_fast_tokenizer_256 \
    --micro-batch-size 4 \
    --global-batch-size 4 \
    --max-steps 20 \
    --warmup-steps 2 \
    --constant-steps 2 \
    --eval-interval 10 \
    --eval-iters 3 \
    --lr 3e-5 \
    --min-lr 3e-6 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_causal_smoketest_${SLURM_JOB_ID} \
    --experiment-name smoketest \
    --lora-finetune \
    --lora-dim 16 \
    --lora-alpha 32 \
    --lora-dropout 0.1
