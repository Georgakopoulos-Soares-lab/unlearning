"""Pure deterministic finite keys. No scientific arrays, effects or dispatch."""
import csv,gzip,io,hashlib,json
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];HOOKS=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];SEEDS=[42,17,1234];POLICIES=['independent_refit','fixed_original_base'];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy'];ANCHORS=['decoder.layers.16','decoder.final_norm']
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def reporting_splits(task):return ['dev','test_exploratory'] if task=='emp_H3' else ['dev']
def coverage_rows():
 out=[]
 for candidate in ['base','R1','R2','R3','R4','R5','R6']:
  status='MISSING_R2' if candidate=='R2' else ('PROPOSED_R5' if candidate=='R5' else 'REUSED_RELEASED')
  for task in TASKS:
   for hook in HOOKS:
    for seed in SEEDS:
     for kind,policy in [('final_head','independent_refit'),('fixed_base_application','fixed_original_base')]:out.append({'unit_id':'/'.join([kind,candidate,task,hook,str(seed)]),'kind':kind,'candidate':candidate,'task':task,'split':'N/A','representation':hook,'CV_seed':str(seed),'policy':policy,'status':status,'new_owner_stage':('A06' if task=='emp_H3' else 'A07') if candidate=='R5' else 'NONE'})
   for split in reporting_splits(task):out.append({'unit_id':'/'.join(['primary_LM',candidate,task,split]),'kind':'primary_LM','candidate':candidate,'task':task,'split':split,'representation':'N/A','CV_seed':'N/A','policy':'actual_causal_head','status':status,'new_owner_stage':'A06' if candidate=='R5' else 'NONE'})
 for task in TASKS:
  for control in ['composition','kmer4']:
   for seed in SEEDS:out.append({'unit_id':'/'.join(['control',control,task,str(seed)]),'kind':'shared_control','candidate':control,'task':task,'split':'N/A','representation':'N/A','CV_seed':str(seed),'policy':'control','status':'REUSED_RELEASED','new_owner_stage':'NONE'})
 assert len(out)==6637 and len({r['unit_id'] for r in out})==6637
 return out
def table_keys(design,coverage_sha):
 endpoints=design['endpoint_content_ids'];protocol=design['original_protocol_sha256'];rows=[]
 def add(kind,target,reference,task,split,hook,seed,policy,refpolicy,metric,family,owner):
  tc=endpoints[target];rc=endpoints.get(reference,'N/A')
  if reference in ['composition','kmer4']:rc=design['control_heads']['|'.join([reference,task,str(seed)])]
  core={'table_kind':kind,'target':target,'target_content_id':tc,'reference':reference,'reference_content_id':rc,'task':task,'split':split,'representation':hook,'CV_seed':str(seed),'target_policy':policy,'reference_policy':refpolicy,'metric':metric,'family':family,'original_protocol_sha256':protocol}
  rows.append({'logical_id':digest(core),**core,'coverage_plan_sha256':coverage_sha,'owner_stage':owner,'status':'EXPECTED_NOT_MEASURED','direction':'target_minus_reference' if reference!='N/A' else 'metric_value','metric_orientation':'lower' if metric in ['classification_cross_entropy','causal_nll','perplexity'] else 'higher'})
 for task in TASKS:
  for split in reporting_splits(task):
   for hook in HOOKS:
    for seed in SEEDS:
     for policy in POLICIES:
      for metric in METRICS:
       add('classifier_marginal','R5','N/A',task,split,hook,seed,policy,'N/A',metric,'R5_marginal','A06' if task=='emp_H3' else 'A07')
       for target,reference,owner in [('R5','base','A06' if task=='emp_H3' else 'A07'),('R5','R1','A06' if task=='emp_H3' else 'A07'),('R4','R3','A08'),('R5','R4','A08'),('R6','R5','A08')]:add('classifier_paired',target,reference,task,split,hook,seed,policy,policy,metric,target+'_minus_'+reference,owner)
       if hook in ANCHORS:
        for control in ['composition','kmer4']:add('classifier_paired','R5',control,task,split,hook,seed,policy,'control',metric,'R5_minus_control_'+control,'A06' if task=='emp_H3' else 'A07')
   for metric in ['causal_nll','perplexity']:
    add('LM_marginal','R5','N/A',task,split,'N/A','N/A','actual_causal_head','N/A',metric,'R5_LM','A06')
    for target,reference in [('R5','base'),('R5','R1'),('R4','R3'),('R5','R4'),('R6','R5')]:add('LM_paired',target,reference,task,split,'N/A','N/A','actual_causal_head','actual_causal_head',metric,target+'_minus_'+reference,'A08')
 assert len(rows)==33684 and len({r['logical_id'] for r in rows})==len(rows)
 return rows
def csv_bytes(rows):
 s=io.StringIO(newline='');w=csv.DictWriter(s,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows);return s.getvalue().encode()
def compressed_keys(rows):return gzip.compress(csv_bytes(rows),compresslevel=9,mtime=0)
