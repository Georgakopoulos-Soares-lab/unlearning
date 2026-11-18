"""Resolve every published artifact descriptor and row locator to immutable members."""
from common6 import *
from protect_final6 import public_proof
from finish6 import seal
from delivery6 import deliver
import csv
def main():
 proof=public_proof();lookup={};nodes=read(D5/'RECOVERY_DEPENDENCY_GRAPH.json')['nodes'];backups=read(C/'BACKUP_VERIFICATION.json')['checkpoints']
 for b in backups:
  manifest=read(Path(b['fresh_consumer'])/'MEMBER_MANIFEST.json');lookup[(b['repository'],b['revision'],b['archive_path'])]={e['path']:e for e in manifest['files']}
 for name in ['base_R1','controls']:
  n=next(n for n in nodes if n['id']=='historical/'+name);index=C.parent/'A03-attempt-001'/('PAYLOAD_CHECKSUMS_'+name+'.json');assert sha(index)==n['prior_A09_local_hash_proof']['member_index']['sha256'];lookup[(n['repository'],n['revision'],n['remote_path'])]={e['path']:e for e in read(index)['files']}
 descriptors=read(D/'PRIVATE_PROVENANCE_MAP.json')['artifacts']
 for identity,e in descriptors.items():
  assert digest(e)==identity;member=lookup[(e['repository'],e['revision'],e['archive_path'])][e['member']];assert member['sha256']==e['sha256'] and member['bytes']==e['bytes']
 rows=0;locators=0
 for name in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv','LM_RESULTS.csv']:
  with (D/name).open() as f:
   for r in csv.DictReader(f):
    rows+=1
    for field,hashfield in [('prediction_locator','prediction_sha256'),('reference_prediction_locator','reference_prediction_sha256'),('producer_receipt_locator','producer_receipt_sha256'),('audit_receipt_locator','audit_receipt_sha256'),('input_locator','input_sha256')]:
     if not r.get(field):continue
     pointer=r[field].split('#',1)[0];assert pointer.startswith('provenance:');entry=descriptors[pointer.removeprefix('provenance:')];assert entry['sha256']==r[hashfield];locators+=1
 assert rows==4934
 for name in ['SOURCE_IDENTITY.json','CPU_SOURCE_IDENTITY.json']:
  source=read(C/name)
  for e in source.get('inference_files',source.get('files',[])):assert sha(A/'code'/e['path'])==e['sha256']
 record={'status':'PASS','rows':rows,'unique_typed_immutable_artifact_descriptors':len(descriptors),'row_locator_hash_joins_verified':locators,'all_new_descriptors_resolve_in_fresh_verified_archive_member_manifests':True,'historical_descriptors_match_exact_pinned_checksum_indexes':True,'frozen_scientific_and_CPU_sources_unchanged':True,'scientific_delivery_commit':proof['commit'],'large_arrays_reaudited_or_retransferred':False,'observed_utc':now()};put(C/'PORTABLE_PROVENANCE_VALIDATION.json',record);publish('PORTABLE_PROVENANCE_VALIDATION.json',record);publish('METADATA_POST_PUSH_PROOF.json',proof)
 dtext=(D/'SESSION_HANDOFF.md').read_text();dtext=dtext.replace('Read [receipt]','Read [predeclared H3 findings](H3_FINDINGS.md), [stage history](STAGE_HISTORY.csv), [receipt]');publish('SESSION_HANDOFF.md',dtext);guard();md(B/'SESSION_HANDOFF.md',dtext.replace('](','](attempts/'+cfg['attempt_id']+'/'));publish('DELIVERY_IDENTITY_CHAIN.json',{'scientific_delivery_commit':read(C/'SCIENTIFIC_DELIVERY.json')['commit'],'current_metadata_readback_proof_commit':proof['commit'],'later_proof_commit':'Own commit hash is recorded in subsequent private delivery receipt, avoiding self-reference.','final_private_receipt_repository':REPO,'final_private_receipt_path':'POD_A/'+cfg['run_id']+'/A06/'+cfg['attempt_id']+'/delivery-001/A06_R5_DELIVERY_RECEIPT.final.json','returned_receipt_revision_binding':'Pod-local FINAL_CLOSEOUT.json','A07_started':False});publish('code/postcheck6.py',(A/'code/postcheck6.py').read_bytes());seal();r=deliver('A06 R5: verify portable artifact joins and bind exact delivery readback');put(C/'METADATA_DELIVERY.json',r);print(json.dumps({k:r[k] for k in ['status','commit','remote_equal']}));print(json.dumps(record))
if __name__=='__main__':main()
