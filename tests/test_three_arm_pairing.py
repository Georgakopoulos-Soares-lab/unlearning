import numpy as np
import pytest
from scripts.sayyed.aggregate_three_arm import subtract_shared_base_contrasts
from scripts.sayyed.multiretain_metrics import bootstrap_metrics
from scripts.sayyed.multiretain_independent import metrics

@pytest.mark.parametrize('classes',[np.array([0,1]),np.array([0,1,2])])
def test_shared_base_cancels_with_ties_and_missing_class_draw(classes):
    y=np.repeat(classes,2);n=len(y)
    base=np.full((n,len(classes)),1/len(classes))
    old=np.full_like(base,.1);new=np.full_like(base,.15)
    for i,label in enumerate(y):
        old[i,label]=.8;new[i,label]=.7
    old/=old.sum(1,keepdims=True);new/=new.sum(1,keepdims=True)
    new[[0,2]]=new[[2,0]]
    weights=np.stack([np.ones(n),np.arange(1,n+1),np.eye(n)[0]*n])
    bm,valid=bootstrap_metrics(y,base,classes,weights)
    om,_=bootstrap_metrics(y,old,classes,weights);nm,_=bootstrap_metrics(y,new,classes,weights)
    ni,_=metrics(y,new,classes,weights);oi,_=metrics(y,old,classes,weights)
    assert valid.tolist()==[True,True,False]
    for key in nm:
        delta,ci=subtract_shared_base_contrasts(nm[key]-bm[key],om[key]-bm[key],valid)
        independent=ni[key]-oi[key]
        np.testing.assert_allclose(delta[valid],independent[valid],rtol=0,atol=1e-12)
        np.testing.assert_allclose(ci,np.quantile(independent[valid],[.025,.975]),rtol=0,atol=1e-12)
