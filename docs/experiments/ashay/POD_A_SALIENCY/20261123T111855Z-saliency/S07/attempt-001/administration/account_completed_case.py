"""One bounded stat witness per completed S07 candidate including restored copies; no payload reads."""
from pathlib import Path
import os,sys,json
from ops import C,A,save,now
sys.path.insert(0,str(A/'code'));from artifact_seals import sha,load,need
alias=sys.argv[1];r=load(C/(alias+'-PRIVATE_RECOVERY_RECEIPT.json'));need(r['status']=='PASS','Only closed protected cases admit immutable accounting');p=C/'COMPLETED_CASE_CAPACITY_WITNESSES.json';w=load(p) if p.exists() else {};h=sha(C/(alias+'-PRIVATE_RECOVERY_RECEIPT.json'))
if alias in w:need(w[alias]['recovery_receipt_sha256']==h,'Changed recovered case invalidates witness');print('REUSED_CLOSED_CASE_CAPACITY_WITNESS',alias,flush=True);raise SystemExit(0)
roots=[A/'candidates'/alias,A/'private-checkpoints'/(alias+'-other-five-probes-001.tar.gz')]+sorted((A/'fresh-consumers').glob(alias+'-*'));count=0;charge=0;device=A.stat().st_dev
for root in roots:
 paths=[root]
 while paths:
  q=paths.pop();need(not q.is_symlink(),'Unexpected owned symlink');s=q.lstat();need(s.st_dev==device,'Unexpected mount');count+=1;need(count<=160000,'Finite owned-case entry limit');charge+=max((s.st_size+4095)//4096*4096,s.st_blocks*512)
  if q.is_dir():
   with os.scandir(q) as scan:paths.extend(Path(e.path) for e in scan)
need(charge<=40*1024**3,'Actual candidate charge exceeds admitted40GiB envelope; readmit before next production');w[alias]={'alias':alias,'entries':count,'conservative_stat_charge_bytes':charge,'admitted_envelope_bytes':40*1024**3,'recovery_receipt_sha256':h,'closed_roots':[str(p) for p in roots],'payload_bytes_read':0,'frozen_after_recovery':True,'observed_utc':now()};save(p,w);print('S07_CLOSED_CASE_CAPACITY_WITNESS',alias,count,charge,flush=True)
