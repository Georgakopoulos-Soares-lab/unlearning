"""Verify exact pushed scientific bytes; publish subsequent metadata without self hashes."""
from common import *
from research_guard import guard
import shutil

def verify():
 guard();commit=git('rev-parse','HEAD');assert git('ls-remote','--heads','origin','POD_A').split()[0]==commit;seal=read(C/'PUBLICATION_SEAL.json');assert sha(D/'OUTPUT_SHA256SUMS')==seal['output_manifest_sha256']
 for e in seal['files']:
  p=D/e['path'];assert sha(p)==e['sha256']
  data=subprocess.check_output(['git','-C',str(W),'show',commit+':'+str(p.relative_to(W))]);assert hashlib.sha256(data).hexdigest()==e['sha256']
 data=subprocess.check_output(['git','-C',str(W),'show',commit+':'+str((D/'OUTPUT_SHA256SUMS').relative_to(W))]);assert hashlib.sha256(data).hexdigest()==seal['output_manifest_sha256']
 changed=git('diff','--name-only',cfg['research_head_before'],commit).splitlines();allowed=guard()['scoped_paths'];assert all(any(p==a or p.startswith(a+'/') for a in allowed) for p in changed)
 proof={'schema':'pod-a-a08-post-push-v1','status':'PASS','research_commit':commit,'remote_commit':commit,'remote_equal':True,'prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'protocol_sha256':cfg['protocol_sha256'],'manifest_sha256':seal['output_manifest_sha256'],'listed_files_verified_against_raw_git_blobs':len(seal['files']),'manifest_blob_verified':True,'guard':guard(),'only_explicit_owned_paths_changed':True,'prompt_worktree_clean':not subprocess.check_output(['git','-C','/workspace/test-prompts-push','status','--porcelain']).strip(),'observed_utc':now(),'A09_started':False};put(C/('POST_PUSH_'+commit+'.json'),proof);return proof

def main():
 proof=verify();put(C/'SCIENTIFIC_POST_PUSH_PROOF.json',proof);publish('SCIENTIFIC_POST_PUSH_PROOF.json',proof)
 receipt=read(C/'A08_RECEIPT.json');receipt.update(status='COMPLETE',scientific_scope='COMPLETE_QUALIFIED_AVAILABLE_ENDPOINTS',delivery_gate='Scientific public payload exact-byte verified; final later metadata commit and separate private metadata recovery receipt bind delivery identities',scientific_publication_commit=proof['research_commit'],scientific_public_manifest_sha256=proof['manifest_sha256'],scientific_public_file_count=proof['listed_files_verified_against_raw_git_blobs'],delivery_proof=ref(C/'SCIENTIFIC_POST_PUSH_PROOF.json'),completed_utc=now());put(C/'A08_RECEIPT.json',receipt);publish('A08_RECEIPT.json',receipt)
 handoff=(C/'SESSION_HANDOFF.md').read_text().replace('**Qualified scientific scope complete; final delivery being sealed. Full project PARTIAL; A04 PARTIAL.**','**A08 COMPLETE for its approved qualified scope. Full project PARTIAL; A04 PARTIAL.**').replace('Exact published commit and post-push recovery revisions are bound by the separate final DELIVERY_RECEIPT.json, avoiding a self-hash cycle.',f"Scientific publication `{proof['research_commit']}` passed raw Git blob checks for all {proof['listed_files_verified_against_raw_git_blobs']} indexed files and its checksum manifest. The later final metadata commit and recovery revisions are bound by the separate final DELIVERY_RECEIPT.json, avoiding a self-hash cycle.")
 put(C/'SESSION_HANDOFF.md',handoff);publish('SESSION_HANDOFF.md',handoff)
 resume=read(C/'RESUME_MANIFEST.json');resume.update(scientific_publication_commit=proof['research_commit'],scientific_public_manifest_sha256=proof['manifest_sha256'],scientific_stage_status='COMPLETE');put(C/'RESUME_MANIFEST.json',resume);publish('RESUME_MANIFEST.json',resume)
 state=read(C/'CONTROLLER_STATE.json');state.update(status='COMPLETE',scientific_job_state='QUIESCENT',owned_job=None,A09_started=False,next_allowed_action='WAITING_FOR_APPROVAL: A09');put(C/'CONTROLLER_STATE.json',state);put(R/'CONTROLLER_STATE.json',state)
 from progress import update
 update('Completed all780independent audits,60sampled refits,5460new classifier/14LMrows,31inspected figures,threefresh scientific restores and exact public delivery. Readout-policy divergence and mixed R6−R4 outcomes are documented in ANALYSIS.md; full project remains PARTIAL','COMPLETE')
 handoff_record={'stage':'A08','status':'COMPLETE','run_id':R.name,'attempt_id':C.name,'scientific_publication_commit':proof['research_commit'],'final_delivery_commit':'Bound by separate immutable final DELIVERY_RECEIPT.json','research_branch':'POD_A','prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'protocol_sha256':cfg['protocol_sha256'],'paths':cfg,'next_state':'WAITING_FOR_APPROVAL: A09','A09_started':False,'full_project_status':'PARTIAL','original_start_utc':None,'deadline_utc':None};put(C/'REMOTE_HANDOFF.json',handoff_record);publish('REMOTE_HANDOFF.json',handoff_record)
 # Root files are current pointers only; all previous bytes are preserved in PRIOR_CURRENT_*.
 for n in ['SESSION_HANDOFF.md','RESUME_MANIFEST.json','REMOTE_HANDOFF.json']:shutil.copyfile(C/n,R/n)
 # Receipt references the updated resume manifest, which has no receipt cycle.
 receipt['resume_manifest_sha256']=sha(C/'RESUME_MANIFEST.json');put(C/'A08_RECEIPT.json',receipt);publish('A08_RECEIPT.json',receipt)
 # Include final helper bytes in the reviewable public source supplement.
 for p in sorted((A/'stage_drivers').glob('*.py')):
  if p.name!='control_views.py':publish('CODE/stage_drivers/'+p.name,p.read_bytes())
 supplement=read(D/'SOURCE_SUPPLEMENT.json');supplement['report_plot_recovery_source']=[{'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((D/'CODE').rglob('*')) if p.is_file()];publish('SOURCE_SUPPLEMENT.json',supplement)
 print(json.dumps({'status':'SCIENTIFIC_DELIVERY_PASS_FINAL_METADATA_READY','scientific_commit':proof['research_commit'],'listed_files_verified':proof['listed_files_verified_against_raw_git_blobs']}))
if __name__=='__main__':main()
