"""Fixed physical batching for reproducible checkpoint-native BF16 evaluation."""
def pack(sequences, device, physical_size=8):
    import torch
    if not 1 <= len(sequences) <= physical_size:
        raise ValueError('Logical batch must fit the fixed physical batch')
    if any(not 2 <= len(s) <= 1000 or set(s)-set('ACGTN') for s in sequences):
        raise ValueError('Unqualified nucleotide sequence')
    tokens = torch.ones((physical_size, 1000), dtype=torch.long, device=device)
    lengths = torch.ones(physical_size, dtype=torch.long, device=device)
    for index, sequence in enumerate(sequences):
        tokens[index, :len(sequence)] = torch.tensor([ord(c) for c in sequence], device=device)
        lengths[index] = len(sequence)
    positions = torch.arange(1000, device=device)[None].expand(physical_size, -1)
    return tokens, lengths, positions
