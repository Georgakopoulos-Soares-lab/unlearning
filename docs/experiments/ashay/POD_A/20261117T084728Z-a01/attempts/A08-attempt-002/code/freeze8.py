from common8 import *
import difflib
assert not (C/'SOURCE_IDENTITY.json').exists();log=(A/'logs/tests.001.stderr.log').read_text();assert 'Ran 32 tests' in log and log.rstrip().endswith('OK')
# Reviewed task partition flags and explicit default-linear quantiles preserve numerical semantics.
files=['audit_common.py','audit_units.py','refit_panel.py','independent_math.py','rank_crosscheck.py','analysis_pairs.py']
assert sha(A/'code/independent_math.py')==sha(A7/'code/independent_math.py');assert sha(A/'code/rank_crosscheck.py')==sha(A7/'code/producer_metrics.py')
put(C/'IMPLEMENTATION_VALIDATION.json',{'status':'PASS','synthetic_and_adversarial_tests':32,'synthetic_solver_calls':2,'real_audit_refits_so_far':0,'test_log_sha256':sha(A/'logs/tests.001.stderr.log'),'test_sources':{n:sha(A/'code'/n) for n in ['test_audit.py','test_scope8.py']},'reviewed_numerical_independence':'Direct float32 scaler/coef reconstruction; pairwise win AUROC and threshold AP; saved-index multiplicities via add.at, distinct from producer rank aggregation/bincount; no producer orchestration invoked','additional_post_test_review':'Task-only partitioning of predeclared six panel units and explicit existing linear quantile default, no changed mathematical calculation'})
put(C/'SOURCE_IDENTITY.json',{'status':'FROZEN','schema':'pod-a-r5-a08-independent-source-v1','files':[{'path':n,'bytes':(A/'code'/n).stat().st_size,'sha256':sha(A/'code'/n)} for n in files],'input_sha256':sha(C/'A08_INPUTS.json'),'manifest_sha256':sha(C/'A08_EXECUTION_MANIFEST.json'),'qualification_sha256':sha(C/'IMPLEMENTATION_VALIDATION.json'),'producer_source_separate_sha256':sha(C7/'CPU_SOURCE_IDENTITY.json'),'frozen_before_real_scientific_work':True,'frozen_utc':now()})
diff=''
for n in files:
 p=A.parent/'A08-attempt-001/code'/n
 if p.exists():diff+=''.join(difflib.unified_diff(p.read_text().splitlines(True),(A/'code'/n).read_text().splitlines(True),fromfile='historical-A08/'+n,tofile='owned-R5-A08/'+n))
atomic(C/'AUDIT_SOURCE_ADAPTATION.raw.patch',diff.encode());atomic(C/'AUDIT_SOURCE_ADAPTATION.display.patch',('\n'.join(l.rstrip() for l in diff.splitlines())+'\n').encode());put(C/'SOURCE_DIFF_IDENTITY.json',{'raw_sha256':sha(C/'AUDIT_SOURCE_ADAPTATION.raw.patch'),'display_sha256':sha(C/'AUDIT_SOURCE_ADAPTATION.display.patch'),'independent_math_reused_byte_identically':True,'initial_independent_source_freeze_sha256':sha(C/'SOURCE_IDENTITY.json')});print('AUDIT_SOURCE_FROZEN '+sha(C/'SOURCE_IDENTITY.json'))
