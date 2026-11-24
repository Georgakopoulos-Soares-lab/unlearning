"""Fresh-consumer exhaustive S09 regeneration. Producer data paths are forbidden."""
from s09_common import *
from contrasts import load_endpoints
from paired_producer import paired
from paired_verifier import reconstruct,check_binding
import numpy as np,sys,shutil,collections
root=Path(sys.argv[1]).resolve();assert (root/'control/RECOVERY_CONTRACT.json').is_file();out=root/'regenerated';out.mkdir(exist_ok=True)
forbidden=[str(B/'control'/RUN),str(R),str(A)]
def deny_producer(event,args):
 if event=='open':
  name=args[0]
  if isinstance(name,(str,bytes)):
   name=os.fsdecode(name);resolved=str(Path(name).absolute())
   if any(resolved==x or resolved.startswith(x+'/') for x in forbidden) and not(resolved==str(root) or resolved.startswith(str(root)+'/')):raise PermissionError('Undeclared producer-path fallback forbidden')
sys.addaudithook(deny_producer)
specs=rows(root/'frozen/FROZEN_ADMITTED_KEYS.jsonl');expected={x['id'] for x in specs};assert len(specs)==len(expected)==48924;completed=[];worst={'max_abs_residual':0.0};attempted=validcount=0
for t in TASKS:
 meta=read(root/'endpoints/inputs'/(t+'-dev-metadata.json'));y=np.array([v['label'] for v in meta]);names,inverse=np.unique([v['group'] for v in meta],return_inverse=True);classes=sorted(set(y.tolist()));drawfile=root/'endpoints/inputs'/(t+'-dev.npz')
 with np.load(drawfile,allow_pickle=False) as z:
  assert z['ids'].tolist()==[v['id'] for v in meta] and z['group_names'].tolist()==names.tolist() and np.array_equal(z['row_groups'],inverse);draw=z['group_draws'];assert draw.shape==(2000,len(names))
 group_class=np.array([[np.sum((inverse==i)&(y==cl)) for cl in classes] for i in range(len(names))]);taskmask=(group_class[draw].sum(1)>0).all(1)
 references=load_endpoints(root/'endpoints/references'/t)
 for candidate in ['candidate_'+str(i).zfill(2) for i in range(1,10)]:
  endpoints=load_endpoints(root/'endpoints'/candidate/t);endpoints.update(references);cr=root/'contrasts'/candidate/t;original=rows(cr/'CONTRASTS.jsonl');ids={r['id']:i for i,r in enumerate(original)};assert len(ids)==906
  with np.load(cr/'paired.npz',allow_pickle=False) as z:expected_values=z['draws'];expected_masks=z['valid']
  for ep,point,vector,mask in endpoints.values():
   assert ep['task']==t and ep['cohort_sha256']==digest(meta) and ep['draw_sha256']==sha(drawfile) and ep['row_order_sha256']==digest([v['id'] for v in meta]) and ep['group_order_sha256']==digest([v['group'] for v in meta]) and ep['class_order']==classes;assert np.array_equal(mask,taskmask) and np.array_equal(np.isfinite(vector),mask);assert point==ep['estimate']
  for s in [r for r in specs if r['t']==t and r['c']==candidate]:
   a,tp,tv,tm=endpoints[s['d']];b,rp,rv,rm=endpoints[s['q'] if s['f']=='anchor_policy_gap' else s['q']+'|'+s['m']];check_binding(s,a,b)
   p,v,m,ci=paired(tv,rv,tm,rm,tp,rp);q,w,n,cj=reconstruct(tv,rv,tm,rm,tp,rp);i=ids[s['id']];old=original[i];assert np.array_equal(m,n) and np.array_equal(m,expected_masks[i]) and hashlib.sha256(v.tobytes()).hexdigest()==old['paired_vector_sha256']
   diffs=[abs(p-old['estimate']),abs(p-q),float(np.abs(v[m]-w[m]).max(initial=0)),float(np.abs(v[m]-expected_values[i][m]).max(initial=0))]+[abs(x-y) for x,y in zip(ci,[old['ci_low'],old['ci_high']])]+[abs(x-y) for x,y in zip(ci,cj)];mx=max(diffs);assert mx<=1e-12
   if mx>worst['max_abs_residual']:worst={'max_abs_residual':mx,'id':s['id'],'component_index':diffs.index(mx),'task':t,'candidate':candidate}
   attempted+=2000;validcount+=int(m.sum());completed.append(s['id'])
  print('FRESH_EXHAUSTIVE_NUMERICAL_REGENERATION_PASS',candidate,t,906,flush=True)
assert len(completed)==len(set(completed))==48924 and set(completed)==expected and attempted==97848000
# Rebuild eligibility/coverage and source tables from restored endpoint evidence.
from build_tables import build
tableout=out/'tables';build(root,tableout)
checks=[]
for n,h in read(root/'public/TABLE_REGENERATION_INDEX.json')['files'].items():
 assert sha(tableout/n)==h;checks.append(n)
from figure_specs import make_specs
# Table source equivalence was exact above; rebuild specs against these regenerated tables and restored full contrasts.
shutil.copytree(root/'public/contrasts',tableout/'contrasts');specifications,source=make_specs(tableout);sd=tableout/'figure-specs';sd.mkdir(exist_ok=True)
for spec in specifications:
 assert spec==read(root/'public/figure-specs'/(spec['id']+'.json'));save(sd/(spec['id']+'.json'),spec)
import runpy
before=list(sys.argv);sys.argv=[str(root/'code/write_analysis.py'),str(tableout)];runpy.run_path(str(root/'code/write_analysis.py'),run_name='__main__');sys.argv=before
for name in ['ANALYSIS.md','COMPARISON_SUMMARY.jsonl','ANCHOR_AUROC_SUMMARY.jsonl','CLAIM_EVIDENCE_LEDGER.jsonl','CLAIM_VALIDATION.json','METRIC_DISAGREEMENT.jsonl','SEED_DIRECTION_EXCEPTIONS.jsonl','LIMITATIONS.json']:
 assert sha(tableout/name)==sha(root/'public'/name);checks.append(name)
save(out/'NUMERICAL_RECOVERY.json',{'status':'PASS','regenerated_specifications':len(completed),'attempted_draw_differences':attempted,'valid_draw_differences':validcount,'exact_masks':True,'atol':1e-12,'rtol':0,'worst':worst,'complete_keyset_sha256':digest(sorted(completed)),'regenerated_tables_exact_SHA256':checks,'regenerated_figure_specifications':len(specifications),'producer_path_fallback':False,'producer_paths_denied_by_audit_hook':True,'new_fits':0,'GPU_replay':False,'clean_runtime_recreation_claim':False});print('FRESH_EXHAUSTIVE_S09_REGENERATION_COMPLETE',attempted,flush=True)
