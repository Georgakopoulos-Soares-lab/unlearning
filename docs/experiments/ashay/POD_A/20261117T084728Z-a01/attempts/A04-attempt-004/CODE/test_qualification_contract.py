"""Focused synthetic software checks for A04's changed rejection and arithmetic paths."""
from qualification_contract import *
import unittest,tempfile,copy,io,json
from pathlib import Path
import numpy as np
import torch

def rows():
 s='ACGTNACGT';h=hashlib.sha256(s.encode()).hexdigest();rc=s.translate(str.maketrans('ACGTN','TGCAN'))[::-1];g=hashlib.sha256(min(s,rc).encode()).hexdigest();return [{'id':str(i),'sequence':s,'sequence_sha256':h,'exact_rc_group':g,'label':i%2,'split':'train','task':'synthetic'} for i in range(12)]
def values(n=12):return {k:np.zeros((n,1920),dtype=np.float32) for k in LAYERS}
class Tiny(torch.nn.Module):
 def __init__(self,dtype=torch.float32):super().__init__();self.weight=torch.nn.Parameter(torch.zeros(3,dtype=dtype))
class Checks(unittest.TestCase):
 def test_valid_frozen_schema(self):self.assertEqual(len(validate_rows(rows())),12)
 def test_heldout_rejected(self):
  for split in ['dev','test']:
   r=rows();r[0]['split']=split
   with self.assertRaises(ValueError):validate_rows(r)
 def test_duplicate_ids_rejected(self):
  r=rows();r[1]['id']=r[0]['id']
  with self.assertRaises(ValueError):validate_rows(r)
 def test_sequence_digest_and_RC_rejected(self):
  for field in ['sequence_sha256','exact_rc_group']:
   r=rows();r[0][field]='0'*64
   with self.assertRaises(ValueError):validate_rows(r)
 def test_preprocessing_rejected(self):
  for seq in ['aCGT','AXGT','A','A'*1001]:
   r=rows();r[0]['sequence']=seq
   with self.assertRaises(ValueError):validate_rows(r)
 def test_manifest_bytes_and_order_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   p=Path(td)/'fixture.jsonl';p.write_text(''.join(json.dumps(x)+'\n' for x in rows()));h=sha(p);validate_manifest(p,h,[str(i) for i in range(12)])
   with self.assertRaises(ValueError):validate_manifest(p,'0'*64)
   with self.assertRaises(ValueError):validate_manifest(p,h,list(reversed([str(i) for i in range(12)])))
 def test_checkpoint_identity_rejected(self):
  for alias,cid in [('R7','selected'),('R4','wrong')]:
   with self.assertRaises(ValueError):validate_alias(alias,cid,{'R4':'selected'})
 def test_protected_path_and_symlink_rejected(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td)/'owned';root.mkdir();owned_path(root/'valid',root);(root/'escape').symlink_to(Path(td))
   for p in [root,Path(td)/'historical-ledger.json',root/'escape/historical-ledger.json']:
    with self.assertRaises(ValueError):owned_path(p,root)
 def test_wrong_hook_index_and_width_rejected(self):
  check_hook_registry(HOOKS,1920)
  for names,width in [(HOOKS[:-1],1920),([*HOOKS[:16],'decoder.layers.15',*HOOKS[17:]],1920),(HOOKS,1919)]:
   with self.assertRaises(ValueError):check_hook_registry(names,width)
 def test_packer_physical8_padding_fillers(self):
  t,l,p=pack(['ACGT','NAC']);self.assertEqual(tuple(t.shape),(8,1000));self.assertEqual(l.tolist(),[4,3,1,1,1,1,1,1]);self.assertEqual(t[0,:4].tolist(),[65,67,71,84]);self.assertTrue(torch.all(t[0,4:]==1));self.assertTrue(torch.all(t[2:]==1));self.assertEqual(p[0].tolist(),list(range(1000)))
  for seqs in [[],['ACGT']*9]:
   with self.assertRaises(ValueError):pack(seqs)
 def test_masked_nucleotide_pool(self):
  h=torch.full((1000,8,1920),100.,dtype=torch.float32);h[:4,0]=1.;l=torch.tensor([4,1,1,1,1,1,1,1]);got=pool(h,l);self.assertTrue(torch.equal(got[0],torch.ones(1920)))
  with self.assertRaises(ValueError):pool(h[:,:7],l)
 def test_row_order_and_filler_output_rejected(self):
  ids=[str(i) for i in range(12)];x=values();loss=np.ones(12,dtype=np.float32);counts=np.full(12,8,dtype=np.int64);lens=np.full(12,9);check_real_population(ids,ids,x,loss,counts,lens)
  with self.assertRaises(ValueError):check_real_population(ids[::-1],ids,x,loss,counts,lens)
  with self.assertRaises(ValueError):check_real_population(ids+['FILLER'],ids,values(13),np.ones(13,dtype=np.float32),np.ones(13,dtype=np.int64),np.ones(13,dtype=np.int64))
 def test_feature_shape_dtype_nonfinite_rejected(self):
  ids=[str(i) for i in range(12)]
  for invalid in [np.zeros((12,1919),np.float32),np.zeros((12,1920),np.float64),np.full((12,1920),np.nan,np.float32)]:
   x=values();x[LAYERS[0]]=invalid
   with self.assertRaises(ValueError):check_real_population(ids,ids,x,np.ones(12,np.float32),np.full(12,8),np.full(12,9))
 def test_missing_unexpected_shape_dtype_tensor_keys(self):
  model=Tiny()
  for state in [{},{'weight':torch.zeros(3),'extra':torch.zeros(1)},{'weight':torch.zeros(4)},{'weight':torch.tensor([float('nan'),0,0])}]:
   with self.assertRaises(ValueError):validate_state(model,state)
  with self.assertRaises(ValueError):validate_state(Tiny(torch.bfloat16),{'weight':torch.zeros(3,dtype=torch.float32)})
  r=validate_state(model,{'weight':torch.zeros(3,dtype=torch.bfloat16)});self.assertEqual(len(r['dtype_promotions']),1)
 def test_extra_state_tensor_cannot_hide_missing_tensor(self):
  class Bad(torch.nn.Module):
   def __init__(self):super().__init__();self.register_buffer('_extra_state',torch.ones(3))
  with self.assertRaises(ValueError):validate_state(Bad(),{})
  class NonTE(torch.nn.Module):
   def get_extra_state(self):return io.BytesIO()
   def set_extra_state(self,value):pass
  with self.assertRaises(ValueError):validate_state(NonTE(),{})
 def test_TE_serialized_None_metadata_and_nonempty_rejection(self):
  import pickle
  class TE(torch.nn.Module):
   def __init__(self,payload):super().__init__();self.payload=payload;self.fp8_meta={'fp8_checkpoint':False}
   def get_extra_state(self):return torch.tensor(list(pickle.dumps(self.payload)),dtype=torch.uint8)
   def set_extra_state(self,value):pass
  TE.__module__='transformer_engine.pytorch.synthetic'
  class Parent(torch.nn.Module):
   def __init__(self,payload):super().__init__();self.layer=TE(payload)
  self.assertEqual(len(validate_state(Parent(None),{})['allowed_missing_non_tensor_metadata']),1)
  self.assertEqual(len(validate_state(Parent({}),{})['allowed_missing_non_tensor_metadata']),1)
  bad=Parent({});bad.layer._fp8_metas={'forward':{'scaling':'present'},'backward':None}
  with self.assertRaises(ValueError):validate_state(bad,{})
  with self.assertRaises(ValueError):validate_state(Parent({'unexpected':'FP8 state'}),{})
  model=Parent(None);model.layer.fp8_meta['fp8_checkpoint']=True
  with self.assertRaises(ValueError):validate_state(model,{})

 def test_unrecognized_nonTE_None_is_rejected(self):
  class Unknown(torch.nn.Module):
   def get_extra_state(self):return None
   def set_extra_state(self,state):pass
  with self.assertRaises(ValueError):validate_state(Unknown(),{})

 def test_actual_loading_metadata_and_MCore_default_hook(self):
  report={'allowed_missing_non_tensor_metadata':[{'key':'te._extra_state','MCore_output_TE_compatibility_None':False},{'key':'output._extra_state','MCore_output_TE_compatibility_None':True},{'key':'attention._extra_state','TE_attention_missing_metadata_removed_by_pinned_posthook':True}]}
  got=validate_actual_loading(['te._extra_state'],[],report);self.assertEqual(got['MCore_compatibility_None_added_by_pinned_load_hook'],['output._extra_state'])
  for missing,unexpected in [(['learned.weight'],[]),([],[]),(['te._extra_state'],['extra.weight']),(['te._extra_state','output._extra_state'],[])]:
   with self.assertRaises(ValueError):validate_actual_loading(missing,unexpected,report)

 def test_loaded_values_not_just_shapes(self):
  with self.assertRaises(ValueError):check_loaded_values(Tiny(),{'weight':torch.ones(3)})
  self.assertEqual(check_loaded_values(Tiny(),{'weight':torch.zeros(3)}),1)
 def test_actual_head_shape_causal_shift_mask_counts(self):
  t,l,p=pack(['ACGTN']);logits=torch.zeros((8,1000,512))
  for i in range(4):logits[0,i,int(t[0,i+1])]=20.
  sums,counts,loss,mask=production_loss(logits,t,l,p);self.assertEqual(counts.tolist(),[4,0,0,0,0,0,0,0]);self.assertLess(sums[0].item(),1e-4);self.assertTrue(torch.all(sums[1:]==0));ind=independent_cross_entropy(logits[0,:4].numpy(),t[0,1:5].numpy());self.assertEqual(componentwise(ind,loss[0,:4].numpy())['status'],'PASS')
  with self.assertRaises(ValueError):production_loss(logits[:7],t,l,p)
  with self.assertRaises(ValueError):production_loss(logits,t,l,torch.zeros_like(p))
 def test_componentwise_threshold_and_nearzero(self):
  self.assertEqual(componentwise(np.array([0.,1.]),np.array([0.,1.]))['status'],'PASS');r=componentwise(np.array([1.00001e-4,1.]),np.array([0.,1.]));self.assertEqual(r['status'],'FAIL');self.assertEqual(r['violations'],1);self.assertEqual(r['relative_undefined_nonzero_at_reference_zero'],1)

 def test_actual_packed_order_padding_fillers_rejected(self):
  sequences=['ACGT','NAC'];t,l,p=pack(sequences);validate_batch(t,l,p,sequences)
  for kind in ['wrongrow','filler','length','positions']:
   tt,ll,pp=t.clone(),l.clone(),p.clone()
   if kind=='wrongrow':tt[0,0]=67
   elif kind=='filler':tt[7,0]=65
   elif kind=='length':ll[0]+=1
   else:pp=pp.flip(1)
   with self.assertRaises(ValueError):validate_batch(tt,ll,pp,sequences)
 def test_LM_head_shape_mask_and_saved_counts_rejected(self):
  t,l,p=pack(['ACGTN']);logits=torch.zeros((8,1000,512))
  with self.assertRaises(ValueError):production_loss(logits[:,:,:256],t,l,p)
  with self.assertRaises(ValueError):production_loss(logits,t,l,p+1)
  ids=[str(i) for i in range(12)]
  with self.assertRaises(ValueError):check_real_population(ids,ids,values(),np.ones(12,np.float32),np.full(12,9),np.full(12,9))

class MetadataChecks(unittest.TestCase):
 def test_metadata_arbitrary_global_rejected(self):
  import pickle
  from native_loader import restricted_metadata_load
  with self.assertRaises(ValueError):restricted_metadata_load(io.BytesIO(pickle.dumps(Path('/tmp/should-not-be-constructed'))))
 def test_native_extra_state_payloads_reject_learned_nonempty_and_unknown(self):
  import pickle
  from native_loader import validate_extra_state_blob
  def blob(v):
   b=io.BytesIO();torch.save(v,b);return b.getvalue()
  for v in [[None],[torch.empty(0,dtype=torch.uint8)],[torch.tensor(list(pickle.dumps(None)),dtype=torch.uint8)],[torch.tensor(list(pickle.dumps({})),dtype=torch.uint8)]]:self.assertEqual(validate_extra_state_blob(blob(v))['learned_tensor_values'],0)
  for v in [[torch.ones(3)],[torch.empty(0,dtype=torch.float32)],[None,None],[torch.tensor(list(pickle.dumps({'nonempty':1})),dtype=torch.uint8)],{'unwrapped':None}]:
   with self.assertRaises(ValueError):validate_extra_state_blob(blob(v))

 def test_metadata_all_selected_indexes(self):
  from native_loader import restricted_metadata_load
  for p in Path(__file__).parent.parent.glob('checkpoints/*/.metadata'):
   with p.open('rb') as f:self.assertGreater(len(restricted_metadata_load(f).state_dict_metadata),0)

if __name__=='__main__':
 torch.set_num_threads(4);result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)));raise SystemExit(not result.wasSuccessful())
