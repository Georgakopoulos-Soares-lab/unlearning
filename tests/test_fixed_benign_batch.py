import pytest
import torch
from scripts.sayyed.fixed_benign_batch import pack


def test_physical_shape_and_real_row_identity_are_independent_of_logical_batch():
    one, lengths_one, positions_one = pack(['ACGT'], 'cpu')
    many, lengths_many, positions_many = pack(['ACGT', 'N'*70, 'A'*500], 'cpu')
    assert one.shape == many.shape == (8, 1000)
    assert torch.equal(one[0], many[0])
    assert torch.equal(positions_one, positions_many)
    assert lengths_one.tolist() == [4, 1, 1, 1, 1, 1, 1, 1]
    assert lengths_many.tolist() == [4, 70, 500, 1, 1, 1, 1, 1]
    assert torch.equal(one[0, :4], torch.tensor([65, 67, 71, 84]))
    assert torch.all(one[1:] == 1)


def test_invalid_logical_batch_or_sequence_rejected():
    for sequences in ([], ['AA']*9, ['AX'], ['A'*1001]):
        with pytest.raises(ValueError):
            pack(sequences, 'cpu')
