"""CPU-only verification of a fresh private S04 metadata consumer; no producer-path fallback."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
root=Path(sys.argv[1]).resolve();inp=json.loads((root/'control/INPUTS_SAFE.json').read_text());meta=root/'metadata-inputs';verification=json.loads((root/'control/METADATA_VERIFICATION.json').read_text());H=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();read=lambda p:json.loads(p.read_text())
for name,expected in verification['metadata_file_manifest'].items():
 p=meta/name;assert p.is_file() and not p.is_symlink() and p.stat().st_size==expected['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==expected['sha256']
cohorts={}
for task in inp['tasks']:
 cohorts[task]={}
 for split in ['train','dev']:
  rows=read(meta/(task+'-'+split+'-metadata.json'));expected=inp['cohorts'][task][split];assert len(rows)==expected['rows'] and len({r['id'] for r in rows})==len(rows) and len({r['group'] for r in rows})==expected['groups'];assert sorted({r['label'] for r in rows})==expected['class_order'];assert H(rows)==expected['ordered_metadata_sha256'];assert H([r['id'] for r in rows])==expected['ordered_ids_sha256'];assert H([r['group'] for r in rows])==expected['ordered_groups_sha256'];cohorts[task][split]=rows
for fold in inp['folds']:
 fs=read(meta/fold['metadata_member']);assert hashlib.sha256((meta/fold['metadata_member']).read_bytes()).hexdigest()==fold['sha256'];train={r['id']:r for r in cohorts[fold['task']]['train']};allval=[]
 for v in fs:
  tr=v['train_ids'];va=v['validation_ids'];assert set(tr)|set(va)==set(train) and not set(tr)&set(va);assert not {train[x]['group'] for x in tr}&{train[x]['group'] for x in va};allval+=va
 assert len(allval)==len(set(allval))==len(train)
for v in inp['draws']:
 with np.load(meta/v['metadata_member'],allow_pickle=False) as z:
  rows=cohorts[v['task']]['dev'];assert z['ids'].tolist()==[r['id'] for r in rows];names,inverse=np.unique([r['group'] for r in rows],return_inverse=True);assert np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse);d=z['group_draws'];assert d.dtype==np.int32 and list(d.shape)==v['shape'] and int(z['seed'])==20261103 and d.min()>=0 and d.max()<len(names);assert hashlib.sha256(d.tobytes(order='C')).hexdigest()==v['draw_array_C_order_bytes_sha256'];classes=inp['cohorts'][v['task']]['dev']['class_order'];support=np.zeros((len(names),len(classes)),dtype=np.int32)
  for n,r in enumerate(rows):support[inverse[n],classes.index(r['label'])]+=1
  valid=np.all(support[d].sum(1)>0,axis=1);assert hashlib.sha256(valid.tobytes()).hexdigest()==v['class_complete_metadata_mask_sha256']
for v in inp['source']:assert hashlib.sha256((meta/v['metadata_member']).read_bytes()).hexdigest()==v['sha256']
print(json.dumps({'status':'FRESH_CONSUMER_METADATA_IDENTITY_PASS','permitted_rows':21148,'folds':18,'existing_draw_files':6,'source_files':5,'producer_input_fallback':False,'prediction_values_or_sequences_read':False,'new_draws_or_scientific_results':False},indent=2),flush=True)
