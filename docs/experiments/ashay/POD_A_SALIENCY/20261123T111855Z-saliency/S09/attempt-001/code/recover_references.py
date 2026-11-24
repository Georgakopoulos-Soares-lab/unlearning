"""Only exact frozen DEV prediction members; reuse existing verified local archives."""
from s09_common import *
import tarfile,time
from pathlib import PurePosixPath
reuse=read(public('S04/attempt-001/REUSE_MAP.json')); bindings=reuse['base_prediction_endpoints']+reuse['control_prediction_endpoints']; assert len(bindings)==504
index={digest(v):v for v in bindings}; assert len(index)==504
spec=rows(C/'FROZEN_ADMITTED_KEYS.jsonl');assert {s['q'] for s in spec if s['f']!='anchor_policy_gap'}==set(index)
save(C/'REFERENCE_RECOVERY_PLAN.json',{'status':'ADMITTED','members':504,'selected_bytes':sum(v['bytes'] for v in bindings),'local_archives_already_verified_in_S03':True,'full_archive_rehash':False,'sequential_gzip_member_selection_required':True,'no_test_members_or_native_weights_materialized':True,'frozen_reference_ids':list(index),'started_utc':now()})
receipts=[]
for archive_id in ['historical-archive-001','historical-archive-002']:
 wanted={v['archive_member']:v for v in bindings if v['archive_id']==archive_id}; dest=A/'reference-predictions'/archive_id; dest.mkdir(parents=True,exist_ok=True)
 completed=set()
 for n,v in wanted.items():
  p=dest/(digest(v)+'.npz')
  if p.exists():assert p.stat().st_size==v['bytes'] and sha(p)==v['sha256'];completed.add(n)
 if len(completed)<len(wanted):
  archive=stage('S03/attempt-001/minimum-archives')/(archive_id+'.tar.gz');last=time.monotonic();seen=set();expanded=0
  with tarfile.open(archive,'r|gz') as tar:
   for m in tar:
    q=PurePosixPath(m.name); assert not q.is_absolute() and '..' not in q.parts and '\\' not in m.name and m.name not in seen;seen.add(m.name);assert m.isfile() or m.isdir();expanded+=m.size;assert expanded<40*1024**3
    logical=m.name.removeprefix('multiretain-layers-v1-final-20261110T140836Z/') if archive_id=='historical-archive-001' else m.name
    if logical in wanted and logical not in completed:
     v=wanted[logical]; assert m.isfile() and m.size==v['bytes'];b=tar.extractfile(m).read(); assert len(b)==v['bytes'] and hashlib.sha256(b).hexdigest()==v['sha256'];p=dest/(digest(v)+'.npz');temp=p.with_suffix('.partial');temp.write_bytes(b);os.replace(temp,p);completed.add(logical)
    if time.monotonic()-last>15:print(archive_id,'recovered',len(completed),'/',len(wanted),'stream_expanded',expanded,flush=True);last=time.monotonic()
    if len(completed)==len(wanted):break
 assert set(wanted)==completed
 for n,v in wanted.items():receipts.append({'reference_id':digest(v),'frozen_binding':v,'relative_path':str((dest/(digest(v)+'.npz')).relative_to(A)),'sha256':v['sha256'],'bytes':v['bytes']})
 print('RECOVERED_EXACT_REFERENCE_MEMBERS',archive_id,len(completed),flush=True)
save(C/'REFERENCE_RECOVERY_RECEIPT.json',{'status':'PASS','members':receipts,'model_downloads':0,'new_network_bytes':0,'full_archive_rehash':False,'completed_utc':now()});progress('REFERENCE_MEMBERS_RECOVERED',reference_prediction_members=504)
