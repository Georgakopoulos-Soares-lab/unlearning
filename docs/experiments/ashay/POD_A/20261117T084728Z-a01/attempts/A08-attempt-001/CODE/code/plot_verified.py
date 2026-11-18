"""Publication figures from released aggregate tables only; no model/data inference."""
from pathlib import Path
import argparse,csv,json,hashlib,os,sys,math,resource,time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];LABELS={'emp_H3':'H3','gue_tf_0':'Human TF','gue_prom_core_all':'Core promoter','gue_prom_300_all':'Promoter 300','gue_splice_reconstructed':'Splice (3 classes)','gue_mouse_0':'Mouse TF'};POLICIES=['independent_refit','fixed_original_base'];PLABEL={'independent_refit':'Refitted readout','fixed_original_base':'Original-base readout'};METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy'];MLABEL={'auroc':'AUROC','average_precision':'Average precision','accuracy':'Accuracy','balanced_accuracy':'Balanced accuracy','classification_cross_entropy':'Classifier cross-entropy'};COLORS={'base':'#394653','R1':'#b78320','R3':'#7558a5','R4':'#c34f82','R6':'#087fa6'};SEEDS=[17,1234,42]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rows(p):return list(csv.DictReader(Path(p).open()))
def pointkey(r):return (r['checkpoint_alias'],r['task'],r['split'],r['representation'],str(r['CV_seed']),r['policy'],r['metric'])
def xcoord(rep):return 25 if rep=='decoder.final_norm' else int(rep.rsplit('.',1)[1])
def main(docs):
 render_started=time.monotonic();render_cpu_started=time.process_time()
 root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'stage_drivers'));from research_guard import guard
 cfg=json.loads((Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/attempts/A08-attempt-001')/'RUN_CONFIG.json').read_text());assert docs.resolve()==Path(cfg['docs']).resolve();resource.setrlimit(resource.RLIMIT_AS,(32*1024**3,32*1024**3));guard(allow_dirty=True)
 plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':10,'axes.labelsize':9,'legend.fontsize':8,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':'white','axes.unicode_minus':True})
 point=rows(docs/'VERIFIED_METRICS.csv');controls=rows(docs/'CONTROL_METRICS_REUSED.csv');manifest=json.loads((docs/'TABLE_PARTITIONS.json').read_text());pairs=[r for part in manifest['logical_PAIRED_CONTRASTS']['partitions'] for r in rows(docs/part['file'])];lm=rows(docs/'LM_METRICS_VERIFIED.csv');lmpairs=rows(docs/'LM_CONTRASTS_VERIFIED.csv')
 assert all(r['status'] in ['VERIFIED','REUSED_VALIDATED'] for r in point+pairs+lm+lmpairs+controls);lookup={pointkey(r):r for r in point};assert len(lookup)==len(point);pair_lookup={(r['checkpoint_alias'],r['reference'],r['task'],r['split'],r['representation'],str(r['CV_seed']),r['policy'],r['metric']):r for r in pairs};assert len(pair_lookup)==len(pairs);control_lookup={(r['checkpoint_alias'],r['task'],r['split'],str(r['CV_seed']),r['metric']):r for r in controls};figures=[];data_sources={name:sha(docs/name) for name in ['VERIFIED_METRICS.csv','CONTROL_METRICS_REUSED.csv','LM_METRICS_VERIFIED.csv','LM_CONTRASTS_VERIFIED.csv']+[p['file'] for p in manifest['logical_PAIRED_CONTRASTS']['partitions']]};plot_rows=[]
 def save(fig,name,caption,used):
  guard(allow_dirty=True);dest=docs/'figures'/name;dest.parent.mkdir(parents=True,exist_ok=True);fig.canvas.draw();axes=fig.axes
  for ax in axes:
   for line in ax.lines:
    y=np.asarray(line.get_ydata(),dtype=float);assert np.isfinite(y).all(),'Nonfinite plotted y'
  files=[]
  for ext in ['png','pdf']:
   p=dest.with_suffix('.'+ext);fig.savefig(p,dpi=150,bbox_inches='tight',bbox_extra_artists=([fig._suptitle] if fig._suptitle is not None else [])+list(fig.legends));assert p.stat().st_size>1000;files.append({'path':str(p.relative_to(docs)),'bytes':p.stat().st_size,'sha256':sha(p)})
  figures.append({'name':name,'files':files,'axes':len(axes),'source_rows':len(used),'caption':caption,'all_plotted_values_from_released_tables':True,'source_tables':data_sources});plot_rows.extend({'figure':name,**r} for r in used);plt.close(fig)
 def profile(metric,split='dev',historical=False):
  tasks=TASKS if split=='dev' else ['emp_H3'];models=['base','R1','R3'] if historical else ['base','R1','R4','R6'];fig,axs=plt.subplots(len(tasks),2,figsize=(13,2.55*len(tasks)+1),squeeze=False,sharex=True);used=[]
  for i,task in enumerate(tasks):
   for j,policy in enumerate(POLICIES):
    ax=axs[i,j]
    for alias in models:
     for seed in SEEDS:
      rr=[lookup[alias,task,split,('decoder.layers.'+str(k) if k<25 else 'decoder.final_norm'),str(seed),policy,metric] for k in range(26)];yy=[float(r['estimate']) for r in rr];ax.plot(range(26),yy,color=COLORS[alias],lw=1.65 if seed==42 else .65,alpha=1 if seed==42 else .45,label=alias if seed==42 else None);used.extend(rr)
    if not historical:
     for kind,color,style in [('control_composition','#87959e','--'),('control_kmer4','#4b8b70',':')]:
      r=control_lookup[kind,task,split,'42',metric];ax.axhline(float(r['estimate']),color=color,ls=style,lw=.9,label=kind.removeprefix('control_'));used.append(r)
    ax.axvline(16,color='#b9c1c6',ls=':',lw=.7);ax.set_title(LABELS[task]+' · '+PLABEL[policy]);ax.set_ylabel(MLABEL[metric]);ax.set_xticks([0,4,8,12,16,20,24,25],['0','4','8','12','16','20','24','FN']);ax.grid(axis='y',alpha=.16)
    if metric!='classification_cross_entropy':ax.set_ylim(0,1)
    else:ax.set_ylim(bottom=0)
    if i==len(tasks)-1:ax.set_xlabel('Decoder block index (0-based); FN = final norm')
  handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',ncol=len(labels),bbox_to_anchor=(.5,1-.65/fig.get_figheight()));scope='Historical domain only: base/R1/R3; no bridge to current R4/R6 effects' if historical else 'Qualified endpoints; shared input controls do not create extra fits';fig.suptitle(MLABEL[metric]+' · '+('official dev' if split=='dev' else 'H3 previously examined exploratory test')+'\n'+scope,y=1-.1/fig.get_figheight(),fontsize=12).set_in_layout(False);fig.tight_layout(rect=(0,0,1,1-1.1/fig.get_figheight()));name=('historical_domain/' if historical else 'dev/' if split=='dev' else 'exploratory_test/')+'profiles_'+metric
  save(fig,name,'All 26 representations and 3 CV seeds. Bold seed 42; thin 17/1234. Seed spread is not a confidence band. Layer16 is the 17th block. Horizontal shared controls are point displays; paired control inference remains limited to predeclared anchors. '+scope,used)
 def anchors(metric,refs=('base','R1')):
  fig,axs=plt.subplots(6,2,figsize=(13,14.2),squeeze=False);used=[];refcolors=['#347a9c','#b78320']
  for i,task in enumerate(TASKS):
   for j,policy in enumerate(POLICIES):
    ax=axs[i,j]
    for y,(alias,rep) in enumerate([('R4','decoder.layers.16'),('R4','decoder.final_norm'),('R6','decoder.layers.16'),('R6','decoder.final_norm')]):
     for n,reference in enumerate(refs):
      r=pair_lookup[alias,reference,task,'dev',rep,'42',policy,metric];v,lo,hi=[float(r[k]) for k in ['estimate','ci_low','ci_high']];ax.errorbar(v,y+(n-.5)*.18,xerr=[[v-lo],[hi-v]],fmt='o',ms=3,capsize=2,color=refcolors[n],lw=.9);used.append(r)
    ax.axvline(0,color='#66747f',lw=.7,ls='--');ax.set_yticks(range(4),['R4 · block16','R4 · final norm','R6 · block16','R6 · final norm']);ax.invert_yaxis();ax.set_title(LABELS[task]+' · '+PLABEL[policy]);ax.grid(axis='x',alpha=.15)
    if i==5:ax.set_xlabel('Target minus reference · '+MLABEL[metric])
  fig.legend([Line2D([0],[0],marker='o',color=c,lw=.8) for c in refcolors],[x.removeprefix('control_') for x in refs],ncol=2,loc='upper center',bbox_to_anchor=(.5,1-.65/fig.get_figheight()));fig.suptitle('Predeclared anchors, seed42 · '+MLABEL[metric]+'\nPointwise 95% paired group-bootstrap intervals; '+('lower' if metric=='classification_cross_entropy' else 'higher')+' is favorable',y=1-.1/fig.get_figheight(),fontsize=12).set_in_layout(False);fig.tight_layout(rect=(0,0,1,1-1.1/fig.get_figheight()));save(fig,'dev/anchors_'+('_controls_' if refs[0].startswith('control_') else '')+metric,'Seed 42 and layer 16/final norm were predeclared, not selected using scores. Intervals are conditional on fitted heads and unadjusted across the grid; all seeds remain in released tables.',used)
 def nonadjacent(metric,split='dev'):
  tasks=TASKS if split=='dev' else ['emp_H3'];fig,axs=plt.subplots(len(tasks),2,figsize=(13,2.5*len(tasks)+1),squeeze=False,sharex=True);used=[]
  for i,task in enumerate(tasks):
   for j,policy in enumerate(POLICIES):
    ax=axs[i,j]
    for seed in SEEDS:
     rr=[pair_lookup['R6','R4',task,split,('decoder.layers.'+str(k) if k<25 else 'decoder.final_norm'),str(seed),policy,metric] for k in range(26)];v=np.array([float(r['estimate']) for r in rr]);ax.plot(range(26),v,color=COLORS['R6'],lw=1.6 if seed==42 else .65,alpha=1 if seed==42 else .45,label='seed42' if seed==42 else 'seed'+str(seed));used.extend(rr)
     if seed==42:ax.fill_between(range(26),[float(r['ci_low']) for r in rr],[float(r['ci_high']) for r in rr],color=COLORS['R6'],alpha=.13,label='seed 42: pointwise 95% CI')
    ax.axhline(0,color='#555f67',ls='--',lw=.7);ax.axvline(16,color='#aeb9c1',ls=':',lw=.6);ax.set_title(LABELS[task]+' · '+PLABEL[policy]);ax.set_ylabel('R6−R4 · '+MLABEL[metric]);ax.set_xticks([0,4,8,12,16,20,24,25],['0','4','8','12','16','20','24','FN']);ax.grid(axis='y',alpha=.15)
    if i==len(tasks)-1:ax.set_xlabel('0-based decoder block; FN separate final norm hook')
  handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,ncol=4,loc='upper center',bbox_to_anchor=(.5,1-.65/fig.get_figheight()));fig.suptitle('R6−R4: predeclared NONADJACENT contrast · '+('official dev' if split=='dev' else 'H3 exploratory test')+'\nSpans two planned additions and unmatched training differences; no isolated causal effect',y=1-.1/fig.get_figheight(),fontsize=12).set_in_layout(False);fig.tight_layout(rect=(0,0,1,1-1.1/fig.get_figheight()));save(fig,('dev/' if split=='dev' else 'exploratory_test/')+'R6_minus_R4_'+metric,'All 26 hooks and 3 seeds shown. Shading is seed 42 pointwise bootstrap CI, not seed spread or a simultaneous band. R6−R4 is nonadjacent and cannot replace missing adjacent edges.',used)
 def language():
  ll={(r['checkpoint_alias'],r['task'],r['split'],r['metric']):r for r in lm};dd={(r['task'],r['split'],r['metric']):r for r in lmpairs if r['checkpoint_alias']=='R6' and r['reference']=='R4'};fig,axs=plt.subplots(6,2,figsize=(13,14.5),squeeze=False);used=[]
  for i,task in enumerate(TASKS):
   for j,metric in enumerate(['causal_nll','perplexity']):
    ax=axs[i,j]
    for alias,pos in [('base',0),('R1',1),('R4',4),('R6',6)]:
     r=ll[alias,task,'dev',metric];v=float(r['estimate']);ax.plot(pos,v,'o',ms=5,color=COLORS[alias]);used.append(r)
     if r['ci_low'] and r['ci_high']:ax.errorbar(pos,v,yerr=[[v-float(r['ci_low'])],[float(r['ci_high'])-v]],color=COLORS[alias],capsize=3,lw=.8)
    ax.axvspan(2.6,3.4,color='#b8b0c6',alpha=.15,hatch='//');ax.set_xticks(range(7),['base','R1','R2\npending','R3\nhistory','R4','R5\npending','R6']);ax.set_title(LABELS[task]+' · '+('Corpus causal NLL' if metric=='causal_nll' else 'Corpus perplexity'));ax.set_ylabel('Lower is favorable');ax.grid(axis='y',alpha=.15)
  fig.suptitle('Within-task actual causal-head likelihood · official dev\nUnconnected endpoint points; R3 historical domain remains separate; no layer/seed axis',y=1.01,fontsize=12);fig.tight_layout();save(fig,'dev/LM_within_task','Corpus NLL=sum(loss)/sum(targets); PPL=exp(NLL). Historical marginal CIs not present in inherited point tables; current R4/R6CIs reused. No averaging sequence perplexities or across-task capability score.',used)
  for split,tasks in [('dev',TASKS),('test_exploratory',['emp_H3'])]:
   fig,axs=plt.subplots(1,2,figsize=(12,5 if split=='dev' else 2.8),squeeze=False);used=[]
   for j,metric in enumerate(['causal_nll','perplexity']):
    ax=axs[0,j]
    for i,task in enumerate(tasks):
     r=dd[task,split,metric];v,lo,hi=[float(r[k]) for k in ['estimate','ci_low','ci_high']];ax.errorbar(v,i,xerr=[[v-lo],[hi-v]],fmt='o',color=COLORS['R6'],capsize=3,ms=4);used.append(r)
    ax.axvline(0,color='#65717a',lw=.7,ls='--');ax.set_yticks(range(len(tasks)),[LABELS[t] for t in tasks]);ax.invert_yaxis();ax.set_xlabel('R6−R4 · '+metric+' (lower favorable)');ax.grid(axis='x',alpha=.15)
   fig.suptitle('Predeclared NONADJACENT LM comparison · '+('official dev' if split=='dev' else 'H3 previously examined exploratory test')+'\nPointwise 95% paired exact/RC-group bootstrap; no causal task-addition attribution',fontsize=11);fig.tight_layout();save(fig,('dev/' if split=='dev' else 'exploratory_test/')+'LM_R6_minus_R4','No representation/CVseed axis; seven primary split units,14metrics for this new contrast family. Classification cross-entropy is a different output.',used)
 def coverage():
  fig,(ax,edge)=plt.subplots(2,1,figsize=(12,7),gridspec_kw={'height_ratios':[3,1.5]});matrix=np.tile([1,1,0,1,2,0,2],(6,1));from matplotlib.colors import ListedColormap
  ax.imshow(matrix,cmap=ListedColormap(['#d9dfe3','#9cbbd1','#6cae91']),vmin=0,vmax=2,aspect='auto');ax.set_xticks(range(7),['base','R1','R2','R3\nhistorical only','R4','R5','R6']);ax.set_yticks(range(6),[LABELS[t] for t in TASKS])
  for y in range(6):
   for x in range(7):ax.text(x,y,'pending' if matrix[y,x]==0 else '78 reused' if matrix[y,x]==1 else '78 verified',ha='center',va='center',fontsize=9)
  edge.set_xlim(-.5,6.5);edge.set_ylim(-.8,1.4);edge.axis('off')
  for x,alias in enumerate(['base','R1','R2','R3','R4','R5','R6']):edge.plot(x,0,'o',color='#466475' if x not in [2,5] else '#b5bcc2',ms=9);edge.text(x,-.25,alias,ha='center')
  for a,b,label in [(1,2,'R2 missing'),(2,3,'R2 missing'),(3,4,'R3 bridge'),(4,5,'R5 missing'),(5,6,'R5 missing')]:edge.plot([a,b],[0,0],'--',color='#9ba7ae');edge.text((a+b)/2,.17,label,ha='center',fontsize=8)
  edge.annotate('',xy=(6,.52),xytext=(4,.52),arrowprops={'arrowstyle':'->','connectionstyle':'arc3,rad=-.3','color':COLORS['R6']});edge.text(5,1.18,'R6−R4: verified NONADJACENT',ha='center',color=COLORS['R6']);fig.suptitle('Head coverage: 2340/3276 available; 936 R2/R5 cells remain pending\nSeparate fixed-reference universe also 3276 cells. R3 live bridge is still gated.',fontsize=12);fig.tight_layout();save(fig,'coverage/availability_and_missing_edges','Each colored task/endpoint cell represents26 representations x 3 seeds. A04 remains PARTIAL; no full-project completion or inferred trajectory through missing stages.',[])
 for metric in METRICS:profile(metric);anchors(metric);nonadjacent(metric);profile(metric,'test_exploratory');nonadjacent(metric,'test_exploratory')
 profile('auroc',historical=True);anchors('auroc',('control_composition','control_kmer4'));language();coverage()
 guard(allow_dirty=True);out=docs/'PLOT_DATA';out.mkdir(exist_ok=True);fields=['figure','checkpoint_alias','reference','task','split','representation','CV_seed','policy','metric','estimate','ci_low','ci_high','status','original_endpoint_id','reference_endpoint_id','producer_receipt_sha256','audit_receipt_sha256']
 with (out/'plotted_values.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore',lineterminator='\n');w.writeheader();w.writerows(plot_rows)
 proof={'status':'PASS_PROGRAMMATIC_RENDER_PENDING_VISUAL_INSPECTION','figures':figures,'figure_count':len(figures),'plotted_value_records':len(plot_rows),'plotted_values_csv_sha256':sha(out/'plotted_values.csv'),'all_source_tables_released_only':True,'no_pending_cells_plotted':True,'full_precision_data':True,'seed_spread_not_CI':True,'H3_test_separate':True,'R3_historical_domain_separate':True,'source_code_sha256':sha(__file__),'matplotlib_version':matplotlib.__version__,'data_sources':data_sources,'render_wall_seconds':time.monotonic()-render_started,'render_CPU_seconds':time.process_time()-render_cpu_started,'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'executed_argv':[sys.executable,*sys.argv]};(docs/'FIGURE_VALIDATION.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({'status':proof['status'],'figures':len(figures),'plotted_records':len(plot_rows)}))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--docs',type=Path,required=True);main(p.parse_args().docs)
