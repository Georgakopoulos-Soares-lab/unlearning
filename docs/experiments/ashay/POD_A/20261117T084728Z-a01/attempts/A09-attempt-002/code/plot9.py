"""Portable A09 layout renderer. Reads only released aggregate inputs; no project imports."""
from pathlib import Path
import argparse,json,csv,hashlib,time,math,xml.etree.ElementTree as ET
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
LABEL={'emp_H3':'H3','gue_tf_0':'Human TF0','gue_prom_core_all':'Core promoter','gue_prom_300_all':'Promoter 300','gue_splice_reconstructed':'Splice','gue_mouse_0':'Mouse TF0'}
COLORS={'base':'#666666','R1':'#0072B2','R3':'#E69F00','R4':'#009E73','R5':'#CC79A7','R6':'#D55E00'}
POLICIES=['independent_refit','fixed_original_base'];PLABEL={'independent_refit':'Refitted readout','fixed_original_base':'Unchanged-base readout'};SEEDS=[42,17,1234];STYLES={42:'-',17:'--',1234:':'};MARKERS={42:'o',17:'s',1234:'^'}
def main(source,out,only=None):
 start=time.monotonic();cpu=time.process_time();data=json.loads(source.read_text());out.mkdir(parents=True,exist_ok=False);plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white'});figures=[]
 def save(fig,name,caption,used):
  fig.canvas.draw();files=[]
  for ext in ['pdf','png','svg']:
   p=out/(name+'.'+ext);fig.savefig(p,dpi=175,bbox_inches='tight')
   if ext=='svg':p.write_bytes(b'\n'.join(line.rstrip(b' \t\r') for line in p.read_bytes().split(b'\n')));ET.parse(p)
   files.append({'path':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
  fieldnames=sorted(set().union(*(r.keys() for r in used)));p=out/(name+'.csv')
  with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fieldnames,lineterminator='\n');w.writeheader();w.writerows(used)
  figures.append({'name':name,'caption':caption,'files':files,'source_rows':{'path':p.name,'rows':len(used),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}});plt.close(fig)
 def coverage():
  models=data['coverage_models'];tasks=data['tasks'];fig,axes=plt.subplots(2,1,figsize=(11,8.3));used=[]
  for i,(key,title,colors) in enumerate([('coverage','Independent classifier release: 2,808 / 3,276 heads and applications each',['#d8d8d8','#56B4E9']),('declarations','Supplied retain-configuration declarations; realized exposure remains UNKNOWN',['#fff4cc','#009E73','#cccccc'])]):
   rs=data[key];vals=np.array([[next(r['value'] for r in rs if r['checkpoint_alias']==m and r['task']==t) for t in tasks] for m in models]);ax=axes[i];ax.imshow(vals,cmap=matplotlib.colors.ListedColormap(colors),vmin=0,vmax=len(colors)-1,aspect='auto');ax.set_yticks(range(7),models);ax.set_xticks(range(6),[LABEL[t] for t in tasks],rotation=10);ax.set_title(title,pad=12)
   if i==0:
    for y,m in enumerate(models):
     for x,t in enumerate(tasks):ax.text(x,y,'MISSING' if m=='R2' else '78 / 78',ha='center',va='center',fontsize=9)
   else:ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in zip(colors,['Not declared','Declared','Unknown / missing'])],loc='lower center',bbox_to_anchor=(.5,-.40),ncol=3,frameon=False)
   used.extend(dict(r,source_kind=key) for r in rs)
  fig.suptitle('What is available, and what was declared',fontsize=16,x=.04,ha='left');fig.text(.04,.035,'R2 remains missing. LM: 36 dev + 6 previously examined H3 test units / 49 planned. Shared controls: 36.\nDeclarations do not prove which rows, sources or tokens were consumed. Full project/A04 remains PARTIAL.',fontsize=10);fig.tight_layout(rect=(0,.11,1,.94),h_pad=2.0);save(fig,'main_coverage','Coverage and declarations are separate evidence. Gray is missing or unknown, never a zero performance score. Before declaration does not mean unseen examples.',used)
 def task_entry():
  transitions=data['transitions'];fig,axes=plt.subplots(3,2,figsize=(11,8.8));rs=data['task_entry'];extent=max(abs(float(r[k])) for r in rs for k in ['estimate','ci_low','ci_high']);lim=max(.1,extent*1.13)
  for i,(family,task) in enumerate(transitions):
   for j,policy in enumerate(POLICIES):
    ax=axes[i,j]
    for a,hook in enumerate(data['anchors']):
     for s,seed in enumerate(SEEDS):
      r=next(r for r in rs if r['family']==family and r['task']==task and r['representation']==hook and r['policy']==policy and str(r['CV_seed'])==str(seed));x=a+(s-1)*.085;color='#0072B2' if a==0 else '#D55E00';ax.vlines(x,float(r['ci_low']),float(r['ci_high']),color=color,lw=1.2);ax.scatter(x,float(r['estimate']),color=color,marker=MARKERS[seed],s=30,zorder=3)
    ax.axhline(0,color='#333333',lw=.8);ax.set_ylim(-lim,lim);ax.set_xlim(-.38,1.38);ax.set_xticks([0,1],['Layer 16','Final norm']);ax.set_ylabel('ΔAUROC (raw units)');ax.set_title(LABEL[task]+' · '+family.replace('_minus_','−')+'\n'+PLABEL[policy],loc='left');ax.grid(axis='y',alpha=.15)
  handles=[Line2D([0],[0],marker=MARKERS[s],color='#333333',ls='none',label='CV seed '+str(s)) for s in SEEDS];fig.legend(handles=handles,loc='lower center',ncol=3,bbox_to_anchor=(.5,.015),frameon=False);fig.suptitle('Task-entry transitions are not uniformly favorable\nTarget − reference; pointwise exploratory 95% intervals',fontsize=15,x=.04,ha='left');fig.tight_layout(rect=(0,.06,1,.91),h_pad=1.3);save(fig,'main_task_entry','Both predeclared anchors, policies and all three CV seeds are shown. Intervals are unadjusted and conditional on fitted heads; overlapping identical seed results are not independent training replications.',rs)
 def profiles():
  tasks=[t for _,t in data['transitions']];rs=data['profiles'];gaps=data['policy_gaps'];fig,axes=plt.subplots(3,3,figsize=(13.5,9.3),sharex=True);used=[]
  for i,task in enumerate(tasks):
   for j,policy in enumerate(POLICIES):
    ax=axes[i,j]
    for model,color in COLORS.items():
     for seed in [17,1234,42]:
      line=sorted([r for r in rs if r['task']==task and r['checkpoint_alias']==model and r['policy']==policy and str(r['CV_seed'])==str(seed)],key=lambda r:26 if r['representation']=='decoder.final_norm' else int(r['representation'].rsplit('.',1)[1]));assert len(line)==26;ax.plot([26 if r['representation']=='decoder.final_norm' else int(r['representation'].rsplit('.',1)[1]) for r in line],[float(r['estimate']) for r in line],color=color,ls=STYLES[seed],alpha=.95 if seed==42 else .55,lw=1.2 if seed==42 else .7);used.extend(line)
    ax.set_ylim(0,1.02);ax.set_title(LABEL[task]+' · '+PLABEL[policy],loc='left');ax.set_ylabel('AUROC')
   ax=axes[i,2]
   for seed in SEEDS:
    line=sorted([r for r in gaps if r['task']==task and str(r['CV_seed'])==str(seed)],key=lambda r:26 if r['representation']=='decoder.final_norm' else int(r['representation'].rsplit('.',1)[1]));assert len(line)==26;ax.plot([26 if r['representation']=='decoder.final_norm' else int(r['representation'].rsplit('.',1)[1]) for r in line],[float(r['estimate']) for r in line],color=COLORS['R5'],ls=STYLES[seed],lw=1.0);used.extend(line)
   ax.axhline(0,color='black',lw=.7);ax.set_ylim(-1,1);ax.set_title(LABEL[task]+' · R5 policy gap',loc='left');ax.set_ylabel('ΔAUROC (point gap)')
   for ax in axes[i]:
    ax.set_xticks([0,8,16,24,26],['0','8','16','24','FN']);ax.axvline(25,color='#aaaaaa',lw=.5);ax.grid(axis='y',alpha=.15)
    if i==2:ax.set_xlabel('Decoder block 0–24; FN = final norm')
  handles=[Line2D([0],[0],color=c,label=m) for m,c in COLORS.items()]+[Line2D([0],[0],color='black',ls=STYLES[s],label='CV seed '+str(s)) for s in SEEDS];fig.legend(handles=handles,loc='lower center',ncol=5,bbox_to_anchor=(.5,.01),frameon=False);fig.suptitle('Representation and readout policy change the apparent pattern\nAll layers and seeds; policy gaps are descriptive points with no new confidence intervals',fontsize=15,x=.04,ha='left');fig.tight_layout(rect=(0,.085,1,.91),h_pad=1.7,w_pad=1.3);save(fig,'main_profiles_policy','All three task-entry tasks; all six available checkpoints,26 representations and three CV seeds. R5 policy-gap curves subtract matched point estimates only. Full six-task profiles are in the inherited appendix.',used)
 def lm():
  rs=data['LM'];fig,axes=plt.subplots(1,3,figsize=(12,6));limit=max(abs(float(r[k])) for r in rs for k in ['estimate','ci_low','ci_high'])*1.2
  for j,(family,_) in enumerate(data['transitions']):
   ax=axes[j]
   for y,task in enumerate(data['tasks']):
    r=next(r for r in rs if r['family']==family and r['task']==task);color=COLORS[family.split('_')[0]];pt,lo,hi=[float(r[k]) for k in ['estimate','ci_low','ci_high']];ax.hlines(y,lo,hi,color=color,lw=1.4);ax.scatter(pt,y,color=color,s=32,zorder=3);ax.text(.98,y+.20,f'{pt:+.4f}',transform=ax.get_yaxis_transform(),ha='right',fontsize=8,color='#333333')
   ax.axvline(0,color='black',lw=.8);ax.set_xlim(-limit,limit);ax.set_ylim(5.65,-.65);ax.set_yticks(range(6),[LABEL[t] for t in data['tasks']]);ax.set_title(family.replace('_minus_','−'),loc='left');ax.set_xlabel('Δ corpus NLL (lower is better)');ax.grid(axis='x',alpha=.15)
  fig.suptitle('Actual LM loss gives a distinct view of the same checkpoints\nDev only; existing pointwise exploratory intervals; each task remains separate',fontsize=15,x=.04,ha='left');fig.text(.04,.03,'NLL uses the actual autoregressive head. Perplexity is exp(NLL), not independent corroborating evidence.\nThese comparisons do not isolate the effect of adding a retain source.',fontsize=10);fig.tight_layout(rect=(0,.13,1,.83),w_pad=2);save(fig,'main_LM_adjacent','All six tasks and three eligible adjacent transitions. Lower NLL is favorable. No pooled task-capability score, new LM evaluation or new confidence-interval family.',rs)
 funcs={'main_coverage':coverage,'main_task_entry':task_entry,'main_profiles_policy':profiles,'main_LM_adjacent':lm}
 for name,fn in funcs.items():
  if only is None or only==name:fn()
 result={'status':'RENDERED_PENDING_INSPECTION','figures':figures,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'matplotlib':matplotlib.__version__,'numpy':np.__version__,'wall_seconds':time.monotonic()-start,'CPU_seconds':time.process_time()-cpu};(out/'FIGURE_RENDER.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':'PASS_RENDERED','figure_families':len(figures),'wall_seconds':result['wall_seconds']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--only',choices=['main_coverage','main_task_entry','main_profiles_policy','main_LM_adjacent']);a=p.parse_args();main(a.input,a.output,a.only)
