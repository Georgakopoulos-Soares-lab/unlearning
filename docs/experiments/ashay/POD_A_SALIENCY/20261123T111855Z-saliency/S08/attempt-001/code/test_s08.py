"""Analytic/adversarial fixtures for the actual S08 paths, not a production-grid test."""
from pathlib import Path
import sys,json,types,io,tarfile,hashlib,warnings,inspect,ast
from unittest.mock import patch
import numpy as np
from s08_shared import *
from s08_verify import check_identity
from inherited_independent import metrics,reconstruct
from safe_archive import restore
import s08_audit
from sklearn.preprocessing import StandardScaler

ROOT=Path(sys.argv[1]);ROOT.mkdir(exist_ok=False,parents=True);results=[]
def rejected(fn):
    try:fn()
    except (ValueError,AssertionError,FileNotFoundError,BlockingIOError):return
    raise AssertionError('Corruption unexpectedly accepted')
def test(name,fn):
    try:fn();results.append({'case':name,'status':'PASS'})
    except Exception as e:results.append({'case':name,'status':'FAIL','error':repr(e)});raise

def binary():
    y=np.array([0,0,1,1]);p=np.array([[.9,.1],[.5,.5],[.5,.5],[.1,.9]]);m,v=metrics(y,p,np.array([0,1]),np.ones((1,4)));assert v.tolist()==[True]
    for k,x in [('auroc',7/8),('average_precision',5/6),('accuracy',3/4),('balanced_accuracy',3/4),('classification_cross_entropy',-(2*np.log(.9)+2*np.log(.5))/4)]:assert abs(m[k][0]-x)<1e-15
    rejected(lambda:compare(p[:,::-1],p,1e-10,'swapped class probability columns'))
test('binary analytic ranks/AP/ties/threshold and swapped columns',binary)

def multi():
    p=np.full((3,3),.1);np.fill_diagonal(p,.8);m,v=metrics(np.array([0,1,2]),p,np.arange(3),np.array([[1,1,1],[1,1,0]],float));assert v.tolist()==[True,False]
    for k in ['auroc','average_precision','accuracy','balanced_accuracy']:assert m[k][0]==1
    assert abs(m['classification_cross_entropy'][0]+np.log(.8))<1e-15 and all(np.isnan(x[1]) for x in m.values())
with warnings.catch_warnings():warnings.simplefilter('ignore',RuntimeWarning);test('multiclass analytic macro metrics and missing-class masks',multi)

def extreme():
    y=np.array([0,1]);p=np.array([[1.,0.],[0.,1.]]);m,v=metrics(y,p,np.array([0,1]),np.ones((1,2)));assert m['classification_cross_entropy'][0]==-np.log(1-np.finfo(float).eps)
    tied=np.full((2,2),.5);m,_=metrics(y,tied,np.array([0,1]),np.ones((1,2)));assert (m['auroc'][0],m['average_precision'][0],m['accuracy'][0])==(.5,.5,.5)
test('extreme probability clipping and exact half threshold',extreme)

def precision():
    x=np.array([[10000.003,.1211212],[9999.998,-.413213]],np.float32);sc=StandardScaler();sc.mean_=np.array([10000.0002,.001122]);sc.scale_=np.array([.100003,.713]);sc.var_=sc.scale_**2;sc.n_features_in_=2;head=types.SimpleNamespace(classes_=np.array([0,1]),coef_=np.array([[.27,-.57]]),intercept_=np.array([.13]));pipe=[sc,head]
    from scipy.special import expit
    expected=expit((sc.transform(x)@head.coef_.T+head.intercept_)[:,0]);actual=reconstruct(pipe,x);compare(actual[:,1],expected,0,'qualifiedF32scaler');bad=expit((((x.astype(float)-sc.mean_)/sc.scale_)@head.coef_.T+head.intercept_)[:,0]);assert np.max(np.abs(bad-expected))>1e-10
    rejected(lambda:compare(np.column_stack([1-bad,bad]),actual,1e-10,'wrong transform precision'));old=sc.mean_.copy();sc.mean_[0]+=.01;rejected(lambda:compare(reconstruct(pipe,x),actual,1e-10,'corrupt scaler'));sc.mean_=old
test('float32 scaler arithmetic and wrong precision/parameter detection',precision)

def chunk():
    rows=[{'id':'a','label':0,'group':'g0'},{'id':'b','label':1,'group':'g1'}];z={'ids':np.array(['a','b']),'labels':np.array([0,1]),'groups':np.array(['g0','g1']),'classes':np.array([0,1]),'task':np.array(['gue_tf_0']*2),'split':np.array(['dev']*2),'decoder_layer_0':np.zeros((2,1920),np.float32)};check_chunk(z,rows,[0,1],'gue_tf_0','dev','decoder.layers.0')
    for name,value in [('ids',np.array(['b','a'])),('classes',np.array([1,0])),('task',np.array(['wrong']*2)),('split',np.array(['train']*2)),('decoder_layer_0',np.zeros((2,1920),np.float64))]:
        bad={**z,name:value};rejected(lambda:check_chunk(bad,rows,[0,1],'gue_tf_0','dev','decoder.layers.0'))
test('actual feature adapter catches row permutation/classes/task/split/dtype',chunk)

def identities():
    fc={'cohorts':{'gue_tf_0':{'train':{'ordered_metadata_sha256':'tr'},'dev':{'ordered_metadata_sha256':'dv'}}},'folds':{'gue_tf_0':[{'cv_seed':42,'sha256':'fold'}]}};cfg={'protocol_semantic_sha256':'protocol','producer_source_identity_sha256':'source','cpu_runtime_lock_sha256':'runtime','producer_config':{'feature_config':fc}};v={'candidate_id':'c','model_tensor_content_sha256':'weights'};ident={'candidate_id':'c','candidate_content_sha256':'weights','task':'gue_tf_0','representation':'decoder.layers.0','cv_seed':42,'protocol_semantic_sha256':'protocol','source_identity_sha256':'source','cpu_runtime_lock_sha256':'runtime','feature_dtype':'float32','width':1920,'TRAIN_cohort_sha256':'tr','DEV_cohort_sha256':'dv','fold_sha256':'fold'};check_identity(ident,cfg,v,'gue_tf_0','decoder.layers.0',42)
    for k,value in [('candidate_content_sha256','other'),('task','gue_mouse_0'),('representation','decoder.final_norm'),('cv_seed',17),('source_identity_sha256','stale')]:rejected(lambda:check_identity({**ident,k:value},cfg,v,'gue_tf_0','decoder.layers.0',42))
    exact_keys(['a','b'],['a','b'])
    for bad in [['a','a'],['a'],['a','b','c']]:rejected(lambda:exact_keys(bad,['a','b']))
test('checkpoint/task/layer/seed/source and exact-key failures',identities)

def multiplicity():
    draws=np.array([[0,0,2],[1,2,2]]);inv=np.array([0,0,1,2]);w=group_weights(draws,inv,3);assert np.array_equal(w,[[2,2,0,1],[0,0,1,2]]) and np.array_equal(w[:,0],w[:,1]);rejected(lambda:group_weights(np.array([[0,1,3]]),inv,3));rejected(lambda:group_weights(np.array([[0,1]]),inv,3))
    p=np.array([[.8,.2],[.2,.8],[.3,.7],[.1,.9]]);y=np.array([0,1,1,1]);m,mask=metrics(y,p,np.array([0,1]),w);assert mask.tolist()==[True,False];rejected(lambda:need(np.array_equal(mask,np.array([True,True])),'Wrongmask'))
with warnings.catch_warnings():warnings.simplefilter('ignore',RuntimeWarning);test('shared splice-group multiplicity and independent mask rejection',multiplicity)

def intervals():
    d=np.array([0.,1.,2.,3.]);linear=np.percentile(d,[2.5,97.5],method='linear');assert np.allclose(linear,[.075,2.925],rtol=0,atol=1e-15);rejected(lambda:compare(np.percentile(d,[2.5,97.5],method='nearest'),linear,1e-12,'Wrongpercentile'))
    assert choose([{'C':10.,'mean_fold_AUROC':.8},{'C':1.,'mean_fold_AUROC':.8},{'C':.1,'mean_fold_AUROC':.8}])==.1
test('independent percentile endpoints and exact C tie behavior',intervals)

def seal_locks():
    p=ROOT/'partial';p.mkdir();put(p/'value.json',{'a':1});rejected(lambda:verify_seal(p));ident={'input':'i'};write_seal(p,ident,['value.json']);verify_seal(p,ident,required=['value.json']);rejected(lambda:verify_seal(p,{'input':'wrong'},required=['value.json']));put(p/'value.json',{'a':2});rejected(lambda:verify_seal(p,ident,required=['value.json'],full_hash=True))
    with exclusive(ROOT/'same.lock'):rejected(lambda:enter_lock(ROOT/'same.lock'))
def enter_lock(p):
    with exclusive(p):pass
test('partial writes, changed dependencies, corrupted bytes and competing writers',seal_locks)

def source():
    p=ROOT/'source';p.mkdir();(p/'code.py').write_text('a=1\n');put(p/'RUN_CONFIG.json',{'phase':'fixture'});cfg=load(p/'RUN_CONFIG.json');put(p/'SOURCE_IDENTITY.json',{'config_sha256':sha(p/'RUN_CONFIG.json'),'code_root':str(p),'files':[{'path':'code.py','sha256':sha(p/'code.py')}]});check_source(p,cfg);(p/'code.py').write_text('a=2\n');rejected(lambda:check_source(p,cfg))
test('actual source checker rejects stale implementation',source)

def archive():
    data=b'exact fixture';manifest={'a/value':{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}};limits={'members':3,'expanded_bytes':100,'member_bytes':100}
    def tar(name,items):
        path=ROOT/(name+'.tar.gz')
        with tarfile.open(path,'w:gz') as f:
            for n,b,kind in items:
                m=tarfile.TarInfo(n);m.type=kind;m.size=len(b) if kind==tarfile.REGTYPE else 0
                if kind!=tarfile.REGTYPE:m.linkname='a/value'
                f.addfile(m,io.BytesIO(b) if kind==tarfile.REGTYPE else None)
        return path
    good=tar('good',[('a/value',data,tarfile.REGTYPE)]);assert restore(good,manifest,ROOT/'good-restore',limits)['members']==1
    cases={'traversal':[('../value',data,tarfile.REGTYPE)],'absolute':[('/value',data,tarfile.REGTYPE)],'duplicate':[('a/value',data,tarfile.REGTYPE)]*2,'extra':[('a/value',data,tarfile.REGTYPE),('extra',b'1',tarfile.REGTYPE)],'corrupt':[('a/value',b'wrong fixture',tarfile.REGTYPE)],'symlink':[('a/value',b'',tarfile.SYMTYPE)],'hardlink':[('a/value',b'',tarfile.LNKTYPE)]}
    for n,items in cases.items():rejected(lambda:restore(tar(n,items),manifest,ROOT/(n+'-restore'),limits))
test('actual restoration rejects corrupt/extra/duplicate/traversal/link members',archive)

class FakeScaler:
    mean_=np.zeros(2);scale_=np.ones(2);var_=np.ones(2)
    def transform(self,x):return x.astype(np.float32)
class FakeHead:
    classes_=np.array([0,1]);coef_=np.zeros((1,2));intercept_=np.zeros(1);n_iter_=np.array([2])
class FakePipeline:
    def __init__(self,limit,mode):self.limit=limit;self.mode=mode
    def __getitem__(self,i):return FakeScaler() if i==0 else FakeHead()
    def fit(self,x,y):
        if self.mode=='persistent' or self.mode=='retry' and self.limit==2000:warnings.warn('fixture convergence',s08_audit.ConvergenceWarning)
        if self.mode=='other':warnings.warn('fixture other warning',UserWarning)
        return self
def retries():
    x=np.zeros((4,2),np.float32);y=np.array([0,1,0,1]);seen=[]
    def create(C,limit):seen.append(limit);return FakePipeline(limit,'retry')
    with patch.object(s08_audit,'pipeline',create):_,tr=s08_audit.call(ROOT/'retry',{'fixture':'retry'},x,y,.1,[0,1])
    assert seen==[2000,10000] and len(tr['attempts'])==2 and not tr['attempts'][-1]['warnings']
    for mode in ['persistent','other']:
        with patch.object(s08_audit,'pipeline',lambda C,n:FakePipeline(n,mode)):rejected(lambda:s08_audit.call(ROOT/mode,{'fixture':mode},x,y,.1,[0,1]))
    assert 'dev' not in inspect.signature(s08_audit.call).parameters
test('actual audit retry procedure permits only fresh convergence retry and preserves failures',retries)

put(ROOT/'TEST_REPORT.json',{'schema_version':'s08-adversarial-fixtures-v1','status':'PASS','cases':results,'scientific_fits':0,'synthetic_sklearn_fits':0,'warning_policy_exercised_with_fake_estimators':True,'scope':'Actual input/identity/group/numerical/seal/restore/audit-call functions; analytic rational/log expected values and adversarial corruptions. No production-grid or package self-test rerun.'});print('S08_FOCUSED_IMPLEMENTATION_CHECKS_PASS',len(results),flush=True)
