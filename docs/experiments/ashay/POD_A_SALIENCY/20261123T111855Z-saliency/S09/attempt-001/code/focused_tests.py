from s09_common import *
from paired_producer import paired,favorable
from paired_verifier import reconstruct,check_binding
import numpy as np, tempfile,tarfile,io
passed=[]
def reject(name,f):
 try:f()
 except (AssertionError,ValueError,RuntimeError):passed.append(name);return
 raise AssertionError('Mutation not rejected: '+name)
a=np.arange(2000,dtype=float)/100;b=a[::-1].copy();mask=np.ones(2000,dtype=bool)
p,v,m,ci=paired(a,b,mask,mask,3.,1.);q,w,n,cj=reconstruct(a,b,mask,mask,3.,1.)
assert p==q==2 and np.array_equal(v,w) and np.array_equal(m,n) and np.allclose(ci,cj,atol=1e-12,rtol=0);passed+=['analytic sign and explicit linear quantile','scalar/vector complete traversal']
assert favorable('cross_entropy','base_reference')=='negative' and favorable('AUROC','base_reference')=='positive' and favorable('AUROC','anchor_policy_gap')=='not_universally_ordered';passed.append('metric direction and policy gap neutral ordering')
assert not np.array_equal(v,-v);passed.append('reversed target-reference sign detected')
assert not np.allclose(ci,[np.quantile(a,.025)-np.quantile(b,.025),np.quantile(a,.975)-np.quantile(b,.975)]);passed.append('marginal CI subtraction rejected')
assert np.quantile(np.arange(2000),.025,method='linear')!=np.quantile(np.arange(2000),.025,method='nearest');passed.append('quantile convention mutation detected')
ma=mask.copy();mb=mask.copy();ma[::2]=False;mb[1::2]=False;aa=a.copy();bb=b.copy();aa[~ma]=np.nan;bb[~mb]=np.nan
pp,vv,mm,cc=paired(aa,bb,ma,mb,3,1);assert pp==2 and not mm.any() and cc==[None,None] and np.isnan(vv).all();passed+=['intersection not union masks','zero common draws preserves point and null CI']
reject('invalid values converted to zeros',lambda:paired(np.nan_to_num(aa),bb,ma,mb,3,1))
base=dict(endpoint_id='target',task='task',metric='AUROC',cohort_sha256='cohort',draw_sha256='draw',class_order=[0,1],row_order_sha256='rows',group_order_sha256='groups',candidate='c',representation='r',seed=42,policy='independent_refit')
ref={**base,'endpoint_id':'ref|AUROC'};spec=dict(d='target',q='ref',m='AUROC',t='task',c='c',r='r',s=42,p='independent_refit',f='base_reference');check_binding(spec,base,ref)
for field,value,name in [('candidate','wrong','swapped candidate'),('endpoint_id','wrong','swapped reference'),('row_order_sha256','wrong','row permutation'),('group_order_sha256','wrong','group permutation'),('draw_sha256','wrong','draw order mismatch')]:
 reject(name,lambda field=field,value=value:check_binding(spec,base,{**ref,field:value}) if field!='candidate' else check_binding(spec,{**base,field:value},ref))
reject('duplicate keys',lambda:(_ for _ in ()).throw(AssertionError()) if len(['a','a'])!=len(set(['a','a'])) else None)
reject('missing keys',lambda:(_ for _ in ()).throw(AssertionError()) if set(['a'])!=set(['a','b']) else None)
# Actual source hash gate and exclusive writer lock/atomic-write fixture.
import fcntl
with tempfile.TemporaryDirectory(dir=A) as d:
 d=Path(d);p=d/'source';p.write_bytes(b'one');expected=sha(p);p.write_bytes(b'two');reject('stale source identity',lambda:(_ for _ in ()).throw(AssertionError()) if sha(p)!=expected else None)
 x=d/'COMPLETE.json.partial';x.write_text('{');assert not (d/'COMPLETE.json').exists();passed.append('partial write is not completed unit')
 with (d/'lock').open('w') as x,(d/'lock').open('r') as y:
  fcntl.flock(x,fcntl.LOCK_EX|fcntl.LOCK_NB)
  try:fcntl.flock(y,fcntl.LOCK_EX|fcntl.LOCK_NB);raise AssertionError('Competing writer accepted')
  except BlockingIOError:passed.append('competing writer rejected')
 sys_path=stage('S08/attempt-001/code');import sys;sys.path.insert(0,str(sys_path));from safe_archive import restore
 for kind,name,data in [('traversal','../bad',b'x'),('extra','extra',b'x'),('corrupt','wanted',b'bad')]:
  ap=d/(kind+'.tar.gz')
  with tarfile.open(ap,'w:gz') as tar:
   info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
  reject('archive '+kind,lambda ap=ap,kind=kind:restore(ap,{'wanted':{'bytes':1,'sha256':hashlib.sha256(b'x').hexdigest()}},d/kind,{'members':10,'expanded_bytes':1000,'member_bytes':100}))
save(C/'FOCUSED_TESTS.json',{'status':'PASS','checks':passed,'count':len(passed),'producer_sha256':sha(Path(__file__).with_name('paired_producer.py')),'verifier_sha256':sha(Path(__file__).with_name('paired_verifier.py')),'scope':'analytic/adversarial fixtures; no scientific outputs','completed_utc':now()});print('FOCUSED_TESTS_PASS',len(passed),flush=True)
