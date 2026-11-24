from pathlib import Path
import json, hashlib, os, datetime
RUN='20261123T111855Z-saliency'
B=Path('/workspace/pod-a-saliency'); R=B/'research-POD_A_SALIENCY'; T=R/'docs/experiments/ashay/POD_A_SALIENCY'/RUN
C=B/'control'/RUN/'S09/attempt-001'; A=B/'artifacts'/RUN/'S09/attempt-001'; P=T/'S09/attempt-001'
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']
REPS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm']; SEEDS=[42,17,1234]; POLICIES=['independent_refit','fixed_original_base']
METRICS=['AUROC','AP','accuracy','balanced_accuracy','cross_entropy']; MAP=dict(zip(METRICS,['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy']))
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.partial-'+str(os.getpid()));tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');os.replace(tmp,p)
def jsonl(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.partial-'+str(os.getpid()));tmp.write_text(''.join(json.dumps(v,separators=(',',':'),allow_nan=False)+'\n' for v in x));os.replace(tmp,p)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def key(r):return 'final_norm' if r==REPS[-1] else 'decoder_layer_'+r.rsplit('.',1)[1]
def stage(p):return B/'artifacts'/RUN/p
def control(p):return B/'control'/RUN/p
def public(p):return T/p
def progress(status,**kw):
 v=read(C/'RESUME_MANIFEST.json');v.update(status=status,updated_utc=now(),**kw);save(C/'RESUME_MANIFEST.json',v)
 with (C/'EVENTS.jsonl').open('a') as f:f.write(json.dumps(dict(status=status,utc=now(),**kw))+'\n')
