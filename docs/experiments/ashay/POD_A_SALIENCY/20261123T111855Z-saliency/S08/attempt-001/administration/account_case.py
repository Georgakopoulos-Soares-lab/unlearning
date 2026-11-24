"""One bounded stat-only witness for the new owned S08 case and its fresh consumer."""
from pathlib import Path
import os,sys,json
from ops import C,A,save,now
alias=sys.argv[1];cfg=json.loads((C/'RUN_CONFIG.json').read_text());witness=C/'CASE_CAPACITY_WITNESSES.json';old=json.loads(witness.read_text()) if witness.exists() else {}
if alias in old:print('S08_CASE_CAPACITY_WITNESS_REUSED',alias);raise SystemExit(0)
roots=[A/'candidates'/alias,A/'fresh-consumers'/(alias+'-HTTP-001')];entries=0;charge=0
for root in roots:
    assert root.is_dir()
    for d,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(d)/name;assert not p.is_symlink();s=p.lstat();entries+=1;assert entries<=60000;charge+=max(((s.st_size+4095)//4096)*4096,s.st_blocks*512)
archive=A/'private-checkpoints'/(alias+'-S08-001.tar.gz');s=archive.stat();charge+=max(((s.st_size+4095)//4096)*4096,s.st_blocks*512);assert charge<=8*1024**3;old[alias]={'schema_version':'s08-closed-case-capacity-v1','status':'PASS','metadata_entries':entries,'conservative_stat_charge_bytes':charge,'owned_case_envelope_bytes':8*1024**3,'payload_bytes_read_or_rehashed':0,'observed_utc':now()};remaining=json.loads((C/'RESOURCE_ADMISSION.json').read_text())['starting_S07_conservative_remaining_bytes']-sum(x['conservative_stat_charge_bytes'] for x in old.values())-4*1024**3;assert remaining>=64*1024**3;save(witness,old);print('S08_SCOPED_CASE_CAPACITY_PASS',alias,entries,charge,remaining,flush=True)
