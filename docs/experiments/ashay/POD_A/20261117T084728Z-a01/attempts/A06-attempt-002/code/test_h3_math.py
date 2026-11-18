import unittest,numpy as np
from threadpoolctl import threadpool_limits
from fit_h3 import train
from audit_h3 import fresh_fit,predict_parts,residual
from producer_metrics import bootstrap_metrics,point_metrics
from independent_math import metrics,reconstruct
class H3MathTests(unittest.TestCase):
 def setUp(self):
  rng=np.random.default_rng(90210);self.x=rng.normal(size=(80,12)).astype(np.float32);self.y=np.arange(80)%2;self.w=np.array([np.bincount(row,minlength=80) for row in rng.integers(0,80,size=(100,80))])
 def test_saved_vs_direct_and_fresh(self):
  with threadpool_limits(limits=4):
   model,_=train(self.x,self.y,.1);sc,head,_=fresh_fit(self.x,self.y,.1);p=model.predict_proba(self.x);self.assertLessEqual(residual(p,reconstruct(model,self.x),1e-10,'direct'),1e-10);self.assertLessEqual(residual(p,predict_parts(sc,head,self.x),1e-10,'fresh'),1e-10)
 def test_all_metrics_all_draws(self):
  score=np.linspace(.1,.9,80);score[0:4]=.3;p=np.c_[1-score,score];a,valid=bootstrap_metrics(self.y,p,np.array([0,1]),self.w);b,iv=metrics(self.y,p,np.array([0,1]),self.w);self.assertTrue(np.array_equal(valid,iv))
  for k in a:self.assertLessEqual(residual(a[k],b[k],1e-12,k),1e-12)
 def test_missing_class_common_mask(self):
  w=np.zeros((2,80));w[0,::2]=1;w[1]=1;p=np.c_[np.full(80,.4),np.full(80,.6)];a,v=bootstrap_metrics(self.y,p,np.array([0,1]),w);b,iv=metrics(self.y,p,np.array([0,1]),w);self.assertEqual(v.tolist(),[False,True]);self.assertTrue(np.array_equal(v,iv));self.assertTrue(all(np.isnan(values[0]) for values in a.values()))
 def test_infinite_residual_rejected(self):
  with self.assertRaises(ValueError):residual([np.inf],[np.inf],1e-12,'infinite')
if __name__=='__main__':unittest.main()
