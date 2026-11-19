"""Preserve unavailable exit codes; accept only enumerated sealed scientific outputs."""
from common8 import *

def main():
 name='adjacent-R4_minus_R3-001';active=C/'jobs'/(name+'.active.json');e=read(active);p=Path('/proc')/str(e['pid'])/'stat';assert not (p.exists() and p.read_text().split()[2]!='Z' and p.read_text().split()[21]==e['proc_start_ticks']);assert e['launcher_sha256']==sha(C/'WORKER8.before_exit_record_fix.txt');root=A/'contrasts/classifier/R4_minus_R3';receipts=list(root.glob('*/*/*/seed*/COMPLETE.json'));assert len(receipts)==546;attempted=0
 for p in receipts:
  r=read(p);assert r['status']=='PASS' and r['identity']['contrast_source_sha256']==sha(C/'CONTRAST_SOURCE_IDENTITY.json')
  for f in r['files']:assert sha(p.parent/f['path'])==f['sha256']
  j=read(p.parent/'RESULTS.json');assert j['status']=='PASS' and len(j['rows'])==10;attempted+=j['attempted_values']
 lines=[json.loads(l) for l in (A/'logs'/(name+'.stdout.log')).read_text().splitlines()];assert len(lines)==546 and all(r['status']=='PASS' for r in lines);assert not (A/'logs'/(name+'.stderr.log')).read_bytes();assert attempted==10920000;out=e|{'status':'EXIT_CONFIRMED_SEALED_SCIENCE_PASS_WRAPPER_RECORD_REPAIRED','exit_code':None,'exit_code_missing_reason':'Supervisor bookkeeping exception after wait; child status was not persisted and is not fabricated','wall_seconds':None,'completion_observed_utc':now(),'science_acceptance':'All546 source-bound units/5460 exact-key rows sealed PASS;546 terminal PASS records;scientific stderr empty','attempted_paired_values_verified':attempted,'repeated_computation':False,'stdout_sha256':sha(A/'logs'/(name+'.stdout.log')),'stderr_sha256':sha(A/'logs'/(name+'.stderr.log'))};assert not (C/'jobs'/(name+'.result.json')).exists();put(C/'jobs'/(name+'.result.json'),out);atomic(active.with_name(name+'.active.running-snapshot.json'),active.read_bytes());put(active,out);print('WRAPPER_EXIT_METADATA_RECONCILED_WITHOUT_RECOMPUTATION')
if __name__=='__main__':main()
