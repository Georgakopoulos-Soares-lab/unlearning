from common import *
from research_guard import guard
import argparse,re
def deliver(label):
 guard(allow_dirty=True)
 remote=git('ls-remote','--heads','origin','POD_A').split()[0]
 subprocess.run(['git','-C',str(W),'merge-base','--is-ancestor',remote,'HEAD'],check=True)
 paths=[str(p.relative_to(W)) for p in D.rglob('*') if p.is_file()]+[str((BASE/n).relative_to(W)) for n in ['PROGRESS.md','CONTROLLER_LATEST.json','LATEST_A07.json'] if (BASE/n).exists()]
 if (C/'BACKFILL_REPORT_PATHS.json').exists():paths+=read(C/'BACKFILL_REPORT_PATHS.json')
 for p in paths:
  q=W/p;assert q.resolve().is_relative_to(W.resolve()) and not q.is_symlink();data=q.read_bytes();assert q.stat().st_size<(50 if q.suffix=='.csv' else 20)*1024**2
  assert q.suffix not in ['.npz','.npy','.joblib','.distcp','.pt','.bin']
  assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',data)
  assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',data)
 guard(allow_dirty=True);subprocess.run(['git','-C',str(W),'add','--',*paths],check=True)
 changed=git('diff','--cached','--name-only').splitlines();assert changed and set(changed)<=set(paths)
 subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True);guard(allow_dirty=True)
 subprocess.run(['git','-C',str(W),'-c','user.name=AshaySrivastava','-c','user.email=149273902+ashay-sriv-06@users.noreply.github.com','commit','-m',label],check=True,stdout=subprocess.PIPE)
 commit=git('rev-parse','HEAD');guard();assert git('ls-remote','--heads','origin','POD_A').split()[0]==remote
 subprocess.run(['git','-C',str(W),'push','origin','HEAD:refs/heads/POD_A'],check=True)
 assert git('ls-remote','--heads','origin','POD_A').split()[0]==commit;guard()
 receipt={'status':'PASS','commit':commit,'parent_remote':remote,'remote_equal':True,'changed_paths':changed,'delivered_utc':now(),'label':label}
 put(C/('DELIVERY_'+commit[:12]+'.json'),receipt);print(json.dumps({'status':'DELIVERED','commit':commit,'files':len(changed)}));return receipt
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--message',required=True);args=p.parse_args();deliver(args.message)
