from pathlib import Path
import sys,json,hashlib,re,fcntl,urllib.parse
from ops import C,A,R,run,save,now
label=sys.argv[1];message=sys.argv[2];assert re.fullmatch('[A-Za-z0-9_-]+',label)
T=R/json.loads((C/'PATHS.json').read_text())['run_root'];P=T/'S06/attempt-001';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(s,*a,network=False):return run(label+'-'+s,['git',*a],R,network=network).decode().strip()
with (C/'RESEARCH_PUBLICATION.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert git('branch','branch','--show-current')=='POD_A_SALIENCY';assert git('origin','remote','get-url','origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git';before=git('head','rev-parse','HEAD');run(label+'-ancestry',['git','merge-base','--is-ancestor','63703809d2ff5062a82af43f5b4f8b7e53e04f36','HEAD'],R)
 for phase in ['S00','S01','S02','S03','S04','S05']:run(label+'-preserve-'+phase,['git','diff','--exit-code','63703809d2ff5062a82af43f5b4f8b7e53e04f36','--',str((T/phase).relative_to(R))],R)
 pkg=Path(json.loads((C/'PATHS.json').read_text())['package_root']);sys.path.insert(0,str(pkg));import S_validate_package as canonical_validator
 canonical_validator.schema_engine()(json.loads((pkg/'S_support/CONTROLLER_STATE.schema.json').read_text())).validate(json.loads((T/'CONTROLLER_STATE.json').read_text()));save(C/(label+'-CONTROLLER_SCHEMA.json'),{'status':'PASS','controller_sha256':sha(T/'CONTROLLER_STATE.json'),'schema_sha256':sha(pkg/'S_support/CONTROLLER_STATE.schema.json')})
 assert git('index','diff','--cached','--name-only')==''
 (P/'OUTPUT_SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(P))+'\n' for p in sorted(P.rglob('*')) if p.is_file() and p.name!='OUTPUT_SHA256SUMS'))
 baseline=run(label+'-root-manifest-baseline',['git','show','63703809d2ff5062a82af43f5b4f8b7e53e04f36:'+str((T/'OUTPUT_SHA256SUMS').relative_to(R))],R).decode();root_hashes={n:h for line in baseline.splitlines() for h,n in [line.split(None,1)]}
 for n in ['CONTROLLER_STATE.json','EVENTS.jsonl','PROGRESS.md','SESSION_HANDOFF.md']:root_hashes[n]=sha(T/n)
 for p in sorted(P.rglob('*')):
  if p.is_file():root_hashes[str(p.relative_to(T))]=sha(p)
 (T/'OUTPUT_SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(root_hashes.items())))
 root=str(T.relative_to(R))+'/';prefix=str(P.relative_to(R))+'/';allowed={root+n for n in ['CONTROLLER_STATE.json','EVENTS.jsonl','PROGRESS.md','SESSION_HANDOFF.md','OUTPUT_SHA256SUMS']}
 paths=git('changed','diff','--name-only').splitlines()+git('new','ls-files','--others','--exclude-standard').splitlines();assert paths and all(n in allowed or n.startswith(prefix) for n in paths)
 for n in paths:
  p=R/n;assert p.is_file() and not p.is_symlink() and p.stat().st_size<8*1024**2; b=p.read_bytes();assert not re.search(rb'\bhf_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+|X-Goog-Signature=[A-Za-z0-9%]{8,}|X-Amz-Signature=[A-Za-z0-9%]{8,}',b),n;assert (b'ashay-sriv/' + b'undo-') not in b and (b'ashay-sriv/' + b'unlearning-checkpoint-mirror') not in b,n
  assert p.suffix not in ['.npz','.npy','.joblib','.pt','.distcp','.tar','.gz']
  if p.suffix=='.json':json.loads(b)
 remote=git('remote-before','ls-remote','--exit-code','origin','refs/heads/POD_A_SALIENCY',network=True).split()[0];assert remote==before,'Remote advanced; inspect before mutation'
 run(label+'-whitespace',['git','diff','--check','--',*paths],R);hashes={n:sha(R/n) for n in paths};save(C/(label+'-ALLOWLIST.json'),{'before':before,'paths':paths,'hashes':hashes})
 run(label+'-stage',['git','add','--',*paths],R);assert set(git('staged','diff','--cached','--name-only').splitlines())==set(paths);run(label+'-commit',['git','commit','-m',message],R);commit=git('commit-id','rev-parse','HEAD');assert git('parent','rev-parse','HEAD^')==before;save(C/(label+'-COMMIT.json'),{'commit':commit,'parent':before,'paths':paths,'hashes':hashes,'status':'COMMITTED_NOT_YET_REMOTE_VERIFIED'})
 run(label+'-push',['git','push','origin','HEAD:refs/heads/POD_A_SALIENCY'],R,network=True);assert git('remote-after','ls-remote','--exit-code','origin','refs/heads/POD_A_SALIENCY',network=True).split()[0]==commit
 for i,n in enumerate(paths):
  blob=run(label+'-blob-'+str(i),['git','show',commit+':'+n],R);assert hashlib.sha256(blob).hexdigest()==hashes[n];endpoint='repos/Georgakopoulos-Soares-lab/unlearning/contents/'+urllib.parse.quote(n,safe='/')+'?ref='+commit;fresh=run(label+'-HTTP-'+str(i),['gh','api',endpoint,'-H','Accept: application/vnd.github.raw+json'],R,network=True);assert fresh==blob
 assert git('clean','status','--porcelain')=='';save(C/(label+'-DELIVERY.json'),{'status':'PASS','commit':commit,'parent':before,'verified_remote_files':len(paths),'file_sha256':hashes,'branch':'POD_A_SALIENCY','readback':'Exact committed Git bytes and fresh immutable GitHub raw API bytes matched for every changed file','completed_utc':now()});print('S06_PUBLICATION_PASS',commit,len(paths),flush=True)
