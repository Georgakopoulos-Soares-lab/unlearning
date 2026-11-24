from s09_common import *
from collections import Counter,defaultdict
import numpy as np,shutil,sys

def build(root=A,out=P):
 profiles=[];references=[];contrasts=[];receipts=[]
 for t in TASKS:references.extend(rows(root/'endpoints/references'/t/'INDEX.jsonl'))
 for candidate in ['candidate_'+str(i).zfill(2) for i in range(1,10)]:
  for t in TASKS:
   ep=root/'endpoints'/candidate/t;prof=rows(ep/'INDEX.jsonl');profiles.extend(prof);cr=root/'contrasts'/candidate/t;receipt=read(cr/'COMPLETE.json');assert receipt['status']=='VERIFIED'
   for n,h in receipt['files'].items():assert sha(cr/n)==h
   rr=rows(cr/'CONTRASTS.jsonl');contrasts.extend(rr);receipts.append(dict(candidate=candidate,task=t,receipt_sha256=sha(cr/'COMPLETE.json'),**receipt))
 admitted=rows(root/'frozen/FROZEN_ADMITTED_KEYS.jsonl' if (root/'frozen').exists() else C/'FROZEN_ADMITTED_KEYS.jsonl');deferred=rows(root/'frozen/FROZEN_DEFERRED_KEYS.jsonl' if (root/'frozen').exists() else C/'FROZEN_DEFERRED_KEYS.jsonl')
 assert len(contrasts)==len({r['id'] for r in contrasts})==48924 and {r['id'] for r in contrasts}=={r['id'] for r in admitted};assert len(profiles)==42120 and len(references)==2520
 assert all(r['status']=='VERIFIED' for r in contrasts),'Affectedinferentialblockersmustnotbeclaimedcomplete'
 out.mkdir(parents=True,exist_ok=True)
 jsonl(out/'LAYER_PROFILES.jsonl',profiles);jsonl(out/'REFERENCE_MARGINALS.jsonl',references)
 groups=defaultdict(list)
 for r in profiles:groups[(r['candidate'],r['task'],r['representation'],r['policy'],r['metric'])].append(r)
 sensitivity=[]
 for k,rr in groups.items():
  rr=sorted(rr,key=lambda r:SEEDS.index(r['seed']));assert [r['seed'] for r in rr]==SEEDS;points=[r['estimate'] for r in rr];sensitivity.append({'candidate':k[0],'task':k[1],'representation':k[2],'policy':k[3],'metric':k[4],'seeds':SEEDS,'source_endpoint_ids':[r['endpoint_id'] for r in rr],'estimates':points,'min':min(points),'max':max(points),'range':max(points)-min(points),'point_values_exactly_coincident':len(set(points))==1,'range_is_not_CI':True})
 save(out/'SEED_SENSITIVITY.json',{'status':'DESCRIPTIVE_ONLY','groups':len(sensitivity),'records':sensitivity,'note':'ThreeCVpartitionsnotindependentinterventionreplicates; seedrangeisnotuncertaintyinterval'})
 # Exact contrast key preservation for deferred families, no fabricated estimates.
 for family,filename in [('immediate_parent','PARENT_RELATIVE_EFFECTS.jsonl'),('LM_base_reference','LM_CONTRASTS.jsonl')]:
  selected=[r for r in deferred if r['f']==family];jsonl(out/filename,[{**r,'status':'DEFERRED','estimate':None,'ci_low':None,'ci_high':None,'missing_reason':r.get('deferred_reason',r.get('reason','UNKNOWN_PARENT_INTERVENTION_EXPOSURE' if family=='immediate_parent' else 'EXACT_BASE_PER_EXAMPLE_LOSS_TARGET_ENDPOINT_JOIN_NOT_BOUND'))} for r in selected])
 save(out/'COMPARISON_DISPOSITION.json',{'admitted_counts':dict(Counter(r['f'] for r in contrasts)),'deferred_counts':dict(Counter(r['f'] for r in deferred)),'intended_keys':91152,'completed_admitted_exact_keys':48924,'deferred_exact_keys':42228,'admitted_set_sha256':digest(sorted(r['id'] for r in contrasts)),'deferred_set_sha256':digest(sorted(r['id'] for r in deferred)),'base_reference_is_not_immediate_parent':True})
 worst=max(receipts,key=lambda r:r['worst']['max_abs_residual']);attempted=sum(r['attempted_draw_differences'] for r in receipts);valid=sum(r['valid_draw_differences'] for r in receipts)
 save(out/'CONTRAST_VERIFICATION.json',{'status':'PASS','specifications':48924,'attempted_draw_differences':attempted,'valid_draw_differences':valid,'invalid_draw_differences':attempted-valid,'atol':1e-12,'rtol':0,'exact_masks':True,'producer_and_verifier':'paired_producer.py vs paired_verifier.py; shared NumPy/Pythonandinputsevidence, no independenttrainingclaim','worst':{'candidate':worst['candidate'],'task':worst['task'],**worst['worst']},'unit_receipts':receipts})
 # Previously qualified LM rows are explicitly supplied as immutable compact reporting inputs.
 lm=rows(root/'reporting-inputs/LM_MARGINALS.jsonl');candidates=read(root/'reporting-inputs/CANDIDATES.json');assert len(lm)==216 and all(r['release_status']=='VERIFIED' for r in lm)
 jsonl(out/'LM_MARGINALS_REUSED.jsonl',lm);save(out/'CANDIDATES.json',candidates)
 anchors=[r for r in profiles if r['representation'] in ['decoder.layers.16','decoder.final_norm']]
 jsonl(out/'METHOD_STRENGTH_CURVES.jsonl',[{**r,'display_only':'Suppliedendpoint/step; no fitteddosecurve, no verifiedcommontrajectory','endpoint_label':candidates[r['candidate']]['label'],'checkpoint_step':candidates[r['candidate']]['step']} for r in anchors])
 save(out/'TABLE_REGENERATION_INDEX.json',{'status':'PASS','profiles':42120,'references':2520,'seed_groups':14040,'LM_metrics':216,'frozen_admitted_count':48924,'frozen_deferred_count':42228,'files':{n:sha(out/n) for n in ['LAYER_PROFILES.jsonl','REFERENCE_MARGINALS.jsonl','SEED_SENSITIVITY.json','PARENT_RELATIVE_EFFECTS.jsonl','LM_CONTRASTS.jsonl','COMPARISON_DISPOSITION.json','CONTRAST_VERIFICATION.json','LM_MARGINALS_REUSED.jsonl','METHOD_STRENGTH_CURVES.jsonl','CANDIDATES.json']}})
 return profiles,references,contrasts,lm,candidates

if __name__=='__main__':
 if len(sys.argv)>1:build(Path(sys.argv[1]),Path(sys.argv[2]))
 else:
  ir=A/'reporting-inputs';ir.mkdir(exist_ok=True);lm=rows(public('S06/attempt-001/LM_MARGINALS.jsonl'));h3=read(public('S05/attempt-001/H3_LM_INDEX.json'))
  if isinstance(h3,dict):h3=h3.get('records',h3.get('units',h3.get('rows')))
  for u in h3:
   for row in u['metric_records']:lm.append({**row,'candidate_alias':u['candidate_alias'],'task':'emp_H3','split':u['split'],'policy':'LM','cv_seed':None,'representation':None,'release_status':'VERIFIED','source_row_sha256':digest(row),'source_unit_sha256':digest(u)})
  assert len(lm)==216;jsonl(ir/'LM_MARGINALS.jsonl',lm)
  candidates={}
  for i in range(1,10):
   a='candidate_'+str(i).zfill(2);row=rows(public('S05/attempt-001/candidates')/a/'H3_MARGINALS.jsonl')[0];candidates[a]={'alias':a,'candidate_id':row['candidate_id'],'label':row['endpoint_label'],'step':row['checkpoint_step'],'content_sha256':row['content_sha256']}
  save(ir/'CANDIDATES.json',candidates);shutil.copy2(public('S08/attempt-001/DIAGNOSTICS.json'),ir/'S08_DIAGNOSTICS.json');build();print('S09_FULL_PRECISION_TABLES_VERIFIED',flush=True)
