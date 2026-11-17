"""B04 aggregate occupied-stage accounting, including failures and cleanup.

The controller owns both established GPU locks until its entire child process
group has exited. Charging starts before process creation (conservative CPU
loading/import overhead is charged too) and ends after cleanup, never at the last
forward. Old ledgers are checked and read, never rewritten.
"""
from __future__ import annotations
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid
from .contracts import require
from scripts.sayyed.multiretain_support import atomic_json

SHARED_LEDGER_PATH = Path('/workspace/meeting-artifacts/evo2-pilot.gpu-budget.json')
SHARED_LOCK_ROOT = SHARED_LEDGER_PATH.parent
ENGINEERING = 'ENGINEERING_DIAGNOSTIC'
SCIENTIFIC = 'SCIENTIFIC_QUALIFICATION'

def allowance(state: dict, mode: str, *, now: float | None = None, reserve_reason: str | None = None) -> float:
    require(mode in (ENGINEERING, SCIENTIFIC), 'MODE', mode)
    require(reserve_reason is None or bool(reserve_reason.strip()), 'RESERVE_REASON', 'Empty reserve reason')
    require(state.get('active') is None, 'GPU_OWNER_UNRESOLVED', 'Reconcile recorded owner before any retry')
    limits = state['limits']; used = state['used_seconds']
    require(used >= 0 and state['engineering_seconds'] >= 0, 'BUDGET_CORRUPT', 'Negative usage')
    deadline = dt.datetime.fromisoformat(limits['forward_deadline_utc']).timestamp()
    remaining = min(9000 - used, deadline - (time.time() if now is None else now))
    if not reserve_reason:
        remaining = min(remaining, 7200 - used)
    if mode == ENGINEERING:
        remaining = min(remaining, 1800 - state['engineering_seconds'])
    return max(0., min(1200., remaining))


def run_budgeted(command: list[str], *, ledger: Path, mode: str, log: Path,
                 label: str, env: dict, reserve_reason: str | None = None,
                 execution_plan: dict | None = None) -> dict:
    from .approval import validate_live, verify_runner, reserve_reason as approved_reserve
    require(execution_plan is not None, 'APPROVAL_RECORD', 'Explicit live execution plan required')
    plan=execution_plan
    context=validate_live(plan)
    verify_runner(plan,native=True)
    require(mode==plan['mode'] and ledger.resolve()==Path(plan['ledger_path']).resolve(),
            'APPROVAL_BINDING','Wrong mode or aggregate ledger')
    approved_reserve(plan,reserve_reason)
    locks=[];started=None;process=None;status='FAILED_TO_START';code=None
    event_id=uuid.uuid4().hex;token=uuid.uuid4().hex;start_epoch=None
    try:
        for name in ['evo2-pilot.gpu.lock','evo2-pilot.gpu-budget.lock']:
            stream=(SHARED_LOCK_ROOT/name).open('a')
            try:fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BaseException:stream.close();raise
            locks.append(stream)
        shared=json.loads(SHARED_LEDGER_PATH.read_text())
        require(shared.get('active_since') is None,'GPU_OWNER_UNRESOLVED','Preserve historical owner')
        context=validate_live(plan);state=context['ledger']
        seconds=allowance(state,mode,reserve_reason=reserve_reason)
        if reserve_reason is not None:seconds=min(seconds,plan['reserve']['maximum_gpu_seconds'])
        require(seconds>=30,'BUDGET_EXHAUSTED','Stage plus cleanup must fit')
        env=dict(env,POD_B_LEASE_TOKEN=token,POD_B_LEDGER=str(ledger),
                 POD_B_FORWARD_DEADLINE_EPOCH=str(time.time()+seconds-10),
                 POD_B_EXECUTION_PLAN=context['plan_path'],POD_B_CONTROL_STATE=context['control_path'],
                 POD_B_EXECUTION_EVENT=event_id)
        started=time.monotonic();start_epoch=time.time()
        state['active']=dict(controller_pid=os.getpid(),token=token,started_epoch=start_epoch,
            mode=mode,label=label,allowance_seconds=seconds,event_id=event_id,
            execution_id=plan['execution_id'],plan_sha256=context['plan_sha256'],
            approval_sha256=context['approval_sha256'])
        atomic_json(ledger,state)
        with log.open('x') as stream:
            validate_live(plan);verify_runner(plan,native=True)
            process=subprocess.Popen(command,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,cwd=plan['runner_root'])
            state['active']['worker_pid']=process.pid;atomic_json(ledger,state)
            try:
                code=process.wait(timeout=seconds-10);status='EXITED' if code==0 else 'FAILED'
            except subprocess.TimeoutExpired:status='TIMEOUT'
    finally:
        # This also covers failures writing the worker PID/lease after Popen.
        if process is not None:
            try:os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            if process.poll() is None:
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=3)
            try:os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        if started is not None:
            elapsed=time.monotonic()-started;end_epoch=time.time()
            current=json.loads(ledger.read_text())
            require((current.get('active')or{}).get('token')==token,'LEASE_CHANGED','Foreign accounting')
            current['used_seconds']+=elapsed
            if mode==ENGINEERING:current['engineering_seconds']+=elapsed
            event=dict(label=label,mode=mode,occupied_seconds=elapsed,status=status,
                worker_pid=None if process is None else process.pid,controller_pid=os.getpid(),
                returncode=code,actual_exit_code=None if process is None else (process.returncode if isinstance(process.returncode,int) else code),event_id=event_id,execution_id=plan['execution_id'],
                plan_sha256=context['plan_sha256'],approval_sha256=context['approval_sha256'],
                started_epoch=start_epoch,ended_epoch=end_epoch,reserve_reason=reserve_reason,
                reserve=plan.get('reserve'),command_sha256=__import__('hashlib').sha256(
                    json.dumps(command,separators=(',',':')).encode()).hexdigest())
            current['stages'].append(event);current['active']=None;atomic_json(ledger,current)
            control_path=Path(context['control_path']);control=json.loads(control_path.read_text())
            if control.get('execution_id')==plan['execution_id']:
                control['budget_high_water_used_seconds']=current['used_seconds']
                control['budget_high_water_engineering_seconds']=current['engineering_seconds']
                atomic_json(control_path,control)
        for stream in locks:stream.close()
    return dict(status=status,returncode=code,label=label,event_id=event_id,
                worker_pid=None if process is None else process.pid,controller_pid=os.getpid(),
                execution_id=plan['execution_id'],plan_sha256=context['plan_sha256'],
                approval_sha256=context['approval_sha256'],occupied_seconds=elapsed,
                started_epoch=start_epoch,ended_epoch=end_epoch,reserve_reason=reserve_reason)


def worker_guard() -> dict:
    """Validate current approval/source and actual controller lease at each boundary."""
    from .approval import validate_live,verify_runner
    token=os.environ.get('POD_B_LEASE_TOKEN');path=os.environ.get('POD_B_LEDGER')
    plan_path=os.environ.get('POD_B_EXECUTION_PLAN')
    require(bool(token) and bool(path) and bool(plan_path),'GPU_LEASE_REQUIRED','Use the live budget controller')
    plan=json.loads(Path(plan_path).read_text())
    context=validate_live(plan,control_path=Path(os.environ['POD_B_CONTROL_STATE']))
    verify_runner(plan,native=True);state=context['ledger'];active=state.get('active')or{}
    require(str(Path(path).resolve())==str(Path(plan['ledger_path']).resolve()),'GPU_LEASE_REQUIRED','Wrong ledger')
    require(active.get('token')==token and active.get('controller_pid')==os.getppid()
            and active.get('worker_pid')==os.getpid() and active.get('event_id')==os.environ.get('POD_B_EXECUTION_EVENT')
            and active.get('execution_id')==plan['execution_id'] and active.get('plan_sha256')==context['plan_sha256']
            and active.get('approval_sha256')==context['approval_sha256'],'GPU_LEASE_REQUIRED','Stale or foreign lease')
    require(time.time()<float(os.environ['POD_B_FORWARD_DEADLINE_EPOCH']),'WALL_DEADLINE','No new work beyond lease')
    return {k:active[k] for k in ['event_id','execution_id','worker_pid','controller_pid','plan_sha256','approval_sha256']}
