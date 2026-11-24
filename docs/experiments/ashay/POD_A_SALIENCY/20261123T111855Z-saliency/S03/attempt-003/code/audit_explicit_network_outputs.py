"""Finite immutable private-output network audit, then restored CPU checks; no GPU work."""
from pathlib import Path
import json,sys
from ops import C,A,run,save,now
from long_run import execute
hf='/workspace/pod-a-saliency/tools/hf/bin/python';cpu=str(A.with_name('attempt-001')/'cpu-reference-runtime/bin/python');aliases=sys.argv[1:];assert aliases and len(aliases)==len(set(aliases)) and set(aliases)<={f'candidate_{i:02d}' for i in range(2,10)}
for alias in aliases:
 http=C/(alias+'-HTTP_READBACK_RECEIPT.json')
 if not http.exists():execute('explicit-network-'+alias+'-001',[hf,str(C/'explicit_network_readback.py'),alias])
 r=json.loads(http.read_text());assert r['status']=='EXPLICIT_HTTP_NETWORK_EXACT_MEMBER_RESTORE_PASS' and r['file_or_Xet_cache_used'] is False and r['HTTP_body_bytes_received']==r['archive_bytes'];out=C/(alias+'-HTTP_RESTORED_CPU_REPLAY.json')
 if not out.exists():run('explicit-HTTP-CPU-replay-'+alias+'-001',[cpu,str(C/'verify_candidate_numeric.py'),alias,r['restored_root'],'HTTP_RESTORED_CPU_REPLAY'])
 assert json.loads(out.read_text())['status']=='PASS';print('EXPLICIT_PRIVATE_NETWORK_AND_CPU_PROOF_PASS',alias,flush=True)
print('FINITE_EXPLICIT_NETWORK_OUTPUT_AUDIT_DRAINED',len(aliases),flush=True)
