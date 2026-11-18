from common7 import *
import difflib
assert 'Ran 26 tests' in (A/'logs/tests.002.stderr.log').read_text() and (A/'logs/tests.002.stderr.log').read_text().rstrip().endswith('OK')
names=['scope7.py','other_five_common.py','production_contract.py','qualification_contract.py','producer_metrics.py','independent_math.py','build_other_five_cache.py','fit_other_five.py','restore7.py','initial_gate7.py']
assert not (C/'CPU_SOURCE_IDENTITY.json').exists()
files=[{'path':n,'bytes':(A/'code'/n).stat().st_size,'sha256':sha(A/'code'/n)} for n in names]
put(C/'ADAPTER_VALIDATION.json',{'status':'PASS','tests':26,'synthetic_binary_and_multiclass_fits':2,'real_production_fits':0,'test_source_sha256':sha(A/'code/test_other_five.py'),'scope_tests_sha256':sha(A/'code/test_scope7.py'),'stdout_sha256':sha(A/'logs/tests.002.stdout.log'),'stderr_sha256':sha(A/'logs/tests.002.stderr.log'),'observed_utc':now()})
put(C/'CPU_SOURCE_IDENTITY.json',{'schema':'pod-a-a07-cpu-source-v2','files':files,'input_unit_manifest':{'path':str(C/'A07_EXECUTION_MANIFEST.json'),'sha256':sha(C/'A07_EXECUTION_MANIFEST.json')},'input_identity_sha256':sha(C/'A07_INPUTS.json'),'validation_sha256':sha(C/'ADAPTER_VALIDATION.json'),'upstream_A06_source':'06752139d8c655457629394be35c89b2a09ffa1f5fb483c1a1aabe43b4008593','upstream_A06_CPU_source':'61bc0471e0ea793ef2c8be3529d0990390c97be7786c6144c1ed14a97dbb5eb8','frozen_before_any_real_production':True,'frozen_utc':now()})
diff=''
old=A.parent/'A07-attempt-001/code'
for n in names:
 if (old/n).exists():diff+=''.join(difflib.unified_diff((old/n).read_text().splitlines(True),(A/'code'/n).read_text().splitlines(True),fromfile='prior/'+n,tofile='owned/'+n))
atomic(C/'CPU_SOURCE_ADAPTATION.raw.patch',diff.encode());atomic(C/'CPU_SOURCE_ADAPTATION.display.patch',('\n'.join(s.rstrip() for s in diff.splitlines())+'\n').encode())
put(C/'SOURCE_DIFF_IDENTITY.json',{'raw_sha256':sha(C/'CPU_SOURCE_ADAPTATION.raw.patch'),'display_sha256':sha(C/'CPU_SOURCE_ADAPTATION.display.patch'),'display_changes_only_trailing_whitespace':True,'new_module_names':[n for n in names if not (old/n).exists()]})
print('SOURCE_FROZEN '+sha(C/'CPU_SOURCE_IDENTITY.json'))
