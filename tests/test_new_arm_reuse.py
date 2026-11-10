import json
import joblib
import pytest
from scripts.sayyed.fit_multiretain_new_arm import reuse_base_head, sealed_files, sha

def fixture(tmp_path):
    old=tmp_path/'old';new=tmp_path/'new';old.mkdir();new.mkdir()
    joblib.dump({'immutable':'baseline'},old/'base.joblib')
    (old/'base_cv.json').write_text('[]')
    (old/'results.json').write_text(json.dumps({'fits':{'base':{'selected_C':.1}}}))
    sealed_files(old/'COMPLETE.json',[old/'base.joblib',old/'base_cv.json',old/'results.json'])
    return old,new

def test_reuses_exact_bytes_and_metadata(tmp_path):
    old,new=fixture(tmp_path);model,fit,files=reuse_base_head(old,new)
    assert model=={'immutable':'baseline'} and fit['reused'] and fit['selected_C']==.1
    for p in files:assert sha(p)==sha(old/p.name)

def test_rejects_changed_baseline_before_copy(tmp_path):
    old,new=fixture(tmp_path);(old/'base_cv.json').write_text('[1]')
    with pytest.raises(ValueError):reuse_base_head(old,new)
    assert not list(new.iterdir())
