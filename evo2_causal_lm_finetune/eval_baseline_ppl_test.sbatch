#!/bin/bash
#SBATCH --job-name=evo2_baseline_ppl
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=evo2_baseline_ppl_%j.out
#SBATCH --error=evo2_baseline_ppl_%j.err

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

# Pure baseline evaluation: --lr 0 --min-lr 0 guarantees exactly zero weight
# drift (a zero-learning-rate optimizer step is a no-op), so this measures
# the ORIGINAL unmodified checkpoint's causal-LM loss/perplexity, not a
# fine-tuned version. --eval-iters sized to cover the FULL 138,024-sequence
# test set in one pass (2157 = ceil(138024/64)), not a sampled subset.
train_evo2 \
    --dataset-config /projects/MENTISLab/unlearning/evo2_causal_lm_finetune/training_data_config.yaml \
    --dataset-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm \
    --finetune-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --model-size evo2_1b_base \
    --seq-length 1024 \
    --hf-tokenizer-model-path tokenizers/nucleotide_fast_tokenizer_256 \
    --micro-batch-size 16 \
    --global-batch-size 64 \
    --max-steps 1 \
    --warmup-steps 0 \
    --constant-steps 0 \
    --eval-interval 1 \
    --eval-iters 2157 \
    --lr 0 \
    --min-lr 0 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_baseline_eval \
    --experiment-name baseline_ppl_test
