"""Finite R3/R5 immutable acquisition; verify originals and retain eight-file layouts."""
from common4 import *
from asset_contract4 import safe_relative,immutable_revision,verify_file,runtime_relative
from huggingface_hub import HfApi,hf_hub_download
import shutil,time
def link_or_copy(source,target):
 assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
 try:os.link(source,target);return 'HARDLINK_SAME_BYTES_NO_EXTRA_ALLOCATION'
 except OSError:shutil.copyfile(source,target);return 'COPIED_EXACT_BYTES'
def main():
 assert read(C/'A04_INPUT_VERIFICATION.json')['status']=='PASS';api=HfApi();assert api.repo_info(MIRROR_REPO,repo_type='dataset').private;job={'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'status':'RUNNING','scope':'Only exact R3/R5 manifest assets','started_utc':now()};put(C/'TRANSFER_JOB.json',job);records=[];diagnostics=[];items=[];small=[];t0=time.monotonic();cpu0=time.process_time()
 for e in read(C/'MIRROR_ASSETS.json')['files']:
  alias=e['alias'];native=safe_relative(e['relative_path']);immutable_revision(e['mirror_revision']);native_target=A/'native-deliveries'/alias/str(native);view=A/'checkpoints'/alias/runtime_relative(str(native));start=time.monotonic();hstart=time.process_time();status='PENDING';source=None;fresh=False
  try:
   old=Path(e['old_local_path']) if e['old_local_path'] else None
   candidates=[old] if old and old.exists() and old.stat().st_size==e['bytes'] else []
   # Check only the exact accepted mirror path at its pinned revision in the standard local cache.
   global_snapshot=Path('/root/.cache/huggingface/hub')/('datasets--'+MIRROR_REPO.replace('/','--'))/'snapshots'/e['mirror_revision']/e['mirror_path']
   if global_snapshot.exists():candidates.append(global_snapshot.resolve())
   if candidates:
    source=candidates[0];actual=verify_file(source,e['bytes'],e['sha256'],e['md5']);status='VERIFIED_REUSED_LOCAL';route='matching accepted local asset'
   else:
    print(json.dumps({'event':'EXACT_MIRROR_DOWNLOAD_START','alias':alias,'relative_path':str(native),'bytes':e['bytes'],'revision':e['mirror_revision']}),flush=True)
    # SDK cache can resume only this immutable object's partial transfer; no byte stitching or mutable ref.
    source=Path(hf_hub_download(MIRROR_REPO,e['mirror_path'],repo_type='dataset',revision=e['mirror_revision'],cache_dir=str(A/'mirror-payload-cache'))).resolve();fresh=True;actual=verify_file(source,e['bytes'],e['sha256'],e['md5']);status='VERIFIED';route='pinned private HF mirror'
   layout_mode=link_or_copy(source,native_target);view_mode=link_or_copy(native_target,view);assert native_target.stat().st_size==view.stat().st_size==e['bytes'];entry={**e,'status':status,'target':str(view),'native_target':str(native_target),'source_local_path':str(source),'fresh_download':fresh,'route':route,'actual_md5':actual['md5'],'layout_materialization':layout_mode,'runtime_view_materialization':view_mode,'elapsed_wall_seconds':time.monotonic()-start,'hash_and_transfer_process_CPU_seconds':time.process_time()-hstart,'completed_utc':now()};records.append(entry);print(json.dumps({'event':'ASSET_VERIFIED','alias':alias,'path':str(native),'status':status,'fresh_download':fresh,'bytes':e['bytes'],'seconds':entry['elapsed_wall_seconds']}),flush=True)
   base={'alias':alias,'candidate_id':read(C/'ACCEPTED_CHECKPOINT_REGISTRY.json')['selected_by_stage'][alias],'file_id':e['file_id'],'name':view.name,'sha256':e['sha256']}
   if view.name in ['__0_0.distcp','train_state.pt','common.pt']:items.append({**base,'target':str(view),'expected_bytes':e['bytes'],'expected_historical_sha256':e['historical_native_digest'],'optional_for_model_only_native_loading':view.name!='__0_0.distcp'})
   else:small.append({**base,'path':str(view),'bytes':e['bytes'],'status':'REUSED_VERIFIED_SMALL_ASSET'})
  except Exception as exc:
   diagnostics.append({'alias':alias,'path':str(native),'exception_type':type(exc).__name__,'status':'BLOCKED_OR_FAILED_ASSET','full_error_log_private':True,'fresh_transfer_started':fresh,'no_unpinned_fallback':True});print(json.dumps({'event':'ASSET_FAILED','alias':alias,'path':str(native),'exception_type':type(exc).__name__}),flush=True)
  put(C/'DOWNLOAD_RECEIPTS.json',{'schema':'pod-a-a04-exact-mirror-download-v1','records':records,'diagnostics':diagnostics,'complete_assets':len(records),'expected_assets':16,'source_repository':MIRROR_REPO});put(C/'ASSET_TRANSFER_MANIFEST.json',{'schema':'pod-a-a04-asset-transfer-v1','items':items,'small_assets':small,'R2':'EXCLUDED_NO_DISCOVERY'})
 outcomes=[]
 for alias in ['R3','R5']:
  rr=[r for r in records if r['alias']==alias];success=len(rr)==8;outcomes.append({'alias':alias,'payload_integrity_status':'PASS' if success else 'BLOCKED','verified_files':len(rr),'expected_files':8,'native_layout':str(A/'native-deliveries'/alias),'runtime_view':str(A/'checkpoints'/alias),'normalization':'Only tokenizer files have a flattened hardlinked runtime view; native eight-file layout is retained byte-for-byte','native_digest_origin':'historical equality' if alias=='R3' else 'fresh mirror/provider-bound digest; not historical'})
 put(C/'CHECKPOINT_HASHES.json',{'status':'PASS' if len(records)==16 else 'PARTIAL','records':[{k:r[k] for k in ['alias','relative_path','file_id','bytes','sha256','actual_md5','mirror_revision','mirror_path','native_target','target','fresh_download','digest_origin']} for r in records]});put(C/'PAYLOAD_RECOVERY_INDEX.json',{'status':'PASS' if len(records)==16 else 'PARTIAL','repository':MIRROR_REPO,'scope':'Full local original-byte verification of immutable mirror assets; durable mirrors referenced without redundant large archives','targets':outcomes,'all_assets':records,'fresh_transferred_logical_bytes':sum(r['bytes'] for r in records if r['fresh_download']),'reused_logical_bytes':sum(r['bytes'] for r in records if not r['fresh_download']),'wire_bytes':None,'wire_bytes_reason':'SDK/Xet object sizes measured; wire dedup counters not captured','no_duplicate_weight_archive':True,'private_at_closeout':api.repo_info(MIRROR_REPO,repo_type='dataset').private})
 put(C/'TRANSFER_DIAGNOSTICS.json',{'status':'PASS' if not diagnostics else 'PARTIAL','new_diagnostics':diagnostics,'historical_Drive_failures':'Preserved in A04-attempt-003; no Colab/Drive retry this attempt','wall_seconds':time.monotonic()-t0,'CPU_seconds':time.process_time()-cpu0});job.update(status='COMPLETED_AWAITING_PROCESS_EXIT',completed_utc=now(),verified_assets=len(records));put(C/'TRANSFER_JOB.json',job);print(json.dumps({'status':'PASS' if len(records)==16 else 'PARTIAL','verified_assets':len(records),'new_logical_bytes':sum(r['bytes'] for r in records if r['fresh_download']),'reused_logical_bytes':sum(r['bytes'] for r in records if not r['fresh_download']),'targets':outcomes}),flush=True)
if __name__=='__main__':main()
