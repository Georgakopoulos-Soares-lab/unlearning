"""R5-approved finite endpoint caches; two numerical routes, no model forwards."""
from audit_common import *
from independent_math import metrics
from rank_crosscheck import bootstrap_metrics,point_metrics
from audit_units import residual
from portable_math8 import resolve,probabilities,pair,weights_from_draws
from functools import lru_cache
import csv,gzip,io,time

@lru_cache(None)
def bindings():
 b=read(C/'ENDPOINT_BINDINGS.json');return {(e['candidate'],e['task'],e['split'],e['representation'],str(e['seed'])):e for e in b['classifier_units']}
@lru_cache(None)
def immutable_map():return read(C/'INHERITED_IMMUTABLE_MAP.json')
@lru_cache(None)
def keys():
 with gzip.open(C/'EXPECTED_A08_KEYS.csv.gz','rt') as f:rows=list(csv.DictReader(f))
 return {(r['table_kind'],r['family'],r['task'],r['split'],r['representation'],r['CV_seed'],r['target_policy'],r['metric']):r for r in rows}
def contrast_source():
 source_check();j=read(C/'CONTRAST_SOURCE_IDENTITY.json');require(j['status']=='FROZEN' and sha(C/'ENDPOINT_BINDINGS.json')==j['endpoint_bindings_sha256'] and sha(C/'CONTRAST_EXECUTION_MANIFEST.json')==j['contrast_manifest_sha256'],'Contrast input drift')
 for e in j['files']:require(sha(A/'code'/e['path'])==e['sha256'],'Contrast numerical source changed after freeze')
 return sha(C/'CONTRAST_SOURCE_IDENTITY.json')

def distribution(endpoint,policy,prob,meta,classes,weights):
 src=contrast_source();identity={'stage':'A08','endpoint':{k:endpoint[k] for k in ['candidate','task','split','representation','seed','effective_content_id','prediction','release_receipts','draw']},'policy':policy,'selector':endpoint['selectors'][policy],'probability_array_sha256':array_sha(prob),'classes':classes.tolist(),'ids_sha256':array_sha(meta['ids']),'labels_sha256':array_sha(meta['labels']),'groups_sha256':array_sha(meta['groups']),'source_sha256':src,'protocol_sha256':CFG['protocol_sha256']};root=A/'endpoint-cache/classifier'/digest(identity)
 with Lock(A/'locks/endpoint-cache'/(digest(identity)+'.lock')):
  if (root/'COMPLETE.json').exists():seal_check(root,identity)
  else:
   tmp=workdir(root);t=time.monotonic();ind,valid=metrics(meta['labels'],prob,classes,weights);rank,rv=bootstrap_metrics(meta['labels'],prob,classes,weights);require(np.array_equal(valid,rv),'Independent/rank class masks differ');pt,pv=metrics(meta['labels'],prob,classes,np.ones((1,len(prob))));rp,_=point_metrics(meta['labels'],prob,classes);require(pv.all(),'Point classes absent');maxdraw=max(residual(ind[m],rank[m],valid) for m in METRICS);maxpoint=max(residual(pt[m],[rp[m]]) for m in METRICS);np.savez_compressed(tmp/'vectors.npz',valid=valid,**{'ind__'+m:ind[m] for m in METRICS},**{'rank__'+m:rank[m] for m in METRICS});put(tmp/'ENDPOINT.json',{'status':'PASS','point':{m:float(pt[m][0]) for m in METRICS},'rank_point':rp,'draw_max_abs':maxdraw,'point_max_abs':maxpoint,'new_independent_saved_output_arithmetic':True,'no_historical_model_or_probe_refit':True,'wall_seconds':time.monotonic()-t});seal(tmp,root,{'status':'PASS','identity':identity})
  with np.load(root/'vectors.npz',allow_pickle=False) as z:values={k:z[k] for k in z.files}
  return values,read(root/'ENDPOINT.json'),ref(root/'COMPLETE.json')
