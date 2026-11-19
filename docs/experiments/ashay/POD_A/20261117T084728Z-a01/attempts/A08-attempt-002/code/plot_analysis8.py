"""Standalone publication assets from released aggregate rows, never private examples."""
from common8 import *
import argparse,csv,time,resource,collections,math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np
LABEL={'emp_H3':'H3','gue_tf_0':'Human TF0','gue_prom_core_all':'Core promoter','gue_prom_300_all':'Promoter 300','gue_splice_reconstructed':'Splice (3 classes)','gue_mouse_0':'Mouse TF0'}
PLABEL={'independent_refit':'Refitted readout','fixed_original_base':'Unchanged original-base readout'}
MLABEL={'auroc':'AUROC','average_precision':'Average precision','accuracy':'Accuracy','balanced_accuracy':'Balanced accuracy','classification_cross_entropy':'Classifier cross-entropy (lower is better)'}
COLORS={'base':'#666666','R1':'#0072B2','R3':'#E69F00','R4':'#009E73','R5':'#CC79A7','R6':'#D55E00'}
MODELS=list(COLORS);STYLES={42:'-',17:'--',1234:':'};ANCHORCOLORS={'decoder.layers.16':'#0072B2','decoder.final_norm':'#D55E00'};MARKERS={42:'o',17:'s',1234:'^'}

def load(p):
 with Path(p).open() as f:return list(csv.DictReader(f))
def pointkey(r):return tuple(str(r[k]) for k in ['checkpoint_alias','task','split','representation','CV_seed','policy','metric'])
def xcoord(hook):return 26 if hook=='decoder.final_norm' else int(hook.rsplit('.',1)[1])

def main():
 guard();start=time.monotonic();cpu=time.process_time();resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white','axes.unicode_minus':True});points=[r for task in TASKS for r in load(D/('plot_data/points_'+task+'.csv'))];index={pointkey(r):r for r in points};assert len(index)==32760;adj=[r for family in ['R4_minus_R3','R5_minus_R4','R6_minus_R5'] for task in TASKS for r in load(D/f'plot_data/{family}_{task}.csv')];matched=load(D/'plot_data/R5_base_R1_controls.csv');lm=load(D/'plot_data/LM_contrasts.csv');repair='--repair-panels' in sys.argv;figures=[f for f in read(D/'FIGURE_MANIFEST.json')['figures'] if f['name'] not in ['adjacent_anchor_AUROC','R5_matched_reference_AUROC','LM_primary_dev','LM_exploratory_H3_test']] if repair else [];sourcefiles={str(p.relative_to(D)):sha(p) for p in sorted((D/'plot_data').glob('*.csv'))}
 def save(fig,name,caption,used):
  fig.canvas.draw();assert used
  for ax in fig.axes:
   for line in ax.lines:assert np.isfinite(np.asarray(line.get_ydata(),dtype=float)).all()
  files=[]
  for ext in ['pdf','png','svg']:
   p=D/'figures'/(name+'.'+ext);guard();p.parent.mkdir(parents=True,exist_ok=True);fig.savefig(p,dpi=160,bbox_inches='tight');assert p.stat().st_size>1000;files.append({'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':sha(p)})
  fields=sorted(set().union(*(set(r) for r in used)));normalized=[{k:r.get(k) for k in fields} for r in used];table('figures/data/'+name+'.csv',normalized);dataref={'path':'figures/data/'+name+'.csv','rows':len(used),'sha256':sha(D/'figures/data'/(name+'.csv'))};figures.append({'name':name,'caption':caption,'files':files,'plot_data':dataref,'all_values_from_released_aggregate_rows':True,'all_comparable_axes_include_data_and_intervals':True});plt.close(fig)
 def profile(metric,split='dev'):
  tasks=TASKS if split=='dev' else ['emp_H3'];fig,axes=plt.subplots(len(tasks),2,figsize=(13,2.45*len(tasks)+1.2),sharex=True,squeeze=False);used=[];allvals=[float(r['estimate']) for r in points if r['metric']==metric and r['split']==split];limits=(0,max(allvals)*1.04) if metric=='classification_cross_entropy' else (0,1.02)
  for i,task in enumerate(tasks):
   for j,policy in enumerate(POLICIES):
    ax=axes[i,j]
    for model in MODELS:
     for seed in [17,1234,42]:
      rows=[index[model,task,split,hook,str(seed),policy,metric] for hook in HOOKS];ax.plot([xcoord(r['representation']) for r in rows],[float(r['estimate']) for r in rows],color=COLORS[model],ls=STYLES[seed],lw=1.15 if seed==42 else .7,alpha=.95 if seed==42 else .55);used.extend({'source_key':r['point_id'],'model':model,'task':task,'split':split,'representation':r['representation'],'CV_seed':seed,'policy':policy,'metric':metric,'estimate':r['estimate']} for r in rows)
    ax.set_title(LABEL[task]+' · '+PLABEL[policy]);ax.set_ylim(*limits);ax.set_xticks([0,8,16,24,26],['0','8','16','24','FN']);ax.axvline(16,color='#999999',lw=.5,ls=':');ax.axvline(25,color='#bbbbbb',lw=.5);ax.grid(axis='y',alpha=.16);ax.set_ylabel(MLABEL[metric])
    if i==len(tasks)-1:ax.set_xlabel('Decoder block index (0–24); FN = final norm')
  handles=[Line2D([0],[0],color=COLORS[m],label=m) for m in MODELS]+[Line2D([0],[0],color='black',ls=STYLES[s],label='CV seed '+str(s)) for s in SEEDS];fig.legend(handles=handles,loc='lower center',ncol=5,bbox_to_anchor=(.5,.003));fig.suptitle(('PRIMARY DEV' if split=='dev' else 'PREVIOUSLY EXAMINED H3 EXPLORATORY TEST')+' · all layers, policies and CV seeds\nRetain-set labels are configuration order; R2 is missing',fontsize=13);fig.tight_layout(rect=(0,.06,1,.95));save(fig,('profiles_dev_' if split=='dev' else 'profiles_exploratory_H3_')+metric,'Every line is a released checkpoint/readout at one CV seed. Seed styles are not confidence bands or independently trained checkpoints. No R2 trajectory or best-layer selection is drawn.',used)
 def interval_point(ax,x,r,color,marker):
  lo,hi,pt=[float(r[k]) for k in ['ci_low','ci_high','estimate']];assert math.isfinite(lo+hi+pt) and lo<=hi;ax.vlines(x,lo,hi,color=color,lw=.8,alpha=.75);ax.hlines([lo,hi],x-.015,x+.015,color=color,lw=.7);ax.scatter([x],[pt],color=color,marker=marker,s=16,zorder=3)
 def effect_panel(which):
  rows=adj if which=='adjacent' else matched;refs=['R4_minus_R3','R5_minus_R4','R6_minus_R5'] if which=='adjacent' else ['base','R1','composition','kmer4'];fig,axes=plt.subplots(6,2,figsize=(13,17.5),squeeze=False);used=[];selected=[r for r in rows if r['metric']=='auroc' and r['split']=='dev' and r['representation'] in ANCHORS];extent=max(abs(float(r[k])) for r in selected for k in ['estimate','ci_low','ci_high']);limit=max(.05,extent*1.07)
  for i,task in enumerate(TASKS):
   for j,policy in enumerate(POLICIES):
    ax=axes[i,j]
    for n,ref in enumerate(refs):
     for ai,hook in enumerate(ANCHORS):
      for si,seed in enumerate(SEEDS):
       r=next(r for r in selected if r['task']==task and r['policy']==policy and r['representation']==hook and str(r['CV_seed'])==str(seed) and r['family' if which=='adjacent' else 'reference']==ref);x=n+(ai-.5)*.22+(si-1)*.045;interval_point(ax,x,r,ANCHORCOLORS[hook],MARKERS[seed]);used.append({k:r.get(k) for k in ['logical_id','family','reference','task','split','representation','CV_seed','policy','metric','estimate','ci_low','ci_high']})
    ax.axhline(0,color='black',lw=.7);ax.set_ylim(-limit,limit);ax.set_xticks(range(len(refs)),[r.replace('_minus_','−') for r in refs],rotation=15);ax.set_title(LABEL[task]+' · '+PLABEL[policy]);ax.set_ylabel('ΔAUROC (raw units)');ax.grid(axis='y',alpha=.15)
  handles=[Line2D([0],[0],color=ANCHORCOLORS[h],marker=MARKERS[s],ls='none',label=('Layer16' if h==ANCHORS[0] else 'Final norm')+' · seed'+str(s)) for h in ANCHORS for s in SEEDS];fig.legend(handles=handles,loc='lower center',ncol=3,bbox_to_anchor=(.5,.002));fig.suptitle('Eligible adjacent checkpoint effects' if which=='adjacent' else 'R5 minus matched pretrained base, R1 and unchanged simple controls',fontsize=13);fig.tight_layout(rect=(0,.06,1,.96));save(fig,'adjacent_anchor_AUROC' if which=='adjacent' else 'R5_matched_reference_AUROC','Dots are point estimates; vertical lines are pointwise exploratory unadjusted95% saved-group-bootstrap intervals conditional on fitted heads. Every anchor/CV seed/policy is shown; intervals crossing zero are inconclusive. R2-dependent edges remain missing.',used)
 def lm_panel(split='dev'):
  tasks=TASKS if split=='dev' else ['emp_H3'];families=['R5_minus_base','R5_minus_R1','R4_minus_R3','R5_minus_R4','R6_minus_R5'];fig,axes=plt.subplots(len(tasks),2,figsize=(13,2.5*len(tasks)+1),squeeze=False);used=[]
  for col,metric in enumerate(['causal_nll','perplexity']):
   selected=[r for r in lm if r['metric']==metric and r['split']==split];extent=max(abs(float(r[k])) for r in selected for k in ['estimate','ci_low','ci_high']);limit=max(.005,extent*1.08)
   for i,task in enumerate(tasks):
    ax=axes[i,col]
    for x,family in enumerate(families):
     r=next(r for r in selected if r['task']==task and r['family']==family);interval_point(ax,x,r,COLORS[family.split('_')[0]],'o');used.append({k:r.get(k) for k in ['logical_id','family','task','split','metric','estimate','ci_low','ci_high']})
    ax.axhline(0,color='black',lw=.7);ax.set_ylim(-limit,limit);ax.set_xticks(range(5),[f.replace('_minus_','−') for f in families],rotation=20);ax.set_title(LABEL[task]+' · '+('Corpus NLL' if metric=='causal_nll' else 'Corpus perplexity'));ax.set_ylabel('Δ'+('NLL' if metric=='causal_nll' else 'PPL'));ax.grid(axis='y',alpha=.15)
  fig.suptitle(('PRIMARY DEV' if split=='dev' else 'EXPLORATORY H3 TEST')+' · actual causal-LM paired changes\nTarget − reference; lower is better',fontsize=13);fig.tight_layout(rect=(0,0,1,.96));save(fig,'LM_primary_dev' if split=='dev' else 'LM_exploratory_H3_test','Corpus NLL is summed saved causal loss divided by valid targets; PPL is exp(corpus NLL). Within-task paired group-bootstrap intervals; no layer/CV axis or cross-task capability average.',used)
 def coverage_and_entry():
  models=['base','R1','R2','R3','R4','R5','R6'];fig,ax=plt.subplots(figsize=(11,5.8));values=np.array([[0 if m=='R2' else 1 for _ in TASKS] for m in models]);ax.imshow(values,cmap=matplotlib.colors.ListedColormap(['#d8d8d8','#56B4E9']),vmin=0,vmax=1,aspect='auto')
  for i,m in enumerate(models):
   for j,task in enumerate(TASKS):ax.text(j,i,'MISSING' if m=='R2' else '78 / 78',ha='center',va='center',fontsize=9)
  ax.set_xticks(range(6),[LABEL[t] for t in TASKS],rotation=15);ax.set_yticks(range(7),models);ax.set_title('Independent classifier release:2808/3276 heads and2808/3276 fixed-base applications\nPrimary LM42/49;36 shared controls; full A04/project remains PARTIAL',pad=14);fig.tight_layout();save(fig,'coverage_map','Each released task cell contains26 representations×3 CV seeds. H3 test adds reporting records, not additional fitted heads. R2 missingness is not a zero performance score.',[{'checkpoint_alias':m,'task':t,'released_heads':0 if m=='R2' else 78,'planned_heads':78,'state':'MISSING_R2' if m=='R2' else 'RELEASED'} for m in models for t in TASKS])
  inc=load(D/'INCLUSION_EXPOSURE_PLAN.csv');lookup={(r['candidate'],r['task']):r for r in inc};fig,ax=plt.subplots(figsize=(11,5.8));values=np.zeros((7,6),dtype=int);used=[]
  for i,m in enumerate(models):
   for j,task in enumerate(TASKS):
    r=lookup.get((m,task));v=2 if r is None or m=='R2' else {'true':1,'false':0}.get(r['observed_selected_config_declares_family'].lower(),2);values[i,j]=v;used.append({'checkpoint_alias':m,'task':task,'declaration_state':['Not declared in supplied config','Declared in supplied config','Unknown / not delivered'][v],'realized_exposure':'UNKNOWN','source_row_sha256':r['source_row_sha256'] if r else None})
  ax.imshow(values,cmap=matplotlib.colors.ListedColormap(['#fff4cc','#009E73','#cccccc']),vmin=0,vmax=2,aspect='auto');ax.set_xticks(range(6),[LABEL[t] for t in TASKS],rotation=15);ax.set_yticks(range(7),models);ax.set_title('Supplied retain-configuration declarations\nPlanned membership, observed declaration and realized exposure are distinct',pad=14);ax.legend(handles=[Patch(facecolor=c,label=l) for c,l in [('#fff4cc','Not declared'),('#009E73','Declared'),('#cccccc','Unknown / missing')]],loc='lower center',bbox_to_anchor=(.5,-.27),ncol=3);fig.text(.5,.01,'Realized row/source/token exposure is UNKNOWN. Before declaration does not mean unseen examples.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.08,1,.96));save(fig,'task_entry_declarations','Declaration colors reflect supplied configuration evidence only. Missing R2 is unknown, not absence; no biological or training-exposure inference is made.',used)
 if not repair:
  for metric in METRICS:profile(metric)
  profile('auroc','test_exploratory');coverage_and_entry()
 effect_panel('adjacent');effect_panel('matched');lm_panel();lm_panel('test_exploratory')
 manifest={'status':'RENDERED_PENDING_VISUAL_INSPECTION','figure_count':len(figures),'figures':figures,'plot_source_files':sourcefiles,'formats':['pdf','png','svg'],'all_primary_figures_dev_only':True,'exploratory_H3_test_separate':True,'no_missing_R2_interpolation':True,'all_three_CV_seeds_identifiable':True,'seed_ranges_are_not_CI_bands':True,'no_new_scientific_measurements':True,'render_wall_seconds':time.monotonic()-start,'render_CPU_seconds':time.process_time()-cpu,'matplotlib_version':matplotlib.__version__,'numpy_version':np.__version__,'plot_code_sha256':sha(__file__)};publish('FIGURE_MANIFEST.json',manifest);put(C/'FIGURE_RENDER_RECEIPT.json',manifest);lines=['# A08 figure gallery','','All assets have standalone PDF, PNG and SVG versions and full-precision plotted-row CSVs. Primary dev panels and previously examined H3 exploratory-test panels are separate.','']
 for f in figures:
  lines.extend(['## '+f['name'],'',f['caption'],'','[PDF]('+f['files'][0]['path']+') · [PNG]('+f['files'][1]['path']+') · [SVG]('+f['files'][2]['path']+') · [plotted rows]('+f['plot_data']['path']+')','','![Preview]('+f['files'][1]['path']+')',''])
 publish('FIGURE_GALLERY.md','\n'.join(lines));print(json.dumps({'status':'RENDERED','figures':len(figures),'formats':3,'wall_seconds':manifest['render_wall_seconds']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--stage',choices=['A08'],required=True);p.add_argument('--repair-panels',action='store_true');p.parse_args();main()
