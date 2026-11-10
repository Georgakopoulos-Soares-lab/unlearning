import json
import math
import tarfile
from types import SimpleNamespace
import pytest
import torch
from scripts.sayyed.multiretain_support import remaining_seconds, SessionBudget, layer_specs, pooled_activation
from scripts.sayyed.recover_multiretain import validate_members


def test_uncapped_and_finite_authorization():
    assert math.isinf(remaining_seconds(None, 9000))
    assert remaining_seconds(100, 40) == 60
    assert remaining_seconds(0, 0) == 0
    for bad in (-1, float('nan'), True, 'uncapped'):
        with pytest.raises(ValueError):
            remaining_seconds(bad, 0)


def test_session_budget_requires_identity_and_inactive_ledger(tmp_path):
    import hashlib
    config = tmp_path / 'config.json'
    config.write_text(json.dumps(dict(AUTHORIZED_GPU_STAGE_SECONDS=None, AUTHORIZED_RENTAL_WALL_MINUTES=None)))
    path = tmp_path / 'ledger.json'
    state = dict(effective_config_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
                 used_seconds=0, session_started_epoch=0, active_since=None)
    path.write_text(json.dumps(state))
    budget = SessionBudget(path, config)
    assert math.isinf(budget.read())
    budget.begin()
    with pytest.raises(ValueError, match='active'):
        budget.read()
    budget.end()
    assert json.loads(path.read_text())['used_seconds'] >= 0
    config.write_text('{}')
    with pytest.raises(ValueError, match='configuration changed'):
        budget.read()


def test_missing_authorization_rejected(tmp_path):
    config = tmp_path / 'config.json'
    config.write_text('{}')
    with pytest.raises(ValueError, match='Missing explicit authorization'):
        SessionBudget(tmp_path / 'ledger.json', config)


def test_all_hooks_and_padding_pooling():
    model = SimpleNamespace(decoder=SimpleNamespace(layers=list(range(25)), final_norm='norm'))
    specs = layer_specs(model)
    assert len(specs) == 26
    assert specs[16][:2] == ('decoder_layer_16', 'decoder.layers.16')
    hidden = torch.tensor([[[1., 3.]], [[3., 5.]], [[999., 999.]]])
    assert torch.equal(pooled_activation(hidden, torch.tensor([2]), 2), torch.tensor([[2., 4.]]))
    with pytest.raises(ValueError, match='lengths'):
        pooled_activation(hidden, torch.tensor([0]), 2)
    hidden[0, 0, 0] = float('nan')
    with pytest.raises(ValueError, match='Nonfinite'):
        pooled_activation(hidden, torch.tensor([2]), 2)


@pytest.mark.parametrize('name,kind', [('../escape', tarfile.REGTYPE),
    ('/absolute', tarfile.REGTYPE), ('maxent-benign-v16/link', tarfile.SYMTYPE),
    ('other/file', tarfile.REGTYPE)])
def test_unsafe_recovery_member_rejected(name, kind):
    member = tarfile.TarInfo(name)
    member.type = kind
    with pytest.raises(ValueError, match='Unsafe'):
        validate_members([member])
