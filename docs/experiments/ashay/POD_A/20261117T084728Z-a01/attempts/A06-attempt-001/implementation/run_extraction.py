"""One finite approved candidate/task group. No remote writes, fits or future-stage dispatch."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,subprocess,sys,time,signal,resource,re
import numpy as np
from production_contract import *
from qualification_contract import componentwise,independent_cross_entropy,validate_manifest
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def preflight(args):
 c=Path(args.control).resolve();require(c==Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-001'),'Unapproved control root');require(re.fullmatch(r'[A-Za-z0-9_-]+',args.run_label) is not None,'Unsafe run label');cfg=read(c/'RUN_CONFIG.json');a=Path(cfg['artifacts']);require(cfg['stage']=='A06' and cfg['prompt_commit']==args.prompt_commit,'Wrong stage/pin');approval=read(c/'APPROVAL_RECORD.json');require(approval['stage']=='A06' and approval['prompt_commit']==args.prompt_commit,'No matching direct approval receipt');require(cfg['coverage_plan_sha256']==args.coverage_sha256==approval['coverage_plan_sha256'],'Coverage hash differs');inp=read(c/'A06_INPUTS.json');require(args.candidate in ['R4','R6'],'Unknown checkpoint');require(Path(args.output_root).resolve()==(a/('parity' if args.mode=='parity' else 'features')).resolve(),'Wrong output root');require(args.group in ['H3','other_five'],'Unknown group')
 sys.path.insert(0,str(a/'stage_drivers'));from research_guard import guard;guard(allow_dirty=True)
 source=read(c/'SOURCE_IDENTITY.json')
 for e in source['inference_files']:require(sha(a/'code'/e['path'])==e['sha256'],'Adapter source changed before inference')
 require(read(c/'SYNTHETIC_VALIDATION.json')['status']=='PASS','Synthetic adapter validation absent')
 if args.mode=='extraction':
  parity=read(c/('ADAPTER_PARITY_'+args.candidate+'.json'));require(parity['status']=='PASS' and parity['source_identity_sha256']==sha(c/'SOURCE_IDENTITY.json'),'Unqualified adapter source/candidate')
 units=[u for u in inp['extraction_units'] if u['candidate']==args.candidate and (u['task']=='emp_H3')==(args.group=='H3')]
 for u in units:
  require_gate(args.candidate,u['task'],c)
  p=Path(u['manifest']['path']);require(sha(p)==u['manifest']['sha256'],'Cohort byte identity changed');require(sha(u['parent_manifest']['path'])==u['parent_manifest']['sha256'],'Parent cohort changed')
  rr=validate_rows([json.loads(l) for l in p.read_text().splitlines()],u['task'],u['split']);require(digest([r['id'] for r in rr])==u['ordered_ids_sha256'],'Row order changed')
 if args.mode=='parity':require(args.group=='H3','Parity is frozen TRAIN-only fixture')
 assets=inp['assets'][args.candidate];cache=read(c/'ASSET_STAT_CACHE.json')
 for e in assets:
  p=Path(e['path']);s=p.stat();st=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns];require(s.st_size==e['bytes'],'Native asset size changed')
  if cache.get(str(p))!={'sha256':e['sha256'],'stat':st}:require(sha(p)==e['sha256'],'Native bytes changed')
 # Binding fold/reference hashes is checked without executing heads or touching held-out arrays.
 for e in inp['H3_reference_dependencies']:require(sha(e['path'])==e['sha256'],'Fold/reference head input changed')
 return c,cfg,inp,units
def arrays(rows,features,nll,counts):
 return dict(ids=np.array([r['id'] for r in rows]),task=np.array([r['task'] for r in rows]),split=np.array([r['split'] for r in rows]),labels=np.array([r['label'] for r in rows]),groups=np.array([r['exact_rc_group'] for r in rows]),sequence_sha256=np.array([hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows]),lengths=np.array([len(r['sequence']) for r in rows]),nll_sum=nll,n_tokens=counts,**features)
def main(args):
 c,cfg,inp,units=preflight(args);a=Path(cfg['artifacts']);mode=args.mode;candidate=args.candidate;out=owned(Path(args.output_root)/candidate/(args.run_label if mode=='parity' else 'jobs/'+args.run_label),a);require(not out.exists(),'Existing invocation preserved; use a new run-label and sealed-unit resume');out.mkdir(parents=True);cpu=time.process_time();start=time.monotonic();source_sha=sha(c/'SOURCE_IDENTITY.json');job={'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'candidate':candidate,'mode':mode,'group':args.group,'run_label':args.run_label,'started_utc':stamp(),'source_identity_sha256':source_sha,'status':'RUNNING','command_sha256':digest(sys.argv)};put(c/'ACTIVE_GPU_JOB.json',job);status='FAILED';physical=0;real=0;rows_new=0;forwards=[]
 def abort(*_):raise InterruptedError('A06 safe owned interruption; no future stage')
 signal.signal(signal.SIGTERM,abort);signal.signal(signal.SIGINT,abort)
 with UnitLock(Path(cfg['root_control'])/'GPU_EXECUTION.lock'):
  foreign=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip();require(not [s for s in foreign.splitlines() if s.strip().isdigit() and int(s.strip())!=os.getpid()],'Foreign GPU owner; no interference')
  try:
   from runtime_model import load_model,forward
   import torch,torch.distributed as dist
   checkpoint=Path(inp['assets'][candidate][0]['path']).parent;model,tokenizer,specs,loading=load_model(checkpoint,inp['assets'][candidate],out,inp['checkpoint_identities'][candidate]['model_tensor_content_sha256'])
   if mode=='parity':
    fixture=Path(inp['training_smoke']['path']);rows=validate_manifest(fixture);parts={k:[] for k in LAYERS};losses=[];counts=[];witnesses={}
    for offset in range(0,len(rows),8):
     rr=rows[offset:offset+8];fe,nll,nt,wit,elapsed=forward(model,specs,rr,tokenizer,witness=True);physical+=1;real+=len(rr);forwards.append(elapsed)
     for key in LAYERS:parts[key].append(fe[key])
     losses.append(nll);counts.append(nt)
     for i,w in enumerate(wit):
      index=offset+i;ind=independent_cross_entropy(w['logits'],w['targets']);require(componentwise(ind,w['losses'])['status']=='PASS','Actual-logit independent CE failed');require(componentwise(np.array([ind.sum(dtype=np.float64)]),np.array([nll[i]]))['status']=='PASS','Actual-logit full-row sum failed');witnesses.update({f'row{index}_logits':w['logits'],f'row{index}_targets':w['targets'],f'row{index}_losses':w['losses']})
    fe={k:np.concatenate(v) for k,v in parts.items()};nll=np.concatenate(losses);nt=np.concatenate(counts);payload=arrays(rows,fe,nll,nt);check_real_population(payload['ids'],[r['id'] for r in rows],fe,nll,nt,payload['lengths']);np.savez_compressed(out/'features_and_lm.npz',**payload);np.savez_compressed(out/'TRAIN_logits_witness.npz',**witnesses);put(out/'COMPLETE.json',{'status':'PASS','candidate':candidate,'source_identity_sha256':source_sha,'mode':'TRAIN_ONLY_ADAPTER_PARITY','rows':12,'manifest_sha256':sha(fixture),'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in out.glob('*.npz')],'physical_forwards':physical,'real_rows':real,'fillers':physical*8-real,'completed_utc':stamp()})
   else:
    for u in units:
     rows=validate_rows([json.loads(l) for l in Path(u['manifest']['path']).read_text().splitlines()],u['task'],u['split']);root=owned(a/'features'/candidate/u['task']/u['split'],a/'features');root.mkdir(parents=True,exist_ok=True);quarantine=a/'quarantine'/candidate/u['task']/u['split'];quarantine_temporaries(root,quarantine);chunks=[];base={'candidate':candidate,'candidate_id':inp['checkpoint_identities'][candidate]['candidate_id'],'model_tensor_content_sha256':inp['checkpoint_identities'][candidate]['model_tensor_content_sha256'],'asset_manifest_sha256':inp['checkpoint_identities'][candidate]['asset_manifest_sha256'],'native_assets':inp['assets'][candidate],'adapter_source_identity_sha256':source_sha,'qualified_source_identity_sha256':inp['qualified_source_identity_sha256'],'environment_sha256':inp['environment_sha256'],'protocol_sha256':cfg['protocol_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'unit':u,'hooks':HOOKS,'width':1920,'physical_batch':8,'dtype':'float32','LM_sum_dtype':'float32','LM_aggregate_dtype':'float64'}
     with UnitLock(root/'writer.lock'):
      for startrow in range(0,len(rows),256):
       rr=rows[startrow:startrow+256];identity={**base,'first_row':startrow,'real_rows':len(rr),'ordered_ids_sha256':digest([r['id'] for r in rr])};chunk=root/f'chunk_{startrow:06d}';state,receipt=prepare_chunk(chunk,identity,rr,quarantine)
       if state=='REUSE':
        require(receipt['identity']==identity,'Sealed chunk identity mismatch');chunks.append({'path':str(chunk.relative_to(a)),'receipt_sha256':sha(chunk/'COMPLETE.json'),'rows':len(rr),'reused':True});continue
       parts={k:[] for k in LAYERS};losses=[];counts=[];ts=time.monotonic();batch_times=[]
       for offset in range(0,len(rr),8):
        batch=rr[offset:offset+8];fe,nll,nt,_,elapsed=forward(model,specs,batch,tokenizer);physical+=1;real+=len(batch);rows_new+=len(batch);batch_times.append(elapsed);forwards.append(elapsed)
        for key in LAYERS:parts[key].append(fe[key])
        losses.append(nll);counts.append(nt)
       fe={k:np.concatenate(v) for k,v in parts.items()};nll=np.concatenate(losses);nt=np.concatenate(counts);payload=arrays(rr,fe,nll,nt);timing={'wall_seconds_forward_capture':time.monotonic()-ts,'batch_seconds':batch_times,'physical_forwards':len(batch_times),'real_rows':len(rr),'fillers':len(batch_times)*8-len(rr)};receipt=seal_chunk(chunk,identity,rr,payload,timing,quarantine);chunks.append({'path':str(chunk.relative_to(a)),'receipt_sha256':sha(chunk/'COMPLETE.json'),'rows':len(rr),'reused':False});put(c/'EXTRACTION_LIVE.json',{'candidate':candidate,'task':u['task'],'split':u['split'],'sealed_rows_this_unit':startrow+len(rr),'total_unit_rows':len(rows),'new_physical_forwards':physical,'new_real_rows_this_job':real,'observed_utc':stamp()});print(json.dumps({'event':'CHUNK_SEALED','candidate':candidate,'task':u['task'],'split':u['split'],'rows':startrow+len(rr),'total':len(rows)}),flush=True)
      bundle={'schema':'pod-a-a06-extraction-bundle-v1','status':'PASS','identity':base,'chunks':chunks,'rows':len(rows),'raw_feature_bytes':len(rows)*26*1920*4,'physical_forwards_expected':(len(rows)+7)//8,'completed_utc':stamp()}
      if (root/'COMPLETE.json').exists():
       prior=read(root/'COMPLETE.json');require(prior['identity']==base and [(e['path'],e['receipt_sha256']) for e in prior['chunks']]==[(e['path'],e['receipt_sha256']) for e in chunks],'Prior sealed bundle changed')
      else:put(root/'COMPLETE.json',bundle)
   status='PASS';put(out/'RESOURCE_MEASUREMENTS.json',{'status':'PASS','candidate':candidate,'mode':mode,'group':args.group,'new_physical_forwards':physical,'new_real_rows':real,'fillers':physical*8-real,'synchronized_batch_seconds':forwards,'loading':loading,'wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cpu,'peak_GPU_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_GPU_reserved_bytes':torch.cuda.max_memory_reserved(),'peak_RSS_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':stamp()})
  except Exception as exc:
   put(out/'FAILED.json',{'status':'FAIL','exception_type':type(exc).__name__,'reason':str(exc),'source_identity_sha256':source_sha,'new_physical_forwards':physical,'new_real_rows':real,'observed_utc':stamp()});raise
  finally:
   if 'dist' in locals() and dist.is_initialized():dist.destroy_process_group()
   job.update(status='EXITING_'+status,completed_utc=stamp(),new_physical_forwards=physical,new_real_rows=real);put(c/'ACTIVE_GPU_JOB.json',job)
   with (c/'RESOURCE_LEDGER.jsonl').open('a') as ledger:ledger.write(json.dumps({**job,'wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cpu,'cost':None,'time_caps':None})+'\n')
 print(json.dumps({'status':status,'candidate':candidate,'mode':mode,'group':args.group,'new_forwards':physical}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);p.add_argument('--prompt-commit',required=True);p.add_argument('--coverage-sha256',required=True);p.add_argument('--candidate',required=True,choices=['R4','R6']);p.add_argument('--mode',required=True,choices=['parity','extraction']);p.add_argument('--group',required=True,choices=['H3','other_five']);p.add_argument('--output-root',required=True);p.add_argument('--run-label',required=True);main(p.parse_args())
