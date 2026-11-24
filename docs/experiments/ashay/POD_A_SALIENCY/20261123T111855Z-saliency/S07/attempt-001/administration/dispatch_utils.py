from pathlib import Path
import json,sys,hashlib
from ops import C,A,save,now
sys.path.insert(0,str(A/'code'));from artifact_seals import sha,load,need,verify_seal

def complete(alias,t,rep,seed):
 key='final_norm' if rep=='decoder.final_norm' else 'decoder_layer_'+rep.rsplit('.',1)[1];case=A/'candidates'/alias/'tasks'/t;done=case/'unit-completions'/(key+'-seed'+str(seed)+'.json')
 if not done.exists():return False
 r=load(done);source=load(C/'SOURCE_IDENTITY.json');need(r['status']=='COMPLETE_UNVERIFIED' and r['producer_status']=='PASS' and r['source_identity_sha256']==source['producer_source_identity_sha256'] and (r['alias'],r['task'],r['representation'],r['cv_seed'])==(alias,t,rep,seed),'Completed-unit source/selector changed');head=case/'production'/key/('seed'+str(seed));need(sha(head/'COMPLETE.json')==r['head_receipt_sha256'],'Completed head seal changed');verify_seal(head,required=['head.joblib','PARAMETERS.npz','SUMMARY.json','CV_INDEX.json'])
 for policy in ['independent_refit','fixed_original_base']:verify_seal(case/'probabilities'/key/('seed'+str(seed))/policy,required=['predictions.npz','draws.npz','METRICS.json'])
 verify_seal(case/'fixed-applications'/key/('seed'+str(seed)),required=['APPLICATION.json']);return True
