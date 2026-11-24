"""Read-only selectors for the frozen S04 manifest. Prints metadata; never dispatches jobs."""
from pathlib import Path
from collections import Counter
import argparse,json,hashlib
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--candidate');p.add_argument('--task');p.add_argument('--kind');p.add_argument('--phase',choices=['S05','S06','S07','S08','S09']);p.add_argument('--include-deferred',action='store_true');p.add_argument('--emit-keys',action='store_true');a=p.parse_args();c=json.loads((a.root/'COVERAGE_PLAN.json').read_text());source=a.root/'EXPECTED_UNIT_KEYS.jsonl';assert hashlib.sha256(source.read_bytes()).hexdigest()==c['expected_keys_sha256'];count=Counter();n=0;digest=hashlib.sha256()
for line in source.open():
 r=json.loads(line)
 if a.candidate and r['c']!=a.candidate:continue
 if a.task and r['t']!=a.task:continue
 if a.kind and r['k']!=a.kind:continue
 deferred=r.get('f') in ['immediate_parent','LM_base_reference']
 if deferred and not a.include_deferred:continue
 if r['k']=='contrast':phase='S09'
 elif r['k'] in ['audit_refit','audit_optimizer_call']:phase='S05' if r['t']=='emp_H3' else 'S08'
 elif r['t']=='emp_H3':phase='S05'
 elif r['k'] in ['extraction','LM','LM_metric']:phase='S06'
 else:phase='S07'
 if a.phase and a.phase!=phase:continue
 n+=1;count[r['k']]+=1;digest.update((r['id']+'\n').encode())
 if a.emit_keys:print(json.dumps(r,separators=(',',':'),sort_keys=True))
if not a.emit_keys:print(json.dumps({'matching_planned_specs':n,'counts':dict(count),'ordered_ids_sha256':digest.hexdigest(),'execution_performed':False,'deferred_included':a.include_deferred},indent=2))
