from pathlib import Path
import csv,datetime,hashlib,json,os,subprocess,sys
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A07-attempt-001');cfg=json.loads((C/'RUN_CONFIG.json').read_text());A=Path(cfg['artifacts']);D=Path(cfg['docs']);W=Path(cfg['worktree']);R=Path(cfg['root_control']);BASE=D.parent.parent;C02=R/'attempts/A04-attempt-002';C03=R/'attempts/A03-attempt-001';C05=R/'attempts/A05-attempt-001';D05=BASE/'attempts/A05-attempt-001';A02=A.parent/'A04-attempt-002';H=Path('/workspace/recovery/POD_A')/R.name/'A03-attempt-001/restored/base_R1/multiretain-layers-v1-final-20261110T140836Z'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name('.'+p.name+'.tmp');t.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');os.replace(t,p)
def ref(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
def csvwrite(p,rows):
 with Path(p).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def publish(name,data):
 from research_guard import guard
 guard(allow_dirty=True);p=D/name;assert p.resolve().is_relative_to(D.resolve());p.parent.mkdir(parents=True,exist_ok=True)
 if isinstance(data,str):p.write_text(data)
 elif isinstance(data,bytes):p.write_bytes(data)
 else:put(p,data)
# Consistent descriptive alias used by orchestration/report modules.
publish_file=publish
