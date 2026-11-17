"""Live B04 approval, immutable plan/source identity and inherited ledger checks.

Metadata inspection is separate from permission to execute. No native libraries
are imported here. The control record can revoke a running worker at each safe
boundary; a known historical prompt digest is never a standing approval.
"""
from __future__ import annotations
import datetime as dt
import json
import math
import re
import sys
import time
from pathlib import Path
from .contracts import canonical_sha, file_sha, require, verify_file

APPROVED_FIXTURE_SHA='42d64d32b77e946bc962c32d2b801e485d41a095221af49a492079ff0f76fd30'
APPROVED_IDS_SHA='1800b51b5262a453820797b1c42e7e99ca1788bd6d2aca4c77c886b053436ba8'
CURRENT_CONTROL_PATH = Path('/workspace/agent-handoff/POD_B/STATE.json')
NATIVE_MODES = ('ENGINEERING_DIAGNOSTIC', 'SCIENTIFIC_QUALIFICATION')
RUNNER_MODULES = tuple('scripts.sayyed.pod_b_runtime.'+n for n in
                       ('approval','budget','modes','native','qualification','finalize','contracts','gate')) + (
    'scripts.sayyed.fixed_benign_batch','scripts.sayyed.multiretain_support','scripts.sayyed.check_benign_checkpoint_pair')


def ledger_identity(path: Path, state: dict) -> str:
    return canonical_sha(dict(path=str(path.resolve()), schema=state['schema'],
                              limits=state['limits'], prior_B04_seconds=state.get('prior_B04_seconds',0)))


def check_ledger(plan: dict, approval: dict, control: dict) -> dict:
    path=Path(plan['ledger_path']); state=json.loads(path.read_text())
    require(ledger_identity(path,state)==approval['ledger_identity']==control.get('ledger_identity')==plan['ledger_identity'],
            'LEDGER_IDENTITY','Changed ledger or immutable limits')
    used,engineering=state['used_seconds'],state['engineering_seconds']
    require(all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 for v in (used,engineering)),
            'BUDGET_CORRUPT','Nonfinite/negative usage')
    require(used>=max(approval['minimum_used_seconds'],control.get('budget_high_water_used_seconds',0))
            and engineering>=max(approval['minimum_engineering_seconds'],control.get('budget_high_water_engineering_seconds',0)),
            'BUDGET_RESET','Previously charged usage cannot be reset')
    count=approval['inherited_stage_count']
    require(len(state['stages'])>=count and canonical_sha(state['stages'][:count])==approval['inherited_stages_sha256'],
            'BUDGET_RESET','Inherited attempts changed or disappeared')
    measured=state.get('prior_B04_seconds',0)+sum(s['occupied_seconds'] for s in state['stages'])
    eng=sum(s['occupied_seconds'] for s in state['stages'] if s['mode']=='ENGINEERING_DIAGNOSTIC')
    require(abs(used-measured)<1e-6 and abs(engineering-eng)<1e-6,'BUDGET_CORRUPT','Counters disagree with preserved event history')
    require(state['limits']['forward_deadline_utc']==approval['forward_deadline_utc']==plan['forward_deadline_utc'],
            'DEADLINE_CHANGED','Forward deadline is inherited, not restarted')
    return state


def validate_live(plan: dict, *, control_path: Path | None=None, now: float | None=None,
                  native: bool=True) -> dict:
    control_path=Path(control_path or CURRENT_CONTROL_PATH)
    require(control_path.resolve()==CURRENT_CONTROL_PATH.resolve() and plan.get('control_state_path')==str(control_path),
            'APPROVAL_CONTROL','Use the actual current control record, not a plan-selected substitute')
    control=json.loads(control_path.read_text())
    require(control.get('stage')=='B04' and control.get('status')=='RUNNING',
            'STAGE_NOT_AUTHORIZED','B04 must have a current RUNNING approval')
    require(plan.get('synthetic_contract_test') is not True,'SYNTHETIC_NOT_SCIENCE','Disposable CPU fixtures never authorize native execution')
    require(plan.get('stage')=='B04' and control.get('execution_id')==plan.get('execution_id') and bool(plan.get('execution_id')),
            'EXECUTION_ID','Wrong stage or stale execution')
    root=Path(plan['artifact_root']).resolve()
    require(control.get('artifact_root')==str(root),'APPROVAL_ROOT','Unapproved output root')
    record=control.get('approval_record')
    require(isinstance(record,dict),'APPROVAL_RECORD','Direct approval record required')
    approval=json.loads(verify_file(record,roots=[str(root)]).read_text())
    require(approval.get('stage')=='B04' and approval.get('execution_id')==plan['execution_id']
            and bool(approval.get('direct_user_approval')),'APPROVAL_RECORD','Missing direct approval or stale record')
    digest=canonical_sha(plan)
    require(digest==control.get('execution_plan_sha256')==approval.get('execution_plan_sha256'),
            'PLAN_CHANGED','Execution plan bytes/content no longer match approval')
    plan_path=Path(control['execution_plan_path'])
    require(canonical_sha(json.loads(plan_path.read_text()))==digest,'PLAN_CHANGED','Changed plan on disk')
    require(approval.get('approved_prompt_sha256')==plan.get('approved_prompt_sha256')==control.get('approved_prompt_sha256')
            and re.fullmatch('[0-9a-f]{64}',str(plan.get('approved_prompt_sha256',''))) is not None,
            'APPROVAL_VERSION','Wrong prompt revision')
    require(plan['mode'] in approval['permitted_modes'] and control.get('permitted_modes')==approval['permitted_modes'],
            'APPROVAL_MODE','Mode not approved')
    if native:
        require(plan['mode'] in NATIVE_MODES,'APPROVAL_MODE','CPU remediation does not authorize a native launch')
        require(plan.get('inputs',{}).get('fixture_sha256')==APPROVED_FIXTURE_SHA
                and plan['inputs'].get('ordered_ids_sha256')==APPROVED_IDS_SHA,'FIXTURE_APPROVAL','Only the approved fixed training fixture may execute')
    for key in ('artifact_root','ledger_path','ledger_identity','forward_deadline_utc','closure_deadline_utc'):
        require(plan.get(key)==approval.get(key)==control.get(key),'APPROVAL_BINDING',key)
    require(not plan.get('reset_budget') and not plan.get('reset_counters') and plan.get('next_stage_authorized') is False,
            'BUDGET_RESET','No counter reset or next-stage queue')
    cutoff=approval['forward_deadline_utc'] if native else approval['closure_deadline_utc']
    require((time.time() if now is None else now)<dt.datetime.fromisoformat(cutoff).timestamp(),
            'WALL_DEADLINE','Fixed approval deadline has passed')
    state=check_ledger(plan,approval,control)
    if native:
        remaining=9000-state['used_seconds']
        if plan['mode']=='ENGINEERING_DIAGNOSTIC':remaining=min(remaining,1800-state['engineering_seconds'])
        require(remaining>=30,'BUDGET_EXHAUSTED','No useful native stage plus cleanup fits')
    return dict(approval=approval,approval_sha256=record['sha256'],plan_sha256=digest,
                control=control,control_path=str(control_path),plan_path=str(plan_path),ledger=state)


def verify_runner(plan: dict, *, native: bool=False) -> dict:
    """Hash declared files and check actual origins of already imported modules."""
    manifest=json.loads(verify_file(plan['runner_manifest'],roots=[plan['artifact_root']]).read_text())
    entries=manifest.get('modules',{})
    require(set(RUNNER_MODULES)<=set(entries),'RUNNER_MANIFEST','Missing actual runner/backend source')
    for name,record in entries.items():
        path=verify_file(record,roots=manifest['allowed_source_roots'])
        module=sys.modules.get(name)
        main=sys.modules.get('__main__')
        if module is None and getattr(getattr(main,'__spec__',None),'name',None)==name:module=main
        if module is not None:
            require(Path(module.__file__).resolve()==path.resolve(),'MODULE_ORIGIN',name)
    require(all(Path(entries[name]['path']).resolve().is_relative_to(Path(plan['runner_root']).resolve()) for name in RUNNER_MODULES),
            'RUNNER_MANIFEST','Runner/helpers must be inside the declared frozen runner root')
    environment=verify_file(plan['environment_lock'],roots=plan['allowed_read_roots'])
    require(file_sha(environment)==plan['environment_lock_sha256'],'RUNTIME_HASH','Environment lock changed')
    if native:
        require(sys.prefix==plan['runtime_prefix'],'RUNTIME_ORIGIN','Use the explicitly pinned isolated interpreter')
        for name,record in manifest.get('runtime_modules',{}).items():
            path=verify_file(record,roots=manifest['allowed_source_roots'])
            module=sys.modules.get(name)
            if module is not None:require(Path(module.__file__).resolve()==path.resolve(),'MODULE_ORIGIN',name)
    return manifest


def reserve_reason(plan: dict, cli_reason: str | None) -> str | None:
    reserve=plan.get('reserve')
    if cli_reason is None:
        require(reserve is None,'RESERVE_NOT_CONFIRMED','Pass the exact approved --reserve-reason to use a reserve plan')
        return None
    require(isinstance(cli_reason,str) and len(cli_reason.strip())>=16,'RESERVE_REASON','Concrete nonempty bounded repair/completion reason required')
    require(isinstance(reserve,dict) and cli_reason==reserve.get('reason')
            and reserve.get('purpose') in ('repair','completion'),'RESERVE_NOT_APPROVED','CLI reason must match the immutable plan')
    require(isinstance(reserve.get('maximum_gpu_seconds'),(float,int)) and not isinstance(reserve.get('maximum_gpu_seconds'),bool) and 0<reserve['maximum_gpu_seconds']<=1800,
            'RESERVE_BOUND','Reserve must have a finite bounded allocation')
    verify_file(reserve['evidence_record'],roots=plan['allowed_read_roots'])
    return cli_reason
