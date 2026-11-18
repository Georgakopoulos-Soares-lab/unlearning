"""Synthetic/adversarial A08 qualification; no real cohorts or model forwards."""
import unittest,tempfile,warnings
from unittest.mock import patch
from audit_common import *
from independent_math import metrics,reconstruct
from rank_crosscheck import bootstrap_metrics,point_metrics,decisions
from refit_panel import fit_independent
from sklearn.exceptions import ConvergenceWarning
class AuditTests(unittest.TestCase):
 def compare(self,y,p,c,w):
  with np.errstate(divide='ignore',invalid='ignore'):
   independent,valid=metrics(y,p,c,w);rank,rankvalid=bootstrap_metrics(y,p,c,w)
  self.assertTrue(np.array_equal(valid,rankvalid))
  for m in METRICS:np.testing.assert_allclose(independent[m],rank[m],atol=1e-12,rtol=0,equal_nan=True)
  point,_=point_metrics(y,p,c);ind,_=metrics(y,p,c,np.ones((1,len(y))))
  for m in METRICS:self.assertLessEqual(abs(point[m]-ind[m][0]),1e-12)
 def test_binary_tied_scores_absent_draw(self):
  y=np.array([0,1,0,1,0,1]);p=np.array([[.5,.5],[.5,.5],[.8,.2],[.2,.8],[1.,0.],[0.,1.]]);self.compare(y,p,np.array([0,1]),np.array([[1]*6,[1,0,1,0,1,0],[2,3,1,4,2,1]]))
 def test_threeclass_tied_macro_absent_draw(self):
  y=np.tile([0,1,2],4);p=np.array([[1/3]*3,[.2,.4,.4],[.2,.4,.4],[.7,.2,.1]]*3);self.compare(y,p,np.array([0,1,2]),np.array([[1]*12,[1,0,0]*4,[2,3,1]*4]))
 def test_binary_threshold_equality(self):self.assertEqual(decisions(np.array([[.5,.5]]),np.array([0,1])).tolist(),[1])
 def test_threeway_argmax_tie(self):self.assertEqual(decisions(np.full((1,3),1/3),np.array([0,1,2])).tolist(),[0])
 def test_zero_variance_float32_reconstruction(self):
  rng=np.random.default_rng(7)
  for nclass in [2,3]:
   x=rng.normal(size=(36,5)).astype(np.float32);x[:,4]=2;y=np.arange(36)%nclass;model,attempts=fit_independent(x,y,.1,'SYNTHETIC_ONLY');self.assertEqual(model[0].scale_[-1],1);np.testing.assert_allclose(reconstruct(model,x),model.predict_proba(x),atol=1e-10,rtol=0)
 def test_nonfinite_probabilities(self):
  with self.assertRaises(ValueError):probabilities_valid(np.array([[np.nan,.5],[.5,.5]]),np.array([0,1]),np.array([0,1]))
 def test_permuted_classes(self):
  with self.assertRaises(ValueError):probabilities_valid(np.full((3,3),1/3),np.array([0,1,2]),np.array([2,1,0]))
 def test_bad_normalization(self):
  with self.assertRaises(ValueError):probabilities_valid(np.ones((2,2)),np.array([0,1]),np.array([0,1]))
 def fixture(self):
  ids=np.array(['r'+str(i) for i in range(40)]);y=np.repeat(np.arange(20)%2,2);groups=np.repeat(np.arange(20).astype(str),2);meta={'ids':ids,'labels':y,'groups':groups};saved=[{'validation_ids':ids[i*8:(i+1)*8].tolist(),'train_ids':np.r_[ids[:i*8],ids[(i+1)*8:]].tolist()} for i in range(5)];return meta,saved
 def test_duplicate_groups_distinct_rows_folds(self):
  meta,saved=self.fixture();self.assertEqual(len(validate_folds(saved,meta,5,np.array([0,1]))),5)
 def test_group_leakage_rejected(self):
  meta,saved=self.fixture();meta['groups'][-1]=meta['groups'][0]
  with self.assertRaises(ValueError):validate_folds(saved,meta,5,np.array([0,1]))
 def test_missing_fold_member_rejected(self):
  meta,saved=self.fixture();saved[0]['train_ids'].pop()
  with self.assertRaises(ValueError):validate_folds(saved,meta,5,np.array([0,1]))
 def test_row_order_rejected(self):
  meta={k:np.array(v) for k,v in {'ids':['a','b'],'labels':[0,1],'groups':['x','y'],'sequence_sha256':['u','v']}.items()};z={**meta,'ids':meta['ids'][::-1],'classes':np.array([0,1])}
  with self.assertRaises(ValueError):paired(z,meta,np.array([0,1]))
 def test_group_order_rejected(self):
  meta={k:np.array(v) for k,v in {'ids':['a','b'],'labels':[0,1],'groups':['x','y'],'sequence_sha256':['u','v']}.items()};z={**meta,'groups':meta['groups'][::-1],'classes':np.array([0,1])}
  with self.assertRaises(ValueError):paired(z,meta,np.array([0,1]))
 def temp(self):
  (A/'synthetic-tests').mkdir(exist_ok=True);return tempfile.TemporaryDirectory(dir=A/'synthetic-tests')
 def test_corrupt_member(self):
  with self.temp() as t:
   p=Path(t)/'data';p.write_bytes(b'abc');entry=ref(p);p.write_bytes(b'bad')
   with self.assertRaises(ValueError):checked(entry)
 def test_wrong_fixed_base_hash(self):
  with self.temp() as t:
   p=Path(t)/'base.joblib';p.write_bytes(b'wrong')
   with self.assertRaises(ValueError):checked({'path':str(p),'bytes':5,'sha256':'0'*64})
 def test_extra_cache_member(self):
  with self.temp() as t:
   root=Path(t);(root/'extra').write_text('x')
   with self.assertRaises(ValueError):validate_members(root,{'files':[]})
 def test_restart_after_valid_seal(self):
  with self.temp() as t:
   root=Path(t)/'unit';tmp=workdir(root);(tmp/'value').write_text('x');identity={'stage':'A08'};seal(tmp,root,{'status':'PASS','identity':identity});seal_check(root,identity);seal_check(root,identity)
 def test_stale_identity(self):
  with self.temp() as t:
   root=Path(t);put(root/'COMPLETE.json',{'status':'PASS','identity':{'stage':'A08'},'files':[]})
   with self.assertRaises(ValueError):seal_check(root,{'stage':'A07'})
 def test_partial_preserved_on_restart(self):
  with self.temp() as t:
   root=Path(t)/'unit';root.mkdir();(root/'partial').write_bytes(b'keep');temp=workdir(root);self.assertTrue(temp.exists());self.assertFalse(root.exists());self.assertTrue(any(p.read_bytes()==b'keep' for p in (A/'quarantine').rglob('partial')))
 def test_single_writer(self):
  with self.temp() as t:
   with Lock(Path(t)/'unit.lock'):
    with self.assertRaises(BlockingIOError):
     with Lock(Path(t)/'unit.lock'):pass
 def test_foreign_stage_dispatch(self):
  with self.assertRaises(ValueError):unit_spec('R4/gue_tf_0/final_norm/seed42','A07')
 def test_foreign_unit_dispatch(self):
  with self.assertRaises(ValueError):unit_spec('R4/gue_tf_0/final_norm/seed42')
 def test_path_escape(self):
  with self.assertRaises(ValueError):owned(A/'../foreign')
 def test_splice_group_multiplicity_shared(self):
  groups=np.array(['a','b','b','c']);names,inverse=np.unique(groups,return_inverse=True);draw=np.array([1,1,2]);multiplicity=np.zeros(3,dtype=int);np.add.at(multiplicity,draw,1);expanded=multiplicity[inverse];self.assertEqual(expanded.tolist(),[0,2,2,1])
 def test_nonfinite_features_rejected(self):
  with self.temp() as t:
   fake=Path(t);root=fake/'cache/R5/gue_tf_0/train';root.mkdir(parents=True);np.save(root/'final_norm.npy',np.full((2,1920),np.nan,dtype=np.float32));np.savez(root/'metadata.npz',ids=np.array(['a','b']));put(root/'COMPLETE.json',{'files':file_entries(root)})
   with patch('audit_common.A7',fake):
    with self.assertRaises(ValueError):features('R5','gue_tf_0','train','final_norm')
 def test_LM_corpus_ratio_and_shared_groups(self):
  from analysis_pairs import lm_numbers
  meta={'groups':np.array(['a','b','b']),'nll_sum':np.array([2.,8.,4.],dtype=np.float32),'n_tokens':np.array([1,2,1],dtype=np.int64)};draw=np.array([[0,1],[1,1]]);weights=np.array([[1,1,1],[0,2,2]]);point,ratio,other=lm_numbers(meta,draw,weights);self.assertEqual(point,3.5);np.testing.assert_allclose(ratio,other,atol=1e-12,rtol=0);self.assertGreater(abs(np.exp(point)-np.mean(np.exp(meta['nll_sum']/meta['n_tokens']))),1e-3)
 def test_LM_invalid_count_rejected(self):
  from analysis_pairs import lm_numbers
  meta={'groups':np.array(['a']),'nll_sum':np.array([2.],dtype=np.float32),'n_tokens':np.array([0],dtype=np.int64)}
  with self.assertRaises(ValueError):lm_numbers(meta,np.array([[0]]),np.ones((1,1)))
if __name__=='__main__':unittest.main(verbosity=2)
