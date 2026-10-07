====================================================================
BioNeMo Evo2 Setup & LoRA Classification Fine-Tuning — Setup Notes
Explorer Cluster (Northeastern), H200 GPU, pip-only (no container)
====================================================================

CONTEXT
-------
Goal: probe whether the Evo2 genomic language model has inherent
capability for a binary classification task (host-tropism prediction,
GUE benchmark), as a precursor to model-unlearning work. Approach:
LoRA fine-tune a classification head on top of the Evo2 1B backbone.

Repo locations:
  BioNeMo framework + evo2_megatron recipe:
    /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
  Our own classification code + data + results:
    /projects/MENTISLab/unlearning/


====================================================================
1. ENVIRONMENT SETUP (pip-only, no Docker/Apptainer)
====================================================================

WHY PIP-ONLY WAS HARD: the official recipe's Docker image
(nvcr.io/nvidia/pytorch) ships a pinned NVIDIA-internal nightly
PyTorch build tied to CUDA 13.0, which is not published on PyPI or
pytorch.org. We had to reconstruct an equivalent environment from
public pip packages, which required a stable PyPI torch build
(cu128) instead, and manually fixing several dependencies that
assume the container's pre-built environment.

1.1 Cluster prerequisites confirmed
  - GPU: NVIDIA H200 (143GB), driver supports CUDA 12.8
  - CUDA module: cuda/12.8.0 (matches driver ceiling)
  - Python module: python/3.13.5 exists but recipe needs 3.10-3.12 for
    dependency wheel availability -> used conda env with Python 3.12
    instead (conda 4.13.0 available via /shared/centos7/anaconda3/2022.05)
  - GCC 11.5.0 (compatible with CUDA 12.8, supports up to GCC 12)
  - git/2.52.0 module

1.2 Create the conda environment
    conda create -n bionemo_evo2 python=3.12 -y
    conda activate bionemo_evo2
    pip install --upgrade pip

1.3 Load modules + set env vars (every session)
    module load cuda/12.8.0
    module load git/2.52.0
    conda activate bionemo_evo2
    cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
    source .venv/bin/activate   # after .venv exists, see below

  Required environment variables (headers/libs for NCCL & cuDNN,
  since torch's pip wheel bundles these under site-packages/nvidia/
  but doesn't put them on the compiler/linker search path by default):

    export CPATH=<conda_env>/lib/python3.12/site-packages/nvidia/nccl/include:<conda_env>/lib/python3.12/site-packages/nvidia/cudnn/include:$CPATH
    export LD_LIBRARY_PATH=<conda_env>/lib/python3.12/site-packages/nvidia/nccl/lib:<conda_env>/lib/python3.12/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH

  where <conda_env> = /home/<user>/.conda/envs/bionemo_evo2

  Saved as env_setup.sh in the recipe directory for convenience:
    module load cuda/12.8.0
    module load git/2.52.0
    conda activate bionemo_evo2
    cd /projects/MENTISLab/bionemo-framework/recipes/evo2_megatron
    source .venv/bin/activate
    export CPATH=...      (as above)
    export LD_LIBRARY_PATH=...  (as above)

1.4 Clone the repo and build the recipe's venv
    git clone https://github.com/NVIDIA/bionemo-framework.git
    cd bionemo-framework/recipes/evo2_megatron
    pip install uv    # .ci_build.sh requires this
    export NVTE_CUDA_ARCHS=90        # Hopper (H200) build target, speeds up TE compile
    export NVTE_WITH_NCCL_EP=0       # disables MoE/expert-parallel code path (not needed for dense Evo2, avoids a torch-version-mismatch header error)
    bash .ci_build.sh

  This creates .venv/ with most dependencies. Known build issues we
  hit and fixed (see section 1.5-1.8):
    - nvidia-resiliency-ext has no compatible PyPI wheel for Rocky
      Linux 9.3's glibc (2.34); PyPI only ships manylinux_2_39 wheels.
    - causal_conv1d and nv-grouped-gemm need torch as a build
      dependency but don't declare it (--no-build-isolation issue).
    - No stable PyPI torch matching the recipe's internal nightly
      pin exists; must install a real stable torch release instead.
    - Transformer Engine needs to be installed/built separately.

1.5 FIX: nvidia-resiliency-ext (missing wheel for this glibc)
    mkdir -p /tmp/nvrx_build && cd /tmp/nvrx_build
    git clone --branch v0.6.0 https://github.com/NVIDIA/nvidia-resiliency-ext.git
    cd nvidia-resiliency-ext
    pip install pybind11
    python -m pip wheel . --no-deps --no-build-isolation -w /tmp/nvrx_wheels
    export UV_FIND_LINKS=/tmp/nvrx_wheels
    # then re-run bash .ci_build.sh -- uv will prefer this local wheel

1.6 FIX: causal_conv1d / nv-grouped-gemm missing torch as build dep
  Edit pyproject.toml in the recipe directory, in the
  [tool.uv.extra-build-dependencies] section, add:
    causal_conv1d = ["torch"]
    nv-grouped-gemm = ["torch"]

1.7 FIX: install a real stable torch (cu128) manually
    pip install torch==2.9.1 torchvision==0.24.1 torchaudio==2.9.1 \
      --index-url https://download.pytorch.org/whl/cu128
  .ci_build.sh's `uv venv --system-site-packages` picks this up from
  the parent conda env automatically; uv did not try to reinstall it.

1.8 FIX: install Transformer Engine (not included in build_requirements)
    export NVTE_CUDA_ARCHS=90
    export NVTE_WITH_NCCL_EP=0
    export CPATH=...  (nccl/cudnn include dirs, see 1.3)
    pip install --no-build-isolation transformer_engine[pytorch]

  ADDITIONAL FIX needed: cuDNN must physically exist INSIDE .venv's
  own site-packages (not just the parent conda env), because TE's
  runtime library-loader only checks sysconfig.get_path("purelib")
  of the currently-active interpreter:
    .venv/bin/python -m pip install --ignore-installed --no-deps \
      nvidia-cudnn-cu12==9.10.2.21

  Also: always use `.venv/bin/python -m pip` explicitly (not bare
  `pip`) to avoid installing into the wrong environment -- `uv venv`
  does not install a `pip` binary into .venv by default, so a bare
  `pip` command can silently resolve to the parent conda env's pip.

1.9 Verify the environment
    .venv/bin/python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
    .venv/bin/python -c "import transformer_engine.pytorch as te; print(te.__version__)"
    .venv/bin/python -c "import megatron.bridge; print('OK')"
    train_evo2 --help


====================================================================
2. RUNNING JOBS ON EXPLORER (SLURM)
====================================================================

  GPU partition GRES name confirmed via: sinfo -p gpu -o "%P %G"
    -> gpu:h200:8 available (also v100, a100, t4 on same partition)

  Interactive session for building/debugging:
    srun -p gpu-interactive --gres=gpu:h200:1 --time=00:20:00 --pty /bin/bash

  Batch jobs: max 8h on "gpu" partition. For long training runs,
  submit multiple sequential jobs and rely on checkpoint-resume
  (see section 5) -- just resubmit the same sbatch script unchanged.

  Conda activation inside a non-interactive batch script requires
  explicitly sourcing conda's init script first (conda isn't
  auto-initialized in non-login shells):
    source /shared/centos7/anaconda3/2022.05/etc/profile.d/conda.sh
    conda activate bionemo_evo2


====================================================================
3. CONVERTING A HUGGINGFACE CHECKPOINT TO MBRIDGE FORMAT
====================================================================

  Evo2 checkpoints on HuggingFace are in "Savanna" format (Arc
  Institute's original training codebase). The recipe ships a
  converter: evo2_convert_savanna_to_mbridge.

  MUST run on an actual GPU node (not the login node) -- the
  conversion script calls torch.cuda.synchronize() during checkpoint
  saving and fails with "Found no NVIDIA driver" otherwise.

  Command used (evo2_1b_base):
    evo2_convert_savanna_to_mbridge \
      --savanna-ckpt-path arcinstitute/savanna_evo2_1b_base \
      --revision <commit_sha> \
      --mbridge-ckpt-dir /projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge \
      --model-size evo2_1b_base \
      --tokenizer-path tokenizers/nucleotide_fast_tokenizer_256 \
      --verbose

  NOTE on --revision: the tool strongly recommends pinning a specific
  commit SHA (not "latest") for reproducibility/security. Find the
  current commit at:
    https://huggingface.co/<org>/<repo>/commits/main

  RESULT FORMAT: a PyTorch Distributed Checkpoint (DCP) -- a
  directory (e.g. iter_0000001/) containing __*.distcp shard files,
  .metadata, metadata.json, common.pt, train_state.pt, and a
  tokenizer/ subfolder. NOT a single .pt file.

  KNOWN GAP: the converted checkpoint does NOT contain
  "*._extra_state" keys (TransformerEngine's FP8/metadata
  placeholders) -- Savanna's native format has no such concept, so
  they're simply absent. Loading this checkpoint into a model that
  expects those keys fails by default. Fix: set
    cfg.checkpoint.dist_ckpt_strictness = "ignore_all"
  This is safe -- confirmed via direct inspection of the checkpoint's
  .metadata file that 0 "_extra_state" keys exist while 254 real
  weight keys (embeddings, layer weights, final_norm, etc.) are
  present and correct.

  Verifying checkpoint contents directly (without loading a model):
    python -c "
    from torch.distributed.checkpoint import FileSystemReader
    reader = FileSystemReader('<ckpt_dir>/iter_XXXXXXX')
    metadata = reader.read_metadata()
    print(sorted(metadata.state_dict_metadata.keys()))
    "


====================================================================
4. DATA FORMAT REQUIRED (FASTA WITH LABELED HEADERS)
====================================================================

  Input file: a single FASTA file with metadata encoded in the
  header line as space-separated key=value pairs, e.g.:
    >hvue_hvue_human_host_tropism_val_0 label=0 split=val length=1000
    ACGTACGT...

  Required header fields (configurable key names, defaults shown):
    label=<int>    -- class index (0 or 1 for binary)
    split=<str>    -- one of "train"/"val"/"test" (values configurable)

  Dataset stats for the actual file used (hvue_gue_manifest.fasta):
    Train: 640,016 sequences
    Val:   138,046 sequences
    Test:  138,024 sequences
    Class balance: 40.3% label=0, 59.7% label=1 (moderate imbalance --
      a trivial "always predict majority class" baseline already
      gets ~59.7% accuracy / ~0.674 cross-entropy loss; track a
      balanced metric eventually, not just raw accuracy)
    Sequence length: 96.7% exactly 1000 nt (tail down to 978) ->
      --seq-length 1024 covers every sequence (1000 + 1 BOS token)
      with minimal padding waste.

  IMPORTANT GOTCHA: NvFaidx (bionemo's FASTA indexer) only keeps the
  FIRST whitespace-delimited token of each header line (the sequence
  ID) -- it silently discards label=/split=/etc. We wrote our own
  lightweight header parser (parse_fasta_headers) that does a
  separate pass reading only ">" lines and regex-extracting key=value
  pairs, independent of NvFaidx, then use NvFaidx only for indexed
  sequence access.

  IMPORTANT GOTCHA #2: NvFaidx, despite its name, does NOT do true
  lazy/mmap access -- it loads the ENTIRE FASTA file's sequence
  content into memory as Python strings on construction. Since
  train/val/test all reference the same file, we share ONE NvFaidx
  instance (and one header-parse pass) across all three splits
  instead of building 3 separate ones (was costing ~77s per job
  otherwise, x3 for header parsing + implicitly x3 for full-file
  loads).

  IMPORTANT GOTCHA #3 (the big one -- caused a training collapse):
  our dataset originally sorted sequence IDs alphabetically
  (`sorted(self.fasta.keys())`), and the training dataloader type we
  used ("single") maps to `MegatronPretrainingSampler`, which is
  PURELY SEQUENTIAL -- it does NOT shuffle. Combined, this meant
  every epoch walked the data in the exact same, potentially
  label-correlated order (sequence IDs often encode structure from
  the original benchmark naming). This caused unstable training loss
  and a mid-training collapse to near-random-guessing performance.
  FIX: shuffle sample order explicitly with a fixed seed at dataset
  construction time (independent of the sampler), using Python's
  `random.Random(seed).shuffle(seqids)`. Different seeds are used per
  split (base seed + 0/1/2 offset) so train/val/test orders differ.


====================================================================
5. CLASSIFICATION TASK: WHAT HAD TO BE BUILT (NOT PROVIDED BY BIONEMO)
====================================================================

  BioNeMo's evo2_megatron recipe ONLY supports causal-language-model
  fine-tuning out of the box (--fasta-data, --sharded-eden-data,
  --dataset-config), including with LoRA (--lora-finetune). It does
  NOT support classification -- LoRA there just makes the SAME
  causal-LM objective parameter-efficient; it does not add a
  classification head or loss. We built this ourselves, reusing as
  much of BioNeMo's internals as safely possible. Files (all in
  /projects/MENTISLab/unlearning/evo2_classification/):

  5.1 labeled_fasta_dataset.py
    - parse_fasta_headers(): independent header-only parser (see
      section 4 gotcha #1)
    - LabeledFastaDataset: tokenizes each sequence (reusing the
      tokenizer's .tokenize()/.text_to_ids()), prepends BOS/EOD
      token, pads/truncates to a fixed seq_length, returns
      {tokens, position_ids, label, loss_mask}. loss_mask here marks
      real (non-padding) tokens -- used to find the LAST REAL TOKEN
      for pooling, not for a per-token LM loss.

  5.2 dataset_provider.py
    - LabeledFastaDatasetProvider: implements Megatron-Bridge's
      `DatasetProvider.build_datasets()` abstract contract, building
      one shared NvFaidx + header-parse, then three
      LabeledFastaDataset instances (train/val/test) from it.
    - REQUIRED FIELD: dataloader_type = "single" -- without this
      explicitly set, Megatron-Bridge's dataloader builder raises
      "None dataloader type is not supported." (Evo2DatasetProvider
      sets this too, marked "# critical" in the original source.)

  5.3 model.py
    - HyenaClassificationModelProvider(Hyena1bModelProvider): forces
      post_process=False on the backbone (skips the causal-LM output
      layer, keeps raw hidden states).
    - HyenaForSequenceClassification: wraps the backbone with:
        (a) final_norm -- a manually-reconstructed TENorm layer.
            CRITICAL FIX: when post_process=False, the backbone's own
            HyenaStack does NOT construct its final normalization
            layer AT ALL (confirmed: `self.final_norm = None` in that
            case). Skipping this caused astronomic loss (~1e14) at
            first, because raw unnormalized residual-stream
            activations were fed straight into a classifier.
        (b) last-token pooling: hidden_states[seq_lengths, batch_idx, :]
            where seq_lengths = loss_mask.sum(dim=1) - 1 (index of the
            last real token per sequence).
        (c) classifier: a plain nn.Linear(hidden_size, num_classes).
    - sharded_state_dict(): REQUIRED for Megatron-Bridge's checkpoint
      loading (a plain nn.Module without this raises
      "no attribute 'sharded_state_dict'"). Delegates the backbone's
      own keys UNPREFIXED (so they match the base checkpoint's
      original key names on disk, e.g. "decoder.layers.0..." -- NOT
      "backbone.decoder.layers.0..."). Maps our own final_norm's
      weight to the checkpoint's actual key "decoder.final_norm.weight".
      CRITICAL FIX: must wrap tensors with
      `megatron.core.utils.make_sharded_tensor_for_checkpoint(...)`,
      NOT pass raw/plain tensors. A raw tensor is silently NEVER
      populated by the loader even when the checkpoint key exists and
      no error is raised -- confirmed empirically: final_norm.weight
      stayed at TENorm's default all-1.0s init despite the checkpoint
      having real trained values (mean=0.286, std=0.123), until this
      fix was applied.
    - dtype handling: Megatron-Bridge's mixed-precision setup casts
      ALL model parameters (including our custom classifier) to
      bf16. Match the classifier's INPUT to whatever dtype its
      weights actually are (`pooled.to(self.classifier.weight.dtype)`)
      rather than forcing float32 -- forcing float32 caused a real
      "mat1 and mat2 must have the same dtype" crash. Upcast only the
      OUTPUT logits to float32 for numerically stable loss.

  5.4 forward_step.py
    - classification_data_step(): simplified batch-fetching (skips
      Megatron-Bridge's stage-aware get_batch_from_iterator, since
      we're TP=1/PP=1/CP=1 -- would need updating if scaling to
      multi-GPU with pipeline parallelism).
    - classification_forward_step(): computes seq_lengths from
      loss_mask, calls the model, returns (logits, loss_function).
    - classification_loss_function(): cross-entropy, returning
      (loss, count, {"cls loss": reporting_tensor}) -- the SAME
      3-tuple contract as BioNeMo's own masked_next_token_loss, using
      SUM-of-per-sample-losses / COUNT-of-samples (not mean) so
      Megatron-Bridge's cross-data-parallel-rank averaging
      (sum(loss)/sum(count)) produces a correct global mean.

  5.5 train_classifier.py
    - Reuses bionemo.evo2.recipes.evo2._evo2_common (a PRIVATE,
      underscore-prefixed helper -- not public API, could change) to
      get a fully-valid ConfigContainer (correct optimizer/scheduler/
      DDP/precision settings) by passing a placeholder
      dataset_config_path (never actually read, since we overwrite
      cfg.dataset afterward) and our own model_provider class.
    - Overwrites cfg.dataset with our LabeledFastaDatasetProvider.
    - Sets cfg.checkpoint.pretrained_checkpoint (NOT cfg.checkpoint.load
      -- that field is for resuming THIS experiment's own run, and
      setting it to the base checkpoint caused a real crash trying to
      load base-model keys into the LoRA-wrapped model's shape).
    - Sets cfg.checkpoint.finetune = True, dist_ckpt_strictness =
      "ignore_all" (see section 3).
    - _evo2_common already builds `peft=Evo2LoRA(...)` internally
      when lora_finetune=True -- Evo2LoRA (from
      bionemo.evo2.models.evo2_lora) is architecture-agnostic (pure
      module-name pattern matching + freezing), so it works
      unmodified on our custom classification model as long as the
      backbone still contains the same module names (mixer,
      dense_projection, mlp.linear_fc1/2, self_attention.*, etc.).
    - Overrides cfg.train.eval_iters / eval_interval / save_interval
      post-construction, since _evo2_common hardcodes
      eval_interval=100, eval_iters=32 and doesn't expose them as
      parameters.
    - Calls megatron.bridge.training.pretrain.pretrain(cfg,
      classification_forward_step) -- same entrypoint train_evo2.py
      itself uses.


====================================================================
6. TRAINING RUN SIZING (real numbers, not the tiny smoke-test slice)
====================================================================

  global_batch_size = 64, micro_batch_size = 16 (grad accumulation=4)
    -- H200 has huge headroom (smoke test used ~8GB of 143GB at 1/16
    this batch size)
  1 epoch = 640,016 / 64 ~= 10,000 steps
  Target: ~2 epochs = 20,000 steps (max_steps)
  warmup_steps = 500 (2.5% of total) -- needed to avoid a scheduler
    crash ("lr_decay_steps must be > 0") that happens if
    warmup+constant >= max_steps
  eval_iters = 50 for PERIODIC monitoring during training (NOT a
    full pass -- val set has 138,046 samples; a full pass every
    check would take as long as training itself). Treat a true
    full-validation-set number as a separate follow-up evaluation on
    the final checkpoint.
  Learning rate: started at 1e-4 / min 1e-5 -- caused a training
    COLLAPSE around 60% through a 30,000-step run (loss dropped to a
    genuinely good ~0.35-0.42, well below the 0.674 majority-baseline,
    then suddenly jumped to ~0.69 and stayed flat for 1500+ steps,
    with grad norms collapsing near-zero -- a degenerate/dead
    classifier). Lowered to lr=3e-5 / min 3e-6 for the retry.


====================================================================
7. KEY LESSONS / DEBUGGING METHODOLOGY THAT WORKED
====================================================================

  - When something silently doesn't work (no error, but wrong
    behavior), don't assume the mechanism you added is correct --
    verify empirically. The final_norm.weight bug produced ZERO
    errors and only surfaced via directly comparing live model
    weights against the raw checkpoint file's tensor values.
  - "ignore_all" checkpoint strictness is a broad hammer -- it papers
    over genuinely-missing-but-harmless keys (_extra_state) but would
    equally hide a real loading failure. Always independently verify
    what actually loaded when using it, don't just trust "no crash."
  - When reusing a framework's existing pattern (e.g. copying
    dataloader_type="single" from an existing dataset provider),
    check what that pattern actually DOES, not just that it "looks
    like the same kind of thing" -- it silently disabled shuffling.
  - A sudden mid-training collapse to a fixed baseline value (e.g.
    exactly ln(2) for binary CE) with near-zero gradients is a
    signature of a degenerate/collapsed classifier, often caused by
    too-aggressive LR for the adapter size, or (as suspected/fixed
    here) unshuffled/correlated batch ordering.


====================================================================
8. STATUS AS OF THIS DOCUMENT
====================================================================

  - Full pip-only environment: WORKING and verified.
  - Checkpoint conversion (Savanna -> mbridge): WORKING.
  - Full classification fine-tuning pipeline (data -> model -> LoRA
    -> loss -> checkpoint save/eval): WORKING end-to-end, confirmed
    via a working small-scale run with correct loss magnitude and
    correct pretrained-weight loading.
  - Real training run: in progress / iterating on stability. Two
    fixes applied after the first real attempt collapsed:
      (1) lowered LR (1e-4 -> 3e-5)
      (2) fixed dataset shuffling (was relying on a non-shuffling
          sampler + alphabetically-sorted sequence IDs)
  - Next: confirm the restarted run trains stably to completion
    without a repeat collapse; then evaluate the final checkpoint on
    the full validation/test sets (not the periodic eval_iters=50
    subset) to get a real capability-probe number.