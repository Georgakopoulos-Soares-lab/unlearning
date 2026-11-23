from ops import C,A,save,now
from pathlib import Path
import json,hashlib
root=A/'restored-minimum/historical-archive-001';report=json.loads((C/'SAVED_REFERENCE_QUALIFICATION.json').read_text());refs=json.loads((A/'historical-runtime-metadata-2.json').read_text())['references'];tasks=sorted({r['task'] for r in refs});cohorts={t:{} for t in tasks};manifestids={}
for name,expected in [('H3.jsonl','de2c348126fa84771ceeff38225703231848ac860f8b59a3ed41d9eb0b3f0938'),('other_five.jsonl','a270dd76f1a007b7685c012ca2c2a5bdcdbf67da1122f12c81caf292ae9c4126')]:
 p=root/'manifests'/name;assert hashlib.sha256(p.read_bytes()).hexdigest()==expected;manifestids[name]=expected
 with p.open() as f:
  for line in f:
   v=json.loads(line)
   # Only metadata fields are retained/used; sequence values are never extracted or forwarded.
   if v['split']!='train':continue
   t=v['task'];assert t in cohorts and v['id'] not in cohorts[t];cohorts[t][v['id']]={'label':v['label'],'group':v['exact_rc_group']}
rows=[];done=set()
for r in refs:
 key=(r['task'],r['cv_seed']);cohort=cohorts[r['task']];classes=sorted({v['label'] for v in cohort.values()});actual=next(v['class_order'] for v in report['references'] if (v['task'],v['representation'],v['cv_seed'])==(r['task'],r['representation'],r['cv_seed']));assert classes==actual
 if key in done:continue
 done.add(key);fold=root/r['fold']['path'].split('multiretain-layers-v1-final-20261110T140836Z/')[1];assert hashlib.sha256(fold.read_bytes()).hexdigest()==r['fold']['sha256'];fs=json.loads(fold.read_text());assert len(fs)==(3 if r['task']=='emp_H3' else 5);valall=[]
 for v in fs:
  tr=v['train_ids'];va=v['validation_ids'];assert set(tr)|set(va)==set(cohort) and not set(tr)&set(va);tg={cohort[x]['group'] for x in tr};vg={cohort[x]['group'] for x in va};assert not tg&vg;valall+=va
 assert len(valall)==len(set(valall))==len(cohort);assert len(cohort)==(11971 if r['task']=='emp_H3' else 1024)
 rows.append({'task':r['task'],'cv_seed':r['cv_seed'],'training_rows':len(cohort),'classes':classes,'folds':len(fs),'fold_sha256':r['fold']['sha256'],'complete_training_ID_universe_equal':True,'fold_train_validation_group_disjoint':True,'every_training_ID_validation_once':True,'ordered_training_metadata_sha256':hashlib.sha256(json.dumps(list(cohort.items()),separators=(',',':'),sort_keys=True).encode()).hexdigest()})
assert all(v['producer_bytes_match'] for v in json.loads((C/'REFERENCE_PRODUCER_SOURCE_JOIN.json').read_text()));save(C/'REFERENCE_COHORT_FOLD_CLASS_JOINS.json',{'schema':'s03-reference-cohort-fold-class-v1','status':'PASS','joins':rows,'reference_classes_verified':len(refs),'manifest_sha256':manifestids,'source_confirmation':'Exact producer fit_multiretain_layers and h3_followup bytes at8c651c7... match archived identity; H3 3fold, other5fold; classifier RNG42 distinct from foldCVseed','heldout_arrays_opened':False,'sequence_values_used':False,'verified_utc':now()});print('REFERENCE_JOIN_PASS',len(rows),'task-seed joins',len(refs),'head class orders')
