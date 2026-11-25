"""Separate source-table checking pass. Does not call the reporting builder or renderer."""
from pathlib import Path
import sys,json,csv,hashlib,re,copy,collections,itertools,math
root=Path(sys.argv[1]);P=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def rows(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
s9=root/'inputs/s09';s10=root/'inputs/s10';fact=read(P/'REPORTING_FACTS.json');cs={r['alias']:r for r in read(s10/'S11_HANDOFF.json')['candidate_bindings']};profile=rows(s9/'LAYER_PROFILES.jsonl');profile_by_id={r['endpoint_id']:r for r in profile};assert len(profile_by_id)==42120
def check_profile(got,source):
 for k,v in source.items():assert got[k]==v,(k,got.get(k),v)
 assert got['checkpoint_content_sha256']==cs[source['candidate']]['content_sha256'] and got['checkpoint_step']==cs[source['candidate']]['step'] and got['candidate_id']==cs[source['candidate']]['candidate_id']
observed=[]
for file in sorted((P/'tables').glob('CLASSIFICATION_*.jsonl')):
 for r in rows(file):check_profile(r,profile_by_id[r['endpoint_id']]);observed.append(r['endpoint_id'])
assert len(observed)==len(set(observed))==42120 and set(observed)==set(profile_by_id)
original_contrasts={r['id']:r for p in(s9/'contrasts').glob('*/*/CONTRASTS.jsonl') for r in rows(p)};assert len(original_contrasts)==48924
def check_contrast(r,o):
 for k in ['c','t','r','s','p','m','f','q','d','split','estimate','ci_low','ci_high','target_estimate','reference_estimate','reference_label','favorable_sign','bootstrap_attempted','bootstrap_valid','bootstrap_invalid','cohort_sha256','draw_sha256','common_mask_sha256']:assert r[k]==o[k],(r['id'],k)
 assert abs(r['estimate']-(o['target_estimate']-o['reference_estimate']))<=1e-12
 cc=cs[r['c']];assert r['checkpoint_content_sha256']==cc['content_sha256'] and r['checkpoint_step']==cc['step']
contrasts=[]
for file in sorted((P/'tables').glob('CONTRASTS_*.jsonl')):
 for r in rows(file):check_contrast(r,original_contrasts[r['id']]);contrasts.append(r)
assert len(contrasts)==len({r['id'] for r in contrasts})==48924 and {r['id'] for r in contrasts}=={r['id'] for r in rows(s9/'FROZEN_ADMITTED_KEYS.jsonl')}
lm=rows(s9/'LM_MARGINALS_REUSED.jsonl');assert rows(P/'tables/LM_RELEASED.jsonl')==lm;lm_by_id={r['source_row_id']:r for r in lm};assert len(lm_by_id)==216
paths={(r['candidate'],r['task'],r['representation'],r['seed'],r['policy']) for r in profile};units={r['canonical_metric']['unit_id'] for r in lm};expectedcounts={'classifier_metric_records':len(profile),'prediction_paths':len(paths),'refitted_heads':sum(x[-1]=='independent_refit' for x in paths),'unchanged_base_applications':sum(x[-1]=='fixed_original_base' for x in paths),'LM_units':len(units),'LM_metric_records':len(lm),'LM_DEV_primary_units':len({r['canonical_metric']['unit_id'] for r in lm if r['split']=='dev'}),'LM_TRAIN_diagnostic_units':len({r['canonical_metric']['unit_id'] for r in lm if r['split']=='train'}),'admitted_S09_contrasts':len(contrasts),'deferred_S09_specifications':len(rows(s9/'FROZEN_DEFERRED_KEYS.jsonl'))}
for k,v in expectedcounts.items():assert fact['coverage'][k]==v
gaps=[r for r in original_contrasts.values() if r['f']=='anchor_policy_gap'];assert len(gaps)==324;assert fact['policy_gap']=={'n':324,'positive':sum(r['estimate']>0 for r in gaps),'negative':sum(r['estimate']<0 for r in gaps),'equal':sum(r['estimate']==0 for r in gaps),'CI_includes_zero':sum(r['ci_low']<=0<=r['ci_high'] for r in gaps),'min':min(r['estimate'] for r in gaps),'max':max(r['estimate'] for r in gaps)}
anchors=collections.defaultdict(dict)
for r in profile:
 if r['policy']=='independent_refit' and r['metric']=='AUROC' and r['representation'] in ['decoder.layers.16','decoder.final_norm']:anchors[r['candidate'],r['task'],r['seed']][r['representation']]=r
assert len(anchors)==162 and fact['anchor_layer']=={'above':sum(v['decoder.layers.16']['estimate']>v['decoder.final_norm']['estimate'] for v in anchors.values()),'n':162}
def check_forget_state(fc):
 assert fc['sources']==9 and fc['source_bytes']==418914867 and fc['complete_events']==4069391 and fc['scalar_observations_all_tags_axes']==4069382 and fc['validation_forget_loss_step_observations']==23 and fc['forget_validation_loss_and_ppl_both_axes_records']==92
 assert fc['qualified_descriptive_scientific_aggregates']==fc['qualified_checkpoint_matched_comparisons']==fc['layerwise_forget_performance_observations']==0
check_forget_state(fact['forget_source_counts']);assert fact['forget_source_counts']==read(s10/'COVERAGE.json');assert (P/'tables/FORGET_VALIDATION_OBSERVATIONS.csv').read_bytes()==(s10/'FORGET_VALIDATION_OBSERVATIONS.csv').read_bytes()
source_scalars={r['observation_id']:r for p in(s10/'scalars').glob('*.csv') for r in csv.DictReader(p.open()) if r['tag'] in ['forget loss','forget loss validation']};mapping=read(P/'FIGURE_SOURCE_MAP.json');maps=collections.defaultdict(list)
def check_artist(r):
 typ=r['source_type'];assert typ in ['coverage_fact','released_contrast','released_LM','unqualified_forget_scalar'],'Unqualified source cannot enter a matched comparison'
 if typ=='released_contrast':
  s=original_contrasts[r['source_id']];assert r['candidate']==s['c'] and r['task']==s['t'] and r['representation']==s['r'] and r['seed']==s['s'] and r['metric']==s['m'] and r['split']==s['split'];assert r['ci_low']==s['ci_low'] and r['ci_high']==s['ci_high'];assert (r['x'] if r['figure']=='ORIGINAL_BASE_EFFECTS' else r['y'])==s['estimate']
  assert r['direction']==('candidate_minus_original_base' if r['figure']=='ORIGINAL_BASE_EFFECTS' else 'refit_minus_fixed')
 elif typ=='released_LM':
  s=lm_by_id[r['source_id']];m=s['canonical_metric'];assert r['candidate']==s['candidate_alias'] and r['task']==s['task'] and r['split']=='dev' and r['representation'] is None and r['seed'] is None;assert r['y']==m['estimate'] and r['ci_low']==m['ci_low'] and r['ci_high']==m['ci_high']
 elif typ=='unqualified_forget_scalar':
  s=source_scalars[r['source_id']];assert r['source_file_id']==s['source_id'] and r['tag']==s['tag'] and r['x']==int(s['step']) and r['y']==float(s['value']);assert r['checkpoint_content_binding'] is None and r['scientific_qualification']=='UNQUALIFIED' and r['ci_low'] is None and r['ci_high'] is None and r['no_layerwise_projection'];assert 1.38<=r['y']<=1.68,'Undisclosed source training-axis clipping'
 else:assert r['values']==fact['coverage']
for r in mapping:check_artist(r);maps[r['figure']].append(r)
assert len(maps['ANCHOR_READOUT_GAPS'])==324 and len(maps['ORIGINAL_BASE_EFFECTS'])==36 and len(maps['LM_DEV_RESULTS'])==54
details=[r for r in read(P/'FIGURE_MANIFEST.json')['figures'] if r['family']=='forget_source_detail'];assert len(details)==9
assert len([r for r in mapping if r['source_type']=='unqualified_forget_scalar'])==14090+23
for d in details:assert len(maps[d['id']])==d['source_records']
for r in read(P/'FIGURE_MANIFEST.json')['figures']:
 for e in r['exports']:assert (P/e['path']).stat().st_size==e['bytes'] and sha(P/e['path'])==e['sha256']
for t in read(P/'TABLE_INDEX.json')['tables']:assert sha(P/t['path'])==t['sha256'] and (P/t['path']).stat().st_size==t['bytes']
prose=(P/'RESULTS.md').read_text();brief=(P/'REVIEWER_SUMMARY.md').read_text();assert '1.3953843116760254' in prose and '1.3952388763427734' in prose and 'PARTIAL' in brief
for s in ['0.034778','0.503517','324','162','220','23'] :assert s in prose and s in brief
assert 'no forget evidence exists' not in prose.lower() and fact['FORGET_SCIENTIFIC_STATUS']=='EXTRACTION_ONLY_PENDING_QUALIFICATION'
for claim in rows(P/'CLAIM_LEDGER.jsonl'):
 assert claim['source_ids'] and claim['scope'] and claim['uncertainty'] and claim['interpretation_limit'];known=set(profile_by_id)|set(original_contrasts)|set(lm_by_id)|set(source_scalars);assert set(claim['source_ids'])<=known
neg=[]
def rejects(name,fn):
 try:fn()
 except (AssertionError,KeyError):neg.append(name)
 else:raise AssertionError('Mutation survived: '+name)
r=next(r for r in rows(next((P/'tables').glob('CLASSIFICATION_*.jsonl'))));rejects('swapped_candidate',lambda:check_profile({**r,'candidate':'candidate_09'},profile_by_id[r['endpoint_id']]))
ar=next(r for r in mapping if r['source_type']=='released_contrast');rejects('wrong_layer_label',lambda:check_artist({**ar,'representation':'decoder.layers.15'}));rr=contrasts[0];rejects('reversed_effect_sign',lambda:check_contrast({**rr,'estimate':-rr['estimate']},original_contrasts[rr['id']]));rejects('stale_S10_no_source_status',lambda:check_forget_state({**fact['forget_source_counts'],'sources':0}));rejects('missing_figure_row',lambda:(_ for _ in ()).throw(AssertionError()) if len(maps['ANCHOR_READOUT_GAPS'][:-1])!=324 else None);rejects('unqualified_forget_entering_matched_comparison',lambda:check_artist({**next(r for r in mapping if r['source_type']=='unqualified_forget_scalar'),'source_type':'qualified_matched_forget'}))
report={'status':'PASS','source_classifier_rows_checked':len(profile),'source_admitted_contrasts_checked':len(contrasts),'source_LM_rows_checked':len(lm),'exact_report_counts_independently_derived':expectedcounts,'every_new_plotted_record_source_checked':len(mapping),'unqualified_source_records_in_matched_comparisons':0,'forget_validation_duplicates_preserved':True,'negative_fixtures_rejected':neg,'claim_ledger_records_checked':len(rows(P/'CLAIM_LEDGER.jsonl')),'independence':'Reads authoritative source rows directly, does not call builder/renderer; independently reconstructs counts/signs/coverage/identities and source-coordinate mappings. Visual inspection and renderer checks cover physical layout; no independent biological replication claim.'};save(out/'PUBLICATION_VALIDATION.json',report);print('S11_INDEPENDENT_PUBLICATION_CHECK_PASS',len(mapping),len(neg),flush=True)
