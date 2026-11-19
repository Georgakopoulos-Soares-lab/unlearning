"""Normalize admitted saved sufficient statistics; zero LM forwards/re-scoring."""
from endpoint_common8 import *
from portable_math8 import historical_lm
import argparse,resource

def main():
 source=contrast_source();items=[]
 for endpoint in read(C/'ENDPOINT_BINDINGS.json')['LM_units']:
  alias,task,split=(endpoint[k] for k in ['checkpoint_alias','task','split']);root=A/'normalized-lm'/alias/task/split;identity={'stage':'A08','source_sha256':source,'endpoint':endpoint,'operation':'Typed saved-sum/count selection only; no model evaluation'}
  with Lock(A/'locks/normalize-lm'/alias/task/(split+'.lock')):
   if (root/'COMPLETE.json').exists():seal_check(root,identity)
   else:
    tmp=workdir(root);t=time.monotonic();d=endpoint['prediction_descriptor'];sources=[]
    if d['hash_kind']=='LM_SEALED_FEATURE_BUNDLE_WITH_SUM_COUNT_SELECTOR':meta,sources=historical_lm(d,endpoint['raw_cohort'],task,split,immutable_map())
    else:
     require(d['hash_kind']=='LM_SUFFICIENT_STATISTICS_FILE','Unknown LM source object type')
     with np.load(resolve(d,immutable_map()),allow_pickle=False) as z:meta={k:z[k] for k in ['ids','labels','groups','sequence_sha256','lengths','nll_sum','n_tokens']}
    require(meta['nll_sum'].dtype==np.float32 and meta['n_tokens'].dtype==np.int64 and np.isfinite(meta['nll_sum']).all() and np.all(meta['n_tokens']>0) and np.array_equal(meta['n_tokens'],meta['lengths']-1),'Qualified causal-shift/count/sum type differs');require(len(meta['ids'])==(1497 if task=='emp_H3' else 512),'Wrong reporting LM cohort');w,draw=weights_from_draws(resolve(endpoint['draw'],immutable_map()),meta);np.savez_compressed(tmp/'sufficient_statistics.npz',**meta);nll=float(meta['nll_sum'].astype(np.float64).sum()/meta['n_tokens'].sum())
    if endpoint.get('estimate') is not None:require(abs(nll-float(endpoint['estimate']))<=1e-12,'Normalized source disagrees with accepted LM point')
    put(tmp/'NORMALIZATION.json',{'status':'PASS','checkpoint_alias':alias,'task':task,'split':split,'source':d,'raw_cohort':endpoint['raw_cohort'],'draw':endpoint['draw'],'source_chunks':sources,'rows':len(meta['ids']),'groups':len(np.unique(meta['groups'])),'targets':int(meta['n_tokens'].sum()),'NLL':nll,'source_kind':d['hash_kind'],'historical_R3_bundle_route':alias=='R3','new_LM_forwards':0,'new_LM_loss_evaluations':0,'wall_seconds':time.monotonic()-t});seal(tmp,root,{'status':'PASS','identity':identity})
   items.append({'candidate':alias,'task':task,'split':split,'statistics':ref(root/'sufficient_statistics.npz'),'receipt':ref(root/'COMPLETE.json'),'normalization':ref(root/'NORMALIZATION.json'),'endpoint':endpoint})
 require(len(items)==42,'Wrong primary LM endpoint count');put(C/'LM_NORMALIZATION_INDEX.json',{'status':'PASS','units':items,'new_LM_measurements':0,'hist_R3_route':'Selected from pinned typed feature bundles with exact metadata/chunk hashes','source_sha256':source});print('LM_SAVED_STATISTICS_READY_42',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['A08'],required=True);p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));main()
