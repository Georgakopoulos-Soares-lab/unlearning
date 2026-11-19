"""Additional independent paired point check; no model or production recomputation."""
from endpoint_common8 import *
import argparse,resource

def main():
 contrast_source();paths=list((A/'contrasts/LM').glob('*/*/*/COMPLETE.json'));require(len(paths)==35,'All35 LM coordinate seals required');count=0;maximum=0.;worst=None;refs=[]
 for p in paths:
  record=read(p.parent/'RESULTS.json');numbers={}
  for name in ['target','reference']:
   item=record['endpoints'][name];path=checked(item['statistics'])
   with np.load(path,allow_pickle=False) as z:nll=float(np.sum(z['nll_sum'],dtype=np.float64)/np.sum(z['n_tokens'],dtype=np.int64));numbers[name]={'causal_nll':nll,'perplexity':float(np.exp(nll))}
  for row in record['rows']:
   value=numbers['target'][row['metric']]-numbers['reference'][row['metric']];err=abs(value-row['estimate']);require(err<=1e-12,'Independent paired LM point disagreement');count+=1
   if err>=maximum:maximum=err;worst=row['logical_id']
  refs.append(ref(p))
 require(count==70,'Incorrect paired point key count');out={'status':'PASS','paired_points_checked':70,'max_abs':maximum,'worst_logical_id':worst,'absolute_tolerance':1e-12,'method':'Direct float64 array sums and NumPy exponential; paired point comparison against primary math.fsum/math.exp','source_sha256':sha(__file__),'primary_contrast_source_sha256':sha(C/'CONTRAST_SOURCE_IDENTITY.json'),'primary_unit_receipts':refs,'new_forwards_or_fits':0};put(A/'contrasts/LM/POINT_VERIFICATION.json',out);put(C/'LM_PAIRED_POINT_SUPPLEMENT.json',out);print('LM_PAIRED_POINTS_PASS_70')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['A08'],required=True);p.parse_args();resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));main()
