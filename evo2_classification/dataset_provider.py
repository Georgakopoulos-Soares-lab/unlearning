from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from megatron.bridge.training.config import DatasetBuildContext, DatasetProvider

from .labeled_fasta_dataset import LabeledFastaDataset


@dataclass
class LabeledFastaDatasetProvider(DatasetProvider):
    """DatasetProvider for classification fine-tuning from a single labeled FASTA file.

    Expects headers like: >seqid label=0 split=train ...
    Splits are taken directly from the `split=` field already in your FASTA
    (train/val/test), NOT re-randomized -- this preserves whatever split
    your data-prep pipeline assigned.
    """

    fasta_path: Path = None  # REQUIRED
    seq_length: int = 1024
    label_key: str = "label"
    split_key: str = "split"
    train_split_value: str = "train"
    val_split_value: str = "val"
    test_split_value: str = "test"
    prepend_bos: bool = True
    dataloader_type: str = "single"  # required by build_pretraining_data_loader; Evo2DatasetProvider sets this too
    random_seed: int = 1234

    def build_datasets(self, context: DatasetBuildContext) -> tuple[Any | None, Any | None, Any | None]:
        assert self.fasta_path is not None, "fasta_path must be set on LabeledFastaDatasetProvider"
        assert context.tokenizer is not None

        # Parse headers ONCE and share across all three splits, instead of each
        # LabeledFastaDataset independently re-scanning the whole FASTA file
        # (measured at ~77s for this 916K-sequence file -- 3x that otherwise).
        from .labeled_fasta_dataset import NvFaidx, parse_fasta_headers

        headers = parse_fasta_headers(self.fasta_path)
        fasta = NvFaidx(self.fasta_path)

        def _build(split_value: Optional[str], seed_offset: int):
            if split_value is None:
                return None
            return LabeledFastaDataset(
                fasta_path=self.fasta_path,
                tokenizer=context.tokenizer,
                split=split_value,
                seq_length=self.seq_length,
                label_key=self.label_key,
                split_key=self.split_key,
                prepend_bos=self.prepend_bos,
                precomputed_headers=headers,
                precomputed_fasta=fasta,
                random_seed=self.random_seed + seed_offset,
            )

        train_ds = _build(self.train_split_value, seed_offset=0)
        val_ds = _build(self.val_split_value, seed_offset=1)
        test_ds = _build(self.test_split_value, seed_offset=2)
        return train_ds, val_ds, test_ds
