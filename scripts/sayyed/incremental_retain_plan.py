"""Meeting-defined retain stages; aliases never establish realized exposure."""

TASKS = (
    'emp_H3', 'gue_tf_0', 'gue_prom_core_all', 'gue_prom_300_all',
    'gue_splice_reconstructed', 'gue_mouse_0',
)
STAGES = {f'R{i}': TASKS[:i] for i in range(1, 7)}
STATUSES = ('evaluated', 'available-unqualified', 'eligible', 'running',
            'complete', 'failed', 'awaiting-delivery')


def meeting_role(stage, task):
    """Describe the agreed plan, independently of delivered data or exposure."""
    if task not in TASKS:
        raise ValueError('Unknown qualified task')
    if stage == 'base':
        return 'separate-pretrained-reference'
    members = STAGES[stage]
    if task == members[-1]:
        return 'newly-included-in-plan'
    if task in members:
        return 'already-included-in-plan'
    return 'not-yet-included-in-plan'


def adjacent_status(previous, current, available):
    """Require the immediately preceding meeting stage, without interpolation."""
    keys = list(STAGES)
    if previous not in keys or current not in keys or keys.index(current) != keys.index(previous) + 1:
        raise ValueError('Not adjacent retain stages')
    missing = [x for x in (previous, current) if x not in available]
    return dict(previous=previous, current=current,
                status='available' if not missing else 'awaiting-delivery',
                missing=missing)


def declared_membership(stage, task, declared):
    """Keep absent artifact declarations unknown, even when the plan is known."""
    if stage == 'base':
        return 'no-intervention-retain-declaration'
    if stage not in declared:
        return 'unresolved-no-checkpoint'
    return 'included-in-config' if task in declared[stage] else 'not-in-config'
