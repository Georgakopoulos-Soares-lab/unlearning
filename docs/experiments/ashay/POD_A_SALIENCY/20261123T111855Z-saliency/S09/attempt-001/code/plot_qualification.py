from s09_common import *
import importlib.metadata as md,sys
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image
out=A/'plot-qualification';out.mkdir(exist_ok=True)
plt.rcParams.update({'svg.hashsalt':'POD_A_SALIENCY_S09_7007ebd','font.family':'DejaVu Sans','pdf.fonttype':42,'svg.fonttype':'none'})
x=np.array([0.,1.,2.]);y=np.array([.3,-.1,.6]);lo=np.array([.1,-.4,.4]);hi=np.array([.5,.2,.9]);fig,ax=plt.subplots(figsize=(5,3));line=ax.errorbar(x,y,yerr=[y-lo,hi-y],fmt='o');assert np.array_equal(line.lines[0].get_xdata(),x) and np.array_equal(line.lines[0].get_ydata(),y)
segments=line.lines[2][0].get_segments()
for i,segment in enumerate(segments):assert np.allclose(segment,np.array([[x[i],lo[i]],[x[i],hi[i]]]),atol=1e-15,rtol=0)
ax.axhline(0,color='grey');ax.set(xlabel='Synthetic endpoint',ylabel='Signed test value',title='S09 rendering qualification');fig.tight_layout()
for ext in ['png','pdf','svg']:fig.savefig(out/('fixture.'+ext),dpi=140,metadata={'Date':None} if ext=='svg' else ({'CreationDate':None,'ModDate':None} if ext=='pdf' else {}))
with Image.open(out/'fixture.png') as im:assert im.width>=500 and im.height>=300;im.verify()
assert (out/'fixture.pdf').read_bytes().startswith(b'%PDF') and '<svg' in (out/'fixture.svg').read_text()
lock={'status':'PASS','isolated_python':sys.executable,'python_version':sys.version,'versions':{v.metadata['Name']:v.version for v in md.distributions()},'backend':matplotlib.get_backend(),'font_path':font_manager.findfont('DejaVu Sans'),'font_sha256':sha(font_manager.findfont('DejaVu Sans')),'install_report_sha256':sha(C/'PLOT_INSTALL_REPORT.json'),'synthetic_points_and_errorbar_segments_checked':3,'exports':{p.name:sha(p) for p in out.iterdir()},'scientific_runtime_modified':False,'scientific_calculations_in_plot_runtime':False,'completed_utc':now()};save(C/'PLOT_ENVIRONMENT_LOCK.json',lock);print('PLOT_QUALIFICATION_PASS',lock['versions'],flush=True)
