#!/bin/bash
#SBATCH --job-name=graddiff_train
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --output=graddiff_train_%j.out
#SBATCH --error=graddiff_train_%j.err

set -euo pipefail

module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2

cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate

export CPATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/include:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/lib:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}
export PYTHONPATH=/projects/MENTISLab/unlearning/evo2_unlearn_pipeline:${PYTHONPATH:-}

python -c "import torch; assert torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0))"

# Sizing: max_steps=20000 @ global_batch_size=64 -> ~1.76 forget (HVUE)
# epochs, ~0.88 retain (GUE) epochs (measured corpus sizes: HVUE forget-train
# = 727,892 docs; GUE retain-train = 1,448,334 docs). More forgetting
# pressure, solid-but-not-full retain coverage -- intentional, not accidental.
#
# RESUMABLE: rerun this exact script unchanged to continue from the last
# checkpoint in --result-dir/--experiment-name/checkpoints.
#
# MONITOR: watch "retain loss"/"retain loss PPL" in the eval log lines as
# this runs. The Gradient Difference objective is unbounded-below on the
# forget term and CAN diverge (a validated prior implementation saw retain
# PPL climb 4-9x in its own archived runs) -- if retain PPL starts climbing
# sharply, kill the job and use an EARLIER saved checkpoint (every 1000
# steps) rather than the final one, or restart with --forget-loss-cap set
# to a positive value as a safety valve.
python /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/train_graddiff.py \
    --forget-dataset-config /projects/MENTISLab/unlearning/evo2_causal_lm_finetune/training_data_config.yaml \
    --forget-dataset-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm \
    --retain-dataset-config /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/training_data_config_gue.yaml \
    --retain-dataset-dir /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/fasta_splits/preprocessed_causal_lm \
    --base-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --hf-tokenizer-model-path /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron/tokenizers/nucleotide_fast_tokenizer_256 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_graddiff \
    --experiment-name full_run \
    --max-steps 20000 \
    --seq-length 1024 \
    --micro-batch-size 16 \
    --global-batch-size 64 \
    --warmup-steps 500 \
    --eval-interval 1000 \
    --eval-iters 50 \
    --lr 1e-5 \
    --min-lr 1e-6 \
    --alpha-forget 1.0 \
    --alpha-retain 5.0 \
    --forget-loss-cap 0.0
