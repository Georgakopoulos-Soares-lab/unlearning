import pytest
from benign_pilot.retain import prepare, identity


def fixture():
    return [dict(task='gue_emp_h3', split='train', id=str(i), dataset_source='synthetic-v1', sequence=s)
            for i, s in enumerate(['AAAA', 'AAAC', 'AACC'])]


def test_determinism_accounting_and_shortfall():
    a, report = prepare(fixture(), {'gue_emp_h3': 9})
    assert (a, report) == prepare(list(reversed(fixture())), {'gue_emp_h3': 9})
    assert report['tasks']['gue_emp_h3']['processed'] == 8
    assert report['tasks']['gue_emp_h3']['shortfall'] == 1
    assert len(a) == 2


def test_contamination_and_duplicates():
    rows = fixture()
    with pytest.raises(ValueError):
        prepare(rows, {'gue_emp_h3': 9}, heldout_hashes=[identity('TTTT')])
    with pytest.raises(ValueError):
        prepare(rows + rows[:1], {'gue_emp_h3': 9})
    rows[0]['split'] = 'validation'
    with pytest.raises(ValueError):
        prepare(rows, {'gue_emp_h3': 9})


def test_fail_closed():
    for budgets in ({'viral': 10}, {'gue_emp_h3': -1}, {'gue_emp_h3': True}):
        with pytest.raises(ValueError):
            prepare(fixture(), budgets)
    rows = fixture()
    del rows[0]['dataset_source']
    with pytest.raises(ValueError):
        prepare(rows, {'gue_emp_h3': 9})
