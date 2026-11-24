"""Meaningful synthetic/metadata rejection, estimator math and crash-safety tests. No real forward/fit/score."""
from pathlib import Path
import sys,json,copy,tempfile,subprocess,os,ast,warnings
import numpy as np
from s05_contract import *
from s05_cpu import fit_call_producer,fit_call_auditor,parameter_digest,probability_unit
from inherited_metrics import point_metrics,bootstrap_metrics
from inherited_independent import metrics as independent_metrics,reconstruct
from inherited_fit import pipeline
C=Path(sys.argv[1]);cfg=load(C/'RUN_CONFIG.json');F=Path(cfg['frozen_root']);out=Path(cfg['artifacts_root'])/(sys.argv[2] if len(sys.argv)>2 else 'synthetic-readiness-tests-001');need(not out.exists(),'Preserve prior testattempt');out.mkdir();tests=[]
def reject(name,fn):
 try:fn()
 except (ValueError,FileNotFoundError,BlockingIOError,KeyError):tests.append({'case':name,'status':'PASS_REJECTED'});return
 raise AssertionError('Forbidden boundary accepted '+name)
def passed(name):tests.append({'case':name,'status':'PASS'})
# Fail closed before any sequence open or model import.
reject('test split rejected before data opening',lambda:scope(cfg,'candidate_01',splits=['test']));reject('other task rejected before opening',lambda:scope(cfg,'candidate_01',task='gue_tf_0'));reject('unknown candidate',lambda:scope(cfg,'candidate_10'));bad=copy.deepcopy(cfg);bad['candidates'][0]['alias']='other';reject('substituted candidate content scope',lambda:scope(bad,'candidate_01'));bad=copy.deepcopy(cfg);bad['representations'][16]='decoder.layers.15';reject('wrong zero-based layer16 mapping',lambda:scope(bad,'candidate_01'));bad=copy.deepcopy(cfg);bad['precision_contract']['feature_dtype']='float16';reject('unsupported precision/backend',lambda:scope(bad,'candidate_01'));reject('third readout policy',lambda:scope(cfg,'candidate_01',policies=['independent_refit','recentered']))
expected=[{'id':'SYNTHETIC_row0','label':0,'group':'synthetic0'},{'id':'SYNTHETIC_row1','label':1,'group':'synthetic1'}];arr={k:np.zeros((2,1920),np.float32) for k in KEYS};arr.update(ids=np.array([r['id'] for r in expected]),labels=np.array([0,1]),groups=np.array(['synthetic0','synthetic1']),split=np.array(['train']*2),task=np.array(['emp_H3']*2),lengths=np.array([4,5]),nll_sum=np.array([1,2],np.float32),n_tokens=np.array([3,4]));check_arrays(arr,expected,'train');passed('valid synthetic all26hook metadata')
for name,key,value in [('cohort roworder','ids',np.array(['SYNTHETIC_row1','SYNTHETIC_row0'])),('label/class association','labels',np.array([1,0])),('filler contamination','ids',np.array(['SYNTHETIC_row0','FILLER'])),('other-task array contamination','task',np.array(['emp_H3','gue_tf_0'])),('unsupported feature dtype','decoder_layer_0',np.zeros((2,1920),np.float64)),('nonfinite required feature','decoder_layer_0',np.full((2,1920),np.inf,np.float32)),('wrong LMtarget mask','n_tokens',np.array([4,5]))]:
 bad=dict(arr);bad[key]=value;reject(name,lambda b=bad:check_arrays(b,expected,'train'))
root=out/'atomic';root.mkdir();(root/'data.bin').write_bytes(b'SYNTHETIC incompletewrite');reject('incomplete file is not completion',lambda:verify_seal(root));put(root/'COMPLETE.json',{'status':'COMPLETE_UNVERIFIED','completion_written_last':True,'files':[]});reject('false completed receipt',lambda:verify_seal(root));(root/'COMPLETE.json').unlink();identity={'scope':'SYNTHETIC','input':'fixture1','source':'test-source-v1'};write_seal(root,identity,['data.bin']);verify_seal(root,identity,required=['data.bin']);passed('valid complete unit reused without producer callback');reject('changed source invalidates affected unit',lambda:verify_seal(root,{**identity,'source':'test-source-v2'}));verify_seal(root,identity,required=['data.bin']);passed('unaffected valid unit remains reusable');(root/'data.bin').write_bytes(b'X'*(root/'data.bin').stat().st_size);reject('same-size corrupt completed bytes rejected',lambda:verify_seal(root,identity,required=['data.bin'],full_hash=True))
# Real OS lock contention, child PID/start/boot identity and exit retained as synthetic evidence.
lock=out/'conflict.lock'
with exclusive(lock):
 code="import fcntl,sys,json,os;from pathlib import Path;f=open(sys.argv[1],'a');print(json.dumps({'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}),flush=True)\ntry:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\nexcept BlockingIOError:sys.exit(17)\nsys.exit(0)"
 result=subprocess.run([sys.executable,'-c',code,str(lock)],capture_output=True,text=True,timeout=15);need(result.returncode==17,'Concurrent writer was admitted');put(out/'LOCK_REJECTION_PROCESS.json',{'process':json.loads(result.stdout),'exit_status':result.returncode,'expected_rejection_exit':17,'stderr':result.stderr})
passed('conflicting writer rejected with actual OSlock')
# Construct a small real sealed chunk to exercise the production loader's duplicate/missing boundaries.
inputs=out/'inputs';inputs.mkdir();put(inputs/'emp_H3-train-metadata.json',expected);toy=copy.deepcopy(cfg);toy['inputs_root']=str(inputs);toy['cohorts']['train']={'rows':2,'ordered_metadata_sha256':digest(expected)};case=out/'SYNTHETIC_case';chunk=case/'features/train/chunk-0000';chunk.mkdir(parents=True);one={k:np.zeros((1,1920),np.float32) for k in KEYS};one.update(ids=np.array(['SYNTHETIC_row0']),labels=np.array([0]),groups=np.array(['synthetic0']),nll_sum=np.array([1],np.float32),n_tokens=np.array([3]))
with (chunk/'features_and_lm.npz').open('wb') as f:np.savez(f,**one)
put(chunk/'RESOURCE.json',{'synthetic':True});write_seal(chunk,{'synthetic':True},['features_and_lm.npz','RESOURCE.json']);base={'cohort_sha256':digest(expected),'task':'emp_H3','split':'train','source_identity_sha256':'synthetic','chunks':[{'first':0,'stop':1,'relative_root':'features/train/chunk-0000','seal_sha256':sha(chunk/'COMPLETE.json')}]};put(case/'features/train/INDEX.json',base);reject('missing chunk denominator',lambda:load_layer(case,toy,'train','decoder_layer_0'));base['chunks']*=2;put(case/'features/train/INDEX.json',base);reject('duplicate noncontiguous chunk',lambda:load_layer(case,toy,'train','decoder_layer_0'))
changed=out/'changed';changed.mkdir();(changed/'dev_resampling.npz').write_bytes(b'SYNTHETIC wrongdrawbytes');reject('altered draw identity before array opening',lambda:draw_weights(cfg,changed));seed=42;(changed/'folds_seed42.json').write_text('[]');reject('changed saved fold identity',lambda:fold_indices(cfg,seed,[],changed));panel=load(F/'H3_AUDIT_SUBSET.json')['units'];valid={(z['r'],z['s']) for z in panel if z['c']=='candidate_01'};key=next((r,s) for r in HOOKS for s in SEEDS if (r,s) not in valid);reject('unfrozen audit replacement',lambda:audit_membership(panel,'candidate_01',*key))
# Missing/replaced fixed head must fail before any feature opening.
lookup=planned(C);temp=out/'wrong_fixed';temp.write_bytes(b'SYNTHETIC bogushead');forbad=copy.deepcopy(cfg)
for r in forbad['fixed_heads']:
 if r['representation']=='decoder.layers.0' and r['cv_seed']==42:r['path']=str(temp)
reject('fixed original head replacement before features/predictions',lambda:probability_unit(forbad,'candidate_01','decoder.layers.0',42,'synthetic',out/'no_features',lookup,'fixed_original_base',out/'no_heads'))
# Small unmistakably synthetic estimator/metric fixtures. No production data or draws are used.
x=np.array([[float(i%5),float(i%7),float(i%3),float(i)] for i in range(36)],dtype=np.float32);y=np.array([i%2 for i in range(36)]);model=pipeline(1,2000);model.fit(x,y);p=model.predict_proba(x);direct=reconstruct(model,x);strict_residual(direct,p,1e-10,'SYNTHETIC_direct_float32_probability');passed('independent float32-preserving scaler/linear/logistic math');weights=np.array([np.ones(36),np.array([1+(i%3) for i in range(36)]),np.array([2 if i%2==0 else 0 for i in range(36)])],dtype=np.float64);prod,mask=bootstrap_metrics(y,p,np.array([0,1]),weights);ind,imask=independent_metrics(y,direct,np.array([0,1]),weights);need(np.array_equal(mask,imask) and mask.tolist()==[True,True,False],'Class-completeness invalidmask mismatch');points,_=point_metrics(y,p,np.array([0,1]));ip,ipvalid=independent_metrics(y,direct,np.array([0,1]),np.ones((1,36)))
for name in prod:strict_residual(prod[name][mask],ind[name][mask],1e-12,'SYNTHETIC_'+name+'_draws');strict_residual(np.array([points[name]]),ip[name],1e-12,'SYNTHETIC_'+name+'_point');strict_residual(np.quantile(prod[name][mask],[.025,.975]),np.percentile(ind[name][mask],[2.5,97.5],method='linear'),1e-12,'SYNTHETIC_'+name+'_CI')
passed('independent five-metric point/draw/linearCI math andmissingclass mask')
# Separate actual synthetic full-fit paths validate serialization/reuse and audit constructor parity.
ident={'kind':'SYNTHETIC_fit','input':digest(x.tolist()),'label':digest(y.tolist())};a,atr,_=fit_call_producer(out/'fit_producer',ident,x,y,1,(x,y));b,btr,_=fit_call_auditor(out/'fit_auditor',ident,x,y,1,(x,y));strict_residual(a.predict_proba(x),b.predict_proba(x),1e-10,'SYNTHETIC_audit_repeat');need(parameter_digest(a)==parameter_digest(b),'Synthetic estimator math mismatch');_,_,reused=fit_call_producer(out/'fit_producer',ident,x,y,1,(x,y));need(reused,'Completed syntheticoptimizer reran');passed('separate producer/auditor fitting and completed optimizer reuse')
# Exercise exact retry limits and persistent-failure sealing with tiny synthetic real estimators.
from sklearn.pipeline import Pipeline
from sklearn.exceptions import ConvergenceWarning
original_fit=Pipeline.fit;observed=[]
def require_retry(self,xx,yy,*args,**kwargs):
 observed.append((self[-1].max_iter,self[-1].C,digest(np.asarray(xx).tolist()),digest(np.asarray(yy).tolist())));result=original_fit(self,xx,yy,*args,**kwargs)
 if self[-1].max_iter==2000:warnings.warn('SYNTHETIC convergence retry boundary',ConvergenceWarning)
 return result
try:
 Pipeline.fit=require_retry;_,retry_trace,_=fit_call_producer(out/'fit_retry',{'scope':'SYNTHETIC_retry'},x,y,1,(x,y));need([r['max_iter'] for r in retry_trace['attempts']]==[2000,10000] and len(observed)==2 and observed[0][1:]==observed[1][1:],'Retry changed data/C or limits');passed('convergence retry uses exact same TRAIN inputs C and2000then10000')
 def always_warn(self,xx,yy,*args,**kwargs):
  result=original_fit(self,xx,yy,*args,**kwargs);warnings.warn('SYNTHETIC persistent convergence failure',ConvergenceWarning);return result
 Pipeline.fit=always_warn
 try:fit_call_producer(out/'fit_persistent_failure',{'scope':'SYNTHETIC_persistent'},x,y,1)
 except RuntimeError:pass
 else:raise AssertionError('Persistent convergence falsely completed')
 need(not (out/'fit_persistent_failure/COMPLETE.json').exists() and len(load(out/'fit_persistent_failure/ATTEMPTS.partial.json'))==2,'Failedconvergence evidence lost or completed');passed('persistent convergence preserves both attempts and cannot seal complete')
finally:Pipeline.fit=original_fit

# Static import/dispatch inspection: historical main is never imported by executable adapters.
for name in ['s05_gpu.py','s05_cpu.py','s05_verify.py']:
 tree=ast.parse((Path(__file__).parent/name).read_text());imports=[n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)];need('historical_h3_followup_SOURCE_ONLY' not in imports and 'h3_followup' not in imports,'Historical monolithic import leaked')
passed('adapter import graph excludes historical test-enabled main')
report={'schema_version':'s05-synthetic-tests-v1','status':'PASS','tests':tests,'count':len(tests),'fixtures':'SYNTHETIC_only,36rows4features, manuallyspecifiedweightvectors; no production outcomes/model/GPU/drawgeneration','real_H3_fits_or_forwards':0,'executed_source_sha256':{p.name:sha(p) for p in Path(__file__).parent.glob('*.py')}};put(out/'TEST_REPORT.json',report);print(json.dumps(report,indent=2),flush=True)
