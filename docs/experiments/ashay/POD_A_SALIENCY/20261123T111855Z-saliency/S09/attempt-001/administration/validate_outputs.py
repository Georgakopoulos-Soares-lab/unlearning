from ops import C,A,R,save,now
import sys,json,hashlib,re,collections
from pathlib import Path
sys.path.insert(0,str(A/'code'));from s09_common import P,read,rows,sha,digest,TASKS,REPS,SEEDS,POLICIES
pkg=Path('/workspace/pod-a-saliency/control/20261123T111855Z-saliency/ADMIN/part-a-001/verified-published-package');import jsonschema
schema=read(pkg/'S_RESULT_SCHEMAS.json');validator=jsonschema.Draft202012Validator({'$ref':'#/$defs/metric','$defs':schema['$defs']});admitted=rows(C/'FROZEN_ADMITTED_KEYS.jsonl');deferred=rows(C/'FROZEN_DEFERRED_KEYS.jsonl');allrows=[];seen=set()
for path in sorted((P/'contrasts').glob('*/*/CONTRASTS.jsonl')):
 for row in rows(path):
  assert row['id'] not in seen and row['status']=='VERIFIED';seen.add(row['id']);validator.validate(row['canonical_metric']);allrows.append(row)
assert seen=={r['id'] for r in admitted} and len(seen)==48924
assert collections.Counter(r['f'] for r in allrows)=={'base_reference':42120,'DNA_control':6480,'anchor_policy_gap':324}
assert sum(r['bootstrap_attempted'] for r in allrows)==sum(r['bootstrap_valid'] for r in allrows)==97848000 and sum(r['bootstrap_invalid'] for r in allrows)==0
for name,family,count in [('PARENT_RELATIVE_EFFECTS.jsonl','immediate_parent',42120),('LM_CONTRASTS.jsonl','LM_base_reference',108)]:
 rr=rows(P/name);assert len(rr)==count and {r['id'] for r in rr}=={r['id'] for r in deferred if r['f']==family};assert all(r['status']=='DEFERRED' and r['estimate'] is None and r['ci_low'] is None and r['ci_high'] is None and r['missing_reason'] for r in rr)
prof=rows(P/'LAYER_PROFILES.jsonl');assert len(prof)==42120 and len({(r['candidate'],r['task'],r['representation'],r['seed'],r['policy'],r['metric']) for r in prof})==42120
for task in TASKS:
 assert {r['representation'] for r in prof if r['task']==task}==set(REPS) and {r['seed'] for r in prof if r['task']==task}==set(SEEDS) and {r['policy'] for r in prof if r['task']==task}==set(POLICIES)
source=read(C/'REPORTING_SOURCE_IDENTITY.json')
for name,h in source['files'].items():assert sha(A/'code'/name)==sha(P/'code'/name)==h
manifest=read(P/'FIGURE_MANIFEST.json');assert manifest['figures']==111 and set(manifest['unique_layout_families'])=={'coverage','profiles','forests','heatmaps','gaps','sweep','metrics','seeds'}
for r in manifest['records']:
 for export in r['exports']:assert sha(P/'figures'/export['path'])==export['sha256']
 assert sha(P/'figure-specs'/(r['id']+'.json'))==next(v['spec_file_sha256'] for v in read(P/'PLOT_SOURCE_INDEX.json')['figures'] if v['id']==r['id'])
plot=read(P/'PLOT_SOURCE_INDEX.json');assert plot['unique_profile_rows_in_profiles']==42120 and plot['unique_contrasts_in_figures']==48924
for name,h in read(P/'CLAIM_VALIDATION.json')['source_tables'].items():assert sha(P/name)==h
assert sha(P/'ANALYSIS.md')==read(P/'CLAIM_VALIDATION.json')['analysis_sha256']
files=[]
for p in sorted(P.rglob('*')):
 if not p.is_file():continue
 assert not p.is_symlink() and p.stat().st_size<90*1024**2,(str(p),p.stat().st_size);b=p.read_bytes();assert not re.search(rb'\bhf_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+|X-Goog-Signature=[A-Za-z0-9%]{8,}|X-Amz-Signature=[A-Za-z0-9%]{8,}',b),str(p);assert (b'ashay-sriv/'+b'undo-') not in b and (b'ashay-sriv/'+b'unlearning-checkpoint-mirror') not in b;assert p.suffix not in ['.npz','.npy','.joblib','.pt','.distcp','.tar','.gz']
 if p.suffix=='.json':json.loads(b)
 if p.suffix=='.jsonl':
  for line in b.splitlines():json.loads(line)
 files.append({'path':str(p.relative_to(P)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()})
save(C/'OUTPUT_VALIDATION.json',{'status':'PASS','canonical_metric_schema_rows':48924,'admitted_exact_key_equality':True,'deferred_exact_key_equality':True,'whole_frozen_universe':91152,'verified_draw_differences':97848000,'all_target_profile_rows':42120,'all_plotted_profile_rows':42120,'all_plotted_contrast_rows':48924,'figures':111,'source_identity_and_claim_bindings_unchanged':True,'publication_file_allowlist':files,'public_bytes':sum(v['bytes'] for v in files),'raw_predictions_or_private_locators_in_public':False,'scientific_freezes_unchanged':True,'observed_utc':now()});save(P/'OUTPUT_VALIDATION.json',{k:v for k,v in read(C/'OUTPUT_VALIDATION.json').items() if k!='publication_file_allowlist'});print('S09_ALL_SCIENTIFIC_OUTPUTS_VALIDATED',len(files),flush=True)
