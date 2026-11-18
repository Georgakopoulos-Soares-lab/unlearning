"""A04 exact counts, source, evidence, LM aggregates, privacy and handoff checks."""
from common4 import *
import argparse,ast,math,re,collections
def validate(final=False):
 guard();num=read(C/'numerical-reports/SMOKE_RESULTS.json');assert num['status']=='PASS' and num['sealed_units']==6 and num['comparison_rows']==189 and num['failed']==0;rr=list(csv.DictReader((D/'SMOKE_COMPARISONS.csv').open()));assert len(rr)==189 and len({tuple(r[k] for k in ['alias','kind','variant','array']) for r in rr})==189;assert all(r['status']==r['reverse_direction_status']=='PASS' and r['violations']==r['reverse_direction_violations']=='0' for r in rr);assert collections.Counter(r['alias'] for r in rr)=={'R3':135,'R5':54};assert sum(r['kind']=='same_checkpoint_historical' for r in rr)==81
 matrix=list(csv.DictReader((D/'QUALIFICATION_MATRIX.csv').open()));assert len(matrix)==21 and len({(r['alias'],r['variant']) for r in matrix})==21 and sum(int(r['comparison_rows']) for r in matrix)==621;assert sum(int(r['comparison_rows']) for r in matrix if r['origin']=='NEW_TRAIN_QUALIFICATION')==189;assert sum(int(r['comparison_rows']) for r in matrix if r['origin']=='PRESERVED_A04_002')==378
 for e in read(C/'PRESERVED_WORK_INDEX.json')['prior_run_root_files']:assert sha(D/'preserved-prior-run-root'/e['path'])==e['sha256']
 for e in read(C/'SOURCE_IDENTITY.json')['owned_source_files']:assert sha(A/'code'/e['path'])==e['sha256']
 p=read(D/'CODE/owned_adapter.patch.json');assert bh(p['content'].encode())==p['original_sha256']==sha(A/'code/owned_adapter.patch')
 assert sha(C/'SOURCE_IDENTITY.json')=='e72bb12601855339bf4497d3854cbd90e1f052d1def08a7ed4bcbb1da2192c1c';assert sha(C/'ENVIRONMENT_LOCK.json')=='401c96fdeb59783bf20954b153b24edaf913b87aa3d7607e1cc32c088d3ca294';assert read(C/'MIRROR_REMOTE_CONTENT_BINDING.json')['all_16_remote_asset_identities_bound_to_current_verified_local_bytes'];assert read(C/'IMPLEMENTATION_VALIDATION.json')['tests']==40
 # Independent corpus aggregation from saved actual-head loss sums/counts.
 import numpy as np
 aggregate=[]
 for p in sorted((A/'qualification').glob('*/*/attempt-001/features_and_lm.npz')):
  data=np.load(p,allow_pickle=False);metadata=read(p.parent/'LM_qualification.json');assert np.array_equal(data['n_tokens'],data['lengths']-1) and len(data['ids'])==12;loss=math.fsum(float(x) for x in data['nll_sum']);targets=sum(int(x) for x in data['n_tokens']);nll=loss/targets;ppl=math.exp(nll);assert abs(nll-metadata['corpus_NLL'])<=1e-12 and abs(ppl-metadata['perplexity'])<=1e-12 and targets==metadata['target_count'];aggregate.append({'alias':p.parents[2].name,'variant':p.parents[1].name,'status':'PASS','independent_float64_loss_sum':loss,'valid_target_count':targets,'corpus_NLL':nll,'PPL':ppl,'NLL_abs_residual':abs(nll-metadata['corpus_NLL']),'PPL_abs_residual':abs(ppl-metadata['perplexity'])})
 assert len(aggregate)==6
 required=['APPROVAL_RECORD.json','A04_INPUT_VERIFICATION.json','RECOVERY_PLAN.json','RESOURCE_PLAN.json','PRESERVED_WORK_INDEX.json','R2_DISCOVERY.json','R2_SELECTION_SUPPLEMENT.json','CHECKPOINT_REGISTRY_SUPPLEMENT.json','LINEAGE_EXPOSURE_SUPPLEMENT.csv','TRANSFER_DIAGNOSTICS.json','DOWNLOAD_RECEIPTS.json','CHECKPOINT_IDENTITIES.json','CHECKPOINT_HASHES.json','MISSING_INPUTS_DRAFT.md','SOURCE_IDENTITY.json','ENVIRONMENT_LOCK.json','RUNTIME_REBUILD.md','INVALIDATION_MAP.json','CONVERSION_REPORT.json','LOADING_REPORT.json','NATIVE_METADATA_AUDIT.json','HOOK_TOKENIZER_AUDIT.json','SMOKE_RESULTS.json','SMOKE_COMPARISONS.csv','LM_QUALIFICATION.json','QUALIFICATION_MATRIX.csv','REUSE_BRIDGE_MATRIX.csv','COMPARISON_READINESS.csv','RESOURCE_CALIBRATION.json','PAYLOAD_RECOVERY_INDEX.json','BACKUP_VERIFICATION.json','A05_REQUIREMENTS.md','A05_PROMPT_DELTA.md','A04_RECEIPT.json','SESSION_HANDOFF.md','RESUME_MANIFEST.json','REMOTE_HANDOFF.json','RESTORE.md'];missing=[n for n in required if not (D/n).exists()];assert not final or not missing
 allowed_pending={'BACKUP_VERIFICATION.json','BACKUP_MANIFEST.json','FRESH_RESTORE_CHECK.json','OUTPUT_SHA256SUMS'};links=0;pending=[];sourcecount=0
 for p in D.rglob('*'):
  if not p.is_file():continue
  data=p.read_bytes();assert not p.is_symlink() and p.resolve().is_relative_to(D.resolve()) and len(data)<20*1024**2;assert p.suffix not in ['.npz','.npy','.joblib','.pt','.bin','.distcp'];assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',data);assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',data)
  if p.suffix=='.json':json.loads(data)
  elif p.suffix=='.py':ast.parse(data);sourcecount+=1
  elif p.suffix=='.csv':
   reader=csv.reader(data.decode().splitlines());head=next(reader);assert len(head)==len(set(head)) and all(len(r)==len(head) for r in reader)
  elif p.suffix=='.md' and 'preserved-prior-run-root' not in p.parts:
   text=data.decode();assert text.startswith('# ') and '\n\n' in text and not text.startswith('"')
   for target in re.findall(r'\]\(([^)]+)\)',re.sub(r'```.*?```','',text,flags=re.S)):
    if target.startswith(('http:','https:','#')):continue
    dest=(p.parent/target.split('#',1)[0]).resolve()
    if not dest.exists():assert not final and dest.parent==D.resolve() and dest.name in allowed_pending,(str(p),target);pending.append(target)
    else:links+=1
 if final:
  assert read(C/'BACKUP_VERIFICATION.json')['status']=='PASS' and read(C/'FRESH_RESTORE_CHECK.json')['status']=='PASS';assert read(D/'A04_RECEIPT.json')['accepted_scope_recovery_status']=='PASS';assert read(D/'REMOTE_HANDOFF.json')['A05_proposal_ready_protected'] is True
  assert read(D/'A04_RECEIPT.json')['resource_calibration_sha256']==sha(D/'RESOURCE_CALIBRATION.json')
  for name,key in [('CHECKPOINT_IDENTITIES.json','targets'),('CHECKPOINT_REGISTRY_SUPPLEMENT.json','targets'),('RESUME_MANIFEST.json','target_identities')]:assert all(r['new_evidence_recovery_status']=='PASS' for r in read(D/name)[key])
  for name in ['REMOTE_HANDOFF.json','RESUME_MANIFEST.json']:
   root=read(B/name);assert root['current_stage']=='A04' and root['new_evidence_backup_status']=='PASS' and root['A05_proposal_ready_protected'] is True
   for key in ['qualification_receipt','new_evidence_backup','new_evidence_recovery_check','A09_historical_release','attempt_resume_manifest','current_progress','current_handoff','A05_proposal','A05_requirements','restore','missing_inputs']:
    target=(B/root[key]).resolve();assert target.is_relative_to(B.resolve()) and target.exists(),(name,key)
  proposal=read(D/'A05_PROPOSAL.json');assert proposal['protected'] is True and proposal['approval'] is False and proposal['automatic_execution'] is False;assert read(D/'A04_RECEIPT.json')['qualified_A05_proposal']['sha256']==sha(D/'A05_PROPOSAL.json')==read(B/'TERMINAL_STATE_RECEIPT.json')['A05_proposal_sha256']
 output={'schema':'pod-a-a04-report-QA-v1','status':'PASS' if final else 'PASS_PREFLIGHT_PENDING_RECOVERY','new_variants':6,'new_comparison_rows':189,'R3_comparison_rows':135,'R3_historical_rows':81,'R5_comparison_rows':54,'feature_coordinates':4193280,'LM_values':84,'all_bidirectional_violations':0,'reused_variants':12,'reused_rows':378,'combined_variants':18,'combined_rows':567,'seven_slot_plan_variants':21,'seven_slot_plan_rows':621,'R2_pending_variants':3,'R2_pending_rows':54,'independent_LM_aggregate_rechecks':aggregate,'all_previous_attempt_trees_unchanged':True,'preserved_previous_run_root_files':len(read(C/'PRESERVED_WORK_INDEX.json')['prior_run_root_files']),'public_sources_parsed':sourcecount,'Markdown_links_resolved':links,'pending_links':pending,'required_outputs_missing':missing,'privacy':'PASS','qualified_source_unchanged':True,'guard':guard(),'new_production_scores':0,'new_probe_fits':0,'heldout_forwards':0,'checked_utc':now()};put(C/'REPORT_QA.json',output);publish('REPORT_QA.json',output);print(json.dumps({k:v for k,v in output.items() if k not in ['independent_LM_aggregate_rechecks','guard']}))
def seal():
 assert read(C/'REPORT_QA.json')['status']=='PASS';guard();rootfiles=[{'path':str((B/n).relative_to(B)),'sha256':sha(B/n)} for n in cfg['allowed_root_files']];publish('ROOT_ENTRYPOINTS_SHA256SUMS',''.join(e['sha256']+'  '+e['path']+'\n' for e in rootfiles));files=[{'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='OUTPUT_SHA256SUMS'];publish('OUTPUT_SHA256SUMS',''.join(e['sha256']+'  '+e['path']+'\n' for e in files));put(C/'PUBLICATION_SEAL.json',{'files':files,'manifest_sha256':sha(D/'OUTPUT_SHA256SUMS'),'root_entrypoints':rootfiles,'self_excluded':True,'sealed_utc':now()});print(json.dumps({'status':'SEALED','files':len(files),'root_entrypoints':len(rootfiles),'manifest_sha256':sha(D/'OUTPUT_SHA256SUMS')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');p.add_argument('--seal',action='store_true');v=p.parse_args();seal() if v.seal else validate(v.final)
