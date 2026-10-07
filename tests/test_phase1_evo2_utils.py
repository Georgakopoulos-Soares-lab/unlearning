from __future__ import annotations

import gzip
import random
import sys
import types

import numpy as np
import pytest
import torch

from tests._stub_support import register_stub


# Allow this test module to be collected when evo2 is not installed.
evo2_stub = types.ModuleType("evo2")
evo2_stub.Evo2 = object
register_stub("evo2", evo2_stub)

import phase1_evo2.utils as utils

from phase1_evo2.utils import (
    FeatureWriter,
    LoadedEvo2,
    ManifestRecord,
    clean_sequence,
    extract_hidden,
    forward_differentiable,
    forward_inference,
    get_block,
    get_blocks,
    iter_fasta_gz,
    normalize_layer_output,
    pad_batch,
    read_manifest,
    sample_window,
    tokenize_sequences,
    write_manifest,
)


class FakeTokenizer:
    pad_id = 0

    def tokenize(self, sequence: str) -> list[int]:
        vocabulary = {
            "A": 1,
            "C": 2,
            "G": 3,
            "T": 4,
            "N": 5,
        }
        return [vocabulary[base] for base in sequence]


class FakeWrapper:
    def __init__(self, output):
        self.output = output

    def __call__(self, input_ids: torch.Tensor):
        return self.output


class DifferentiableFakeModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.scale = torch.nn.Parameter(torch.tensor(1.0))
        self.blocks = torch.nn.ModuleList(
            [
                torch.nn.Identity(),
                torch.nn.Identity(),
            ]
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
    ):
        batch_size, sequence_length = input_ids.shape
        logits = self.scale * torch.ones(
            batch_size,
            sequence_length,
            6,
            dtype=torch.float32,
            device=input_ids.device,
        )
        return logits, None


class OutputFakeModel(DifferentiableFakeModel):
    def __init__(self, output) -> None:
        super().__init__()
        self.output = output

    def forward(
        self,
        input_ids: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
    ):
        return self.output


def make_loaded(
    *,
    wrapper=None,
    model=None,
    tokenizer=None,
) -> LoadedEvo2:
    model = model or DifferentiableFakeModel()
    tokenizer = tokenizer or FakeTokenizer()
    wrapper = wrapper or FakeWrapper(
        torch.zeros(1, 4, 6, dtype=torch.float32)
    )

    return LoadedEvo2(
        wrapper=wrapper,
        model=model,
        tokenizer=tokenizer,
        model_name="fake_evo2",
    )


def test_load_huggingface_checkpoint_returns_all_components(
    monkeypatch,
) -> None:
    fake_model = DifferentiableFakeModel()
    fake_tokenizer = FakeTokenizer()
    captured = {}

    class FakeEvo2:
        def __init__(
            self,
            model_name: str,
            local_path: str | None,
            use_kernels: bool,
        ) -> None:
            captured["model_name"] = model_name
            captured["local_path"] = local_path
            captured["use_kernels"] = use_kernels

            self.model = fake_model
            self.tokenizer = fake_tokenizer

    monkeypatch.setattr(utils, "Evo2", FakeEvo2)

    loaded = utils.load_huggingface_checkpoint(
        model_name="evo2_7b_base",
        local_path="/tmp/fake-checkpoint.pt",
        use_kernels=True,
    )

    assert loaded.model is fake_model
    assert loaded.tokenizer is fake_tokenizer
    assert loaded.wrapper.model is fake_model
    assert loaded.model_name == "evo2_7b_base"

    assert captured == {
        "model_name": "evo2_7b_base",
        "local_path": "/tmp/fake-checkpoint.pt",
        "use_kernels": True,
    }


def test_tokenize_sequences_truncates_before_tokenization() -> None:
    tokenizer = FakeTokenizer()

    result = tokenize_sequences(
        ["ACGT", "TGCA"],
        tokenizer,
        max_length=2,
    )

    assert result == [
        [1, 2],
        [4, 3],
    ]


def test_tokenize_sequences_rejects_nonpositive_max_length() -> None:
    with pytest.raises(ValueError, match="max_length must be positive"):
        tokenize_sequences(["ACGT"], FakeTokenizer(), max_length=0)


def test_pad_batch_returns_ids_and_mask() -> None:
    input_ids, mask = pad_batch(
        [
            [1, 2, 3],
            [4, 5],
        ],
        pad_id=0,
    )

    assert input_ids.dtype == torch.int64
    assert mask.dtype == torch.int64

    assert input_ids.tolist() == [
        [1, 2, 3],
        [4, 5, 0],
    ]
    assert mask.tolist() == [
        [1, 1, 1],
        [1, 1, 0],
    ]


def test_pad_batch_rejects_empty_batch() -> None:
    with pytest.raises(ValueError, match="empty batch"):
        pad_batch([], pad_id=0)


def test_pad_batch_rejects_empty_sequence() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        pad_batch([[1, 2], []], pad_id=0)


@pytest.mark.parametrize(
    "wrapped_output",
    [
        torch.zeros(2, 4, 6),
        (torch.zeros(2, 4, 6), None),
        ((torch.zeros(2, 4, 6), None), None),
        {"logits": torch.zeros(2, 4, 6)},
    ],
)
def test_forward_inference_extracts_logits_from_supported_outputs(
    wrapped_output,
) -> None:
    loaded = make_loaded(model=OutputFakeModel(wrapped_output))
    input_ids = torch.ones(2, 4, dtype=torch.int64)

    logits = forward_inference(loaded, input_ids)

    assert logits.shape == (2, 4, 6)
    assert not logits.requires_grad


def test_forward_inference_rejects_wrong_logit_shape() -> None:
    loaded = make_loaded(
        model=OutputFakeModel(torch.zeros(2, 4))
    )

    with pytest.raises(RuntimeError, match="Expected logits"):
        forward_inference(
            loaded,
            torch.ones(2, 4, dtype=torch.int64),
        )


def test_forward_differentiable_preserves_gradients() -> None:
    model = DifferentiableFakeModel()
    loaded = make_loaded(model=model)
    input_ids = torch.ones(2, 4, dtype=torch.int64)

    logits = forward_differentiable(loaded, input_ids)
    loss = logits.sum()
    loss.backward()

    assert logits.requires_grad
    assert model.scale.grad is not None
    assert model.scale.grad.item() == pytest.approx(2 * 4 * 6)


def test_get_blocks_returns_ordered_blocks() -> None:
    model = DifferentiableFakeModel()

    blocks = get_blocks(model)

    assert len(blocks) == 2
    assert blocks[0] is model.blocks[0]
    assert blocks[1] is model.blocks[1]


def test_get_blocks_rejects_model_without_blocks() -> None:
    with pytest.raises(TypeError, match="does not expose"):
        get_blocks(torch.nn.Linear(2, 2))


def test_get_blocks_rejects_empty_blocks() -> None:
    model = torch.nn.Module()
    model.blocks = torch.nn.ModuleList()

    with pytest.raises(RuntimeError, match="contains no blocks"):
        get_blocks(model)


def test_get_block_validates_index() -> None:
    model = DifferentiableFakeModel()

    assert get_block(model, 1) is model.blocks[1]

    with pytest.raises(IndexError, match="outside"):
        get_block(model, 2)

    with pytest.raises(IndexError, match="outside"):
        get_block(model, -1)


@pytest.mark.parametrize(
    "output",
    [
        torch.zeros(2, 4, 8),
        (torch.zeros(2, 4, 8), "auxiliary output"),
        [torch.zeros(2, 4, 8), None],
        {"hidden_states": torch.zeros(2, 4, 8)},
    ],
)
def test_extract_hidden_supports_expected_hook_outputs(output) -> None:
    hidden = extract_hidden(output)
    assert hidden.shape == (2, 4, 8)


def test_extract_hidden_rejects_wrong_shape() -> None:
    with pytest.raises(RuntimeError, match="Expected hidden states"):
        extract_hidden(torch.zeros(2, 8))


def test_extract_hidden_rejects_unknown_output() -> None:
    with pytest.raises(TypeError, match="Could not extract"):
        extract_hidden({"unexpected": torch.zeros(2, 4, 8)})


def test_normalize_layer_output_returns_raw_tensor_unchanged() -> None:
    model = DifferentiableFakeModel()
    hidden = torch.randn(2, 4, 8)

    result = normalize_layer_output(
        model=model,
        hidden=hidden,
        layer_idx=0,
        representation="raw",
    )

    assert result is hidden


def test_next_norm_applies_following_blocks_pre_norm() -> None:
    model = DifferentiableFakeModel()
    hidden = torch.randn(2, 4, 8)
    model.blocks[1].pre_norm = torch.nn.LayerNorm(8)

    result = normalize_layer_output(
        model=model,
        hidden=hidden,
        layer_idx=0,
        representation="next_norm",
    )

    expected = model.blocks[1].pre_norm(hidden)
    torch.testing.assert_close(result, expected)


def test_next_norm_applies_final_norm_for_last_block() -> None:
    model = DifferentiableFakeModel()
    model.norm = torch.nn.LayerNorm(8)
    hidden = torch.randn(2, 4, 8)

    result = normalize_layer_output(
        model=model,
        hidden=hidden,
        layer_idx=1,
        representation="next_norm",
    )

    expected = model.norm(hidden)
    torch.testing.assert_close(result, expected)


def test_next_norm_rejects_missing_following_pre_norm() -> None:
    model = DifferentiableFakeModel()

    with pytest.raises(AttributeError, match="does not expose pre_norm"):
        normalize_layer_output(
            model=model,
            hidden=torch.randn(2, 4, 8),
            layer_idx=0,
            representation="next_norm",
        )


def test_normalize_layer_output_rejects_unknown_representation() -> None:
    with pytest.raises(ValueError, match="Unsupported representation"):
        normalize_layer_output(
            model=DifferentiableFakeModel(),
            hidden=torch.randn(2, 4, 8),
            layer_idx=0,
            representation="unknown",
        )


def test_manifest_round_trip(tmp_path) -> None:
    path = tmp_path / "nested" / "manifest.csv"

    expected = [
        ManifestRecord(
            record_id="target-1",
            label=1,
            split="train",
            sequence="ACGT",
            source="target",
            length=4,
        ),
        ManifestRecord(
            record_id="retain-1",
            label=0,
            split="test",
            sequence="TGCA",
            source="retain",
            length=4,
        ),
    ]

    write_manifest(str(path), expected)
    observed = read_manifest(str(path))

    assert observed == expected


def test_read_manifest_uses_sequence_length_when_length_missing(
    tmp_path,
) -> None:
    path = tmp_path / "manifest.csv"
    path.write_text(
        "id,label,split,sequence,source\n"
        "example,1,val,ACGT,synthetic\n"
    )

    records = read_manifest(str(path))

    assert len(records) == 1
    assert records[0].length == 4


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("example,2,train,ACGT,test\n", "invalid label"),
        ("example,1,validation,ACGT,test\n", "invalid split"),
    ],
)
def test_read_manifest_rejects_invalid_values(
    tmp_path,
    row: str,
    message: str,
) -> None:
    path = tmp_path / "manifest.csv"
    path.write_text(
        "id,label,split,sequence,source\n" + row
    )

    with pytest.raises(ValueError, match=message):
        read_manifest(str(path))


def test_read_manifest_rejects_missing_columns(tmp_path) -> None:
    path = tmp_path / "manifest.csv"
    path.write_text(
        "id,label,sequence\n"
        "example,1,ACGT\n"
    )

    with pytest.raises(ValueError, match="missing columns"):
        read_manifest(str(path))


def test_iter_fasta_gz_reads_multiline_sequences(tmp_path) -> None:
    path = tmp_path / "sequences.fasta.gz"

    with gzip.open(path, "wt") as file:
        file.write(
            ">sequence-1 description\n"
            "ACGT\n"
            "TGCA\n"
            "\n"
            ">sequence-2\n"
            "NNNN\n"
        )

    records = list(iter_fasta_gz(str(path)))

    assert records == [
        ("sequence-1 description", "ACGTTGCA"),
        ("sequence-2", "NNNN"),
    ]


def test_clean_sequence_normalizes_and_filters_characters() -> None:
    assert clean_sequence("acgt-nxU") == "ACGTN"


def test_sample_window_returns_short_sequence_unchanged() -> None:
    sequence = "ACGT"

    assert sample_window(
        sequence,
        max_length=8,
        rng=random.Random(42),
    ) == sequence


def test_sample_window_is_reproducible_and_bounded() -> None:
    sequence = "ACGT" * 20

    first = sample_window(
        sequence,
        max_length=12,
        rng=random.Random(42),
    )
    second = sample_window(
        sequence,
        max_length=12,
        rng=random.Random(42),
    )

    assert first == second
    assert len(first) == 12
    assert first in sequence


def test_sample_window_rejects_nonpositive_length() -> None:
    with pytest.raises(ValueError, match="max_length must be positive"):
        sample_window(
            "ACGT",
            max_length=0,
            rng=random.Random(42),
        )


def test_feature_writer_flushes_when_threshold_is_reached(
    tmp_path,
) -> None:
    writer = FeatureWriter(
        out_dir=str(tmp_path),
        num_layers=2,
        chunk_size=3,
    )

    first = torch.tensor(
        [
            [1.0, 2.0],
            [3.0, 4.0],
        ]
    )
    second = torch.tensor([[5.0, 6.0]])

    writer.add(0, first)
    assert not (tmp_path / "layer_0" / "chunk_0000.npy").exists()

    writer.add(0, second)

    chunk_path = tmp_path / "layer_0" / "chunk_0000.npy"
    assert chunk_path.exists()

    saved = np.load(chunk_path)
    np.testing.assert_array_equal(
        saved,
        np.array(
            [
                [1.0, 2.0],
                [3.0, 4.0],
                [5.0, 6.0],
            ],
            dtype=np.float32,
        ),
    )

    assert not list((tmp_path / "layer_0").glob("*.tmp"))


def test_feature_writer_flush_all_writes_partial_chunks(
    tmp_path,
) -> None:
    writer = FeatureWriter(
        out_dir=str(tmp_path),
        num_layers=2,
        chunk_size=10,
    )

    writer.add(0, torch.ones(2, 4))
    writer.add(1, torch.full((1, 4), 2.0))
    writer.flush_all()

    layer_zero = np.load(
        tmp_path / "layer_0" / "chunk_0000.npy"
    )
    layer_one = np.load(
        tmp_path / "layer_1" / "chunk_0000.npy"
    )

    assert layer_zero.shape == (2, 4)
    assert layer_one.shape == (1, 4)
    assert np.all(layer_zero == 1.0)
    assert np.all(layer_one == 2.0)


def test_feature_writer_rejects_invalid_layer(tmp_path) -> None:
    writer = FeatureWriter(
        out_dir=str(tmp_path),
        num_layers=2,
    )

    with pytest.raises(IndexError, match="outside"):
        writer.add(2, torch.ones(1, 4))


def test_feature_writer_rejects_nonmatrix_features(tmp_path) -> None:
    writer = FeatureWriter(
        out_dir=str(tmp_path),
        num_layers=2,
    )

    with pytest.raises(ValueError, match="Expected features"):
        writer.add(0, torch.ones(4))
