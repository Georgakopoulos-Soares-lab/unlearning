import numpy as np
def paired(t,r,tm,rm,tp,rp):
 t=np.asarray(t,dtype=np.float64);r=np.asarray(r,dtype=np.float64);tm=np.asarray(tm,dtype=bool);rm=np.asarray(rm,dtype=bool)
 assert t.shape==r.shape==tm.shape==rm.shape==(2000,)
 assert np.array_equal(np.isfinite(t),tm) and np.array_equal(np.isfinite(r),rm)
 mask=tm & rm;v=np.full(2000,np.nan);v[mask]=t[mask]-r[mask]
 ci=np.quantile(v[mask],[.025,.975],method='linear').tolist() if mask.any() else [None,None]
 return float(tp-rp),v,mask,ci
def favorable(metric,family):return 'not_universally_ordered' if family=='anchor_policy_gap' else ('negative' if metric=='cross_entropy' else 'positive')
