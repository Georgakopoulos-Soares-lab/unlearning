"""Owned-only normal-FF publication, exact local Git bytes and fresh remote Merkle-tree/readback."""
from pathlib import Path
import sys,json,hashlib,re,fcntl,urllib.parse
from ops import C,A,R,run,save,now
label=sys.argv[1];message=sys.argv[2];assert re.fullmatch('[A-Za-z0-9_-]+',label)
T=R/'docs/experiments/ashay/POD_A_SALIENCY/20261123T111855Z-saliency';P=T/'S10/attempt-001';baseline='3c39552d43c2e4c8aaf223ca97e3b8f6ee33d11c'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def git(s,*args,network=False):return run(label+'-'+s,['git',*args],R,network=network).decode().strip()
with (C/'RESEARCH_PUBLICATION.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);assert git('branch','branch','--show-current')=='POD_A_SALIENCY' and git('origin','remote','get-url','origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git';before=git('head','rev-parse','HEAD');run(label+'-ancestry',['git','merge-base','--is-ancestor',baseline,'HEAD'],R)
 for phase in ['S00','S01','S02','S03','S04','S05','S06','S07','S08','S09']:run(label+'-preserve-'+phase,['git','diff','--exit-code',baseline,'--',str((T/phase).relative_to(R))],R)
 assert git('original-POD-A','rev-parse','POD_A')=='8c651c7ab3c3a2a47f5bbd0e464a69a197512c82';assert git('index','diff','--cached','--name-only')==''
 (P/'OUTPUT_SHA256SUMS').write_text(''.join(sha(p)+'  '+str(p.relative_to(P))+'\n' for p in sorted(P.rglob('*')) if p.is_file() and p.name!='OUTPUT_SHA256SUMS'))
 original=run(label+'-root-manifest',['git','show',baseline+':'+str((T/'OUTPUT_SHA256SUMS').relative_to(R))],R).decode();hashes={n:h for line in original.splitlines() for h,n in [line.split(None,1)]}
 for n in ['CONTROLLER_STATE.json','EVENTS.jsonl','PROGRESS.md','SESSION_HANDOFF.md']:hashes[n]=sha(T/n)
 for p in sorted(P.rglob('*')):
  if p.is_file():hashes[str(p.relative_to(T))]=sha(p)
 (T/'OUTPUT_SHA256SUMS').write_text(''.join(h+'  '+n+'\n' for n,h in sorted(hashes.items())))
 root=str(T.relative_to(R))+'/';prefix=str(P.relative_to(R))+'/';allowed={root+n for n in ['CONTROLLER_STATE.json','EVENTS.jsonl','PROGRESS.md','SESSION_HANDOFF.md','OUTPUT_SHA256SUMS']};paths=git('changed','diff','--name-only').splitlines()+git('new','ls-files','--others','--exclude-standard').splitlines();assert paths and len(paths)==len(set(paths)) and all(n in allowed or n.startswith(prefix) for n in paths)
 assert json.loads((P/'RETAIN_FORGET_VIEWS.json').read_text())['figures']==[];declared={}
 for n in paths:
  p=R/n;assert p.is_file() and not p.is_symlink() and p.stat().st_size<32*1024**2;nbytes=p.read_bytes();assert not re.search(rb'\bhf_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+|X-Goog-Signature=[A-Za-z0-9%]{8,}|X-Amz-Signature=[A-Za-z0-9%]{8,}',nbytes),n;assert (b'ashay-sriv/'+b'undo-') not in nbytes and (b'ashay-sriv/'+b'unlearning-checkpoint-mirror') not in nbytes,n;assert p.suffix not in ['.npz','.npy','.joblib','.pt','.distcp','.tar','.gz']
  if p.suffix in ['.png','.pdf','.svg']:assert n in declared and sha(p)==declared[n]['sha256'] and len(nbytes)==declared[n]['bytes']
  if p.suffix=='.json':json.loads(nbytes)
 remote=git('remote-before','ls-remote','--exit-code','origin','refs/heads/POD_A_SALIENCY',network=True).split()[0];assert remote==before,'Remote advanced; reconcile before mutation'
 run(label+'-whitespace',['git','diff','--check','--',*paths],R);selected={n:sha(R/n) for n in paths};save(C/(label+'-ALLOWLIST.json'),{'before':before,'paths':paths,'SHA256':selected,'PNG_PDF_SVG_only_exact_qualified_figure_manifest':True,'public_file_cap_bytes':32*1024**2})
 run(label+'-stage',['git','add','--',*paths],R);assert set(git('staged','diff','--cached','--name-only').splitlines())==set(paths);run(label+'-commit',['git','commit','-m',message],R);commit=git('commit-id','rev-parse','HEAD');assert git('parent','rev-parse','HEAD^')==before;save(C/(label+'-COMMIT.json'),{'commit':commit,'parent':before,'paths':paths,'file_sha256':selected,'status':'COMMITTED_PENDING_REMOTE_VERIFICATION'})
 run(label+'-push',['git','push','origin','HEAD:refs/heads/POD_A_SALIENCY'],R,network=True);assert git('remote-after','ls-remote','--exit-code','origin','refs/heads/POD_A_SALIENCY',network=True).split()[0]==commit
 # Each committed byte is checked against its sealed SHA256. Fresh server tree proves every remote blob identity.
 for i,n in enumerate(paths):blob=run(label+'-local-blob-'+str(i),['git','show',commit+':'+n],R);assert hashlib.sha256(blob).hexdigest()==selected[n]
 tree=git('local-phase-tree','rev-parse',commit+':'+str(P.relative_to(R)));api='repos/Georgakopoulos-Soares-lab/unlearning';remote_tree=json.loads(run(label+'-remote-phase-tree',['gh','api',api+'/git/trees/'+tree+'?recursive=1'],R,network=True));assert remote_tree['sha']==tree and not remote_tree['truncated'];treefiles={v['path']:v['sha'] for v in remote_tree['tree'] if v['type']=='blob'};local={str(p.relative_to(P)):hashlib.sha1(b'blob '+str(p.stat().st_size).encode()+b'\0'+p.read_bytes()).hexdigest() for p in P.rglob('*') if p.is_file()};assert treefiles==local
 critical=[R/n for n in paths]
 for i,p in enumerate(critical):
  endpoint=api+'/contents/'+urllib.parse.quote(str(p.relative_to(R)),safe='/')+'?ref='+commit;fresh=run(label+'-fresh-raw-'+str(i),['gh','api',endpoint,'-H','Accept: application/vnd.github.raw+json'],R,network=True);assert hashlib.sha256(fresh).hexdigest()==sha(p)
 assert git('clean','status','--porcelain')=='';proof={'status':'PASS','commit':commit,'parent':before,'branch':'POD_A_SALIENCY','all_changed_local_Git_bytes_checked':len(paths),'fresh_remote_phase_tree_blob_identities_checked':len(treefiles),'fresh_remote_raw_changed_files_checked':len(critical),'phase_tree_id':tree,'exact_file_sha256':selected,'verification_method':'EverychangedcommittedbyteSHA256matched; freshimmutableGitHubrecursivephaseMerkletreehasexactfilepaths/blobIDs; EverychangedpublicfilefreshimmutableGitHubrawHTTPbodySHA256matched; exactlocalGitbytesandfreshremotetreealsoverified.','completed_utc':now()};save(C/(label+'-DELIVERY.json'),proof);print('S10_PUBLICATION_VERIFIED',commit,len(paths),flush=True)
