"""Attach complete released-row keys to render data; no plotting/numeric changes."""
from common import *
from research_guard import guard
def rr(p):return list(csv.DictReader(Path(p).open()))
def key(r):return tuple(r.get(k,'') for k in ['checkpoint_alias','reference','task','split','representation','CV_seed','policy','metric'])
def main():
 parts=read(D/'TABLE_PARTITIONS.json')['logical_PAIRED_CONTRASTS']['partitions'];sources=['VERIFIED_METRICS.csv','CONTROL_METRICS_REUSED.csv','LM_METRICS_VERIFIED.csv','LM_CONTRASTS_VERIFIED.csv']+[p['file'] for p in parts];lookup={}
 for n in sources:
  for r in rr(D/n):assert key(r) not in lookup;lookup[key(r)]=r
 p=D/'PLOT_DATA/plotted_values.csv';before=sha(p);rows=rr(p);extra=['plot_record_index','reference_endpoint_id','reference_policy','protocol_sha256','coverage_plan_sha256','contrast_id','prediction_sha256','reference_prediction_sha256','draw_sha256','source_sha256'];fields=list(rows[0])+[k for k in extra if k not in rows[0]]
 for index,r in enumerate(rows):
  original=lookup[key(r)]
  for k in ['estimate','ci_low','ci_high','status','original_endpoint_id']:assert r[k]==original[k]
  for k in extra:r[k]=str(index) if k=='plot_record_index' else original[k]
 guard(allow_dirty=True)
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
 figure=read(D/'FIGURE_VALIDATION.json');figure.setdefault('rendered_plot_data_sha256_before_key_completion',before);figure['plotted_values_csv_sha256']=sha(p);figure['plot_key_completion']={'status':'PASS','rows':len(rows),'helper':ref(__file__),'only_added_exact_metadata_fields':extra,'all_numeric_strings_and_rendered_assets_unchanged':True};publish('FIGURE_VALIDATION.json',figure)
 schema=read(D/'RESULT_SCHEMAS.json');schema['plot_data_primary_key']=['figure','plot_record_index'];schema['plot_scientific_key']=schema['paired_primary_key'];schema['repeated_plot_uses']='A shared control can be drawn in both readout panels; plot_record_index identifies each use without creating a new scientific measurement or fit';schema['plot_data_key_nulls']='Reference endpoint/policy null for marginal points; control representation null; LM representation and CV_seed null; all exact keys join released tables';publish('RESULT_SCHEMAS.json',schema);print(json.dumps({'status':'PASS','rows':len(rows),'new_fields':extra}))
if __name__=='__main__':main()
