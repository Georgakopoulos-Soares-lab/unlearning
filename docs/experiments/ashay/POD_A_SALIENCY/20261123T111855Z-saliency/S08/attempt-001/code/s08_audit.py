"""Original S04 full-CV audit panel only. Separate fitting and output identity."""
from s08_shared import *
from inherited_fit import pipeline
from inherited_independent import reconstruct
from sklearn.metrics import roc_auc_score
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits
import joblib,warnings,time,resource

def score(y,p,classes):
    return float(roc_auc_score(y,p[:,1]) if len(classes)==2 else roc_auc_score(y,p,labels=classes,multi_class='ovr',average='macro'))

def call(root,ident,x,y,C,classes,validation=None):
    if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['model.joblib','TRACE.json']);return joblib.load(root/'model.joblib'),load(root/'TRACE.json')
    need(not root.exists(),'Incomplete audit call preserved');root.mkdir(parents=True);attempts=[]
    for limit in [2000,10000]:
        model=pipeline(C,limit);wall=time.monotonic();cpu=time.process_time()
        with warnings.catch_warnings(record=True) as found:warnings.simplefilter('always');model.fit(x,y)
        attempts.append({'max_iter':limit,'n_iter':model[-1].n_iter_.tolist(),'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in found],'wall_seconds':time.monotonic()-wall,'CPU_seconds':time.process_time()-cpu});put(root/'ATTEMPTS.partial.json',attempts);need(all(issubclass(w.category,ConvergenceWarning) for w in found),'Unapproved audit fit warning')
        if not found:break
    else:raise ValueError('Persistent audit convergence warning after allowed fresh10000retry')
    need(model[-1].classes_.tolist()==classes and model[0].transform(x[:1]).dtype==np.float32,'Audit class/scaler precision changed')
    tmp=root/'model.joblib.partial';joblib.dump(model,tmp);os.replace(tmp,root/'model.joblib');need(parameter_hash(joblib.load(root/'model.joblib'))==parameter_hash(model),'Audit serialization changed parameters')
    tr={'schema_version':'s08-audit-call-v1','status':'COMPLETE_UNVERIFIED','identity':ident,'C':C,'fit_rows':len(y),'fit_features_sha256':hashlib.sha256(x.tobytes()).hexdigest(),'fit_labels_sha256':hashlib.sha256(y.tobytes()).hexdigest(),'attempts':attempts,'validation_AUROC':None if validation is None else score(validation[1],model.predict_proba(validation[0]),np.array(classes)),'parameter_content_sha256':parameter_hash(model),'TRAIN_only':True,'no_dev_selection':True};put(root/'TRACE.json',tr);write_seal(root,ident,['model.joblib','TRACE.json'],{'initial_calls':1,'actual_calls':len(attempts)});return model,tr

def audit(c,a,t,r,s):
    cfg,v=ready(c,a,t,r,s);panel=[x for x in audit_keys(str(c)) if x['k']=='audit_refit' and (x['c'],x['t'],x['r'],x['s'])==(a,t,r,s)];need(len(panel)==1,'Not an original frozen audit selector');unit=panel[0];base=Path(cfg['artifacts_root'])/'candidates'/a;root=base/'audits'/t/key(r)/('seed'+str(s));ident={'phase':'S08','planned_spec_id':unit['id'],'producer_head_spec_id':unit['d'],'alias':a,'task':t,'representation':r,'cv_seed':s,'source_identity_sha256':cfg['_source'],'runtime_lock_sha256':cfg['cpu_runtime_lock_sha256'],'protocol_semantic_sha256':cfg['protocol_semantic_sha256'],'candidate_content_sha256':v['model_tensor_content_sha256']};start=time.monotonic();cpu=time.process_time()
    with exclusive(base/'locks'/('audit-'+t+'-'+key(r)+'-seed'+str(s)+'.lock')),threadpool_limits(limits=4):
        if (root/'COMPLETE.json').exists():verify_seal(root,ident,required=['head.joblib','PARAMETERS.npz','AUDIT.json','CV_INDEX.json']);return load(root/'AUDIT.json')
        root.mkdir(parents=True,exist_ok=True);x,y,ids=matrix(str(c),a,t,r,'train');folds=fold_indices(cfg,t,s,ids);classes=cfg['producer_config']['feature_config']['cohorts'][t]['train']['class_order'];calls=[];choices=[];keys=[z for z in audit_keys(str(c)) if z['k']=='audit_optimizer_call' and z['d']==unit['id']];need(len(keys)==16,'Audit call denominator changed')
        for j,C in enumerate([.1,1.,10.]):
            scores=[]
            for k,(tr,va) in enumerate(folds):
                row=next(z for z in keys if z.get('j')==j and z.get('fold')==k);cr=root/'cv'/('C'+str(j)+'-fold'+str(k));need(sorted(set(y[tr].tolist()))==sorted(set(y[va].tolist()))==classes,'Audit fold required class missing');ci={**ident,'planned_spec_id':row['id'],'audit_parent_spec_id':unit['id'],'C':C,'fold':k,'TRAIN_ids_sha256':digest([ids[i] for i in tr]),'validation_ids_sha256':digest([ids[i] for i in va])};_,trace=call(cr,ci,x[tr],y[tr],C,classes,(x[va],y[va]));scores.append(trace['validation_AUROC']);calls.append({'planned_spec_id':row['id'],'relative_root':str(cr.relative_to(root)),'receipt_sha256':sha(cr/'COMPLETE.json'),'actual_calls':len(trace['attempts'])});print('S08_AUDIT_CALL_SEALED',a,t,r,s,j,k,flush=True)
            choices.append({'C':C,'fold_AUROC':scores,'mean_fold_AUROC':float(np.mean(scores))})
        selected=choose(choices);final=next(z for z in keys if z.get('j') is None and z.get('fold') is None);cr=root/'final';model,trace=call(cr,{**ident,'planned_spec_id':final['id'],'audit_parent_spec_id':unit['id'],'C':selected,'fold':None,'TRAIN_ids_sha256':digest(ids)},x,y,selected,classes);calls.append({'planned_spec_id':final['id'],'relative_root':'final','receipt_sha256':sha(cr/'COMPLETE.json'),'actual_calls':len(trace['attempts'])});(root/'head.joblib').write_bytes((cr/'model.joblib').read_bytes());np.savez(root/'PARAMETERS.npz',scaler_mean=model[0].mean_,scaler_scale=model[0].scale_,scaler_var=model[0].var_,coef=model[-1].coef_,intercept=model[-1].intercept_,classes=model[-1].classes_)
        prod=Path(cfg['producer_artifacts_root'])/'candidates'/a/'tasks'/t/'production'/key(r)/('seed'+str(s));verify_seal(prod,required=['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json']);p=load(prod/'SUMMARY.json');need(p['planned_spec_id']==unit['d'] and p['selected_C']==selected,'Audit selected-C/producer dependency mismatch');checks=[]
        for i in range(3):checks.append(compare(choices[i]['fold_AUROC'],p['CV'][i]['fold_AUROC'],1e-12,'full_CV_C'+str(i)))
        dev,_,_=matrix(str(c),a,t,r,'dev');actual=reconstruct(model,dev);predroot=Path(cfg['producer_artifacts_root'])/'candidates'/a/'tasks'/t/'probabilities'/key(r)/('seed'+str(s))/'independent_refit'
        with np.load(predroot/'predictions.npz',allow_pickle=False) as z:checks.append(compare(actual,z['probabilities'],1e-10,'fresh_audit_vs_saved_producer_probability'))
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024;need(rss<=cfg['worker_RSS_limit_bytes'],'Audit worker RSS exceeded');report={'schema_version':'s08-fresh-full-CV-audit-v1','status':'PASS','identity':ident,'selected_C':selected,'CV':choices,'initial_optimizer_calls':16,'actual_optimizer_calls':sum(z['actual_calls'] for z in calls),'retries':sum(z['actual_calls']-1 for z in calls),'parameter_content_sha256':parameter_hash(model),'producer_parameter_content_sha256':p['parameter_content_sha256'],'parameter_content_exactly_equal':parameter_hash(model)==p['parameter_content_sha256'],'producer_receipt_sha256':sha(prod/'COMPLETE.json'),'producer_head_sha256':sha(prod/'head.joblib'),'audit_head_sha256':sha(root/'head.joblib'),'checks':checks,'acceptance':'OriginalS05qualifiedselectedCexact,CV_AUROC_atol1e-12,devprob_atol1e-10,rtol0; serializationbyteequalitynotrequired.','audit_did_not_replace_producer':True,'dev_used_for_selection':False,'wall_seconds':time.monotonic()-start,'CPU_process_seconds':time.process_time()-cpu,'peak_RSS_bytes':rss,'owned_process':process_identity()};put(root/'AUDIT.json',report);put(root/'CV_INDEX.json',{'calls':calls});write_seal(root,ident,['head.joblib','PARAMETERS.npz','AUDIT.json','CV_INDEX.json'],{'audit_refits':1,'initial_calls':16,'actual_calls':report['actual_optimizer_calls']});print('S08_FULL_CV_AUDIT_PASS',a,t,r,s,flush=True);return report
