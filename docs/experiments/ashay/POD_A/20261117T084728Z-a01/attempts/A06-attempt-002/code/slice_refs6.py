"""Bounded approved CPU feature-integrity slice references, no fitting/effects."""
from common6 import *
import numpy as np
def main(group):
 assert group in ['H3','other_five'];slices={}
 for u in read(C/'A06_INPUTS.json')['extraction_units']:
  if (u['task']=='emp_H3')!=(group=='H3'):continue
  bundle=read(A/'features/R5'/u['task']/u['split']/'COMPLETE.json')
  for e in bundle['chunks']:
   receipt=read(A/e['path']/'COMPLETE.json');assert sha(A/e['path']/'COMPLETE.json')==e['receipt_sha256'];p=A/e['path']/'features_and_lm.npz';assert sha(p)==receipt['files'][0]['sha256']
   with np.load(p,allow_pickle=False) as z:
    for key in [f'decoder_layer_{i}' for i in range(25)]+['final_norm']:
     f=z[key];rows=sorted({0,len(f)//2,len(f)-1});cols=[0,16,1919];slices[str(Path(e['path'])/key)]={'rows':rows,'columns':cols,'sha256':bh(f[rows][:,cols].tobytes()),'selection':'Deterministic first/middle/last rows, fixed channels0/16/1919; no outcome selection'}
 put(C/('FEATURE_SLICE_REFERENCES_R5_'+group+'.json'),slices);print(json.dumps({'status':'PASS','group':group,'sealed_chunk_hook_slices':len(slices),'new_fits_or_effects':0}))
if __name__=='__main__':main(sys.argv[1])
