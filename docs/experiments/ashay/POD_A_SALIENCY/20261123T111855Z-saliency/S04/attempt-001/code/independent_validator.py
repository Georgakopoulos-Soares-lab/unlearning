"""Independent S04 set/counter/identity validator; standard library, no science imports."""
from pathlib import Path,PurePosixPath
from collections import Counter,defaultdict
import json,hashlib,itertools,sys
T=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];L=[f'decoder.layers.{i}' for i in range(25)]+['decoder.final_norm'];S=[42,17,1234];P=['independent_refit','fixed_original_base'];M=['AUROC','AP','accuracy','balanced_accuracy','cross_entropy'];A=['decoder.layers.16','decoder.final_norm']
def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def h(x):return hashlib.sha256(enc(x)).hexdigest()
def check(v,message):
 if not v:raise ValueError(message)
def signature(r):return tuple((k,r.get(k)) for k in ['k','c','t','r','s','p','split','m','f','ctrl','j','fold'] if k in r)
def expected_signatures(candidates,audit):
 result=set()
 def add(k,**d):z={'k':k,**d};sg=signature(z);check(sg not in result,'independent expected duplicate');result.add(sg)
 for c,t in itertools.product(candidates,T):
  for split in ['train','dev']:
   add('extraction',c=c,t=t,split=split);add('LM',c=c,t=t,split=split,r=None,s=None,p='LM')
   for m in ['LM_NLL','LM_PPL']:add('LM_metric',c=c,t=t,split=split,r=None,s=None,p='LM',m=m)
  for r,s in itertools.product(L,S):
   for k,p in [('final_head','independent_refit'),('fixed_application','fixed_original_base')]:add(k,c=c,t=t,r=r,s=s,p=p)
   calls=[(j,f) for f in range(3 if t==T[0] else 5) for j in range(3)]+[(None,None)]
   for j,f in calls:add('optimizer_call',c=c,t=t,r=r,s=s,p='independent_refit',j=j,fold=f)
   for p in P:
    add('prediction',c=c,t=t,r=r,s=s,p=p,split='dev')
    for m in M:
     add('classifier_metric',c=c,t=t,r=r,s=s,p=p,split='dev',m=m)
     for f in ['base_reference','immediate_parent']:add('contrast',f=f,c=c,t=t,r=r,s=s,p=p,split='dev',m=m)
     if r in A:
      for ctrl in ['composition','4mer']:add('contrast',f='DNA_control',c=c,t=t,r=r,s=s,p=p,split='dev',m=m,ctrl=ctrl)
   if r in A:add('contrast',f='anchor_policy_gap',c=c,t=t,r=r,s=s,p='independent_refit',split='dev',m='AUROC')
  for m in ['LM_NLL','LM_PPL']:add('contrast',f='LM_base_reference',c=c,t=t,r=None,s=None,p='LM',split='dev',m=m)
 for a in audit:
  add('audit_refit',**a,p='independent_refit')
  for j,f in [(j,f) for f in range(3 if a['t']==T[0] else 5) for j in range(3)]+[(None,None)]:add('audit_optimizer_call',**a,p='independent_refit',j=j,fold=f)
 return result

def check_key_sets(actual,expected):
 check(len(actual)==len(set(actual)),'duplicate collection keys')
 check(set(actual)==set(expected),'missing or extra collection keys')

def audit_expected():
 cs=[f'candidate_{i:02d}' for i in range(1,10)];rows=[]
 # Independent iteration by task/anchor rather than candidate-major planner loop.
 for ti,task in enumerate(T):
  for ai,layer in enumerate(A):
   for ci,c in enumerate(cs):rows.append({'c':c,'t':task,'r':layer,'s':S[(ci+ti+ai)%3]})
 scores={layer:hashlib.sha256(('S04-AUDIT-v1\n28687da949b4a46bbf8c6015bb8721376e939b70\n'+layer).encode()).hexdigest() for layer in L if layer not in A};ranked=sorted(scores,key=lambda x:(scores[x],x))
 for n in range(18):rows.append({'c':cs[n//2],'t':T[n%6],'r':ranked[n],'s':S[((n//6)+(n%3))%3]})
 return rows

def validate_record(r,inp,rules,bases):
 aliases={v['alias']:v for v in inp['candidates']};refs={(v['task'],v['representation'],v['cv_seed']):v for v in inp['references']};base={(v['task'],v['representation'],v['cv_seed']):v for v in inp['base_prediction_endpoints']};ctrl={(v['task'],v['control'],v['cv_seed']):v for v in inp['controls']};cp={(v['task'],v['control'],v['cv_seed']):v for v in inp['control_prediction_endpoints']};fold={(v['task'],v['cv_seed']):v['sha256'] for v in inp['folds']}
 def one(row):
  check(set(row)<=set(['id','k','c','t','r','s','p','split','m','f','ctrl','j','fold','d','q','ref','why']),'unknown unit fields or fabricated artifact hash');c=row['c'];t=row['t'];rep=row.get('r');seed=row.get('s');pol=row.get('p');fam=row.get('f');check(c in aliases and t in T,'extra candidate/task');check(row.get('split') in [None,'train','dev'],'wrong split/test admitted');check('estimate' not in row and 'producer_hash' not in row,'future outcomes fabricated')
  lm=row['k'] in ['LM','LM_metric'] or fam=='LM_base_reference'
  if lm:check(rep is None and seed is None and pol=='LM','LM layer/seed expansion')
  elif row['k']!='extraction':check(rep in L and seed in S and pol in P,'classifier dimensions')
  if row['k']=='contrast':
   if fam=='immediate_parent':check(row.get('q') is None and row.get('why')=='UNKNOWN_PARENT_INTERVENTION_EXPOSURE','guessed parent promoted')
   elif fam=='LM_base_reference':check(row.get('q') is None and row.get('why'),'unavailable LM endpoint promoted')
   elif fam=='base_reference':check(row['q']==h(base[(t,rep,seed)]),'wrong reference prediction/cohort/draw binding')
   elif fam=='DNA_control':check(rep in A and row['q']==h(cp[(t,row['ctrl'],seed)]),'control scope/binding')
   elif fam=='anchor_policy_gap':check(rep in A and row['m']=='AUROC' and pol=='independent_refit','policy-gap family drift')
   else:raise ValueError('extra contrast family')
  if row['k']=='fixed_application':check(row['ref']==refs[(t,rep,seed)]['head_sha256'],'replacement or wrong reference head')
  key=(c,t,rep,seed,pol,fam,row.get('ctrl'))
  if key not in bases:
   b={'rules_sha256':h(rules),'candidate_content':aliases[c]['model_tensor_content_sha256'],'task_cohort':inp['cohorts'][t],'runtime':inp['runtime_evidence'],'fold':fold.get((t,seed))}
   if pol=='fixed_original_base' or fam in ['base_reference','anchor_policy_gap']:b['base_head']=refs.get((t,rep,seed),{}).get('head_sha256')
   if fam=='base_reference':b['base_prediction']=base[(t,rep,seed)]
   if fam=='DNA_control':b['control']=ctrl[(t,row['ctrl'],seed)];b['control_prediction']=cp[(t,row['ctrl'],seed)]
   bases[key]=h(b)
  spec={k:v for k,v in row.items() if k!='id'};want=hashlib.sha256(b'S04-PLANNED-UNIT-v1\n'+bases[key].encode()+b'\n'+enc(spec)).hexdigest();check(row['id']==want,'planned identity mismatch')
 return one

def safe_metadata_member(value):
 q=PurePosixPath(value);check(not q.is_absolute() and '..' not in q.parts and '\\' not in str(q),'unsafe metadata path')

def global_contract(inp,rules,cov):
 check(all(v['parent_id'] is None and v['independent_intervention_replicates'] is None and not v['causal_interpretation_eligible'] for v in inp['candidates']),'seed-as-replicate or guessed parent')
 check(rules['metrics']['direction']['cross_entropy']=='lower_better' and rules['metrics']['direction']['LM_NLL']=='lower_better' and rules['metrics']['direction']['AUROC']=='higher_better','wrong metric direction')
 for task in T:
  check(inp['cohorts'][task]['train']['rows']==(11971 if task=='emp_H3' else 1024) and inp['cohorts'][task]['dev']['rows']==(1497 if task=='emp_H3' else 512),'incorrect cohort denominator')
 check(inp['cohorts']['gue_splice_reconstructed']['dev']['groups']==511,'sample/group denominator confusion')
 check(all(cov['reused'][k]==0 for k in ['production_extractions','saliency_final_heads','saliency_fixed_applications','saliency_predictions']),'false reused production counts')
 for v in inp['source']+inp['folds']+inp['draws']:safe_metadata_member(v['metadata_member'])

def validate(directory,inp):
 root=Path(directory);load=lambda n:json.loads((root/n).read_text());pro=load('PROTOCOL_FREEZE.json');rules=pro['semantic']['rules'];global_contract(inp,rules,load('COVERAGE_PLAN.json'));check(pro['semantic_protocol_sha256']==h(pro['semantic']),'protocol semantic seal mismatch');
 ordered=json.loads(json.dumps(inp))
 for name,key in [('candidates',lambda v:v['alias']),('folds',lambda v:(T.index(v['task']),S.index(v['cv_seed']))),('draws',lambda v:T.index(v['task'])),('source',lambda v:v['path']),('references',lambda v:(T.index(v['task']),L.index(v['representation']),S.index(v['cv_seed']))),('controls',lambda v:(T.index(v['task']),v['control'],S.index(v['cv_seed']))),('base_prediction_endpoints',lambda v:(T.index(v['task']),L.index(v['representation']),S.index(v['cv_seed']))),('control_prediction_endpoints',lambda v:(T.index(v['task']),v['control'],S.index(v['cv_seed']))),('S03_units',lambda v:v['key'])]:ordered[name].sort(key=key)
 check(h(ordered)==pro['semantic']['planning_foundation_sha256'],'broken freeze/foundation binding')
 check(pro['semantic']['cohorts']==inp['cohorts'] and pro['semantic']['candidates']==inp['candidates'],'frozen input scope mismatch')
 cs=[v['alias'] for v in inp['candidates']];check(cs==[f'candidate_{i:02d}' for i in range(1,10)] and len({v['candidate_id'] for v in inp['candidates']})==9 and len({v['model_tensor_content_sha256'] for v in inp['candidates']})==9,'missing/duplicate/extra candidate or content mapping');check(all(v['parent_id'] is None and v['independent_intervention_replicates'] is None and not v['causal_interpretation_eligible'] for v in inp['candidates']),'seed-as-replicate or parent invention');check(rules['tasks']==T and rules['splits']==['train','dev'] and rules['representations']==L and rules['anchors']==A and rules['CV_seeds']==S,'task/layer16/seed/split mapping changed');check(rules['metrics']['direction']=={'AUROC':'higher_better','AP':'higher_better','accuracy':'higher_better','balanced_accuracy':'higher_better','cross_entropy':'lower_better','LM_NLL':'lower_better','LM_PPL':'lower_better'},'wrong metric directions');check(not rules['uncertainty']['equivalence_noninferiority_preservation_success_enabled'],'unauthorized confirmatory claim')
 refkeys={(v['task'],v['representation'],v['cv_seed']) for v in inp['references']};check(refkeys==set(itertools.product(T,L,S)) and len(inp['references'])==468,'reference keys');check(len(inp['controls'])==36 and len(inp['S03_units'])==32,'false reuse domain');check(inp['cohorts']['gue_splice_reconstructed']['dev']['rows']==512 and inp['cohorts']['gue_splice_reconstructed']['dev']['groups']==511,'incorrect sample/group denominator')
 for v in inp['references']:
  check(v['fold_sha256']==next(f['sha256'] for f in inp['folds'] if f['task']==v['task'] and f['cv_seed']==v['cv_seed']),'mismatched fold identity');check(v['manifest_sha256']==inp['cohorts'][v['task']]['train']['source_manifest_sha256'],'mismatched source cohort');check(v['class_order']==inp['cohorts'][v['task']]['train']['class_order'],'class order changed')
 for ep in inp['base_prediction_endpoints']:
  ref=next(v for v in inp['references'] if (v['task'],v['representation'],v['cv_seed'])==(ep['task'],ep['representation'],ep['cv_seed']));check(ep['head_sha256']==ref['head_sha256'] and ep['class_order']==ref['class_order'],'reference prediction/head class join');check(ep['cohort_sha256']==inp['cohorts'][ep['task']]['dev']['ordered_metadata_sha256'],'reference prediction/cohort join');check(ep['draw_sha256']==next(v['file_sha256'] for v in inp['draws'] if v['task']==ep['task']),'reference prediction/draw join')
 panel=load('AUDIT_PANEL.json');expect_audit=audit_expected();key=lambda z:tuple(z[x] for x in ['c','t','r','s']);check(len(panel['units'])==126 and {key(z) for z in panel['units']}=={key(z) for z in expect_audit},'audit key drift');h3=[z for z in panel['units'] if z['t']=='emp_H3'];check(len(h3)==21 and panel['H3_subset']==h3 and load('H3_AUDIT_SUBSET.json')['units']==h3,'missing/wrong H3 subset');check(Counter(z['s'] for z in h3)=={42:7,17:7,1234:7},'H3 seed stratum');check(Counter(z['s'] for z in panel['units'])=={42:42,17:42,1234:42},'audit seed stratum');check(len({z['r'] for z in panel['units']})==20,'audit representation denominator')
 for c,t in itertools.product(cs,T):check(len([z for z in panel['units'] if z['c']==c and z['t']==t and z['r'] in A])==2,'audit anchor coverage')
 expected=expected_signatures(cs,expect_audit);seen=set();ids=set();rows=[];counts=Counter();families=Counter();khash={};bases={};one=validate_record(None,inp,rules,bases);filehash=hashlib.sha256();phase=Counter()
 with (root/'EXPECTED_UNIT_KEYS.jsonl').open('rb') as f:
  for line in f:
   filehash.update(line);row=json.loads(line);one(row);check(row['id'] not in ids,'duplicate unit ID');sg=signature(row);check(sg in expected and sg not in seen,'missing/extra/duplicate typed unit key');ids.add(row['id']);seen.add(sg);rows.append(row);counts[row['k']]+=1;khash.setdefault(row['k'],hashlib.sha256()).update(row['id'].encode()+b'\n')
   if row['k']=='contrast':families[row['f']]+=1;owner='S09'
   elif row['k'] in ['audit_refit','audit_optimizer_call']:owner='S05' if row['t']==T[0] else 'S08'
   elif row['t']==T[0]:owner='S05'
   elif row['k'] in ['extraction','LM','LM_metric']:owner='S06'
   else:owner='S07'
   phase[owner]+=1
 check_key_sets(seen,expected);check(counts=={'extraction':108,'LM':108,'LM_metric':216,'final_head':4212,'fixed_application':4212,'optimizer_call':63180,'prediction':8424,'classifier_metric':42120,'contrast':91152,'audit_refit':126,'audit_optimizer_call':1890},'wrong independent count domains');check(families=={'base_reference':42120,'DNA_control':6480,'anchor_policy_gap':324,'LM_base_reference':108,'immediate_parent':42120},'wrong family denominators')
 lookup={r['id']:r for r in rows};bykey={signature(r):r['id'] for r in rows}
 def lookupid(k,**d):return bykey[signature({'k':k,**d})]
 for r in rows:
  k=r['k'];c=r['c'];t=r['t'];l=r.get('r');s=r.get('s');p=r.get('p')
  if 'd' in r:check(r['d'] in ids,'dangling dependency')
  if k=='final_head':check(r['d']==lookupid('extraction',c=c,t=t,split='train'),'head linked wrong extraction')
  if k=='fixed_application':check(r['d']==lookupid('extraction',c=c,t=t,split='dev'),'application linked wrong cohort')
  if k=='prediction':check(r['d']==lookupid('final_head' if p=='independent_refit' else 'fixed_application',c=c,t=t,r=l,s=s,p=p),'wrong prediction policy/source')
  if k=='classifier_metric':check(r['d']==lookupid('prediction',c=c,t=t,r=l,s=s,p=p,split='dev'),'wrong metric probability path')
  if k=='contrast' and r['f']=='anchor_policy_gap':check(r['q']==lookupid('classifier_metric',c=c,t=t,r=l,s=s,p='fixed_original_base',split='dev',m='AUROC'),'gap endpoint mismatch')
 cov=load('COVERAGE_PLAN.json');check(cov['requested']==counts and cov['contrast_families']==families and cov['expected_keys_sha256']==filehash.hexdigest(),'coverage file/count/hash drift');check(all(cov['reused'][k]==0 for k in ['production_extractions','saliency_final_heads','saliency_fixed_applications','saliency_predictions']),'false production reuse');check(sum(inp['cohorts'][t][s]['rows'] for t,s in itertools.product(T,['train','dev']))==21148 and cov['logical_rows_all_candidates']==190332,'wrong logical row denominator');check(cov['production_optimizer_calls_excluding_retries']==sum(9*26*3*(3*(3 if t==T[0] else 5)+1) for t in T)==63180,'production optimizer count');check(sum((10 if r['t']==T[0] else 16) for r in panel['units'])==1890,'audit optimizer count')
 check({k:v['requested'] for k,v in cov['by_phase'].items()}==dict(phase),'phase count drift');check(cov['by_phase']['S09']['admitted_spec']==48924 and cov['by_phase']['S09']['deferred']==42228,'phase admitted/deferred drift');con=load('CONTRAST_PLAN.json');check(con['admitted_spec']==48924 and con['deferred']==42228,'wrong admitted/deferred');check(not con['all_pairs_search'],'unsupported family search');check(load('BOOTSTRAP_PLAN.json')['draw_generation_in_S04'] is False,'new draw generation');check(len(load('BOOTSTRAP_PLAN.json')['exact_existing_dev_draws'])==6,'missing draw identities')
 for v in inp['source']+inp['folds']+inp['draws']:
  q=PurePosixPath(v['metadata_member']);check(not q.is_absolute() and '..' not in q.parts and '\\' not in str(q),'unsafe metadata path')
 return {'status':'PASS','unit_records':len(rows),'counts':dict(counts),'contrast_counts':dict(families),'phase_owned_records':dict(phase),'expected_keys_sha256':filehash.hexdigest(),'independent_expected_set_digest':hashlib.sha256('\n'.join(sorted(repr(sg) for sg in seen)).encode()).hexdigest(),'independent_audit_key_set_digest':h(sorted(expect_audit,key=lambda r:(r['c'],r['t'],r['r'],r['s']))),'audits':126,'H3_audits':21,'dependent_links_verified':True,'unit_identity_contract_verified':True}
if __name__=='__main__':print(json.dumps(validate(sys.argv[1],json.loads(Path(sys.argv[2]).read_text())),indent=2),flush=True)
