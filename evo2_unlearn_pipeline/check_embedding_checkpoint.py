"""Read embedding.word_embeddings.weight directly from the base checkpoint
file, independent of the training pipeline, to compare against the live
model's value printed by graddiff_forward_step.py's debug block.

Usage:
    python check_embedding_checkpoint.py
"""

import torch
from torch.distributed.checkpoint import FileSystemReader
from torch.distributed.checkpoint.state_dict_loader import load as dcp_load

CKPT_DIR = "/projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge/iter_0000001"
HIDDEN_SIZE = 1920  # Hyena1bModelProvider.hidden_size
VOCAB_SIZE = 512  # padded vocab size from the tokenizer (confirmed: tok.vocab_size=256, but check padded size below)

reader = FileSystemReader(CKPT_DIR)
metadata = reader.read_metadata()
key = "embedding.word_embeddings.weight"
assert key in metadata.state_dict_metadata, f"{key} not found! Available keys sample: {list(metadata.state_dict_metadata.keys())[:10]}"

# Get the REAL shape from metadata instead of guessing padded vocab size.
real_shape = metadata.state_dict_metadata[key].size
print(f"Real shape of {key} in checkpoint: {real_shape}")

target = {key: torch.zeros(real_shape)}
dcp_load(target, storage_reader=reader)
raw_weight = target[key]

print("=== Raw checkpoint embedding.word_embeddings.weight ===")
print("mean:", raw_weight.float().mean().item())
print("std:", raw_weight.float().std().item())
print("first5 (flattened):", raw_weight.float().flatten()[:5].tolist())
print()
print("Compare this to the [DEBUG] LIVE embedding.word_embeddings.weight line")
print("from the training job's log. If mean/std/first5 match (even")
print("approximately, given bf16 rounding), the checkpoint loaded correctly.")
print("If the live values look like small random noise (mean~0, std~0.02,")
print("typical of fresh initialization) while these raw values are clearly")
print("different, the checkpoint did NOT load and training started from")
print("random init.")
