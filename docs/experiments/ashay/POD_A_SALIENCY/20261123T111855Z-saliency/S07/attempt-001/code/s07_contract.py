"""Strict S07 finite CPU producer contracts. No backbone, LM, tests, comparisons or independent release."""
from pathlib import Path
import os,sys,json,hashlib,functools
from artifact_seals import *
import numpy as np
import inherited_s06_contract as s06
TASKS=s06.TASKS;HOOKS=s06.HOOKS;KEYS=s06.KEYS;SEEDS=[42,17,1234];POLICIES=['independent_refit','fixed_original_base'];METRICS=['AUROC','AP','accuracy','balanced_accuracy','cross_entropy'];NAME_MAP=dict(zip(METRICS,['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy']))

def scope(cfg,alias,task,rep=None,seed=None):
 need(cfg['phase']=='S07' and cfg['tasks']==TASKS and cfg['representations']==HOOKS and cfg['seeds']==SEEDS and cfg['policies']==POLICIES,'Changed frozen S07 scope');need(task in TASKS and (rep is None or rep in HOOKS) and (seed is None or seed in SEEDS),'Unapproved task/representation/seed; H3/test/audit dispatch rejected');need(cfg['new_backbone_or_LM_work_allowed'] is False and cfg['independent_audit_or_release_allowed'] is False and cfg['result_status']=='COMPLETE_UNVERIFIED','Phase boundary changed');v=next((v for v in cfg['feature_config']['candidates'] if v['alias']==alias),None);need(v is not None and v['measurement_eligible'],'Unknown/unqualified candidate');return v

def ready(c,alias,t,rep=None,seed=None,gate=False):
 c=Path(c);cfg=load(c/'RUN_CONFIG.json');v=scope(cfg,alias,t,rep,seed);source=load(c/'SOURCE_IDENTITY.json');need(sha(c/'RUN_CONFIG.json')==source['config_sha256'] and sha(c/'CPU_ENVIRONMENT_LOCK.json')==cfg['cpu_runtime_lock_sha256'],'Configuration/runtime binding changed')
 for f in source['files']:need(sha(Path(source['code_root'])/f['path'])==f['sha256'],'Numerical source changed; versioned affected-scope qualification required')
 r=load(c/'READINESS.json');need(all(x['status']=='PASS' for k,x in r['gates'].items() if k!='R11'),'Mandatory readiness unresolved')
 if gate:need([alias,t,rep,seed] in r['first_operational_selectors'],'Unapproved operational unit')
 else:need(load(c/'FIRST_PRODUCTION_GATES.json')['status']=='PASS','First binary/multiclass ordinary-production gate missing')
 state=load(Path(cfg['research_run_root'])/'CONTROLLER_STATE.json');a=state['approvals']['S07'];need(a['approved'] and a['source']=='direct_chat' and a['package_commit']==cfg['package_commit'] and a['message']=='APPROVE S07 at '+cfg['package_commit'] and v['candidate_id'] in a['scope_candidates'],'Exact direct approval missing');h=state['candidate_gates'][v['candidate_id']];need(h['H3_GATE']=='PASS','Own H3 gate missing')
 for pre in ['h3_gate_receipt','recovery_receipt']:need(sha(Path(cfg['research_worktree'])/h[pre+'_path'])==h[pre+'_sha256'],'Own H3/recovery binding changed')
 need(state['phase_receipts']['S06']['sha256']==r['S06_receipt_sha256'],'S06 predecessor binding changed');need(str(Path(sys.executable).absolute())==cfg['cpu_runtime_python'],'Wrong qualified CPU interpreter');need(int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())>=48*1024**3,'48GiB host headroom unavailable at batch admission');cfg['_source']=source['producer_source_identity_sha256'];return cfg,v

@functools.lru_cache(maxsize=2)
def specs(c,alias,t):
 c=Path(c);cfg=load(c/'RUN_CONFIG.json');need(sha(c/'FINITE_EXECUTION_MANIFEST.jsonl')==cfg['finite_manifest_sha256'],'Frozen unit-key manifest changed');rows=[r for line in (c/'FINITE_EXECUTION_MANIFEST.jsonl').open() if (r:=json.loads(line))['c']==alias and r['t']==t];need(len(rows)==2340 and len({r['id'] for r in rows})==2340,'Wrong candidate-task finite scope');return rows

def sid(rows,k,**d):
 matches=[r for r in rows if r['k']==k and all(r.get(n)==v for n,v in d.items())];need(len(matches)==1,'Missing/duplicate exact frozen key '+str((k,d)));return matches[0]['id']

def metadata(cfg,t,sp,inputs=None):return s06.metadata(cfg['feature_config'],t,sp,Path(inputs or cfg['inputs_root'])/'s06')
@functools.lru_cache(maxsize=4)
def _matrix(c,alias,t,rep,sp):
 cfg=load(Path(c)/'RUN_CONFIG.json');scope(cfg,alias,t,rep);fcfg=cfg['feature_config'];fcfg['_GPU_source']=cfg['feature_source_GPU_identity'];case=Path(cfg['feature_artifacts_root'])/'candidates'/alias;admission=load(Path(c)/(alias+'-FEATURE_CONTENT_ADMISSION.json'));need(admission['status']=='PASS','Actual feature content admission missing')
 for e in admission['files']:
  p=Path(e['path']);need(file_stat(p)==e['stat'],'S06 feature changed after actual hash admission')
 x=s06.read_matrix(case,fcfg,alias,t,sp,rep);rows=metadata(cfg,t,sp);y=np.array([r['label'] for r in rows]);need(x.dtype==np.float32 and x.shape==(len(rows),1920) and sorted(set(y.tolist()))==fcfg['cohorts'][t][sp]['class_order'],'Feature/label/class schema changed');x.flags.writeable=False;return x,y,[r['id'] for r in rows]
def matrix(c,alias,t,rep,sp):return _matrix(str(c),alias,t,rep,sp)

def folds(cfg,t,seed,ids,inputs=None):
 root=Path(inputs or cfg['inputs_root'])/'s06';f=next(f for f in cfg['feature_config']['folds'][t] if f['cv_seed']==seed);need(sha(root/f['relative_path'])==f['sha256'],'Saved fold bytes changed');rows=metadata(cfg,t,'train',inputs);need([r['id'] for r in rows]==ids,'TRAIN fold row order mismatch');groups={r['id']:r['group'] for r in rows};lookup={i:j for j,i in enumerate(ids)};out=[];valid=[]
 for f in load(root/f['relative_path']):
  tr=f['train_ids'];va=f['validation_ids'];need(len(set(tr))==len(tr) and len(set(va))==len(va) and set(tr)|set(va)==set(ids) and not set(tr)&set(va),'TRAIN partition invalid');need(not {groups[i] for i in tr}&{groups[i] for i in va},'Group leakage');out.append((np.array([lookup[i] for i in tr]),np.array([lookup[i] for i in va])));valid+=va
 need(len(out)==5 and len(valid)==len(ids) and set(valid)==set(ids),'Wrong fivefold partition');return out
@functools.lru_cache(maxsize=5)
def weights(c,t):
 cfg=load(Path(c)/'RUN_CONFIG.json');w,h=s06.draw_weights(cfg['feature_config'],t,Path(cfg['inputs_root'])/'s06');return w,h

def reference(cfg,t,rep,seed,inputs=None):
 root=Path(inputs or cfg['inputs_root']);p=root/'ORIGINAL_BASE_HEADS.json';need(sha(p)==cfg['fixed_head_metadata_sha256'],'Reference binding changed');r=next(v for v in load(p) if (v['task'],v['representation'],v['cv_seed'])==(t,rep,seed));q=root/r['relative_path'];need(sha(q)==r['head_sha256'],'Exact original scaler/head changed');return q,r

def base_identity(cfg,v,t,rep,seed,pid):
 co=cfg['feature_config']['cohorts'][t];return {'phase':'S07','planned_spec_id':pid,'candidate_id':v['candidate_id'],'candidate_content_sha256':v['model_tensor_content_sha256'],'config_sha256':v['config_sha256'],'tokenizer_sha256':v['tokenizer_sha256'],'parent_id':v['parent_id'],'parent_null_reason':v['parent_null_reason'],'task':t,'representation':rep,'cv_seed':seed,'classifier_random_state':42,'protocol_semantic_sha256':cfg['protocol_semantic_sha256'],'source_identity_sha256':cfg['_source'],'cpu_runtime_lock_sha256':cfg['cpu_runtime_lock_sha256'],'S06_source_bundle_sha256':cfg['source6_bundle_sha256'],'TRAIN_cohort_sha256':co['train']['ordered_metadata_sha256'],'DEV_cohort_sha256':co['dev']['ordered_metadata_sha256'],'fold_sha256':next(f['sha256'] for f in cfg['feature_config']['folds'][t] if f['cv_seed']==seed),'class_order':co['train']['class_order'],'feature_dtype':'float32','width':1920,'policy':'independent_refit'}

def validate_probabilities(p,classes,expected,n):
 need(np.asarray(classes).tolist()==expected and expected in [[0,1],[0,1,2]],'Wrong probability class column order');need(isinstance(p,np.ndarray) and p.dtype==np.float64 and p.shape==(n,len(expected)) and np.isfinite(p).all() and np.all((p>=0)&(p<=1)) and np.allclose(p.sum(1),1,atol=1e-12,rtol=0),'Invalid probability matrix support/shape/dtype')
