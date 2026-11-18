"""Join all provisional metrics and paired effects without ranking or selection."""
from common import *
from research_guard import guard
def build():
 rows=list(csv.DictReader((D/'RESULTS_LONG.csv').open()));paired=list(csv.DictReader((D/'PAIRED_CONTRASTS.csv').open()));key=['checkpoint_content_id','task','split','representation','CV_seed','policy','metric','protocol_sha256'];lookup={tuple(r[k] for k in key)+(r['reference'],):r for r in paired};assert len(lookup)==16800;joined=[]
 for row in rows:
  add={}
  for reference in ['base','R1','control_composition','control_kmer4']:
   match=lookup.get(tuple(row[k] for k in key)+(reference,));prefix=reference+'__'
   for n in ['estimate','ci_low','ci_high','bootstrap_valid','bootstrap_invalid','reference_policy','reference_prediction_sha256','draw_sha256','status']:add[prefix+n]=match[n] if match else None
   add[prefix+'missing_reason']=None if match else 'Control comparison was predeclared only for layer16/final_norm anchors'
  joined.append({**row,**add})
 assert len(joined)==7800;guard(allow_dirty=True)
 with (D/'TASK_LAYER_SEED_VIEW.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(joined[0]),lineterminator='\n');w.writeheader();w.writerows(joined)
 md='# Provisional predeclared AUROC anchor display\n\nAll40candidate/task/representation/policy cells below use seed42 and the predeclared layer16 (17th block)/final_norm anchors. This is not a best-layer or best-seed selection. Values remain producer-complete, independently unverified pending A08. Intervals are pointwise paired exact/RC-group bootstrap conditional on fitted heads. The complete five-metric,26-representation,three-seed join is TASK_LAYER_SEED_VIEW.csv; it retains full precision and all adverse/flat effects.\n\n| Candidate | Task | Hook | Policy | AUROC [95% CI] | Minus base [95% CI] | Minus R1 [95% CI] |\n|---|---|---|---|---:|---:|---:|\n'
 def fmt(r,prefix=''):
  return f"{float(r[prefix+'estimate']):.6f} [{float(r[prefix+'ci_low']):.6f}, {float(r[prefix+'ci_high']):.6f}]"
 anchors=[r for r in joined if r['CV_seed']=='42' and r['representation'] in ['decoder.layers.16','decoder.final_norm'] and r['metric']=='auroc'];assert len(anchors)==40
 for r in anchors:md+='| '+' | '.join([r['checkpoint_alias'],r['task'],r['representation'],r['policy'],fmt(r),fmt(r,'base__'),fmt(r,'R1__')])+' |\n'
 publish('PROVISIONAL_ANCHOR_VIEW.md',md);schema=read(D/'RESULT_SCHEMAS.json');schema['TASK_LAYER_SEED_VIEW']={'primary_key':key,'rows':7800,'base_metric_schema':'RESULTS_LONG','paired_fields':'Each reference__ field comes from matched PAIRED_CONTRASTS primary identity; no row intersection or score-dependent filtering','numeric_null_encoding':'Empty field=JSON null','control_missing_reason':'Not predeclared outside two anchor representations','status':'COMPLETE_UNVERIFIED'};publish('RESULT_SCHEMAS.json',schema)
 print(json.dumps({'joined_metric_rows':7800,'predeclared_AUROC_display_cells':40,'new_analysis_or_fit':False}))
if __name__=='__main__':build()
