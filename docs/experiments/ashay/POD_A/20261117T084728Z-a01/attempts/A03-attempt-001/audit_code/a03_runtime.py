"""Recover exact training-only fixtures, source/runtime identities and A04 dependencies."""
from a03_common import *
import ast,shutil,subprocess

def main(c):
 c.family='runtime';ensure(jread(c.c/'DATA_AUDIT.json')['status']=='PASS','Frozen cohort gate required');bundle=c.a/'a04-training-only';bundle.mkdir(exist_ok=True);allrows=sum([c.rows(g) for g in HASHES],[]);by={r['id']:r for r in allrows};old=c.roots['base_R1'];new=c.roots['R3'];smokes=[];ids=[]
 for p in sorted((old/'smokes-fixed8/base-b8').glob('chunk_*.npz')):
  with np.load(c.ref(p)['path'],allow_pickle=False) as z:ids.extend(z['ids'].tolist())
 ensure(len(ids)==len(set(ids))==12,'Smoke population must be twelve unique occurrences');rr=[by[i] for i in ids];ensure(all(r['split']=='train' for r in rr),'Held-out row in runtime fixture');ensure(collections.Counter(r['task'] for r in rr)=={t:2 for t in TASKS},'Smoke task accounting differs')
 raw=(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rr)).encode();ensure(hashlib.sha256(raw).hexdigest()==SMOKE_SHA,'Exact historical smoke manifest recovery failed');smoke_path=bundle/'training_smoke_manifest.jsonl';smoke_path.write_bytes(raw)
 write_csv(bundle/'TRAINING_ROW_DIGESTS.csv',[{'ordinal':i,'id':r['id'],'task':r['task'],'split':r['split'],'label':r['label'],'sequence_sha256':hashlib.sha256(r['sequence'].encode()).hexdigest(),'exact_rc_group':r['exact_rc_group'],'length':len(r['sequence'])} for i,r in enumerate(rr)])
 anchors={};comps=[]
 for role,root,arm,parent in [('base',old,'base','smokes-fixed8'),('R1',old,'maxent','smokes-fixed8'),('R3',new,'new','smokes')]:
  values={}
  for variant in ['b1','b8','repeat']:
   folder=root/parent/(arm+'-'+variant);receipt=c.receipt(folder/'COMPLETE.json');ensure(receipt['examples']==12,'Smoke receipt count differs');identity=jread(folder/'identity.json');ensure(identity['manifest_sha256']==SMOKE_SHA and identity['physical_batch_size']==8 and identity['smoke'] and identity['batch_size']==(1 if variant=='b1' else 8),'Historical smoke identity differs');parts={k:[] for k in LAYERS+['ids','labels','split','task','groups','sequence_sha256','lengths','n_tokens','nll_sum']};cursor=0
   for p in sorted(folder.glob('chunk_*.npz')):
    with np.load(c.ref(p)['path'],allow_pickle=False) as z:
     n=len(z['ids']);expect=rr[cursor:cursor+n];ensure(z['cache_key'].item()==identity['cache_key'],'Smoke chunk cache identity differs')
     for key,want in [('ids',[r['id'] for r in expect]),('labels',[r['label'] for r in expect]),('split',['train']*n),('task',[r['task'] for r in expect]),('groups',[r['exact_rc_group'] for r in expect]),('sequence_sha256',[hashlib.sha256(r['sequence'].encode()).hexdigest() for r in expect]),('lengths',[len(r['sequence']) for r in expect]),('n_tokens',[len(r['sequence'])-1 for r in expect])]:
      if key in z.files:ensure(z[key].tolist()==want,'Smoke association/target mismatch '+key)
      else:ensure(identity['schema']=='multiretain-all-layers-fixed8-v2' and key in ['task','groups','lengths'],'Unexpected missing smoke field')
     for key in LAYERS:ensure(z[key].shape==(n,1920) and z[key].dtype==np.float32 and np.isfinite(z[key]).all(),'Smoke representation shape/dtype/finiteness')
     ensure(z['nll_sum'].dtype==np.float32 and np.isfinite(z['nll_sum']).all() and np.all(z['nll_sum']>=0),'Smoke loss invalid')
     for k in parts:
      if k in z.files:parts[k].append(z[k])
      else:parts[k].append(np.array([r['task'] if k=='task' else r['exact_rc_group'] if k=='groups' else len(r['sequence']) for r in expect]))
     cursor+=n
   ensure(cursor==12,'Smoke population/fillers mismatch');value={k:np.concatenate(v) for k,v in parts.items()};values[variant]=value;target=bundle/f'{role}_{variant}_historical_anchors.npz';np.savez_compressed(target,**value);smokes.append({'role':role,'variant':variant,'logical_batch':1 if variant=='b1' else 8,'physical_batch':8,'examples':12,'all_training':True,'representations':[hook(k) for k in LAYERS],'width':1920,'features_dtype':'float32','loss_sum_dtype':'float32','historical_receipt':c.ref(folder/'COMPLETE.json'),'identity':c.ref(folder/'identity.json'),'bundle_path':str(target),'bundle_sha256':sha(target),'scope':'Recovered archived same-model anchors; not current GPU replication','metadata_derived_in_owned_bundle':(['task','groups','lengths'] if identity['schema']=='multiretain-all-layers-fixed8-v2' else []),'derivation_evidence':'Exact frozen smoke-manifest SHA plus stored ordered IDs, labels, split, sequence digests and target counts; historical NPZ files unchanged'})
  for variant in ['b1','repeat']:
   for k in LAYERS+['nll_sum']:
    delta=maxerr(values['b8'][k],values[variant][k]);ensure(np.allclose(values['b8'][k],values[variant][k],atol=1e-4,rtol=1e-5),'Historical fixed8 smoke comparison differs');comps.append({'role':role,'comparison':variant+'-b8','array':k,'max_abs_residual':delta,'status':'PASS'})
  anchors[role]={'all_26_representations':True,'logical_1_logical_8_repeat':'All three variants saved and freshly CPU-compared','weight_identity_qualification':'Historical identities only; A04 must verify reacquired weights and same-model runtime'}
 # Bind every provenance identity to actual archived source/config/tokenizer/sidecar bytes.
 sources=[];source_matches=[];feature_provenance=[]
 for key in ['base_R1','R3','preparation','controls']:
  root=c.roots[key]
  for p in sorted((root/'source').rglob('*')):
   if p.is_file() and p.suffix in ['.py','.md','.json','.txt','.yaml']:
    ref=c.ref(p);sources.append({'dependency':key,**ref,'archived_relative_path':str(p.relative_to(root))})
 file_by_hash=collections.defaultdict(list)
 for p,e in c.lookup.items():file_by_hash[e['sha256']].append(p)
 fs=jread(c.c/'FEATURE_STRUCTURAL_AUDIT.json')['families']
 for f in fs:
  ident=jread(f['identity']['path']);matches={}
  for name in ['source_sha256','support_sha256','fixed_batch_source_sha256','config_sha256','tokenizer_sha256','checkpoint_metadata_sha256']:
   expected=ident.get(name);found=file_by_hash.get(expected,[]) if expected else [];ensure(found,'Historical feature identity dependency not recovered: '+name);matches[name]=[c.ref(p) for p in found]
  ensure(ident['physical_batch_size']==8 and ident['feature_width']==1920 and ident['padding']=='right to1000, pad1' and ident['pool']=='mean nucleotide positions; padding excluded' and ident['attention_backend']=='TE unfused','Historical feature preprocessing protocol differs')
  ensure(ident['hooks']==[hook(k) for k in LAYERS] and ident['batch_size']==8 and ident['feature_dtype']=='float32','Historical extraction hook/batch/dtype differs');feature_provenance.append({'role':f['role'],'group':f['group'],'status':'PASS','identity':f['identity'],'actual_archived_matches':matches,'checkpoint_weights':f['historical_weights'],'weights_read_in_A03':False})
 for rootkey in ['base_R1','R3']:
  for g in HASHES:
   identity=jread(c.roots[rootkey]/'probes'/g/'run_identity.json');matches={}
   for field in ['source_sha256','metrics_source_sha256','training_source_sha256']:
    ensure(file_by_hash.get(identity[field]),'Fit execution source missing: '+field);matches[field]=[c.ref(p) for p in file_by_hash[identity[field]]]
   source_matches.append({'dependency':rootkey,'group':g,'identity':c.ref(c.roots[rootkey]/'probes'/g/'run_identity.json'),'source_bindings':matches})
 # Known repository anchors are read without checkout/reset or mutation.
 pinned=[]
 for rev,files in [('c79ab07e763a9754c68fdaf7d0730d8458f508dc',['scripts/sayyed/extract_multiretain_fixed.py','scripts/sayyed/fit_multiretain_new_arm.py','scripts/sayyed/multiretain_independent.py']),('b70594de8ed4ca0917c6ada866b16f0e34c8b0a3',['scripts/sayyed/prepare_incremental_retain_evidence.py','docs/experiments/ashay/incremental-retain-eval-v1/RESTORE_DEPENDENCIES.json'])]:
  for name in files:
   rawsrc=subprocess.check_output(['git','show',rev+':'+name],cwd='/workspace/wt-pod-a');h=hashlib.sha256(rawsrc).hexdigest();target=bundle/'pinned-source'/rev/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(rawsrc);pinned.append({'commit':rev,'path':name,'sha256':h,'archived_hash_matches':[str(p) for p in file_by_hash.get(h,[])],'bundle_path':str(target)})
 hazard=[]
 for p in [old/'source/scripts/sayyed/extract_multiretain_fixed.py',new/'source/scripts/sayyed/fit_multiretain_new_arm.py',old/'run_fixed_smokes.py',new/'run_new_smokes.py',old/'source/scripts/sayyed/multiretain_support.py',old/'source/scripts/sayyed/check_benign_checkpoint_pair.py']:
  text=p.read_text();ast.parse(text);hazard.append({'source':c.ref(p),'hardcoded_paths':[line.strip() for line in text.splitlines() if '/workspace/' in line][:12],'effects':[word for word in ['.fit(','.cuda(','torch.cuda','subprocess.run','SessionBudget','BUDGET_PATH','torch.distributed.checkpoint','from_pretrained','hf_hub_download','gdown'] if word in text],'A04_action':'Do not execute unchanged. Supply owned path/ledger/env arguments and strict loader; separate guarded entry points; no automatic downstream stages.'})
 locks=[]
 for rootkey in ['base_R1','R3','controls']:
  for p in c.roots[rootkey].glob('*lock*.txt'):locks.append(c.ref(p))
 # A02 small descriptors are reused by exact bytes, no provider discovery repeated.
 registry=jread(c.c/'accepted-a02/CHECKPOINT_REGISTRY.json');selected=registry['selected_by_stage'];candidates={x['candidate_id']:x for x in registry['candidates']};candidate_inputs=[]
 for stage in ['base','R1','R3','R4','R5','R6']:
  v=candidates[selected[stage]];candidate_inputs.append({'stage':stage,'candidate_id':v['candidate_id'],'iteration':v['iteration'],'config':v.get('config'),'tokenizer':v.get('tokenizer'),'index':v.get('index'),'metadata_json':v.get('metadata_json'),'shards':v.get('shards',v.get('weights')),'note':'A02 metadata selection preserved; live payload hashing/strict loading/bridge pending A04; R4=3300,R5=2000,R6=2000 are nominal steps, not matched budgets'})
 report={'status':'READY_FOR_TRAINING_ONLY_A04_APPROVAL','smoke_manifest':{'path':str(smoke_path),'sha256':SMOKE_SHA,'rows':12,'training_only':True,'recovery':'Exact byte reconstruction from archived smoke ordered IDs + hash-verified frozen parent rows, sorted-key JSONL with terminal newline; published historical SHA256 matched exactly. Missing original root-level JSONL was not treated as restored archive member.','parent_manifests':HASHES,'selection_from_heldout_outcomes':False},'anchor_families':smokes,'anchor_availability':anchors,'historical_smoke_comparisons':comps,'feature_identity_dependency_checks':feature_provenance,'fit_execution_source_checks':source_matches,'source_and_environment_recipes':sources,'pinned_repository_sources':pinned,'environment_lock_files':locks,'historical_runtime':fs[0]['runtime'],'actual_A03_cpu_environment':jread(c.c/'CPU_ENVIRONMENT.json'),'runtime_installed_now':False,'weights_downloaded_now':False,'tokenizer_rule':'Base256 and interventions512 are preserved separately; historical DNA ordinal behavior evidence is inherited. A04 verifies live same-model DNA behavior, output-head512 and LM-mask qualification. Do not force equal tokenizer hashes.','representation_semantics':'decoder.layers.16 is zero-indexed module16 (display Block17), plus decoder.final_norm anchor; all26 retained','native_batch_history':'Variable physical batch path failed old numerical gate; fixed physical8 including fillers passed. Preserve failure evidence and fixed8 policy.','legacy_entry_point_hazards':hazard,'owned_adapter':'a03_common.Context.resolve performs explicit longest-prefix read-only translation; GPU path/ledger adaptation remains an A04 patch requirement','candidate_loading_inputs':candidate_inputs,'candidate_registry_reference':{'path':str(c.c/'accepted-a02/CHECKPOINT_REGISTRY.json'),'sha256':sha(c.c/'accepted-a02/CHECKPOINT_REGISTRY.json')},'required_new_stage_refits_conditional':{'R4_R5_R6':1404,'H3':234,'other_five':1170,'R2_additional_if_identified_and_qualified':468},'adjacent_metadata_endpoints':['R4-R3','R5-R4','R6-R5'],'five_planned_adjacent_records_preserved':True,'R3_R1':'Nonadjacent historical comparison','space':'Shared FUSE free-space is not provider quota; A04 must establish actual allocation and staged conversion/scratch coexistence before46.55GB new-weight staging.','remaining_qualification':['Exact current weight payload SHA256 and native index/shard completeness','Same-model native BioNeMo/bridge strict load and all26 activation/LM training-only checks','New runtime/package/source/loader/pooling/precision identity','Actual provider disk/RAM/GPU resources and bounded staging plan','Historical LM-head qualification versus newly loaded output-head qualification are separate','R2 unidentified; no imputation, no causal parent/objective/exposure budget claims'],'future_stage_started':False,'automatic_advance':False}
 c.done('RUNTIME_RECONSTRUCTION_INPUTS',report);put(c.c/'A04_BUNDLE_MANIFEST.json',{'files':[{'path':str(p.relative_to(bundle)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(bundle.rglob('*')) if p.is_file()],'training_only':True,'large_inherited_arrays_repacked':False});c.log('RUNTIME_BUNDLE_PASS',rows=12,models=3,variants=9,representations=26,comparisons=len(comps))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);a=p.parse_args()
 with threadpool_limits(limits=1):main(Context(a.control))
