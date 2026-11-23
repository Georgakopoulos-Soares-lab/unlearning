import unittest,types
import torch
from qualification_contract import validate_tied_weight_contract
class Model:
 def __init__(self,tied,alias=False,extra=False):
  self.share_embeddings_and_output_weights=tied;e=torch.nn.Parameter(torch.tensor([[1.,2.],[3.,4.]]));self.embedding=types.SimpleNamespace(word_embeddings=types.SimpleNamespace(weight=e));h=e if alias else torch.nn.Parameter(e.detach().clone());self.output_layer=types.SimpleNamespace(weight=h if not tied or extra else None)
 def shared_embedding_or_output_weight(self):return self.embedding.word_embeddings.weight
 def named_parameters(self,remove_duplicate=False):
  out=[('embedding.word_embeddings.weight',self.embedding.word_embeddings.weight)]
  if self.output_layer.weight is not None:out.append(('output_layer.weight',self.output_layer.weight))
  return out
class TieTests(unittest.TestCase):
 def test_source_native_tied_head_uses_embedding_without_duplicate_weight(self):
  m=Model(True);r=validate_tied_weight_contract(m,{'embedding.word_embeddings.weight':m.embedding.word_embeddings.weight});self.assertTrue(r['output_layer_omits_duplicate_parameter'])
 def test_equal_values_do_not_justify_wrong_tying_relationship(self):
  for m in [Model(True,extra=True),Model(False,alias=True)]:
   with self.assertRaises(ValueError):validate_tied_weight_contract(m,{'embedding.word_embeddings.weight':m.embedding.word_embeddings.weight,'output_layer.weight':m.output_layer.weight})
 def test_true_untied_head_requires_own_checkpoint_tensor(self):
  m=Model(False);r=validate_tied_weight_contract(m,{'embedding.word_embeddings.weight':m.embedding.word_embeddings.weight,'output_layer.weight':m.output_layer.weight});self.assertFalse(r['share_embeddings_and_output_weights'])
  with self.assertRaises(ValueError):validate_tied_weight_contract(m,{'embedding.word_embeddings.weight':m.embedding.word_embeddings.weight})
if __name__=='__main__':unittest.main(verbosity=2)
