from common7 import *
sys.path.insert(0,str(A/'code'))
from other_five_common import *
import joblib
from independent_math import reconstruct,metrics
checks=[]
for task in ['gue_tf_0','gue_splice_reconstructed']:
 uid='R5/'+task+'/final_norm/seed42';root=A/'probes'/uid;receipt=verify_seal(root);require(receipt['actual_optimizer_fits']==16 and receipt['producer_validation']=='PASS','Initial producer failure');model=joblib.load(root/'head.joblib');entry=next(u for u in read(C/'A07_EXECUTION_MANIFEST.json')['units'] if u['unit_id']==uid);base=joblib.load(check_ref(entry['identity']['original_base_head']));x=features('R5',task,'dev','final_norm');meta=metadata('R5',task,'dev');result=read(root/'RESULTS.json');probmax=0.;metricmax=0.
 with np.load(root/'dev_predictions.npz',allow_pickle=False) as z:
  pair(z,meta,classes_for(task))
  for policy,head in [('independent_refit',model),('fixed_original_base',base)]:
   p=reconstruct(head,x);probmax=max(probmax,float(np.max(np.abs(z[policy]-p))));ind,valid=metrics(meta['labels'],p,classes_for(task),np.ones((1,len(p))));require(valid.all(),'Initial metric invalid')
   for row in result['metrics']:
    if row['policy']==policy:metricmax=max(metricmax,abs(row['estimate']-float(ind[row['metric']][0])))
 require(probmax<=1e-10 and metricmax<=1e-12,'Initial saved-output gate failed');checks.append({'unit_id':uid,'producer_receipt_sha256':sha(root/'COMPLETE.json'),'probability_max_abs':probmax,'metric_max_abs':metricmax,'classes':classes_for(task).tolist(),'rows':len(meta['ids']),'groups':len(np.unique(meta['groups'])),'counts_as_ordinary_production_unit':True,'additional_refits':0})
put(C/'INITIAL_PRODUCTION_GATE.json',{'status':'PASS','checks':checks,'does_not_replace_A08_all_unit_independent_audit':True,'queue_released':'Remaining finite A07 units only','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()});print(json.dumps({'status':'PASS','units':2,'probability_max_abs':max(x['probability_max_abs'] for x in checks),'metric_max_abs':max(x['metric_max_abs'] for x in checks)}))
