"""Exact inherited estimator functions only; no historical main/import side effects."""
import time,warnings
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def pipeline(c,max_iter):
    return make_pipeline(StandardScaler(),LogisticRegression(C=c,class_weight='balanced',solver='lbfgs',
        tol=1e-4,max_iter=max_iter,random_state=42))

def train_model(x,y,c):
    attempts=[]
    for limit in [2000,10000]:
        model=pipeline(c,limit);started=time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always');model.fit(x,y)
        conv=[w for w in caught if issubclass(w.category,ConvergenceWarning)]
        attempts.append(dict(max_iter=limit,n_iter=model[-1].n_iter_.tolist(),seconds=time.perf_counter()-started,
                             warnings=[str(w.message) for w in caught]))
        if not conv:return model,attempts
    raise RuntimeError('Unresolved train-only convergence failure')
