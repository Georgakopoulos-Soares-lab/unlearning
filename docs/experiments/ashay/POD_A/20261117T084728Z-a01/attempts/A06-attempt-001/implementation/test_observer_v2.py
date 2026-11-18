import unittest,time,json
from unittest.mock import patch
from pathlib import Path
import observer_v2 as o
class ObserverMaintenance(unittest.TestCase):
 def mapping(self):return {'stages':[{'id':f'A{i:02d}','file':f} for i,f in enumerate(o.CANONICAL,1)],'execution_on_install':False,'administrative_loop':{'stage_dispatch':False}}
 def test_exact_map(self):o.validate_mapping(self.mapping())
 def test_wrong_filename(self):
  j=self.mapping();j['stages'][5]['file']='A06_DUPLICATE.md'
  with self.assertRaises(ValueError):o.validate_mapping(j)
 def test_extra_stage(self):
  j=self.mapping();j['stages'].append({'id':'A10','file':'X'})
  with self.assertRaises(ValueError):o.validate_mapping(j)
 def test_dispatch_rejected(self):
  j=self.mapping();j['execution_on_install']=True
  with self.assertRaises(ValueError):o.validate_mapping(j)
 def test_wrong_origin(self):
  with self.assertRaises(ValueError):o.validate_identity('https://github.com/other/repo','DISABLED_OBSERVER_READ_ONLY','refs/heads/POD_A')
 def test_wrong_branch(self):
  with self.assertRaises(ValueError):o.validate_identity(o.ORIGIN,'DISABLED_OBSERVER_READ_ONLY','refs/heads/POD_B')
 def test_push_policy(self):
  with self.assertRaises(ValueError):o.validate_identity(o.ORIGIN,o.ORIGIN,'refs/heads/POD_A')
 def test_authoritative_A06_pin(self):
  pin,hashes,stage=o.approved_context();self.assertEqual(stage,'A06');self.assertEqual(pin,'c519b1aa37d0d8334b0b2e1d83a671c6c0eb7ab5');self.assertEqual(len(hashes),34)
 def test_newer_error_not_active(self):self.assertEqual(o.health_status({'observed_utc':'2026-11-18T02:00:00+00:00'},{'observed_utc':'2026-11-18T02:01:00+00:00'},0),'ERROR_NEWER_THAN_SUCCESS')
 def test_stale_success(self):self.assertEqual(o.health_status({'observed_utc':'2026-11-18T00:00:00+00:00'},None,9999999999),'STALE_SUCCESS')
 def test_no_science_dispatch(self):
  s=Path(o.__file__).read_text();self.assertNotIn("g('push'",s);self.assertNotIn('codex exec',s);self.assertIn("'science_execution':False",s)
if __name__=='__main__':unittest.main()
