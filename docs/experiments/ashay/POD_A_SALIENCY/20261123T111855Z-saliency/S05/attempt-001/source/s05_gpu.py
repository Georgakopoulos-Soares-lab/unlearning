"""Finite source-bound S05 H3 extraction, one candidate; calibration retained as production chunk0."""
from pathlib import Path
import os,sys,json,time,resource,signal,dataclasses,subprocess,hashlib,argparse
from s05_contract import *
def main(c,alias):
 cfg,v,source=readiness(c,alias,role='GPU');need(str(Path(sys.executable).absolute())==cfg['runtime_python'],'Wrong qualified runtime');need(os.environ.get('HF_HUB_OFFLINE')=='1','GPUworker must be offline');lookup=planned(c);case=Path(cfg['artifacts_root'])/'candidates'/alias;case.mkdir(parents=True,exist_ok=True);checkpoint=Path(v['checkpoint_root']);native=load(Path(c)/'NATIVE_INPUT_BINDINGS.json')[alias]
 for f in native:
  need(file_stat(f['path'])==f['verified_stat'],'Native input/stat binding changed; affected revalidation required')
 old_finished=all((case/'features'/split/'COMPLETE.json').exists() for split in ['train','dev'])
 if old_finished:
  for split in ['train','dev']:
   eid=spec_id(lookup,'extraction',c=alias,t='emp_H3',split=split);verify_seal(case/'features'/split,{'planned_spec_id':eid,'source_identity_sha256':source,'candidate_content':v['model_tensor_content_sha256'],'cohort_sha256':cfg['cohorts'][split]['ordered_metadata_sha256']},required=['INDEX.json'])
  print('REUSED_TWO_COMPLETE_H3_FEATURE_BUNDLES',alias,flush=True);return
 def stop(*_):raise RuntimeError('Owned finite S05worker interrupted; preserve partials and completed chunks')
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 with exclusive(Path(cfg['root_control'])/'GPU_EXECUTION.lock'),exclusive(case/'GPU_WRITER.lock'):
  process=process_identity();job={**process,'alias':alias,'status':'RUNNING','phase':'S05','source_identity_sha256':source,'started_utc':now()};put(Path(c)/'ACTIVE_GPU_JOB.json',job);ledgerpath=Path(c)/'GPU_ACCOUNTING.json';ledger=load(ledgerpath);need(ledger['active_job'] is None,'Recorded GPUjob requires live reconciliation');ledger['active_job']=job;put(ledgerpath,ledger);began=time.monotonic();cpu_begin=time.process_time();status='FAILED';dist=None;torch=None;model_begin=None;processed=0;physical=0;fillers=0;forward_seconds=0.;write_seconds=0.;new_chunks=0;reused_chunks=0
  try:
   # No framework, model, dataset or forward is opened before strict scope/source/readiness checks above.
   import numpy as np
   import torch
   import torch.distributed as dist
   import yaml
   from tokenizers import Tokenizer
   from native_loader import inventory_and_load
   from qualification_contract import pack,validate_batch,pool,production_loss,check_hook_registry,validate_state,validate_actual_loading,check_loaded_values,validate_tied_weight_contract
   from megatron.core import parallel_state,tensor_parallel
   from megatron.core.transformer.enums import AttnBackend
   from bionemo.evo2.models.evo2_provider import Hyena1bModelProvider
   torch.set_num_threads(4);torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=True;torch.backends.cudnn.benchmark=False;torch.use_deterministic_algorithms(False);torch.set_float32_matmul_precision('highest');supplied=yaml.safe_load((checkpoint/'run_config.yaml').read_text())['model'];need(supplied['num_layers']==25 and supplied['hidden_size']==1920,'Unsupported qualified architecture');tokenizer=Tokenizer.from_file(str(checkpoint/'tokenizer.json'))
   for seq in ['A','C','G','T','N','ACGTN']:need(tokenizer.encode(seq).ids==[ord(ch) for ch in seq],'Qualified ordinal DNA tokenizer changed')
   allowed={f.name for f in dataclasses.fields(Hyena1bModelProvider) if f.init};kwargs={k:x for k,x in supplied.items() if k in allowed and (isinstance(x,(str,int,float,bool)) or x is None)};kwargs.update({'attention_backend':AttnBackend.unfused,'vocab_size':512,'params_dtype':torch.bfloat16,'pipeline_dtype':torch.bfloat16,'bf16':True,'use_cpu_initialization':True,'perform_initialization':False,'recompute_granularity':None,'recompute_method':None,'recompute_num_layers':None,'seq_length':1000})
   foreign=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=15).strip();need(not [l for l in foreign.splitlines() if l.strip().isdigit() and int(l.strip())!=os.getpid()],'Foreign GPUcompute exists, do not interfere');model_begin=time.monotonic();torch.cuda.set_device(0);torch.cuda.reset_peak_memory_stats();init=case/('distributed_init_'+str(os.getpid()));dist.init_process_group('nccl',init_method='file://'+str(init.resolve()),rank=0,world_size=1);parallel_state.initialize_model_parallel(tensor_model_parallel_size=1,pipeline_model_parallel_size=1);tensor_parallel.model_parallel_cuda_manual_seed(42);provider=Hyena1bModelProvider(**kwargs);provider.finalize();model=provider.provide();load_start=time.monotonic();state,nreport=inventory_and_load(checkpoint,{Path(f['path']).name:f['bytes'] for f in native if f['path'].endswith('.distcp')},model);need(nreport['model_tensor_content_sha256']==v['model_tensor_content_sha256'],'Wrong actual reconstructed candidatecontent');model=model.to(device='cuda');report=validate_state(model,state);missing,unexpected=model.load_state_dict(state,strict=False);report.update(validate_actual_loading(missing,unexpected,report));report.update(status='PASS',native=nreport,all_loaded_tensor_values_exactly_checked=check_loaded_values(model,state),tied_weight_contract=validate_tied_weight_contract(model,state));put(case/'LOADING.json',report);del state;load_seconds=time.monotonic()-load_start;model.eval();model.requires_grad_(False);need(not model.training and not any(p.requires_grad for p in model.parameters()),'Backbone not frozen')
   specs=[(f'decoder_layer_{i}',f'decoder.layers.{i}',m) for i,m in enumerate(model.decoder.layers)]+[('final_norm','decoder.final_norm',model.decoder.final_norm)];check_hook_registry([n for k,n,m in specs],model.config.hidden_size);captured={};fires={};lengths=None
   def hook(key):
    def capture(module,inputs,output):fires[key]=fires.get(key,0)+1;need(fires[key]==1,'Repeated hook');captured[key]=pool(output,lengths,1920)
    return capture
   handles=[m.register_forward_hook(hook(k)) for k,n,m in specs]
   for split in ['train','dev']:
    expected=metadata(cfg,split);splitroot=case/'features'/split;splitroot.mkdir(parents=True,exist_ok=True);eid=spec_id(lookup,'extraction',c=alias,t='emp_H3',split=split);index={'schema_version':'s05-feature-bundle-index-v1','planned_spec_id':eid,'candidate_id':v['candidate_id'],'content_sha256':v['model_tensor_content_sha256'],'task':'emp_H3','split':split,'source_identity_sha256':source,'runtime_lock_sha256':cfg['runtime_lock_sha256'],'cohort_sha256':cfg['cohorts'][split]['ordered_metadata_sha256'],'chunks':[],'rows':len(expected),'hooks':HOOKS}
    for ordinal,(first,stoprow) in enumerate(chunks_for(len(expected))):
     root=splitroot/('chunk-'+str(ordinal).zfill(4));identity=chunk_identity(cfg,v,source,split,first,stoprow,eid);rel=str(root.relative_to(case))
     if (root/'COMPLETE.json').exists():
      verify_seal(root,identity,required=['features_and_lm.npz','RESOURCE.json']);index['chunks'].append({'first':first,'stop':stoprow,'relative_root':rel,'seal_sha256':sha(root/'COMPLETE.json')});reused_chunks+=1;put(splitroot/'INDEX.partial.json',index);print('REUSED_VALID_H3_CHUNK',alias,split,ordinal,flush=True);continue
     need(not root.exists(),'Incomplete prior chunk preserved: diagnose and use explicit newattempt mapping, never overwrite');root.mkdir();rows=sequences(cfg,alias,split,first,stoprow)
     for row in rows:need(tokenizer.encode(row['sequence']).ids==[ord(ch) for ch in row['sequence']],'Actual sequence tokenization mismatch')
     parts={k:[] for k in KEYS};sums_parts=[];count_parts=[];batches=[];chunk_start=time.monotonic()
     for offset in range(0,len(rows),8):
      rr=rows[offset:offset+8];tokens,lengths,positions=pack([r['sequence'] for r in rr],device='cuda');validate_batch(tokens,lengths,positions,[r['sequence'] for r in rr]);captured.clear();fires.clear();torch.cuda.synchronize();t=time.monotonic()
      with torch.inference_mode():
       logits=model(input_ids=tokens,position_ids=positions,attention_mask=None);need(set(captured)==set(KEYS) and all(fires.get(k)==1 for k in KEYS),'Missing/repeated qualified hooks');sums,ntokens,_,_=production_loss(logits,tokens,lengths,positions)
       for key in KEYS:parts[key].append(captured[key][:len(rr)].cpu().numpy())
       sums_parts.append(sums[:len(rr)].cpu().numpy());count_parts.append(ntokens[:len(rr)].cpu().numpy())
      torch.cuda.synchronize();elapsed=time.monotonic()-t;batches.append({'first_row':first+offset,'logical_rows':len(rr),'physical_rows':8,'fillers':8-len(rr),'synchronized_forward_capture_seconds':elapsed});forward_seconds+=elapsed;processed+=len(rr);physical+=8;fillers+=8-len(rr)
     arrays={k:np.concatenate(x) for k,x in parts.items()};arrays.update(ids=np.array([r['id'] for r in rows]),labels=np.array([r['label'] for r in rows]),groups=np.array([r['exact_rc_group'] for r in rows]),task=np.array(['emp_H3']*len(rows)),split=np.array([split]*len(rows)),sequence_sha256=np.array([r['sequence_sha256'] for r in rows]),lengths=np.array([len(r['sequence']) for r in rows]),nll_sum=np.concatenate(sums_parts),n_tokens=np.concatenate(count_parts));check_arrays(arrays,expected[first:stoprow],split);need(torch.cuda.max_memory_allocated()<=16*1024**3 and torch.cuda.max_memory_reserved()<=16*1024**3,'Frozen GPU16GiB memory ceiling exceeded');rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;need(rss<=32*1024**3,'Frozen GPUworker hostRSS32GiB exceeded');t=time.monotonic();tmp=root/'features_and_lm.npz.partial'
     with tmp.open('xb') as f:np.savez(f,**arrays);f.flush();os.fsync(f.fileno())
     with np.load(tmp,allow_pickle=False) as roundtrip:
      need(set(roundtrip.files)==set(arrays),'Chunk serialization member set changed')
      for name,value in arrays.items():need(np.array_equal(roundtrip[name],value),'Chunk serialization roundtrip changed '+name)
     os.replace(tmp,root/'features_and_lm.npz');io_time=time.monotonic()-t;write_seconds+=io_time;measurement={'status':'CHUNK_VALIDATED','logical_rows':len(rows),'physical_batches':len(batches),'physical_rows':len(batches)*8,'fillers':sum(b['fillers'] for b in batches),'first':first,'stop':stoprow,'forward_capture_seconds':sum(b['synchronized_forward_capture_seconds'] for b in batches),'NPZ_write_seconds':io_time,'chunk_wall_seconds_before_seal':time.monotonic()-chunk_start,'feature_file_bytes':(root/'features_and_lm.npz').stat().st_size,'peak_GPU_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_GPU_reserved_bytes':torch.cuda.max_memory_reserved(),'peak_host_RSS_bytes':rss,'batch_timings':batches};put(root/'RESOURCE.json',measurement);write_seal(root,identity,['features_and_lm.npz','RESOURCE.json'],{'logical_rows':len(rows),'physical_batches':len(batches),'fillers':measurement['fillers']});index['chunks'].append({'first':first,'stop':stoprow,'relative_root':rel,'seal_sha256':sha(root/'COMPLETE.json')});put(splitroot/'INDEX.partial.json',index);new_chunks+=1
     if alias=='candidate_01' and split=='train' and first==0:
      put(Path(c)/'TRAIN_CALIBRATION.json',{'status':'PASS_REUSED_AS_FIRST_PRODUCTION_CHUNK','alias':alias,'split':'train','planned_spec_id':eid,'source_identity_sha256':source,'chunk_seal_sha256':sha(root/'COMPLETE.json'),'measurement':measurement,'model_only_CPU_load_seconds':load_seconds,'production_specification_identical':True,'repeated_calibration_forwards':0,'forecast_remaining_forward_seconds':measurement['forward_capture_seconds']/256*(13468-256),'forecast_scope':'Firstchunk extrapolation only, excludes modelsetup/IO/CV/audits/recovery; update with laterchunks. Not billing/GPUbusy time.','observed_utc':now()})
     put(Path(c)/'GPU_PROGRESS.json',{'status':'RUNNING','alias':alias,'split':split,'last_completed_chunk':ordinal,'completed_real_rows_this_process':processed,'new_chunks':new_chunks,'reused_chunks':reused_chunks,'owned_process':process,'source_identity_sha256':source,'next_action':'Continue finite missingH3chunks only; no other-task dispatch','updated_utc':now()});print('S05_H3_CHUNK_SEALED',alias,split,ordinal,'rows',stoprow,'of',len(expected),flush=True);del arrays,parts,sums_parts,count_parts
    need(index['chunks'][-1]['stop']==len(expected) and len(index['chunks'])==len(chunks_for(len(expected))),'Incomplete featurebundle');put(splitroot/'INDEX.json',index);write_seal(splitroot,{'planned_spec_id':eid,'source_identity_sha256':source,'candidate_content':v['model_tensor_content_sha256'],'cohort_sha256':index['cohort_sha256']},['INDEX.json'],{'logical_rows':len(expected),'chunks':len(index['chunks'])})
   for handle in handles:handle.remove()
   totals={'alias':alias,'status':'TWO_H3_BUNDLES_PRODUCER_COMPLETE','new_chunks':new_chunks,'reused_chunks':reused_chunks,'new_logical_rows':processed,'new_physical_rows':physical,'new_fillers':fillers,'synchronized_forward_capture_seconds':forward_seconds,'NPZ_write_seconds':write_seconds,'wall_seconds':time.monotonic()-began,'cpu_process_seconds':time.process_time()-cpu_begin,'model_only_CPU_load_seconds':load_seconds,'peak_GPU_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_GPU_reserved_bytes':torch.cuda.max_memory_reserved(),'peak_host_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'fit_calls':0,'other_task_or_test_forwards':0};put(case/'EXTRACTION_RESOURCE.json',totals);status='PASS'
  except BaseException as exc:put(case/'GPU_FAILED_'+str(os.getpid())+'.json',{'status':'FAILED','type':type(exc).__name__,'reason':str(exc),'owned_process':process,'source_identity_sha256':source,'completed_new_rows':processed,'preserve_all_chunks':True});raise
  finally:
   if dist is not None and dist.is_initialized():dist.destroy_process_group()
   ledger=load(ledgerpath);ledger['events'].append({'alias':alias,'phase':'S05','status':status,'source_identity_sha256':source,'wall_seconds':time.monotonic()-began,'model_stage_wall_seconds':None if model_begin is None else time.monotonic()-model_begin,'new_logical_rows':processed,'physical_rows':physical,'fillers':fillers,'ended_utc':now()});ledger['active_job']=None;put(ledgerpath,ledger);put(Path(c)/'ACTIVE_GPU_JOB.json',{**job,'status':'EXITING_'+status,'ended_utc':now()})
 print('S05_CANDIDATE_H3_EXTRACTION_DRAINED',alias,status,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--control',required=True);p.add_argument('--alias',required=True);x=p.parse_args();main(Path(x.control),x.alias)
