# Custom labeled-FASTA dataset for Evo2 classification fine-tuning.
#
# Your FASTA headers look like:
#   >hvue_hvue_human_host_tropism_val_0 label=0 split=val length=1000
#
# NvFaidx (bionemo's FASTA indexer) only keeps the first whitespace-delimited
# token of the header (the sequence id) -- it silently discards `label=` and
# `split=`. So we do our own lightweight header parse here, independent of
# NvFaidx, and use NvFaidx only for indexed sequence access.

import re
from pathlib import Path
from typing import Optional

import torch
import random

from bionemo.common.fasta.nvfaidx import NvFaidx


_HEADER_KV_RE = re.compile(r"(\w+)=(\S+)")


def parse_fasta_headers(fasta_path: Path) -> dict[str, dict[str, str]]:
    """Read only the header lines of a FASTA file and parse key=value metadata.

    Returns:
        dict mapping seqid -> {"label": "...", "split": "...", ...} (raw string values)
    """
    headers: dict[str, dict[str, str]] = {}
    with open(fasta_path) as f:
        for line in f:
            if not line.startswith(">"):
                continue
            line = line[1:].strip()
            seqid = line.split()[0]
            kv = dict(_HEADER_KV_RE.findall(line))
            headers[seqid] = kv
    return headers


class LabeledFastaDataset(torch.utils.data.Dataset):
    """FASTA dataset for sequence classification.

    Each item returns:
        tokens: LongTensor [seq_length]  (BOS/EOD-prepended, truncated/padded to seq_length)
        position_ids: LongTensor [seq_length]
        label: LongTensor scalar
        loss_mask: LongTensor [seq_length]  (1 for real tokens, 0 for padding) -- used only
            to compute the pooled index (last real token), NOT for a per-token LM loss.
    """

    def __init__(
        self,
        fasta_path: Path,
        tokenizer,
        split: str,
        seq_length: int,
        label_key: str = "label",
        split_key: str = "split",
        prepend_bos: bool = True,
        precomputed_headers: dict[str, dict[str, str]] | None = None,
        precomputed_fasta: NvFaidx | None = None,
        random_seed: int = 1234,
    ):
        super().__init__()
        fasta_path = Path(fasta_path)
        # NvFaidx, despite its name, does NOT do true lazy/mmap access -- its
        # _read_fasta loads the entire file's sequence content into memory as
        # Python strings on construction. Since train/val/test all reference
        # the same file, share one instance instead of building it 3x.
        self.fasta = precomputed_fasta if precomputed_fasta is not None else NvFaidx(fasta_path)
        # Parsing headers is a full file scan -- if the caller already did this
        # once (e.g. DatasetProvider sharing it across train/val/test), reuse
        # it instead of re-scanning the file 3x (this alone cost ~77s in the
        # smoke test, and would repeat on every resumed job submission).
        self.headers = precomputed_headers if precomputed_headers is not None else parse_fasta_headers(fasta_path)
        self.tokenizer = tokenizer
        self.seq_length = seq_length
        self.prepend_bos = prepend_bos

        all_ids = sorted(self.fasta.keys())
        seqids = [
            sid
            for sid in all_ids
            if sid in self.headers
            and self.headers[sid].get(split_key) == split
            and label_key in self.headers[sid]
        ]
        if len(seqids) == 0:
            raise ValueError(
                f"No sequences found for split={split!r} in {fasta_path}. "
                f"Check that headers contain '{split_key}=' and '{label_key}=' fields."
            )

        rng = random.Random(random_seed)
        rng.shuffle(seqids)
        self.seqids = seqids
        self.label_key = label_key

    def __len__(self) -> int:
        return len(self.seqids)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        seqid = self.seqids[idx]
        sequence = self.fasta[seqid].sequence().upper()
        label = int(self.headers[seqid][self.label_key])

        if hasattr(self.tokenizer, "tokenize"):
            tokenized = self.tokenizer.tokenize(sequence)
        else:
            tokenized = self.tokenizer.text_to_ids(sequence)

        if self.prepend_bos:
            tokens = [self.tokenizer.eod, *tokenized]
        else:
            tokens = list(tokenized)

        # Truncate or pad to a fixed seq_length so batches can be stacked.
        pad_id = getattr(self.tokenizer, "eod", 0)
        if len(tokens) > self.seq_length:
            tokens = tokens[: self.seq_length]
            n_real = self.seq_length
        else:
            n_real = len(tokens)
            tokens = tokens + [pad_id] * (self.seq_length - len(tokens))

        loss_mask = torch.zeros(self.seq_length, dtype=torch.long)
        loss_mask[:n_real] = 1

        return {
            "tokens": torch.tensor(tokens, dtype=torch.long),
            "position_ids": torch.arange(self.seq_length, dtype=torch.long),
            "label": torch.tensor(label, dtype=torch.long),
            "loss_mask": loss_mask,
        }
