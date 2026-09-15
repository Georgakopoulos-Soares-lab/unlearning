#!/usr/bin/env bash
# Evo-2 Phase 2 orchestration: build splits, run unlearning, evaluate.

set -euo pipefail

PHASE2_PYTHON=${PHASE2_PYTHON:-${PROJECT_PYTHON:-python}}
CKPT_ROOT=${CKPT_ROOT:-data/phase2_evo2/checkpoints}
STEPS=${STEPS:-1000}
LR=${LR:-1e-5}
BATCH=${BATCH:-1}
MAX_LEN=${MAX_LEN:-512}
SAVE_STEPS=${SAVE_STEPS:-}
TARGET_MANIFEST=${TARGET_MANIFEST:-data/evo2/family_targets/coronaviridae/manifest.csv}
EXTRA_FORGET_MANIFEST=${EXTRA_FORGET_MANIFEST:-}
LOCALIZED_LAYERS_PATH=${LOCALIZED_LAYERS_PATH:-data/evo2/family_targets/coronaviridae/localized_layers.json}
INTERNAL_TARGET_CONFIG=${INTERNAL_TARGET_CONFIG:-phase2_evo2/internal_eval_targets.json}
SPLIT_DIR=${SPLIT_DIR:-data/phase2_evo2/splits}
MODEL_NAME=${MODEL_NAME:-evo2_7b_base}
LOCAL_PATH=${LOCAL_PATH:-}
USE_KERNELS=${USE_KERNELS:-0}
DEVICE=${DEVICE:-cuda:0}
GD_ALPHA_FORGET=${GD_ALPHA_FORGET:-1.0}
GD_ALPHA_RETAIN=${GD_ALPHA_RETAIN:-5.0}
GD_FORGET_LOSS_CAP=${GD_FORGET_LOSS_CAP:-0.0}
RMU_CONDITIONS=${RMU_CONDITIONS:-localized full}
RMU_TARGET_DIRECTION=${RMU_TARGET_DIRECTION:-nonhuman}
RMU_DIRECTION_SEQS=${RMU_DIRECTION_SEQS:-500}
PROBE_REPR_INIT_RUN=${PROBE_REPR_INIT_RUN:-}

build_splits() {
    local extra_args=()
    if [ -n "$EXTRA_FORGET_MANIFEST" ]; then
        extra_args+=(--extra-forget-manifest "$EXTRA_FORGET_MANIFEST")
    else
        extra_args+=(--extra-forget-manifest "")
    fi
    "$PHASE2_PYTHON" -u phase2_evo2/build_unlearn_splits.py \
        --manifest "$TARGET_MANIFEST" \
        "${extra_args[@]}" \
        --out-dir "$SPLIT_DIR"
}

verify_retain() {
    "$PHASE2_PYTHON" -u phase2_evo2/verify_retain_set.py \
        --csv "$SPLIT_DIR/retain.csv" \
        --summary-json "$SPLIT_DIR/retain_audit.json"
}

run_gd() {
    for cond in localized probe random full; do
        echo "=== Evo2 GD $cond ==="
        "$PHASE2_PYTHON" -u phase2_evo2/unlearn_gd.py \
            --forget-csv "$SPLIT_DIR/forget.csv" \
            --retain-csv "$SPLIT_DIR/retain.csv" \
            --out-dir "$CKPT_ROOT" \
            --run-name "gd_$cond" \
            --condition "$cond" \
            --steps "$STEPS" --lr "$LR" \
            --alpha-forget "$GD_ALPHA_FORGET" --alpha-retain "$GD_ALPHA_RETAIN" \
            --forget-loss-cap "$GD_FORGET_LOSS_CAP" \
            --batch-size "$BATCH" --max-length "$MAX_LEN" \
            --save-steps "$SAVE_STEPS" \
            --localized-layers-path "$LOCALIZED_LAYERS_PATH" \
            --model-name "$MODEL_NAME" \
            --local-path "$LOCAL_PATH" \
            --use-kernels "$USE_KERNELS" \
            --device "$DEVICE"
    done
}

run_rmu() {
    for cond in $RMU_CONDITIONS; do
        echo "=== Evo2 RMU $cond ==="
        "$PHASE2_PYTHON" -u phase2_evo2/unlearn_rmu.py \
            --forget-csv "$SPLIT_DIR/forget.csv" \
            --retain-csv "$SPLIT_DIR/retain.csv" \
            --condition "$cond" \
            --target-direction "$RMU_TARGET_DIRECTION" \
            --direction-seqs "$RMU_DIRECTION_SEQS" \
            --steps "$STEPS" --lr "$LR" \
            --batch-size "$BATCH" --max-length "$MAX_LEN" \
            --save-steps "$SAVE_STEPS" \
            --localized-layers-path "$LOCALIZED_LAYERS_PATH" \
            --model-name "$MODEL_NAME" \
            --local-path "$LOCAL_PATH" \
            --use-kernels "$USE_KERNELS" \
            --device "$DEVICE"
    done
}

run_probe_repr() {
    for cond in localized probe random full; do
        echo "=== Evo2 probe-repr $cond ==="
        local init_args=()
        if [ -n "$PROBE_REPR_INIT_RUN" ]; then
            init_args=(--init-from-run "$PROBE_REPR_INIT_RUN")
        fi
        "$PHASE2_PYTHON" -u phase2_evo2/unlearn_probe_repr.py \
            --forget-csv "$SPLIT_DIR/forget.csv" \
            --retain-csv "$SPLIT_DIR/retain.csv" \
            --internal-target-config "$INTERNAL_TARGET_CONFIG" \
            --out-dir "$CKPT_ROOT" \
            --run-name "probe_repr_$cond" \
            "${init_args[@]}" \
            --condition "$cond" \
            --steps "$STEPS" --lr "$LR" \
            --batch-size "$BATCH" --max-length "$MAX_LEN" \
            --save-steps "$SAVE_STEPS" \
            --localized-layers-path "$LOCALIZED_LAYERS_PATH" \
            --model-name "$MODEL_NAME" \
            --local-path "$LOCAL_PATH" \
            --use-kernels "$USE_KERNELS" \
            --device "$DEVICE"
    done
}

run_eval() {
    for run in "$CKPT_ROOT"/*/; do
        ckpt="$run/weights.safetensors"
        if [ -f "$ckpt" ]; then
            echo "=== Evo2 eval $run ==="
            "$PHASE2_PYTHON" -u phase2_evo2/eval_unlearn.py \
                --ckpt "$ckpt" \
                --internal-target-config "$INTERNAL_TARGET_CONFIG" \
                --forget-csv "$SPLIT_DIR/forget.csv" \
                --retain-csv "$SPLIT_DIR/retain.csv" \
                --localized-layers-path "$LOCALIZED_LAYERS_PATH" \
                --model-name "$MODEL_NAME" \
                --local-path "$LOCAL_PATH" \
                --use-kernels "$USE_KERNELS" \
                --device "$DEVICE"
        fi
    done
}

case "${1:-splits}" in
    splits) build_splits ;;
    verify_retain) verify_retain ;;
    gd) run_gd ;;
    rmu) run_rmu ;;
    probe_repr) run_probe_repr ;;
    eval) run_eval ;;
    all)
        build_splits
        run_gd
        run_probe_repr
        run_rmu
        run_eval
        ;;
    *)
        echo "Unknown target: $1" >&2
        echo "Usage: bash phase2_evo2/run.sh [splits|verify_retain|gd|probe_repr|rmu|eval|all]" >&2
        exit 1
        ;;
esac
