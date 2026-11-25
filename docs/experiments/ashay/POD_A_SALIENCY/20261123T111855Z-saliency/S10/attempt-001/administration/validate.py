from ops import run
import sys,copy,shutil,re,jsonschema
sys.path.insert(0,'/workspace/pod-a-saliency/artifacts/20261123T111855Z-saliency/S10/attempt-001/code')
from common import *
from independent import reconcile_no_data
schema=read(P/'S10_ASSESSMENT.schema.json');documents={n:read(P/n) for n in ['COLLABORATOR_FORGET_INPUTS.json','EXACT_JOIN_ELIGIBILITY.json','RETAIN_FORGET_VIEWS.json','PENDING_FORGET_INPUTS.json']};jsonschema.Draft202012Validator(schema).validate(documents)
inputs={'discovery':read(A/'inputs/DISCOVERY_MANIFEST.json'),'candidates':read(A/'inputs/CANDIDATE_BINDINGS.json'),'baseline':read(A/'inputs/S10_HANDOFF.json')};assert reconcile_no_data(inputs,documents)['status']=='PASS';checks=[]
for name,mutate in [('Missing forget value cannot become zero',lambda d:d['EXACT_JOIN_ELIGIBILITY.json']['candidate_coverage'][0].update(forget_estimate=0)),('Actual source-record set cannot grow silently',lambda d:d['COLLABORATOR_FORGET_INPUTS.json']['normalized_records'].append({'fabricated':True})),('Missing candidate assessment rejected',lambda d:d['EXACT_JOIN_ELIGIBILITY.json']['candidate_coverage'].pop()),('Phantom integrated view rejected',lambda d:d['RETAIN_FORGET_VIEWS.json']['views'].append({'fabricated':True}))]:
 d=copy.deepcopy(documents);mutate(d)
 try:reconcile_no_data(inputs,d)
 except AssertionError:checks.append(name)
 else:raise AssertionError('Mutation survived '+name)
manifest=read(C/'CORE_OUTPUT_MANIFEST.json');assert len(manifest['files'])==11
for name,h in manifest['files'].items():assert sha(P/name)==h
for name,b in read(C/'INPUT_MANIFEST.json')['files'].items():assert sha(A/'inputs'/name)==b['sha256'] and (A/'inputs'/name).stat().st_size==b['bytes']
source=read(C/'SOURCE_IDENTITY.json')
for name,h in source['files'].items():assert sha(A/'code'/name)==sha(P/'code'/name)==h
for phase in range(10):run('S10-validation-preserve-S'+str(phase).zfill(2),['git','diff','--exit-code',PRIOR,'--',str((T/('S'+str(phase).zfill(2))).relative_to(R))],R)
assert read(T/'CONTROLLER_STATE.json')['approvals']['S11']['approved'] is False
files={}
for path in sorted(P.rglob('*')):
 if not path.is_file():continue
 assert not path.is_symlink() and path.stat().st_size<32*1024**2;b=path.read_bytes();assert not re.search(rb'\bhf_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+|X-Amz-Signature=[A-Za-z0-9%]{8,}|X-Goog-Signature=[A-Za-z0-9%]{8,}',b);assert (b'ashay-sriv/'+b'undo-') not in b and (b'ashay-sriv/'+b'unlearning-checkpoint-mirror') not in b;assert path.suffix not in ['.npz','.npy','.joblib','.pt','.distcp','.tar','.gz']
 if path.suffix=='.json':json.loads(b)
 files[str(path.relative_to(P))]={'sha256':sha(path),'bytes':len(b)}
save(C/'OUTPUT_VALIDATION.json',{'status':'PASS','supplementary_schema_pass':True,'canonical_phase_receipt_schema_pending_until_seal':True,'actual_output_adversarial_checks':checks,'focused_checks_reused':29,'core_outputs_verified':11,'candidate_dependency_assessments_verified':9,'unique_external_measurements':0,'eligible_integrations':0,'rejected_actual_source_records':0,'pending_candidate_missing_source_requirements':9,'layerwise_forget_measurements':0,'prior_S00_S09_preserved':True,'deferred_S09_contrasts_unchanged':True,'public_source_boundaries_checked':True,'file_manifest':files,'completed_utc':now()})
shutil.copy2(C/'INPUT_MANIFEST.json',P/'INPUT_MANIFEST.json');shutil.copy2(C/'OUTPUT_VALIDATION.json',P/'OUTPUT_VALIDATION.json');save(P/'ASSESSMENT_COMPLETE.json',{'status':'VERIFIED_DEPENDENCY_DISPOSITION','core_output_hashes':manifest['files'],'independent_verification_sha256':sha(P/'VERIFICATION.json'),'source_identity_sha256':source['source_identity_sha256'],'input_manifest_sha256':sha(C/'INPUT_MANIFEST.json'),'scientific_integration':'PENDING','stage_complete_before_recovery_publication':False,'completed_utc':now()});progress('OUTPUT_VALIDATION_PASS','Protect the compact assessment/code/inputs privately and freshlyregenerate all11coreoutputs and nineindependent candidate assessments.',owned_processes=[],completed_candidate_assessments=9,scientific_integration='PENDING')
print('S10_OUTPUT_SCHEMA_NULL_IDENTITY_COVERAGE_SOURCE_VALIDATION_PASS',flush=True)
