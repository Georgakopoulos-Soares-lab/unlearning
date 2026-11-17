"""Join independently exited native workers; never promote engineering bytes."""
from pathlib import Path
import argparse
import json
from .modes import preflight,ROUTE_KEYS
from .budget import ENGINEERING,SCIENTIFIC
from .contracts import require,file_sha
from .qualification import compare
from .gate import load_result

REQUIRED_MATRIX_GATES = ('schema_all26_full_vocabulary_train12_filler_exclusion',
    'all100_native_adapter_branch_execution','independent_float64_lm_diagnostic',
    'native_normalized_input_scale_bias_eval_dropout_disable','repeat','logical1',
    'filler_perturbation','hookless','adapter_disabled_vs_plain_same_candidate_parent',
    'A_B_A_same_parent_full_adapter_overwrite','strict_state_after_swap')


def join_receipts(plan,binding,policy,key,matrix,fresh,rows):
    for result in (matrix,fresh):
        require(result['mode']==plan['mode'] and result['checkpoint_id']==binding['checkpoint_id']
                and result['cache_key']==key,'CACHE_KEY','Wrong mode/case/dependencies')
        require(result.get('error') is None and result.get('all_observed_gates_passed') is True,
                'NATIVE_GATES_FAILED','Native worker failed; partial outputs remain diagnostic')
    require(matrix['phase']=='matrix' and fresh['phase']=='fresh','FRESH_PROCESS','Distinct matrix/fresh worker receipts required')
    require(all(matrix['gates'].get(k,{}).get('pass_') is True for k in REQUIRED_MATRIX_GATES),
            'NATIVE_GATES_FAILED','Required numerical/state gate missing or failed')
    for field in ['parent_fingerprint','output_head_fingerprint','adapter_tensors']:
        require(matrix['actual_snapshot'][field]==fresh['actual_snapshot'][field],'FRESH_STATE','Fresh process loaded another state')
    return dict(mode=plan['mode'],checkpoint_id=binding['checkpoint_id'],cache_key=key,
        scientifically_qualified=False,downstream_eligible=False,reference_policy=policy,
        matrix_pass=True,fresh_state_pass=True)


def finalize(plan,case,matrix_dir,fresh_dir,output):
    binding,rows,policy,key=preflight(plan,case)
    require(not output.exists(),'OUTPUT_EXISTS',str(output))
    namespace=Path(plan['artifact_root'])/('engineering' if plan['mode']==ENGINEERING else 'scientific')
    for p in (matrix_dir,fresh_dir,output):require(p.resolve().is_relative_to(namespace.resolve()),'MODE_SEPARATION',str(p))
    mc=json.loads((matrix_dir/'CONTROLLER.json').read_text());fc=json.loads((fresh_dir/'CONTROLLER.json').read_text())
    require(mc['returncode']==fc['returncode']==0,'WORKER_FAILED','Both independent processes must exit successfully')
    matrix=json.loads((matrix_dir/'worker/RESULT.json').read_text());fresh=json.loads((fresh_dir/'worker/RESULT.json').read_text())
    result=join_receipts(plan,binding,policy,key,matrix,fresh,rows)
    comparison=compare(load_result(fresh['principal'],binding['allowed_read_roots']),load_result(matrix['principal'],binding['allowed_read_roots']),rows,matrix['contract'])
    result['fresh_process_comparison']=comparison
    require(comparison['pass_'],'FRESH_NUMERICAL_FAILURE',json.dumps(comparison))
    require(matrix['actual_snapshot']['parent_fingerprint']==fresh['actual_snapshot']['parent_fingerprint'],'FRESH_STATE','Changed backbone')
    if plan['mode']==SCIENTIFIC:
        for k in ('parent_fingerprint','output_head_fingerprint'):
            require(binding.get(k)==matrix['actual_snapshot'][k],'BOUND_STATE',k)
        if policy=='COMPARE_INDEPENDENT_ORIGINAL':
            require(matrix['gates'].get('independent_original_agreement',{}).get('pass_') is True,'REFERENCE_BLOCKED','R2 original comparison did not pass')
        require(policy in ('COMPARE_INDEPENDENT_ORIGINAL','CREATE_FIRST_ORIGINAL_REFERENCE','INHERITED_QUALIFIED_ROUTE'),
                'REFERENCE_BLOCKED','Scientific route policy missing')
        result.update(scientifically_qualified=True,downstream_eligible=True,all_route_gates_passed=True,status='QUALIFIED_B04_SCOPED')
        result.update({k:binding[k] for k in ROUTE_KEYS})
        if policy=='CREATE_FIRST_ORIGINAL_REFERENCE':
            result['first_original_reference']=matrix['principal']
            result['original_agreement']='FIRST_REFERENCE_CREATED; NO_EXTERNAL_AGREEMENT_COMPARISON'
            result['original_provenance']=binding['reviewed_provenance']
    else:
        result.update(status='ENGINEERING_DIAGNOSTIC_PASS',original_agreement='NOT_AVAILABLE',all_route_gates_passed=False)
    result['worker_receipts']=[dict(path=str(p/'worker/RESULT.json'),sha256=file_sha(p/'worker/RESULT.json')) for p in (matrix_dir,fresh_dir)]
    output.write_text(json.dumps(result,indent=2));return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--case',required=True)
    ap.add_argument('--matrix',type=Path,required=True);ap.add_argument('--fresh',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();result=finalize(json.loads(a.plan.read_text()),a.case,a.matrix,a.fresh,a.output)
    print(json.dumps({k:v for k,v in result.items() if k not in ('fresh_process_comparison','worker_receipts')}))
if __name__=='__main__':main()
