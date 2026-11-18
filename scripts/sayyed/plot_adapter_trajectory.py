"""Render parameter-geometry tables only; no model/data/outcome access."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
from scripts.sayyed.adapter_trajectory import verify_owned_output

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();run=a.run;out=a.output;verify_owned_output(run,out)
    def rows(n):
        with(out/n).open()as f:return list(csv.DictReader(f))
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    specsha=sha(run/'ANALYSIS_SPEC.json');cp=rows('CHECKPOINT_SUMMARY.csv');edges=rows('GLOBAL_EDGE_METRICS.csv');blocks=rows('BLOCK_EDGE_SUMMARY.csv');targets=rows('TARGET_EDGE_SUMMARY.csv');figures=[]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
    footer='Serialized U=2BA under the saved parameterization; original job/runtime unbound. No capability measurement.'
    def save(fig,name,sources,description):
        verify_owned_output(run,out);fig.text(.01,.01,footer+'\nSpec '+specsha[:16],fontsize=7,color='#444444');files=[]
        for ext in ['svg','pdf','png']:
            path=out/(name+'.'+ext);fig.savefig(path,dpi=220,bbox_inches='tight');files.append(dict(path=path.name,bytes=path.stat().st_size,sha256=sha(path)))
        figures.append(dict(name=name,description=description,analysis_spec_sha256=specsha,source_tables=[dict(path=s,sha256=sha(out/s))for s in sources],files=files));plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,4.8))
    for series,color in [('base','#31688e'),('maxent','#d95f02')]:
        q=sorted([x for x in cp if x['series']==series],key=lambda x:int(x['step']))
        segments=[q]if series=='base'else[q[:16],q[16:]]
        for j,seg in enumerate(segments):ax.plot([int(x['step'])for x in seg],[float(x['U_norm'])for x in seg],marker='o',ms=4,lw=1.5,color=color,linestyle='-'if j==0 else'--',label=series+(' job11803647'if j else''))
    ax.axvspan(1600,1700,color='#888888',alpha=.13,label='MaxEnt job boundary; continuity unknown');ax.set(xlabel='Delivered step (not measured exposure)',ylabel='Frobenius norm across 100 serialized module blocks',title='Declared adapter magnitude across delivered checkpoints');ax.legend(fontsize=8);fig.tight_layout(rect=(0,.08,1,1));save(fig,'magnitude_trajectory',['CHECKPOINT_SUMMARY.csv'],'All18 saved checkpoints per series; MaxEnt segments are not connected across1600→1700')
    fig,ax=plt.subplots(figsize=(9,4.8))
    for series,color in [('base','#31688e'),('maxent','#d95f02')]:
        q=sorted([x for x in edges if x['kind']=='adjacent'and x['left_series']==series],key=lambda x:int(x['right_step']));ax.plot([int(x['right_step'])for x in q],[float(x['U_distance'])for x in q],marker='o',ms=4,lw=1.4,color=color,label=series)
    b=next(x for x in edges if x['edge_id']=='adjacent:maxent:1600-1700');ax.scatter([1700],[float(b['U_distance'])],s=110,marker='*',color='#c51b7d',zorder=4,label='MaxEnt1600→1700 cross-job edge');ax.set(xlabel='Right endpoint of actual adjacent delivered edge',ylabel='Frobenius distance of declared updates',title='Adjacent delivered parameter changes');ax.legend(fontsize=8);fig.tight_layout(rect=(0,.08,1,1));save(fig,'adjacent_distance',['GLOBAL_EDGE_METRICS.csv'],'All17 actual adjacent edges per series; star marks the cross-job parameter comparison,not a causal restart effect')
    fig,axs=plt.subplots(1,2,figsize=(12,5),sharey=True);matrices=[]
    for series in ['base','maxent']:
        M=np.array([[float(next(x['U_distance']for x in blocks if x['edge_id']==f'adjacent:{series}:{t-100}-{t}'and int(x['group'])==b))for t in range(200,1801,100)]for b in range(25)]);matrices.append(M)
    positive=np.concatenate([x[x>0]for x in matrices]);norm=LogNorm(vmin=positive.min(),vmax=positive.max())
    for ax,M,series in zip(axs,matrices,['base','maxent']):
        im=ax.imshow(np.ma.masked_less_equal(M,0),aspect='auto',origin='lower',cmap='viridis',norm=norm);ax.set_title(series);ax.set_xlabel('Right delivered step');ax.set_xticks(range(0,17,2),list(range(200,1801,200)),rotation=45);ax.set_yticks([0,4,8,12,16,20,24]);
        if series=='maxent':ax.axvspan(14.5,15.5,facecolor='none',edgecolor='#ef8a62',lw=1.5)
    axs[0].set_ylabel('Zero-based decoder block (25 blocks; no final_norm adapter)');fig.subplots_adjust(bottom=.2,top=.87,wspace=.13,right=.84);cax=fig.add_axes([.88,.2,.018,.63]);fig.colorbar(im,cax=cax,label='Block declared-update distance (log color)');fig.suptitle('Every block and every adjacent delivered edge');save(fig,'step_by_block',['BLOCK_EDGE_SUMMARY.csv'],'Shared logarithmic color scale for all25 blocks×17 adjacent edges in both series; MaxEnt1700 column outlined')
    selected=[next(x for x in edges if x['edge_id']==f'adjacent:maxent:{t-100}-{t}')for t in [1600,1700,1800]];labels=['1500→1600','1600→1700','1700→1800'];fig,axs=plt.subplots(1,3,figsize=(13,4.6));colors=['#4575b4','#d73027','#4575b4'];axs[0].bar(labels,[float(x['U_distance'])for x in selected],color=colors);axs[0].set(ylabel='Declared-update Frobenius distance',title='Restart neighborhood');axs[1].bar(labels,[float(x['U_relative_distance'])for x in selected],color=colors);axs[1].set(ylabel='Symmetric relative distance (fraction)',title='Scale-normalized change')
    bottom=np.zeros(3)
    for kind in sorted({x['group']for x in targets}):
        v=[float(next(x['fraction_U_squared_distance']for x in targets if x['edge_id']==e['edge_id']and x['group']==kind))for e in selected];axs[2].bar(labels,v,bottom=bottom,label=kind);bottom+=v
    axs[2].set(ylabel='Fraction of squared parameter distance',ylim=(0,1),title='All target types');axs[2].legend(fontsize=7,loc='upper left',bbox_to_anchor=(1,1));
    for ax in axs:ax.tick_params(axis='x',rotation=35)
    fig.tight_layout(rect=(0,.1,1,.95));save(fig,'restart_neighborhood',['GLOBAL_EDGE_METRICS.csv','TARGET_EDGE_SUMMARY.csv'],'Predeclared three-edge neighborhood with six-type squared-distance composition; no p-value or continuity inference')
    manifest=dict(schema='POD_B.adapter_trajectory.figures.v1',analysis_spec_sha256=specsha,plot_code_sha256=sha(Path(__file__)),figures=figures,plot_scope='Parameter products only; no task labels/sequences/held-out outputs/model inference',zero_color='Masked zero cells if any; not converted to a positive distance',model_qualification_unchanged=0)
    (out/'FIGURE_MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n');print(json.dumps(dict(figures=len(figures),export_files=sum(len(x['files'])for x in figures),manifest='FIGURE_MANIFEST.json')))

if __name__=='__main__':main()
