"""Saved-output-only numeric primitives and finite predeclared contrast runner."""
import math
import numpy as np

def lm_numbers(meta,draw,weights):
 if not np.isfinite(meta['nll_sum']).all() or np.any(meta['n_tokens']<=0):raise ValueError('Nonfinite LM loss or invalid target counts')
 names,inverse=np.unique(meta['groups'],return_inverse=True);group_loss=[math.fsum(float(x) for x in meta['nll_sum'][inverse==g]) for g in range(len(names))];group_tokens=[sum(int(x) for x in meta['n_tokens'][inverse==g]) for g in range(len(names))];point=math.fsum(float(x) for x in meta['nll_sum'])/sum(int(x) for x in meta['n_tokens']);ratio=np.array([math.fsum(group_loss[int(g)] for g in d)/sum(group_tokens[int(g)] for g in d) for d in draw]);other=(weights@meta['nll_sum'].astype(np.float64))/(weights@meta['n_tokens']);return point,ratio,other
