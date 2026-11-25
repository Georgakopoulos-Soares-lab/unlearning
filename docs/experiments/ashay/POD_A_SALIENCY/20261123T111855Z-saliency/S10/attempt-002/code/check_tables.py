"""Independent roundtrip of every emitted scalar CSV field against separately decoded event digests."""
from pathlib import Path
import json,csv,gzip,hashlib,math,sys,collections
root=Path(sys.argv[1]);d=json.loads((root/'extracted/EXTRACTION_RECEIPT.json').read_text());results=[]
for s in d['sources']:
 h=hashlib.sha256();tags=collections.Counter();n=0;nonfinite=[]
 with gzip.open(root/'extracted'/s['full_scalar_table'],'rt',newline='') as f:
  for n,r in enumerate(csv.DictReader(f),1):
   assert r['source_id']==s['id'] and r['source_sha256']==s['sha256'];order=int(r['event_order']);vi=int(r['value_order']);assert r['observation_id']==s['sha256']+':'+str(order)+':'+str(vi)
   value=float(r['value']);wall=float(r['wall_time']);assert repr(value)==r['value'] and repr(wall)==r['wall_time'];tags[r['tag']]+=1
   h.update(json.dumps([order,vi,r['tag'],repr(value),int(r['step']),repr(wall)],ensure_ascii=False,separators=(',',':')).encode()+b'\n')
   if not math.isfinite(value) or not math.isfinite(wall):nonfinite.append(r['observation_id'])
 assert n==s['scalar_count'] and dict(tags)==s['tag_counts'] and h.hexdigest()==s['independent_wire_scalar_digest']
 results.append({'id':s['id'],'rows_checked':n,'CSV_roundtrip_scalar_digest':h.hexdigest(),'nonfinite_observation_ids':nonfinite});print('FULL_CSV_CHECKED',s['label'],n,'nonfinite',len(nonfinite),flush=True)
v={'status':'PASS','scalar_rows_checked':sum(x['rows_checked'] for x in results),'nonfinite_observations':sum(len(x['nonfinite_observation_ids']) for x in results),'all_CSV_rows_equal_independent_wire_decode':True,'sources':results};(root/'extracted/FULL_TABLE_INDEPENDENT_VALIDATION.json').write_text(json.dumps(v,indent=2)+'\n')
