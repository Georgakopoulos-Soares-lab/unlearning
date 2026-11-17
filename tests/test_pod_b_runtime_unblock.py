"""Disposable CPU boundary tests; no synthetic fixture may qualify science."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack,redirect_stdout
from unittest.mock import patch
import numpy as np
from scripts.sayyed.pod_b_runtime import approval as a,contracts as c,modes as m,budget as b,qualification as q,finalize as f


class ExecutionFixture:
    def __init__(self,root,mode=b.ENGINEERING,used=7.,engineering=7.):
        self.root=Path(root);self.mode=mode;self.rows=[dict(id='controlled_'+str(i),sequence='ACGT',split='train')for i in range(12)]
        self.path=self.root/'plan.json';self.control=self.root/'control.json';self.approval=self.root/'approval.json';self.ledger=self.root/'GPU_LEDGER.json'
        self.fixture=self.root/'fixture.jsonl';self.fixture.write_text(''.join(json.dumps(x)+'\n'for x in self.rows))
        self.inputs=dict(fixture_path=str(self.fixture),fixture_sha256=c.file_sha(self.fixture),ordered_ids_sha256=c.canonical_sha([r['id']for r in self.rows]),rows=12)
        state=dict(schema='CPU_TEST_ONLY',used_seconds=used,engineering_seconds=engineering,prior_B04_seconds=0,active=None,
                   limits=dict(artifact_root=str(self.root),forward_deadline_utc='2026-11-17T18:11:46+00:00'),stages=[])
        if engineering:state['stages'].append(dict(mode=b.ENGINEERING,occupied_seconds=engineering,status='EXITED'))
        if used>engineering:state['stages'].append(dict(mode=b.SCIENTIFIC,occupied_seconds=used-engineering,status='EXITED'))
        self.ledger.write_text(json.dumps(state));identity=a.ledger_identity(self.ledger,state)
        modules={name:self.record((Path(a.__file__).parent if '.pod_b_runtime.' in name else Path(a.__file__).parent.parent)/(name.rsplit('.',1)[-1]+'.py'))for name in a.RUNNER_MODULES}
        self.manifest=self.root/'runner.json';self.manifest.write_text(json.dumps(dict(modules=modules,runtime_modules={},allowed_source_roots=[str(Path(a.__file__).resolve().parents[4]),str(self.root)])))
        env=self.make('environment.json',dict(test_only=True))
        self.plan=dict(stage='B04',execution_id='CPU_CONTROLLED_EXECUTION',mode=mode,artifact_root=str(self.root),control_state_path=str(self.control),ledger_path=str(self.ledger),ledger_identity=identity,approved_prompt_sha256='1'*64,next_stage_authorized=False,forward_deadline_utc='2026-11-17T18:11:46+00:00',closure_deadline_utc='2026-11-17T18:56:46+00:00',inputs=self.inputs,runner_manifest=self.record(self.manifest),environment_lock=env,environment_lock_sha256=env['sha256'],runtime_prefix=sys.prefix,runner_root=str(Path(a.__file__).resolve().parents[3]),allowed_read_roots=[str(self.root),str(Path(a.__file__).resolve().parents[4])],reserve=None,route_id='b'*64,cases=[])
        self.ap=dict(stage='B04',execution_id=self.plan['execution_id'],approved_prompt_sha256=self.plan['approved_prompt_sha256'],artifact_root=str(self.root),ledger_path=str(self.ledger),ledger_identity=identity,minimum_used_seconds=used,minimum_engineering_seconds=engineering,inherited_stage_count=len(state['stages']),inherited_stages_sha256=c.canonical_sha(state['stages']),forward_deadline_utc=self.plan['forward_deadline_utc'],closure_deadline_utc=self.plan['closure_deadline_utc'],permitted_modes=[mode],direct_user_approval='DISPOSABLE CPU TEST APPROVAL; no real job evidence')
        self.ctrl=dict(stage='B04',status='RUNNING',execution_id=self.plan['execution_id'],approved_prompt_sha256=self.plan['approved_prompt_sha256'],execution_plan_path=str(self.path),artifact_root=str(self.root),ledger_path=str(self.ledger),ledger_identity=identity,permitted_modes=[mode],forward_deadline_utc=self.plan['forward_deadline_utc'],closure_deadline_utc=self.plan['closure_deadline_utc'])
        self.shared=self.root/'shared-budget.json';self.shared.write_text('{"active_since":null}')
        self.create_binding();self.pin()
    def record(self,p):return dict(path=str(p),bytes=p.stat().st_size,sha256=c.file_sha(p))
    def make(self,name,value):
        p=self.root/name;p.write_text(value if isinstance(value,str)else json.dumps(value));return self.record(p)
    def create_binding(self):
        ar=self.root/'adapter';ar.mkdir();self.adapter=self.make('adapter/__0_0.distcp','CPU synthetic adapter')
        cfg=self.make('config.json',{'CPU_only':True});token=self.make('tokenizer.json',{'CPU_only':True});resolved={'test_only':True}
        parent_records=[dict(key='decoder.final_norm.weight',shape=[1920],dtype='torch.bfloat16',sha256='a'*64,finite=True)]
        schema=json.loads((Path(__file__).resolve().parents[1]/'docs/experiments/ashay/POD_B/ADAPTER_TENSOR_SCHEMA.json').read_text())['model_tensors']
        self.contract=dict(layers=list(c.LAYERS),feature_width=1920,physical_batch_size=8,sequence_length=1000,vocab_size=256,tokenization='historical_char_no_special',nucleotide_ids=dict(A=65,C=67,G=71,T=84,N=78),pad_id=1,atol=c.ATOL,rtol=c.RTOL)
        self.binding=dict(checkpoint_id='controlled',job_id='CPU_UNIT_JOB',family='controlled',mode=self.mode,scientifically_qualified=False,downstream_eligible=False,route_kind='R2_EQUIVALENT',adapter_root=str(ar),parent_root=str(self.root/'parent'),parent_fingerprint=c.canonical_sha(parent_records),adapter_sha256=self.adapter['sha256'],config_sha256=cfg['sha256'],resolved_inference_config=resolved,resolved_inference_config_sha256=c.canonical_sha(resolved),tokenizer_sha256=token['sha256'],output_head_fingerprint=c.canonical_sha(parent_records),extraction_contract=self.contract,route_id=self.plan['route_id'],environment_lock_sha256=self.plan['environment_lock_sha256'],peft_semantics_sha256='e'*64,input_files=[self.adapter,cfg,token],source_files=list(json.loads(self.manifest.read_text())['modules'].values()),allowed_read_roots=self.plan['allowed_read_roots'],parent_tensor_specs={r['key']:{k:v for k,v in r.items()if k not in('key','finite')}for r in parent_records},adapter_tensor_specs={k:dict(**v,sha256='c'*64)for k,v in schema.items()},reviewed_provenance=dict(full_inference_state_complete=True,job_association_established=True,hidden_backbone_merge_or_extra_state_excluded=True,original_source_runtime_authenticated=True,authoritative_evidence_ids=['unit_statement']),**m.fixture_identity(self.inputs,self.rows))
        self.binding['full_state_fingerprint']=m.state_fingerprint(self.binding)
        statement=self.make('producer.json',dict(authoritative=True,issuer='CPU TEST ONLY',statement_utc='2026-11-17T00:00:00Z',job_ids=['CPU_UNIT_JOB'],bound_full_state_fingerprints=[self.binding['full_state_fingerprint']]))
        self.binding['evidence_records']=[dict(evidence_id='unit_statement',file=statement)]
        self.case=dict(checkpoint_id='controlled',identity_established=True,approved_binding_sha256=None)
        self.binding_path=self.root/'binding.json';self.plan['cases']=[self.case]
        if self.mode==b.SCIENTIFIC:self.plan['synthetic_contract_test']=True
    def original_reference(self):
        output=self.output();arrays=self.root/'reference.npz'
        np.savez_compressed(arrays,**{k:v for k,v in output.items()if isinstance(v,np.ndarray)},**{'feature__'+k:v for k,v in output['features'].items()})
        expected={k:self.binding[k]for k in m.STATE_KEYS};expected.update(full_state_fingerprint=self.binding['full_state_fingerprint'],extraction_contract=self.contract,**m.fixture_identity(self.inputs,self.rows))
        meta={k:v for k,v in output.items()if k!='features' and not isinstance(v,np.ndarray)}
        meta.update(expected,arrays_file=self.record(arrays),provenance_kind='AUTHORITATIVE_ORIGINAL_ROUTE',independent_of_candidate=True,candidate_generated=False,original_source_evidence_ids=['unit_statement'],mode='ORIGINAL_ROUTE_REFERENCE')
        p=self.root/'reference.json';p.write_text(json.dumps(meta));ref=dict(**self.record(p),**expected,provenance_kind='AUTHORITATIVE_ORIGINAL_ROUTE',same_full_state=True,independent_of_candidate=True,original_source_evidence_ids=['unit_statement'],arrays_file=self.record(arrays))
        self.binding['reference']=ref;self.case['original_reference_sha256']=ref['sha256'];self.pin()
    def output(self):
        n=12;tokens=np.ones((n,1000),dtype=np.int64);tokens[:,:4]=[65,67,71,84];positions=np.tile(np.arange(1000,dtype=np.int64),(n,1));mask=positions[:,1:]<4
        return dict(ids=[r['id']for r in self.rows],sequence_sha256=m.fixture_identity(self.inputs,self.rows)['sequence_sha256'],physical_batch_size=8,logical_batch_size=8,filler_ids=[],hook_calls={k:2 for k in c.LAYERS},features={k:np.zeros((n,1920),np.float32)for k in c.LAYERS},tokens=tokens,positions=positions,target_mask=mask,n_tokens=mask.sum(1),nll_sum=np.full(n,3*np.log(256),np.float32),logits=np.zeros((n,1000,256),np.float32),mode=self.mode)
    def pin(self):
        self.binding_path.write_text(json.dumps(self.binding));self.case['binding_file']=self.record(self.binding_path);self.case['approved_binding_sha256']=c.file_sha(self.binding_path)
        self.path.write_text(json.dumps(self.plan));digest=c.canonical_sha(self.plan);self.ap['execution_plan_sha256']=digest;self.approval.write_text(json.dumps(self.ap));self.ctrl.update(execution_plan_sha256=digest,approval_record=self.record(self.approval));self.control.write_text(json.dumps(self.ctrl))
    def live(self):
        stack=ExitStack();stack.enter_context(patch.object(b,'SHARED_LEDGER_PATH',self.shared));stack.enter_context(patch.object(b,'SHARED_LOCK_ROOT',self.root));stack.enter_context(patch.object(a,'CURRENT_CONTROL_PATH',self.control));stack.enter_context(patch.object(a,'APPROVED_FIXTURE_SHA',self.inputs['fixture_sha256']));stack.enter_context(patch.object(a,'APPROVED_IDS_SHA',self.inputs['ordered_ids_sha256']));return stack


class LiveApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.x=ExecutionFixture(Path(self.tmp.name))
    def check(self):
        with self.x.live():return a.validate_live(self.x.plan)
    def test_live_specific_plan_validates_without_native_import(self):
        self.assertEqual(self.check()['plan_sha256'],c.canonical_sha(self.x.plan))
    def test_closed_waiting_and_wrong_stage_reject_before_launch(self):
        for status,stage in [('CLOSED','B04'),('WAITING_FOR_STEERING: B04','B04'),('RUNNING','B05')]:
            with self.subTest(status=status,stage=stage):
                self.x.ctrl.update(status=status,stage=stage);self.x.control.write_text(json.dumps(self.x.ctrl))
                with self.x.live(),patch.object(q,'run_budgeted')as launch:
                    with self.assertRaises(c.GateError)as caught:q.main(['run','--plan',str(self.x.path),'--case','controlled','--output',str(self.x.root/'engineering/x')])
                    self.assertEqual(caught.exception.code,'STAGE_NOT_AUTHORIZED');launch.assert_not_called()
    def test_reset_request_is_not_permitted_even_in_a_repinned_plan(self):
        self.x.plan['reset_counters']=True;self.x.pin()
        with self.assertRaises(c.GateError)as caught:self.check()
        self.assertEqual(caught.exception.code,'BUDGET_RESET')
    def test_claimed_origin_cannot_replace_an_already_imported_module(self):
        from scripts.sayyed.pod_b_runtime import native
        manifest=json.loads(self.x.manifest.read_text());copy_path=self.x.root/'copied_native.py';copy_path.write_bytes(Path(native.__file__).read_bytes())
        manifest['modules']['scripts.sayyed.pod_b_runtime.native']=self.x.record(copy_path);self.x.manifest.write_text(json.dumps(manifest));self.x.plan['runner_manifest']=self.x.record(self.x.manifest);self.x.pin()
        with self.assertRaises(c.GateError)as caught:a.verify_runner(self.x.plan)
        self.assertEqual(caught.exception.code,'MODULE_ORIGIN')
    def test_changed_disk_plan_rejected(self):
        self.x.plan['note']='changed';self.x.path.write_text(json.dumps(self.x.plan))
        with self.assertRaises(c.GateError)as caught:self.check()
        self.assertEqual(caught.exception.code,'PLAN_CHANGED')
    def test_stale_execution_rejected(self):
        self.x.ctrl['execution_id']='stale';self.x.control.write_text(json.dumps(self.x.ctrl))
        with self.assertRaises(c.GateError):self.check()
    def test_changed_approval_record_rejected(self):
        self.x.approval.write_text(self.x.approval.read_text()+' ')
        with self.assertRaises(c.GateError)as caught:self.check()
        self.assertEqual(caught.exception.code,'INPUT_BYTES')
    def test_counter_reset_rejected(self):
        st=json.loads(self.x.ledger.read_text());st['used_seconds']=0;self.x.ledger.write_text(json.dumps(st))
        with self.assertRaises(c.GateError)as caught:self.check()
        self.assertEqual(caught.exception.code,'BUDGET_RESET')
    def test_fixed_deadline_not_reset(self):
        with self.x.live(),self.assertRaises(c.GateError)as caught:a.validate_live(self.x.plan,now=__import__('datetime').datetime.fromisoformat(self.x.plan['forward_deadline_utc']).timestamp()+1)
        self.assertEqual(caught.exception.code,'WALL_DEADLINE')
    def test_imported_source_hash_and_origin_checked(self):
        manifest=json.loads(self.x.manifest.read_text());manifest['modules']['scripts.sayyed.pod_b_runtime.native']['sha256']='0'*64;self.x.manifest.write_text(json.dumps(manifest));self.x.plan['runner_manifest']=self.x.record(self.x.manifest);self.x.pin()
        with self.assertRaises(c.GateError)as caught:a.verify_runner(self.x.plan)
        self.assertEqual(caught.exception.code,'INPUT_HASH')
    def test_revocation_rechecked_by_worker_guard(self):
        event=dict(token='controlled',controller_pid=os.getppid(),worker_pid=os.getpid(),event_id='evt',execution_id=self.x.plan['execution_id'],plan_sha256=c.canonical_sha(self.x.plan),approval_sha256=self.x.ctrl['approval_record']['sha256'])
        state=json.loads(self.x.ledger.read_text());state['active']=event;self.x.ledger.write_text(json.dumps(state));env=dict(POD_B_LEASE_TOKEN='controlled',POD_B_LEDGER=str(self.x.ledger),POD_B_EXECUTION_PLAN=str(self.x.path),POD_B_CONTROL_STATE=str(self.x.control),POD_B_EXECUTION_EVENT='evt',POD_B_FORWARD_DEADLINE_EPOCH=str(time.time()+30))
        with self.x.live(),patch.dict(os.environ,env):
            self.assertEqual(b.worker_guard()['event_id'],'evt');self.x.ctrl['status']='WAITING_FOR_STEERING: B04';self.x.control.write_text(json.dumps(self.x.ctrl))
            with self.assertRaises(c.GateError)as caught:b.worker_guard()
            self.assertEqual(caught.exception.code,'STAGE_NOT_AUTHORIZED')


class ReferencePreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.x=ExecutionFixture(Path(self.tmp.name),b.SCIENTIFIC);self.x.original_reference()
    def preflight(self):return m.preflight(self.x.plan,'controlled')
    def mutate_meta(self,mutate):
        p=Path(self.x.binding['reference']['path']);meta=json.loads(p.read_text());mutate(meta);p.write_text(json.dumps(meta));self.x.binding['reference'].update(self.x.record(p));self.x.case['original_reference_sha256']=c.file_sha(p);self.x.pin()
    def test_complete_disposable_preflight_is_only_metadata(self):
        self.assertEqual(self.preflight()[2],'COMPARE_INDEPENDENT_ORIGINAL')
        with self.x.live(),self.assertRaises(c.GateError)as caught:a.validate_live(self.x.plan)
        self.assertEqual(caught.exception.code,'SYNTHETIC_NOT_SCIENCE')
    def test_outer_head_and_fixture_contradictions_rejected(self):
        for key in ['output_head_fingerprint','fixture_sha256','ordered_ids_sha256','resolved_inference_config_sha256','full_state_fingerprint']:
            old=self.x.binding['reference'][key];self.x.binding['reference'][key]='f'*64;self.x.pin()
            with self.subTest(key=key),self.assertRaises(c.GateError)as caught:self.preflight()
            self.assertEqual(caught.exception.code,'REFERENCE_STATE');self.x.binding['reference'][key]=old;self.x.pin()
    def test_metadata_head_contradiction_even_with_rehashed_reference_rejected(self):
        self.mutate_meta(lambda x:x.update(output_head_fingerprint='f'*64))
        with self.assertRaises(c.GateError)as caught:self.preflight()
        self.assertEqual(caught.exception.code,'REFERENCE_METADATA')
    def test_metadata_fixture_contradiction_rejected(self):
        self.mutate_meta(lambda x:x.update(fixture_sha256='f'*64))
        with self.assertRaises(c.GateError):self.preflight()
    def test_missing_required_identity_rejected(self):
        del self.x.binding['reference']['output_head_fingerprint'];self.x.pin()
        with self.assertRaises(c.GateError):self.preflight()
    def test_wrong_sequence_digest_rejected(self):
        self.mutate_meta(lambda x:x.update(sequence_sha256=['f'*64]*12))
        with self.assertRaises(c.GateError):self.preflight()
    def test_candidate_generated_reference_rejected(self):
        self.mutate_meta(lambda x:x.update(candidate_generated=True))
        with self.assertRaises(c.GateError)as caught:self.preflight()
        self.assertEqual(caught.exception.code,'REFERENCE_BLOCKED')
    def test_changed_arrays_rejected_before_native_import(self):
        p=Path(self.x.binding['reference']['arrays_file']['path']);p.write_bytes(p.read_bytes()+b'bad')
        with patch.object(q,'worker_guard')as native:
            with self.assertRaises(c.GateError):self.preflight()
            native.assert_not_called()
    def test_unattested_template_is_not_historical_evidence(self):
        proof=self.x.binding['evidence_records'][0]['file'];p=Path(proof['path']);v=json.loads(p.read_text());v['is_response_template']=True;p.write_text(json.dumps(v));proof.update(self.x.record(p));self.x.pin()
        with self.assertRaises(c.GateError)as caught:self.preflight()
        self.assertEqual(caught.exception.code,'AUTHORITATIVE_EVIDENCE')
    def test_R0_metadata_path_needs_proof_but_no_existing_reference(self):
        self.x.binding['route_kind']='R0_ORIGINAL';del self.x.binding['reference'];self.x.pin()
        self.assertEqual(self.preflight()[2],'CREATE_FIRST_ORIGINAL_REFERENCE')
    def test_changed_tensor_rejected_despite_echoed_parent_fingerprint(self):
        binding=self.x.binding
        snapshot=dict(parent_fingerprint=binding['parent_fingerprint'],output_head_fingerprint=binding['output_head_fingerprint'],adapter_sha256=binding['adapter_sha256'],parent_tensors=[dict(key=k,finite=True,**v)for k,v in binding['parent_tensor_specs'].items()],adapter_tensors=[dict(key=k,finite=True,**v)for k,v in binding['adapter_tensor_specs'].items()],model_training=False,grad_enabled=False,parameters_requiring_grad=0,dropout_training=False,optimizer_restored=False,training_recompute_active=False,adapter_enabled=True,hook_registrations=0)
        result=dict(contract=self.x.contract,resolved_inference_config=binding['resolved_inference_config'],actual_snapshot=snapshot)
        f.validate_loaded_result(binding,result)
        snapshot['parent_tensors'][0]['sha256']='f'*64
        with self.assertRaises(c.GateError)as caught:f.validate_loaded_result(binding,result)
        self.assertEqual(caught.exception.code,'TENSOR_CONTENT')
    def test_actual_runtime_contract_and_state_cannot_echo_binding(self):
        result=dict(contract=dict(self.x.contract,vocab_size=512))
        with self.assertRaises(c.GateError)as caught:f.validate_loaded_result(self.x.binding,result)
        self.assertEqual(caught.exception.code,'BOUND_CONTRACT')


class CLIReserveAndFinalizationTests(unittest.TestCase):
    def test_CLI_reason_reaches_controller_and_persists_without_counter_reset(self):
        with tempfile.TemporaryDirectory()as t:
            x=ExecutionFixture(Path(t),used=7300.,engineering=0.);reason='Complete the specifically recorded fresh-process repair'
            evidence=x.make('repair.json',{'observed_failure':'controlled CPU diagnostic only'})
            x.plan['reserve']=dict(reason=reason,purpose='repair',maximum_gpu_seconds=60,evidence_record=evidence);x.pin()
            with x.live(),patch('scripts.sayyed.pod_b_runtime.budget.fcntl.flock'),patch('scripts.sayyed.pod_b_runtime.budget.subprocess.Popen')as popen,redirect_stdout(io.StringIO()):
                child=popen.return_value;child.pid=99999999;child.wait.return_value=0;child.poll.return_value=0
                with patch('scripts.sayyed.pod_b_runtime.budget.os.killpg'):
                    q.main(['run','--plan',str(x.path),'--case','controlled','--output',str(x.root/'engineering/cli'),'--reserve-reason',reason])
            state=json.loads(x.ledger.read_text());controller=json.loads((x.root/'engineering/cli/CONTROLLER.json').read_text())
            self.assertEqual(state['stages'][-1]['reserve_reason'],reason);self.assertEqual(controller['reserve_reason'],reason);self.assertGreater(state['used_seconds'],7300.)
            self.assertIn('--reserve-reason',popen.call_args.args[0]);self.assertFalse(controller['scientifically_qualified'])
    def test_empty_or_unapproved_reserve_reason_rejected(self):
        with tempfile.TemporaryDirectory()as t:
            x=ExecutionFixture(Path(t))
            for reason in ['','   ','Unapproved completion of an arbitrary task']:
                with x.live(),patch.object(q,'run_budgeted')as launch,self.assertRaises(c.GateError):q.main(['run','--plan',str(x.path),'--case','controlled','--output',str(x.root/'engineering/no'),'--reserve-reason',reason])
                launch.assert_not_called()
    def test_scientific_finalization_cannot_accept_disposable_positive_metadata(self):
        with tempfile.TemporaryDirectory()as t:
            x=ExecutionFixture(Path(t),b.SCIENTIFIC);x.original_reference()
            with x.live(),self.assertRaises(c.GateError)as caught:f.finalize(x.plan,'controlled',x.root/'scientific/matrix',x.root/'scientific/fresh',x.root/'scientific/output.json')
            self.assertEqual(caught.exception.code,'SYNTHETIC_NOT_SCIENCE');self.assertFalse((x.root/'scientific/output.json').exists())
    def test_copied_matrix_rejected_by_full_finalizer(self):
        self.finalizer_rejection(copied=True,missing_gate=False,expected='FRESH_PROCESS')
    def test_missing_gate_rejected_by_full_finalizer(self):
        self.finalizer_rejection(copied=False,missing_gate=True,expected='NATIVE_GATES_FAILED')
    def test_wrong_case_rejected_by_full_finalizer(self):
        self.finalizer_rejection(copied=False,missing_gate=False,expected='CACHE_KEY',wrong_case=True)
    def finalizer_rejection(self,*,copied,missing_gate,expected,wrong_case=False):
        with tempfile.TemporaryDirectory()as t:
            x=ExecutionFixture(Path(t));events=[];dirs=[];source=json.loads(x.manifest.read_text())['modules']['scripts.sayyed.pod_b_runtime.native']
            for i,phase in enumerate(['matrix','fresh']):
                event=dict(event_id='e'+str(0 if copied else i),execution_id=x.plan['execution_id'],worker_pid=100+(0 if copied else i),controller_pid=99,plan_sha256=c.canonical_sha(x.plan),approval_sha256=x.ctrl['approval_record']['sha256'])
                result=dict(mode=b.ENGINEERING,checkpoint_id='wrong_case' if wrong_case else 'controlled',cache_key=m.preflight(x.plan,'controlled')[3],phase=phase,all_observed_gates_passed=True,gates={},execution_event=event,observed_worker_pid=event['worker_pid'],execution_origin=dict(kind='NATIVE_FROZEN_BACKEND',path=source['path'],sha256=source['sha256']),completed_model_batches=1)
                directory=x.root/'engineering'/phase;(directory/'worker').mkdir(parents=True);(directory/'worker/RESULT.json').write_text(json.dumps(result));(directory/'CONTROLLER.json').write_text(json.dumps(dict(**event,returncode=0,status='EXITED',label='controlled:'+phase)));dirs.append(directory)
                if not copied or not i:events.append(dict(**event,mode=b.ENGINEERING,status='EXITED',returncode=0,occupied_seconds=.1,label='controlled:'+phase))
            state=json.loads(x.ledger.read_text());state['stages']+=events;state['used_seconds']+=sum(e['occupied_seconds']for e in events);state['engineering_seconds']+=sum(e['occupied_seconds']for e in events);x.ledger.write_text(json.dumps(state))
            with self.assertRaises(c.GateError)as caught:f.finalize(x.plan,'controlled',dirs[0],dirs[1],x.root/'engineering/final.json')
            self.assertEqual(caught.exception.code,expected);self.assertFalse((x.root/'engineering/final.json').exists())


class ProducerUtilityTests(unittest.TestCase):
    def test_collector_is_read_only_and_does_not_import_native_code(self):
        from scripts.sayyed.pod_b_runtime.collect_provenance import collect
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);source=root/'source';source.mkdir();p=source/'config.json';p.write_text('{"observed":true}');before=c.file_sha(p)
            modules=set(sys.modules);result=collect(dict(files=[dict(label='configuration',path=str(p))],job_metadata={'job_id':'unknown'},producer_attestations=[]),root/'new-output')
            self.assertEqual(c.file_sha(p),before);self.assertEqual(result['producer_attestations'],[]);self.assertFalse(result['CUDA_or_native_imports'])
            self.assertFalse(any(n.startswith(('torch','transformer_engine','bionemo','megatron'))for n in set(sys.modules)-modules))
    def test_collector_rejects_existing_output_and_input_overlap(self):
        from scripts.sayyed.pod_b_runtime.collect_provenance import collect
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);p=root/'config.json';p.write_text('{}');request=dict(files=[dict(label='config',path=str(p))])
            with self.assertRaises(ValueError):collect(request,root)
            with self.assertRaises(ValueError):collect(request,root/'new-output')
    def test_collector_rejects_secret_material_without_echoing_it(self):
        from scripts.sayyed.pod_b_runtime.collect_provenance import collect
        with tempfile.TemporaryDirectory()as t:
            secret='github_pat_'+'x'*30
            with self.assertRaises(ValueError)as caught:collect(dict(producer_attestations=[secret]),Path(t)/'out')
            self.assertNotIn(secret,str(caught.exception))
    def test_recipe_rejects_unpinned_source_without_writes(self):
        from scripts.sayyed.pod_b_runtime.reproduce import build
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);p=root/'source';p.write_text('untrusted')
            args=SimpleNamespace(output=root/'new',official_lora=p,patch=p)
            with self.assertRaises(ValueError):build(args)
            self.assertFalse(args.output.exists())

if __name__=='__main__':unittest.main()
