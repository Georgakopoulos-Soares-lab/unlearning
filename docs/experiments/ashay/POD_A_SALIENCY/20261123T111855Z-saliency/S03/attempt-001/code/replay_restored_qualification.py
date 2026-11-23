from pathlib import Path
import json,sys,hashlib
import numpy as np
from ops import C,A,save,now
n=int(sys.argv[1]);tag=f'qualification-checkpoint-{n:03d}';receipt=json.loads((C/(tag+'-RECEIPT.json')).read_text());root=Path(receipt['restored_root']);manifest=json.loads((root/'MEMBER_MANIFEST.json').read_text())['files']
for name,r in manifest.items():assert (root/name).stat().st_size==r['bytes'] and hashlib.sha256((root/name).read_bytes()).hexdigest()==r['sha256']
sys.path.insert(0,str(root/'code'));from qualification_contract import componentwise,LAYERS
rows=[]
def compare(label,p,q):
 a=np.load(p,allow_pickle=False);b=np.load(q,allow_pickle=False)
 for k in ['ids','task','labels','split','groups','sequence_sha256','lengths','n_tokens']:assert np.array_equal(a[k],b[k])
 metrics={k:{j:v for j,v in componentwise(a[k],b[k]).items() if j not in ['worst_observed','worst_reference']} for k in LAYERS+['nll_sum']};assert all(v['status']=='PASS' for v in metrics.values());rows.append({'comparison':label,'status':'PASS','outputs':metrics})
for aliasroot in sorted((root/'qualification').iterdir()):
 alias=aliasroot.name
 for variant in ['logical1','repeat8']:compare(alias+'/'+variant+'-vs-logical8',aliasroot/variant/'attempt-001/features_and_lm.npz',aliasroot/'logical8/attempt-001/features_and_lm.npz')
 if (aliasroot/'logical8/attempt-002/COMPLETE.json').exists():compare(alias+'/fresh-process-vs-producer',aliasroot/'logical8/attempt-002/features_and_lm.npz',aliasroot/'logical8/attempt-001/features_and_lm.npz')
report={'status':'PASS_RESTORED_CPU_REPLAY','archive_sha256':receipt['archive_sha256'],'immutable_revision':receipt['immutable_revision'],'verified_file_count':len(manifest),'comparisons':rows,'scope':'Fresh immutable private network read + exact member bytes + all26/LM CPU comparison replay using restored code and arrays; actual fresh model replay recorded independently','clean_runtime_rebuild':False,'verified_utc':now()};save(C/(tag+'-CPU_REPLAY.json'),report);print('RESTORED_CPU_REPLAY_PASS',len(manifest),len(rows))
