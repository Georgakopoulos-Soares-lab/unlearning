"""Verify sealed A06 chunks and derive A07 read-only float32 matrices. No GPU."""
import argparse,time
from other_five_common import *
def build(alias,task,split):
 require(CFG['stage']=='A07' and alias in ['R5'] and task in TASKS and split in ['train','dev'],'Unapproved cache bundle')
 u=next(u for u in I6['extraction_units'] if (u['candidate'],u['task'],u['split'])==(alias,task,split));check_ref(u['manifest']);check_ref(u['parent_manifest'])
 mapped=Path(INPUTS['source_manifest_root'])/(task+'__'+split+'.jsonl');require(sha(mapped)==u['manifest']['sha256'],'Portable source manifest differs');rows=validate_rows([json.loads(l) for l in mapped.read_text().splitlines()],task,split);require(len(rows)==(1024 if split=='train' else 512),'Frozen row count differs')
 bundle_root=A6/'features'/alias/task/split;bundle=read(bundle_root/'COMPLETE.json');index=next(e for e in read(D6/'EXTRACTION_INDEX.json')['units'] if (e['candidate'],e['task'],e['split'])==(alias,task,split));require(sha(bundle_root/'COMPLETE.json')==index['receipt_sha256'] and bundle['status']=='PASS','Changed A06 bundle')
 require(bundle['identity']['model_tensor_content_sha256']==I6['checkpoint_identities'][alias]['model_tensor_content_sha256'] and bundle['identity']['unit']==u,'Cross-candidate/task input')
 identity={'stage':'A07','candidate':alias,'task':task,'split':split,'input_bundle':ref(bundle_root/'COMPLETE.json'),'extraction_identity':bundle['identity'],'source_sha256':sha(__file__),'cohort_sha256':u['parent_manifest']['sha256'],'ordered_ids_sha256':u['ordered_ids_sha256'],'representation_keys':LAYERS,'dtype':'float32','transformation':'none; exact concatenation','classes':classes_for(task).tolist(),'A07_plan_sha256':CFG['coverage_plan_sha256'],'approval_sha256':INPUTS['approval_sha256']}
 out=A/'cache'/alias/task/split
 with UnitLock(A/'locks/cache'/alias/task/(split+'.lock')):
  if (out/'COMPLETE.json').exists():verify_seal(out,identity);return
  work=new_work(out);t=time.monotonic();maps={k:np.lib.format.open_memmap(work/(k+'.npy'),mode='w+',dtype=np.float32,shape=(len(rows),1920)) for k in LAYERS};meta={k:[] for k in ['ids','labels','groups','sequence_sha256','lengths','nll_sum','n_tokens']};sources=[];cursor=0
  for e in bundle['chunks']:
   path=A6/e['path'];j=read(path/'COMPLETE.json');require(sha(path/'COMPLETE.json')==e['receipt_sha256'],'Changed chunk receipt');rr=rows[cursor:cursor+e['rows']];verify_chunk(path,j['identity'],rr)
   require(all(j['identity'][k]==v for k,v in bundle['identity'].items()),'Chunk/bundle identity differs');require(j['identity']['first_row']==cursor and j['identity']['real_rows']==e['rows'],'Chunk slice differs')
   with np.load(path/'features_and_lm.npz',allow_pickle=False) as z:
    for k in LAYERS:maps[k][cursor:cursor+len(rr)]=z[k]
    for k in meta:meta[k].append(z[k])
   sources.append({'receipt':ref(path/'COMPLETE.json'),'payload':ref(path/'features_and_lm.npz')});cursor+=len(rr)
  require(cursor==len(rows),'Incomplete ordered population')
  for m in maps.values():m.flush()
  del maps
  np.savez_compressed(work/'metadata.npz',**{k:np.concatenate(v) for k,v in meta.items()})
  for k in LAYERS:
   m=np.load(work/(k+'.npy'),mmap_mode='r');require(m.dtype==np.float32 and m.shape==(len(rows),1920) and np.isfinite(m).all(),'Bad derived matrix')
  receipt={'schema':'pod-a-a07-feature-cache-v1','status':'PASS','identity':identity,'source_chunks':sources,'rows':len(rows),'files':members(work),'wall_seconds':time.monotonic()-t,'derived_cache_backup':'Excluded; regenerate from A06 private hash-verified chunk dependencies'}
  os.replace(work,out);put(out/'COMPLETE.json',receipt)
 print(json.dumps({'event':'CACHE_SEALED','candidate':alias,'task':task,'split':split,'rows':len(rows)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',choices=['R5'],required=True);p.add_argument('--task',choices=TASKS,required=True);v=p.parse_args()
 for split in ['train','dev']:build(v.candidate,v.task,split)
