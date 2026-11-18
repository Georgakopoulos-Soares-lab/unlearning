"""Final read-only public/source/service/process verification after delivery."""
from common7 import *
from finish7 import quiet,STATUS,NEXT
from protect_final7 import public_proof
import csv,ast,gzip

def main():
 no_science_imports();proof=public_proof();final=read(C/'FINAL_CLOSEOUT.json');assert final['stage_status']==STATUS and final['next_state']==NEXT and final['metadata_delivery_commit']==proof['commit'] and final['receipt_fresh_readback']=='PASS';state=quiet();frozen=read(C/'CPU_SOURCE_IDENTITY.json')
 for e in frozen['files']:assert sha(A/'code'/e['path'])==e['sha256']
 assert sha(C/'A07_EXECUTION_MANIFEST.json')==frozen['input_unit_manifest']['sha256'] and sha(C/'A07_INPUTS.json')==frozen['input_identity_sha256']
 parsed={'JSON':0,'CSV':0,'Python':0,'gzip':0};files=[]
 for p in D.rglob('*'):
  if not p.is_file():continue
  assert p.stat().st_size>0 and not p.is_symlink();files.append(str(p.relative_to(D)))
  if p.suffix=='.json':read(p);parsed['JSON']+=1
  elif p.suffix=='.csv':
   with p.open() as f:r=csv.DictReader(f);assert r.fieldnames and next(r,None) is not None
   parsed['CSV']+=1
  elif p.suffix=='.py':ast.parse(p.read_text());parsed['Python']+=1
  elif p.suffix=='.gz':
   with gzip.open(p,'rt') as f:assert f.read(1)
   parsed['gzip']+=1
 receipts=list((A/'probes/R5').glob('*/*/seed*/COMPLETE.json'));assert len(receipts)==390
 assert len(read(D/'PROBE_INDEX.json')['units'])==390 and read(D/'PUBLICATION_VALIDATION.json')['unique_logical_ids']==12300
 for e in read(D/'PUBLICATION_VALIDATION.json')['table_sha256s'].items():assert sha(D/e[0])==e[1]
 for group in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv']:
  with (D/group).open() as f:assert all(r['status']=='COMPLETE_UNVERIFIED' and r['independent_audit_status']=='PENDING_A08' for r in csv.DictReader(f))
 record={'status':'PASS','stage_status':STATUS,'public_proof':proof,'source_identity_unchanged':True,'input_manifest_and_identity_unchanged':True,'all_public_outputs_nonempty_parseable':True,'parse_counts':parsed,'public_files':len(files),'processes':state,'observer':'STOPPED','pod_left_running':True,'A08_started':False,'receipt_revision':final['receipt_revision'],'receipt_sha256':final['receipt_sha256'],'next_state':NEXT,'observed_utc':now()};put(C/'POST_EXIT_CHECK.json',record);print(json.dumps({k:record[k] for k in ['status','stage_status','public_files','receipt_revision','next_state']}))
if __name__=='__main__':main()
