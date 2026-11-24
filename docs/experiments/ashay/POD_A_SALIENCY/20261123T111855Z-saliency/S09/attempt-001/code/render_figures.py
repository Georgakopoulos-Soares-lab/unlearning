"""Qualified Agg renderer. Validate all artist values/bounds, never fabricate missingness."""
from s09_common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np,sys,datetime,textwrap
from PIL import Image
from matplotlib.lines import Line2D
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.titlesize':8,'axes.labelsize':8,'xtick.labelsize':6,'ytick.labelsize':6,'svg.hashsalt':'POD_A_SALIENCY_S09_7007ebd','pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False})
def render_one(spec,out):
 out.mkdir(parents=True,exist_ok=True);fid=spec['id'];seal=out/(fid+'.RENDER.json')
 if seal.exists():
  receipt=read(seal);assert receipt['spec_sha256']==spec['spec_sha256'] and receipt['renderer_sha256']==sha(Path(__file__))
  for f in receipt['exports']:assert sha(out/f['path'])==f['sha256']
  print('REUSE_VERIFIED_RENDER',fid,flush=True);return receipt
 fig,axes=plt.subplots(spec['nrows'],spec['ncols'],figsize=spec['size_inches'],squeeze=False);checked_points=checked_bounds=0
 for ax,panel in zip(axes.flat,spec['panels']):
  kind=panel['kind'];ax.set_title(panel['title'],loc='left',fontweight='bold',pad=5)
  if kind=='coverage':
   ys=np.arange(len(panel['values']));bars=ax.barh(ys,panel['values'],color=panel['colors']);assert [float(v.get_width()) for v in bars]==panel['values'];checked_points+=len(ys);ax.set_yticks(ys,panel['labels']);ax.invert_yaxis();ax.set_xlabel('Frozen specifications (count; deferred is unknown)')
   for y,v in zip(ys,panel['values']):ax.text(v+300,y,f'{v:,}',va='center',fontsize=9)
   ax.set_xlim(0,max(panel['values'])*1.16)
  elif kind in ['matrix','range_matrix']:
   z=np.array(panel['values'],dtype=float);mesh=ax.pcolormesh(np.arange(z.shape[1]+1)-.5,np.arange(z.shape[0]+1)-.5,z,cmap=panel['cmap'],vmin=panel['vmin'],vmax=panel['vmax'],shading='flat');assert np.array_equal(np.array(mesh.get_array()).reshape(z.shape),z,equal_nan=True);checked_points+=z.size;ax.set_xlim(-.5,z.shape[1]-.5);ax.set_ylim(z.shape[0]-.5,-.5);ax.set_yticks(range(z.shape[0]),panel['yticklabels']);bar=fig.colorbar(mesh,ax=ax,fraction=.025,pad=.025,label=panel['colorbar_label'])
   if panel.get('all_exact_zero'):bar.set_ticks([0]);ax.text(.5,.5,'All ranges exactly zero',transform=ax.transAxes,ha='center',va='center',color='white',fontsize=11)
  else:
   for item in panel['lines']:
    x=np.array(item['x'],dtype=float);y=np.array(item['y'],dtype=float);horizontal=item['horizontal'];xp,yp=(y,x) if horizontal else (x,y)
    line,=ax.plot(xp,yp,color=item['color'],marker=item['marker'],markersize=2.8,linewidth=.8,linestyle=item['linestyle'],label=item['label']);assert np.array_equal(np.asarray(line.get_xdata()),xp) and np.array_equal(np.asarray(line.get_ydata()),yp);checked_points+=len(x)
    if item['low'] is not None:
     low=np.array([np.nan if v is None else v for v in item['low']]);high=np.array([np.nan if v is None else v for v in item['high']]);valid=np.isfinite(low)&np.isfinite(high);assert np.all(low[valid]<=high[valid]);collection=ax.hlines(x[valid],low[valid],high[valid],color=item['color'],linewidth=.65,alpha=.65) if horizontal else ax.vlines(x[valid],low[valid],high[valid],color=item['color'],linewidth=.65,alpha=.55)
     for k,segment in enumerate(collection.get_segments()):
      j=np.flatnonzero(valid)[k];expected=np.array([[low[j],x[j]],[high[j],x[j]]]) if horizontal else np.array([[x[j],low[j]],[x[j],high[j]]]);assert np.allclose(segment,expected,atol=1e-12,rtol=0);checked_bounds+=2
   if panel.get('zero'):ax.axvline(0,color='#555555',linewidth=.7)
   if 'ylim' in panel:ax.set_ylim(*panel['ylim'])
   if 'xlim' in panel:ax.set_xlim(*panel['xlim'])
   if 'yticks' in panel:ax.set_yticks(panel['yticks'],panel['yticklabels'])
   if 'xticks' in panel:ax.set_xticks(panel['xticks'],panel['xticklabels'],rotation=48 if panel.get('rotate_labels') else 0,ha='right' if panel.get('rotate_labels') else 'center')
   ax.grid(alpha=.15,linewidth=.5)
  if panel.get('representation_axis'):
   ax.set_xticks([0,4,8,12,16,20,24,25],['0','4','8','12','16*','20','24','FN*'])
   for tick in ax.get_xticklabels():
    if '*' in tick.get_text():tick.set_color('#a12a2a');tick.set_fontweight('bold')
  ax.set_xlabel(panel.get('xlabel',ax.get_xlabel()));ax.set_ylabel(panel.get('ylabel',ax.get_ylabel()))
 for ax in list(axes.flat)[len(spec['panels']):]:ax.set_visible(False)
 title=spec['title'];fig.suptitle(title,fontsize=15,fontweight='bold',y=.995)
 if spec['family'] in ['profiles','gaps','metrics']:
  handles=[Line2D([0],[0],color=c,marker='o',linestyle='-',label='CV seed '+str(s)) for c,s in zip(['#246b9e','#db7840','#6a4c93'],[42,17,1234])]
  if spec['family']=='metrics':handles.extend([Line2D([0],[0],color='black',marker='o',linestyle='none',label='Refitted'),Line2D([0],[0],color='black',marker='s',linestyle='none',label='Original readout')])
  fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.95 if spec['family']=='gaps' else .982),ncol=len(handles),frameon=False,fontsize=8)
 elif spec['family']=='forests':
  handles=[Line2D([0],[0],color=c,marker='o',linestyle='-',label=r) for c,r in zip(['#246b9e','#db7840','#6a4c93'],['Original base','Composition','Forward 4mer'])]+[Line2D([0],[0],color='black',marker=m,linestyle='none',label=l) for m,l in [('o','Refitted'),('s','Original readout')]];fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.982),ncol=5,frameon=False,fontsize=8)
 footer='DEV · 95% pointwise exploratory conditional intervals where shown · no intervention replication or familywise guarantee' if spec['family'] not in ['seeds','coverage'] else ('Seed range is descriptive, not a confidence interval · all26 representations · no intervention replication' if spec['family']=='seeds' else 'Whole inventory PARTIAL · admitted benign scope complete · immediate parents and exact LM base endpoint joins unresolved')
 if spec['split']=='train':footer='TRAIN diagnostic only · no bootstrap interval or new LM contrast · each endpoint labeled separately'
 fig.text(.5,.008,footer,ha='center',fontsize=8)
 key_required=spec['family'] in ['metrics','seeds']
 if key_required:
  labels=list(spec['candidate_labels'].values())
  for j in range(3):fig.text(.5,.025+j*.009,'  ·  '.join(labels[j*3:j*3+3]),ha='center',fontsize=6)
  for ax in axes.flat:
   if ax.get_visible():ax.set_xlabel(ax.get_xlabel().replace('(labels/steps below)','(method/step key below)'))
 fig.tight_layout(rect=(0,.057 if key_required else .018,1,.925 if spec['family']=='gaps' else .965),h_pad=1.5,w_pad=2)
 fig.canvas.draw();renderer=fig.canvas.get_renderer();outside=[]
 # Visible annotation geometry is explicitly qualified, including rotated endpoint labels.
 for ax in fig.axes:
  xt=[label for value,label in zip(ax.get_xticks(),ax.get_xticklabels()) if min(ax.get_xlim())<=value<=max(ax.get_xlim())];yt=[label for value,label in zip(ax.get_yticks(),ax.get_yticklabels()) if min(ax.get_ylim())<=value<=max(ax.get_ylim())]
  for text in [ax.title,ax.xaxis.label,ax.yaxis.label,*xt,*yt]:
   if text.get_visible() and text.get_text():
    bb=text.get_window_extent(renderer)
    if bb.x0<-.5 or bb.y0<-.5 or bb.x1>fig.bbox.width+.5 or bb.y1>fig.bbox.height+.5:outside.append(text.get_text())
 assert not outside,('Clippedtext',fid,outside)
 exports=[]
 for ext in ['png','pdf','svg']:
  dest=out/(fid+'.'+ext);temp=out/(fid+'.partial.'+ext);metadata={'Date':None} if ext=='svg' else ({'CreationDate':None,'ModDate':None} if ext=='pdf' else {})
  fig.savefig(temp,format=ext,dpi=spec['dpi'],metadata=metadata);os.replace(temp,dest);exports.append({'path':dest.name,'sha256':sha(dest),'bytes':dest.stat().st_size})
 with Image.open(out/(fid+'.png')) as im:dimensions=[im.width,im.height];im.verify()
 assert (out/(fid+'.pdf')).read_bytes().startswith(b'%PDF') and '<svg' in (out/(fid+'.svg')).read_text();plt.close(fig)
 receipt={'status':'PASS','id':fid,'family':spec['family'],'spec_sha256':spec['spec_sha256'],'source_rows_sha256':spec['source_rows_sha256'],'checked_artist_point_or_cell_values':checked_points,'checked_interval_bounds':checked_bounds,'png_dimensions':dimensions,'exports':exports,'renderer_sha256':sha(Path(__file__)),'matplotlib_version':matplotlib.__version__};save(seal,receipt);print('RENDER_AND_ALL_ARTIST_VALUES_VERIFIED',fid,checked_points,checked_bounds,flush=True);return receipt

if __name__=='__main__':
 root=Path(sys.argv[1]) if len(sys.argv)>1 else P;out=Path(sys.argv[2]) if len(sys.argv)>2 else root/'figures';receipts=[]
 for file in sorted((root/'figure-specs').glob('*.json')):receipts.append(render_one(read(file),out))
 save(out.parent/'FIGURE_MANIFEST.json',{'status':'PASS_RENDERED_AND_SOURCE_VALUES_VALIDATED','figures':len(receipts),'unique_layout_families':sorted(set(r['family'] for r in receipts)),'artist_values_checked':sum(r['checked_artist_point_or_cell_values'] for r in receipts),'interval_bounds_checked':sum(r['checked_interval_bounds'] for r in receipts),'records':receipts,'byte_determinism':'PNG/PDF/SVG bytes recorded; fresh replay equivalence assessed separately, not assumed'});print('ALL_FIGURES_RENDERED_VERIFIED',len(receipts),flush=True)
