"""Fresh saved-assessment recovery, with producer data paths denied."""
from common import *
import sys
root=Path(sys.argv[1]).resolve();out=root/'regenerated';assert not out.exists()
forbidden=[str(R),str(BASE/'control'/RUN),str(A)]
def reject_fallback(event,args):
 if event=='open' and isinstance(args[0],(str,bytes)):
  p=str(Path(os.fsdecode(args[0])).absolute())
  if any(p==x or p.startswith(x+'/') for x in forbidden) and not(p==str(root) or p.startswith(str(root)+'/')):raise PermissionError('Producer data fallback forbidden')
sys.addaudithook(reject_fallback)
for name,binding in read(root/'control/INPUT_MANIFEST.json')['files'].items():assert sha(root/'inputs'/name)==binding['sha256'] and (root/'inputs'/name).stat().st_size==binding['bytes']
from build_assessment import build
actual=build(root/'inputs',out);expected=read(root/'control/CORE_OUTPUT_MANIFEST.json')['files'];assert actual==expected
from verify_assessment import verify
independent=verify(root/'inputs',out);assert independent==read(root/'public/VERIFICATION.json')
save(root/'RECOVERY_RESULT.json',{'status':'PASS','exactly_regenerated_core_files':actual,'independent_reconciliation':independent,'candidate_assessments_regenerated':9,'external_source_records':0,'integrated_views_regenerated':0,'pending_ledger_regenerated':True,'coverage_regenerated':True,'S11_handoff_sha256':sha(out/'S11_HANDOFF.json'),'producer_path_fallback':False,'producer_paths_denied_by_audit_hook':True,'large_dependencies_repacked_or_rehashed':False,'new_model_or_probe_or_bootstrap_execution':False,'external_evaluation_reproduced':False,'clean_runtime_recreation_claim':False});print('S10_FRESH_ASSESSMENT_RECOVERY_PASS',len(actual),'corefiles;9assessments;0externalmeasurements',flush=True)
