"""Synthetic correctness/adversarial tests; no real cohorts, GPU or dispatch."""
import unittest,tempfile,subprocess
from unittest.mock import patch
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from other_five_common import *
from producer_metrics import point_metrics,bootstrap_metrics,decisions
from independent_math import metrics,reconstruct
class ContractTests(unittest.TestCase):
 def compare(self,y,p,c,w):
  with np.errstate(divide='ignore',invalid='ignore'):
   a,va=bootstrap_metrics(y,p,c,w);b,vb=metrics(y,p,c,w)
  self.assertTrue(np.array_equal(va,vb))
  for m in METRICS:np.testing.assert_allclose(a[m],b[m],atol=1e-12,rtol=0,equal_nan=True)
  point,_=point_metrics(y,p,c);ind,v=metrics(y,p,c,np.ones((1,len(y))))
  for m in METRICS:self.assertLessEqual(abs(point[m]-ind[m][0]),1e-12)
 def test_binary_ties_and_absent_class_draw(self):
  y=np.array([0,1,0,1,0,1]);p=np.array([[.5,.5],[.5,.5],[.8,.2],[.2,.8],[1.,0.],[0.,1.]],dtype=np.float64);w=np.array([[1]*6,[2,0,1,0,1,0],[0,1,0,3,0,1],[2,3,1,4,2,1]]);self.compare(y,p,np.array([0,1]),w)
 def test_splice_tied_macro_and_absent_class(self):
  y=np.tile([0,1,2],4);p=np.array([[1/3]*3,[.2,.4,.4],[.2,.4,.4],[.7,.2,.1]]*3);w=np.array([[1]*12,[1,0,0]*4,[2,3,1]*4]);self.compare(y,p,np.array([0,1,2]),w)
 def test_probability_normalization_failure(self):
  with self.assertRaises(ValueError):validate_prob(np.ones((3,3)),np.array([0,1,2]),np.array([0,1,2]))
 def test_permuted_classes_rejected(self):
  with self.assertRaises(ValueError):validate_prob(np.full((3,3),1/3),np.array([0,1,2]),np.array([2,1,0]))
 def test_binary_threshold_tie(self):self.assertEqual(decisions(np.array([[.5,.5]]),np.array([0,1])).tolist(),[1])
 def test_multiclass_argmax_tie(self):self.assertEqual(decisions(np.full((1,3),1/3),np.array([0,1,2])).tolist(),[0])
 def test_zero_variance_float32_scaler_binary_and_multiclass(self):
  rng=np.random.default_rng(7)
  for nclass in [2,3]:
   x=rng.normal(size=(36,5)).astype(np.float32);x[:,4]=2;y=np.arange(36)%nclass;m=make_pipeline(StandardScaler(),LogisticRegression(solver='lbfgs',C=.1,class_weight='balanced',tol=1e-4,max_iter=2000,random_state=42)).fit(x,y);self.assertEqual(m[0].scale_[-1],1);np.testing.assert_allclose(m.predict_proba(x),reconstruct(m,x),atol=1e-10,rtol=0)
 def fixture(self):
  ids=np.array(['r'+str(i) for i in range(40)]);y=np.repeat(np.arange(20)%2,2);g=np.repeat(np.arange(20).astype(str),2);meta={'ids':ids,'labels':y,'groups':g};folds=[(np.setdiff1d(np.arange(40),np.arange(i*8,(i+1)*8)),np.arange(i*8,(i+1)*8)) for i in range(5)];saved=[{'train_ids':ids[a].tolist(),'validation_ids':ids[b].tolist()} for a,b in folds];return meta,saved
 def test_duplicate_sequences_distinct_ids_and_group_folds(self):
  m,f=self.fixture();out=validate_folds(f,m,5,np.array([0,1]));self.assertEqual(len(out),5)
 def test_group_leakage_rejected(self):
  m,f=self.fixture();a=f[0]['train_ids'][0];b=f[0]['validation_ids'][0];m['groups'][np.where(m['ids']==a)[0][0]]=m['groups'][np.where(m['ids']==b)[0][0]]
  with self.assertRaises(ValueError):validate_folds(f,m,5,np.array([0,1]))
 def test_fold_missing_complement_rejected(self):
  m,f=self.fixture();f[0]['train_ids'].pop()
  with self.assertRaises(ValueError):validate_folds(f,m,5,np.array([0,1]))
 def test_row_order_mismatch(self):
  m={'ids':np.array(['a','b']),'labels':np.array([0,1]),'groups':np.array(['g','h']),'sequence_sha256':np.array(['x','y'])};z={**m,'ids':m['ids'][::-1],'classes':np.array([0,1])}
  with self.assertRaises(ValueError):pair(z,m,np.array([0,1]))
 def test_wrong_candidate(self):
  with self.assertRaises(ValueError):stage_spec('R5',TASKS[0],'final_norm',42)
 def test_wrong_task(self):
  with self.assertRaises(ValueError):stage_spec('R4','emp_H3','final_norm',42)
 def test_cross_stage(self):
  with self.assertRaises(ValueError):stage_spec('R4',TASKS[0],'final_norm',42,'A08')
 def test_escape_path(self):
  with self.assertRaises(ValueError):owned(A/'../outside',A)
 def test_bad_hash_and_wrong_fixed_head(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'base.joblib';p.write_bytes(b'wrong head')
   with self.assertRaises(ValueError):check_ref({'path':str(p),'bytes':p.stat().st_size,'sha256':'0'*64})
 def test_valid_seal_resume_and_corrupt_cache(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);p=root/'values.npz';np.savez(p,x=np.arange(4));ident={'stage':'A07','candidate':'R4'};put(root/'COMPLETE.json',{'status':'PASS','identity':ident,'files':members(root)});verify_seal(root,ident);verify_seal(root,ident)
   p.write_bytes(b'corrupt')
   with self.assertRaises(ValueError):verify_seal(root,ident)
 def test_wrong_cache_identity(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);put(root/'COMPLETE.json',{'status':'PASS','identity':{'stage':'A07'},'files':[]})
   with self.assertRaises(ValueError):verify_seal(root,{'stage':'A08'})
 def test_partial_write_preserved(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);root=base/'unit';root.mkdir();(root/'partial').write_bytes(b'keep')
   with patch('other_five_common.A',base):work=new_work(root)
   self.assertTrue(work.exists());self.assertFalse(root.exists());self.assertEqual(list((base/'quarantine').rglob('partial'))[0].read_bytes(),b'keep')
 def test_sealed_output_never_overwritten(self):
  with tempfile.TemporaryDirectory() as t:
   base=Path(t);root=base/'unit';root.mkdir();put(root/'COMPLETE.json',{'status':'PASS'})
   with patch('other_five_common.A',base):
    with self.assertRaises(ValueError):new_work(root)
 def test_extra_cache_member_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);put(root/'COMPLETE.json',{'status':'PASS','identity':{},'files':[]});(root/'unexpected').write_text('partial')
   with self.assertRaises(ValueError):verify_seal(root,{})
 def test_single_writer_lock(self):
  with tempfile.TemporaryDirectory() as t:
   with UnitLock(Path(t)/'unit.lock'):
    with self.assertRaises(BlockingIOError):
     with UnitLock(Path(t)/'unit.lock'):pass
if __name__=='__main__':unittest.main(verbosity=2)
