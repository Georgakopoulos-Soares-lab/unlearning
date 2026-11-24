"""Source-bound S06 other-five extraction/LM and prospective S07 reader; no head operations."""
from pathlib import Path
import os,sys,json,re,hashlib
from artifact_seals import *
TASKS=['gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];SPLITS=['train','dev'];HOOKS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];KEYS=[f'decoder_layer_{i}' for i in range(25)]+['final_norm']

def scope(cfg,alias,task=None,split=None):
 need(cfg['phase']=='S06' and cfg['tasks']==TASKS and cfg['allowed_splits']==SPLITS,'S06 scope changed; H3/tests/other tasks excluded before opening data/model');need(task is None or task in TASKS,'Unapproved task rejected before opening data/model');need(split is None or split in SPLITS,'Unapproved/test split rejected before opening data/model');need(cfg['representations']==HOOKS and cfg['width']==1920 and cfg['physical_batch']==8 and cfg['chunk_rows']==256,'Frozen hook/layer16/width/geometry changed');need(cfg['precision_contract']=={'feature_dtype':'float32','backbone':'qualified_BF16_FP32','attention_backend':'TE_unfused'},'Qualified precision/backend changed');need(cfg['fitting_or_head_application_allowed'] is False,'Head fitting/application prohibited in S06');v=next((v for v in cfg['candidates'] if v['alias']==alias),None);need(v is not None and v['measurement_eligible'] and v['candidate_id'] and v['model_tensor_content_sha256'],'Unknown/unqualified candidate');return v

def readiness(c,alias,role):
 c=Path(c);cfg=load(c/'RUN_CONFIG.json');v=scope(cfg,alias);g=load(c/'READINESS.json');need(all(g['gates'][k]['status']=='PASS' for k in ['R1','R2','R3','R4','R5']),'S06 readiness incomplete');s=load(c/'SOURCE_IDENTITY.json');need(sha(c/'RUN_CONFIG.json')==s['configuration_sha256'],'Frozen config changed');need(g['source_bundle_sha256']==sha(c/'SOURCE_IDENTITY.json'),'Readiness source binding changed')
 for f in s['files']:need(sha(Path(s['code_root'])/f['path'])==f['sha256'],'Executed source changed; scoped version required')
 state=load(Path(cfg['research_run_root'])/'CONTROLLER_STATE.json');a=state['approvals']['S06'];need(a['approved'] is True and a['source']=='direct_chat' and a['message']=='APPROVE S06 at 7007ebd05bf59432bf69109e5f69baad31ec0d3a' and v['candidate_id'] in a['scope_candidates'],'Missing exact direct S06 approval');gate=state['candidate_gates'][v['candidate_id']];need(gate['H3_GATE']=='PASS','Own H3 gate missing')
 for prefix in ['h3_gate_receipt','recovery_receipt']:need(sha(Path(cfg['research_worktree'])/gate[prefix+'_path'])==gate[prefix+'_sha256'],'Own H3/recovery receipt changed')
 need(state['phase_receipts']['S05']['sha256']==g['S05_receipt_sha256'],'S05 predecessor binding changed');need(sha(c/'ENVIRONMENT_LOCK.json')==cfg['runtime_lock_sha256'] and sha(c/'CPU_ENVIRONMENT_LOCK.json')==cfg['cpu_runtime_lock_sha256'],'Runtime lock changed');need(int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())>=48*1024**3,'48GiB host admission headroom unavailable')
 cfg['_GPU_source']=s['roles']['GPU']['source_identity_sha256'];cfg['_LM_source']=s['roles']['LM_producer']['source_identity_sha256'];cfg['_verifier_source']=s['roles']['verifier']['source_identity_sha256'];cfg['_source']=s['roles'][role]['source_identity_sha256'];need(str(Path(sys.executable).absolute())==(cfg['runtime_python'] if role=='GPU' else cfg['cpu_runtime_python']),'Wrong qualified GPU/CPU interpreter');return cfg,v,cfg['_source']

def planned(c):
 rows=[json.loads(l) for l in (Path(c)/'FINITE_EXECUTION_MANIFEST.jsonl').read_text().splitlines()];need(len(rows)==360 and len({r['id'] for r in rows})==360,'S06 expected manifest missing/duplicate');return rows

def spec_id(lookup,k,**dims):
 rows=[r for r in lookup if r['k']==k and all(r.get(n)==v for n,v in dims.items())];need(len(rows)==1,'Missing/ambiguous frozen specification '+str((k,dims)));return rows[0]['id']

def metadata(cfg,task,split,inputs=None):
 need(task in TASKS and split in SPLITS,'Unapproved metadata access');p=Path(inputs or cfg['inputs_root'])/(task+'-'+split+'-metadata.json');rows=load(p);e=cfg['cohorts'][task][split];need(len(rows)==e['rows'] and digest(rows)==e['ordered_metadata_sha256'],'Cohort/order/label/group changed');need(len({r['id'] for r in rows})==len(rows) and len({r['group'] for r in rows})==e['groups'],'Unexpected ID duplication/group denominator');need(sorted({r['label'] for r in rows})==e['class_order'],'Class ordering changed');return rows

def row_bindings(cfg,task,split,inputs=None):
 rows=metadata(cfg,task,split,inputs);p=Path(inputs or cfg['inputs_root'])/(task+'-'+split+'-row-bindings.json');need(sha(p)==cfg['cohorts'][task][split]['row_binding_file_sha256'],'Scored sequence/length bindings changed');extra=load(p);need([{k:r[k] for k in ['id','label','group']} for r in extra]==rows,'Row metadata mismatch');return extra

def sequences(cfg,alias,task,split,first,stop):
 scope(cfg,alias,task,split);expected=row_bindings(cfg,task,split);need(0<=first<stop<=len(expected),'Invalid chunk bounds');p=Path(cfg['original_manifest']);need(sha(p)==cfg['original_manifest_sha256'],'Original otherfive manifest changed');out=[];cursor=0
 for line in p.open():
  t=re.findall(r'"task"\s*:\s*"([^"]+)"',line);s=re.findall(r'"split"\s*:\s*"([^"]+)"',line);need(len(t)==len(s)==1 and t[0] in TASKS and s[0] in SPLITS,'Unapproved source row; never decode test/H3 data')
  if t[0]!=task or s[0]!=split:continue
  if cursor<first:cursor+=1;continue
  if cursor>=stop:break
  r=json.loads(line);e=expected[cursor];seq=r['sequence'];need({'id':r['id'],'label':r['label'],'group':r['exact_rc_group']}=={k:e[k] for k in ['id','label','group']},'Source row order mismatch');need(len(seq)==e['length']==r['scored_length'] and 2<=len(seq)<=1000 and not set(seq)-set('ACGTN'),'Qualified scored sequence/length handling changed');need(hashlib.sha256(seq.encode()).hexdigest()==r['scored_prefix_sha256']==e['sequence_sha256'],'Scored prefix digest mismatch');rc=seq.translate(str.maketrans('ACGTN','TGCAN'))[::-1];need(hashlib.sha256(min(seq,rc).encode()).hexdigest()==e['group'],'Exact RC group mismatch');r['sequence_sha256']=r['scored_prefix_sha256'];out.append(r);cursor+=1
 need(len(out)==stop-first,'Missing approved rows');return out

def chunks_for(n):return [(a,min(a+256,n)) for a in range(0,n,256)]
def extraction_identity(cfg,v,task,split,pid):return {'phase':'S06','planned_spec_id':pid,'candidate_id':v['candidate_id'],'candidate_content_sha256':v['model_tensor_content_sha256'],'config_sha256':v['config_sha256'],'tokenizer_sha256':v['tokenizer_sha256'],'parent_id':v['parent_id'],'parent_null_reason':v['parent_null_reason'],'task':task,'split':split,'protocol_semantic_sha256':cfg['protocol_semantic_sha256'],'source_identity_sha256':cfg['_GPU_source'],'runtime_lock_sha256':cfg['runtime_lock_sha256'],'cohort_sha256':cfg['cohorts'][task][split]['ordered_metadata_sha256'],'row_binding_sha256':cfg['cohorts'][task][split]['row_binding_file_sha256'],'hooks':HOOKS,'width':1920,'feature_dtype':'float32','physical_batch':8}

def check_arrays(arr,expected,task,split,classes):
 import numpy as np
 n=len(expected);required=set(KEYS)|{'ids','labels','groups','classes','task','split','sequence_sha256','lengths','nll_sum','n_tokens','valid_nucleotide_mask','valid_target_mask'};need(set(arr)==required,'Missing/extra array members');need(arr['ids'].tolist()==[r['id'] for r in expected] and arr['labels'].tolist()==[r['label'] for r in expected] and arr['groups'].tolist()==[r['group'] for r in expected],'Row/label/group/filler mismatch');need(arr['classes'].tolist()==classes,'Class column order mismatch');need(arr['task'].tolist()==[task]*n and arr['split'].tolist()==[split]*n,'Task/test contamination');lengths=np.array([r['length'] for r in expected]);need(np.array_equal(arr['lengths'],lengths) and np.all((lengths>=2)&(lengths<=1000)),'Lengths changed');need(arr['sequence_sha256'].tolist()==[r['sequence_sha256'] for r in expected],'Scored sequence identity changed');need(arr['valid_nucleotide_mask'].dtype==np.bool_ and np.array_equal(arr['valid_nucleotide_mask'],np.arange(1000)[None,:]<lengths[:,None]),'Nucleotide/pad/filler mask changed');need(arr['valid_target_mask'].dtype==np.bool_ and np.array_equal(arr['valid_target_mask'],np.arange(1,1000)[None,:]<lengths[:,None]),'Causal shift/target mask changed');need(arr['n_tokens'].dtype.kind in 'iu' and np.array_equal(arr['n_tokens'],arr['valid_target_mask'].sum(1)) and np.all(arr['n_tokens']>0),'Invalid/zero target counts');need(arr['nll_sum'].shape==(n,) and arr['nll_sum'].dtype==np.float32 and np.isfinite(arr['nll_sum']).all(),'Invalid FP32 sufficient statistics')
 for key in KEYS:need(arr[key].shape==(n,1920) and arr[key].dtype==np.float32 and np.isfinite(arr[key]).all(),'Feature shape/dtype/nonfinite '+key)

def bundle(case,cfg,alias,task,split,inputs=None,restored=False,full=False):
 import numpy as np
 v=scope(cfg,alias,task,split);expected=row_bindings(cfg,task,split,inputs);root=Path(case)/'features'/task/split;index=load(root/'INDEX.json');ident=extraction_identity(cfg,v,task,split,index['planned_spec_id']);verify_seal(root,ident,required=['INDEX.json'],restored=restored);need(index['identity']==ident,'Bundle identity changed');offset=0;ids=[];sums=[];targets=[];seals=[]
 for ch in index['chunks']:
  need(ch['first']==offset and ch['stop']==min(offset+256,len(expected)),'Missing/duplicate/noncontiguous chunk');cr=Path(case)/ch['relative_root'];need(sha(cr/'COMPLETE.json')==ch['seal_sha256'],'Changed chunk receipt');verify_seal(cr,{**ident,'first':offset,'stop':ch['stop']},required=['features_and_lm.npz','RESOURCE.json'],restored=restored)
  with np.load(cr/'features_and_lm.npz',allow_pickle=False) as z:
   if full:check_arrays({k:z[k] for k in z.files},expected[offset:ch['stop']],task,split,cfg['cohorts'][task][split]['class_order'])
   need(z['ids'].tolist()==[r['id'] for r in expected[offset:ch['stop']]],'LM/stat row order differs');ids+=z['ids'].tolist();sums.append(z['nll_sum']);targets.append(z['n_tokens'])
  seals.append(ch['seal_sha256']);offset=ch['stop']
 need(offset==len(expected) and len(index['chunks'])==len(chunks_for(len(expected))),'Bundle population incomplete');return ids,np.concatenate(sums),np.concatenate(targets),digest(seals),index

def read_matrix(case,cfg,alias,task,split,representation,inputs=None,restored=False):
 import numpy as np
 need(representation in HOOKS,'Unqualified S07 representation');ids,_,_,_,idx=bundle(case,cfg,alias,task,split,inputs,restored);key=KEYS[HOOKS.index(representation)];parts=[]
 for ch in idx['chunks']:
  with np.load(Path(case)/ch['relative_root']/'features_and_lm.npz',allow_pickle=False) as z:parts.append(z[key])
 x=np.concatenate(parts);need(x.dtype==np.float32 and x.shape==(len(ids),1920) and np.isfinite(x).all(),'S07 matrix contract failed');return x

def draw_weights(cfg,task,inputs=None):
 import numpy as np
 need(task in TASKS,'Unknown drawtask');d=cfg['draws'][task];p=Path(inputs or cfg['inputs_root'])/d['relative_path'];need(sha(p)==d['file_sha256'],'Draw bytes changed');rows=metadata(cfg,task,'dev',inputs);names,inv=np.unique([r['group'] for r in rows],return_inverse=True)
 with np.load(p,allow_pickle=False) as z:
  need(z['ids'].tolist()==[r['id'] for r in rows] and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inv) and int(z['seed'])==20261103,'Draw mapping/ordered IDs/seed changed');a=z['group_draws'];need(a.dtype==np.int32 and a.shape==(2000,len(names)) and hashlib.sha256(a.tobytes()).hexdigest()==d['draw_array_C_order_bytes_sha256'],'Draw dtype/shape/content changed');weights=np.stack([np.bincount(v,minlength=len(names))[inv] for v in a])
 return weights.astype(np.float64),d['file_sha256']

def s07_bindings(case,cfg,alias,inputs=None,restored=False):
 root=Path(inputs or cfg['inputs_root']);need(sha(root/'S07_PLANNED_UNITS.jsonl')==cfg['S07_planned_units_sha256'],'Future frozen keys changed');need(sha(root/'ORIGINAL_BASE_REFERENCE_DEPENDENCIES.json')==cfg['original_base_reference_dependencies_sha256'],'Original reference identities changed');future=[json.loads(l) for l in (root/'S07_PLANNED_UNITS.jsonl').read_text().splitlines()];refs=load(root/'ORIGINAL_BASE_REFERENCE_DEPENDENCIES.json');out=[]
 for t in TASKS:
  for rep,key in zip(HOOKS,KEYS):
   for seed in [42,17,1234]:
    a=[u for u in future if u['c']==alias and u['t']==t and u['r']==rep and u['s']==seed and u['k']=='final_head'];b=[u for u in future if u['c']==alias and u['t']==t and u['r']==rep and u['s']==seed and u['k']=='fixed_application'];need(len(a)==len(b)==1,'S07 key missing/duplicate');ref=next(v for v in refs if (v['task'],v['representation'],v['cv_seed'])==(t,rep,seed));fold=next(f for f in cfg['folds'][t] if f['cv_seed']==seed);need(sha(root/fold['relative_path'])==fold['sha256']==ref['fold_sha256'],'Future fold/reference join changed');need(ref['class_order']==cfg['cohorts'][t]['train']['class_order'],'Reference class map changed');selectors={}
    for split in SPLITS:
     idx=load(Path(case)/'features'/t/split/'INDEX.json');selectors[split]={'planned_extraction_id':idx['planned_spec_id'],'bundle_receipt_sha256':sha(Path(case)/'features'/t/split/'COMPLETE.json'),'array_key':key,'dtype':'float32','logical_shape':[cfg['cohorts'][t][split]['rows'],1920],'chunks':[{'archive_member':'candidate/'+v['relative_root']+'/features_and_lm.npz','array_key':key,'rows':[v['first'],v['stop']],'chunk_seal_sha256':v['seal_sha256']} for v in idx['chunks']]}
    need(a[0]['d']==selectors['train']['planned_extraction_id'] and b[0]['d']==selectors['dev']['planned_extraction_id'],'Frozen S07 upstream dependency mismatch');out.append({'task':t,'representation':rep,'cv_seed':seed,'planned_refit_id':a[0]['id'],'planned_fixed_application_id':b[0]['id'],'selectors':selectors,'fold_relative_path':fold['relative_path'],'fold_sha256':fold['sha256'],'class_order':ref['class_order'],'original_base_reference':ref['external_original_head'],'head_operations_executed':False})
 need(len(out)==390 and len({v['planned_refit_id'] for v in out})==390 and len({v['planned_fixed_application_id'] for v in out})==390,'S07 exact consumer scope differs');return out
