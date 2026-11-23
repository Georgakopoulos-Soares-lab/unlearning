"""Non-dispatching S03 closure contracts. No network, model or dataset access."""
import itertools,re,hashlib,json
from pathlib import Path
SHA=re.compile(r'^[0-9a-f]{64}$')
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0']
REPS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm']
def need(v,msg):
 if not v:raise ValueError(msg)
def matrix(value,expected_ids):
 rows=value['candidates'];need(len(rows)==len(expected_ids)==9 and {v['candidate_id'] for v in rows}==set(expected_ids),'Nine distinct discovery dispositions required');need(len({r['candidate_id'] for r in rows})==9,'Duplicate candidate')
 for r in rows:
  if r['local_technical_status']=='PASS':
   need(bool(SHA.fullmatch(r.get('model_tensor_content_sha256',''))) and bool(SHA.fullmatch(r.get('payload_sha256',''))),'No inferred model or payload identity');need(r['strict_tensor_loading']=='PASS' and r['hook_count']==26 and r['width']==1920 and r['LM_actual_head']=='PASS','Incomplete strict/hook/LM proof');need(r['same_model_batch_repeat']=='PASS' and r['GPU_atol']==1e-4 and r['GPU_rtol']==1e-5 and r['worst_scaled_residual']<=1,'Numerical gate failed or tolerance changed')
  else:need(r['model_tensor_content_sha256'] is None and not r['S04_eligible'],'Unavailable native payload cannot be admitted')
  if r['S04_eligible']:need(r['local_technical_status']=='PASS' and r['private_artifact_CPU_restore']=='PASS' and r['fresh_process_model_replay']=='PASS','Route/bytes proof alone is not model recovery')
  need(r['immediate_parent_identity'] is None and not r['parent_relative_contrasts_admitted'],'Unknown lineage cannot create paired claims')
 need(value['counts']['S04_eligible']==sum(r['S04_eligible'] for r in rows),'Eligible count mismatch');need(value['counts']['locally_qualified_candidates']==sum(r['local_technical_status']=='PASS' for r in rows),'Qualification count mismatch')
 return True
def references(value,producer_rows):
 rows=value['references'];need(len(rows)==468,'Incomplete head key set');expected=set(itertools.product(TASKS,REPS,[42,17,1234]));need({(r['task'],r['representation'],r['cv_seed']) for r in rows}==expected,'Wrong head keys');original={(r['task'],r['representation'],r['cv_seed']):r for r in producer_rows}
 for r in rows:
  o=original[(r['task'],r['representation'],r['cv_seed'])];need(r['head_sha256']==o['head']['sha256'] and r['fold_sha256']==o['fold']['sha256'] and r['producer_identity_sha256']==o['identity']['sha256'],'Original head/scaler/fold substitution');need(r['class_order']==([0,1,2] if r['task']=='gue_splice_reconstructed' else [0,1]),'Wrong task/class probability order');need(r['width']==1920 and r['max_abs_residual']<=1e-10 and r['atol']==1e-10 and r['rtol']==0 and not r['fit_executed'],'Invalid CPU reference qualification')
 return True
def sealed_files(root,records):
 for name,h in records.items():
  p=Path(root)/name;need(not Path(name).is_absolute() and '..' not in Path(name).parts and not p.is_symlink(),'Unowned seal path');need(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==h,'Stale or corrupt seal: '+name)
 return True
