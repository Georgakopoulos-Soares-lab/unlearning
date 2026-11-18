"""Exact direct-request, R5-only CPU ownership guard; no side effects/model imports."""
from pathlib import Path
import json,hashlib
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A07-attempt-002');PIN='112bd37081f5e55896057c6046195e8603c5e751';PLAN='06d290bdc76404a8dcfe25da6f057fc78f868364cc1d2e8aa6df77791f0bdfa3';MODEL='9cab388a46a873902317ff022ab0b9a43d3e42c8753d3842837f74f5dd474259'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(v,s):
 if not v:raise ValueError(s)
def authorize():
 cfg=read(C/'RUN_CONFIG.json');ap=read(C/'APPROVAL_RECORD.json');inp=read(C/'A07_INPUTS.json');require(cfg['stage']==ap['stage']=='A07' and cfg['attempt_id']==ap['attempt_id']=='A07-attempt-002','Wrong stage/attempt');require(cfg['prompt_commit']==ap['prompt_commit']==PIN and cfg['coverage_plan_sha256']==ap['coverage_plan_sha256']==PLAN,'Wrong prompt/plan');require(ap['direct_user_message'].endswith('/a07_v2.md') and sha(C/'APPROVAL_RECORD.json')==inp['approval_sha256'],'No matching direct execution request');require(inp['approved_model']['model_tensor_content_sha256']==MODEL,'Wrong R5 model identity');require(Path(cfg['artifacts']).resolve()==Path('/workspace/meeting-artifacts/POD_A/20261117T084728Z-a01/A07-attempt-002'),'Historical write-root escape');return True
