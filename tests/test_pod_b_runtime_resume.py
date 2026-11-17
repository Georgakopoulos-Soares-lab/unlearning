"""Mode/budget boundaries and snapshots of real CPU tensors; no native GPU import."""
import copy
import importlib.util
import datetime as dt
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from scripts.sayyed.pod_b_runtime.contracts import GateError,file_sha
from scripts.sayyed.pod_b_runtime.modes import reference_policy,ROUTE_KEYS
from scripts.sayyed.pod_b_runtime.budget import allowance,ENGINEERING,SCIENTIFIC


def identified():
    return dict(route_kind='R0_ORIGINAL',reviewed_provenance=dict(full_inference_state_complete=True,job_association_established=True,hidden_backbone_merge_or_extra_state_excluded=True,authoritative_evidence_ids=['controlled-test'],original_source_runtime_authenticated=True)),dict(identity_established=True,approved_binding_sha256='a'*64)


class ModeTests(unittest.TestCase):
    def test_engineering_requires_ineligibility(self):
        b,c=identified()
        with self.assertRaises(GateError):reference_policy(ENGINEERING,b,c)
        b.update(scientifically_qualified=False,downstream_eligible=False)
        self.assertEqual(reference_policy(ENGINEERING,b,c),'NOT_AVAILABLE_ENGINEERING')
    def test_authenticated_R0_creates_first_reference_without_existing_adapter_fixture(self):
        b,c=identified();self.assertEqual(reference_policy(SCIENTIFIC,b,c),'CREATE_FIRST_ORIGINAL_REFERENCE')
    def test_R0_candidate_not_automatically_original(self):
        b,c=identified();b['reviewed_provenance']['original_source_runtime_authenticated']=False
        with self.assertRaises(GateError):reference_policy(SCIENTIFIC,b,c)
    def test_R2_needs_independent_original(self):
        b,c=identified();b['route_kind']='R2_EQUIVALENT'
        with self.assertRaises(GateError):reference_policy(SCIENTIFIC,b,c)
    def test_unknown_job_identity_cannot_inherit_qualified_route(self):
        b,c=identified();b['qualified_route_receipt']={'path':'does-not-matter'};c['identity_established']=False
        with self.assertRaises(GateError) as e:reference_policy(SCIENTIFIC,b,c)
        self.assertEqual(e.exception.code,'IDENTITY_BLOCKED')
    def inheritance(self,mutate=None,binding_mutate=None):
        with tempfile.TemporaryDirectory() as tmp:
            b,c=identified();b.update({k:'a'*64 for k in ROUTE_KEYS});b['allowed_read_roots']=[tmp]
            receipt=dict(b,scientifically_qualified=True,mode=SCIENTIFIC,all_route_gates_passed=True)
            if mutate:mutate(receipt)
            p=Path(tmp)/'receipt.json';p.write_text(json.dumps(receipt));b['qualified_route_receipt']=dict(path=str(p),bytes=p.stat().st_size,sha256=file_sha(p))
            if binding_mutate:binding_mutate(b)
            return reference_policy(SCIENTIFIC,b,c)
    def test_additional_payload_can_inherit_applicable_qualified_route(self):
        self.assertEqual(self.inheritance(),'INHERITED_QUALIFIED_ROUTE')
    def test_engineering_receipt_never_promoted(self):
        with self.assertRaises(GateError):self.inheritance(lambda r:r.update(mode=ENGINEERING,scientifically_qualified=False))
    def test_parent_change_cannot_inherit(self):
        with self.assertRaises(GateError):self.inheritance(binding_mutate=lambda b:b.update(parent_fingerprint='b'*64))
    def test_incomplete_route_cannot_inherit(self):
        with self.assertRaises(GateError):self.inheritance(lambda r:r.update(all_route_gates_passed=False))


class BudgetTests(unittest.TestCase):
    def state(self):return dict(active=None,used_seconds=100.,engineering_seconds=100.,limits=dict(forward_deadline_utc='2026-11-17T18:11:46+00:00'))
    def test_engineering_ceiling_is_part_of_aggregate(self):
        s=self.state();s['engineering_seconds']=1780
        self.assertEqual(allowance(s,ENGINEERING,now=0),20.)
    def test_history_is_never_zeroed(self):
        s=self.state();s['used_seconds']=8995
        self.assertEqual(allowance(s,SCIENTIFIC,now=0,reserve_reason='specific repair'),5.)
        self.assertEqual(s['used_seconds'],8995)
    def test_reserve_requires_concrete_reason(self):
        s=self.state();s['used_seconds']=7205
        self.assertEqual(allowance(s,SCIENTIFIC,now=0),0.)
        self.assertGreater(allowance(s,SCIENTIFIC,now=0,reserve_reason='observed cleanup failure'),0.)
    def test_fresh_window_deadline_remains_fixed(self):
        s=self.state();deadline=dt.datetime.fromisoformat(s['limits']['forward_deadline_utc']).timestamp()
        self.assertEqual(allowance(s,ENGINEERING,now=deadline-20),20.)
        self.assertEqual(allowance(s,ENGINEERING,now=deadline+1),0.)
    def test_unreconciled_owner_blocks_retry(self):
        s=self.state();s['active']={'worker_pid':123}
        with self.assertRaises(GateError):allowance(s,ENGINEERING,now=0)


class OwnedControllerTests(unittest.TestCase):
    def test_failed_spawn_charges_and_clears_only_own_new_ledger(self):
        from scripts.sayyed.pod_b_runtime.budget import run_budgeted
        from tests.test_pod_b_runtime_unblock import ExecutionFixture
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture=ExecutionFixture(root,used=7.,engineering=7.);ledger=fixture.ledger
            with fixture.live(),patch('scripts.sayyed.pod_b_runtime.budget.fcntl.flock'),patch('scripts.sayyed.pod_b_runtime.budget.subprocess.Popen',side_effect=OSError('controlled spawn failure')):
                with self.assertRaises(OSError):run_budgeted(['unused'],ledger=ledger,mode=ENGINEERING,log=root/'log',label='CPU-test',env=dict(os.environ),execution_plan=fixture.plan)
            final=json.loads(ledger.read_text());self.assertIsNone(final['active']);self.assertGreater(final['used_seconds'],7.)
            self.assertEqual(final['stages'][-1]['status'],'FAILED_TO_START')
    def test_timeout_stops_owned_process_and_accounts_cleanup(self):
        from scripts.sayyed.pod_b_runtime.budget import run_budgeted
        from tests.test_pod_b_runtime_unblock import ExecutionFixture
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);fixture=ExecutionFixture(root,used=0.,engineering=0.);ledger=fixture.ledger
            with fixture.live(),patch('scripts.sayyed.pod_b_runtime.budget.fcntl.flock'),patch('scripts.sayyed.pod_b_runtime.budget.allowance',return_value=30.01),patch('scripts.sayyed.pod_b_runtime.budget.subprocess.Popen') as popen:
                fake=popen.return_value;fake.pid=99999999;fake.wait.side_effect=[__import__('subprocess').TimeoutExpired('owned',.01),0];fake.poll.return_value=None
                with patch('scripts.sayyed.pod_b_runtime.budget.os.killpg') as kill:
                    result=run_budgeted(['controlled'],ledger=ledger,mode=ENGINEERING,log=root/'log',label='CPU-timeout-test',env=dict(os.environ),execution_plan=fixture.plan)
                    self.assertEqual(result['status'],'TIMEOUT');self.assertTrue(kill.called)
            final=json.loads(ledger.read_text());self.assertIsNone(final['active']);self.assertGreater(final['used_seconds'],0.)
            self.assertEqual(final['used_seconds'],final['engineering_seconds'])


class FinalizationBoundaryTests(unittest.TestCase):
    def test_missing_gate_cannot_finalize_even_if_summary_claims_pass(self):
        from scripts.sayyed.pod_b_runtime.finalize import join_receipts
        result=dict(mode=ENGINEERING,checkpoint_id='controlled',cache_key='k',all_observed_gates_passed=True,phase='matrix',gates={})
        fresh=dict(result,phase='fresh')
        with self.assertRaises(GateError):join_receipts(dict(mode=ENGINEERING),dict(checkpoint_id='controlled'),'NOT_AVAILABLE_ENGINEERING','k',result,fresh,[])
    def test_phase_copy_cannot_substitute_for_fresh(self):
        from scripts.sayyed.pod_b_runtime.finalize import join_receipts
        result=dict(mode=ENGINEERING,checkpoint_id='controlled',cache_key='k',all_observed_gates_passed=True,phase='matrix',gates={})
        with self.assertRaises(GateError) as caught:join_receipts(dict(mode=ENGINEERING),dict(checkpoint_id='controlled'),'NOT_AVAILABLE_ENGINEERING','k',result,result,[])
        self.assertEqual(caught.exception.code,'FRESH_PROCESS')


class ActualTensorSnapshotTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec('torch') is not None,'Torch unavailable for real CPU tensor snapshots')
    def test_fingerprint_observes_parameter_persistent_and_nonpersistent_buffers(self):
        import torch
        from scripts.sayyed.pod_b_runtime.native import NativeBackend
        with tempfile.TemporaryDirectory() as tmp:
            backend=NativeBackend(Path(tmp));backend.model=torch.nn.Linear(3,2)
            backend.model.register_buffer('persistent',torch.tensor(3.))
            backend.model.register_buffer('transient',torch.tensor([4.]),persistent=False)
            before=backend.parent_snapshot()
            with torch.no_grad():backend.model.weight[0,0]+=1
            after=backend.parent_snapshot();self.assertNotEqual(before['parent_fingerprint'],after['parent_fingerprint'])
            with torch.no_grad():backend.model.transient[0]+=1
            self.assertNotEqual(after['parent_fingerprint'],backend.parent_snapshot()['parent_fingerprint'])
            self.assertIn('nonpersistent:transient',[r['key'] for r in before['parent_tensors']])
            self.assertIn('persistent',[r['key'] for r in before['parent_tensors']])

if __name__=='__main__':unittest.main()
