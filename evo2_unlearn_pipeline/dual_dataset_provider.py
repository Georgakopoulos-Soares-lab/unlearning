"""Dual forget+retain dataset provider for Gradient Difference unlearning.

Reuses bionemo's own Evo2DatasetProvider (the SAME mechanism our causal-LM
LoRA continued-pretraining run already validated) for BOTH the forget-set
(HVUE) and retain-set (GUE) sides independently, then combines them into one
dataset whose __getitem__ returns BOTH a forget sample and a retain sample
under distinct key prefixes -- so a single training-loop batch contains both,
letting Gradient Difference's joint loss (-L_forget + lambda*L_retain) be
computed in one step.

IMPORTANT: forget and retain sets almost certainly differ in size. Indices
wrap around (modulo) for whichever is shorter, so every training step still
sees a full-size batch from both sides.
"""

from dataclasses import dataclass
from typing import Any, Optional

import torch
from megatron.bridge.training.config import DatasetBuildContext, DatasetProvider

from bionemo.evo2.data.evo2_dataset_provider import Evo2DatasetProvider


class _DualSplitDataset(torch.utils.data.Dataset):
    """Combines a forget-set dataset and a retain-set dataset into one.

    Each __getitem__ call returns a dict with BOTH "forget_*" and "retain_*"
    keyed entries (e.g. "forget_tokens", "retain_tokens", ...), so the
    default PyTorch collate function batches each side independently and
    correctly (it operates per dict key across the batch dimension).
    """

    def __init__(self, forget_ds, retain_ds):
        self.forget_ds = forget_ds
        self.retain_ds = retain_ds
        # Use the LARGER of the two so neither side gets starved across an
        # epoch; the shorter side simply wraps around via modulo indexing.
        self.length = max(len(forget_ds), len(retain_ds))

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        f = self.forget_ds[idx % len(self.forget_ds)]
        r = self.retain_ds[idx % len(self.retain_ds)]
        out: dict[str, torch.Tensor] = {}
        for k, v in f.items():
            out[f"forget_{k}"] = v
        for k, v in r.items():
            out[f"retain_{k}"] = v
        return out


class _FixedSampleContext:
    """Mimics DatasetBuildContext but with explicit sample counts, so we can
    ask each sub-provider to build ONLY the splits we actually need (e.g.
    forget: train + val only, test=0 so it's skipped; retain: same)."""

    def __init__(self, tokenizer, train_samples: int, valid_samples: int, test_samples: int):
        self.tokenizer = tokenizer
        self.train_samples = train_samples
        self.valid_samples = valid_samples
        self.test_samples = test_samples


@dataclass
class GradDiffDualDatasetProvider(DatasetProvider):
    """Builds the combined forget+retain dataset for Gradient Difference.

    forget_dataset_config_path / forget_dataset_dir: point at HVUE's
        training_data_config.yaml and preprocessed_causal_lm dir (already
        built and validated in our causal-LM continued-pretraining work).
        Only the "train" split of this config is used for TRAINING (forget
        signal); the "validation" split (HVUE val) is used ONLY for
        held-out monitoring of forgetting progress, never trained on.
    retain_dataset_config_path / retain_dataset_dir: point at GUE's
        equivalent config/preprocessed dir (to be filled in once GUE
        preprocessing is complete).
    """

    forget_dataset_config_path: Optional[str] = None
    forget_dataset_dir: Optional[str] = None
    retain_dataset_config_path: Optional[str] = None
    retain_dataset_dir: Optional[str] = None
    seq_length: int = 1024
    random_seed: int = 1234
    dataloader_type: str = "single"  # required by build_pretraining_data_loader
    # Batch assembly (document lookup + disk read + concatenation for
    # short-document packing) happens in CPU-side Python/NumPy code inside
    # GPTDataset.__getitem__, NOT on the GPU. Without background worker
    # processes, this blocks the GPU idle every single step waiting for the
    # next batch -- confirmed as the likely cause of a ~15x GPU-utilization
    # drop (3.6-5.3 vs the validated 50.4 TFLOP/s/GPU) on a short-sequence
    # retain dataset (emp_h3) that needs heavy document concatenation to fill
    # seq_length=1024. These defaults enable prefetching so CPU assembly for
    # step N+1 overlaps with GPU compute for step N.
    num_workers: int = 4
    persistent_workers: bool = True
    pin_memory: bool = True

    def _build_one_side(
        self,
        dataset_config_path: str,
        dataset_dir: str,
        context: DatasetBuildContext,
        train_samples: int,
        valid_samples: int,
    ):
        provider = Evo2DatasetProvider(
            random_seed=self.random_seed,
            seq_length=self.seq_length,
            dataset_config_path=dataset_config_path,
            dataset_dir=dataset_dir,
        )
        # test_samples=0 -> BlendedMegatronDatasetBuilder skips building the
        # test split entirely (standard Megatron convention), since we don't
        # need it here (HVUE/GUE test splits stay reserved for classification
        # evaluation, untouched by unlearning).
        sub_context = _FixedSampleContext(context.tokenizer, train_samples, valid_samples, 0)
        train_ds, val_ds, _test_ds = provider.build_datasets(sub_context)
        return train_ds, val_ds

    def build_datasets(self, context: DatasetBuildContext) -> tuple[Any | None, Any | None, Any | None]:
        assert self.forget_dataset_config_path is not None, "forget_dataset_config_path must be set"
        assert self.retain_dataset_config_path is not None, "retain_dataset_config_path must be set"

        forget_train, forget_val = self._build_one_side(
            self.forget_dataset_config_path,
            self.forget_dataset_dir,
            context,
            context.train_samples,
            context.valid_samples,
        )
        retain_train, retain_val = self._build_one_side(
            self.retain_dataset_config_path,
            self.retain_dataset_dir,
            context,
            context.train_samples,
            context.valid_samples,
        )

        train_ds = _DualSplitDataset(forget_train, retain_train)
        val_ds = (
            _DualSplitDataset(forget_val, retain_val)
            if (forget_val is not None and retain_val is not None)
            else None
        )
        # No combined test split -- forgetting-verification against the
        # reserved HVUE test split happens as a SEPARATE evaluation step
        # after unlearning, not as part of this training run.
        return train_ds, val_ds, None
