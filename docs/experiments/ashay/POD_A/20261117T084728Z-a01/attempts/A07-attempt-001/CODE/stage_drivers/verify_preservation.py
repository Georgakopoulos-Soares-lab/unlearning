"""Check immutable predecessor bytes and repository boundaries; no prior science rerun."""
from common import *
from research_guard import guard
def verify():
 proof=read(C/'A06_INPUT_ANCHORS.json');old=BASE/'attempts/A06-attempt-001'
 for e in proof['A06_public_files']:assert sha(old/e['path'])==e['sha256']
 for p,h in proof['anchors'].items():assert sha(BASE/'attempts'/p)==h
 sourcefiles=[]
 for n in ['CPU_SOURCE_IDENTITY.json','SOURCE_IDENTITY.json']:
  j=read(C.parent/'A06-attempt-001'/n)
  for e in j.get('files',j.get('inference_files',[])):
   p=A.parent/'A06-attempt-001/code'/e['path'];assert sha(p)==e['sha256'];sourcefiles.append({'path':str(p),'sha256':e['sha256']})
 result={'status':'PASS','A06_public_files_unchanged':len(proof['A06_public_files']),'accepted_byte_anchors_unchanged':len(proof['anchors']),'A06_source_files_unchanged':sourcefiles,'research_boundary_guard':guard(allow_dirty=True),'historical_audits_reexecuted':False,'scope':'Current immutable byte identity and Git boundary checks only; no old fitting/extraction/numerical audit repeated','verified_utc':now()};put(C/'PRESERVATION_VERIFICATION.json',result);publish('PRESERVATION_VERIFICATION.json',result)
 # Make inherited private archive locators explicit without repacking unchanged payloads.
 inherited={'A03_historical_restores':read(C03/'RESTORE_VALIDATION.json'),'A03_backup_graph':read(C03/'BACKUP_VERIFICATION.json'),'A06_checkpoint_graph':read(C.parent/'A06-attempt-001/BACKUP_VERIFICATION.json'),'historical_payloads_repacked':False,'original_base_fold_draw_reference_map':'A07_EXECUTION_MANIFEST.json','backbone_runtime_recreation':'Excluded from A07; exact A04/A06 asset/runtime recipes remain linked by immutable receipt hashes'};publish('HISTORICAL_DEPENDENCIES.json',inherited)
 print(json.dumps({'status':'PASS','A06_public_files_unchanged':len(proof['A06_public_files']),'A06_source_files_unchanged':len(sourcefiles)}))
if __name__=='__main__':verify()
