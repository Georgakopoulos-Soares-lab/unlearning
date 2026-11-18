import argparse,copy,hashlib,json,tempfile,unittest,os
from pathlib import Path
import numpy as np
from production_contract import *
from run_extraction import preflight
class AdapterTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.rows=[]
  for i,s in enumerate(['ACGT','CCGTA']):
   rc=s.translate(str.maketrans('ACGTN','TGCAN'))[::-1];self.rows.append({'id':'row'+str(i),'task':'emp_H3','split':'train','label':i,'sequence':s,'sequence_sha256':hashlib.sha256(s.encode()).hexdigest(),'exact_rc_group':hashlib.sha256(min(s,rc).encode()).hexdigest()})
  self.arr=payload(self.rows,{k:np.ones((2,1920),np.float32) for k in LAYERS},np.array([1.,2.],np.float32),np.array([3,4],np.int64));self.path=self.root/'chunk_000000';self.q=self.root/'quarantine';self.identity={'candidate':'R4','order':'fixed'}
 def tearDown(self):self.tmp.cleanup()
 def test_valid_arrays(self):validate_arrays(self.arr,self.rows)
 def test_cross_split(self):
  rr=copy.deepcopy(self.rows);rr[1]['split']='test'
  with self.assertRaises(ValueError):validate_rows(rr,'emp_H3','train')
 def test_duplicate_id(self):
  rr=copy.deepcopy(self.rows);rr[1]['id']=rr[0]['id']
  with self.assertRaises(ValueError):validate_rows(rr,'emp_H3','train')
 def test_wrong_row_order(self):
  with self.assertRaises(ValueError):validate_arrays(self.arr,self.rows[::-1])
 def test_filler_leakage(self):
  arr=dict(self.arr);arr['ids']=np.array(['row0','FILLER'])
  with self.assertRaises(ValueError):validate_arrays(arr,self.rows)
 def test_hook_misindex(self):
  arr=dict(self.arr);arr['decoder_layer_26']=arr.pop('decoder_layer_16')
  with self.assertRaises((ValueError,KeyError)):validate_arrays(arr,self.rows)
 def test_wrong_target_count(self):
  arr=dict(self.arr);arr['n_tokens']=np.array([4,5])
  with self.assertRaises(ValueError):validate_arrays(arr,self.rows)
 def test_seal_reuse_once(self):
  seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q);before=sha(self.path/'COMPLETE.json');state,_=prepare_chunk(self.path,self.identity,self.rows,self.q);self.assertEqual(state,'REUSE');self.assertEqual(sha(self.path/'COMPLETE.json'),before)
  with self.assertRaises(ValueError):seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q)
 def test_before_rename_interruption(self):
  with self.assertRaises(InterruptedError):seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q,interrupt='before_rename')
  quarantine_temporaries(self.root,self.q);self.assertEqual(len(list(self.q.iterdir())),1);self.assertEqual(prepare_chunk(self.path,self.identity,self.rows,self.q)[0],'NEW');seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q)
 def test_after_rename_interruption(self):
  with self.assertRaises(InterruptedError):seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q,interrupt='after_rename')
  self.assertEqual(prepare_chunk(self.path,self.identity,self.rows,self.q)[0],'NEW');self.assertEqual(len(list(self.q.iterdir())),1);seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q)
 def test_corrupt_payload_rejected(self):
  seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q);p=self.path/'features_and_lm.npz';p.write_bytes(p.read_bytes()[:100])
  with self.assertRaises(ValueError):prepare_chunk(self.path,self.identity,self.rows,self.q)
 def test_wrong_candidate_reuse(self):
  seal_chunk(self.path,self.identity,self.rows,self.arr,{},self.q)
  with self.assertRaises(ValueError):prepare_chunk(self.path,{'candidate':'R6'},self.rows,self.q)
 def test_escape(self):
  with self.assertRaises(ValueError):owned(self.root/'../escaped',self.root)
 def test_symlink_escape(self):
  (self.root/'link').symlink_to('/tmp')
  with self.assertRaises(ValueError):owned(self.root/'link'/'owned',self.root)
 def test_foreign_lock(self):
  with UnitLock(self.root/'lock'):
   with self.assertRaises(BlockingIOError):
    with UnitLock(self.root/'lock'):pass
 def test_stale_process_identity(self):self.assertFalse(process_identity(os.getpid(),'NOT_MY_START'))
 def test_gate_blocks_other_five(self):
  with self.assertRaises(ValueError):require_gate('R4','gue_tf_0',self.root)
  require_gate('R4','emp_H3',self.root)
 def test_failed_gate_blocks(self):
  put(self.root/'H3_GATE_R4.json',{'candidate':'R4','status':'FAIL','backup_status':'PASS'})
  with self.assertRaises(ValueError):require_gate('R4','gue_tf_0',self.root)
 def args(self):return argparse.Namespace(control='/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A06-attempt-001',prompt_commit='WRONG',coverage_sha256='wrong',candidate='R4',mode='extraction',group='H3',output_root='/tmp',run_label='fixture')
 def test_wrong_pin_before_inference(self):
  with self.assertRaises(ValueError):preflight(self.args())
 def test_wrong_control_before_inference(self):
  args=self.args();args.control=str(self.root)
  with self.assertRaises(ValueError):preflight(args)
 def test_unsafe_run_label(self):
  args=self.args();args.run_label='../overwrite'
  with self.assertRaises(ValueError):preflight(args)
 def test_class_column_rejection(self):
  from plan_contract import probabilities
  with self.assertRaises(ValueError):probabilities(np.array([[.2,.8]]),np.array([1,0]),np.array([0,1]))
 def test_unsafe_archive_member(self):
  import tarfile
  member=tarfile.TarInfo('payload/../escape')
  with self.assertRaises(ValueError):safe_archive_members([member],'payload')
 def test_archive_symlink(self):
  import tarfile
  member=tarfile.TarInfo('payload/link');member.type=tarfile.SYMTYPE;member.linkname='/tmp'
  with self.assertRaises(ValueError):safe_archive_members([member],'payload')
 def test_wrong_branch_guard(self):
  import sys
  from unittest.mock import patch
  sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'stage_drivers'))
  import research_guard
  original=research_guard.git
  def wrong(*args,**kwargs):
   if args==('branch','--show-current'):return b'POD_B\n'
   return original(*args,**kwargs)
  with patch.object(research_guard,'git',side_effect=wrong):
   with self.assertRaises(AssertionError):research_guard.guard(allow_dirty=True)
if __name__=='__main__':unittest.main()
