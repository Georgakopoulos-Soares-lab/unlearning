"""Reporting acceptance checks; no numerical release audit or fitting."""
from common import *
from research_guard import guard
import re,ast
def main():
 guard(allow_dirty=True);schemas=read(D/'RESULT_SCHEMAS.json');counts={};links=[]
 for name in ['RESULTS_LONG','PAIRED_CONTRASTS']:
  rows=list(csv.DictReader((D/(name+'.csv')).open()));schema=schemas[name];assert len(rows)==(7800 if name=='RESULTS_LONG' else 16800);assert len({tuple(r[k] for k in schema['primary_key']) for r in rows})==len(rows);assert all(set(schema['required'])<=set(r) for r in rows)
  for r in rows:
   assert r['lineage']=='NEW' and r['ingestion_status']=='NEW_IN_A07' and r['status']=='COMPLETE_UNVERIFIED' and r['producer_validation']=='PASS';assert r['split']=='dev' and r['target_count']=='';assert int(r['sample_count'])==512 and int(r['group_count'])==(511 if r['task']=='gue_splice_reconstructed' else 512);assert int(r['bootstrap_attempted'])==2000==int(r['bootstrap_valid'])+int(r['bootstrap_invalid']);assert float(r['ci_low'])<=float(r['ci_high']);assert sha(A/r['receipt'])==r['receipt_sha256']
   for f in ['estimate','ci_low','ci_high']:assert r[f] not in ['nan','NaN','None','null'];float(r[f])
  counts[name]=len(rows)
 events=[json.loads(l) for l in (D/'PROGRESS_EVENTS.jsonl').read_text().splitlines()];assert len({x['event_id'] for x in events})==len(events);last=-1
 for e in events:
  assert e['stage']=='A07' and e['prompt_commit']==cfg['prompt_commit'];n=e['unit_counts']['new_final_heads_producer_complete'];assert last<=n<=780 and e['unit_counts']['remaining_A07']==780-n;last=n
 assert last==780 and read(BASE/'CONTROLLER_LATEST.json')['status']=='COMPLETE' and not read(BASE/'CONTROLLER_LATEST.json')['A08_started']
 for p in [BASE/'PROGRESS.md',D/'PROGRESS.md']:
  for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if target.startswith(('https:','http:','#')):continue
   q=(p.parent/target).resolve();assert q.is_file(),str(q);links.append({'report':str(p.relative_to(BASE)),'target':target})
 original=BASE/'attempts/A06-attempt-001/PAIRED_CONTRASTS.csv';old=list(csv.DictReader(original.open()));normalized=list(csv.DictReader((D/'A06_PAIRED_CONTRASTS.normalized.v1.csv').open()));assert len(old)==len(normalized)==6776 and all(all(a[k]==b[k] for k in a) for a,b in zip(old,normalized));assert all(r['lineage']=='NEW' and r['ingestion_status']=='REUSED_IN_A07' for r in normalized)
 for p in (D/'CODE').rglob('*.py'):ast.parse(p.read_text())
 result={'status':'PASS','table_counts':counts,'required_columns_and_unique_primary_keys':True,'full_precision_numeric_and_null_mapping':True,'receipt_links_hash_valid':True,'splice_rows_groups_distinct':True,'report_links':links,'events_monotonic_idempotent_identities':True,'A06_normalized_original_fields_unchanged':6776,'no_A08_execution':True,'scope':'Reporting/producer acceptance only; independent numerical release checks require fresh A08 approval','verified_utc':now()};put(C/'PUBLICATION_VALIDATION.json',result);publish('PUBLICATION_VALIDATION.json',result);print(json.dumps({'status':'PASS','tables':counts,'relative_report_links':len(links)}))
if __name__=='__main__':main()
