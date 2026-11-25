from pathlib import Path
import json,hashlib,os,datetime
RUN='20261123T111855Z-saliency';BASE=Path('/workspace/pod-a-saliency');R=BASE/'research-POD_A_SALIENCY';T=R/'docs/experiments/ashay/POD_A_SALIENCY'/RUN
C=BASE/'control'/RUN/'S10/attempt-002';A=BASE/'artifacts'/RUN/'S10/attempt-002';P=T/'S10/attempt-002'
PACKAGE='7007ebd05bf59432bf69109e5f69baad31ec0d3a';SUPPLEMENT='586afb0911a092e2fb7b020b65e0ee32057f71b6';SUPP_SHA='b33fb24547156cdfed9c24796668120b43f9e4a3a7167e929c2ff4ef359de494';PACKAGE_SHA='3b089d6b7d7ab16812272a500519db269050c855f0a0f29e3333752d9a62a5e9';PRIOR='092cd2ea0b48cb8612dd978dce8498b93f4b5302'
PKG=BASE/'control'/RUN/'ADMIN/part-a-001/verified-published-package'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.partial-'+str(os.getpid()));tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');os.replace(tmp,p)
def textfile(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.partial-'+str(os.getpid()));tmp.write_text(x);os.replace(tmp,p)
def progress(state,next_action,**values):
 v=read(C/'RESUME_MANIFEST.json') if (C/'RESUME_MANIFEST.json').exists() else {'run_id':RUN,'phase':'S10','attempt_id':'attempt-002','canonical_package_commit':PACKAGE,'supplement_commit':SUPPLEMENT,'supplement_sha256':SUPP_SHA}
 v.update(status=state,next_permitted_action=next_action,updated_utc=now(),**values);save(C/'RESUME_MANIFEST.json',v)
 with (C/'EVENTS.jsonl').open('a') as f:f.write(json.dumps({'utc':now(),'state':state,'next_action':next_action,**values})+'\n')
