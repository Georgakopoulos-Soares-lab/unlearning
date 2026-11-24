"""S08 immutable inputs and independent row/group/fold adapters; no model forwards."""
from pathlib import Path
import os, sys, json, hashlib, functools
import numpy as np
from artifact_seals import *

TASKS=['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']
REPS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm']
KEYS=[f'decoder_layer_{i}' for i in range(25)]+['final_norm']
POLICIES=['independent_refit','fixed_original_base']
METRICS=['AUROC','AP','accuracy','balanced_accuracy','cross_entropy']
MAP=dict(zip(METRICS,['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy']))

def key(rep):
    need(rep in REPS,'Unknown representation');return KEYS[REPS.index(rep)]

def choose(choices):return max(choices,key=lambda x:(x['mean_fold_AUROC'],-x['C']))['C']

def exact_keys(actual,expected):need(len(actual)==len(set(actual)) and set(actual)==set(expected),'Duplicate/missing/unexpected identities')

def check_source(c,cfg):
    source=load(Path(c)/'SOURCE_IDENTITY.json');need(sha(Path(c)/'RUN_CONFIG.json')==source['config_sha256'],'Configuration changed')
    for f in source['files']:need(sha(Path(source['code_root'])/f['path'])==f['sha256'],'Verifier source changed; affected-scope requalification required')
    return source

def scope(cfg,a,t,r,s):
    need(cfg['phase']=='S08' and cfg['tasks']==TASKS and cfg['representations']==REPS and cfg['seeds']==[42,17,1234] and cfg['policies']==POLICIES and not cfg['S09_allowed'],'Changed S08 scope')
    need(t in TASKS and r in REPS and s in [42,17,1234],'Unapproved selector')
    v=next((x for x in cfg['candidates'] if x['alias']==a),None);need(v is not None,'Unknown candidate');return v

def ready(c,a,t,r,s):
    cfg=load(Path(c)/'RUN_CONFIG.json');v=scope(cfg,a,t,r,s);source=check_source(c,cfg)
    need(sha(Path(c)/'CPU_ENVIRONMENT_LOCK.json')==cfg['cpu_runtime_lock_sha256'],'Runtime lock changed')
    need(str(Path(sys.executable).absolute())==cfg['cpu_runtime_python'],'Wrong qualified CPU interpreter')
    need(load(Path(c)/'READINESS.json')['status']=='PASS','S08 readiness not admitted')
    state=load(Path(cfg['research_run_root'])/'CONTROLLER_STATE.json');approval=state['approvals']['S08']
    need(approval['approved'] and approval['source']=='direct_chat' and approval['message']=='APPROVE S08 at '+cfg['package_commit'] and v['candidate_id'] in approval['scope_candidates'],'Direct S08 approval missing')
    need(not state['approvals']['S09']['approved'],'Unexpected S09 approval')
    cfg['_source']=source['verifier_source_identity_sha256'];return cfg,v

@functools.lru_cache(maxsize=8)
def specs(c,a,t):
    cfg=load(Path(c)/'RUN_CONFIG.json');b=cfg['task_spec_shards'][a+'|'+t];need(sha(b['path'])==b['sha256'],'Frozen task manifest changed');rows=[json.loads(l) for l in Path(b['path']).read_text().splitlines()]
    need(len(rows)==2340 and len({x['id'] for x in rows})==2340,'Missing/duplicate task keys');return rows

def select(rows,k,**dims):
    out=[x for x in rows if x['k']==k and all(x.get(n)==v for n,v in dims.items())];need(len(out)==1,'Missing/extra key '+str((k,dims)));return out[0]

@functools.lru_cache(maxsize=1)
def audit_keys(c):
    cfg=load(Path(c)/'RUN_CONFIG.json');p=Path(c)/'ORIGINAL_AUDIT_KEYS.json';need(sha(p)==cfg['original_audit_keys_sha256'],'Audit panel changed');return load(p)

def meta(cfg,t,sp):
    need(t in TASKS and sp in ['train','dev'],'Unauthorized metadata split')
    rows=load(Path(cfg['inputs_root'])/'s06'/(t+'-'+sp+'-metadata.json'));b=cfg['producer_config']['feature_config']['cohorts'][t][sp]
    need(digest(rows)==b['ordered_metadata_sha256'] and len(rows)==b['rows'],'Cohort/row metadata changed')
    need(len({x['id'] for x in rows})==len(rows) and len({x['group'] for x in rows})==b['groups'],'Duplicate rows or group denominator mismatch');need(sorted({x['label'] for x in rows})==b['class_order'],'Class mapping changed');return rows

@functools.lru_cache(maxsize=4)
def matrix(c,a,t,r,sp):
    cfg=load(Path(c)/'RUN_CONFIG.json');scope(cfg,a,t,r,42);rows=meta(cfg,t,sp);fc=cfg['producer_config']['feature_config'];case=Path(cfg['producer_config']['feature_artifacts_root'])/'candidates'/a
    b=cfg['feature_admissions'][a];need(sha(b['path'])==b['sha256'],'Prior feature hash witness changed');witness={x['path']:x for x in load(b['path'])['files']}
    root=case/'features'/t/sp;verify_seal(root,required=['INDEX.json']);idx=load(root/'INDEX.json');v=next(x for x in cfg['candidates'] if x['alias']==a);identity=idx['identity'];need(identity['candidate_content_sha256']==v['model_tensor_content_sha256'] and identity['task']==t and identity['split']==sp and identity['source_identity_sha256']==cfg['producer_config']['feature_source_GPU_identity'],'Wrong checkpoint/task/split/feature source')
    parts=[];offset=0
    for ch in idx['chunks']:
        need(ch['first']==offset and 0<ch['stop']-offset<=256,'Chunk order changed');cr=case/ch['relative_root'];need(sha(cr/'COMPLETE.json')==ch['seal_sha256'],'Chunk receipt changed');verify_seal(cr,required=['features_and_lm.npz','RESOURCE.json']);p=cr/'features_and_lm.npz';need(str(p) in witness and file_stat(p)==witness[str(p)]['stat'],'Feature content changed since qualified actual hash admission')
        sealed=load(cr/'COMPLETE.json');need(next(x['sha256'] for x in sealed['files'] if x['path']=='features_and_lm.npz')==witness[str(p)]['sha256'],'Feature witness/receipt mismatch')
        rr=rows[offset:ch['stop']]
        with np.load(p,allow_pickle=False) as z:
            parts.append(check_chunk(z,rr,fc['cohorts'][t][sp]['class_order'],t,sp,r))
        offset=ch['stop']
    need(offset==len(rows),'Feature rows missing');x=np.concatenate(parts);x.flags.writeable=False;return x,np.array([v['label'] for v in rows]),[v['id'] for v in rows]

def check_chunk(z,rows,classes,t,sp,r):
    for n,field in [('ids','id'),('labels','label'),('groups','group')]:need(z[n].tolist()==[x[field] for x in rows],'Feature '+n+' order mismatch')
    need(z['classes'].tolist()==classes and z['task'].tolist()==[t]*len(rows) and z['split'].tolist()==[sp]*len(rows),'Feature class/task/split mismatch');x=z[key(r)];need(x.dtype==np.float32 and x.shape==(len(rows),1920) and np.isfinite(x).all(),'Feature dtype/width/finiteness mismatch');return x

def fold_indices(cfg,t,s,ids):
    b=next(x for x in cfg['producer_config']['feature_config']['folds'][t] if x['cv_seed']==s);p=Path(cfg['inputs_root'])/'s06'/b['relative_path'];need(sha(p)==b['sha256'],'Fold bytes changed');rows=meta(cfg,t,'train');need(ids==[x['id'] for x in rows],'Fold row order changed');lookup={v:i for i,v in enumerate(ids)};groups={x['id']:x['group'] for x in rows};out=[];seen=[]
    for row in load(p):
        tr=row['train_ids'];va=row['validation_ids'];need(len(set(tr))==len(tr) and len(set(va))==len(va) and not set(tr)&set(va) and set(tr)|set(va)==set(ids),'Invalid fold partition');need(not {groups[v] for v in tr}&{groups[v] for v in va},'Group leakage');out.append((np.array([lookup[v] for v in tr]),np.array([lookup[v] for v in va])));seen+=va
    need(len(out)==5 and len(seen)==len(ids) and set(seen)==set(ids),'Fold coverage changed');return out

@functools.lru_cache(maxsize=5)
def weights(c,t):
    cfg=load(Path(c)/'RUN_CONFIG.json');rows=meta(cfg,t,'dev');b=cfg['producer_config']['feature_config']['draws'][t];p=Path(cfg['inputs_root'])/'s06'/b['relative_path'];need(sha(p)==b['file_sha256'],'Original draw bytes changed');names=sorted({x['group'] for x in rows});lookup={g:i for i,g in enumerate(names)};inverse=np.array([lookup[x['group']] for x in rows])
    with np.load(p,allow_pickle=False) as z:
        need(z['ids'].tolist()==[x['id'] for x in rows] and z['group_names'].tolist()==names and np.array_equal(z['row_groups'],inverse) and int(z['seed'])==20261103,'Draw ID/group/seed mismatch');draws=z['group_draws'];need(draws.dtype==np.int32 and draws.shape==(2000,len(names)) and hashlib.sha256(draws.tobytes()).hexdigest()==b['draw_array_C_order_bytes_sha256'],'Draw content/dtype/order mismatch');need(np.all((draws>=0)&(draws<len(names))),'Invalid draw group index')
    w=group_weights(draws,inverse,len(names))
    if t=='gue_splice_reconstructed':need(len(rows)==512 and len(names)==511,'Splice group denominator changed')
    return w,b['file_sha256']

def group_weights(draws,inverse,n):
    need(draws.ndim==2 and draws.shape[1]==n and np.all((draws>=0)&(draws<n)) and np.all((inverse>=0)&(inverse<n)),'Invalid group multiplicity input');counts=np.zeros((len(draws),n),dtype=np.int64);np.add.at(counts,(np.arange(len(draws))[:,None],draws),1);need(np.array_equal(counts.sum(1),np.full(len(draws),n)),'Group multiplicity lost');return counts[:,inverse].astype(np.float64)

def original(cfg,t,r,s):
    p=Path(cfg['inputs_root'])/'ORIGINAL_BASE_HEADS.json';need(sha(p)==cfg['producer_config']['fixed_head_metadata_sha256'],'Original reference map changed');b=next(x for x in load(p) if (x['task'],x['representation'],x['cv_seed'])==(t,r,s));q=Path(cfg['producer_inputs_root'])/b['relative_path'];need(sha(q)==b['head_sha256'],'Original reference head changed');return q,b

def compare(a,b,atol,label):
    a=np.asarray(a);b=np.asarray(b);need(a.shape==b.shape and a.size and np.isfinite(a).all() and np.isfinite(b).all(),'Nonfinite/shape mismatch '+label);d=np.abs(a.astype(np.float64)-b.astype(np.float64));flat=int(np.argmax(d));ix=np.unravel_index(flat,d.shape);out={'label':label,'status':'PASS' if np.all(d<=atol) else 'FAIL','atol':atol,'rtol':0,'coordinates':int(d.size),'max_abs_residual':float(d.flat[flat]),'worst_index':[int(i) for i in ix],'worst_actual':float(a.flat[flat]),'worst_reference':float(b.flat[flat])};need(out['status']=='PASS','NUMERICAL_MISMATCH '+json.dumps(out));return out

def parameter_hash(pipe):
    h=hashlib.sha256()
    for n,x in [('mean',pipe[0].mean_),('scale',pipe[0].scale_),('var',pipe[0].var_),('coef',pipe[-1].coef_),('intercept',pipe[-1].intercept_),('classes',pipe[-1].classes_)]:
        a=np.asarray(x);need(np.isfinite(a).all(),'Nonfinite saved parameter');h.update(json.dumps([n,str(a.dtype),list(a.shape)],separators=(',',':')).encode()+b'\0');h.update(a.tobytes(order='C'))
    return h.hexdigest()
