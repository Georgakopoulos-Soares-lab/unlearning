from common7 import *
import fcntl,re
def deliver(label):
 with (R/'REPOSITORY_DELIVERY.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);guard();remote=git('ls-remote','--heads','origin','POD_A').split()[0];assert remote==git('rev-parse','HEAD'),'Remote advanced; preserve work and wait'
  paths=[str(p.relative_to(W)) for p in D.rglob('*') if p.is_file()]+[str((B/n).relative_to(W)) for n in cfg['allowed_root_files'] if (B/n).exists()]
  for rel in paths:
   p=W/rel;data=p.read_bytes();assert owned(rel) and p.resolve().is_relative_to(B.resolve()) and not p.is_symlink();assert len(data)<20*1024**2 and p.suffix not in ['.npz','.npy','.joblib','.distcp','.pt','.bin'];assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',data);assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',data)
  assert all(owned(p) for p in paths);staged=git('diff','--cached','--name-only').splitlines();assert set(staged)<=set(paths) and all(owned(p) for p in staged),'Unowned staged input; preserve and stop';guard();subprocess.run(['git','-C',str(W),'add','--',*paths],check=True);changed=git('diff','--cached','--name-only').splitlines();assert changed and set(changed)<=set(paths);subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True);guard();assert git('ls-remote','--heads','origin','POD_A').split()[0]==remote
  subprocess.run(['git','-C',str(W),'-c','user.name=AshaySrivastava','-c','user.email=149273902+ashay-sriv-06@users.noreply.github.com','commit','-m',label],check=True,stdout=subprocess.PIPE);head=git('rev-parse','HEAD');guard(head=head);subprocess.run(['git','-C',str(W),'push','origin','HEAD:refs/heads/POD_A'],check=True);assert git('ls-remote','--heads','origin','POD_A').split()[0]==head;guard(dirty=False,head=head)
  for rel in paths:assert gitb('show',head+':'+rel)==(W/rel).read_bytes()
  receipt={'status':'PASS','commit':head,'parent_remote':remote,'changed_paths':changed,'all_owned_committed_bytes_verified':True,'remote_equal':True,'delivered_utc':now()};put(C/('GIT_DELIVERY.'+head[:12]+'.json'),receipt);return receipt
