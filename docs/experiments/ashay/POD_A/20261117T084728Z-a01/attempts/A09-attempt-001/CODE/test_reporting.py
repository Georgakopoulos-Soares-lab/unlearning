"""Focused failure tests for A09 typed writers, ownership and identity joins."""
import unittest,tempfile,json,csv
from pathlib import Path
from common import put,write_md,atomic
from research_guard import identity,owned
from repairs import resolve_control
class ReportingTests(unittest.TestCase):
 def test_markdown_writer_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'handoff.md';text='# Handoff\n\n## Findings\n\n[Results](RESULTS.md)\n';write_md(p,text);self.assertEqual(p.read_text(),text);self.assertNotIn('\\n',p.read_text());self.assertTrue(p.read_text().startswith('# '))
 def test_json_writer_rejects_markdown(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'bad.md'
   with self.assertRaises(TypeError):put(p,'# Handoff\n\nContent\n')
   self.assertFalse(p.exists())
 def test_markdown_rejects_json_encoded_text(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(TypeError):write_md(Path(d)/'bad.md',json.dumps('# Handoff\n\nText\n'))
 def test_json_atomic_object(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'object.json';put(p,{'n':None,'pass':True});self.assertEqual(json.loads(p.read_text()),{'n':None,'pass':True});self.assertFalse(p.with_name('.'+p.name+'.tmp').exists())
 def test_wrong_branch_and_origin_rejected(self):
  args=['/workspace/wt-pod-a','/workspace/repos/unlearning-pod-a/.git','https://github.com/Georgakopoulos-Soares-lab/unlearning.git','https://github.com/Georgakopoulos-Soares-lab/unlearning.git','POD_A'];identity(*args)
  for k,v in [(2,'https://github.com/other/repo.git'),(3,'https://github.com/other/repo.git'),(4,'main'),(4,'POD_B'),(0,'/workspace/wt-eval-pilot')]:
   wrong=list(args);wrong[k]=v
   with self.assertRaises(ValueError):identity(*wrong)
 def test_path_boundary(self):
  self.assertTrue(owned('docs/run/attempt/report.md',['docs/run/attempt']));self.assertFalse(owned('docs/run/attempt-other/report.md',['docs/run/attempt']));self.assertFalse(owned('docs/peer/report.md',['docs/run/attempt']))
 def fixture(self):
  pair={'reference':'control_composition','task':'emp_H3','split':'dev','CV_seed':'42','metric':'auroc','reference_endpoint_id':'control-head-sha256:abc','reference_prediction_sha256':'pred'};p={'checkpoint_alias':'control_composition','task':'emp_H3','split':'dev','CV_seed':'42','metric':'auroc','checkpoint_content_id':'abc','prediction_sha256':'pred'};u={'task':'emp_H3','control':'composition','seed':42,'head':{'sha256':'abc'},'records':[{'split':'dev','predictions':{'sha256':'pred'}}]};return pair,p,u
 def test_unique_identity_alias(self):
  pair,p,u=self.fixture();out=resolve_control(pair,[p],[u]);self.assertEqual(out[0],p)
 def test_name_only_conflict_rejected(self):
  pair,p,u=self.fixture();p['prediction_sha256']='other'
  with self.assertRaises(ValueError):resolve_control(pair,[p],[u])
 def test_duplicate_and_wrong_seed_rejected(self):
  pair,p,u=self.fixture()
  with self.assertRaises(ValueError):resolve_control(pair,[p,p],[u])
  p['CV_seed']='17'
  with self.assertRaises(ValueError):resolve_control(pair,[p],[u])
 def test_wrong_control_content_rejected(self):
  pair,p,u=self.fixture();pair['reference_endpoint_id']='control-head-sha256:wrong'
  with self.assertRaises(ValueError):resolve_control(pair,[p],[u])
if __name__=='__main__':unittest.main(verbosity=2)
