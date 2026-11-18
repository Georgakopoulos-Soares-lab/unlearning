import unittest,tempfile,json,hashlib,csv,copy,sys,fcntl
from pathlib import Path
import numpy as np
from plan_contract import *
from review_loop import validate_package,safe_path,publish_boundary,STAGES,ORIGIN
P=Path(__file__).resolve().parent.parent/'publication'
class ScientificContracts(unittest.TestCase):
 def setUp(self):
  self.row={'ids':np.array(['a','b']),'labels':np.array([0,1]),'groups':np.array(['g1','g2']),'classes':np.array([0,1])}
 def test_order_rejected(self):
  r=copy.deepcopy(self.row);r['ids']=r['ids'][::-1]
  with self.assertRaises(ValueError):paired_rows(self.row,r)
 def test_label_mismatch(self):
  r=copy.deepcopy(self.row);r['labels']=r['labels'][::-1]
  with self.assertRaises(ValueError):paired_rows(self.row,r)
 def test_class_column_inversion(self):
  with self.assertRaises(ValueError):probabilities(np.array([[.2,.8]]),[1,0],[0,1])
 def test_duplicate_identity(self):
  r=copy.deepcopy(self.row);r['ids']=np.array(['a','a'])
  with self.assertRaises(ValueError):paired_rows(r,r)
 def test_paired_draws(self):
  a=np.array([1.,4.,7.]);b=np.array([0.,2.,5.]);draws=np.array([[0,0,1],[1,2,2]])
  np.testing.assert_allclose(paired_draw_difference(a,b,draws),[4/3,2],rtol=0,atol=1e-15)
 def test_filler_exclusion_actual_ratio(self):self.assertEqual(lm_corpus([2,6,9999],[1,3,1],[True,True,False]),2)
 def test_H3_dependency_order(self):
  self.assertEqual(next_gate('R4',{'R4/H3_EXTRACTION'}),'R4/H3_78_REFITS');self.assertEqual(next_gate('R6',{'R4/H3_SEALED'}),'R6/H3_EXTRACTION')
 def test_bridge_not_blanket_block(self):self.assertTrue(eligible_contrast('R4','base'));self.assertTrue(eligible_contrast('R6','R1'));self.assertFalse(eligible_contrast('R4','R3'))
 def test_missing_adjacent_endpoint(self):self.assertFalse(eligible_contrast('R3','R2'));self.assertFalse(eligible_contrast('R6','R5'))
 def test_historical_write_rejected(self):
  with self.assertRaises(ValueError):output_path('/workspace/old/receipt.json','/workspace/new')
 def test_full_grid_arithmetic(self):
  plan=json.loads((P/'COVERAGE_PLAN.json').read_text());rows=list(csv.DictReader((P/'COVERAGE.csv').read_text().splitlines()));self.assertEqual(validate_plan(plan,rows)['full_heads'],3276)
 def test_shrunk_grid_rejected(self):
  plan=json.loads((P/'COVERAGE_PLAN.json').read_text());rows=list(csv.DictReader((P/'COVERAGE.csv').read_text().splitlines()))[1:]
  with self.assertRaises(ValueError):validate_plan(plan,rows)
 def test_all_five_adjacent_edges(self):
  rows=json.loads((P/'CONTRAST_PLAN.json').read_text())['contrasts'];self.assertEqual({r['contrast_id'] for r in rows if r['adjacent']},{f'R{i}_minus_R{i-1}' for i in range(2,7)})
class ObserverDraftBoundary(unittest.TestCase):
 def fixture(self):
  stages={f'A{i:02d}':f'A{i:02d}_x.md' for i in range(1,10)}
  tree={'STAGE_MAP.json':json.dumps({'stages':[{'id':k,'file':v} for k,v in stages.items()]}).encode(),**{v:b'fixture' for v in stages.values()}}
  tree['PACKAGE_FILES.json']=json.dumps({'files':['PACKAGE_FILES.json',*tree]}).encode();tree['SHA256SUMS']=''.join(hashlib.sha256(v).hexdigest()+'  '+k+'\n' for k,v in tree.items()).encode();return tree
 def test_valid_package(self):
  tree=self.fixture();self.assertEqual(len(validate_package(tree.__getitem__,lambda p:'100644')),11)
 def test_corrupt_checksum(self):
  tree=self.fixture();tree['A06_x.md']=b'changed'
  with self.assertRaises(ValueError):validate_package(tree.__getitem__,lambda p:'100644')
 def test_duplicate_checksum(self):
  tree=self.fixture();tree['SHA256SUMS']+=tree['SHA256SUMS'].splitlines(keepends=True)[0]
  with self.assertRaises(ValueError):validate_package(tree.__getitem__,lambda p:'100644')
 def test_symlink_mode(self):
  tree=self.fixture()
  with self.assertRaises(ValueError):validate_package(tree.__getitem__,lambda p:'120000')
 def test_traversal(self):
  for path in ['../secret','/abs','a/../b','a\\b']:
   with self.assertRaises(ValueError):safe_path(path)
 def test_locked_contract_proposed_only(self):
  stage='A06_EXTRACTION_H3_GATE.md'
  with self.assertRaises(ValueError):publish_boundary([stage,'SHA256SUMS','POD_A_MASTER.md'],'A05',stage,'a','a')
 def test_remote_advance(self):
  stage='A06_EXTRACTION_H3_GATE.md'
  with self.assertRaises(ValueError):publish_boundary([stage,'SHA256SUMS'],'A05',stage,'a','b')
 def test_active_stage_cannot_publish(self):
  stage='A05_PROTOCOL_COVERAGE_FREEZE.md'
  with self.assertRaises(ValueError):publish_boundary([stage,'SHA256SUMS'],stage,stage,'a','a')
 def test_atomic_checksum_required(self):
  stage='A06_EXTRACTION_H3_GATE.md'
  with self.assertRaises(ValueError):publish_boundary([stage],'A05',stage,'a','a')
 def test_no_git_approval_dispatch(self):
  text=Path(__file__).with_name('review_loop.py').read_text();self.assertNotIn("g('push'",text);self.assertNotIn('codex exec',text);self.assertIn("'science_execution':False",text)
 def test_lock_coalesces(self):
  with tempfile.TemporaryDirectory() as td:
   with open(Path(td)/'lock','a') as a,open(Path(td)/'lock','a') as b:
    fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaises(BlockingIOError):fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
if __name__=='__main__':unittest.main()
