"""Minimal exact unchanged S06 dev-anchor projections for declared S07 private recovery; no new inference."""
from pathlib import Path
import sys,json
from ops import C,A,save,now
sys.path.insert(0,str(A/'code'));from s07_contract import *
alias=sys.argv[1];cfg=load(C/'RUN_CONFIG.json');case=A/'candidates'/alias;out=case/'recovery-inputs';need(not out.exists(),'Preserve prior projection identity');out.mkdir();records=[];C6=C.parent.parent/'S06/attempt-001';origin=load(C6/(alias+'-PRIVATE_RECOVERY_LOCATORS.json'))
for t in cfg['tasks']:
 for rep in cfg['anchors']:
  x,y,ids=matrix(C,alias,t,rep,'dev');meta=metadata(cfg,t,'dev');key=KEYS[HOOKS.index(rep)];p=out/(t+'-'+key+'-dev.npz');classes=cfg['feature_config']['cohorts'][t]['dev']['class_order'];np.savez(p,features=x,ids=np.array(ids),labels=y,groups=np.array([r['group'] for r in meta]),classes=np.array(classes));msha=hashlib.sha256(x.tobytes()).hexdigest()
  with np.load(p,allow_pickle=False) as z:need(np.array_equal(z['features'],x) and z['ids'].tolist()==ids,'Unchanged projection serialization changed')
  source=Path(cfg['feature_artifacts_root'])/'candidates'/alias/'features'/t/'dev';idx=load(source/'INDEX.json');records.append({'task':t,'representation':rep,'split':'dev','planned_S06_extraction_id':idx['planned_spec_id'],'S06_bundle_seal_sha256':sha(source/'COMPLETE.json'),'original_chunks':idx['chunks'],'original_array_key':key,'original_S06_private_revision':origin['revision'],'original_S06_archive_sha256':origin['archive_sha256'],'typed_matrix_bytes_sha256':msha,'projection_file_sha256':sha(p),'cohort_sha256':cfg['feature_config']['cohorts'][t]['dev']['ordered_metadata_sha256'],'shape':[512,1920],'dtype':'float32','class_order':classes,'mathematical_transformation':'NONE; exact original typed array values only'})
put(out/'PROJECTION_BINDINGS.json',{'schema_version':'s07-bounded-unchanged-recovery-inputs-v1','status':'PASS','alias':alias,'records':records,'raw_feature_value_bytes':10*512*1920*4,'full_S06_archives_repacked':False,'reason':'Only ten predeclared anchor-dev matrices are internal exact recovery inputs (~39.3MB/candidate), avoiding full1.35GB unchanged archive repack/download; all other S06 features remain exact immutable external dependencies','source_sha256':sha(Path(__file__)),'observed_utc':now()});print('S07_MINIMAL_UNCHANGED_RECOVERY_PROJECTIONS_SEALED',alias,10)
