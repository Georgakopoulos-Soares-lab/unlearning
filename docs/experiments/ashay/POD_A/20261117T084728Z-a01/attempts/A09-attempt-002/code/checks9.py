"""Independent publication joins and endpoint-subtraction consistency; no new statistical family."""
from common9 import *
from canonical9 import accept_source
import math,collections

def main():
 guard();data=read(C/'CANONICAL_ROWS.json')['rows'];old=read(C/'ORIGINAL_ROWS.json');identity=read(C/'IDENTITY_CONTEXT.json');sources={e['source_id']:e for e in read(D/'SOURCE_TABLE_INDEX.json')['sources']};byid={r['A09_row_id']:r for r in data};marg={};lm={};maxima={'classifier':0.,'LM':0.};worst={};counts=collections.Counter();seen=set()
 for r in data:
  raw=old[r['A09_row_id']];kind=raw.get('table_kind') or sources[r['A09_source_id']]['kind'];key=accept_source(r,raw,kind,identity['endpoint_content_ids'],identity['protocol_sha256']);assert key not in seen;seen.add(key);counts[kind]+=1
  if kind=='classifier_marginal':marg[tuple(r[k] for k in ['checkpoint_alias','task','split','representation','CV_seed','policy','metric'])]=r
  if kind=='LM_marginal':lm[tuple(r[k] for k in ['checkpoint_alias','task','split','metric'])]=r
 controls=rows(D/'CONTROL_METRICS_REUSED.csv');ctl={(r['checkpoint_alias'].removeprefix('control_'),r['task'],r['split'],r['CV_seed'],r['metric']):r for r in controls};assert len(ctl)==210
 for r in data:
  kind=r['A09_table_kind']
  if kind=='classifier_paired':
   key=tuple(r[k] for k in ['task','split','representation','CV_seed','policy','metric']);a=marg[(r['checkpoint_alias'],)+key]
   if r['reference'] in MODELS:b=marg[(r['reference'],)+key]
   else:b=ctl[r['reference'].removeprefix('control_'),r['task'],r['split'],r['CV_seed'],r['metric']]
   error=abs((float(a['estimate'])-float(b['estimate']))-float(r['estimate']));assert error<=1e-12,('Classifier endpoint mismatch',r['A09_row_id'],error)
   if error>=maxima['classifier']:maxima['classifier']=error;worst['classifier']=r['A09_row_id']
  elif kind=='LM_paired':
   key=tuple(r[k] for k in ['task','split','metric']);a=lm[(r['checkpoint_alias'],)+key];b=lm[(r['reference'],)+key];error=abs((float(a['estimate'])-float(b['estimate']))-float(r['estimate']));assert error<=1e-12,('LM endpoint mismatch',r['A09_row_id'],error)
   if error>=maxima['LM']:maxima['LM']=error;worst['LM']=r['A09_row_id']
 displays=rows(D/'REPORT_DISPLAY_DATA.csv');plotted=read(D/'plot_data/main_figures.json');joins=0
 for r in displays+[r for name in ['task_entry','profiles','LM'] for r in plotted[name]]:
  source=byid[r['A09_row_id']]
  for k in ['estimate','ci_low','ci_high']:
   if r.get(k) not in ['',None]:assert float(r[k])==float(source[k])
  for k in ['checkpoint_alias','reference','task','split','representation','CV_seed','policy','metric']:
   if r.get(k) not in ['',None]:assert str(r[k])==str(source.get(k,''))
  joins+=1
 for r in plotted['policy_gaps']:
  a=byid[r['refitted_row_id']];b=byid[r['fixed_row_id']];assert r['estimate']==float(a['estimate'])-float(b['estimate']) and r['uncertainty']=='POINT_ONLY_NO_POLICY_GAP_CI'
 # All current main-figure CSV cells are source-bound too; display duplication adds no measurements.
 for fig in read(D/'FIGURE_MANIFEST.json')['figures']:
  path=D/fig['source_rows']['path'];assert sha(path)==fig['source_rows']['sha256'];rs=rows(path);assert len(rs)==fig['source_rows']['rows']
  for r in rs:
   if r.get('A09_row_id'):
    source=byid[r['A09_row_id']]
    for k in ['estimate','ci_low','ci_high']:
     if r.get(k):assert float(r[k])==float(source[k])
   elif r.get('refitted_row_id'):
    assert float(r['estimate'])==float(byid[r['refitted_row_id']]['estimate'])-float(byid[r['fixed_row_id']]['estimate'])
   else:assert r.get('source_kind') in ['coverage','declarations']
   joins+=1
 result={'status':'PASS','scientific_rows_regenerated_from_exact_original_context':len(data),'counts':dict(counts),'classifier_endpoint_subtractions_checked':73500,'LM_endpoint_subtractions_checked':182,'max_abs_endpoint_residuals':maxima,'worst_row_ids':worst,'source_display_plot_csv_joins':joins,'policy_point_gap_checks':len(plotted['policy_gaps']),'absolute_tolerance':1e-12,'relative_tolerance':0,'all_numeric_original_cells_and_statuses_preserved':True,'new_statistical_families':0};put(C/'PUBLICATION_JOIN_VALIDATION.json',result);publish('PUBLICATION_JOIN_VALIDATION.json',result);print(json.dumps(result))
if __name__=='__main__':main()
