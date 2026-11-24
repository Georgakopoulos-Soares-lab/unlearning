"""Restored-only original audit-selector saved-output panel; no refits or live fallback."""
from pathlib import Path
import sys,json,hashlib,time,resource
import numpy as np,joblib
from artifact_seals import *
from s08_shared import compare,parameter_hash,group_weights,MAP
from inherited_independent import reconstruct,metrics
from s08_index import assemble
from threadpoolctl import threadpool_limits

def run(root,alias):
    root=Path(root).resolve();need(Path(__file__).resolve()==root/'code/s08_recovery.py','Restored verifier source required');cfg=load(root/'control/RUN_CONFIG.json');source=load(root/'control/SOURCE_IDENTITY.json');need(sha(root/'control/RUN_CONFIG.json')==source['config_sha256'],'Restored config changed');need(sha(root/'control/CPU_ENVIRONMENT_LOCK.json')==cfg['cpu_runtime_lock_sha256'],'Restored runtime binding changed');need(str(Path(sys.executable).absolute())==cfg['cpu_runtime_python'],'Wrong qualified recovery runtime')
    for f in source['files']:need(sha(root/'code'/f['path'])==f['sha256'],'Restored code changed')
    need(sha(root/'control/RECOVERY_CONTRACT.json')==cfg['recovery_contract_sha256'],'Recovery panel changed');panel=load(root/'control/RECOVERY_CONTRACT.json')['panel'][alias];projections=load(root/'recovery-inputs/PROJECTION_BINDINGS.json')['records'];refs=load(root/'inputs/ORIGINAL_BASE_HEADS.json');checks=[];records=[];auditseen=set();cache={};start=time.monotonic()
    with threadpool_limits(limits=4):
        for selector in panel:
            t=selector['task'];rep=selector['representation'];s=selector['cv_seed'];pol=selector['policy'];key='final_norm' if rep=='decoder.final_norm' else 'decoder_layer_'+rep.rsplit('.',1)[1];rows=load(root/'inputs/s06'/(t+'-dev-metadata.json'));co=cfg['producer_config']['feature_config']['cohorts'][t]['dev'];need(digest(rows)==co['ordered_metadata_sha256'],'Restored row metadata changed');b=next(v for v in projections if (v['task'],v['representation'])==(t,rep));projection=root/'recovery-inputs'/b['relative_path'];need(sha(projection)==b['file_sha256'],'Restored projection changed')
            with np.load(projection,allow_pickle=False) as z:
                x=z['features'];y=z['labels'];classes=z['classes'];need(x.dtype==np.float32 and x.shape==(512,1920) and np.isfinite(x).all() and hashlib.sha256(x.tobytes()).hexdigest()==b['matrix_value_sha256'],'Wrong restored feature values');need(z['ids'].tolist()==[v['id'] for v in rows] and y.tolist()==[v['label'] for v in rows] and z['groups'].tolist()==[v['group'] for v in rows] and classes.tolist()==co['class_order'],'Restored feature class/row/group association changed')
            if t not in cache:
                d=cfg['producer_config']['feature_config']['draws'][t];path=root/'inputs/s06'/d['relative_path'];need(sha(path)==d['file_sha256'],'Restored draw changed');names=sorted({v['group'] for v in rows});lookup={v:i for i,v in enumerate(names)};inv=np.array([lookup[v['group']] for v in rows])
                with np.load(path,allow_pickle=False) as z:
                    draws=z['group_draws'];need(z['ids'].tolist()==[v['id'] for v in rows] and z['group_names'].tolist()==names and np.array_equal(z['row_groups'],inv) and int(z['seed'])==20261103 and draws.dtype==np.int32 and draws.shape==(2000,len(names)) and hashlib.sha256(draws.tobytes()).hexdigest()==d['draw_array_C_order_bytes_sha256'],'Restored draw mapping/array identity changed');cache[t]=group_weights(draws,inv,len(names))
            pr=root/'producer/tasks'/t/'probabilities'/key/('seed'+str(s))/pol;verify_seal(pr,required=['predictions.npz','draws.npz','METRICS.json'],restored=True);m=load(pr/'METRICS.json');need(m['identity']['planned_spec_id']==selector['planned_prediction_spec_id'] and m['identity']['source_identity_sha256']==cfg['producer_source_identity_sha256'] and m['identity']['policy']==pol,'Restored prediction identity changed')
            if pol=='independent_refit':head=root/'producer/tasks'/t/'production'/key/('seed'+str(s))/'head.joblib'
            else:
                ref=next(v for v in refs if (v['task'],v['representation'],v['cv_seed'])==(t,rep,s));head=root/'inputs'/ref['relative_path'];need(sha(head)==ref['head_sha256'],'Restored original base changed')
            need(sha(head)==m['identity']['head_sha256'],'Restored prediction head changed');model=joblib.load(head);need(model[-1].classes_.tolist()==classes.tolist() and parameter_hash(model)==m['identity']['head_parameter_content_sha256'],'Restored model classes/parameters changed')
            with np.load(pr/'predictions.npz',allow_pickle=False) as z:
                need(z['ids'].tolist()==[v['id'] for v in rows] and np.array_equal(z['labels'],y) and z['groups'].tolist()==[v['group'] for v in rows] and np.array_equal(z['classes'],classes),'Restored saved prediction associations changed');p=z['probabilities'];checks.append(compare(reconstruct(model,x),p,1e-10,selector['planned_prediction_spec_id']))
            points,pvalid=metrics(y,p,classes,np.ones((1,len(y))));dist,valid=metrics(y,p,classes,cache[t]);need(bool(pvalid[0]),'Undefined recovery point');need(len(m['metrics'])==5,'Missing recovery metrics')
            with np.load(pr/'draws.npz',allow_pickle=False) as z:
                for row in m['metrics']:
                    cr=row['canonical_metric'];name=cr['metric'];d=dist[MAP[name]];mask=valid&np.isfinite(d);need(np.array_equal(mask,z[name+'_valid']) and np.isnan(d[~mask]).all() and np.isnan(z[name][~mask]).all(),'Restored validity changed');need(cr['bootstrap_valid']==int(mask.sum()) and cr['bootstrap_invalid']==int((~mask).sum()) and cr['bootstrap_attempted']==2000 and cr['sample_count']==512 and cr['group_count']==co['groups'],'Restored denominator changed');checks.append(compare(points[MAP[name]],[cr['estimate']],1e-12,name+'_point'))
                    if mask.any():checks+=[compare(d[mask],z[name][mask],1e-12,name+'_draw'),compare(np.percentile(d[mask],[2.5,97.5],method='linear'),[cr['ci_low'],cr['ci_high']],1e-12,name+'_CI')]
                    else:need(cr['ci_low'] is None and cr['ci_high'] is None and cr['missing_reason'],'Undefined recovery interval not explicit')
            if pol=='independent_refit':
                ar=root/'candidate/audits'/t/key/('seed'+str(s));verify_seal(ar,required=['head.joblib','PARAMETERS.npz','AUDIT.json','CV_INDEX.json'],restored=True);audit=load(ar/'AUDIT.json');need(audit['status']=='PASS' and audit['identity']['planned_spec_id']==selector['planned_audit_spec_id'] and audit['identity']['source_identity_sha256']==source['verifier_source_identity_sha256'],'Restored audit identity changed');am=joblib.load(ar/'head.joblib');need(parameter_hash(am)==audit['parameter_content_sha256'],'Restored audit parameters changed');checks.append(compare(reconstruct(am,x),p,1e-10,'restored_fresh_audit_vs_S07_'+selector['planned_audit_spec_id']));producer=load(head.parent/'SUMMARY.json');need(audit['selected_C']==producer['selected_C'],'Restored selected C changed')
                for i in range(3):checks.append(compare(audit['CV'][i]['fold_AUROC'],producer['CV'][i]['fold_AUROC'],1e-12,'restored_saved_full_CV_C'+str(i)))
                auditseen.add(selector['planned_audit_spec_id'])
            records.append({**selector,'status':'PASS','metric_vectors':5})
    expected=load(root/'control/RECOVERY_CONTRACT.json')['panel'][alias];need(len(records)==len(expected) and len(auditseen)*2==len(records),'Declared restored panel incomplete');regen=root/'regenerated';assemble(root/'candidate',root/'control/CASE_EXPECTED.jsonl',root/'control/CASE_PRODUCER.jsonl',root/'control/ORIGINAL_AUDIT_KEYS.json',alias,source['verifier_source_identity_sha256'],regen);mapping={}
    for n in ['ELIGIBLE_INDEX.jsonl','COVERAGE.json','HEAD_PROVENANCE.json','AUDIT_INDEX.json']:need(sha(regen/n)==sha(root/'candidate/eligible'/n),'Restored eligibility mapping mismatch '+n);mapping[n]=sha(regen/n)
    result={'schema_version':'s08-declared-private-recovery-v1','status':'PASS','alias':alias,'restored_saved_prediction_paths':len(records),'restored_marginal_vectors':len(records)*5,'attempted_draw_values':len(records)*10000,'fresh_audit_heads_reconstructed':len(auditseen),'new_CV_calls':0,'max_probability_abs_residual':max(x['max_abs_residual'] for x in checks if x['atol']==1e-10),'max_metric_draw_CI_abs_residual':max(x['max_abs_residual'] for x in checks if x['atol']==1e-12),'probability_atol':1e-10,'metric_atol':1e-12,'rtol':0,'checks':checks,'records':records,'regenerated_mappings':mapping,'producer_path_fallback':False,'runtime_scope':'Existing qualified CPU runtime; exact restored selected features/scalers/heads/savedoutputs and allnewS08bytes. No freshCV/GPU/nativeweight/cleanruntime recreation.','wall_seconds':time.monotonic()-start,'peak_RSS_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024};need(result['peak_RSS_bytes']<=8*1024**3,'Recovery RSS limit exceeded');put(root/'NUMERICAL_RECOVERY.json',result);print('S08_RESTORED_NUMERICAL_AND_MAPPING_PANEL_PASS',alias,len(records),len(auditseen),flush=True);return result

if __name__=='__main__':run(sys.argv[1],sys.argv[2])
