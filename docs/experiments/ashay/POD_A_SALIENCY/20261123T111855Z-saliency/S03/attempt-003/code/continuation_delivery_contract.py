"""Non-dispatching cross-artifact S03 release contracts. No network, arrays or models."""
import re,itertools
SHA=re.compile(r'^[0-9a-f]{64}$')
def need(v,msg):
 if not v:raise ValueError(msg)
def validate_release(matrix,payloads,proof,handoff,private_pass,source_old,source_new,runtime_sha):
 rows=matrix['candidates'];expected={r['alias']:r for r in handoff};need(len(rows)==9 and len(expected)==9 and {r['alias'] for r in rows}==set(expected),'Exact9candidate keys required');need(len({r['candidate_id'] for r in rows})==9,'Duplicate discovery ID');units=matrix['units'];need(len({u['key'] for u in units})==len(units),'Duplicate completed unit key');need(matrix['counts']['new_GPU_units']==sum(not u['reused'] for u in units) and matrix['counts']['reused_GPU_units']==sum(u['reused'] for u in units),'Incorrect new/reused unit totals');need(sum(u['reused'] for u in units)==10,'Historical10completed units must remain separately identified')
 for u in units:
  need(u['actual_source_identity_sha256']==(source_old if u['reused'] else source_new),'Historical unit relabeled to a new source or stale new source');need(u['actual_runtime_lock_sha256']==runtime_sha,'Unqualified runtime relabeling');need(u['witness_sha256']=='42d64d32b77e946bc962c32d2b801e485d41a095221af49a492079ff0f76fd30','Wrong TRAIN witness')
 ps={p['alias']:p for p in payloads['payloads']};need(set(ps)==set(expected),'Payload scope missing');eligible=[]
 for r in rows:
  h=expected[r['alias']];p=ps[r['alias']];need(r['candidate_id']==h['candidate_id']==p['candidate_id'],'Discovery substitution');need(r['mirror_payload_revision']==p['payload_revision']==h['payload_revision'] and r['mirror_receipt_revision']==p['receipt_revision']==h['receipt_revision'],'Payload/receipt revisions interchanged or substituted');need(r['native_shard_sha256']==p['native_shard_sha256']==h['native_shard_sha256'],'Native content pin differs');need(len(p['members'])==9 and sum(f['bytes'] for f in p['members'])==h['payload_bytes'],'Mirror member/byte closure differs');need(r['immediate_parent_identity'] is None and not r['parent_relative_or_causal_effects_admitted'],'Unknown parent became a causal comparator')
  if r['local_technical_status']=='PASS':
   variants={u['variant'] for u in units if u['alias']==r['alias'] and (u['reused'] if r['alias'] in ['candidate_01','candidate_02'] else not u['reused'])};need(variants=={'logical1','logical8','repeat8'},'TechnicalPASS lacks all required variants');need(r['strict_loading'] and r['hooks_qualified']==26 and r['width']==1920 and r['actual_LM_head']=='PASS','Missing strict/hooks/LM qualification');need(r['GPU_atol']==1e-4 and r['GPU_rtol']==1e-5 and r['max_scaled_residual']<=1,'Changed tolerance or failed numeric gate');need(SHA.fullmatch(r['model_tensor_content_sha256'] or ''),'No complete tensor identity')
  if r['S04_eligible']:
   need(r['local_technical_status']=='PASS' and r['transport_status'].startswith('PASS'),'Transport alone cannot release model');need(private_pass.get(r['alias']) is True,'Private bytes or route alone cannot replace restoredCPU proof');eligible.append(r['candidate_id'])
  if r['alias']=='candidate_05':need(r['original_upload_privacy'] is None and r['recovery_readback_privacy'] is True,'Candidate05privacy distinction lost')
 need(matrix['counts']['S04_eligible_candidates']==len(eligible),'Eligible count differs from actualkeys')
 if len(eligible)==9:need(matrix['counts']['new_GPU_units']==22,'Full9release lacks22missing/recovery units')
 n=proof['unique_reconstructed_parameter_contents']
 if n is not None:need(proof['all9_same_tensor_layout_and_transform'] and proof['only_injective_BF16toFP32_promotions'] and proof['all_tensor_values_exactly_checked'] and len(proof['native_tensor_content_digests'])==9 and n==len(set(proof['native_tensor_content_digests'].values())),'Serialized hash inequality is not complete reconstructed-model identity proof')
 return {'eligible_candidate_ids':eligible,'candidate_count':9,'new_GPU_units':matrix['counts']['new_GPU_units'],'reused_GPU_units':10,'status':'PASS'}
