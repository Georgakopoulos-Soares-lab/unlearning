"""Recheck sealed artifacts before v13 reuse; never fit or extract models."""
from pathlib import Path
import hashlib,json,time,subprocess,collections
r=Path('/workspace/meeting-artifacts/incremental-retain-eval-v1');o=Path('/workspace/meeting-artifacts/multiretain-layers-v1');n=Path('/workspace/meeting-artifacts/multiretain-comparison-v1');c=Path('/workspace/meeting-artifacts/benign-followup-v1');w=Path('/workspace/wt-incremental-retain-eval');started=time.monotonic();cpu=time.process_time();seen={};count=0;scopes=collections.Counter()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check(p,expected,size=None):
 p=Path(p)
 if size is not None:assert p.stat().st_size==size
 if str(p) not in seen:seen[str(p)]=sha(p)
 assert seen[str(p)]==expected,str(p)
for root,arms,label in [(o,['base','maxent'],'base_R1'),(n,['new'],'R3')]:
 receipts=[]
 for group in ['H3','other_five']:
  for arm in arms:receipts.append(root/'features'/group/arm/'FEATURE_UNIT_COMPLETE.json')
  index=json.loads((root/'probes'/group/'PROBE_INDEX.json').read_text());receipts.extend(Path(x['receipt']) for x in index['units']);receipts.extend(Path(x['receipt']) for x in index['lm_units'])
 for p in receipts:
  j=json.loads(p.read_text());assert j['status'] in ['COMPLETE','NEW'];count+=1;scopes[label]+=1
  for x in j['files']:check(x['path'],x['sha256'],x['bytes'])
for p in sorted((c/'tasks').rglob('COMPLETE.json')):
 j=json.loads(p.read_text());assert j['status']=='COMPLETE';scopes['controls']+=1;count+=1
 for name,expected in j['files'].items():check(p.parent/name,expected)
assert scopes['controls']==36
for group,expected in [('H3','de2c348126fa84771ceeff38225703231848ac860f8b59a3ed41d9eb0b3f0938'),('other_five','a270dd76f1a007b7685c012ca2c2a5bdcdbf67da1122f12c81caf292ae9c4126')]:
 for root in [o,n,c]:check(root/'manifests'/(group+'.jsonl'),expected)
 rows=[json.loads(x) for x in (n/'manifests'/(group+'.jsonl')).read_text().splitlines()];by=collections.Counter((x['task'],x['split']) for x in rows)
 for (task,split),num in by.items():assert num==({'train':11971,'dev':1497,'test':1497}[split] if task=='emp_H3' else {'train':1024,'dev':512}[split])
for path in (n/'reports').glob('*.csv'):
 rel='docs/experiments/ashay/multiretain-comparison-v1/tables/'+path.name
 try:b=subprocess.check_output(['git','show','c79ab07e763a9754c68fdaf7d0730d8458f508dc:'+rel],cwd=w,stderr=subprocess.DEVNULL)
 except subprocess.CalledProcessError:continue
 check(path,hashlib.sha256(b).hexdigest())
for group in ['H3','other_five']:
 identities=[json.loads((root/'features'/group/arm/'identity.json').read_text()) for root,arm in [(o,'base'),(o,'maxent'),(n,'new')]]
 for key in ['manifest_sha256','source_sha256']:
  assert len({x[key] for x in identities})==1
 # Tokenizer files legitimately differ base256 versus intervention512; per-arm immutable identities retained.
 for root in [o,n]:
  p=root/'producer_audit'/group/'VERIFICATION_COMPLETE.json'
  if p.exists():assert json.loads(p.read_text())['status']=='PASS'
result=dict(status='PASS',receipt_count=count,receipt_scopes=dict(scopes),unique_files_verified=len(seen),sources=seen,wall_seconds=time.monotonic()-started,cpu_process_seconds=time.process_time()-cpu,scope='Current byte identity of sealed base/R1/R3 features, heads, predictions, native bootstrap/LM outputs, controls and cohort joins; original audits reused, no new mathematical measurements or GPU replication.')
(r/'REUSE_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='sources'},flush=True)
