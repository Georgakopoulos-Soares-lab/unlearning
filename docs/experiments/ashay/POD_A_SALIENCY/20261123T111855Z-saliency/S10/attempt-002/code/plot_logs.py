"""Source-label traces only: no checkpoint-matched tradeoff, smoothing, ranking or uncertainty invention."""
from pathlib import Path
import sys,json,csv,hashlib
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
P=Path(sys.argv[1]);O=Path(sys.argv[2]);O.mkdir(parents=True,exist_ok=True);inv=json.loads((P/'SOURCE_LOG_INVENTORY.json').read_text());plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.hashsalt':'S10-corrective-source-logs-v2','pdf.compression':6,'savefig.facecolor':'white'})
fig,axs=plt.subplots(3,3,figsize=(14,11),layout='constrained')
for ax,s in zip(axs.flat,inv['sources']):
 rows=list(csv.DictReader((P/'scalars'/s['relevant_scalar_table']).open()));training=[r for r in rows if r['tag']=='forget loss'];validation=[r for r in rows if r['tag']=='forget loss validation']
 ax.plot([int(r['step']) for r in training],[float(r['value']) for r in training],color='#286b9b',lw=.7,alpha=.65)
 ax.scatter([int(r['step']) for r in validation],[float(r['value']) for r in validation],color='#982b51',marker='x',s=30,zorder=4)
 ax.set_title(s['label'].replace('_',' '),loc='left',fontweight='bold');ax.set_xlabel('Logged step');ax.set_ylabel('Original logged scalar');ax.grid(alpha=.14);ax.text(.02,.97,f"{len(training):,} training / {len(validation)} validation",ha='left',va='top',transform=ax.transAxes,fontsize=8,color='#444444')
 if s['label']=='reinit5_A':ax.annotate('Step 1500: two distinct validations\nBoth retained; checkpoint match unresolved',xy=(.03,.08),xycoords='axes fraction',fontsize=7.5,color='#982b51')
fig.suptitle('Supplied forget-related log evidence\nSource-label traces; exact checkpoint and evaluation semantics remain unqualified',fontsize=16,fontweight='bold')
fig.legend(handles=[Line2D([0],[0],color='#286b9b',lw=1,label='Original tag: forget loss'),Line2D([0],[0],color='#982b51',marker='x',lw=0,label='Original tag: forget loss validation')],loc='outside lower center',ncol=2,frameon=False)
fig.supxlabel('Independent y-axis scales. No smoothing or last-value selection. Steps are not intervention replicates; no confidence intervals supplied.',fontsize=9)
entries=[]
for ext in ['png','svg','pdf']:
 q=O/('SOURCE_LOG_TRACES.'+ext);metadata={'Date':None} if ext=='svg' else {'CreationDate':None,'ModDate':None} if ext=='pdf' else {'Software':'S10 corrective evidence visualization'}
 fig.savefig(q,dpi=180,metadata=metadata);entries.append({'path':'figures/'+q.name,'sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'bytes':q.stat().st_size,'kind':'UNQUALIFIED_SOURCE_LOG_EVIDENCE','input_inventory_sha256':hashlib.sha256((P/'SOURCE_LOG_INVENTORY.json').read_bytes()).hexdigest()})
plt.close(fig);(O/'FIGURE_MANIFEST.json').write_text(json.dumps({'status':'GENERATED_PENDING_INDEPENDENT_QUALIFICATION','figures':entries,'scientific_checkpoint_join_claim':False,'smoothing':False,'duplicate_selection':False,'intervals_invented':False},indent=2)+'\n');print('SOURCE_LOG_FIGURE_EXPORTS',len(entries),flush=True)
