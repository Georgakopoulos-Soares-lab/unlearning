"""Small CPU tests of adapter product algebra and safe descriptor policy."""
import io
import pathlib
import tempfile
import json
import pickle
import unittest
import numpy as np
from scripts.sayyed.adapter_trajectory import point,pair,factors,descriptors,DescriptorUnpickler,AnalysisError,model_chunks,InertRecord,verify_owned_output

class AdapterAlgebraTests(unittest.TestCase):
    def setUp(self):self.rng=np.random.default_rng(20261118)
    def arrays(self,m=11,n=13,r=4):return self.rng.normal(size=(r,n)),self.rng.normal(size=(m,r))
    def close(self,a,b):np.testing.assert_allclose(a,b,rtol=5e-11,atol=1e-12)
    def test_research_output_scope_rejected_before_git_or_compute(self):
        with tempfile.TemporaryDirectory()as tmp:
            root=pathlib.Path(tmp);(root/'APPROVAL.json').write_text(json.dumps(dict(worktree=str(root),documentation_root=str(root/'approved'))))
            with self.assertRaisesRegex(AnalysisError,'Unapproved research output'):verify_owned_output(root,root/'elsewhere')
    def test_rectangular_norms_spectra_and_rank(self):
        A,B=self.arrays();P=B@A;q=point(A,B,2);s=np.linalg.svd(P,compute_uv=False)
        self.close(q['P_norm'],np.linalg.norm(P));self.close(q['P_spectral'],s[0]);self.close(q['U_norm'],2*np.linalg.norm(P));self.close(q['P_RMS'],np.sqrt(np.mean(P*P)));self.close(q['singular_values'],s[:4]);self.close(q['stable_rank'],np.linalg.norm(P)**2/s[0]**2)
    def test_metrics_have_strict_JSON_scalar_types(self):
        A,B=self.arrays();json.dumps(point(A,B),allow_nan=False);json.dumps(pair(A,B,A,B),allow_nan=False)
    def test_dense_pair_distance_inner_cosine(self):
        A,B=self.arrays();C,D=self.arrays();q=pair(A,B,C,D,2,3);U=2*B@A;V=3*D@C
        self.close(q['distance'],np.linalg.norm(V-U));self.close(q['inner_product'],np.sum(U*V));self.close(q['cosine'],np.sum(U*V)/np.linalg.norm(U)/np.linalg.norm(V));self.close(q['relative_distance'],2*np.linalg.norm(V-U)/(np.linalg.norm(U)+np.linalg.norm(V)))
    def test_nonorthogonal_gauge_invariance(self):
        A,B=self.arrays();G=np.diag([1.,1.3,1.7,2.])+np.triu(self.rng.normal(scale=.04,size=(4,4)),1);C=G@A;D=B@np.linalg.inv(G)
        self.assertGreater(np.linalg.norm(C-A),.1);self.close(B@A,D@C);self.close(point(A,B)['P_norm'],point(C,D)['P_norm']);self.close(point(A,B)['singular_values'],point(C,D)['singular_values']);self.close(pair(A,B,C,D)['distance'],0)
    def test_factor_rescaling_and_sign_gauge(self):
        A,B=self.arrays();self.close(pair(A,B,7*A,B/7)['distance'],0);self.close(pair(A,B,-A,-B)['distance'],0)
    def test_identical_exactly_zero_distance(self):
        A,B=self.arrays();q=pair(A,B,A.copy(),B.copy());self.assertEqual(q['distance'],0);self.assertTrue(q['exact_same_factors']);self.close(q['cosine'],1)
    def test_zero_conventions(self):
        A,B=self.arrays();Z=np.zeros_like(B);q=point(A,Z);self.assertEqual(q['P_norm'],0);self.assertIsNone(q['stable_rank']);self.assertEqual(q['energy90_rank'],0)
        q=pair(A,Z,A,Z);self.assertEqual(q['relative_distance'],0);self.assertIsNone(q['cosine']);q=pair(A,Z,A,B);self.close(q['relative_distance'],2);self.assertIsNone(q['cosine'])
    def test_cancelling_zero_product_with_nonzero_factors(self):
        A=np.ones((2,5));B=np.array([[1.,-1.]]*7);q=point(A,B);self.assertTrue(q['numerical_zero']);self.assertFalse(q['exact_factor_zero']);self.close(q['P_raw_norm'],0)
    def test_opposite_products(self):
        A,B=self.arrays();q=pair(A,B,A,-B);self.close(q['relative_distance'],2);self.close(q['cosine'],-1)
    def test_near_identical_difference_stability(self):
        A,B=self.arrays();C=A+self.rng.normal(scale=1e-10,size=A.shape);D=B+self.rng.normal(scale=1e-10,size=B.shape);q=pair(A,B,C,D);self.close(q['distance'],np.linalg.norm(D@C-B@A));self.assertGreater(q['distance'],0)
    def test_unequal_rank(self):
        A,B=self.arrays(r=3);C,D=self.arrays(r=5);q=pair(A,B,C,D);self.close(q['distance'],np.linalg.norm(D@C-B@A));self.assertEqual(q['difference_method'],'CONCAT_FACTOR_QR')
    def test_changed_scale(self):
        A,B=self.arrays();q=pair(A,B,A,B,1,3);self.close(q['distance'],2*np.linalg.norm(B@A));self.close(q['relative_distance'],1)
    def test_invalid_orientation_and_nonfinite(self):
        A,B=self.arrays()
        with self.assertRaises(AnalysisError):factors(A.T,B)
        A[0,0]=np.nan
        with self.assertRaises(AnalysisError):point(A,B)
    def test_cached_scale_mismatch_rejected(self):
        A,B=self.arrays()
        with self.assertRaises(AnalysisError):pair(A,B,A,B,2,2,pi=point(A,B),pj=point(A,B))
    def test_unsafe_metadata_globals_rejected(self):
        raw=b"cposix\nsystem\n(S'NEVER_RUN_THIS'\ntR."
        with self.assertRaisesRegex(AnalysisError,'UNSAFE_METADATA_GLOBAL'):DescriptorUnpickler(io.BytesIO(raw)).load()
    def test_missing_unpaired_and_overlapping_chunks_rejected(self):
        schema={'decoder.x.adapter.linear_in.weight':{'shape':[2,3]}}
        typ=type('Inert_TensorStorageMetadata',(InertRecord,),{});meta=InertRecord();meta.state_dict_metadata={};meta.storage_data={}
        with self.assertRaises(AnalysisError):model_chunks(meta,schema)
        v=typ();v.size=(2,3);chunk=InertRecord();chunk.offsets=(0,0);chunk.sizes=(2,3);v.chunks=[chunk,chunk];meta.state_dict_metadata={next(iter(schema)):v};idx=InertRecord();idx.fqn=next(iter(schema));idx.offset=(0,0);info=InertRecord();info.relative_path='__0_0.distcp';info.offset=0;info.length=10;meta.storage_data={idx:info}
        with self.assertRaisesRegex(AnalysisError,'Overlapping'):model_chunks(meta,schema)
        v.chunks=[chunk];info.relative_path='../outside.distcp'
        with self.assertRaisesRegex(AnalysisError,'bounds/path'):model_chunks(meta,schema)

if __name__=='__main__':unittest.main()
