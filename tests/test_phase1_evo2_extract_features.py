from __future__ import annotations

import json
import sys
import types

import numpy as np
import pytest
import torch

from tests._stub_support import register_stub


# Keep these tests runnable without the optional Evo-2 installation.
evo2_stub = types.ModuleType("evo2")
evo2_stub.Evo2 = object
register_stub("evo2", evo2_stub)

import phase1_evo2.extract_features as workflow

from phase1_evo2.utils import LoadedEvo2, ManifestRecord


class FakeTokenizer:
    pad_id = 0

    def tokenize(self, sequence: str) -> list[int]:
        vocabulary = {"A": 1, "C": 2, "G": 3, "T": 4, "N": 5}
        return [vocabulary[base] for base in sequence]


class AddValue(torch.nn.Module):
    def __init__(self, value: float) -> None:
        super().__init__()
        self.value = value

    def forward(self, hidden: torch.Tensor) -> torch.Tensor:
        return hidden + self.value


class FakeEvo2Model(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.tensor(0.0))
        self.blocks = torch.nn.ModuleList([AddValue(1.0), AddValue(2.0)])

    def forward(
        self,
        input_ids: torch.Tensor,
        padding_mask: torch.Tensor | None = None,
    ):
        hidden = input_ids.to(torch.float32).unsqueeze(-1)
        hidden = torch.cat([hidden, hidden * 10], dim=-1)
        for block in self.blocks:
            hidden = block(hidden)
        return hidden


@pytest.mark.parametrize(
    ("specification", "expected"),
    [
        ("all", [0, 1, 2, 3]),
        ("0-2,3", [0, 1, 2, 3]),
        ("3, 1,1", [1, 3]),
    ],
)
def test_parse_layers(specification: str, expected: list[int]) -> None:
    assert workflow.parse_layers(specification, num_layers=4) == expected


@pytest.mark.parametrize(
    ("specification", "message"),
    [
        ("", "No layers"),
        ("3-1", "descending"),
        ("4", "outside"),
        ("-1", "outside"),
    ],
)
def test_parse_layers_rejects_invalid_specifications(
    specification: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        workflow.parse_layers(specification, num_layers=4)


def test_resolve_input_device_uses_requested_device() -> None:
    model = torch.nn.Linear(2, 2)
    assert workflow.resolve_input_device(model, "cpu") == torch.device("cpu")


def test_resolve_input_device_infers_parameter_device() -> None:
    model = torch.nn.Linear(2, 2)
    assert workflow.resolve_input_device(model, None) == next(
        model.parameters()
    ).device


def test_resolve_input_device_rejects_unavailable_cuda(monkeypatch) -> None:
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)

    with pytest.raises(RuntimeError, match="CUDA is unavailable"):
        workflow.resolve_input_device(torch.nn.Linear(2, 2), "cuda:0")


def test_main_extracts_masked_mean_features_and_writes_metadata(
    tmp_path,
    monkeypatch,
) -> None:
    model = FakeEvo2Model()
    loaded = LoadedEvo2(
        wrapper=object(),
        model=model,
        tokenizer=FakeTokenizer(),
        model_name="fake_evo2",
    )
    records = [
        ManifestRecord("first", 1, "train", "ACG", "test", 3),
        ManifestRecord("second", 0, "test", "T", "test", 1),
    ]
    out_dir = tmp_path / "features"

    monkeypatch.setattr(workflow, "read_manifest", lambda _path: records)
    monkeypatch.setattr(
        workflow,
        "load_huggingface_checkpoint",
        lambda **_kwargs: loaded,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "extract_features.py",
            "--manifest",
            "fake-manifest.csv",
            "--model-name",
            "fake_evo2",
            "--out-dir",
            str(out_dir),
            "--input-device",
            "cpu",
            "--batch-size",
            "2",
            "--chunk-size",
            "10",
            "--layers",
            "0-1",
        ],
    )

    workflow.main()

    np.testing.assert_array_equal(np.load(out_dir / "labels.npy"), [1, 0])
    np.testing.assert_array_equal(
        np.load(out_dir / "splits.npy"), ["train", "test"]
    )
    np.testing.assert_array_equal(
        np.load(out_dir / "ids.npy"), ["first", "second"]
    )

    # Padding must not affect the second sequence's pooled representation.
    np.testing.assert_allclose(
        np.load(out_dir / "layer_0" / "chunk_0000.npy"),
        [[3.0, 21.0], [5.0, 41.0]],
    )
    np.testing.assert_allclose(
        np.load(out_dir / "layer_1" / "chunk_0000.npy"),
        [[5.0, 23.0], [7.0, 43.0]],
    )

    metadata = json.loads((out_dir / "metadata.json").read_text())
    assert metadata["model_name"] == "fake_evo2"
    assert metadata["layers"] == [0, 1]
    assert metadata["input_device"] == "cpu"

    # main() must remove its temporary hooks after extraction completes.
    assert all(not block._forward_hooks for block in model.blocks)
