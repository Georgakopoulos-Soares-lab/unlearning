from pathlib import Path
import json,hashlib,sys
from ops import C,A,R,save,now
from mirror_contract import admit
old=C.with_name('attempt-001');T=R/'docs/experiments/ashay/POD_A_SALIENCY/20261123T111855Z-saliency';plan=json.loads((T/'S02/attempt-001/S03_RECOVERY_PLAN.json').read_text());selected=json.loads((old/'ACCEPTED_CHECKPOINT_REGISTRY.json').read_text())['selected_by_stage'];rows=json.loads((C/'MIRROR_HANDOFF.json').read_text());out=[];source={};sidecar=A.parent.parent/'S01/attempt-001/sidecars'
for p in plan['candidate_dependencies']:
 for m in p['members']:source[m['object_id']]={'name':m['name'],'bytes':m['reported_size_bytes'],'sha256':m.get('local_sha256')}
# Latest-pointer sidecars were sealed separately in S01; recover exact ID/name/bytes locally, without a new Drive query.
for r in rows:
 m=json.loads((C/'remote-evidence'/r['alias']/'manifest.json').read_text())
 for f in m['files']:
  if f['source_file_id'] not in source:
   p=sidecar/f['source_file_id']
   if p.is_file():
    data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==f['sha256'];source[f['source_file_id']]={'name':f['path'].rsplit('/',1)[-1],'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
   else:
    observed=json.loads((sidecar.parent/('metadata-'+f['source_file_id']+'.json')).read_text())['result']['structuredContent'];assert observed['id']==f['source_file_id'] and observed['title']==f['path'].rsplit('/',1)[-1] and int(observed['size'])==f['bytes'];source[f['source_file_id']]={'name':observed['title'],'bytes':int(observed['size']),'sha256':None,'sha256_null_reason':'No current sealed local S01 byte copy at expected location. Retain original metadata ID/name/size join; independently hash newly acquired exact HF bytes. Do not rewrite historical S01 claim or fabricate prior local hash.'}
for r in sorted(rows,key=lambda r:r['alias']):
 root=C/'remote-evidence'/r['alias'];recraw=(root/'receipt.json').read_bytes();manraw=(root/'manifest.json').read_bytes();assert hashlib.sha256(recraw).hexdigest()==r['receipt_sha256'] and hashlib.sha256(manraw).hexdigest()==r['manifest_sha256'];entry=admit(r,json.loads(recraw),json.loads(manraw),selected,source)
 if r['alias'] in ['candidate_01','candidate_02']:
  earlier=json.loads((T/'S03/attempt-001/QUALIFICATION_MATRIX.json').read_text());match=next(x for x in earlier['candidates'] if x['alias']==r['alias']);assert match['payload_sha256']==r['native_shard_sha256'];entry['prior_qualified_native_digest_matches']=True
 entry['upstream_limit']='Transfer-observed Drive IDs/version/checksums are supplied remote evidence, not a fresh independent Drive query or immutable upstream revision. No retrospective rewrite of S01unknown fields.';out.append(entry)
save(C/'SEALED_SOURCE_MEMBER_MAP.json',source);save(C/'MIRROR_ADMISSION.json',{'schema_version':'s03-exact-hf-mirror-admission-v1','status':'PASS9REMOTE_METADATA_AND_PROVENANCE_JOINS','records':out,'current_repository_private':True,'handoff_sha256':hashlib.sha256((C/'MIRROR_HANDOFF.json').read_bytes()).hexdigest(),'observed_utc':now()});print('REMOTE_MIRROR_METADATA_ADMISSION_PASS',len(out))
