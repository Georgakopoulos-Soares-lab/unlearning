#!/bin/bash
#SBATCH --job-name=graddiff_smoketest
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=graddiff_smoketest_%j.out
#SBATCH --error=graddiff_smoketest_%j.err

set -euo pipefail

module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2

cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate

export CPATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/include:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/lib:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}
export PYTHONPATH=/projects/MENTISLab/unlearning/evo2_unlearning:${PYTHONPATH:-}

python -c "import torch; assert torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0))"

# TODO: update --retain-dataset-config / --retain-dataset-dir once GUE
# preprocessing is complete (see training_data_config_gue_TEMPLATE.yaml).
# This smoke test CANNOT run until that's filled in with real GUE paths.
python /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/train_graddiff.py \
    --forget-dataset-config /projects/MENTISLab/unlearning/evo2_causal_lm_finetune/training_data_config.yaml \
    --forget-dataset-dir /projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm \
    --retain-dataset-config /projects/MENTISLab/unlearning/evo2_unlearn_pipeline/training_data_config_gue.yaml \
    --retain-dataset-dir /projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/preprocessed \
    --base-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --hf-tokenizer-model-path /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron/tokenizers/nucleotide_fast_tokenizer_256 \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_graddiff \
    --experiment-name smoketest \
    --max-steps 20 \
    --seq-length 1024 \
    --micro-batch-size 4 \
    --global-batch-size 4 \
    --warmup-steps 2 \
    --eval-interval 10 \
    --eval-iters 3 \
    --lr 1e-5 \
    --min-lr 1e-6 \
    --alpha-forget 1.0 \
    --alpha-retain 5.0 \
    --forget-loss-cap 0.0
