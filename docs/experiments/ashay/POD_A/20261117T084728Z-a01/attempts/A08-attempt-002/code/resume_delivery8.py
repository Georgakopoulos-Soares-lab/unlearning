from common8 import *
from finish8 import quiet,seal
from delivery8 import deliver
import shutil,xml.etree.ElementTree as ET

def shape(el):return (el.tag,{k:' '.join(v.split()) for k,v in el.attrib.items()},el.text.strip() if el.text else '',[shape(c) for c in el])
def main():
 guard();assert not (C/'SCIENTIFIC_DELIVERY.json').exists();quiet();changes=[];saved=A/'svg-before-whitespace-normalization';saved.mkdir()
 for p in sorted((D/'figures').glob('*.svg')):
  before=p.read_bytes();after=b'\n'.join(line.rstrip(b' \t\r') for line in before.split(b'\n'));assert shape(ET.fromstring(before))==shape(ET.fromstring(after));shutil.copyfile(p,saved/p.name);guard();atomic(p,after);changes.append({'path':str(p.relative_to(D)),'before_sha256':bh(before),'after_sha256':bh(after),'bytes':len(after),'XML_structure_text_and_normalized_attributes_identical':True})
 m=read(D/'FIGURE_MANIFEST.json')
 for f in m['figures']:
  for e in f['files']:
   p=D/e['path']
   if p.suffix=='.svg':e.update(sha256=sha(p),bytes=p.stat().st_size)
   else:assert sha(p)==e['sha256']
 publish('FIGURE_MANIFEST.json',m);v=read(C/'VISUAL_VALIDATION.json');v['SVG_trailing_whitespace_normalized_after_visual_inspection']={'XML_semantic_structure_identical':True,'PDF_PNG_unchanged':True,'source_data_unchanged':True};put(C/'VISUAL_VALIDATION.json',v);publish('VISUAL_VALIDATION.json',v)
 r={'status':'PASS','reason':'Matplotlib SVG path-line trailing whitespace rejected by git diff --check; only SVG trailing horizontal whitespace removed','failed_delivery_log':'logs/finish.001.stdout.log','changed':changes,'all_numerical_sources_science_points_intervals_PDF_PNG_unchanged':True,'model_audit_refit_contrast_recomputations':0,'observed_utc':now()};put(C/'DELIVERY_WHITESPACE_REPAIR.json',r);publish('DELIVERY_WHITESPACE_REPAIR.json',r);publish('PLOT_RENDER_REPAIR.json',read(C/'PLOT_RENDER_REPAIR.json'));publish('code/'+Path(__file__).name,Path(__file__).read_bytes());publish('ORCHESTRATION_SOURCE_IDENTITY.json',{'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((A/'code').glob('*.py'))],'frozen_audit_source_sha256':sha(C/'SOURCE_IDENTITY.json'),'frozen_contrast_source_sha256':sha(C/'CONTRAST_SOURCE_IDENTITY.json'),'reporting_plotting_supervision_sources_are_separate_from_numerical_freezes':True});seal();r=deliver('A08 R5: independently release390 units, verify eligible contrasts and publish scientific analysis');put(C/'SCIENTIFIC_DELIVERY.json',r);print(json.dumps({k:r[k] for k in ['status','commit','remote_equal']}))
if __name__=='__main__':main()
