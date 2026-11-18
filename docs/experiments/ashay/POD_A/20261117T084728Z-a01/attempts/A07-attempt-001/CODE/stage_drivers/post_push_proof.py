"""Public proof of a completed scientific delivery; does not claim its own commit."""
from common import *
from research_guard import guard
def main():
 guard();commit=git('rev-parse','HEAD');assert git('ls-remote','--heads','origin','POD_A').split()[0]==commit;checks=[]
 for line in (D/'OUTPUT_SHA256SUMS').read_text().splitlines():
  h,p=line.split('  ',1);q=D/p;assert sha(q)==h;raw=subprocess.check_output(['git','-C',str(W),'show',commit+':'+str(q.relative_to(W))]);assert hashlib.sha256(raw).hexdigest()==h;checks.append({'path':p,'sha256':h,'committed_blob_bytes':len(raw)})
 source_files=[]
 for e in read(C/'CPU_SOURCE_IDENTITY.json')['files']:
  q=D/'CODE/code'/e['path'];raw=subprocess.check_output(['git','-C',str(W),'show',commit+':'+str(q.relative_to(W))]);assert hashlib.sha256(raw).hexdigest()==e['sha256'];source_files.append({'path':str(q.relative_to(D)),'sha256':e['sha256']})
 proof={'schema':'pod-a-a07-post-push-proof-v1','status':'PASS','scientific_delivery_commit':commit,'remote_equal_at_verification':True,'research_branch':'POD_A','verified_utc':now(),'source_research_handoff':cfg['research_head_before'],'approved_prompt_commit':cfg['prompt_commit'],'source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'coverage_plan_sha256':cfg['coverage_plan_sha256'],'public_manifest_at_scientific_delivery_sha256':sha(D/'OUTPUT_SHA256SUMS'),'all_listed_committed_raw_blobs_verified':checks,'frozen_source_files_bound_to_committed_blobs':source_files,'next_state':'WAITING_FOR_APPROVAL: A08','A08_started':False,'self_reference_policy':'This proof is delivered by a later metadata-only commit; it names the completed scientific delivery above, not its own future commit.'};publish('POST_PUSH_DELIVERY_PROOF.json',proof);put(C/'POST_PUSH_DELIVERY_PROOF.json',proof)
 publish('SOURCE_BINDING.json',{'scientific_code_delivery_commit':commit,'frozen_CPU_source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'source_primitives_unchanged':True,'outputs_bind':'Exact source bytes identified before every producer fit and stored in each immutable unit identity; code was first executed in owned uncommitted stage paths and subsequently delivered with identical hashes','no_extra_fits_or_scientific_value_changes':True})
 print(json.dumps({'status':'PASS','scientific_delivery_commit':commit,'committed_files_checked':len(checks)}))
if __name__=='__main__':main()
