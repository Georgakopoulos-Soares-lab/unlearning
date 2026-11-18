"""Freeze A07 exact units and A08 audit inventory; repair only a derived A06 export."""
from common import *
sys.path.insert(0,str(A/'code'))
from other_five_common import checked_old,H,CONTROL,I6,LAYERS,TASKS,SEEDS,stage_spec,check_ref
from research_guard import guard
import collections
plan=read(D05/'COVERAGE_PLAN.json');units=[u for u in plan['new_proposed_units'] if u['owning_stage']=='A07'];assert len(units)==780
expected={stage_spec(alias,t,k,s) for alias in ['R4','R6'] for t in TASKS for k in LAYERS for s in SEEDS};assert {u['unit_id'] for u in units}==expected
frozen=[]
for u in units:
 assert hashlib.sha256(json.dumps(u['dependencies'],sort_keys=True).encode()).hexdigest()==u['dependency_sha256'];alias,task,key,ss=u['unit_id'].split('/');seed=int(ss[4:]);fold=checked_old(H/'probes/other_five'/task/('folds_seed'+str(seed)+'.json'));head=checked_old(H/'probes/other_five'/task/key/ss/'base.joblib');pred=checked_old(head.parent/'dev_predictions.npz');draw=checked_old(H/'probes/other_five'/task/'dev_resampling.npz')
 assert sha(fold)==u['dependencies']['fold'] and sha(head)==u['dependencies']['original_base_head'] and u['dependencies']['checkpoint']==I6['checkpoint_identities'][alias]['model_tensor_content_sha256']
 bundles={split:ref(Path(I6['extraction_units'][0]['manifest']['path']).parent.parent/'features'/alias/task/split/'COMPLETE.json') for split in ['train','dev']}
 identity={'stage':'A07','attempt_id':C.name,'unit_id':u['unit_id'],'candidate_identity':I6['checkpoint_identities'][alias],'A05_dependencies':u['dependencies'],'A06_bundles':bundles,'fold':ref(fold),'original_base_head':ref(head),'historical_predictions':ref(pred),'draw':ref(draw),'protocol_sha256':cfg['protocol_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256']}
 frozen.append({'unit_id':u['unit_id'],'candidate':alias,'task':task,'representation':key,'seed':seed,'identity':identity,'identity_sha256':digest(identity)})
manifest={'schema':'pod-a-a07-execution-v1','stage':'A07','count':780,'fixed_base_applications':780,'original_base_heads':390,'planned_optimizer_fits':12480,'units':frozen,'no_dynamic_discovery':True};put(C/'A07_EXECUTION_MANIFEST.json',manifest)
panel=[u['unit_id'] for u in frozen if u['representation'] in ['decoder_layer_16','final_norm']];assert len(panel)==60
audit={'schema':'pod-a-a08-prospective-audit-plan-v1','frozen_utc':now(),'before_any_A07_dev_predictions':True,'execution_requires':'Fresh direct A08 approval; no A08 execution under A07','all_units':[u['unit_id'] for u in frozen],'all_unit_checks':['Independent direct scaler/coefficient reconstruction from float32 features, probability tolerance1e-10','All five point metrics, every target and paired bootstrap value, masks and intervals at1e-12','TRAIN-only scaler moments and exact frozen five-fold identities, class order and pairing','Full schema/coverage/source/recovery verification; preserve original producer evidence'],'fresh_refit_panel':panel,'fresh_refit_panel_count':60,'selection':'Both candidates x all five tasks x layer16/final_norm x all three CV seeds; metadata selected before outputs','fresh_refit_procedure':'Independent scaler/logistic route, all C/fold CV traces, exact ties and final fit; no dev selection','extra_refits_under_A07':0,'bootstrap_draws':2000,'draw_seed':20261103,'source_execution_manifest_sha256':sha(C/'A07_EXECUTION_MANIFEST.json'),'scope_status':'PLANNED_NOT_EXECUTED'};put(C/'A08_AUDIT_HANDOFF_PLAN.json',audit)
# All H3 gates and their producer/audit links must still match, without rerunning computation.
gates=[]
for alias in ['R4','R6']:
 p=C.parent/'A06-attempt-001'/('H3_GATE_'+alias+'.json');g=read(p);assert g['status']=='PASS' and g['backup_status']=='PASS' and g['production_heads']==78
 for e in g['head_receipts']:
  q=A.parent/'A06-attempt-001'/e['path'];assert sha(q)==e['sha256'];j=read(q);assert j['status']=='VERIFIED' and sha(q.parent/'PRODUCER_COMPLETE.json')==j['producer_sha256'] and sha(q.parent/'AUDIT.json')==j['audit_sha256']
 gates.append(ref(p))
required=['A06_INPUTS.json','RESULT_SCHEMAS.json','COVERAGE.csv','COMPARABILITY_MATRIX.csv','CONTRAST_PLAN.json','INCLUSION_EXPOSURE_PLAN.csv','RESUME_MANIFEST.json','SESSION_HANDOFF.md','NEXT_PROMPT_RECOMMENDATIONS.md','RESOURCE_MEASUREMENTS.json','RESOURCE_LEDGER.jsonl','OBSERVER_STATUS.json','OWNED_JOB_DISPOSITION.json']
inputrefs=[]
for n in required:
 p=BASE/'attempts/A06-attempt-001'/n;content=p.read_bytes();inputrefs.append(ref(p))
 if p.suffix=='.json':json.loads(content)
 elif p.suffix=='.csv':list(csv.DictReader(content.decode().splitlines()))
put(C/'A07_INPUTS.json',{'schema':'pod-a-a07-inputs-v1','status':'PASS','prompt_commit':cfg['prompt_commit'],'research_handoff':cfg['research_head_before'],'coverage_plan':ref(D05/'COVERAGE_PLAN.json'),'protocol':ref(D05/'PROTOCOL_FROZEN.json'),'A06_required_evidence':inputrefs,'A06_H3_gates':gates,'A06_post_push_delivery':read(C.parent/'A06-attempt-001/FINAL_CLOSEOUT.json'),'cohort':ref(checked_old(H/'manifests/other_five.jsonl')),'checkpoint_identities':I6['checkpoint_identities'],'A04_status':'PARTIAL','time_policy':cfg['time_policy'],'semantic_mapping':{'requested INCLUSION_EXPOSURE_PLAN.json':'Existing authoritative INCLUSION_EXPOSURE_PLAN.csv; all columns/rows retained'},'historical_audits_repeated':False,'GPU_work':0})
# Derive measurement lineage from immutable target production receipts and result provenance.
src=BASE/'attempts/A06-attempt-001/PAIRED_CONTRASTS.csv';f=src.open(newline='');reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader);f.close();assert len(rows)==6776 and 'lineage' not in fields
schema=read(BASE/'attempts/A06-attempt-001/RESULT_SCHEMAS.json')['PAIRED_CONTRASTS'];pk=schema['primary_key'];assert len({tuple(x[k] for k in pk) for x in rows})==6776
extra=['lineage','ingestion_status','measurement_attempt','target_receipt_sha256','reference_measurement_lineage','reference_source_receipt','reference_source_sha256'];out=[];provenance={}
for row in rows:
 q=A.parent/'A06-attempt-001'/row['receipt'];receipt=read(q);assert receipt['status']=='VERIFIED';result=read(q.parent/'RESULTS.json')
 if row['policy']=='actual_causal_head':alias=result['candidate'];assert result['task']==row['task'] and result['split']==('test' if row['split']=='test_exploratory' else row['split'])
 else:
  alias=receipt['candidate'];producer=read(q.parent/'PRODUCER_COMPLETE.json');assert producer['candidate']==alias and producer['task']==row['task'] and producer['seed']==int(row['CV_seed']);assert sha(q.parent/'PRODUCER_COMPLETE.json')==receipt['producer_sha256']
 assert I6['checkpoint_identities'][alias]['model_tensor_content_sha256']==row['checkpoint_content_id'] and I6['checkpoint_identities'][alias]['candidate_id']==row['target_endpoint_id']
 split='test' if row['split']=='test_exploratory' else row['split'];key='final_norm' if row['representation']=='decoder.final_norm' else row['representation'].replace('decoder.layers.','decoder_layer_')
 if row['reference'].startswith('control_'):
  rtype='4mer' if row['reference']=='control_kmer4' else 'composition';rp=checked_old(CONTROL/'tasks'/row['task']/rtype/('seed'+row['CV_seed'])/(split+'_predictions.npz'));source=ref(rp)
 elif row['policy']=='actual_causal_head':source=ref(C03/'PAYLOAD_CHECKSUMS_base_R1.json')
 else:source=ref(checked_old(H/'probes/H3'/row['task']/key/('seed'+row['CV_seed'])/(split+'_predictions.npz')))
 additions={'lineage':'NEW','ingestion_status':'REUSED_IN_A07','measurement_attempt':'A06-attempt-001','target_receipt_sha256':sha(q),'reference_measurement_lineage':'REUSED','reference_source_receipt':source['path'],'reference_source_sha256':source['sha256']};out.append({**row,**additions});provenance[str(q.relative_to(A.parent/'A06-attempt-001'))]=sha(q)
target=C/'A06_PAIRED_CONTRASTS.normalized.v1.csv'
with target.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields+extra,lineterminator='\n');w.writeheader();w.writerows(out)
restored=list(csv.DictReader(target.open(newline='')));assert [[r[k] for k in fields] for r in restored]==[[r[k] for k in fields] for r in rows];assert [tuple(r[k] for k in pk) for r in restored]==[tuple(r[k] for k in pk) for r in rows]
repair={'status':'PASS','original_schema_status':'FAIL_MISSING_REQUIRED_LINEAGE','original':ref(src),'normalized':ref(target),'original_rows':6776,'original_primary_keys_preserved_in_order':True,'all_original_field_strings_preserved':True,'scientific_values_changed':False,'original_fields':fields,'added_fields':extra,'field_mapping':{k:k for k in fields},'measurement_lineage_definition':'NEW means measured in original A06 production; REUSED_IN_A07 describes ingestion separately. This is not checkpoint parent/training lineage.','reference_lineage':'REUSED historical base/R1/controls, receipt identities preserved','target_receipts':provenance};put(C/'A06_REPORT_SCHEMA_REPAIR.json',repair)
accept='# A06 acceptance reconciliation\n\nA06 computation is accepted from the pinned handoff. Its original PAIRED_CONTRASTS.csv fails its declared schema because lineage is missing. The immutable original and every original field/value/key/order remain unchanged. The owned normalized v1 copy adds measurement lineage NEW (relative to A06 production), ingestion REUSED_IN_A07 and evidence-derived receipt provenance. Base/R1/control measurements remain REUSED. This repair does not recompute or change probabilities, estimates, intervals, validity counts, unresolved comparisons or training lineage.\n\nAll 6,776 original rows and keys were compared field-for-field in order. A04 remains PARTIAL; R2/R5 and R3 bridge gaps remain. See A06_REPORT_SCHEMA_REPAIR.json for source/output digests and mapping.\n'
(C/'A06_ACCEPTANCE_RECONCILIATION.md').write_text(accept)
print(json.dumps({'manifest_units':len(frozen),'audit_panel':len(panel),'A06_schema_repair':'PASS','original_rows':len(rows),'H3_gates':'PASS'}))
