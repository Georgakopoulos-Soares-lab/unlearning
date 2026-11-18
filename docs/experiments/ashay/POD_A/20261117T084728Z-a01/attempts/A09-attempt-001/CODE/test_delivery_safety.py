"""Real disposable Git/lock/event failure tests; no project ref mutations."""
from pathlib import Path
import tempfile,subprocess,unittest,fcntl,json
from progress import append_event_once
class DeliverySafety(unittest.TestCase):
 def test_event_replay_idempotent(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'events.jsonl';e={'event_id':'1','event_type':'sealed','prompt_commit':'pin','unit_counts':{'n':8},'next_allowed_action':'terminal'};self.assertTrue(append_event_once(p,dict(e)));self.assertFalse(append_event_once(p,dict(e)));self.assertEqual(len(p.read_text().splitlines()),1);e['unit_counts']={'n':9};self.assertTrue(append_event_once(p,e));self.assertEqual(len(p.read_text().splitlines()),2)
 def test_one_publisher_lock(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'publish.lock'
   with p.open('a') as a,p.open('a') as b:
    fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with self.assertRaises(BlockingIOError):fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
    fcntl.flock(a,fcntl.LOCK_UN);fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def test_rejected_push_preserves_local_work(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);origin=root/'origin.git';one=root/'one';two=root/'two'
   def g(cwd,*args,check=True):return subprocess.run(['git','-C',str(cwd),*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)
   subprocess.run(['git','init','--bare','--initial-branch=POD_A',str(origin)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE);g(root,'clone',str(origin),str(one));(one/'report.txt').write_text('base\n');g(one,'add','report.txt');g(one,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','base');g(one,'push','origin','HEAD:refs/heads/POD_A');g(root,'clone',str(origin),str(two));(two/'peer.txt').write_text('peer\n');g(two,'add','peer.txt');g(two,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','peer');g(two,'push','origin','HEAD:refs/heads/POD_A');(one/'report.txt').write_text('owned new report\n');g(one,'add','report.txt');g(one,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-m','local report');before=g(one,'rev-parse','HEAD').stdout;remote_before=g(two,'rev-parse','HEAD').stdout;r=g(one,'push','origin','HEAD:refs/heads/POD_A',check=False);self.assertNotEqual(r.returncode,0);self.assertEqual(g(one,'rev-parse','HEAD').stdout,before);self.assertEqual((one/'report.txt').read_text(),'owned new report\n');self.assertEqual(g(one,'ls-remote','--heads','origin','POD_A').stdout.split()[0],remote_before.strip())
if __name__=='__main__':unittest.main(verbosity=2)
