"""Independent actual-output reconciliation; source projections are not measurements."""
from common import *
from independent import reconcile_no_data
import csv,sys
def verify(inputs,out):
 d={'discovery':read(inputs/'DISCOVERY_MANIFEST.json'),'candidates':read(inputs/'CANDIDATE_BINDINGS.json'),'baseline':read(inputs/'S10_HANDOFF.json')};outputs={n:read(out/n) for n in ['COLLABORATOR_FORGET_INPUTS.json','EXACT_JOIN_ELIGIBILITY.json','RETAIN_FORGET_VIEWS.json','PENDING_FORGET_INPUTS.json']};receipt=reconcile_no_data(d,outputs)
 with (out/'COVERAGE.csv').open() as f:table=list(csv.DictReader(f))
 assert len(table)==9 and {r['candidate'] for r in table}=={c['alias'] for c in d['candidates']}
 for row in table:
  candidate=next(v for v in d['candidates'] if v['alias']==row['candidate']);assert row['logical_content_sha256']==candidate['content_sha256'] and int(row['step'])==candidate['step'] and row['forget_estimate']=='NOT_SUPPLIED' and row['forget_interval']=='NOT_SUPPLIED' and row['layerwise_forget_evidence']=='NOT_SUPPLIED' and row['forget_source_records']=='0' and int(row['retain_classifier_marginals'])==4680 and int(row['retain_admitted_contrasts'])==5436
 handoff=read(out/'S11_HANDOFF.json');assert handoff['administrative_disposition']=='LIMITED_SCOPE_COMPLETE' and handoff['scientific_integration']=='PENDING' and handoff['external_dependency_disposition']=='PENDING' and handoff['S11_permitted_scope']=='RETAIN_ONLY_WITH_EXTERNAL_FORGET_INTEGRATION_PENDING' and handoff['S11_approved'] is False and handoff['S11_executed'] is False
 for n,h in handoff['source_files'].items():assert sha(out/n)==h
 for name,phrases in {'S10_REPORT.md':['0 supplied aggregate files,0 source records,0 qualified source joins and0 rejected source joins','9 verified candidate dependency assessments and9 missing-source requirements','48,924','42,228','PENDING','PARTIAL'],'UNSENT_COLLABORATOR_REQUEST.md':['not sent','no raw forget','Sayyed'],'INTEGRATION_LIMITS.md':['No missing value is replaced by zero','S11 may report','no-deadline']}.items():
  content=(out/name).read_text()
  for phrase in phrases:assert phrase.lower() in content.lower(),(name,phrase)
 receipt.update(coverage_rows_verified=9,source_record_coverage='Emptysetexactlyaccounted,notunobserveddatafabricated',source_and_handoff_hashes_verified=True,report_counts_and_uncertainty_labels_verified=True,conditional_intervals_inherited_unchanged=True,figures_generated=0,scientific_integration='PENDING',external_dependency_disposition='PENDING',S11_permitted_scope=handoff['S11_permitted_scope'])
 return receipt
if __name__=='__main__':
 ir=Path(sys.argv[1]) if len(sys.argv)>1 else A/'inputs';out=Path(sys.argv[2]) if len(sys.argv)>2 else P;v=verify(ir,out);save(out/'VERIFICATION.json',v)
 if ir==A/'inputs':save(C/'VERIFICATION.json',v);progress('INDEPENDENT_ASSESSMENT_VERIFIED','Run finite private archive freshreadback/safeextraction and regenerate allcoreoutputs fromrestoredinputs; no S11.',verified_candidate_assessments=9,eligible_external_joins=0,scientific_integration='PENDING',owned_processes=[])
 print('S10_INDEPENDENT_ASSESSMENT_PASS',flush=True)
