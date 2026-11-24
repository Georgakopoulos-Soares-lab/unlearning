"""Explicit finite remaining eight-candidate S06 queue. Stops on error and never dispatches S07."""
from pathlib import Path
import sys,json
from ops import C,A
from long_run import execute
cfg=json.loads((C/'RUN_CONFIG.json').read_text());assert len(cfg['candidates'])==9
for v in cfg['candidates'][1:]:
 alias=v['alias'];gate=Path(cfg['research_run_root'])/'S06/attempt-001/candidates'/alias/'S06_GATE.json'
 assert not gate.exists(),'Reconcile existing exact completion before scheduling; never duplicate work'
 execute('S06-'+alias+'-GPU-chain-001',[sys.executable,str(C/'run_candidate_stage.py'),alias,'GPU'])
 execute('S06-'+alias+'-finish-chain-001',[sys.executable,str(C/'finish_candidate.py'),alias])
print('S06_FINITE_NINE_CANDIDATE_PRODUCTION_PROTECTION_PUBLICATION_DRAINED_STOP_BEFORE_S07',flush=True)
