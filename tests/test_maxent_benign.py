import json
import numpy as np
import pytest
import torch
import torch.distributed.checkpoint as dcp
from scripts.sayyed.check_benign_checkpoint_pair import load
from scripts.sayyed.fit_maxent_benign import arrays
from scripts.sayyed.fit_maxent_extension import auc
from scripts.sayyed.verify_h3_followup import rank_metrics

def test_missing_or_nonfinite_backbone_tensor_rejected(tmp_path):
    dcp.save({'weight':torch.tensor([1.0])},checkpoint_id=tmp_path/'good')
    with pytest.raises(ValueError,match='Missing model tensors'):load(tmp_path/'good',keys=['missing'])
    dcp.save({'weight':torch.tensor([float('nan')])},checkpoint_id=tmp_path/'bad')
    with pytest.raises(ValueError,match='Nonfinite'):load(tmp_path/'bad')

def test_saved_label_association_rejected(tmp_path):
    import hashlib
    rows=[dict(id='a',sequence='AC',label=0,split='train'),dict(id='b',sequence='GT',label=1,split='dev')]
    (tmp_path/'identity.json').write_text(json.dumps(dict(cache_key='synthetic')))
    (tmp_path/'complete.json').write_text(json.dumps(dict(examples=2)))
    np.savez(tmp_path/'chunk_000000.npz',cache_key=np.array('synthetic'),ids=np.array(['a','b']),labels=np.array([1,0]),split=np.array(['train','dev']),sequence_sha256=np.array([hashlib.sha256(r['sequence'].encode()).hexdigest() for r in rows]))
    with pytest.raises(ValueError,match='Label/split mismatch'):arrays(tmp_path,rows)

def test_macro_ovr_agrees_with_independent_tied_rank():
    y=np.array([0,1,2,0,1,2]);p=np.array([[.7,.2,.1],[.2,.5,.3],[.1,.5,.4],[.4,.5,.1],[.2,.6,.2],[.2,.3,.5]])
    expected=np.mean([rank_metrics((y==c).astype(int),p[:,c])['auroc'] for c in range(3)])
    assert auc(y,p,np.array([0,1,2]))==pytest.approx(expected)
