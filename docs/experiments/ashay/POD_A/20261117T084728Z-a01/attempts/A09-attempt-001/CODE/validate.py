"""A09 exact key/claim/alias/figure/Markdown validation; no numerical production."""
from common import *
from research_guard import guard
import argparse,ast,collections,math,re
FIELDS=['original_endpoint_id','task','split','representation','CV_seed','policy','metric','protocol_sha256']
def pk(r):return tuple(r[k] for k in FIELDS)
def ck(r):return tuple(r[k] for k in ['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256'])
def validate(final=False):
 guard(allow_dirty=True);index=read(D/'TABLE_INDEX.json');allrows={};logical=[]
 for e in index['tables']:
  p=D/e['file'];assert p.is_file() and sha(p)==e['sha256'];rr=rows(p);assert len(rr)==e['rows'];allrows[e['logical_table'] if e['logical_table']!='PAIRED_CONTRASTS' else e['file']]=rr
  if e['logical_table']=='PAIRED_CONTRASTS':logical+=rr
 assert len(logical)==45360 and len({ck(r) for r in logical})==45360
 points=allrows['VERIFIED_METRICS'];controls=allrows['CONTROL_METRICS_REUSED'];lm=allrows['LM_METRICS_VERIFIED'];lmp=allrows['LM_CONTRASTS_VERIFIED'];assert [len(r) for r in [points,controls,lm,lmp]]==[27300,210,70,112];pmap={pk(r):r for r in points+controls+lm};assert len(pmap)==len(points)+len(controls)+len(lm)
 residual=0.;control_rows=0
 for r in logical+lmp:
  assert r['status'] in ['VERIFIED','REUSED_VALIDATED'] and r['direction']=='target-reference' and r['protocol_sha256']==cfg['protocol_sha256'];target=pmap[pk(r)];refkey=(r['reference_endpoint_id'],r['task'],r['split'],'' if r['reference_policy']=='control' else r['representation'],r['CV_seed'],r['reference_policy'],r['metric'],r['protocol_sha256']);reference=pmap[refkey];err=abs(float(r['estimate'])-(float(target['estimate'])-float(reference['estimate'])));assert err<=1e-12;residual=max(residual,err)
  if r['reference_policy']=='control':
   assert r['reference_endpoint_id']==reference['original_endpoint_id'] and r['reference_prediction_sha256']==reference['prediction_sha256'];control_rows+=1
 assert control_rows==1680
 aliases=rows(D/'ENDPOINT_ALIAS_MAP.csv');assert len(aliases)==480 and len({r['source_row_key'] for r in aliases})==480
 original=rows(D8/'PAIRED_CONTRASTS.H3_reused.csv');canonical=rows(D/'PAIRED_CONTRASTS.H3_canonical.v1.csv');assert len(original)==len(canonical)==6720
 for a,b in zip(original,canonical):
  assert b['original_reference_endpoint_id']==a['reference_endpoint_id']
  for k in a:
   if k!='reference_endpoint_id':assert a[k]==b[k],k
 release=rows(D/'AUDIT_RELEASE_STATUS.csv');assert len(release)==780 and len({r['unit_id'] for r in release})==780;assert sum(r['sampled_refit_required']=='True' for r in release)==60;assert all(r['all_unit_audit']=='PASS' and r['analysis_eligible']=='True' and r['producer_status']=='COMPLETE_UNVERIFIED' for r in release)
 coverage=rows(D/'COVERAGE.csv');missing=rows(D/'MISSING_UNIT_KEYS.csv');assert len(coverage)==6637 and len(missing)==1886 and len({r['unit_id'] for r in missing})==1886
 for n,count in [('PENDING_ADJACENT_CONTRASTS.csv',27300),('PENDING_ADJACENT_LM.csv',70)]:
  rr=rows(D/n);assert len(rr)==count and all(not r['estimate'] and not r['ci_low'] and not r['ci_high'] and r['reason'] for r in rr)
 source_cache={};claims=rows(D/'CLAIMS_TO_EVIDENCE.csv');assert len(claims)==420 and len({r['claim_id'] for r in claims})==420;displayvalues=set()
 for c in claims:
  filename=c['source_table'];p=D/filename;assert sha(p)==c['source_table_sha256'] and c['source_research_commit']==cfg['research_head_before']
  if filename not in source_cache:source_cache[filename]={ck(r):r for r in rows(p)}
  r=source_cache[filename][tuple(json.loads(c['row_key'])[k] for k in ['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256'])]
  for k in ['estimate','ci_low','ci_high','measurement_attempt','prediction_sha256','reference_prediction_sha256','draw_sha256','producer_receipt_sha256','audit_receipt_sha256']:assert c[k]==r[k]
  assert c['release_status']==r['status'] and r['status'] in ['VERIFIED','REUSED_VALIDATED']
  for k in ['estimate','ci_low','ci_high']:
   if c[k]:assert math.isfinite(float(c[k]));displayvalues.add(f"{float(c[k]):.6f}")
 for n in ['RESULTS.md','ONE_PAGE_SUMMARY.md','TEAM_UPDATE_DRAFT.md']:
  text=(D/n).read_text()
  for v in re.findall(r'(?<![A-Za-z0-9])[-+]?\d+\.\d{6}(?![A-Za-z0-9])',text):assert v in displayvalues,(n,v)
 # Original plot rows carry original IDs; apply only the exact recorded alias map.
 alias={r['source_row_key']:r for r in aliases};pairmap={ck(r):r for r in logical+lmp};plot=rows(D8/'PLOT_DATA/plotted_values.csv');assert len(plot)==30886;seen=set()
 for r in plot:
  assert (r['figure'],r['plot_record_index']) not in seen;seen.add((r['figure'],r['plot_record_index']))
  if r['reference']:
   key={k:r[k] for k in ['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256']};amap=alias.get(json.dumps(key,sort_keys=True))
   if amap:r=dict(r);r['reference_endpoint_id']=amap['canonical_reference_endpoint_id']
   source=pairmap[ck(r)]
  else:source=pmap[pk(r)]
  for k in ['estimate','ci_low','ci_high','status']:assert r[k]==source[k]
 figures=read(D8/'FIGURE_VALIDATION.json');assert len(figures['figures'])==31
 for f in figures['figures']:
  assert len(f['files'])==2
  for e in f['files']:assert sha(D8/e['path'])==e['sha256']
 assert read(D/'FIGURE_REUSE_VALIDATION.json')['status']=='PASS'
 graph=read(D/'RECOVERY_DEPENDENCY_GRAPH.json');assert graph['status']=='PASS' and len(graph['nodes'])==42;nodes={n['id']:n for n in graph['nodes']};visited=set();active=set()
 def visit(k):
  assert k in nodes and k not in active
  if k in visited:return
  active.add(k)
  for dep in nodes[k]['dependencies']:visit(dep)
  active.remove(k);visited.add(k)
 for k,n in nodes.items():assert n['current_local']['status']==n['current_remote']['status']=='PASS';visit(k)
 required=read(C/'A09_EXECUTION_MANIFEST.json')['deliverables'];missing_outputs=[n for n in required if not (D/n).exists()];allowed_pending={'BACKUP_MANIFEST.json','BACKUP_VERIFICATION.json','FRESH_RESTORE_CHECK.json','REPORT_VALIDATION.json','OUTPUT_SHA256SUMS','RESOURCE_CLOSEOUT.json','REMOTE_HANDOFF.json','A09_RECEIPT.json'};assert not final or not set(missing_outputs)-{'OUTPUT_SHA256SUMS','REPORT_VALIDATION.json'}
 jsons=csvs=sources=links=0;pending_links=[]
 for p in sorted(D.rglob('*')):
  if not p.is_file():continue
  assert not p.is_symlink() and p.resolve().is_relative_to(D.resolve());b=p.read_bytes();assert len(b)<(50 if p.suffix=='.csv' else 20)*1024**2;assert p.suffix not in ['.npz','.npy','.joblib','.pt','.bin','.distcp'];assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',b);assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',b)
  if p.suffix=='.json':json.loads(b,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)));jsons+=1
  elif p.suffix=='.jsonl':
   for line in b.splitlines():json.loads(line)
  elif p.suffix=='.csv':
   reader=csv.reader(b.decode().splitlines());h=next(reader);assert len(h)==len(set(h)) and all(len(r)==len(h) for r in reader);csvs+=1
  elif p.suffix=='.py':ast.parse(b);sources+=1
  elif p.suffix=='.md':
   text=b.decode();assert text.startswith('# ') and '\n\n' in text and not text.startswith('"');prose=re.sub(r'```.*?```','',text,flags=re.S)
   for target in re.findall(r'\]\(([^)]+)\)',prose):
    if target.startswith(('http:','https:','#','mailto:')):continue
    dest=(p.parent/target.split('#',1)[0]).resolve()
    if not dest.exists():
     assert not final and dest.parent==D.resolve() and dest.name in allowed_pending,(str(p),target);pending_links.append(target)
    else:links+=1
 # Immutable A08 index is checked after all A09 mutations, not merely at start.
 for e in read(C/'INPUT_VALIDATION.json')['files']:assert sha(D8/e['path'])==e['sha256']
 if final:
  fresh=read(D/'FRESH_RESTORE_CHECK.json');assert fresh['status']=='PASS' and fresh['consumer_checks']['path_count']==8 and len(fresh['consumer_checks']['restored_A08_refit_artifacts'])==2;assert read(D/'BACKUP_VERIFICATION.json')['status']=='PASS'
 result={'schema':'pod-a-a09-report-validation-v1','status':'PASS' if final else 'PASS_PREFLIGHT_PENDING_DELIVERY','all_three_repairs_pass':True,'logical_paired_keys':len(logical),'marginal_classifier_keys':len(points),'control_keys':len(controls),'LM_point_keys':len(lm),'LM_paired_keys':len(lmp),'typed_control_rows_joined':control_rows,'typed_H3_alias_rows':480,'paired_endpoint_difference_max_abs':residual,'released_row_claims_checked':len(claims),'plotted_released_records_checked':len(plot),'figure_pairs_hash_checked':31,'A08_predecessor_indexed_files_preserved':168,'dependency_nodes_resolved':len(visited),'pending_ledger_units':len(missing),'pending_classifier_edge_keys':27300,'pending_LM_edge_keys':70,'JSON_files_parsed':jsons,'CSV_files_parsed':csvs,'Python_sources_parsed':sources,'Markdown_links_resolved':links,'planned_outputs_pending':missing_outputs,'planned_links_pending':pending_links,'privacy_scan':'PASS','numerical_tolerances_unchanged':True,'new_scientific_measurements':0,'guard':guard(allow_dirty=True),'validated_utc':now()};put(C/'REPORT_VALIDATION.json',result);publish('REPORT_VALIDATION.json',result);print(json.dumps(result))
def seal():
 guard(allow_dirty=True);assert read(D/'REPORT_VALIDATION.json')['status'] in ['PASS','PASS_PREFLIGHT_PENDING_DELIVERY'];files=[{'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='OUTPUT_SHA256SUMS'];publish('OUTPUT_SHA256SUMS',''.join(e['sha256']+'  '+e['path']+'\n' for e in files));put(C/'PUBLICATION_SEAL.json',{'schema':'pod-a-a09-public-seal-v1','status':'PASS','files':files,'manifest_sha256':sha(D/'OUTPUT_SHA256SUMS'),'parent_commit':git('rev-parse','HEAD'),'self_manifest_excluded':True,'sealed_utc':now()});print(json.dumps({'status':'SEALED','files':len(files),'manifest_sha256':sha(D/'OUTPUT_SHA256SUMS')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--final',action='store_true');p.add_argument('--seal',action='store_true');a=p.parse_args();seal() if a.seal else validate(a.final)
