#!/bin/bash
#SBATCH --job-name=evo2_cls_smoketest
#SBATCH --partition=gpu
#SBATCH --gres=gpu:h200:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --output=evo2_cls_smoketest_%j.out
#SBATCH --error=evo2_cls_smoketest_%j.err

set -euo pipefail

module load cuda/12.8.0
module load git/2.52.0
source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
conda activate bionemo_evo2

cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
source .venv/bin/activate

export CPATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/include:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/include:${CPATH:-}
export LD_LIBRARY_PATH=/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/nccl/lib:/home/sayyed.a/.conda/envs/bionemo_evo2/lib/python3.12/site-packages/nvidia/cudnn/lib:${LD_LIBRARY_PATH:-}

# So `evo2_classification` package is importable -- adjust if you place the folder elsewhere.
export PYTHONPATH=/projects/MENTISLab/unlearning:${PYTHONPATH:-}

python -c "import torch; assert torch.cuda.is_available(); print('GPU:', torch.cuda.get_device_name(0))"

# Small smoke test: few steps, small batch, to validate the whole pipeline
# (dataset loading, model forward, LoRA application, loss, checkpoint save)
# before committing to a real run.
python /projects/MENTISLab/unlearning/evo2_classification/train_classifier.py \
    --fasta-path /projects/MENTISLab/unlearning/data/evo2/benchmarks/hvue_gue_manifest.fasta \
    --finetune-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
    --result-dir /projects/MENTISLab/unlearning/results/evo2_cls_smoketest_${SLURM_JOB_ID} \
    --max-steps 20 \
    --seq-length 1024 \
    --micro-batch-size 4 \
    --global-batch-size 4 \
    --warmup-steps 5
