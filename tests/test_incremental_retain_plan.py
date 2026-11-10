import pytest
from scripts.sayyed.incremental_retain_plan import (
    STAGES, TASKS, adjacent_status, declared_membership, meeting_role,
)


def test_meeting_order_and_missing_declaration_remain_separate():
    assert STAGES['R2'] == ('emp_H3', 'gue_tf_0')
    assert STAGES['R3'] == ('emp_H3', 'gue_tf_0', 'gue_prom_core_all')
    assert STAGES['R6'] == TASKS
    assert meeting_role('R3', 'gue_prom_core_all') == 'newly-included-in-plan'
    assert meeting_role('R3', 'gue_tf_0') == 'already-included-in-plan'
    assert declared_membership('R2', 'emp_H3', {'R1': STAGES['R1']}) == 'unresolved-no-checkpoint'


def test_nonadjacent_observation_cannot_be_promoted_to_adjacent_effect():
    with pytest.raises(ValueError, match='Not adjacent'):
        adjacent_status('R1', 'R3', {'R1', 'R3'})
    assert adjacent_status('R2', 'R3', {'R1', 'R3'})['missing'] == ['R2']
    assert adjacent_status('R3', 'R4', {'R1', 'R3'})['missing'] == ['R4']
    assert adjacent_status('R2', 'R3', {'R2', 'R3'})['status'] == 'available'
