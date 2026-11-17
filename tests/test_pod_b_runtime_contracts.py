"""Disposable CPU contract tests. No real model/backend or scientific outputs."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

import numpy as np

from scripts.sayyed.pod_b_runtime import contracts as c
from scripts.sayyed.pod_b_runtime import gate


def toy_contract():
    return {'layers': list(c.LAYERS), 'feature_width': 3, 'sequence_length': 5, 'vocab_size': 5,
            'tokenization': 'historical_char_no_special', 'nucleotide_ids': dict(A=1,C=2,G=3,T=4,N=0), 'pad_id': 0}


def toy_rows():
    return [{'id': 'synthetic_train_0', 'sequence': 'ACGT', 'split': 'train'},
            {'id': 'synthetic_train_1', 'sequence': 'AN', 'split': 'train'}]


def toy_output(value=1., *, logical=8, hooks=True):
    rows = toy_rows(); contract = toy_contract(); n = len(rows)
    tokens = np.array([[1,2,3,4,0], [1,0,0,0,0]], dtype=np.int64)
    mask = np.array([[1,1,1,0], [1,0,0,0]], dtype=np.bool_)
    counts = mask.sum(1).astype(np.int64)
    return {'ids': [r['id'] for r in rows], 'sequence_sha256': [hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows],
        'physical_batch_size': 8, 'logical_batch_size': logical, 'filler_ids': [],
        'hook_calls': {k: (n+logical-1)//logical for k in contract['layers']} if hooks else {},
        'features': {k: np.full((n,3), value, dtype=np.float32) for k in contract['layers']} if hooks else {},
        'tokens': tokens, 'positions': np.tile(np.arange(5,dtype=np.int64),(n,1)), 'target_mask': mask,
        'n_tokens': counts, 'nll_sum': (counts*np.log(5.)).astype(np.float32), 'logits': np.zeros((n,5,5),dtype=np.float32),
        'adapter_branch_calls': {'decoder.layers.0.mixer.dense': 1}}


def toy_binding(adapter='c'*64):
    keys = ['decoder.layers.0.mixer.dense.adapter.linear_in.weight', 'decoder.layers.0.mixer.dense.adapter.linear_out.weight']
    spec = {k: {'shape':[2,2], 'dtype':'torch.bfloat16', 'sha256':adapter} for k in keys}
    return {'checkpoint_id': 'synthetic_only', 'parent_fingerprint':'a'*64, 'output_head_fingerprint':'b'*64,
            'adapter_sha256':adapter, 'adapter_tensor_specs':spec, 'adapter_storage_files':['adapter.bin'],
            'parent_tensor_specs':{'buffer':{'shape':[1], 'dtype':'torch.float32','sha256':'d'*64}},
            'parent_storage_files':['parent.bin'], 'extraction_contract':toy_contract()}


def toy_snapshot(binding, generation=1):
    return {'parent_fingerprint':binding['parent_fingerprint'], 'output_head_fingerprint':binding['output_head_fingerprint'],
        'adapter_sha256':binding['adapter_sha256'], 'adapter_tensors':[dict(key=k,finite=True,**v) for k,v in binding['adapter_tensor_specs'].items()],
        'adapter_storage_files':['adapter.bin'], 'parent_tensors':[dict(key=k,finite=True,**v) for k,v in binding['parent_tensor_specs'].items()],
        'parent_storage_files':['parent.bin'], 'model_training':False, 'grad_enabled':False, 'optimizer_restored':False,
        'training_recompute_active':False, 'adapter_enabled':True, 'dropout_training':False,
        'transient_state_cleared':True, 'hook_registrations':0, 'load_generation':generation}


class Errors(unittest.TestCase):
    def rejects(self, code, function, *args, **kwargs):
        with self.assertRaises(c.GateError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)


class TensorRejectionTests(Errors):
    def setUp(self):
        self.binding=toy_binding();self.spec=self.binding['adapter_tensor_specs']
        self.records=toy_snapshot(self.binding)['adapter_tensors']
    def run_check(self, records, shards=None):
        return c.validate_tensor_records(self.spec,records,['adapter.bin'],['adapter.bin']if shards is None else shards)
    def test_known_records_are_valid_metadata(self):self.run_check(self.records)
    def test_missing_tensor(self):self.rejects('TENSOR_KEYS',self.run_check,self.records[:-1])
    def test_duplicate_mapping(self):self.rejects('DUPLICATE_MAPPING',self.run_check,self.records+[self.records[0]])
    def test_unexpected_key(self):
        a=copy.deepcopy(self.records);a[0]['key']='unreported.embedding.weight';self.rejects('TENSOR_KEYS',self.run_check,a)
    def test_shape(self):
        a=copy.deepcopy(self.records);a[0]['shape']=[1,4];self.rejects('TENSOR_SHAPE',self.run_check,a)
    def test_dtype(self):
        a=copy.deepcopy(self.records);a[0]['dtype']='torch.float32';self.rejects('TENSOR_DTYPE',self.run_check,a)
    def test_content(self):
        a=copy.deepcopy(self.records);a[0]['sha256']='e'*64;self.rejects('TENSOR_CONTENT',self.run_check,a)
    def test_nonfinite(self):
        a=copy.deepcopy(self.records);a[0]['finite']=False;self.rejects('NONFINITE_TENSOR',self.run_check,a)
    def test_incomplete_shards(self):self.rejects('SHARD_SET',self.run_check,self.records,[])
    def test_duplicate_shards(self):self.rejects('SHARD_SET',self.run_check,self.records,['adapter.bin','adapter.bin'])


class StateRejectionTests(Errors):
    def setUp(self):self.binding=toy_binding();self.snapshot=toy_snapshot(self.binding)
    def test_state(self):c.loaded_state(self.snapshot,self.binding)
    def test_wrong_parent(self):
        self.snapshot['parent_fingerprint']='e'*64;self.rejects('WRONG_PARENT',c.loaded_state,self.snapshot,self.binding)
    def test_changed_buffer_despite_claimed_same_parent(self):
        self.snapshot['parent_tensors'][0]['sha256']='e'*64;self.rejects('TENSOR_CONTENT',c.loaded_state,self.snapshot,self.binding)
    def test_stale_adapter(self):
        self.snapshot['adapter_sha256']='e'*64;self.rejects('STALE_ADAPTER',c.loaded_state,self.snapshot,self.binding)
    def test_no_parent_only_fallback(self):
        self.snapshot['adapter_enabled']=False;self.rejects('ADAPTER_DISABLED',c.loaded_state,self.snapshot,self.binding)
    def test_dropout_not_eval(self):
        self.snapshot['dropout_training']=True;self.rejects('ADAPTER_DISABLED',c.loaded_state,self.snapshot,self.binding)
    def test_grad_or_optimizer(self):
        for field in ['grad_enabled','optimizer_restored','model_training','training_recompute_active']:
            with self.subTest(field=field):
                s=copy.deepcopy(self.snapshot);s[field]=True;self.rejects('TRAINING_MODE',c.loaded_state,s,self.binding)
    def test_stale_hooks(self):
        self.snapshot['hook_registrations']=1;self.rejects('STALE_STATE',c.loaded_state,self.snapshot,self.binding)
    def test_uncleared_inference_state(self):
        self.snapshot['transient_state_cleared']=False;self.rejects('STALE_STATE',c.loaded_state,self.snapshot,self.binding)
    def test_generation_not_advanced(self):
        self.rejects('STALE_STATE',c.loaded_state,self.snapshot,self.binding,previous_generation=1)
    def test_branch_parameters_without_execution(self):
        out=toy_output();out['adapter_branch_calls']={};self.rejects('ADAPTER_NOT_EXECUTED',c.adapter_activity,out,self.binding)
    def test_zero_branch_calls(self):
        out=toy_output();out['adapter_branch_calls']={next(iter(out['adapter_branch_calls'])):0};self.rejects('ADAPTER_NOT_EXECUTED',c.adapter_activity,out,self.binding)


class OutputRejectionTests(Errors):
    def setUp(self):self.out=toy_output();self.rows=toy_rows();self.contract=toy_contract()
    def check(self,out):return c.validate_forward(out,self.rows,self.contract)
    def test_all26_and_independent_uniform_lm(self):
        records=c.compare_forward(self.out,copy.deepcopy(self.out),self.rows,self.contract)
        self.assertEqual(len(records),29);self.assertTrue(all(x['pass']for x in records))
    def test_one_bad_layer_not_hidden_by_average(self):
        other=copy.deepcopy(self.out);other['features']['decoder_layer_23'][1,2]+=1
        self.rejects('NUMERICAL_MISMATCH',c.compare_forward,other,self.out,self.rows,self.contract)
    def test_missing_layer(self):
        del self.out['features']['decoder_layer_12'];self.rejects('COORDINATES',self.check,self.out)
    def test_stale_duplicate_hooks(self):
        self.out['hook_calls']['final_norm']+=1;self.rejects('HOOK_COUNT',self.check,self.out)
    def test_nonfinite(self):
        self.out['features']['final_norm'][0,0]=np.nan;self.rejects('NONFINITE_OUTPUT',self.check,self.out)
    def test_feature_precision_changed(self):
        self.out['features']['final_norm']=self.out['features']['final_norm'].astype(np.float64);self.rejects('FEATURE_SCHEMA',self.check,self.out)
    def test_filler_id_cannot_escape(self):
        self.out['ids'].append('FILLER');self.rejects('OUTPUT_IDS',self.check,self.out)
    def test_extra_filler_arrays(self):
        self.out['n_tokens']=np.append(self.out['n_tokens'],0);self.rejects('OUTPUT_SCHEMA',self.check,self.out)
    def test_explicit_filler_markers(self):
        self.out['filler_ids']=['filler'];self.rejects('FILLER_OUTPUT',self.check,self.out)
    def test_reordered_rows(self):
        self.out['ids'].reverse();self.rejects('OUTPUT_IDS',self.check,self.out)
    def test_physical_batch_reduction(self):
        self.out['physical_batch_size']=1;self.rejects('FILLER_OUTPUT',self.check,self.out)
    def test_shifted_mask_even_with_same_count(self):
        self.out['target_mask'][1]=[0,1,0,0];self.rejects('TARGET_MASK',self.check,self.out)
    def test_count_mismatch(self):
        self.out['n_tokens'][0]+=1;self.rejects('TARGET_COUNT',self.check,self.out)
    def test_wrong_nucleotide_ids(self):
        self.out['tokens'][0,0]=4;self.rejects('TOKENIZATION',self.check,self.out)
    def test_position_ids(self):
        self.out['positions'][0,0]=1;self.rejects('POSITION_IDS',self.check,self.out)
    def test_dna_only_normalization_not_full_head(self):
        self.out['logits']=self.out['logits'][:,:,:4];self.rejects('OUTPUT_SCHEMA',self.check,self.out)
    def test_bad_lm_sum(self):
        self.out['nll_sum'][0]+=1;self.rejects('NUMERICAL_MISMATCH',c.compare_forward,self.out,copy.deepcopy(self.out),self.rows,self.contract)
    def test_zero_feature_delta_is_allowed(self):
        for key in self.out['features']:self.out['features'][key].fill(0)
        self.check(self.out)
    def test_relative_error_diagnostic_is_defined_at_zero(self):
        r=c.numeric_comparison(np.array([1.]),np.array([0.]),'zero')
        self.assertEqual(r['failing_elements'],1);self.assertEqual(r['max_error_index'],[0]);self.assertEqual(r['max_relative_error'],10000.)


class AlgebraTests(Errors):
    def example(self):
        x=[[.5,-.5],[2.,1.]];a=[[1.,2.],[-1.,1.]];b=[[2.,-1.],[1.,3.]]
        # Independent scalar oracle, no model constructor or native code import.
        branch=[]
        for xx in x:
            low=[sum(v*w for v,w in zip(xx,row))for row in a]
            branch.append([2*sum(v*w for v,w in zip(low,row))for row in b])
        branch=np.array(branch);base=np.array([[10.,20.],[30.,40.]]);bias=np.array([.3,-.7])
        return dict(normalized_input=x,linear_in=a,linear_out=b,rank=16,alpha=32,base_without_bias=base,bias=bias,
                    branch_output=branch,combined_with_bias=base+bias+branch,eval_mode=True,dropout_applied=False)
    def test_source_contract_attention_mlp_hyena(self):
        for family in ['attention','MLP','Hyena']:
            with self.subTest(family=family):c.validate_algebra_evidence(self.example())
    def test_wrong_scaling(self):
        e=self.example();e['branch_output']/=2;self.rejects('ADAPTER_ALGEBRA',c.validate_algebra_evidence,e)
    def test_bias_added_twice(self):
        e=self.example();e['combined_with_bias']+=e['bias'];self.rejects('ADAPTER_ALGEBRA',c.validate_algebra_evidence,e)
    def test_raw_instead_of_normalized_input(self):
        e=self.example();e['branch_output']+=10;self.rejects('ADAPTER_ALGEBRA',c.validate_algebra_evidence,e)
    def test_eval_dropout(self):
        e=self.example();e['dropout_applied']=True;self.rejects('ADAPTER_ALGEBRA',c.validate_algebra_evidence,e)
    def test_mathematically_zero_branch_is_allowed(self):
        e=self.example();e['linear_out']=np.zeros((2,2));e['branch_output']=np.zeros((2,2));e['combined_with_bias']=e['base_without_bias']+e['bias'];c.validate_algebra_evidence(e)


class DisposableBackend:
    def __init__(self, *, stale=False, changed_buffer=False):
        self.binding=None;self.generation=0;self.enabled=True;self.stale=stale;self.changed_buffer=changed_buffer;self.forwards=0
    def load(self,binding):self.binding=binding;self.generation+=1;self.enabled=True
    def snapshot(self):
        s=toy_snapshot(self.binding,self.generation)
        if self.stale and self.generation==2:s['adapter_tensors'][0]['sha256']='c'*64
        if self.changed_buffer and self.forwards:s['parent_tensors'][0]['sha256']='f'*64
        return s
    def forward(self,rows,*,logical_batch_size,hooks):
        self.forwards+=1
        value=0. if not self.enabled else(1. if self.binding['adapter_sha256']=='c'*64 else 2.)
        return toy_output(value,logical=logical_batch_size,hooks=hooks)
    def set_adapter_enabled(self,enabled):self.enabled=enabled
    def close(self):pass


class LifecycleTests(Errors):
    def test_matrix_controller_on_disposable_data_only(self):
        result,_=gate.qualify_matrix(DisposableBackend(),toy_binding(),toy_rows(),toy_output(),toy_output(0.),toy_binding('e'*64))
        self.assertEqual(result['status'],'PASS_MATRIX_PENDING_FRESH_PROCESS');self.assertFalse(result['full_route_qualification'])
        self.assertIn('A_B_A_swap_isolation',[r['gate']for r in result['gates']])
    def test_stale_adapter_values_during_swap(self):
        self.rejects('TENSOR_CONTENT',gate.qualify_matrix,DisposableBackend(stale=True),toy_binding(),toy_rows(),toy_output(),toy_output(0.),toy_binding('e'*64))
    def test_changed_non_adapter_buffer(self):
        self.rejects('TENSOR_CONTENT',gate.qualify_matrix,DisposableBackend(changed_buffer=True),toy_binding(),toy_rows(),toy_output(),toy_output(0.),toy_binding('e'*64))
    def test_cross_parent_swap(self):
        other=toy_binding('e'*64);other['parent_fingerprint']='f'*64
        self.rejects('SWAP_PARENT',gate.qualify_matrix,DisposableBackend(),toy_binding(),toy_rows(),toy_output(),toy_output(0.),other)
    def test_no_silent_omission_of_swap(self):
        self.rejects('SWAP_NOT_QUALIFIED',gate.qualify_matrix,DisposableBackend(),toy_binding(),toy_rows(),toy_output(),toy_output(0.))


class FileAndEntryTests(Errors):
    def test_corrupted_file(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'payload';p.write_bytes(b'old');r=dict(path=str(p),bytes=3,sha256=c.file_sha(p));p.write_bytes(b'bad')
            self.rejects('INPUT_HASH',c.verify_file,r)
    def test_provider_id_is_not_hash(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'x';p.write_bytes(b'x');self.rejects('HASH_FORMAT',c.verify_file,dict(path=str(p),bytes=1,sha256='drive-id'))
    def test_old_output_root(self):
        with tempfile.TemporaryDirectory()as t:self.rejects('OUTPUT_PATH',c.output_path,'/workspace/meeting-artifacts/relearning-benign-v1/new',[t])
    def test_relative_output(self):
        with tempfile.TemporaryDirectory()as t:self.rejects('OUTPUT_PATH',c.output_path,'relative',[t])
    def test_symlink_output_escape(self):
        with tempfile.TemporaryDirectory()as t, tempfile.TemporaryDirectory()as other:
            (Path(t)/'escape').symlink_to(other,target_is_directory=True);self.rejects('OUTPUT_PATH',c.output_path,Path(t)/'escape/new',[t])
    def test_non_training_fixture(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'rows.jsonl';rows=toy_rows();rows[0]['split']='dev';p.write_text(''.join(json.dumps(r)+'\n'for r in rows))
            self.rejects('NON_TRAINING_INPUT',c.fixture_rows,p,expected_sha=c.file_sha(p),expected_ordered_ids_sha=c.canonical_sha([r['id']for r in rows]),expected_rows=2)
    def test_reference_order_not_replaced(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'rows.jsonl';p.write_text(''.join(json.dumps(r)+'\n'for r in toy_rows()))
            self.rejects('FIXTURE_ORDER',c.fixture_rows,p,expected_sha=c.file_sha(p),expected_ordered_ids_sha='f'*64,expected_rows=2)
    def test_identity_block_before_backend_import(self):
        with tempfile.TemporaryDirectory()as t:
            root=Path(t);plan=root/'plan.json';marker=root/'IMPORTED';backend=root/'bad_backend.py'
            backend.write_text('from pathlib import Path\nPath('+repr(str(marker))+').touch()\n')
            plan.write_text(json.dumps({'representatives':[{'id':'blocked_case','identity_established':False}]}))
            captured=io.StringIO()
            with redirect_stdout(captured):status=gate.main(['preflight','--plan',str(plan),'--checkpoint-id','blocked_case','--binding',str(backend)])
            self.assertEqual(status,2);self.assertEqual(json.loads(captured.getvalue())['code'],'IDENTITY_BLOCKED');self.assertFalse(marker.exists())
    def test_future_stage_is_not_permission(self):
        self.rejects('STAGE_NOT_AUTHORIZED',gate.execution_authorized,{},dict(stage='B05',status='RUNNING'))
    def test_owned_timeout_stops_its_child(self):
        with tempfile.TemporaryDirectory()as t:
            p=Path(t)/'pid';command=[sys.executable,'-c','import os,time;from pathlib import Path;Path('+repr(str(p))+').write_text(str(os.getpid()));time.sleep(60)']
            with (Path(t)/'log').open('w')as log:self.rejects('WORKER_TIMEOUT',gate.run_owned_worker,command,log,.4,{})
            pid=int(p.read_text())
            with self.assertRaises(ProcessLookupError):os.kill(pid,0)


class BindingPreflightTests(Errors):
    """Synthetic pinned manifests exercise real preflight, without model construction."""
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        def record(name,content):
            p=self.root/name;p.write_text(content)
            return dict(path=str(p),bytes=p.stat().st_size,sha256=c.file_sha(p))
        parent=record('parent.bin','synthetic parent');adapter=record('adapter.bin','synthetic adapter')
        source=record('backend.py','raise RuntimeError("A synthetic metadata test must never import me")\n')
        evidence=record('proof.json','{"scope":"synthetic contract test, not actual job evidence"}')
        cfg=record('cfg.json','{"synthetic":true}');resolved=record('resolved.json','{"resolved":true}')
        tokenizer=record('tokenizer.json','{"test_only":true}');env=record('env.json','{"test_cpu_only":true}')
        head=record('head.json',json.dumps(dict(fingerprint='b'*64)))
        ref=record('reference.json','{"test_only":true}')
        rows=[dict(id='unit_'+str(i),sequence='ACGT',split='train')for i in range(12)]
        fixture=self.root/'fixture.jsonl';fixture.write_text(''.join(json.dumps(r)+'\n'for r in rows))
        # The actual pinned200-key shape schema is metadata, never allocated here.
        doc=Path(__file__).resolve().parents[1]/'docs/experiments/ashay/POD_B/ADAPTER_TENSOR_SCHEMA.json'
        schema=json.loads(doc.read_text())['model_tensors'];schema={k:dict(**v,sha256='c'*64)for k,v in schema.items()}
        contract=dict(layers=list(c.LAYERS),feature_width=1920,physical_batch_size=8,sequence_length=1000,vocab_size=512,
                      tokenization='historical_char_no_special',nucleotide_ids=dict(A=65,C=67,G=71,T=84,N=78),pad_id=1,atol=c.ATOL,rtol=c.RTOL)
        self.binding=dict(checkpoint_id='synthetic_case',family='base_all',job_id='synthetic_unit_job',route_kind='R2_EQUIVALENT',
            reviewed_provenance=dict(full_inference_state_complete=True,job_association_established=True,
                hidden_backbone_merge_or_extra_state_excluded=True,authoritative_evidence_ids=['SYNTHETIC_UNIT_ONLY']),
            source_files=[source],parent_files=[parent],adapter_files=[adapter],evidence_files=[evidence],allowed_read_roots=[str(self.root)],
            adapter_sha256=adapter['sha256'],config_sha256=cfg['sha256'],parent_fingerprint='a'*64,
            tokenizer_sha256=tokenizer['sha256'],output_head_fingerprint='b'*64,route_source_sha256=source['sha256'],
            resolved_inference_config_sha256=resolved['sha256'],environment_lock_sha256=env['sha256'],
            identity_files=dict(delivered_config=cfg,resolved_inference_config=resolved,tokenizer=tokenizer,environment_lock=env,output_head_manifest=head),
            backend_file=source,parent_tensor_specs={'buffer':dict(shape=[1],dtype='torch.float32',sha256='d'*64)},
            adapter_tensor_specs=schema,extraction_contract=contract)
        self.plan=dict(synthetic_contract_test=True,representatives=[dict(id='synthetic_case',family='base_all',job_id='synthetic_unit_job',
            adapter_sha256=adapter['sha256'],config_sha256=cfg['sha256'],backend_source_sha256=source['sha256'],identity_established=True,
            original_reference_sha256=ref['sha256'])],inputs=dict(fixture_path=str(fixture),fixture_sha256=c.file_sha(fixture),
            ordered_ids_sha256=c.canonical_sha([r['id']for r in rows]),rows=12))
        state={k:self.binding[k]for k in ['parent_fingerprint','adapter_sha256','config_sha256','tokenizer_sha256','output_head_fingerprint']}
        self.binding['reference']=dict(**ref,provenance_kind='AUTHORITATIVE_ORIGINAL_ROUTE',same_full_state=True,independent_of_candidate=True,
            original_source_evidence_ids=['SYNTHETIC_UNIT_ONLY'],full_state_fingerprint=c.canonical_sha(state),
            fixture_sha256=self.plan['inputs']['fixture_sha256'],ordered_ids_sha256=self.plan['inputs']['ordered_ids_sha256'])
        self.path=self.root/'binding.json';self.pin()
    def pin(self):
        self.path.write_text(json.dumps(self.binding));self.plan['representatives'][0]['approved_binding_sha256']=c.file_sha(self.path)
    def run_check(self):return c.binding_preflight(self.plan,'synthetic_case',self.path)
    def test_complete_pinned_metadata_is_not_scientific_qualification(self):
        binding,rows,key=self.run_check();self.assertEqual(len(rows),12);self.assertEqual(len(key),64)
        self.rejects('SYNTHETIC_NOT_SCIENCE',gate.execution_authorized,self.plan,dict(stage='B04',status='RUNNING'))
    def test_binding_hash_stale(self):
        self.path.write_text(self.path.read_text()+' ');self.rejects('BINDING_HASH',self.run_check)
    def test_route_hash_stale(self):
        self.plan['representatives'][0]['backend_source_sha256']='e'*64;self.rejects('ROUTE_HASH',self.run_check)
    def test_corrupted_parent_fails_before_backend(self):
        Path(self.binding['parent_files'][0]['path']).write_text('synthetic parenz');self.rejects('INPUT_HASH',self.run_check)
    def test_missing_parent_file(self):
        Path(self.binding['parent_files'][0]['path']).unlink();self.rejects('MISSING_INPUT',self.run_check)
    def test_no_backend_substitute(self):
        del self.binding['backend_file'];self.pin();self.rejects('NATIVE_BACKEND_MISSING',self.run_check)
    def test_parent_only_reference(self):
        self.binding['reference']['provenance_kind']='PARENT_ONLY';self.pin();self.rejects('REFERENCE_BLOCKED',self.run_check)
    def test_candidate_self_reference(self):
        self.binding['reference']['independent_of_candidate']=False;self.pin();self.rejects('REFERENCE_BLOCKED',self.run_check)
    def test_wrong_reference_full_state(self):
        self.binding['reference']['full_state_fingerprint']='e'*64;self.pin();self.rejects('REFERENCE_STATE',self.run_check)
    def test_head_tokenizer_vocabulary_cannot_be_resized(self):
        self.binding['extraction_contract']['vocab_size']=256;self.pin();self.rejects('EXTRACTION_CONTRACT',self.run_check)
    def test_token_id_remapping_cannot_make_load_pass(self):
        self.binding['extraction_contract']['nucleotide_ids']['A']=0;self.pin();self.rejects('TOKENIZATION_UNSUPPORTED',self.run_check)
    def test_noncanonical_tensor_names(self):
        specs=self.binding['adapter_tensor_specs'];k=next(iter(specs));specs['arbitrary_prefix.'+k]=specs.pop(k);self.pin();self.rejects('TENSOR_SCHEMA',self.run_check)


if __name__=='__main__':unittest.main()
