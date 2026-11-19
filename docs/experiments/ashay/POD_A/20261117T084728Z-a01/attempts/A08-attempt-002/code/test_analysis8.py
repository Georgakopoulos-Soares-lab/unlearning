"""Independent contrast qualification using synthetic saved objects only."""
from pathlib import Path
import unittest,tempfile,json,hashlib
import numpy as np
from portable_math8 import weights_from_draws,pair,historical_lm,resolve
from independent_math import metrics
from rank_crosscheck import bootstrap_metrics
from analysis_pairs import lm_numbers
from audit_common import A,C,read

class AnalysisTests(unittest.TestCase):
 def test_exact_predeclared_families(self):
  m=read(C/'CONTRAST_EXECUTION_MANIFEST.json');self.assertEqual({u['family'] for u in m['classifier_units']},{'R4_minus_R3','R5_minus_R4','R6_minus_R5'});self.assertEqual(len(m['classifier_units']),1638);self.assertEqual({u['family'] for u in m['LM_units']},{'R5_minus_base','R5_minus_R1','R4_minus_R3','R5_minus_R4','R6_minus_R5'});self.assertEqual(len(m['LM_units']),35)
 def test_unequal_group_expansion_saved_indices(self):
  with tempfile.TemporaryDirectory(dir=A) as t:
   p=Path(t)/'draw.npz';ids=np.array(['a','b','c','d']);groups=np.array(['g0','g1','g1','g2']);np.savez(p,ids=ids,group_names=np.array(['g0','g1','g2']),row_groups=np.array([0,1,1,2]),seed=20261103,group_draws=np.tile(np.array([1,1,2],dtype=np.int32),(2000,1)));w,d=weights_from_draws(p,{'ids':ids,'groups':groups});self.assertEqual(w[0].tolist(),[0,2,2,1]);self.assertTrue(np.array_equal(w[:,1],w[:,2]))
 def test_point_and_draw_direction_with_ties_and_missing_class(self):
  y=np.array([0,1,0,1,0,1]);cl=np.array([0,1]);p=np.array([[.5,.5],[.5,.5],[.8,.2],[.2,.8],[.7,.3],[.1,.9]]);q=np.full((6,2),.5);w=np.array([[1]*6,[2,1,3,2,1,1],[1,0,1,0,1,0]])
  a,v=metrics(y,p,cl,w);b,vb=metrics(y,q,cl,w);ra,rv=bootstrap_metrics(y,p,cl,w);rb,rvb=bootstrap_metrics(y,q,cl,w);self.assertTrue(np.array_equal(v,vb)&np.array_equal(v,rv)&np.array_equal(v,rvb));self.assertFalse(v[-1])
  for m in a:np.testing.assert_allclose((a[m]-b[m])[v],(ra[m]-rb[m])[v],atol=1e-12,rtol=0);self.assertTrue(np.isnan((a[m]-b[m])[~v]).all())
 def test_pair_wrong_row_and_class_rejected(self):
  meta={'ids':np.array(['a','b']),'labels':np.array([0,1]),'groups':np.array(['a','b']),'sequence_sha256':np.array(['x','y'])}
  for change in [{'ids':meta['ids'][::-1]},{'sequence_sha256':meta['sequence_sha256'][::-1]}]:
   with self.assertRaises(AssertionError):pair(meta,meta|change,np.array([0,1]),np.array([0,1]))
  with self.assertRaises(AssertionError):pair(meta,meta,np.array([0,1]),np.array([1,0]))
 def test_LM_paired_ratio_and_exponentials(self):
  a={'groups':np.array(['a','b','b']),'nll_sum':np.array([2.,8.,4.],dtype=np.float32),'n_tokens':np.array([1,2,1],dtype=np.int64)};b=a|{'nll_sum':a['nll_sum']*.5};draw=np.array([[0,1],[1,1],[0,0]],dtype=np.int32);w=np.array([[1,1,1],[0,2,2],[2,0,0]]);pa,da,aa=lm_numbers(a,draw,w);pb,db,ab=lm_numbers(b,draw,w);np.testing.assert_allclose(da-db,aa-ab,atol=1e-12,rtol=0);np.testing.assert_allclose(np.exp(da)-np.exp(db),np.exp(aa)-np.exp(ab),atol=1e-12,rtol=0);self.assertNotAlmostEqual(np.exp(pa)-np.exp(pb),np.mean(np.exp(a['nll_sum']/a['n_tokens']))-np.mean(np.exp(b['nll_sum']/b['n_tokens'])))
 def fixture(self,base):
  root=base/'consumer';folder=root/'features/other_five/new';folder.mkdir(parents=True);rows=[];files=[];members={};h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();seq='ACGT';sh=hashlib.sha256(seq.encode()).hexdigest()
  for i in range(520):rows.append({'id':f'r{i}','task':'gue_tf_0','split':'train' if i<8 else 'dev','label':i%2,'exact_rc_group':f'g{i//2}','sequence':seq})
  for start in range(0,520,8):
   rr=rows[start:start+8];p=folder/f'chunk_{start:06d}.npz';np.savez(p,ids=np.array([r['id'] for r in rr]),labels=np.array([r['label'] for r in rr]),groups=np.array([r['exact_rc_group'] for r in rr]),sequence_sha256=np.array([sh]*8),lengths=np.array([4]*8),nll_sum=np.array([1.5]*8,dtype=np.float32),n_tokens=np.array([3]*8,dtype=np.int64),task=np.array(['gue_tf_0']*8),split=np.array([r['split'] for r in rr]));e={'path':str(p),'sha256':h(p),'bytes':p.stat().st_size};files.append(e);members[str(p.relative_to(root))]=e
  manifest=root/'manifest.jsonl';manifest.write_text(''.join(json.dumps(r)+'\n' for r in rows));bundle=folder/'FEATURE_UNIT_COMPLETE.json';bundle.write_text(json.dumps({'examples':520,'files':files}));node={'repository':'synthetic','revision':'fixture','archive_path':'fixture.tar','archive_sha256':'fixture','consumer_root':str(root)}
  def desc(p):return {'storage_kind':'IMMUTABLE_ARCHIVE_MEMBER',**{k:node[k] for k in ['repository','revision','archive_path','archive_sha256']},'member':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':h(p)}
  return desc(bundle),desc(manifest),{'archives':{'fixture':node},'member_indices':{'fixture':members}},folder
 def test_historical_R3_typed_bundle_selects_only_saved_dev(self):
  with tempfile.TemporaryDirectory(dir=A) as t:
   d,m,mp,f=self.fixture(Path(t));(f/'chunk_000000.npz').write_bytes(b'train_chunk_not_consumed');z,sources=historical_lm(d,m,'gue_tf_0','dev',mp);self.assertEqual(len(z['ids']),512);self.assertEqual(z['ids'][0],'r8');self.assertEqual(len(sources),64);self.assertEqual(z['nll_sum'].dtype,np.float32);self.assertEqual(int(z['n_tokens'].sum()),1536)
 def test_corrupt_selected_historical_chunk_rejected(self):
  with tempfile.TemporaryDirectory(dir=A) as t:
   d,m,mp,f=self.fixture(Path(t));(f/'chunk_000008.npz').write_bytes(b'corrupt')
   with self.assertRaises(AssertionError):historical_lm(d,m,'gue_tf_0','dev',mp)
 def test_descriptor_escape_rejected(self):
  with tempfile.TemporaryDirectory(dir=A) as t:
   d,m,mp,f=self.fixture(Path(t));bad=d|{'member':'../../escape'}
   with self.assertRaises(AssertionError):resolve(bad,mp)
if __name__=='__main__':unittest.main(verbosity=2)
