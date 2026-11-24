from pathlib import Path
import json,sys,hashlib
from planner import build
inp=json.loads(Path(sys.argv[1]).read_text());frozen=Path(sys.argv[2]);dest=Path(sys.argv[3]);assert not dest.exists()
# Permute unordered record lists; preserve meaningful cohort/seed/row ordering.
for name in ['candidates','folds','draws','source','references','controls','base_prediction_endpoints','control_prediction_endpoints','S03_units']:inp[name].reverse()
result=build(inp,dest);names=['PROTOCOL_FREEZE.json','COVERAGE_PLAN.json','EXPECTED_UNIT_KEYS.jsonl','CONTRAST_PLAN.json','REUSE_MAP.json','AUDIT_PANEL.json','H3_AUDIT_SUBSET.json','BOOTSTRAP_PLAN.json'];hashes={}
for name in names:
 a=hashlib.sha256((dest/name).read_bytes()).hexdigest();b=hashlib.sha256((frozen/name).read_bytes()).hexdigest();assert a==b,name;hashes[name]=a
print(json.dumps({'status':'PERMUTED_INPUT_EXACT_REGENERATION_PASS','files':hashes,'counts':result['counts'],'semantic_protocol_sha256':result['semantic_protocol_sha256'],'producer_fallback':False,'science_executed':False},indent=2),flush=True)
