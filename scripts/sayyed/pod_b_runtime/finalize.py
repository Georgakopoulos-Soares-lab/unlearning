"""Join independently exited native workers; never promote engineering bytes."""
from pathlib import Path
import argparse
import json
from .modes import preflight,ROUTE_KEYS,STATE_KEYS,fixture_identity,state_fingerprint
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



def validate_loaded_result(binding,result):
    from .contracts import canonical_sha,validate_tensor_records
    require(result.get('contract')==binding.get('extraction_contract'),'BOUND_CONTRACT','Actual runtime extraction contract differs')
    require(result.get('resolved_inference_config')==binding.get('resolved_inference_config')
            and canonical_sha(result.get('resolved_inference_config'))==binding['resolved_inference_config_sha256'],
            'EFFECTIVE_CONFIG','Actual resolved configuration differs')
    snapshot=result['actual_snapshot']
    for k in ('parent_fingerprint','output_head_fingerprint','adapter_sha256'):
        require(snapshot.get(k)==binding.get(k),'BOUND_STATE',k)
    for role in ('parent','adapter'):
        records=snapshot.get(role+'_tensors',[])
        validate_tensor_records(binding[role+'_tensor_specs'],records,[],[])
    parent=sorted(snapshot['parent_tensors'],key=lambda r:r['key'])
    head=[r for r in parent if r['key'].startswith(('embedding.','output_layer.','decoder.final_norm.'))]
    require(canonical_sha(parent)==snapshot['parent_fingerprint'] and canonical_sha(head)==snapshot['output_head_fingerprint'],
            'BOUND_STATE','Snapshot digest contradicts actual recorded tensor/buffer values')
    require(snapshot.get('model_training') is False and snapshot.get('grad_enabled') is False
            and snapshot.get('parameters_requiring_grad')==0 and snapshot.get('dropout_training') is False
            and snapshot.get('optimizer_restored') is False and snapshot.get('training_recompute_active') is False
            and snapshot.get('adapter_enabled') is True and snapshot.get('hook_registrations')==0,
            'TRAINING_MODE','Loaded inference state is not frozen/clean')


def validate_execution_events(plan,controllers,results):
    from .contracts import canonical_sha
    ledger=json.loads(Path(plan['ledger_path']).read_text())
    seen_events=set();seen_pids=set()
    manifest=json.loads(Path(plan['runner_manifest']['path']).read_text())
    native=manifest['modules']['scripts.sayyed.pod_b_runtime.native']
    for controller,result in zip(controllers,results):
        event=result.get('execution_event') or {}
        require(controller.get('execution_id')==event.get('execution_id')==plan['execution_id']
                and controller.get('plan_sha256')==event.get('plan_sha256')==canonical_sha(plan),
                'EXECUTION_EVENT','Wrong execution/plan')
        require(controller.get('worker_pid')==event.get('worker_pid')==result.get('observed_worker_pid')
                and isinstance(event.get('worker_pid'),int) and event['worker_pid']>0
                and controller.get('controller_pid')==event.get('controller_pid')
                and controller.get('event_id')==event.get('event_id') and bool(event.get('event_id')),
                'EXECUTION_EVENT','Worker must match the actually observed controller event')
        require(event['worker_pid'] not in seen_pids and event['event_id'] not in seen_events,
                'FRESH_PROCESS','Copied/renamed matrix is not an independent fresh process')
        seen_pids.add(event['worker_pid']);seen_events.add(event['event_id'])
        entries=[s for s in ledger['stages'] if s.get('event_id')==event['event_id']]
        require(len(entries)==1,'EXECUTION_EVENT','No unique accounted execution event')
        entry=entries[0]
        require(controller.get('label')==entry.get('label')==result['checkpoint_id']+':'+result['phase'],
                'EXECUTION_EVENT','Observed invocation phase/case differs from result')
        for key in ('event_id','execution_id','worker_pid','controller_pid','plan_sha256','approval_sha256'):
            require(controller.get(key)==event.get(key)==entry.get(key),'EXECUTION_EVENT',key)
        require(entry['status']==controller.get('status')=='EXITED' and entry.get('returncode')==controller.get('returncode')==0
                and entry['mode']==result['mode']==plan['mode'] and entry['occupied_seconds']>0,
                'WORKER_FAILED','Unsuccessful/unaccounted process')
        origin=result.get('execution_origin',{})
        require(origin.get('kind')=='NATIVE_FROZEN_BACKEND' and origin.get('path')==native['path']
                and origin.get('sha256')==native['sha256'],'NATIVE_EVIDENCE','Mocked/other backend cannot qualify science')
        require(result.get('completed_model_batches',0)>0,'NATIVE_EVIDENCE','No completed native batch evidence')


def finalize(plan,case,matrix_dir,fresh_dir,output):
    if plan.get('mode')==SCIENTIFIC:
        from .approval import validate_live,verify_runner
        validate_live(plan);verify_runner(plan,native=True)
    binding,rows,policy,key=preflight(plan,case)
    require(not output.exists(),'OUTPUT_EXISTS',str(output))
    namespace=Path(plan['artifact_root'])/('engineering' if plan['mode']==ENGINEERING else 'scientific')
    for p in (matrix_dir,fresh_dir,output):require(p.resolve().is_relative_to(namespace.resolve()),'MODE_SEPARATION',str(p))
    mc=json.loads((matrix_dir/'CONTROLLER.json').read_text());fc=json.loads((fresh_dir/'CONTROLLER.json').read_text())
    require(mc['returncode']==fc['returncode']==0,'WORKER_FAILED','Both independent processes must exit successfully')
    matrix=json.loads((matrix_dir/'worker/RESULT.json').read_text());fresh=json.loads((fresh_dir/'worker/RESULT.json').read_text())
    require(matrix.get('checkpoint_id')==fresh.get('checkpoint_id')==case,'CACHE_KEY','Wrong checkpoint receipts')
    validate_execution_events(plan,[mc,fc],[matrix,fresh])
    result=join_receipts(plan,binding,policy,key,matrix,fresh,rows)
    actual=load_result(fresh['principal'],binding['allowed_read_roots']);reference=load_result(matrix['principal'],binding['allowed_read_roots'])
    require(actual.get('mode')==reference.get('mode')==plan['mode'],'MODE_SEPARATION','Engineering arrays cannot qualify scientific execution')
    comparison=compare(actual,reference,rows,matrix['contract'])
    result['fresh_process_comparison']=comparison
    require(comparison['pass_'],'FRESH_NUMERICAL_FAILURE',json.dumps(comparison))
    require(matrix['actual_snapshot']['parent_fingerprint']==fresh['actual_snapshot']['parent_fingerprint'],'FRESH_STATE','Changed backbone')
    if plan['mode']==SCIENTIFIC:
        validate_loaded_result(binding,matrix);validate_loaded_result(binding,fresh)
        for k in ('parent_fingerprint','output_head_fingerprint'):
            require(binding.get(k)==matrix['actual_snapshot'][k],'BOUND_STATE',k)
        if policy=='COMPARE_INDEPENDENT_ORIGINAL':
            require(matrix['gates'].get('independent_original_agreement',{}).get('pass_') is True,'REFERENCE_BLOCKED','R2 original comparison did not pass')
        require(policy in ('COMPARE_INDEPENDENT_ORIGINAL','CREATE_FIRST_ORIGINAL_REFERENCE','INHERITED_QUALIFIED_ROUTE'),
                'REFERENCE_BLOCKED','Scientific route policy missing')
        result.update(scientifically_qualified=True,downstream_eligible=True,all_route_gates_passed=True,status='QUALIFIED_B04_SCOPED')
        result.update({k:binding[k] for k in ROUTE_KEYS})
        if policy=='CREATE_FIRST_ORIGINAL_REFERENCE':
            from .contracts import canonical_sha
            raw=json.loads(Path(matrix['principal']['path']).read_text())
            raw.update({k:binding[k] for k in STATE_KEYS})
            raw.update(**fixture_identity(plan['inputs'],rows),full_state_fingerprint=state_fingerprint(binding),
                extraction_contract=binding['extraction_contract'],provenance_kind='AUTHORITATIVE_ORIGINAL_ROUTE',
                mode='ORIGINAL_ROUTE_REFERENCE',independent_of_candidate=True,candidate_generated=False,
                original_source_evidence_ids=binding['reviewed_provenance']['authoritative_evidence_ids'],
                original_execution_events=[matrix['execution_event'],fresh['execution_event']])
            refpath=output.with_name(output.stem+'.original_reference.json')
            require(not refpath.exists(),'OUTPUT_EXISTS',str(refpath));refpath.write_text(json.dumps(raw,indent=2))
            result['first_original_reference']=dict(path=str(refpath),bytes=refpath.stat().st_size,sha256=file_sha(refpath))
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
