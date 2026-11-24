from s09_common import *
import html,sys,collections
root=Path(sys.argv[1]) if len(sys.argv)>1 else P
manifest=read(root/'FIGURE_MANIFEST.json');specs=[read(p) for p in sorted((root/'figure-specs').glob('*.json'))];assert len(specs)==manifest['figures']==111
family_names={'coverage':'Coverage and deferred comparisons','profiles':'Complete layer profiles','forests':'Paired anchor reference effects','heatmaps':'Complete original-base effect heatmaps','gaps':'All admitted anchor policy gaps','sweep':'Supplied endpoints and separate LM splits','metrics':'Ranking, decisions and classifier probability loss','seeds':'Descriptive CV-seed sensitivity'}
def pattern(s):
 vals=[v for p in s['panels'] if p['kind']=='lines' for line in p['lines'] for v in line['y']]
 if s['family'] in ['profiles','forests','gaps']:
  return f'Displayed point values span {min(vals):.6f} to {max(vals):.6f}; {sum(v>0 for v in vals)} of {len(vals)} displayed points are positive. These are displayed observations, with repeated/shared dependencies retained, not independent replicates.'
 if s['family']=='heatmaps':
  values=[v for p in s['panels'] for row in p['values'] for v in row];return f'Complete signed effects span {min(values):.6f} to {max(values):.6f}; {sum(v<0 for v in values)} negative, {sum(v>0 for v in values)} positive and {sum(v==0 for v in values)} exactly zero cells. Favorability follows the metric direction, with lower classifier CE better.'
 if s['family']=='seeds':
  return 'Observed range by metric: '+ '; '.join(p['title'].split(' | ')[0]+f' max {max(v for pp in s["panels"][j:j+2] for row in pp["values"] for v in row):.6g}' for j,p in enumerate(s['panels']) if j%2==0)+'. Zero ranges are explicitly labeled; no CI is inferred from seeds.'
 if s['family']=='metrics':
  return 'Displayed anchor point ranges: '+ '; '.join(p['title'].split(' | ')[0]+f' {min(v for pp in s["panels"][j:j+2] for line in pp["lines"] for v in line["y"]):.6f}–{max(v for pp in s["panels"][j:j+2] for line in pp["lines"] for v in line["y"]):.6f}' for j,p in enumerate(s['panels']) if j%2==0)+'. Ranges are metric-specific and descriptive.'
 if s['family']=='sweep':return 'The two noise-5% endpoints at steps2000 and2151 remain separate. Each task/metric has its own labeled axis, with NLL and perplexity kept distinct; TRAIN panels are diagnostic only.'
 return '48,924 admitted and42,228 deferred keys exhaust the frozen91,152 specification universe; deferred is not a measured zero.'
captions={s['id']:s['caption']+' '+pattern(s) for s in specs};save(root/'FIGURE_CAPTIONS.json',captions)
md='# Figure atlas and source guide\n\nAll 111 figures are available as readable PNG and vector PDF/SVG. Every displayed value and interval bound was checked against exact source rows; complete machine-readable plot specifications and hashes are in PLOT_SOURCE_INDEX.json. Figures are descriptive/exploratory, with pointwise conditional uncertainty where shown. Source tables retain full precision.\n\n'
md+='## Compact reading sequence\n\nThe following figures illustrate the questions discussed in ANALYSIS.md. This reading sequence was chosen after outcome exposure; the complete atlas below preserves every task, metric, checkpoint, policy and seed.\n\n'
main=['coverage','profiles-emp_H3-AUROC','gaps-gue_prom_300_all','heatmaps-gue_prom_300_all-cross_entropy','metrics-gue_prom_300_all','supplied-LM-dev']
for fid in main:
 s=next(v for v in specs if v['id']==fid);md+='### '+s['title']+'\n\n[PNG](figures/'+fid+'.png) · [PDF](figures/'+fid+'.pdf) · [SVG](figures/'+fid+'.svg)\n\n'+captions[fid]+'\n\n'
md+='## Complete supplementary atlas\n\n'
for fam,name in family_names.items():
 md+='### '+name+'\n\n| Figure | PNG | PDF | SVG | Exact source specification |\n|---|---|---|---|---|\n'
 for s in specs:
  if s['family']==fam:
   fid=s['id'];md+='| '+s['title']+' | [PNG](figures/'+fid+'.png) | [PDF](figures/'+fid+'.pdf) | [SVG](figures/'+fid+'.svg) | [JSON](figure-specs/'+fid+'.json) |\n'
 md+='\n'
md+='Every individual caption, including its descriptive observed range and interpretation limits, is recorded in [FIGURE_CAPTIONS.json](FIGURE_CAPTIONS.json). The searchable [HTML gallery](FIGURE_GALLERY.html) displays captions and source links together.\n';(root/'FIGURE_GALLERY.md').write_text(md)
cards=[]
for s in specs:
 fid=s['id'];cards.append('<article data-search="'+html.escape((s['family']+' '+s['title']).lower(),quote=True)+'"><h2>'+html.escape(s['title'])+'</h2><a href="figures/'+fid+'.png"><img loading="lazy" src="figures/'+fid+'.png" alt="'+html.escape(s['title'],quote=True)+'"></a><p>'+html.escape(captions[fid])+'</p><p><a href="figures/'+fid+'.pdf">Vector PDF</a> · <a href="figures/'+fid+'.svg">SVG</a> · <a href="figure-specs/'+fid+'.json">Source specification</a></p></article>')
page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Pod A · verified benign comparison atlas</title><style>body{font:16px/1.6 system-ui,sans-serif;max-width:1500px;margin:auto;padding:30px;background:#f6f8fb;color:#15283b}header{border-bottom:3px solid #246b9e;padding-bottom:20px}input{width:min(650px,90%);padding:14px;border:1px solid #8196aa;border-radius:8px;font-size:16px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:24px;margin-top:24px}article{background:white;padding:22px;border:1px solid #d9e2eb;border-radius:12px}img{width:100%;max-height:560px;object-fit:contain;background:#fff}h1{line-height:1.15;font-size:42px}h2{font-size:18px}a{color:#12609c}small{display:block;color:#405568}</style><header><small>POD A · S09 · all admitted benign comparisons</small><h1>Accessibility and readout compatibility</h1><p>111 figures · six benign tasks · nine supplied endpoints · all26 representations · all3 CV partitions · both readout policies.</p><p>48,924 verified comparisons. 42,228 deferred specifications preserved. Pointwise exploratory conditional intervals; no causal or forgetting conclusion.</p><p><a href="ANALYSIS.md">Scientific report</a> · <a href="FIGURE_GALLERY.md">Atlas index</a> · <a href="CLAIM_EVIDENCE_LEDGER.jsonl">Claims and exceptions</a></p><label for="search">Filter by task, metric or figure family</label><br><input id="search" placeholder="e.g. emp_H3 AUROC, gaps, heatmaps, seeds"><p id="count">111 figures</p></header><main>'+''.join(cards)+'</main><script>const q=document.getElementById("search");q.addEventListener("input",()=>{const terms=q.value.toLowerCase().split(/\s+/).filter(Boolean);let count=0;document.querySelectorAll("article").forEach(x=>{x.hidden=!terms.every(t=>x.dataset.search.includes(t));if(!x.hidden)count++});document.getElementById("count").textContent=count+" figures"});</script></html>'
(root/'FIGURE_GALLERY.html').write_text(page);print('NAVIGABLE_GALLERY_GENERATED',111,flush=True)
