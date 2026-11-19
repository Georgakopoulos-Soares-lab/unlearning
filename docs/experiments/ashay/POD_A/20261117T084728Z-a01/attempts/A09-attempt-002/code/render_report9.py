"""Standalone PDF report and page previews from editable Markdown and released main figures."""
from pathlib import Path
import argparse,json,hashlib,re,textwrap,time,datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties
from PIL import Image

def main(root,figures,out):
 start=time.monotonic();out.mkdir(parents=True,exist_ok=False);(out/'page-previews').mkdir();plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'font.size':10.5,'savefig.facecolor':'white'});pages=[];pdf=PdfPages(out/'REPORT.pdf',metadata={'Title':'Readout gains and regressions across supplied genomic checkpoints','Author':'Pod A evaluation','Subject':'Verified available-checkpoint analysis; full incremental sequence remains partial','Keywords':'genomic checkpoints, frozen readouts, descriptive evaluation, saved-analysis recovery'})
 def page(title,section='REPORT'):
  fig=plt.figure(figsize=(8.27,11.69));fig.patch.set_facecolor('white');fig.text(.085,.955,'POD A   /   AVAILABLE-CHECKPOINT STUDY',fontsize=8,color='#52636c');fig.text(.915,.955,section,fontsize=8,color='#52636c',ha='right');fig.text(.085,.919,title,fontsize=17,weight='bold',color='#142e3c');fig.add_artist(plt.Line2D([.085,.915],[.902,.902],color='#c8d5db',lw=.8));return fig
 def finish(fig,title):
  number=len(pages)+1;fig.text(.085,.035,'Run 20261117T084728Z-a01 · pointwise exploratory evidence',fontsize=7.5,color='#52636c');fig.text(.915,.035,str(number),fontsize=8,ha='right',color='#52636c');fig.canvas.draw();width,height=fig.canvas.get_width_height()
  for t in fig.texts:
   bb=t.get_window_extent(fig.canvas.get_renderer());assert bb.x0>=-1 and bb.x1<=width+1 and bb.y0>=-1 and bb.y1<=height+1,('Clipped text',t.get_text())
  name=f'page-{number:02d}.png';fig.savefig(out/'page-previews'/name,dpi=125);pdf.savefig(fig);pages.append({'page':number,'title':title,'preview':name});plt.close(fig)
 fig=plt.figure(figsize=(8.27,11.69));fig.patch.set_facecolor('white');fig.text(.085,.94,'POD A / VERIFIED AVAILABLE-CHECKPOINT EVALUATION',fontsize=9,color='#52636c');fig.text(.085,.855,'Readout gains\nand regressions',fontsize=31,weight='bold',color='#142e3c',linespacing=1.15);fig.text(.085,.77,'Across the supplied genomic checkpoints',fontsize=15,color='#52636c');fig.text(.085,.726,'Base · R1 · R3 · R4 · R5 · R6   |   R2 remains missing',fontsize=11)
 for x,value,label in [(.085,'2,808 / 3,276','heads / applications, each'),(.395,'36 + 6','dev + exploratory H3-test LM units'),(.705,'36','shared control heads')]:fig.text(x,.655,value,fontsize=20,weight='bold',color='#12677c');fig.text(x,.625,label,fontsize=8.1,color='#52636c')
 data=json.loads((root/'plot_data/main_figures.json').read_text())
 def cell(family,task,hook,policy):return next(r for r in data['task_entry'] if r['family']==family and r['task']==task and r['representation']==hook and r['policy']==policy and str(r['CV_seed'])=='42')
 p=cell('R4_minus_R3','gue_prom_300_all','decoder.final_norm','independent_refit');s=cell('R5_minus_R4','gue_splice_reconstructed','decoder.layers.16','independent_refit');m=cell('R6_minus_R5','gue_mouse_0','decoder.final_norm','independent_refit')
 takeaways=[('Promoter 300 improves at the displayed anchor',f"R4 − R3 final-norm refitted ΔAUROC: {float(p['estimate']):+.4f}."),('Splice depends on representation',f"R5 − R4 layer16 refitted ΔAUROC: {float(s['estimate']):+.4f}; final norm is inconclusive."),('Mouse declines from R5 to R6',f"Final-norm refitted ΔAUROC: {float(m['estimate']):+.4f}; R6 still exceeds base."),('Readout policy matters','Refitted and unchanged-base classifiers can give different patterns.'),('Before declaration does not mean unseen','Higher scores before supplied-config inclusion do not establish absent exposure.'),('Actual LM loss is a separate measurement','R6 − R5 dev NLL worsens on each task; no pooled capability test is claimed.')]
 y=.565
 for title,body in takeaways:
  fig.text(.085,y,title,fontsize=11,weight='bold',color='#142e3c');y-=.026
  for line in textwrap.wrap(body,90):fig.text(.085,y,line,fontsize=9.5,color='#334c59');y-=.021
  y-=.021
 note='Descriptive comparisons of one supplied checkpoint per configuration. Existing intervals are pointwise exploratory and conditional on fitted heads. Unknown training lineage/exposure limits causal interpretation. Available analysis is complete; full project and full GPU reconstruction remain incomplete.'
 y=.12
 for line in textwrap.wrap(note,100):fig.text(.085,y,line,fontsize=8.5,color='#52636c');y-=.017
 finish(fig,'Executive overview')
 def prose(path,title,section):
  fig=page(title,section);y=.865
  def new():
   nonlocal fig,y;finish(fig,title);fig=page(title+' — continued',section);y=.865
  for raw in path.read_text().splitlines():
   if raw.startswith('# '):continue
   if not raw.strip():y-=.009;continue
   if raw.startswith('|---') or raw.startswith('| Evidence'):continue
   if raw.startswith('|'):
    cells=[c.strip() for c in raw.strip('|').split('|')];raw=cells[0]+': '+'; '.join(cells[1:])
   heading=raw.startswith('##');clean=re.sub(r'^#+\s*','',raw);clean=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',r'\1 [\2]',clean);clean=clean.replace('**','').replace('`','');clean=re.sub(r',(?=[A-Za-z])',', ',clean);clean=re.sub(r'(?<=[A-Za-z]),(?=\d)',', ',clean);clean=re.sub(r'(?<=[a-z])(?=\d)',' ',clean);clean=re.sub(r'(?<=\d)(?![eE][+-])(?=[A-Za-z])',' ',clean);clean=re.sub(r'\b(\d+) (st|nd|rd|th)\b',r'\1\2',clean);clean=clean.replace('andsix','and six').replace('andseven','and seven');size=12 if heading else 10.5;prop=FontProperties(family='DejaVu Sans',size=size,weight='bold' if heading else 'normal');maxwidth=fig.get_figwidth()*fig.dpi*.82;renderer=fig.canvas.get_renderer();lines=[];line=''
   for word in clean.split():
    trial=(line+' '+word).strip()
    if line and renderer.get_text_width_height_descent(trial,prop,False)[0]>maxwidth:lines.append(line);line=word
    else:line=trial
   if line:lines.append(line)
   need=len(lines)*(.022 if heading else .019)+(.012 if heading else .003)
   if y-need-(.14 if heading else 0)<.075:new()
   if heading:y-=.011
   for line in lines:
    fig.text(.085,y,line,fontsize=size,weight='bold' if heading else 'normal',color='#142e3c' if heading else '#253f4d');y-=.022 if heading else .019
   y-=.004
  finish(fig,title)
 prose(root/'RESULTS.md','Scientific findings','RESULTS')
 manifest=json.loads((figures/'FIGURE_RENDER.json').read_text())
 for f in manifest['figures']:
  p=figures/(f['name']+'.png');img=Image.open(p);fig=plt.figure(figsize=(11.69,8.8));fig.patch.set_facecolor('white');ax=fig.add_axes([.025,.105,.95,.85]);ax.imshow(img);ax.axis('off');caption=textwrap.fill(f['caption'],150);fig.text(.04,.072,caption,fontsize=8.5,color='#52636c',va='top');finish(fig,f['name'])
 prose(root/'METHODS_AND_LIMITS.md','Methods and interpretation limits','METHODS')
 fig=page('Reproducibility and remaining work','HANDOFF');paragraphs=['The exhaustive machine-readable release has 32,760 classifier marginals,73,500 classifier paired rows,84 LM marginals and182 LM paired rows. TABLE_INDEX.json indexes every canonical partition; SOURCE_TABLE_INDEX.json binds complete original files and rows at immutable commits. Original measurement values and statuses remain unchanged.','The inherited12-family A08 appendix contains all six tasks,26 representations,three CV seeds,both policies,matched controls and actual LM quantities. FIGURE_GALLERY.md links those assets and the four new main layouts.','A09’s new saved-analysis recovery panel is24 prediction paths,60 saved classifier vectors andsix LM vectors,with producer paths denied. Byte integrity covers every new archive member. FRESH_RESTORE_CHECK.json records actual scope and residuals; RESTORE.md gives exact commands. Full model/GPU/runtime recreation remains untested.','R2 remains missing468heads,468unchanged-base applications andseven LM reporting units. Only R2-dependent adjacent edges remain unavailable. Training parents,objective/steps/LR/tokens,source exposure and biological-label semantics remain limited. These are separate coverage and identifiability gaps.','No new fitting,model forwards,bootstrap draws or inferential families were performed. No perturbation evaluation,Pod B work,collaborator messaging or automatic next-stage dispatch was authorized. The Pod remains running; administrative services remain stopped. Unknown original/rental start,rate and cost are not invented.','Read the terminal SESSION_HANDOFF.md,REPORT_VALIDATION.json and separate final delivery receipt for exact Git commits,private revisions and checks. Subsequent scientific work requires fresh scoped approval. Completed available-checkpoint science should be reused.'];closing=out/'REPRODUCIBILITY_SOURCE.md';closing.write_text('# Reproducibility and remaining work\n\n'+'\n\n'.join(paragraphs)+'\n');plt.close(fig)
 prose(closing,'Reproducibility and remaining work','HANDOFF');pdf.close();b=(out/'REPORT.pdf').read_bytes();assert b.startswith(b'%PDF-') and b'%%EOF' in b[-1024:];actual_pages=len(re.findall(rb'/Type /Page\b',b));assert actual_pages==len(pages),(actual_pages,len(pages));(out/'REPORT_RENDER.json').write_text(json.dumps({'status':'RENDERED_PENDING_VISUAL_INSPECTION','PDF_pages':len(pages),'page_previews':pages,'REPORT_pdf_sha256':hashlib.sha256(b).hexdigest(),'REPORT_pdf_bytes':len(b),'editable_source':'RESULTS.md,METHODS_AND_LIMITS.md,plot_data/main_figures.json,render_report9.py and plot9.py','matplotlib':matplotlib.__version__,'wall_seconds':time.monotonic()-start},indent=2)+'\n');print(json.dumps({'status':'PASS_RENDERED','PDF_pages':len(pages),'PDF_bytes':len(b)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--figures',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();main(a.root,a.figures,a.output)
