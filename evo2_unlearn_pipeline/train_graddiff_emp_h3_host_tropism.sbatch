#!/bin/bash
#SBATCH --job-name=graddiff_train
#SBATCH --partition=gpu
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=64
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
# = 727,892 docs; GUE retain-train = 1,448,334 docs).
#
# DELIBERATELY AGGRESSIVE SETTINGS (confirmed choice, not an oversight):
#   lr=3e-5 (vs the smoke-tested 1e-5) and alpha_forget=alpha_retain=1.0
#   (vs the divergence-resistant 1.0/5.0 ratio from the validated reference
#   implementation). Both independently increase divergence risk; combined,
#   more so. This trades safety for seeing a larger effect size faster.
#
# RESUMABLE: rerun this exact script unchanged to continue from the last
# checkpoint in --result-dir/--experiment-name/checkpoints.
#
# MONITOR CLOSELY: given the above, watch "retain loss"/"retain loss PPL" in
# EVERY eval log line as this runs -- divergence is more likely here than in
# the validated-settings configuration. A prior validated implementation of
# this exact algorithm saw retain PPL climb 4-9x even at the SAFER 1.0/5.0
# ratio; expect faster/larger divergence at 1.0/1.0. save_interval=500 gives
# 40 checkpoints total across the run (all kept, keep_last_n=-1) as rollback
# points if you need to stop and restart from an earlier, less-diverged state.
python /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/train_graddiff.py \
    --forget-dataset-config /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/forget_data_config.yaml \
    --forget-dataset-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_hvue_human_host_tropism \
    --retain-dataset-config /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/training_data_config_emp_h3.yaml \
    --retain-dataset-dir /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_h3_fasta_splits/preprocessed_emp_h3 \
    --base-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --hf-tokenizer-model-path /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron/tokenizers/nucleotide_fast_tokenizer_256 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_graddiff \
    --experiment-name emp_h3_human_host_tropism \
    --max-steps 2200 \
    --seq-length 1024 \
    --micro-batch-size 16 \
    --global-batch-size 64 \
    --warmup-steps 200 \
    --eval-interval 100 \
    --eval-iters 50 \
    --save-interval 10 \
    --keep-last-n-checkpoints 10 \
    --lr 1e-5 \
    --min-lr 1e-6 \
    --alpha-forget 1.0 \
    --alpha-retain 5.0 \
    --forget-loss-cap 0.0
