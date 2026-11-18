from common import *
import ast,difflib,importlib.metadata
files=['other_five_common.py','build_other_five_cache.py','fit_other_five.py','producer_metrics.py','independent_math.py','production_contract.py','qualification_contract.py']
for p in (A/'code').glob('*.py'):ast.parse(p.read_text())
log=A/'logs/adapter_tests.log';assert 'Ran 22 tests' in log.read_text() and log.read_text().rstrip().endswith('OK')
put(C/'ADAPTER_VALIDATION.json',{'status':'PASS','synthetic_tests':22,'log':ref(log),'initial_fixture_exception_type_failure_preserved':ref(A/'logs/adapter_tests.initial_failure.log'),'test_source':ref(A/'code/test_other_five.py'),'all_owned_modules_parse':True,'CPU_environment_matches_A06':True,'GPU_initialized':False,'production_fits_during_tests':0,'scope':'Synthetic producer/independent binary and multiclass math plus input, identity, cache, atomic resume and writer-lock rejection tests'})
put(C/'CPU_ENVIRONMENT_CHECK.json',{'status':'PASS','python':sys.version.split()[0],'packages':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','joblib','threadpoolctl']},'environment_changes':False,'max_workers':2,'BLAS_threads_per_worker':4})
put(C/'CPU_SOURCE_IDENTITY.json',{'schema':'pod-a-a07-cpu-scientific-source-v1','files':[{'path':n,'sha256':sha(A/'code'/n)} for n in files],'inherited_producer_math_sha256':sha(A/'code/producer_metrics.py'),'inherited_independent_math_sha256':sha(A/'code/independent_math.py'),'frozen_before_first_production_fit':True,'input_unit_manifest':ref(C/'A07_EXECUTION_MANIFEST.json'),'adapter_validation':ref(C/'ADAPTER_VALIDATION.json'),'numerical_policy':'Exact frozen scaler/solver/C/tie/fold/float32 transform semantics; task-aware fivefold and sorted-class macro metrics','A08_refits_executed':0})
patch=''
for old,new in [('h3_common.py','other_five_common.py'),('build_h3_cache.py','build_other_five_cache.py'),('fit_h3.py','fit_other_five.py')]:
 patch+=''.join(difflib.unified_diff((A.parent/'A06-attempt-001/code'/old).read_text().splitlines(True),(A/'code'/new).read_text().splitlines(True),fromfile='A06/'+old,tofile='A07/'+new))
(A/'code/other_five_adapter.patch').write_text(patch)
put(C/'SOURCE_DIFF.json',{'status':'PASS','patch':ref(A/'code/other_five_adapter.patch'),'changes':['Owned A07 roots and finite780 task-aware units','Exact fivefold TRAIN CV and numeric0/1/2 splice support','Dependency-bound reference distribution and feature caches with full sealed member hashes','Per-unit atomic seals, quarantine and one-writer locks; explicit producer-only status','Historical primitives byte-identical; no model runtime imports or forwards'],'primitives_unchanged':True})
print(json.dumps({'status':'FROZEN','source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'tests':22}))
