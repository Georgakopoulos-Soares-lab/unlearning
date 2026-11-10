import numpy as np
import pytest
from benign_pilot.extension import controls

def test_ambiguity_denominators_and_padding_exclusion():
    result=controls(['AAAAN'])
    np.testing.assert_array_equal(result['composition'],[[1,0,0,0]])
    assert result['4mer'][0,0]==1 and result['4mer'].sum()==1

def test_forward_orientation_is_not_reverse_complement_aggregation():
    result=controls(['AAAAC','GTTTT'])['4mer']
    assert np.count_nonzero(result[0])==2
    assert not np.array_equal(result[0],result[1])
    np.testing.assert_array_equal(result.sum(1),[1,1])

def test_undefined_denominator_rejected():
    with pytest.raises(ValueError):controls(['NNNN'])
    with pytest.raises(ValueError):controls(['ACG'])
