"""A09 typed, atomic reporting primitives; no numerical production dispatch."""
from pathlib import Path
import csv,datetime,hashlib,json,os,subprocess,sys
C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A09-attempt-001');cfg=json.loads((C/'RUN_CONFIG.json').read_text());R=Path(cfg['root_control']);A=Path(cfg['artifacts']);D=Path(cfg['docs']);W=Path(cfg['worktree']);BASE=D.parent.parent;D8=D.parent/'A08-attempt-001';C8=C.parent/'A08-attempt-001';A8=A.parent/'A08-attempt-001';REC=Path(cfg['recovery']);REPO='ashay-sriv/undo-evo2-pilot-backup-20261020'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def ref(p):
 p=Path(p);return {'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)}
def atomic(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name('.'+p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def put(p,v):
 if not isinstance(v,(dict,list)):raise TypeError('JSON writer accepts objects/arrays only; Markdown must use write_md')
 atomic(p,(json.dumps(v,indent=2,allow_nan=False)+'\n').encode())
def write_md(p,text):
 if not isinstance(text,str) or not text.startswith('# ') or '\n' not in text:raise TypeError('Expected plain Markdown document with real newlines')
 atomic(p,(text.rstrip()+'\n').encode('utf-8'))
def git(*args):return subprocess.check_output(['git','-C',str(W),*args],text=True).strip()
def rows(p):return list(csv.DictReader(Path(p).open()))
def publish(name,data):
 from research_guard import guard
 guard(allow_dirty=True);p=D/name;assert p.resolve().is_relative_to(D.resolve())
 if p.suffix=='.md':write_md(p,data.decode() if isinstance(data,bytes) else data)
 elif isinstance(data,bytes):atomic(p,data)
 elif isinstance(data,str):atomic(p,data.encode())
 else:put(p,data)
def table(name,data,fields=None):
 from research_guard import guard
 guard(allow_dirty=True);p=D/name;p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name('.'+p.name+'.tmp')
 with t.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields or list(data[0]),lineterminator='\n');w.writeheader();w.writerows(data)
 os.replace(t,p)
