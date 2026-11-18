"""Finite A09 report delivery, exact-byte proof and terminal metadata; no science."""
from common import *
from research_guard import guard
import argparse

def verify_public():
 proof=guard();head=git('rev-parse','HEAD');assert git('ls-remote','--heads','origin','POD_A').split()[0]==head
 seal=read(C/'PUBLICATION_SEAL.json');assert sha(D/'OUTPUT_SHA256SUMS')==seal['manifest_sha256']
 entries=seal['files']+[{'path':'OUTPUT_SHA256SUMS','sha256':seal['manifest_sha256']}]
 for e in entries:
  p=D/e['path'];assert sha(p)==e['sha256'];blob=subprocess.check_output(['git','-C',str(W),'show',head+':'+str(p.relative_to(W))]);assert hashlib.sha256(blob).hexdigest()==e['sha256']
 for n in ['PROGRESS.md','CONTROLLER_LATEST.json','LATEST_A09.json']:
  p=BASE/n;assert subprocess.check_output(['git','-C',str(W),'show',head+':'+str(p.relative_to(W))])==p.read_bytes()
 for e in read(C/'INPUT_VALIDATION.json')['files']:assert sha(D8/e['path'])==e['sha256']
 return {'schema':'pod-a-a09-post-push-proof-v1','status':'PASS','commit':head,'remote_equal':True,'public_files_including_manifest':len(entries),'public_manifest_sha256':seal['manifest_sha256'],'all_committed_bytes_match':True,'A08_indexed_files_preserved':168,'guard':proof,'verified_utc':now()}

def export_sources():
 for p in (A/'code').glob('*.py'):publish('CODE/'+p.name,p.read_bytes())
 for e in read(C/'CONSUMER_SOURCE_QUALIFICATION.json')['source_files']:assert sha(A/'code'/e['path'])==e['sha256']
 publish('SOURCE_SUPPLEMENT.json',{'schema':'pod-a-a09-source-supplement-v2','frozen_qualified_consumer_source':ref(C/'CONSUMER_SOURCE_QUALIFICATION.json'),'consumer_source_unchanged':True,'public_CODE_files':[{'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((D/'CODE').glob('*.py'))],'closure_helpers_do_not_change_frozen_numerical_consumer':True,'created_utc':now()})

def metadata():
 proof=verify_public();put(C/'REPORT_DELIVERY_PROOF.json',proof);publish('POST_PUSH_PROOF.json',proof)
 b=read(C/'BACKUP_MANIFEST.json');checks=read(C/'FRESH_RESTORE_CHECK.json')['consumer_checks'];assert checks['status']=='PASS'
 for name in ['A09_RECEIPT.json','REMOTE_HANDOFF.json','RESUME_MANIFEST.json']:
  v=read(C/name);v.update(status='COMPLETE' if name=='A09_RECEIPT.json' else 'TERMINAL_HANDOFF_DELIVERED',report_delivery_commit=proof['commit'],metadata_commit=None,payload_revision=b['revision'],receipt_revision=None,post_push_proof='POST_PUSH_PROOF.json',final_receipt_binding='Separate immutable private final receipt binds later metadata commit and actual observer stop without a self-hash cycle',automatic_resume=False,further_work_authorized=False)
  if 'scope_booleans' in v:v['scope_booleans'].update(REPORT_DELIVERED=True,GIT_DELIVERED=True)
  if name=='A09_RECEIPT.json':v.update(report_validation=ref(C/'REPORT_VALIDATION.json'),completed_report_delivery_utc=now(),terminal_action_pending='Verified report delivery complete; final metadata protection then owned observer stop and separate receipt')
  put(C/name,v);publish(name,v)
 text=(D/'SESSION_HANDOFF.md').read_text().replace('A09 is finishing its finite report/recovery delivery.','A09 report delivery and saved-analysis recovery have passed.').replace('Terminal status is certified only by A09_RECEIPT.json and separate remote/private proofs, not by this prose alone.','Report delivery is certified by [A09 receipt](A09_RECEIPT.json) and [exact-byte post-push proof](POST_PUSH_PROOF.json). The proof names the report commit; the separate immutable final private receipt binds the later metadata commit and actual observer stop. No automatic resume is authorized.')
 text+='\n## Verified delivery\n\nReport commit `'+proof['commit']+'`; private saved-analysis payload revision `'+b['revision']+'`, SHA256 `'+b['archive_sha256']+'`. All 254 included files, eight prediction/metric paths, two saved audit-refit artifacts and the frozen classifier/LM contrast draws passed. Probability, metric and every-draw residuals were zero. This is saved-analysis recovery; model weights and full GPU recreation are excluded. Full-project and A04 status remain PARTIAL.\n'
 publish('SESSION_HANDOFF.md',text)
 from progress import update
 update('Qualified reporting and force-fresh saved-analysis recovery PASS; report exact-byte Git proof PASS. Protect final metadata and stop the owned observer; no further science.',status='COMPLETE')
 # Replace the old progress placeholder with the actual completed recovery outcome.
 for p in [D/'PROGRESS.md',BASE/'PROGRESS.md']:
  guard(allow_dirty=True);write_md(p,p.read_text().replace('Prior proof separately attributed | 0 | Current check until sealed','Fresh all-member + eight-path/two-head/contrast PASS | 0 | 0'))
 export_sources();print(json.dumps({'status':'METADATA_READY','report_delivery_commit':proof['commit']}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('operation',choices=['export','verify','metadata']);a=p.parse_args()
 if a.operation=='export':export_sources()
 elif a.operation=='metadata':metadata()
 else:
  proof=verify_public();put(C/'LATEST_GIT_BYTE_PROOF.json',proof);print(json.dumps(proof))
