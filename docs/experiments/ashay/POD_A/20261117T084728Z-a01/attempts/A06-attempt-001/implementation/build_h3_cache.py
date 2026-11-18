"""Derive float32 matrices from verified A06 chunks; no inference or fitting."""
import argparse,time
from h3_common import *
from production_contract import verify_chunk,validate_rows
def main(alias):
 for split in ['train','dev','test']:
  unit=next(u for u in INPUTS['extraction_units'] if u['candidate']==alias and u['task']=='emp_H3' and u['split']==split);rows=validate_rows([json.loads(l) for l in Path(unit['manifest']['path']).read_text().splitlines()],'emp_H3',split);bundle_root=A/'features'/alias/'emp_H3'/split;bundle=read(bundle_root/'COMPLETE.json');require(bundle['status']=='PASS','H3 extraction incomplete');out=A/'h3-cache'/alias/split
  if (out/'COMPLETE.json').exists():
   receipt=read(out/'COMPLETE.json');require(receipt['input_bundle_sha256']==sha(bundle_root/'COMPLETE.json'),'Changed cache dependency');verify_refs(out,receipt);continue
  require(not out.exists(),'Partial derived cache preserved; create a new derivation identity');out.mkdir(parents=True);maps={k:np.lib.format.open_memmap(out/(k+'.npy'),mode='w+',dtype=np.float32,shape=(len(rows),1920)) for k in LAYERS};meta={'ids':[],'labels':[],'groups':[],'sequence_sha256':[],'lengths':[],'nll_sum':[],'n_tokens':[]};cursor=0
  for entry in bundle['chunks']:
   path=A/entry['path'];receipt=read(path/'COMPLETE.json');require(sha(path/'COMPLETE.json')==entry['receipt_sha256'],'Changed chunk receipt');rr=rows[cursor:cursor+entry['rows']];verify_chunk(path,receipt['identity'],rr)
   with np.load(path/'features_and_lm.npz',allow_pickle=False) as z:
    for k in LAYERS:maps[k][cursor:cursor+len(rr)]=z[k]
    for k in meta:meta[k].append(z[k])
   cursor+=len(rr)
  require(cursor==len(rows),'Missing H3 rows')
  for m in maps.values():m.flush()
  del maps;np.savez_compressed(out/'metadata.npz',**{k:np.concatenate(v) for k,v in meta.items()});receipt={'status':'PASS','candidate':alias,'split':split,'rows':len(rows),'input_bundle_sha256':sha(bundle_root/'COMPLETE.json'),'source_sha256':sha(__file__),'files':file_refs(out),'derived_cache_excluded_from_backup':'Reconstruct exactly from included verified chunks; samefloat32 values, no numerical transformation'};put(out/'COMPLETE.json',receipt);print(json.dumps({'event':'H3_CACHE_SEALED','candidate':alias,'split':split,'rows':len(rows)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',choices=['R4','R6'],required=True);main(p.parse_args().candidate)
