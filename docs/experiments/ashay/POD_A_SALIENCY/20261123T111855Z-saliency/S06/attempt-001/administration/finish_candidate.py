"""Finite S06 candidate finish only; no later-stage dispatch."""
from pathlib import Path
import os,sys,json
from ops import C,A,save,now
from long_run import execute
alias=sys.argv[1];assert alias in {f'candidate_{i:02d}' for i in range(1,10)};g=json.loads((C/('S06-GPU-'+alias+'-001-PROGRESS.json')).read_text());assert g['status']=='COMPLETE' and g['exit_status']==0
for stage in ['LM','verify']:execute('S06-'+alias+'-'+stage+'-chain-001',[sys.executable,str(C/'run_candidate_stage.py'),alias,stage])
execute('S06-'+alias+'-exact-index-001',[sys.executable,str(C/'index_candidate.py'),alias])
execute('S06-'+alias+'-private-protection-001',['/workspace/pod-a-saliency/tools/hf/bin/python',str(C/'protect_candidate.py'),alias,'1'])
execute('S06-'+alias+'-release-001',[sys.executable,str(C/'release_candidate.py'),alias])
execute('S06-'+alias+'-resume-001',[sys.executable,str(C/'refresh_resume.py')])
execute('S06-'+alias+'-publication-001',[sys.executable,str(C/'publish_checkpoint.py'),'S06-'+alias+'-001','Release verified recoverable S06 other-five '+alias+' with exact frozen keys'])
print('S06_CANDIDATE_END_TO_END_COMPLETE',alias,flush=True)
