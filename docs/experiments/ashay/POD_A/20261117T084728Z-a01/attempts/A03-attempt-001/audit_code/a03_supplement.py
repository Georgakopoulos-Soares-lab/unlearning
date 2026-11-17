"""Finish all-unit dependency/draw structure, semantics and bounded exposure accounting."""
from a03_common import *
import subprocess

def main(c):
 c.family='supplement';refs=set();receipts=[];bootstrap=[];base_equal=0;valid_cache={};rows={g:c.rows(g) for g in HASHES};taskrows={t:[r for r in rows[group(t)] if r['task']==t] for t in TASKS}
 for rootkey,arms in [('base_R1',['base','maxent']),('R3',['new'])]:
  root=c.roots[rootkey]
  for g in HASHES:
   for arm in arms:receipts.append(root/'features'/g/arm/'FEATURE_UNIT_COMPLETE.json')
   idx=jread(root/'probes'/g/'PROBE_INDEX.json');receipts.extend(c.resolve(e['receipt']) for e in idx['units']+idx['lm_units'])
 receipts.extend(sorted((c.roots['controls']/'tasks').rglob('COMPLETE.json')))
 for rp in receipts:
  v=c.receipt(rp)
  refs.update(c.resolve(e['path']) for e in v['files']) if isinstance(v['files'],list) else refs.update(rp.parent/name for name in v['files'])
 ensure(len(receipts)==990,'Sealed receipt accounting differs')
 # Validate every native and paired draw output against the already verified common saved population.
 for t in TASKS:
  for sp in splits(t):
   path=c.roots['base_R1']/'probes'/group(t)/t/f'{sp}_resampling.npz';sr=[r for r in taskrows[t] if r['split']==sp];y=np.array([r['label'] for r in sr]);classes=np.unique(y)
   with np.load(path,allow_pickle=False) as z:
    w=np.stack([np.bincount(draw,minlength=len(z['group_names'])) for draw in z['group_draws']])[:,z['row_groups']];valid=np.all(np.stack([w[:,y==k].sum(1)>0 for k in classes]),axis=0)
   for l in LAYERS:
    for s in SEEDS:
     old=c.roots['base_R1']/'probes'/group(t)/t/l/f'seed{s}';new=c.roots['R3']/'probes'/group(t)/t/l/f'seed{s}'
     with np.load(old/f'{sp}_predictions.npz',allow_pickle=False) as a,np.load(new/f'{sp}_predictions.npz',allow_pickle=False) as b:ensure(np.array_equal(a['prob_base_refit'],b['prob_base_refit']),'Duplicated historical base probabilities differ');base_equal+=1
     for rootkey,u,pols in [('base_R1',old,['h3_only_refit','h3_only_fixed_base']),('R3',new,['new_refit','new_fixed_base'])]:
      p=u/f'{sp}_bootstrap.npz'
      with np.load(p,allow_pickle=False) as z:
       ensure(np.array_equal(z['valid'],valid),'All-unit native invalid-class mask differs')
       for pol in pols:
        for m in NAMES:ensure(z[pol+'__'+m].shape==(2000,) and np.isfinite(z[pol+'__'+m][valid]).all() and np.isnan(z[pol+'__'+m][~valid]).all(),'All-unit native draw support/finiteness differs')
      bootstrap.append({'kind':'native_probe','task':t,'split':sp,'layer':l,'seed':s,'dependency':rootkey,'reference':c.ref(p),'valid':int(valid.sum()),'invalid':int((~valid).sum())})
     for pol in ['new_refit','new_fixed_base']:
      p=c.roots['R3']/'paired_bootstrap'/group(t)/t/l/f'seed{s}'/f'{sp}_{pol}_vs_h3.npz'
      with np.load(c.ref(p)['path'],allow_pickle=False) as z:
       ensure(np.array_equal(z['valid'],valid),'All-unit paired invalid mask differs')
       for m in NAMES:ensure(z[m].shape==(2000,) and np.isfinite(z[m][valid]).all() and np.isnan(z[m][~valid]).all(),'All-unit paired shape/finiteness differs')
      bootstrap.append({'kind':'R3_R1_paired','task':t,'split':sp,'layer':l,'seed':s,'dependency':'R3','reference':c.ref(p),'valid':int(valid.sum()),'invalid':int((~valid).sum())})
   for name in ['composition','4mer']:
    for s in SEEDS:
     p=c.roots['controls']/'tasks'/t/name/f'seed{s}'/f'{sp}_bootstrap.npz'
     with np.load(c.ref(p)['path'],allow_pickle=False) as z:
      ensure(np.array_equal(z['valid'],valid),'Control draw mask differs')
      for m in NAMES:ensure(z[m].shape==(2000,) and np.isfinite(z[m][valid]).all() and np.isnan(z[m][~valid]).all(),'Control draw shape/finiteness differs')
     bootstrap.append({'kind':'control','task':t,'split':sp,'layer':'sequence_control','seed':s,'dependency':'controls','reference':c.ref(p),'valid':int(valid.sum()),'invalid':int((~valid).sum())})
   c.log('ALL_DRAW_STRUCTURE',task=t,split=sp,checked=len(bootstrap))
 put(c.cache/'ALL_BOOTSTRAP_STRUCTURES.json',bootstrap)
 loading=[]
 for role,rootkey,arm in [('base','base_R1','base'),('R1','base_R1','maxent'),('R3','R3','new')]:
  for g in HASHES:
   p=c.roots[rootkey]/'features'/g/arm/'loading.json';v=jread(p);ensure(all('_extra_state' in k for k in v['missing']+v['unexpected']),'Archived backbone loading exception exceeds extra_state');ensure(all(z==['torch.bfloat16','torch.float32'] for z in v['dtype_promotions'].values()),'Archived lossy dtype conversion');loading.append({'role':role,'group':g,'status':'INHERITED_LOADER_RECORD_STRUCTURALLY_VALIDATED','reference':c.ref(p),'missing_extra_state':len(v['missing']),'unexpected_extra_state':len(v['unexpected']),'live_qualification':'NOT_PERFORMED'})
 c.done('DEPENDENCY_AND_DRAW_AUDIT',{'status':'PASS','sealed_receipts':len(receipts),'unique_files_referenced_by_receipts':len(refs),'heterogeneous_receipt_types':{'feature':6,'probe':936,'LM':12,'control':36},'all_payload_file_integrity':'RESTORE_VALIDATION independently verifies23326 payload files plus4 checksum manifests; counts differ from scientific dependency accounting','draw_output_files':len(bootstrap),'draw_output_types':dict(collections.Counter(x['kind'] for x in bootstrap)),'duplicated_base_prediction_records_exactly_equal':base_equal,'all_resampling_population_arrays':'21 checked in PAIRING_POPULATION_CHECKS','loading_records':loading,'detailed_private_draw_structure_index':str(c.cache/'ALL_BOOTSTRAP_STRUCTURES.json'),'numerical_reconstruction_scope':'Separate predeclared NUMERICAL_RECOVERY_CHECKS; this all-unit scan does not rerun all numerical values'})
 # Trusted versioned interpretation sources, with precise unresolved semantics.
 gaprev='e95380d22b982a8fa5d71e4aaf7f8553010b6408';gappath='docs/experiments/ashay/graddiff-qualification-v1/DATA_EVIDENCE_GAPS.md';gapbytes=subprocess.check_output(['git','show',gaprev+':'+gappath],cwd='/workspace/wt-pod-a');gaphash=hashlib.sha256(gapbytes).hexdigest();sem=jread(c.c/'SEMANTIC_SOURCE_RECEIPT.json');labelrows=[]
 claims=[('emp_H3','biological_positive_of_numeric1','UNRESOLVED','Numeric0/1 is consistent; numerical1 remains AUROC/AP positive; yeast H3 task description does not establish integer biological meaning'),('gue_splice_reconstructed','biological_class_mapping_0_1_2','UNRESOLVED','Donor/acceptor/nonsplice task description supported; exact code-to-class map not established; sortednumeric macroOVR AUROC/meanAP and argmax preserved'),('gue_tf_0','exact_TF_experiment_identity','UNRESOLVED','wgEncodeEH000552 is only a size-based historical association, not verified alias identity'),('gue_mouse_0','exact_TF_experiment_identity','UNRESOLVED','Ch12Nrf2Iggrab is only a size-based historical association, not verified alias identity'),('gue_prom_core_all','task_window_alias','Human core promoter/TSS window -34,+35','Source task coordinate description; sample loci/convention/biological class code not recovered'),('gue_prom_300_all','task_window_alias','Human promoter/TSS window -249,+50','Do not equate promoter4 with this task alias; sample loci/class code unqualified')]
 for t,field,value,limit in claims:
  labelrows.append({'task':t,'field':field,'value':value,'evidence_status':'UNRESOLVED' if value=='UNRESOLVED' else 'SUPPORTED_TASK_DESCRIPTION_ONLY','source_repository':'Georgakopoulos-Soares-lab/unlearning','source_revision':gaprev,'source_path':gappath,'source_sha256':gaphash,'source_locator':'Current exact identity table row '+t,'primary_source_revision':'f25bed9ee20db966dff39e5c1571249d04e36404','primary_source_path':'MAGICS-LAB/DNABERT_2/README.md','primary_source_sha256':sem.get('sha256','UNAVAILABLE'),'primary_source_limit':'Pinned README sequence,label format does not establish biological code mapping or TF0 accessions','limitation':limit})
 for t in TASKS:
  labelrows.append({'task':t,'field':'numerical_class_convention','value':'sorted0/1/2 macroOVR AUROC, meanAP, argmax' if t=='gue_splice_reconstructed' else 'numeric1 positive AUROC/AP; p(class1)>=0.5','evidence_status':'VERIFIED_NUMERIC_CONSISTENCY','source_repository':'Verified historical private recovery archives','source_revision':jread(c.c/'RECOVERY_DEPENDENCIES.json')['dependencies'][0]['revision'],'source_path':'manifests/'+group(t)+'.jsonl + probes + all saved predictions','source_sha256':HASHES[group(t)],'source_locator':'DATA_AUDIT + STRUCTURAL_REUSE_AUDIT + NUMERICAL_RECOVERY_CHECKS','primary_source_revision':'f25bed9ee20db966dff39e5c1571249d04e36404','primary_source_path':'sequence,label source schema','primary_source_sha256':sem.get('sha256','UNAVAILABLE'),'primary_source_limit':'Integer schema is distinct from biological class meaning','limitation':'No unproved biological label mapping'})
 write_csv(c.out/'LABEL_SOURCE_MAP.csv',labelrows)
 # No row-level benign-retain source/consumption manifest exists among the scoped authoritative members.
 reg=jread(c.c/'accepted-a02/CHECKPOINT_REGISTRY.json');candidates={x['candidate_id']:x for x in reg['candidates']};entry={r['task']:r for r in csv.DictReader((c.c/'accepted-a02/TASK_ENTRY_MATRIX.csv').open())};exposure=[]
 for stage,cid in reg['selected_by_stage'].items():
  v=candidates[cid]
  for t in TASKS:
   rr=taskrows[t];exposure.append({'stage':stage,'candidate_id':cid,'task':t,'evaluation_rows':len(rr),'evaluation_unique_exact_sequences':len({hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rr}),'evaluation_unique_rc_groups':len({r['exact_rc_group'] for r in rr}),'planned_first_stage':entry[t]['planned_first_stage'],'first_observed_selected_config_declaration':entry[t]['first_observed_config_declaration_in_selected_scope'],'config_declares_family':t in v['declared_task_families'],'config_sha256':v['config']['sha256'],'config_locator':'Accepted A02 checkpoint registry/config fields; no new provider discovery','actual_benign_retain_row_manifest':'NOT_SUPPLIED_IN_SCOPED_DEPENDENCIES','unique_actual_training_rows':'UNKNOWN','exact_sequence_overlap_with_actual_training':'UNKNOWN','exact_rc_overlap_with_actual_training':'UNKNOWN','repeated_presentations':'UNKNOWN','per_source_tokens':'UNKNOWN','realized_sampling_proportions':'UNKNOWN','actual_first_training_exposure':'UNKNOWN','actual_parent':'UNKNOWN','executed_objective':'UNKNOWN','causal_eligibility':'NOT_ESTABLISHED','limit':'Not listed does not mean unseen. R2 unobserved; pretraining/parent exposure unknown; retain_sizes:null does not prove uniform sampling; progress counters do not identify retain-token budgets.'})
 write_csv(c.out/'EXPOSURE_AUDIT.csv',exposure)
 c.done('SEMANTIC_EXPOSURE_AUDIT',{'status':'COMPLETE_WITH_EXPLICIT_UNRESOLVED_FIELDS','label_source_rows':len(labelrows),'exposure_rows':len(exposure),'scoped_member_manifests':[c.ref(root/'CHECKSUMS.sha256') for root in c.roots.values()],'actual_benign_retain_row_manifests_found':0,'scope_limit':'Only four explicit authorized dependencies and accepted A02 metadata; no account-wide search or unrelated forget data inspected. Absence here is not global absence.','actual_overlap_computation':'BLOCKED_MISSING_TRAINING_ROW_DIGEST_MANIFEST; not reported as zero','questions_unsent':['Supply immutable numeric-to-biological label mapping and exact human/mouse TF0 accession metadata','Supply intended and actually consumed benign retain row/source digests, sampler revision, repeats and per-source token counts','Supply checkpoint parent hashes and executed objective/runtime code; identify R2 if intended'],'messages_sent':False,'cohort_changes':False})
 c.log('SUPPLEMENT_FINISHED',receipts=len(receipts),referenced_files=len(refs),draw_outputs=len(bootstrap),label_fields=len(labelrows),exposure_rows=len(exposure))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);a=p.parse_args()
 with threadpool_limits(limits=4):main(Context(a.control))
