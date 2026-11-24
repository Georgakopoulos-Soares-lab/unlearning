"""Finite S07 producer validation/protection/publication chain. No S08 dispatch."""
from pathlib import Path
import sys,json
from ops import C,A
from long_run import execute
env_numeric={'PATH':str(Path(json.loads((C/'RUN_CONFIG.json').read_text())['cpu_runtime_python']).parent)+':/usr/bin:/bin','CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'4','OPENBLAS_NUM_THREADS':'4','MKL_NUM_THREADS':'4','PYTHONNOUSERSITE':'1','PYTHONPATH':str(A/'code'),'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'}
alias=sys.argv[1];assert alias in {f'candidate_{i:02d}' for i in range(1,10)};cfg=json.loads((C/'RUN_CONFIG.json').read_text())
for t in cfg['tasks']:assert json.loads((A/'candidates'/alias/'tasks'/t/'GROUP_PRODUCTION.json').read_text())['producer_status']=='PASS'
execute('S07-'+alias+'-producer-validation-001',[cfg['cpu_runtime_python'],str(C/'index_candidate.py'),alias],env_numeric)
execute('S07-'+alias+'-canonical-schema-001',['/usr/local/bin/python3',str(C/'validate_candidate_schema.py'),alias])
execute('S07-'+alias+'-recovery-projections-001',[cfg['cpu_runtime_python'],str(C/'project_recovery_inputs.py'),alias],env_numeric)
execute('S07-'+alias+'-private-protection-001',['/workspace/pod-a-saliency/tools/hf/bin/python',str(C/'protect_candidate.py'),alias,'1'])
execute('S07-'+alias+'-public-records-001',[sys.executable,str(C/'publish_candidate_records.py'),alias])
execute('S07-'+alias+'-resume-001',[sys.executable,str(C/'refresh_resume.py')])
execute('S07-'+alias+'-publication-001',[sys.executable,str(C/'publish_checkpoint.py'),'S07-'+alias+'-001','Protect and publish provisional S07 five-task producer results for '+alias+'; independent S08 release pending'])
print('S07_CANDIDATE_END_TO_END_PRODUCER_COMPLETE_UNVERIFIED',alias,flush=True)
