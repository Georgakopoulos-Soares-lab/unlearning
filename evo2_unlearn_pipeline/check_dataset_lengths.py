"""Report real sequence/token counts for the raw (pre-repetition) HVUE and GUE
indexed datasets, rather than estimating from .bin/.idx file sizes.

Usage (same env as training):
    python check_dataset_lengths.py
"""

from megatron.core.datasets.indexed_dataset import IndexedDataset

DATASETS = {
    "HVUE forget (train)": "/projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm/hvue_manual_train_nucleotide_fast_tokenizer_256_train",
    "HVUE forget (val, held-out)": "/projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm/hvue_manual_val_nucleotide_fast_tokenizer_256_val",
    "GUE retain (train)": "/projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/fasta_splits/preprocessed_causal_lm/gue_train_split_nucleotide_fast_tokenizer_256_train",
    "GUE retain (val)": "/projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/fasta_splits/preprocessed_causal_lm/gue_val_split_nucleotide_fast_tokenizer_256_val",
    "GUE retain (test)": "/projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/fasta_splits/preprocessed_causal_lm/gue_test_split_nucleotide_fast_tokenizer_256_test",
    "HVUE forget (test, held-out)": "/projects/MENTISLab/unlearning/data/evo2/benchmarks/preprocessed_causal_lm/hvue_manual_test_nucleotide_fast_tokenizer_256_test",
}

for name, prefix in DATASETS.items():
    ds = IndexedDataset(prefix)
    n_docs = len(ds)
    total_tokens = sum(ds.sequence_lengths) if hasattr(ds, "sequence_lengths") else None
    print(f"{name}:")
    print(f"  prefix: {prefix}")
    print(f"  num documents/sequences: {n_docs}")
    if total_tokens is not None:
        print(f"  total tokens: {total_tokens:,}")
        print(f"  mean tokens/doc: {total_tokens / n_docs:.1f}")
    print()
