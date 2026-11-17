"""Recovery extraction must reject paths/types that could overwrite another member."""
import tarfile

import pytest

from scripts.sayyed.backup_pod_b_qualification import safe_members


def member(name, kind=tarfile.REGTYPE):
    result=tarfile.TarInfo(name)
    result.type=kind
    return result


def test_regular_payload_is_eligible():
    safe_members([member('payload',tarfile.DIRTYPE),member('payload/a')],'payload')


@pytest.mark.parametrize('name',['/payload/a','payload/../outside','other/a','payload\\a',''])
def test_rejects_unsafe_paths(name):
    with pytest.raises(ValueError):
        safe_members([member(name)],'payload')


@pytest.mark.parametrize('kind',[tarfile.SYMTYPE,tarfile.LNKTYPE,tarfile.FIFOTYPE,tarfile.CHRTYPE])
def test_rejects_nonregular_members(kind):
    with pytest.raises(ValueError):
        safe_members([member('payload/a',kind)],'payload')


@pytest.mark.parametrize('second',['payload/a','payload/./a','payload//a'])
def test_rejects_normalized_duplicate_targets(second):
    with pytest.raises(ValueError):
        safe_members([member('payload/a'),member(second)],'payload')
