"""Persist the cumulative GPU-job budget across stages and attempts."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

BUDGET_PATH = Path('/workspace/meeting-artifacts/evo2-pilot.gpu-budget.json')
LIMIT_SECONDS = 7200


def update(action, path=BUDGET_PATH, now=None):
    now = now or datetime.now(timezone.utc)
    state = json.loads(path.read_text()) if path.exists() else dict(used_seconds=0., limit_seconds=LIMIT_SECONDS)
    if state.get('active_since'):
        state['used_seconds'] += max(0., (now-datetime.fromisoformat(state['active_since'])).total_seconds())
    state['active_since'] = now.isoformat() if action == 'begin' else None
    state['updated_utc'] = now.isoformat()
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(state,indent=2))
    temporary.replace(path)
    return max(0, int(state['limit_seconds']-state['used_seconds']))


if __name__ == '__main__':
    print(update(sys.argv[1]))
