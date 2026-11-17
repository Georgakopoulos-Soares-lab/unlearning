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

ENGINEERING = 'ENGINEERING_DIAGNOSTIC'
SCIENTIFIC = 'SCIENTIFIC_QUALIFICATION'

def allowance(state: dict, mode: str, *, now: float | None = None, reserve_reason: str | None = None) -> float:
    require(mode in (ENGINEERING, SCIENTIFIC), 'MODE', mode)
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
                 label: str, env: dict, reserve_reason: str | None = None) -> dict:
    state = json.loads(ledger.read_text())
    # Ledger must live in this continuation, not a historical/shared location.
    require(ledger.resolve().parent == Path(state['limits']['artifact_root']).resolve(), 'LEDGER_PATH', str(ledger))
    locks = []
    for name in ['evo2-pilot.gpu.lock', 'evo2-pilot.gpu-budget.lock']:
        stream = Path('/workspace/meeting-artifacts', name).open('a')
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            stream.close()
            for held in locks: held.close()
            raise
        locks.append(stream)
    started = None; process = None; status = 'FAILED_TO_START'; token = uuid.uuid4().hex
    try:
        shared = json.loads(Path('/workspace/meeting-artifacts/evo2-pilot.gpu-budget.json').read_text())
        require(shared.get('active_since') is None, 'GPU_OWNER_UNRESOLVED', 'Preserve historical active owner')
        state = json.loads(ledger.read_text()); seconds = allowance(state, mode, reserve_reason=reserve_reason)
        require(seconds >= 30, 'BUDGET_EXHAUSTED', 'No stage may start without time for bounded cleanup')
        # Reserve ten seconds inside all ceilings for process-group cleanup.
        env = dict(env, POD_B_LEASE_TOKEN=token, POD_B_LEDGER=str(ledger),
                   POD_B_FORWARD_DEADLINE_EPOCH=str(time.time() + seconds - 10))
        started = time.monotonic()
        state['active'] = dict(controller_pid=os.getpid(), token=token, started_epoch=time.time(),
                               mode=mode, label=label, allowance_seconds=seconds)
        atomic_json(ledger, state)
        with log.open('x') as stream:
            process = subprocess.Popen(command, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            state['active']['worker_pid'] = process.pid; atomic_json(ledger, state)
            try:
                code = process.wait(timeout=seconds-10)
                status = 'EXITED' if code == 0 else 'FAILED'
            except subprocess.TimeoutExpired:
                status = 'TIMEOUT'; code = None
            finally:
                # Also remove any surviving owned descendants after a normal leader exit.
                try: os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError: pass
                if process.poll() is None:
                    try: process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=3)
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
        return dict(status=status, returncode=code, label=label)
    finally:
        if started is not None:
            elapsed = time.monotonic() - started
            current = json.loads(ledger.read_text())
            require(current.get('active', {}).get('token') == token, 'LEASE_CHANGED', 'Do not overwrite foreign accounting')
            current['used_seconds'] += elapsed
            if mode == ENGINEERING: current['engineering_seconds'] += elapsed
            current['stages'].append(dict(label=label, mode=mode, occupied_seconds=elapsed, status=status,
                                         worker_pid=None if process is None else process.pid, reserve_reason=reserve_reason))
            current['active'] = None; atomic_json(ledger, current)
        for stream in locks: stream.close()


def worker_guard() -> None:
    """Called before native construction and every forward. No standalone worker."""
    token = os.environ.get('POD_B_LEASE_TOKEN'); path = os.environ.get('POD_B_LEDGER')
    require(bool(token) and bool(path), 'GPU_LEASE_REQUIRED', 'Run through the budget controller')
    state = json.loads(Path(path).read_text()); active = state.get('active') or {}
    require(active.get('token') == token and active.get('controller_pid') == os.getppid(), 'GPU_LEASE_REQUIRED', 'Stale/foreign owner')
    require(time.time() < float(os.environ['POD_B_FORWARD_DEADLINE_EPOCH']), 'WALL_DEADLINE', 'No new native work beyond deadline')
