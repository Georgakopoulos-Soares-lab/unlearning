"""Assemble exact case eligibility and bounded unchanged dependency projections."""
from pathlib import Path
import sys,json,hashlib,shutil
from ops import C,A
cfg=json.loads((C/'RUN_CONFIG.json').read_text());alias=sys.argv[1];sys.path.insert(0,str(A/'code'))
from s08_shared import *
from s08_index import assemble
source=load(C/'SOURCE_IDENTITY.json')['verifier_source_identity_sha256'];case=A/'candidates'/alias;b=cfg['case_bindings'][alias]
for x in b.values():need(sha(x['path'])==x['sha256'],'Case key binding changed')
coverage=assemble(case,b['expected']['path'],b['producer']['path'],C/'ORIGINAL_AUDIT_KEYS.json',alias,source,case/'eligible');need(coverage['prediction_paths']==780 and coverage['metric_vectors']==3900,'Incomplete numeric case');root=case/'recovery-inputs';root.mkdir(exist_ok=True);panel=load(C/'RECOVERY_CONTRACT.json')['panel'][alias];seen=set();records=[]
for s in panel:
    t=s['task'];r=s['representation']
    if (t,r) in seen:continue
    seen.add((t,r));x,y,ids=matrix(str(C),alias,t,r,'dev');rows=meta(cfg,t,'dev');name=t+'-'+key(r)+'-dev.npz';p=root/name
    if p.exists():
        with np.load(p,allow_pickle=False) as z:need(np.array_equal(z['features'],x) and z['ids'].tolist()==ids,'Existing exact projection changed')
    else:np.savez(p,features=x,labels=y,ids=np.array(ids),groups=np.array([v['group'] for v in rows]),classes=np.array(cfg['producer_config']['feature_config']['cohorts'][t]['dev']['class_order']))
    fc=Path(cfg['producer_config']['feature_artifacts_root'])/'candidates'/alias/'features'/t/'dev';index=load(fc/'INDEX.json');records.append({'task':t,'representation':r,'relative_path':name,'file_sha256':sha(p),'matrix_value_sha256':hashlib.sha256(x.tobytes()).hexdigest(),'S06_bundle_receipt_sha256':sha(fc/'COMPLETE.json'),'S06_array_key':key(r),'S06_chunk_seals':[v['seal_sha256'] for v in index['chunks']],'candidate_content_sha256':next(v['model_tensor_content_sha256'] for v in cfg['candidates'] if v['alias']==alias),'cohort_sha256':cfg['producer_config']['feature_config']['cohorts'][t]['dev']['ordered_metadata_sha256'],'not_new_extraction':True})
put(root/'PROJECTION_BINDINGS.json',{'schema_version':'s08-exact-selected-recovery-inputs-v1','records':records,'selection':'Original S04remaining audit selectors only; no new model/LM inference or subset selected from scores.'});print('S08_CASE_ELIGIBILITY_AND_EXACT_RECOVERY_PROJECTIONS_READY',alias,len(records),flush=True)
