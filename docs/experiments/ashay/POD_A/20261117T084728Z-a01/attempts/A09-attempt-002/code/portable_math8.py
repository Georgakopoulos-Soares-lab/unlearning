"""Consumer-only immutable file/draw readers shared by live checks and recovery."""
from pathlib import Path
import json,hashlib
import numpy as np

def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def resolve(d,mapping):
 assert d['storage_kind']=='IMMUTABLE_ARCHIVE_MEMBER';node=mapping['archives'][d['archive_sha256']];assert all(d[k]==node[k] for k in ['repository','revision','archive_path']);root=Path(node['consumer_root']);p=root/d['member'];assert p.resolve().is_relative_to(root.resolve()) and ('/consumer' in str(root) or '/restored/' in str(root));assert not p.is_symlink() and p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];return p

def probabilities(endpoint,policy,mapping):
 p=resolve(endpoint['prediction'],mapping)
 with np.load(p,allow_pickle=False) as z:meta={k:z[k] for k in ['ids','labels','groups','sequence_sha256']};classes=z['classes'];prob=z[endpoint['selectors'][policy]]
 expected=np.array([0,1,2] if endpoint['task']=='gue_splice_reconstructed' else [0,1]);assert np.array_equal(classes,expected) and np.array_equal(np.unique(meta['labels']),classes);assert len(meta['ids'])==(1497 if endpoint['task']=='emp_H3' else 512);assert len(set(meta['ids']))==len(meta['ids']) and prob.dtype==np.float64 and np.isfinite(prob).all() and prob.shape==(len(meta['ids']),len(classes));assert np.all((prob>=0)&(prob<=1)) and np.allclose(prob.sum(1),1,atol=1e-12,rtol=0);return prob,meta,classes

def pair(a,b,ca,cb):
 for k in ['ids','labels','groups','sequence_sha256']:assert np.array_equal(a[k],b[k]),'Pair order/metadata differs: '+k
 assert np.array_equal(ca,cb)

def weights_from_draws(path,meta):
 with np.load(path,allow_pickle=False) as z:
  names,inverse=np.unique(meta['groups'],return_inverse=True);assert np.array_equal(z['ids'],meta['ids']) and np.array_equal(z['group_names'],names) and np.array_equal(z['row_groups'],inverse) and int(z['seed'])==20261103;draw=z['group_draws'];assert draw.shape==(2000,len(names)) and draw.dtype==np.int32 and np.all((draw>=0)&(draw<len(names)));group_weights=np.zeros((2000,len(names)),dtype=np.int64)
  for i,d in enumerate(draw):np.add.at(group_weights[i],d,1)
 return group_weights[:,inverse],draw

def historical_lm(bundle_descriptor,manifest_descriptor,task,split,mapping):
 """Select saved LM sums/counts from a typed historical bundle, without feature loading."""
 bundlepath=resolve(bundle_descriptor,mapping);bundle=read(bundlepath);mp=resolve(manifest_descriptor,mapping);rows=[json.loads(l) for l in mp.read_text().splitlines()];assert len(rows)==bundle['examples'];storage='test' if split=='test_exploratory' else split;positions=[i for i,r in enumerate(rows) if r['task']==task and r['split']==storage];assert len(positions)==(1497 if task=='emp_H3' else 512);wanted=set(positions);files={Path(e['path']).name:e for e in bundle['files']};assert len(files)==len(bundle['files']),'Duplicate historical bundle basename';parts={k:[] for k in ['ids','labels','groups','sequence_sha256','lengths','nll_sum','n_tokens']};sources=[]
 for start in sorted({i//8*8 for i in positions}):
  name=f'chunk_{start:06d}.npz';path=bundlepath.parent/name;e=files[name];assert not path.is_symlink() and path.stat().st_size==e['bytes'] and sha(path)==e['sha256'];rel=str(Path(bundle_descriptor['member']).parent/name);listed=mapping['member_indices'][bundle_descriptor['archive_sha256']][rel];assert listed['sha256']==e['sha256'] and listed['bytes']==e['bytes'];select=[i-start for i in range(start,min(start+8,len(rows))) if i in wanted]
  with np.load(path,allow_pickle=False) as z:
   assert len(z['ids'])==min(8,len(rows)-start);assert z['nll_sum'].dtype==np.float32 and z['n_tokens'].dtype==np.int64
   for local in select:
    r=rows[start+local];assert str(z['ids'][local])==r['id'] and int(z['labels'][local])==r['label'] and str(z['groups'][local])==r['exact_rc_group'];assert str(z['sequence_sha256'][local])==hashlib.sha256(r['sequence'].encode()).hexdigest();assert int(z['lengths'][local])==len(r['sequence']) and int(z['n_tokens'][local])==len(r['sequence'])-1 and str(z['task'][local])==task and str(z['split'][local])==storage
   for k in parts:parts[k].append(z[k][select])
  sources.append({'member':rel,'sha256':e['sha256'],'bytes':e['bytes']})
 result={k:np.concatenate(v) for k,v in parts.items()};assert len(result['ids'])==len(positions) and np.isfinite(result['nll_sum']).all() and np.all(result['n_tokens']>0);return result,sources
